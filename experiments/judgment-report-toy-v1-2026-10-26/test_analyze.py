"""Meaningful analysis checks using synthetic scores; no model dependencies."""
import copy
import unittest

from analyze import CONDITIONS, summarize, validate


def output(target, prediction):
    scores = [0.0] * 4
    scores[prediction] = 1.0
    return {"scores": scores, "margin": scores[target] - max(scores[j] for j in range(4) if j != target),
            "prediction": prediction, "correct": prediction == target}


def records():
    result = []
    for panel, count in (("mmlu_rotation", 32), ("comparison", 16)):
        for number in range(count):
            base = f"{panel}-{number}"
            target_content = number % 4
            for demand in (("required",) if panel == "mmlu_rotation" else ("required", "direct")):
                for rotation in range(4):
                    order = [(j + rotation) % 4 for j in range(4)]
                    target = order.index(target_content)
                    row = {"id": f"{base}-{demand}-{rotation}", "base_id": base, "pair_id": base,
                        "panel": panel, "demand": demand, "rotation": rotation, "order": order,
                        "target_index": target, "target_content_index": target_content}
                    # Clean follows content. AB always says D only when judgment is required.
                    ab = 3 if demand == "required" else target
                    row["conditions"] = {condition: output(target,
                        ab if condition in ("AB_d1", "replay", "control_repair") else target)
                        for condition in CONDITIONS}
                    result.append(row)
    return result


class AnalysisTests(unittest.TestCase):
    def test_label_bias_and_base_clustering(self):
        report = summarize(records(), draws=100)
        panel = report["panels"]["mmlu_rotation"]["required"]
        self.assertEqual(panel["base_count"], 32)
        self.assertEqual(panel["variant_count"], 128)
        self.assertEqual(panel["conditions"]["clean"]["content_consistent_base_rate"], 1)
        self.assertEqual(panel["conditions"]["clean"]["label_consistent_base_rate"], 0)
        self.assertEqual(panel["conditions"]["AB_d1"]["content_consistent_base_rate"], 0)
        self.assertEqual(panel["conditions"]["AB_d1"]["label_consistent_base_rate"], 1)
        self.assertEqual(panel["AB_minus_clean_D_rate"]["effect"], .75)
        self.assertEqual(panel["AB_minus_clean_D_rate"]["unit_count"], 32)
        interaction = report["required_minus_direct_contrast_interactions"]["repair_vs_AB"]["correct"]
        self.assertEqual(interaction["effect"], .75)
        self.assertEqual(interaction["unit_count"], 16)

    def test_net_replay_zero_does_not_hide_turnovers(self):
        rows = records()
        for row in rows:
            t = row["target_index"]
            p = t if row["rotation"] < 2 else (t + 1) % 4
            row["conditions"]["clean"] = output(t, p)
            row["conditions"]["replay"] = output(t, (t + 1) % 4 if row["rotation"] < 2 else t)
        report = summarize(rows, draws=100)["panels"]["mmlu_rotation"]["required"]
        self.assertEqual(report["contrasts"]["replay_damage_vs_clean"]["correct"]["effect"], 0)
        self.assertEqual(report["transitions"]["clean_right_replay_wrong"]["variant_count"], 64)
        self.assertEqual(report["transitions"]["clean_wrong_replay_right"]["variant_count"], 64)

    def test_malformed_grid_and_score_rejected(self):
        rows = records()
        with self.assertRaises(ValueError):
            validate(rows[:-1])
        bad = copy.deepcopy(rows)
        bad[-1] = copy.deepcopy(bad[-2])
        with self.assertRaises(ValueError):
            validate(bad)
        bad = copy.deepcopy(rows)
        bad[0]["conditions"]["clean"]["margin"] = 99
        with self.assertRaises(ValueError):
            validate(bad)
        bad = copy.deepcopy(rows)
        bad[0]["target_content_index"] = (bad[0]["target_content_index"] + 1) % 4
        with self.assertRaises(ValueError):
            validate(bad)

    def test_interpretation_guard_boundaries(self):
        for clean_hits, ab_required_hits, ab_direct_hits, expect_clean, expect_floor in (
                (3, 1, 1, False, True),
                (2, 1, 1, True, True),
                (3, 1, 2, False, False),
                (3, 2, 1, False, False)):
            with self.subTest(clean_hits=clean_hits, ab_required_hits=ab_required_hits, ab_direct_hits=ab_direct_hits):
                rows = records()
                for row in rows:
                    if row["panel"] != "comparison":
                        continue
                    target = row["target_index"]
                    clean_prediction = target if row["rotation"] < clean_hits else (target + 1) % 4
                    ab_hits = ab_required_hits if row["demand"] == "required" else ab_direct_hits
                    ab_prediction = target if row["rotation"] < ab_hits else (target + 1) % 4
                    row["conditions"]["clean"] = output(target, clean_prediction)
                    row["conditions"]["AB_d1"] = output(target, ab_prediction)
                report = summarize(rows, draws=100)
                guards = report["interpretation_guards"]
                self.assertEqual(guards["flags"]["clean_function_accuracy_below_minimum"], expect_clean)
                self.assertEqual(guards["flags"]["both_demands_at_AB_floor"], expect_floor)
                self.assertEqual(guards["observed_accuracy"]["required"]["clean"], clean_hits / 4)
                self.assertEqual(report["variant_count"], 256)


if __name__ == "__main__":
    unittest.main()
