"""Descriptive, base-paired analysis of the frozen judgment/report toy.

Rotated variants are repeated measurements, never independent samples. This
module reads scores only; it cannot load a model or certify a mechanism.
"""
from collections import Counter, defaultdict
import importlib.util
import json
import math
from pathlib import Path
import statistics

_spec = importlib.util.spec_from_file_location(
    "root_toy_metrics", Path(__file__).resolve().parents[1] /
    "root-cause-toy-v1-2026-10-26/metrics.py")
_metrics = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_metrics)

CONDITIONS = ("clean", "AB_d1", "repair", "replay", "control_repair", "control_replay")
CONTRASTS = [("AB_damage", "clean", "AB_d1"), *_metrics.candidate_comparisons()]
SEED = 20261026


def validate(records):
    """Reject incomplete grids, inconsistent labels, and malformed score records."""
    if len(records) != 256 or len({row["id"] for row in records}) != 256:
        raise ValueError("Exactly 256 distinct item records are required")
    groups, panels = defaultdict(list), defaultdict(set)
    for row in records:
        panel, base = row["panel"], row["base_id"]
        if panel not in ("mmlu_rotation", "comparison") or row["pair_id"] != base:
            raise ValueError("Unknown panel or inconsistent paired unit")
        if type(row["rotation"]) is not int or row["rotation"] not in range(4):
            raise ValueError("Invalid rotation")
        order = row["order"]
        if len(order) != 4 or any(type(x) is not int for x in order) or sorted(order) != list(range(4)):
            raise ValueError("Display-to-content order must be a permutation")
        target = row["target_index"]
        if type(target) is not int or target not in range(4) or order[target] != row["target_content_index"]:
            raise ValueError("Target label does not identify the correct content")
        if set(row["conditions"]) != set(CONDITIONS):
            raise ValueError("Every item needs all six frozen conditions")
        for output in row["conditions"].values():
            scores, prediction = output["scores"], output["prediction"]
            if len(scores) != 4 or not all(math.isfinite(x) for x in scores):
                raise ValueError("Four finite option scores are required")
            if type(prediction) is not int or prediction != max(range(4), key=scores.__getitem__):
                raise ValueError("Prediction disagrees with the frozen tie-breaking rule")
            if output["correct"] not in (True, False, 0, 1) or bool(output["correct"]) != (prediction == target):
                raise ValueError("Incorrect saved correctness")
            margin = scores[target] - max(scores[j] for j in range(4) if j != target)
            if not math.isfinite(output["margin"]) or not math.isclose(margin, output["margin"], rel_tol=1e-9, abs_tol=1e-9):
                raise ValueError("Incorrect saved margin")
        panels[panel].add(base)
        groups[(panel, base)].append(row)
    if {key: len(value) for key, value in panels.items()} != {"mmlu_rotation": 32, "comparison": 16}:
        raise ValueError("Frozen base counts are MMLU 32 and comparison 16")
    if panels["mmlu_rotation"] & panels["comparison"]:
        raise ValueError("Base identifiers must distinguish panels")
    for (panel, _), rows in groups.items():
        demands = ("required",) if panel == "mmlu_rotation" else ("required", "direct")
        if Counter((r["demand"], r["rotation"]) for r in rows) != Counter((d, r) for d in demands for r in range(4)):
            raise ValueError("Missing or duplicate demand/rotation variant")
        if len({r["target_content_index"] for r in rows}) != 1:
            raise ValueError("The correct content must stay fixed within a base")
        for demand in demands:
            variants = [r for r in rows if r["demand"] == demand]
            if sorted(r["target_index"] for r in variants) != list(range(4)):
                raise ValueError("Each base must place its correct content under all four labels")
    return groups


def _effect(records, positive, negative, metric, draws):
    return _metrics.paired_effect(records, positive, negative, metric, seed=SEED, draws=draws)


def _transitions(rows):
    by_base = defaultdict(list)
    for row in rows:
        c = row["conditions"]
        clean, ab, repair, replay = (bool(c[k]["correct"]) for k in ("clean", "AB_d1", "repair", "replay"))
        by_base[row["base_id"]].append({
            "clean_right_AB_wrong": clean and not ab,
            "lost_answer_restored": clean and not ab and repair,
            "new_gain_both_clean_AB_wrong": not clean and not ab and repair,
            "AB_right_repair_wrong": ab and not repair,
            "clean_right_replay_wrong": clean and not replay,
            "clean_wrong_replay_right": not clean and replay,
        })
    keys = next(iter(by_base.values()))[0]
    return {key: {
        "variant_count": sum(value[key] for values in by_base.values() for value in values),
        "base_mean_rate": statistics.mean(statistics.mean(value[key] for value in values) for values in by_base.values()),
        "base_count": len(by_base),
        "variant_denominator": len(rows),
    } for key in keys}


def _panel(rows, draws):
    by_base = defaultdict(list)
    for row in rows:
        by_base[row["base_id"]].append(row)
    conditions = {}
    for condition in CONDITIONS:
        hist = Counter(row["conditions"][condition]["prediction"] for row in rows)
        conditions[condition] = {
            "accuracy": statistics.mean(float(row["conditions"][condition]["correct"]) for row in rows),
            "mean_margin": statistics.mean(row["conditions"][condition]["margin"] for row in rows),
            "label_counts": {chr(65 + i): hist[i] for i in range(4)},
            "D_rate": hist[3] / len(rows),
            "content_consistent_base_rate": statistics.mean(len({r["order"][r["conditions"][condition]["prediction"]] for r in variants}) == 1 for variants in by_base.values()),
            "label_consistent_base_rate": statistics.mean(len({r["conditions"][condition]["prediction"] for r in variants}) == 1 for variants in by_base.values()),
        }
    d_rows = [{"id": row["id"], "pair_id": row["base_id"], "conditions": {
        condition: {"D_selected": int(row["conditions"][condition]["prediction"] == 3)}
        for condition in ("clean", "AB_d1")}} for row in rows]
    return {
        "base_count": len(by_base), "variant_count": len(rows),
        "conditions": conditions,
        "contrasts": {name: {metric: _effect(rows, positive, negative, metric, draws)
            for metric in ("correct", "margin")} for name, positive, negative in CONTRASTS},
        "AB_minus_clean_D_rate": _effect(d_rows, "AB_d1", "clean", "D_selected", draws),
        "transitions": _transitions(rows),
    }


def summarize(records, draws=10000, guards=None):
    if guards is None:
        guards = json.loads(Path(__file__).with_name("contract.json").read_text())["interpretation_guards"]
    groups = validate(records)
    panels = defaultdict(lambda: defaultdict(list))
    for row in records:
        panels[row["panel"]][row["demand"]].append(row)
    interactions = {}
    for name, positive, negative in CONTRASTS:
        paired = []
        for (panel, base), rows in sorted(groups.items()):
            if panel != "comparison":
                continue
            conditions = {}
            for demand in ("required", "direct"):
                variants = [row for row in rows if row["demand"] == demand]
                conditions[demand] = {metric: statistics.mean(
                    float(row["conditions"][positive][metric]) - float(row["conditions"][negative][metric])
                    for row in variants) for metric in ("correct", "margin")}
            paired.append({"id": base, "pair_id": base, "conditions": conditions})
        interactions[name] = {metric: _effect(paired, "required", "direct", metric, draws)
            for metric in ("correct", "margin")}
    panel_reports = {panel: {demand: _panel(rows, draws) for demand, rows in sorted(demands.items())}
        for panel, demands in sorted(panels.items())}
    values = {demand: {condition: panel_reports["comparison"][demand]["conditions"][condition]["accuracy"]
        for condition in ("clean", "AB_d1")} for demand in ("required", "direct")}
    minimum = guards["minimum_clean_function_accuracy_per_demand"]
    floor = guards["joint_AB_floor_accuracy_per_demand"]
    low_clean = [demand for demand, scores in values.items() if scores["clean"] < minimum]
    return {
        "status": "analyzed", "independent_confirmation": False,
        "base_count": len(groups), "variant_count": len(records),
        "panels": panel_reports,
        "required_minus_direct_contrast_interactions": interactions,
        "interpretation_guards": {
            "flags": {"clean_function_accuracy_below_minimum": bool(low_clean),
                      "both_demands_at_AB_floor": all(scores["AB_d1"] <= floor for scores in values.values())},
            "low_clean_demands": low_clean,
            "observed_accuracy": values,
            "thresholds": {"minimum_clean_function_accuracy_per_demand": minimum,
                           "joint_AB_floor_accuracy_per_demand": floor},
            "action": "Interpretation flags only; no data exclusions, automatic reruns, or threshold changes.",
        },
        "interpretation": [
            "All results are exploratory; candidates were selected using previous development data.",
            "A base, not a rotated item or token, is the resampling unit. Interactions pair demands within the same base.",
            "Intervals are descriptive 95% paired bootstrap intervals, without familywise multiplicity control.",
            "A zero-containing interval does not establish equivalence or lack of a pathway.",
            "Fixed-letter and fixed-content rates are diagnostics, not proof of a reporting or reasoning mechanism.",
            "An explicit-answer task still requires reading and answer-to-label mapping; differences are demand dependence, not pure process isolation.",
            "Repair and replay transitions are reported over every frozen variant; no result-conditioned filtering is used.",
        ],
    }
