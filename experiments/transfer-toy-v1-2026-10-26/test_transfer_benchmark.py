"""CPU tests for exact panel reuse, transfer arm binding, budgets, and scoring semantics."""
from copy import deepcopy
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from run_benchmark import (ARM_NAMES, BenchmarkEngine, COUNTS, V3, frozen_panel,
                           load_v3, validate_pair)
from finish_benchmark import sandbox_command


class FakeEngine:
    def __init__(self):
        self.calls = []

    def calibrate(self, contexts):
        self.calls.append(("calibrate", contexts))
        return [{"context_sha256": hashlib.sha256(context.encode()).hexdigest(),
                 "input_token_count": 4, "input_token_sha256": "synthetic",
                 "residual_scales": {"13": 3.0, "14": 4.0}, "activation_offsets": {}}
                for context in contexts]

    def score(self, contexts, continuations, arm, calibrations):
        self.calls.append(("score", arm, contexts, calibrations))
        return [{"loglikelihood": -float(i + 1), "continuation_token_ids": [i],
                 "context_token_count": 4, "input_token_sha256": "synthetic"}
                for i in range(len(continuations))]

    def generate(self, contexts, arm, calibrations, budget, stops):
        self.calls.append(("generate", arm, budget, stops, calibrations))
        return [{"max_new_tokens": budget, "generated_token_count": 1, "token_ids": [248046],
                 "end_reason": "eos_token", "raw_text": "<|im_end|>", "answer_text": ""}]


class TransferBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protocol, cls.panel, cls.items = frozen_panel()
        cls.evaluate = staticmethod(load_v3("run_panel").evaluate_pair)

    def test_fixed_items_and_no_hidden_resampling(self):
        self.assertEqual({key: len(value) for key, value in self.items.items()}, COUNTS)
        self.assertEqual(sum(self.panel["mmlu_population_subject_counts"].values()), 14042)
        self.assertEqual(len(self.panel["mmlu_population_subject_counts"]), 57)
        for task, items in self.items.items():
            halves = [items[index::2] for index in range(2)]
            self.assertEqual(len(halves[0]), len(halves[1]))
            self.assertFalse(set(x["id"] for x in halves[0]) & set(x["id"] for x in halves[1]))

    def test_exact_public_prompt_calibration_once_and_arm_binding(self):
        item = self.items["arc_challenge"][0]
        engine = FakeEngine()
        with TemporaryDirectory() as directory:
            row = self.evaluate(BenchmarkEngine(engine), item, 0, self.protocol,
                                Path(directory) / "partial.json")
        validate_pair(row, item)
        self.assertEqual(engine.calls[0], ("calibrate", [item["context"]]))
        self.assertEqual([call[1] for call in engine.calls[1:]], ["T_0", "true_S_recipe"])
        self.assertEqual(engine.calls[1][3], engine.calls[2][3])
        self.assertEqual(engine.calls[1][2], [item["context"]] * len(item["continuations"]))
        self.assertEqual(sum(call[0] == "calibrate" for call in engine.calls), 1)

    def test_math_code_budgets_and_task_stops_remain_exact(self):
        for task, budget in (("gsm8k", 2048), ("humaneval", 1024)):
            item, engine = self.items[task][0], FakeEngine()
            with TemporaryDirectory() as directory:
                row = self.evaluate(BenchmarkEngine(engine), item, 1, self.protocol,
                                    Path(directory) / "partial.json")
            validate_pair(row, item)
            self.assertEqual([call[1] for call in engine.calls[1:]], ["true_S_recipe", "T_0"])
            for call in engine.calls[1:]:
                self.assertEqual(call[2:4], (budget, item["gen_kwargs"]["until"]))
            broken = deepcopy(row)
            broken["outputs"]["evo"]["max_new_tokens"] = 512
            with self.assertRaises(AssertionError):
                validate_pair(broken, item)

    def test_broken_pair_is_not_completed(self):
        item, engine = self.items["mmlu"][0], FakeEngine()
        with TemporaryDirectory() as directory:
            row = self.evaluate(BenchmarkEngine(engine), item, 0, self.protocol,
                                Path(directory) / "partial.json")
        for field, value in (("status", "failed"), ("id", "wrong")):
            bad = deepcopy(row)
            bad[field] = value
            with self.assertRaises(AssertionError):
                validate_pair(bad, item)
        bad = deepcopy(row)
        bad["outputs"]["evo"]["status"] = "infrastructure_failure"
        with self.assertRaises(AssertionError):
            validate_pair(bad, item)

    def test_exact_official_scorer_weighting_and_safe_checker(self):
        scorer = load_v3("score_results")
        example = []
        for identity, subject, baseline, evo in (("a", "a", True, False), ("b", "b", False, True)):
            example.append({"id": identity, "subject": subject, "cluster_id": identity,
                "outputs": {arm: {"correct": correct, "parse_failed": False, "end_reason": "loglikelihood"}
                            for arm, correct in (("baseline", baseline), ("evo", evo))}})
        summary = scorer.summarize(example, {"a": 3, "b": 1})
        self.assertEqual(summary["baseline"]["score_percent"], 75)
        self.assertEqual(summary["evo"]["score_percent"], 25)
        self.assertEqual(summary["paired_interval"]["lower_pp"], 50)
        self.assertEqual(summary["paired_interval"]["repeats"], 10000)
        paths = [Path(f"/run/shard-{i % 2}/humaneval/{i:05d}.jsonl") for i in range(100)]
        command = sandbox_command(Path("/workspace/acupuncture"), paths, Path("/run/result.jsonl"))
        self.assertEqual(command[2], str(V3 / "humaneval_sandbox.py"))
        self.assertIn("--bwrap", command)
        self.assertIn("--official", command)
        self.assertEqual(ARM_NAMES, {"baseline": "T_0", "evo": "true_S_recipe"})


if __name__ == "__main__":
    unittest.main()
