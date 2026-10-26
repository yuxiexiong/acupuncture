import json
from pathlib import Path
import tempfile
import unittest

from metrics import candidate_comparisons, choice_metrics, paired_effect, summarize, task_evidence
from prepare_data import FAMILIES, freeze_function, functional_rows


class ScoringTests(unittest.TestCase):
    def test_complete_arc_choices_use_characters_without_separator(self):
        item = {"benchmark": "arc_challenge", "continuations": [" x", " yy"],
                "choices": ["x", "yy"], "target_index": 1}
        result = choice_metrics(item, [-2, -3])
        self.assertEqual(result["scores"], [-2, -1.5])
        self.assertEqual(result["correct"], 1)
        self.assertEqual(result["margin"], .5)

    def test_mmlu_tie_is_first_and_margin_zero(self):
        item = {"benchmark": "mmlu", "continuations": [" A", " B"], "target_index": 1}
        result = choice_metrics(item, [-1, -1])
        self.assertEqual((result["prediction"], result["correct"], result["margin"]), (0, 0, 0))

    def test_pair_variants_do_not_inflate_sample(self):
        rows = [{"id": str(i), "pair_id": str(i // 4),
                 "conditions": {"a": {"correct": 1}, "b": {"correct": 0}}} for i in range(8)]
        result = paired_effect(rows, "a", "b", "correct", draws=200)
        self.assertEqual((result["unit_count"], result["item_count"], result["ci95"]), (2, 8, [1, 1]))

    def test_control_beats_repair_cannot_pass(self):
        rows = []
        for i in range(32):
            conditions = {}
            for name, correct in (("clean", 1), ("AB_d1", 0), ("repair", i < 2),
                                  ("control_repair", i < 3), ("replay", 0), ("control_replay", 1)):
                conditions[name] = {"correct": int(correct), "margin": float(correct)}
            rows.append({"id": str(i), "benchmark": "mmlu", "conditions": conditions})
        result = summarize(rows, candidate_comparisons(), draws=200)["mmlu"]
        self.assertLess(result["repair_vs_matched_control"]["correct"]["effect"], 0)
        self.assertFalse(task_evidence(result)["task_endpoint_supported"])

    def test_missing_pairs_and_duplicate_rows_fail(self):
        row = {"id": "x", "conditions": {"a": {"correct": 1}, "b": {"correct": 0}}}
        with self.assertRaises(ValueError):
            paired_effect([row, row], "a", "b", "correct", draws=200)
        with self.assertRaises(KeyError):
            paired_effect([row], "a", "missing", "correct", draws=200)


class FunctionTests(unittest.TestCase):
    def test_function_budget_splits_and_label_controls(self):
        for family in FAMILIES:
            rows = functional_rows(family)
            self.assertEqual(len(rows), 128)
            self.assertEqual(len({row["id"] for row in rows}), 128)
            self.assertEqual(sum(row["split"] == "confirm" for row in rows), 64)
            self.assertEqual(len({row["pair_id"] for row in rows}), 32)
            first = rows[:4]
            self.assertEqual(first[0]["target_index"], first[1]["target_index"])
            self.assertNotEqual(first[0]["target_index"], first[2]["target_index"])
            self.assertEqual(first[0]["choices"][first[0]["target_index"]],
                             first[2]["choices"][first[2]["target_index"]])
            self.assertNotEqual(first[0]["target_index"], first[0]["donor_target_index"])
            self.assertEqual(first[1]["target_index"], first[1]["donor_target_index"])
            self.assertNotEqual(first[0]["context"], first[0]["donor_context"])

    def test_function_contract_is_required_and_immutable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contract = root / "function.json"
            contract.write_text('{}')
            with self.assertRaises(ValueError):
                freeze_function(contract, root)
            contract.write_text(json.dumps({"status": "frozen_before_confirmation", "candidate_ids": ["c1"],
                "family": "reading", "function_hypothesis": "source reading", "reader": "unpatched module",
                "relation": "input-content dependence", "expected_direction": "restored", "falsifier": "label-only"}))
            result = freeze_function(contract, root)
            self.assertEqual(result["files"]["functional_confirm.jsonl"]["pair_count"], 16)
            with self.assertRaises(ValueError):
                freeze_function(contract, root)


if __name__ == "__main__":
    unittest.main()
