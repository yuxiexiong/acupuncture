"""Synthetic-only export checks. All generated fixture/output files stay in TemporaryDirectory."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

import export_recipes as exporter

runner = exporter.runner


def token_hash(tokens):
    return hashlib.sha256(json.dumps(tokens, separators=(",", ":")).encode()).hexdigest()


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="acupuncture-synthetic-export-")
        self.old_here, self.old_repo = runner.HERE, runner.REPO
        self.root = Path(self.temp.name)
        self.make_fixture(2)

    def tearDown(self):
        runner.HERE, runner.REPO = self.old_here, self.old_repo
        self.temp.cleanup()

    def make_fixture(self, shards):
        here = self.root / f"synthetic-{shards}-shards"
        here.mkdir()
        runner.HERE, runner.REPO = here, self.root
        self.here, self.output = here, here / "synthetic-export"
        self.questions = [{"id": f"Q{i:02}", "prompt": f"SYNTHETIC fixture question {i}"} for i in range(1, 6)]
        self.recipes = [{"id": f"recipe-{i}", "label": f"SYNTHETIC <script>{i}</script>",
                         "question_ids": [q["id"] for q in self.questions],
                         "interventions": [{"layer": i, "neuron": 10 + i, "dose": 0.5}]}
                        for i in range(3)]
        self.recipes[1]["normalization"] = "per_prompt_median"
        self.recipes[2]["generation"] = {"do_sample": True, "temperature": 0.7, "top_k": 20, "top_p": 0.8}
        contract = {"synthetic": True, "model": {"id": "4b", "revision": "synthetic-revision", "layers": 32,
                                                "hidden_size": 2560, "intermediate_size": 9216,
                                                "dtype": "bfloat16", "attention": "synthetic"},
                    "versions": {"torch": "not-loaded-synthetic"},
                    "generation": {"enable_thinking": False, "max_new_tokens": 128, "eos_token_ids": [248044, 248046]}}
        scales = {"residual_scales": {str(i): 1.0 for i in range(32)}}
        for name, value in (("contract.json", contract), ("recipes.json", self.recipes),
                            ("questions.json", self.questions), ("scales.json", scales)):
            runner.io.write(here / name, value)
        files = {str((here / name).relative_to(self.root)): runner.io.sha(here / name)
                 for name in ("contract.json", "recipes.json", "questions.json", "scales.json")}
        runner.io.write(here / "freeze.json", {"experiment": here.name, "synthetic": True, "files": files})
        metadata = {"synthetic": True, "model_id": "4b", "revision": "synthetic-revision", "dtype": "bfloat16",
                    "versions": {"torch": "not-loaded-synthetic"}, "target_weight_sha256_before": {"test": "synthetic"},
                    "effective_stop_tokens": {"248044": "<|endoftext|>", "248046": "<|im_end|>"},
                    "enable_thinking": False, "attention_backend": "synthetic"}
        self.runs = []
        for shard in range(shards):
            run = here / f"synthetic-run-{shard}"
            self.runs.append(run)
            runner.io.write(run / "metadata.json", metadata)
            jobs = runner.schedule(self.recipes, self.questions, shard, shards)
            hashes = {}
            for rid, points, qid, generation in jobs:
                context = f"SYNTHETIC context {qid}"
                calibration = {"context_sha256": hashlib.sha256(context.encode()).hexdigest(),
                               "input_token_sha256": token_hash([1, 2, 3]), "input_token_count": 3,
                               "normalization": "per_prompt_median" if rid == "recipe-1" else "fixed_reference",
                               "residual_scales": scales["residual_scales"], "scales_sha256": runner.io.sha(here / "scales.json")}
                tokens = [7] * 128 if qid == "Q05" else [7, 248046]
                output = {"token_ids": tokens, "generated_token_count": len(tokens), "returned_padding_count": 0,
                          "max_new_tokens": 128, "end_reason": "length_limit" if qid == "Q05" else "eos_token",
                          "raw_text": f"SYNTHETIC {rid}/{qid}\n<unsafe>& 原文\n<|im_end|>",
                          "answer_text": f"SYNTHETIC {rid}/{qid}", "effective_generation": generation,
                          "input_token_sha256": calibration["input_token_sha256"], "token_sha256": token_hash(tokens)}
                audit = [{**point, "reference_residual_scale": 1.0, "column_norm": 2.0,
                          "requested_offset": point["dose"] / 2.0, "calls": len(tokens),
                          "positions": 3 + len(tokens) - 1, "prefill_target_values_checked": True} for point in points]
                row = {"synthetic": True, "recipe_id": rid, "baseline_id": runner.baseline_id(generation),
                       "question_id": qid, "prompt": next(q["prompt"] for q in self.questions if q["id"] == qid),
                       "context": context, "interventions": points, "calibration": calibration,
                       "hook_audit": audit, "output": output}
                relative = f"records/{rid}__{qid}.json"
                runner.io.write(run / relative, row)
                hashes[relative] = runner.io.sha(run / relative)
            runner.io.write(run / "receipt.json", {"synthetic": True, "status": "completed", "mode": "run",
                "experiment": here.name, "shard": shard, "shards": shards,
                "freeze_sha256": runner.io.sha(here / "freeze.json"), "scales_sha256": runner.io.sha(here / "scales.json"),
                "jobs": jobs, "record_hashes": hashes, "expected_records": len(jobs), "completed_records": len(jobs),
                "metadata_sha256": runner.io.sha(run / "metadata.json"),
                "integrity": {"target_weight_sha256_after": metadata["target_weight_sha256_before"], "hooks_removed": True}})

    def record_path(self, rid="recipe-0", qid="Q01"):
        return next(run / f"records/{rid}__{qid}.json" for run in self.runs
                    if (run / f"records/{rid}__{qid}.json").exists())

    def rewrite_record(self, path, row):
        runner.io.write(path, row)
        receipt_path = path.parent.parent / "receipt.json"
        receipt = runner.io.read(receipt_path)
        receipt["record_hashes"][str(path.relative_to(path.parent.parent))] = runner.io.sha(path)
        runner.io.write(receipt_path, receipt)

    def test_complete_raw_roundtrip_and_escaped_html(self):
        receipt = exporter.export(self.runs, self.output)
        self.assertEqual(receipt["counts"], {"recipes": 3, "questions_per_recipe": 5, "pairs": 15,
                         "original_records": 10, "modified_records": 15, "all_records": 25})
        for name in ("original.raw.jsonl", "modified.raw.jsonl"):
            for row in runner.io.rows(self.output / name):
                source = runner.io.read(Path(row["source_run"]) / row["source_record"])
                self.assertTrue(row["synthetic"])
                self.assertEqual({k: row[k] for k in source}, source)
        page = (self.output / "paired_raw.html").read_text()
        self.assertIn('&lt;unsafe&gt;&amp; 原文\n&lt;|im_end|&gt;', page)
        self.assertNotIn('<script>0</script>', page)
        self.assertIn('id="filter"', page)
        self.assertEqual(page.count('<article>'), 15)
        self.assertTrue(receipt["whole_frozen_schedule_complete"])
        for name, digest in receipt["files"].items():
            self.assertEqual(runner.io.sha(self.output / name), digest)
        self.assertNotIn("torch", sys.modules)
        self.assertNotIn("transformers", sys.modules)

    def test_single_complete_shard(self):
        self.make_fixture(1)
        self.assertEqual(exporter.export(self.runs, self.output)["counts"]["pairs"], 15)

    def test_missing_incomplete_and_duplicate_runs(self):
        for runs in ([self.here / "missing"], self.runs[:1], [self.runs[0], self.runs[0]]):
            with self.subTest(runs=runs), self.assertRaises((AssertionError, FileNotFoundError)):
                exporter.export(runs, self.output)
            self.assertFalse(self.output.exists())
        path = self.runs[0] / "receipt.json"
        receipt = runner.io.read(path); receipt["status"] = "running"; runner.io.write(path, receipt)
        with self.assertRaises(AssertionError):
            exporter.export(self.runs, self.output)

    def test_pair_context_must_match_even_with_valid_hashes(self):
        path = self.record_path(); row = runner.io.read(path)
        row["context"] += " changed"
        row["calibration"]["context_sha256"] = hashlib.sha256(row["context"].encode()).hexdigest()
        self.rewrite_record(path, row)
        with self.assertRaisesRegex(AssertionError, "Mismatched paired input"):
            exporter.export(self.runs, self.output)

    def test_token_stop_and_budget_checks_survive_rehashed_files(self):
        path = self.record_path(); original = runner.io.read(path)
        mutations = [lambda out: out.update(token_sha256="wrong"),
                     lambda out: out.update(end_reason="length_limit"),
                     lambda out: out.update(max_new_tokens=129),
                     lambda out: out.update(token_ids=[248046, 7], token_sha256=token_hash([248046, 7]))]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                row = deepcopy(original); mutate(row["output"]); self.rewrite_record(path, row)
                with self.assertRaises(AssertionError):
                    exporter.export(self.runs, self.output)
                self.assertFalse(self.output.exists())
        self.rewrite_record(path, original)

    def test_record_and_freeze_tampering(self):
        path = self.record_path(); data = path.read_bytes(); path.write_bytes(data + b" ")
        with self.assertRaises(AssertionError):
            exporter.export(self.runs, self.output)
        path.write_bytes(data)
        questions = self.here / "questions.json"; questions.write_text(questions.read_text() + " ")
        with self.assertRaisesRegex(AssertionError, "Frozen source changed"):
            exporter.export(self.runs, self.output)

    def test_extra_record_and_five_question_requirement(self):
        path = self.runs[0] / "records/extra.json"; runner.io.write(path, {"synthetic": True})
        with self.assertRaises(AssertionError):
            exporter.export(self.runs, self.output)
        path.unlink()
        self.recipes[0]["question_ids"].pop()
        runner.io.write(self.here / "recipes.json", self.recipes)
        with self.assertRaises(AssertionError):
            exporter.export(self.runs, self.output)

    def test_existing_output_is_never_overwritten(self):
        self.output.mkdir(); path = self.output / "modified.raw.jsonl"; path.write_text("SYNTHETIC preserved")
        with self.assertRaisesRegex(AssertionError, "never overwrite"):
            exporter.export(self.runs, self.output)
        self.assertEqual(path.read_text(), "SYNTHETIC preserved")
        self.assertEqual(list(self.output.iterdir()), [path])


if __name__ == "__main__":
    unittest.main()
