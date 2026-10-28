"""CPU fake-engine checks; never load model weights or execute generated code."""
from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import benchmark


class FakeEngine:
    def __init__(self, *args, **kwargs):
        self.calls = []
        self.batch_size, self.stop_ids, self.pad_id = 1, [128001, 128008, 128009], 128009
        self.conditions = {"T_0": {}, "true_D_match": {}, "true_S_recipe": {}}
        self.metadata = {"batch_size": 1, "dtype": "bfloat16", "attention_backend": "eager",
            "effective_stop_tokens": {str(i): f"stop-{i}" for i in self.stop_ids},
            "bos_token_id": 128000, "pad_token_id": self.pad_id, "target_weight_sha256_before": {"13": "a", "14": "b"},
            "tokenization": "One BOS", "chat_template_date_string": "26 Oct 2026"}

    def calibrate(self, contexts):
        self.calls.append(("calibrate", contexts))
        return [{"context_sha256": hashlib.sha256(text.encode()).hexdigest(), "input_token_count": 4,
            "input_token_sha256": "synthetic", "residual_scales": {"13": 3.0, "14": 4.0},
            "activation_offsets": {}} for text in contexts]

    def score(self, contexts, continuations, arm, calibrations):
        self.calls.append(("score", arm, contexts, calibrations))
        return [{"loglikelihood": -float(i + 1), "continuation_token_ids": [i],
            "context_token_count": 4, "input_token_sha256": "synthetic"} for i in range(len(continuations))]

    def generate(self, contexts, arm, calibrations, budget, stops):
        self.calls.append(("generate", arm, budget, stops, calibrations))
        return [{"max_new_tokens": budget, "generated_token_count": 1, "token_ids": [128009],
            "end_reason": "eos_token", "raw_text": "<|eot_id|>", "answer_text": ""} for _ in contexts]

    def verify_unchanged(self):
        return {"hooks_removed": True, "target_weight_sha256_after": {"13": "a", "14": "b"}}


class BenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol, cls.panel, cls.items = benchmark.frozen_panel()
        cls.evaluate = staticmethod(benchmark.load_v3("run_panel").evaluate_pair)

    def test_panel_and_stage_binding(self):
        self.assertEqual({key: len(value) for key, value in self.items.items()}, benchmark.COUNTS)
        self.assertEqual(sum(map(len, self.items.values())), 1400)
        self.assertEqual(len(self.panel["mmlu_population_subject_counts"]), 57)
        for stage, arm in ((1, "true_D_match"), (2, "true_S_recipe")):
            engine, item = FakeEngine(), self.items["arc_challenge"][0]
            with TemporaryDirectory() as directory:
                row = self.evaluate(benchmark.BenchmarkEngine(engine, stage), item, 0, self.protocol,
                                    Path(directory) / "partial.json")
            benchmark.validate_pair(row, item)
            self.assertEqual(engine.calls[0], ("calibrate", [item["context"]]))
            self.assertEqual([call[1] for call in engine.calls[1:]], ["T_0", arm])
            self.assertEqual(engine.calls[1][3], engine.calls[2][3])
            self.assertEqual(benchmark.finish_module(stage).ARM_NAMES, benchmark.arm_bindings(stage))

    def test_native_token_policy_and_budgets(self):
        engine = FakeEngine()
        self.assertEqual(benchmark.native_metadata(engine)["bos_token_id"], 128000)
        engine.metadata["effective_stop_tokens"].pop("128008")
        with self.assertRaises(AssertionError):
            benchmark.native_metadata(engine)
        for task, budget in (("gsm8k", 2048), ("humaneval", 1024)):
            engine, item = FakeEngine(), self.items[task][0]
            with TemporaryDirectory() as directory:
                row = self.evaluate(benchmark.BenchmarkEngine(engine, 1), item, 1, self.protocol,
                                    Path(directory) / "partial.json")
            benchmark.validate_pair(row, item)
            self.assertEqual([call[1] for call in engine.calls[1:]], ["true_D_match", "T_0"])
            self.assertTrue(all(call[2:4] == (budget, item["gen_kwargs"]["until"]) for call in engine.calls[1:]))
            self.assertEqual(row["outputs"]["evo"]["token_ids"], [128009])
            broken = deepcopy(row)
            broken["outputs"]["evo"]["max_new_tokens"] = 512
            with self.assertRaises(AssertionError):
                benchmark.validate_pair(broken, item)

    def test_all_1400_fake_pairs_and_legacy_finish_verification(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            output, model = root / "run/stage1/benchmark", root / "model"
            model.mkdir()
            conditions, freeze = root / "bundle.pt", root / "freeze.json"
            conditions.write_text("fake bundle, not model weights")
            freeze.write_text("{}")
            args = SimpleNamespace(stage=1, model=model, conditions=conditions, output=output, freeze=freeze)
            with patch.object(benchmark, "verify_freeze", return_value={}), \
                 patch.object(benchmark, "source_hashes", return_value={}), redirect_stdout(io.StringIO()):
                for shard in (0, 1):
                    args.shard_index = shard
                    benchmark.run(args, engine_factory=FakeEngine)
            records, paths, receipts = benchmark.verified_records(output, self.items, 1, freeze)
            self.assertEqual(len(records), 1400)
            self.assertEqual(len({row["id"] for row in records}), 1400)
            self.assertEqual([receipt["completed_pairs"] for receipt in receipts], [700, 700])
            self.assertEqual(receipts[0]["arm_bindings"], {"baseline": "T_0", "evo": "true_D_match"})
            command = benchmark.finish_module(1).sandbox_command(root, paths, root / "execution.jsonl")
            self.assertIn("--bwrap", command)
            self.assertIn("--official", command)
            self.assertEqual(command[2], str(benchmark.V3 / "humaneval_sandbox.py"))
            with self.assertRaises(AssertionError):
                benchmark.verified_records(output, self.items, 2, freeze)
            path = output / "shard-0/receipt.json"
            receipt = json.loads(path.read_text())
            receipt["completed_pairs"] = 699
            path.write_text(json.dumps(receipt))
            with self.assertRaises(AssertionError):
                benchmark.verified_records(output, self.items, 1, freeze)

    def test_stage2_gate_precedes_model_loading(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            args = SimpleNamespace(stage=2, output=root / "stage2/benchmark", freeze=root / "freeze.json",
                                   conditions=root / "bundle.pt")
            with patch.object(benchmark, "verify_freeze", return_value={}):
                with self.assertRaises(FileNotFoundError):
                    benchmark.run(args, engine_factory=lambda *a, **k: self.fail("Model loading bypassed stage gate"))
            self.assertFalse(args.output.exists())


if __name__ == "__main__":
    unittest.main()
