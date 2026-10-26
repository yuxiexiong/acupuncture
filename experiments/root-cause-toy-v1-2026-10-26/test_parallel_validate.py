"""Model-free checks for the two-worker execution extension and evidence merge."""
import argparse
from contextlib import ExitStack
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import parallel_validate as parallel
import run_root as runner
from test_run_root import CONTRACT, FunctionalFakeEngine


class ParallelValidationTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.contract = copy.deepcopy(CONTRACT)
        self.contract["execution"] = {"maximum_model_workers": 1}
        self.contract["source"]["model_path"] = "unused"
        runner.write(self.root / "contract.json", self.contract)
        runner.write(self.root / "freeze.json", {})
        self.freeze_sha = runner.sha(self.root / "freeze.json")
        self.auth = self.root / "authorization.json"
        runner.write(self.auth, {"status": "authorized", "experiment": "test",
            "user_instruction": "synthetic CPU test only", "granted_at": "test",
            "maximum_model_workers": 2})
        self.items = [{"id": task, "benchmark": task, "context": task,
            "context_sha256": runner.hashlib.sha256(task.encode()).hexdigest(),
            "continuations": [" a", " b"], "choices": ["a", "b"], "target_index": 0}
            for task in ("mmlu", "arc_challenge")]
        self.candidates = [{"id": f"C{i:02d}", "component": f"L{14+i}.mlp",
            "positions": "prompt_last", "control_seed": 100+i} for i in range(1, 4)]
        self.preflight = self.root / "preflight" / "receipt.json"
        self.preflight.parent.mkdir()
        runner.write(self.preflight, {"status": "completed", "stage": "preflight",
            "freeze_sha256": self.freeze_sha, "files": {}})
        self.rank = self.root / "rank" / "receipt.json"
        self.rank.parent.mkdir()
        runner.write(self.rank.parent / "candidates.json", self.candidates)
        engine = FunctionalFakeEngine()
        self.calibrations = engine.calibrate([item["context"] for item in self.items])
        for i, (item, calibration) in enumerate(zip(self.items, self.calibrations)):
            runner.write(self.rank.parent / f"item-{i:03d}.json",
                {"id": item["id"], "benchmark": item["benchmark"],
                 "item_sha256": runner.digest(item), "calibration": calibration, "ranking": []})
        runner.write(self.rank, {"status": "completed", "stage": "rank",
            "freeze_sha256": self.freeze_sha, "files": runner.evidence_manifest(self.rank.parent)})
        self.parents_before = {path: path.read_bytes() for path in
            (self.preflight, self.rank, self.root / "freeze.json", self.rank.parent / "candidates.json")}
        self.stack.enter_context(patch.object(runner, "HERE", self.root))
        self.stack.enter_context(patch.object(runner, "verify"))
        self.stack.enter_context(patch.object(runner, "read_rows", return_value=self.items))
        self.stack.enter_context(patch.object(runner, "summarize", return_value={}))
        self.output = self.root / "parallel"

    def prepare(self):
        return parallel.prepare(self.preflight, self.rank, self.auth, self.output)

    def run_workers(self):
        self.prepare()
        for shard in (0, 1):
            parallel.worker(self.output, shard, device="cpu", engine_factory=FunctionalFakeEngine)

    def refresh_shard_manifest(self, shard=0):
        folder = self.output / f"shard-{shard}"
        path = folder / "receipt.json"
        receipt = runner.read(path)
        receipt["files"] = runner.evidence_manifest(folder)
        runner.write(path, receipt)

    def test_two_shards_equal_serial_and_preserve_original_evidence(self):
        self.run_workers()
        assignments = [{p.name for p in (self.output / f"shard-{i}").iterdir() if p.is_dir()}
                       for i in (0, 1)]
        self.assertEqual([len(group) for group in assignments], [2, 1])
        self.assertFalse(assignments[0] & assignments[1])
        self.assertEqual(assignments[0] | assignments[1], {c["id"] for c in self.candidates})
        merged = parallel.merge(self.output)
        self.assertEqual(merged["status"], "completed")
        args = argparse.Namespace(freeze=self.root / "freeze.json", execute=True,
            launch_authorization=self.auth, prior=[self.preflight, self.rank],
            stage="validate", explanations=None, output=self.root / "serial", model="unused", device="cpu")
        runner.run(args, engine_factory=FunctionalFakeEngine)
        for candidate in self.candidates:
            for i in range(len(self.items)):
                relative = Path(candidate["id"]) / f"ability-{i:03d}.json"
                self.assertEqual(runner.read(self.output / relative), runner.read(args.output / relative))
        self.assertEqual(self.parents_before, {p: p.read_bytes() for p in self.parents_before})
        with self.assertRaises((ValueError, FileExistsError)):
            parallel.worker(self.output, 0, device="cpu", engine_factory=FunctionalFakeEngine)

    def test_prepare_requires_parallel_authorization_and_original_freeze(self):
        auth = runner.read(self.auth)
        auth["maximum_model_workers"] = 1
        runner.write(self.auth, auth)
        with self.assertRaises(ValueError):
            self.prepare()
        auth["maximum_model_workers"] = 2
        runner.write(self.auth, auth)
        receipt = runner.read(self.rank)
        receipt["freeze_sha256"] = "other-version"
        runner.write(self.rank, receipt)
        with self.assertRaises(ValueError):
            self.prepare()

    def test_worker_rejects_changed_parent(self):
        self.prepare()
        runner.write(self.rank.parent / "candidates.json", list(reversed(self.candidates)))
        before = FunctionalFakeEngine.loads
        with self.assertRaises(ValueError):
            parallel.worker(self.output, 0, device="cpu", engine_factory=FunctionalFakeEngine)
        self.assertEqual(FunctionalFakeEngine.loads, before)

    def test_worker_rejects_duplicate_shard_assignment_before_model_load(self):
        self.prepare()
        path = self.output / "execution.json"
        plan = runner.read(path)
        plan["shards"][1] = plan["shards"][0]
        runner.write(path, plan)
        before = FunctionalFakeEngine.loads
        with self.assertRaises(ValueError):
            parallel.worker(self.output, 1, device="cpu", engine_factory=FunctionalFakeEngine)
        self.assertEqual(FunctionalFakeEngine.loads, before)

    def test_merge_rejects_incomplete_or_tampered_worker(self):
        self.run_workers()
        path = self.output / "shard-0" / "C01" / "ability-000.json"
        path.unlink()
        self.refresh_shard_manifest()
        with self.assertRaises((ValueError, FileNotFoundError)):
            parallel.merge(self.output)
        self.assertFalse((self.output / "receipt.json").exists())

    def test_merge_checks_question_identity_even_with_updated_file_hash(self):
        self.run_workers()
        path = self.output / "shard-0" / "C01" / "ability-000.json"
        row = runner.read(path)
        row["id"] = "another-question"
        runner.write(path, row)
        self.refresh_shard_manifest()
        with self.assertRaises(ValueError):
            parallel.merge(self.output)

    def test_merge_rejects_modified_scores_without_receipt_update(self):
        self.run_workers()
        path = self.output / "shard-0" / "C01" / "ability-000.json"
        row = runner.read(path)
        row["conditions"]["repair"]["correct"] = 0
        runner.write(path, row)
        with self.assertRaises(ValueError):
            parallel.merge(self.output)

    def test_merge_rejects_shard_from_another_freeze(self):
        self.run_workers()
        path = self.output / "shard-1" / "receipt.json"
        receipt = runner.read(path)
        receipt["base_freeze_sha256"] = "another-freeze"
        runner.write(path, receipt)
        with self.assertRaises(ValueError):
            parallel.merge(self.output)

    def test_merged_verification_binds_worker_receipts(self):
        self.run_workers()
        parallel.merge(self.output)
        parallel.verify_merged(self.output)
        path = self.output / "shard-1" / "receipt.json"
        receipt = runner.read(path)
        receipt["wall_seconds"] += 1
        runner.write(path, receipt)
        with self.assertRaises(ValueError):
            parallel.verify_merged(self.output)

    def test_worker_failure_keeps_failed_receipt(self):
        class FailingEngine(FunctionalFakeEngine):
            def score_item(self, *args, **kwargs):
                raise RuntimeError("deliberate synthetic worker failure")
        self.prepare()
        with self.assertRaises(RuntimeError):
            parallel.worker(self.output, 0, device="cpu", engine_factory=FailingEngine)
        receipt = runner.read(self.output / "shard-0" / "receipt.json")
        self.assertEqual(receipt["status"], "failed")
        self.assertIn("deliberate synthetic", (self.output / "shard-0" / "failure.log").read_text())
        with self.assertRaises(ValueError):
            parallel.merge(self.output)


if __name__ == "__main__":
    unittest.main()
