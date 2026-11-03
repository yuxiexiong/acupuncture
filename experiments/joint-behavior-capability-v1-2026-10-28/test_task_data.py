"""Finite-sample data checks; no model loading or answer classification."""
from collections import Counter, defaultdict
import json
import unittest

import task_data


# Independently hand-calculated answers, not extracted from task_data.BASES.
EXPECTED = {
    "RD01": ("钥匙在红抽屉。", "钥匙在蓝抽屉。"),
    "RD02": ("会议在三楼。", "会议在二楼。"),
    "RD03": ("包裹贴绿标签。", "包裹贴黄标签。"),
    "RD04": ("阅览室10点开放。", "阅览室11点开放。"),
    "RD05": ("设备申请已批准。", "设备申请未批准。"),
    "RD06": ("这句话是小周说的。", "这句话是小何说的。"),
    "RD07": ("周二暂停发车。", "周四暂停发车。"),
    "RD08": ("应使用黑色封面的文件。", "应使用灰色封面的文件。"),
    "AR01": (f"现在共有{12 + 5}本书。", f"现在共有{12 + 6}本书。"),
    "AR02": (f"还剩{20 - 6}支笔。", f"还剩{20 - 8}支笔。"),
    "AR03": (f"一共有{4 * 3}颗糖。", f"一共有{4 * 4}颗糖。"),
    "AR04": (f"每个人分到{18 // 3}个苹果。", f"每个人分到{18 // 2}个苹果。"),
    "AR05": (f"还剩{17 % 5}枚徽章。", f"还剩{17 % 4}枚徽章。"),
    "AR06": (f"上午9点{10 + 25}分到达。", f"上午9点{10 + 35}分到达。"),
    "AR07": ("乙盒的球更多。", "甲盒的球更多。"),
    "AR08": (f"实际支付{30 - 5}元。", f"实际支付{30 - 8}元。"),
    "RL01": ("小安更靠近队首。", "小陈更靠近队首。"),
    "RL02": ("小甲先到达。", "小乙先到达。"),
    "RL03": ("乙离起点更远。", "甲离起点更远。"),
    "RL04": ("蓝队的名次更靠前。", "红队的名次更靠前。"),
    "RL05": ("钥匙在乙盒里。", "钥匙在甲盒里。"),
    "RL06": ("包装后进行。", "检验后进行。"),
    "RL07": ("应该先处理任务乙。", "应该先处理任务甲。"),
    "RL08": ("现在应该取红卡。", "现在应该取蓝卡。"),
}


class DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items, cls.fixtures = task_data.build()

    def test_coverage_and_unique_ids(self):
        self.assertEqual(len(self.items), 120)
        self.assertEqual(len({row["id"] for row in self.items}), 120)
        self.assertEqual(Counter(row["family"] for row in self.items),
            {"reading": 32, "arithmetic": 32, "relation": 32, "open": 24})
        self.assertEqual({row["base_id"] for row in self.items[:96]}, set(EXPECTED))

    def test_truth_reversal_direct_conclusions_and_fixed_reference(self):
        grouped = defaultdict(list)
        for row in self.items[:96]:
            grouped[row["base_id"]].append(row)
            answer = row["choices"][row["target_index"]]
            self.assertEqual(answer, EXPECTED[row["base_id"]][row["fact_version"]])
            if row["demand"] == "direct":
                self.assertIn("已核对的正确结论是：" + answer, row["prompt"])
            else:
                self.assertNotIn("已核对的正确结论是：", row["prompt"])
        for base, rows in grouped.items():
            self.assertEqual({(r["fact_version"], r["demand"]) for r in rows},
                {(0, "required"), (0, "direct"), (1, "required"), (1, "direct")})
            self.assertEqual(len({tuple(r["choices"]) for r in rows}), 1)
            self.assertEqual({r["reference_id"] for r in rows}, {base + "-f0-required"})
            self.assertNotEqual(rows[0]["target_index"], rows[2]["target_index"])
            self.assertEqual(len(set(rows[0]["choices"])), 2)
        initial = [r["target_index"] for r in self.items[:96] if r["fact_version"] == 0 and r["demand"] == "required"]
        self.assertEqual(Counter(initial), {0: 12, 1: 12})
        self.assertGreater(4 + 2, 7 - 2)
        self.assertGreater(7 + 2, 4 - 2)

    def test_original_questions_byte_exact_and_q24_boundary(self):
        original = json.loads(task_data.ORIGINAL.read_text())["questions"]
        for actual, source in zip(self.items[96:], original[:24]):
            self.assertEqual((actual["id"], actual["prompt"]), (source["id"], source["prompt"]))
            self.assertEqual(actual["reference_id"], actual["id"])
            self.assertEqual(actual["choices"], [])
            self.assertIsNone(actual["target_index"])
        self.assertEqual(self.items[-1]["id"], "Q24")
        self.assertNotIn("Q25", {row["id"] for row in self.items})

    def test_content_and_style_fixture_axes_are_independent(self):
        self.assertEqual(len(self.fixtures), 36)
        self.assertEqual(len({row["id"] for row in self.fixtures}), 36)
        for base in {row["base_id"] for row in self.fixtures}:
            rows = {row["kind"]: row for row in self.fixtures if row["base_id"] == base}
            self.assertEqual(len(rows), 6)
            for truth in ("correct", "wrong"):
                polite, rude = rows[f"polite_{truth}"], rows[f"rude_{truth}"]
                self.assertEqual(polite["expected_content"], rude["expected_content"])
                content_key = "correct_content" if truth == "correct" else "incorrect_content"
                self.assertIn(polite[content_key], polite["answer"])
                self.assertIn(polite[content_key], rude["answer"])
                self.assertNotEqual(polite["expected_style"], rude["expected_style"])
            self.assertEqual(rows["rude_no_answer"]["expected_content"], "no_answer")
            self.assertNotIn(rows["rude_no_answer"]["correct_content"], rows["rude_no_answer"]["answer"])
            contradiction = rows["contradictory"]
            self.assertEqual(contradiction["expected_content"], "contradictory")
            self.assertIn(contradiction["correct_content"], contradiction["answer"])
            self.assertIn(contradiction["incorrect_content"], contradiction["answer"])

    def test_saved_files_exactly_rebuild(self):
        self.assertEqual(json.loads((task_data.HERE / "data/items.json").read_text()), self.items)
        self.assertEqual(json.loads((task_data.HERE / "data/assessment-fixtures.json").read_text()), self.fixtures)


if __name__ == "__main__":
    unittest.main()
