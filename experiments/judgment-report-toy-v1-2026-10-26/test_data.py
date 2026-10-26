"""CPU-only checks of paired content, rotations, and immutable data preparation."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import task_data as data


class DataTest(unittest.TestCase):
    def test_rotations_keep_question_and_few_shot_prefix(self):
        source = {row["id"]: row for row in data.read_rows(data.SOURCE) if row["benchmark"] == "mmlu"}
        variants = data.mmlu_rows()
        self.assertEqual(len(variants), 128)
        for row in variants:
            old = source[row["base_id"]]
            old_block = data.option_block(old["doc"]["choices"])
            prefix = old["context"][:-len(old_block)]
            self.assertEqual(row["context"], prefix + data.option_block(row["choices"]))
            if row["rotation"] == 0:
                self.assertEqual(row["context"], old["context"])
            self.assertEqual(row["order"][row["target_index"]], old["target_index"])
            restored = [None] * 4
            for display, original in enumerate(row["order"]):
                restored[original] = row["choices"][display]
            self.assertEqual(restored, old["doc"]["choices"])

    def test_comparison_demand_and_target_are_not_confounded(self):
        rows = data.comparison_rows()
        self.assertEqual(len(rows), 128)
        for row in rows:
            self.assertEqual(row["target_content_index"], row["amounts"].index(max(row["amounts"])))
            answer = row["original_choices"][row["target_content_index"]]
            if row["demand"] == "direct":
                self.assertIn(f"The correct answer is {answer}.", row["context"])
                self.assertNotIn("The correct answer is D.", row["context"])
            else:
                self.assertNotIn("The correct answer is", row["context"])
            self.assertTrue(row["context"].endswith(data.option_block(row["choices"])))
        self.assertEqual(data.validate_rows(data.build())["base_units"], 48)

    def test_wrong_mapping_or_missing_variant_is_rejected(self):
        rows = data.build()
        bad = copy.deepcopy(rows)
        bad[1]["target_index"] = (bad[1]["target_index"] + 1) % 4
        with self.assertRaises(ValueError):
            data.validate_rows(bad)
        with self.assertRaises(ValueError):
            data.validate_rows(rows[:-1])

    def test_freeze_is_repeatable_but_never_overwrites_changed_data(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            first = data.write(output)
            self.assertEqual(first, data.write(output))
            self.assertEqual(data.verify(output)["variants"], 256)
            path = output / "items.jsonl"
            path.write_text(path.read_text() + "{}\n")
            with self.assertRaises(ValueError):
                data.write(output)
            with self.assertRaises(ValueError):
                data.verify(output)

    def test_position_reference_is_flagged_not_dropped(self):
        self.assertEqual(data.reference_flags(["Both A and C", "all of the above", "blue", "none"]), [0, 1])


if __name__ == "__main__":
    unittest.main()
