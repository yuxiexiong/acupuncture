"""Paired toy-experiment estimates; question/pair units, never token counts."""
from collections import defaultdict
import math
import random
import statistics


def choice_metrics(item, loglikelihoods):
    """Use the frozen v3 scoring convention; first index wins an exact tie."""
    if len(loglikelihoods) != len(item["continuations"]):
        raise ValueError("One log likelihood is required per complete option")
    scores = [float(value) for value in loglikelihoods]
    if not all(math.isfinite(value) for value in scores):
        raise ValueError("Non-finite option score")
    if item["benchmark"] == "arc_challenge":
        scores = [value / len(text) for value, text in zip(scores, item["choices"])]
    target = item["target_index"]
    prediction = max(range(len(scores)), key=scores.__getitem__)
    return {"scores": scores, "prediction": prediction, "correct": int(prediction == target),
            "margin": scores[target] - max(value for i, value in enumerate(scores) if i != target)}


def quantile(values, probability):
    ordered = sorted(values)
    index = (len(ordered) - 1) * probability
    lo = int(index)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (index - lo)


def paired_effect(records, positive, negative, metric, *, seed=20261026, draws=10000):
    """Average variants within pair first, then resample independent units."""
    if not records or draws < 100:
        raise ValueError("Need nonempty paired records and at least 100 bootstrap draws")
    by_unit = defaultdict(list)
    seen = set()
    for row in records:
        if row["id"] in seen:
            raise ValueError("Duplicate item, which would inflate the denominator")
        seen.add(row["id"])
        a, b = row["conditions"][positive][metric], row["conditions"][negative][metric]
        if not math.isfinite(a) or not math.isfinite(b):
            raise ValueError("Non-finite paired outcome")
        by_unit[row.get("pair_id") or row["id"]].append(float(a) - float(b))
    units = [statistics.mean(values) for _, values in sorted(by_unit.items())]
    rng = random.Random(seed)
    samples = [statistics.mean(rng.choices(units, k=len(units))) for _ in range(draws)]
    return {"effect": statistics.mean(units), "ci95": [quantile(samples, .025), quantile(samples, .975)],
            "unit_count": len(units), "item_count": len(records), "positive": positive,
            "negative": negative, "metric": metric, "method": "paired percentile bootstrap of question/pair means",
            "seed": seed, "draws": draws,
            "interpretation": "A zero-containing interval is inconclusive; it does not establish equivalence."}


def summarize(records, comparisons, *, seed=20261026, draws=10000):
    """Comparisons are explicit tuples (name, positive arm, negative arm)."""
    groups = defaultdict(list)
    for row in records:
        groups[row["benchmark"]].append(row)
    return {benchmark: {name: {metric: paired_effect(rows, positive, negative, metric,
                seed=seed, draws=draws) for metric in ("correct", "margin")}
            for name, positive, negative in comparisons}
            for benchmark, rows in sorted(groups.items())}


def candidate_comparisons(repair="repair", replay="replay", control_repair="control_repair",
                          control_replay="control_replay"):
    """Positive always means support in the preregistered causal direction."""
    return [("repair_vs_AB", repair, "AB_d1"),
            ("repair_vs_matched_control", repair, control_repair),
            ("replay_damage_vs_clean", "clean", replay),
            ("replay_damage_vs_matched_control", control_replay, replay)]


def task_evidence(summary):
    """Task endpoint only. This cannot certify an unpatched mechanistic relation."""
    checks = [result["correct"]["ci95"][0] > 0 for result in summary.values()]
    return {"task_endpoint_supported": bool(checks) and all(checks),
            "mechanism_confirmed": False,
            "reason": "Independent unpatched-reader and functional tests are still required."}
