"""CPU checks for task identity, pair truth, and frozen preparation; no model use."""
import json
from pathlib import Path
import tempfile
import unittest

import task_data


class TaskDataTests(unittest.TestCase):
    def setUp(self):
        self.panels = task_data.build()

    def test_development_is_exact_old_required_subset(self):
        original = json.loads(task_data.JOINT.read_text(encoding="utf-8"))
        expected = [r for r in original if r["base_id"] in task_data.DEVELOPMENT_BASES
                    and r["demand"] == "required"]
        actual = [{k: v for k, v in row.items() if k not in ("split", "source")}
                  for row in self.panels["development"]]
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 24)
        self.assertEqual({r["demand"] for r in actual}, {"required"})

    def test_fact_pairs_share_candidates_and_reference(self):
        for name in ("development", "confirmation"):
            rows = self.panels[name]
            self.assertEqual(len(rows), 24)
            self.assertEqual(len({r["id"] for r in rows}), 24)
            for base in {r["base_id"] for r in rows}:
                pair = sorted((r for r in rows if r["base_id"] == base), key=lambda r: r["fact_version"])
                self.assertEqual([r["fact_version"] for r in pair], [0, 1])
                self.assertEqual(pair[0]["choices"], pair[1]["choices"])
                self.assertEqual(len(set(pair[0]["choices"])), 2)
                self.assertEqual({r["target_index"] for r in pair}, {0, 1})
                self.assertEqual({r["reference_id"] for r in pair}, {f"{base}-f0-required"})
                self.assertNotEqual(pair[0]["prompt"], pair[1]["prompt"])
                self.assertTrue(all(r["truth_explanation"] for r in pair))
            self.assertEqual({family: sum(r["family"] == family for r in rows)
                              for family in ("reading", "arithmetic", "relation")},
                             {"reading": 8, "arithmetic": 8, "relation": 8})

    def test_confirmation_has_new_structures_and_fixed_truth(self):
        original = json.loads(task_data.JOINT.read_text(encoding="utf-8"))
        self.assertFalse({r["prompt"] for r in original} & {r["prompt"] for r in self.panels["confirmation"]})
        self.assertFalse({r["base_id"] for r in original} & {r["base_id"] for r in self.panels["confirmation"]})
        self.assertEqual(len({r["source"]["structure"] for r in self.panels["confirmation"]}), 12)
        # Authored ground-truth check, not independent semantic review or model evidence.
        answers = {
            "CRD01": ("入库日是周二。", "入库日是周三。"),
            "CRD02": ("已确认的位置是左柜。", "已确认的位置是右柜。"),
            "CRD03": ("资料袋由小何接收。", "资料袋由小周接收。"),
            "CRD04": ("布袋里装的是钥匙。", "布袋里装的是印章。"),
            "CAR01": ("最初余额是17元。", "最初余额是18元。"),
            "CAR02": ("应该配12克粉。", "应该配18克粉。"),
            "CAR03": ("应记录16克。", "应记录18克。"),
            "CAR04": ("买了3张儿童票。", "买了4张儿童票。"),
            "CRL01": ("袋丙位于箱甲里面。", "袋丙位于箱丁里面。"),
            "CRL02": ("绿点更靠左。", "蓝点更靠左。"),
            "CRL03": ("铜牌应该放进甲柜。", "铜牌应该放进乙柜。"),
            "CRL04": ("甲绳更长。", "丙绳更长。"),
        }
        for row in self.panels["confirmation"]:
            self.assertEqual(row["choices"][row["target_index"]], answers[row["base_id"]][row["fact_version"]])
            self.assertEqual(row["demand"], "required")
        self.assertEqual([14 - 2 + 5, 15 - 2 + 5], [17, 18])
        self.assertEqual([8 // 4 * 6, 12 // 4 * 6], [12, 18])
        self.assertEqual([(14 + 18) // 2, (14 + 22) // 2], [16, 18])
        self.assertEqual([(31 - 2 * 8) // 5, (36 - 2 * 8) // 5], [3, 4])

    def test_anchors_keep_original_prompt_and_common_instruction(self):
        original = json.loads((task_data.SURVEY / "questions.json").read_text(encoding="utf-8"))
        instruction = json.loads((task_data.SURVEY / "contract.json").read_text(encoding="utf-8"))["instruction"]
        anchors = self.panels["anchors"]
        self.assertEqual([r["id"] for r in anchors], [f"Q{i:02d}" for i in range(1, 9)])
        self.assertEqual([{k: r[k] for k in ("id", "prompt")} for r in anchors], original)
        for row in anchors:
            self.assertEqual(row["user_message"], instruction + "\n\n" + row["prompt"])
            self.assertEqual(row["choices"], [])
        self.assertFalse(any(r["id"].startswith(tuple(f"Q{i:02d}" for i in range(25, 41)))
                             for rows in self.panels.values() for r in rows))

    def test_prepare_is_reproducible_and_refuses_changed_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self.assertEqual(task_data.prepare(path), {"development": 24, "confirmation": 24, "anchors": 8})
            before = {p.name: p.read_bytes() for p in path.glob("*.json")}
            task_data.prepare(path)
            self.assertEqual(before, {p.name: p.read_bytes() for p in path.glob("*.json")})
            (path / "confirmation.json").write_text("[]\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Refusing to overwrite"):
                task_data.prepare(path)
            self.assertEqual((path / "confirmation.json").read_text(), "[]\n")


if __name__ == "__main__":
    unittest.main()
