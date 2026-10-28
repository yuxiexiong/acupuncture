"""Stage 1 damage gate. Behavior labels are never inferred from capability scores."""
import argparse
from collections import defaultdict
from pathlib import Path

from common import BENCHMARK_ARMS, read, rows, sha, write, verify_freeze

TASKS = ("mmlu", "arc_challenge", "gsm8k", "humaneval")


def interval(records, population=None):
    import numpy as np
    strata = defaultdict(list)
    for row in records:
        strata[row.get("subject", "all")].append(row)
    counts = population or {key: len(value) for key, value in strata.items()}
    assert set(counts) == set(strata)
    rng = np.random.default_rng(20261026)
    draws, point = np.zeros(10000), 0.0
    for name, group in strata.items():
        clusters = defaultdict(list)
        for row in group:
            clusters[row.get("cluster_id", row["id"])].append(int(row["outputs"]["baseline"]["correct"]) - int(row["outputs"]["evo"]["correct"]))
        sums = np.array([sum(v) for v in clusters.values()])
        sizes = np.array([len(v) for v in clusters.values()])
        weight = counts[name] / sum(counts.values())
        point += weight * sums.sum() / sizes.sum()
        if np.all(sizes == 1):
            values, frequencies = np.unique(sums, return_counts=True)
            draws += weight * rng.multinomial(len(group), frequencies / len(group), size=10000).dot(values) / len(group)
        else:
            for start in range(0, 10000, 128):
                idx = rng.integers(len(sums), size=(min(128, 10000 - start), len(sums)))
                draws[start:start + len(idx)] += weight * sums[idx].sum(1) / sizes[idx].sum(1)
    return {"damage_pp": float(point * 100), "lower_pp": float(np.quantile(draws, .00625) * 100),
        "upper_pp": float(np.quantile(draws, .99375) * 100), "nominal_level": .9875,
        "discordant_pairs": sum(r["outputs"]["baseline"]["correct"] != r["outputs"]["evo"]["correct"] for r in records)}


def decide(metrics):
    assert set(metrics) == set(TASKS)
    passed = [t for t, m in metrics.items() if m["damage_pp"] >= 5 and m["lower_pp"] > 0 and m["discordant_pairs"] > 5]
    if passed:
        return "PASS", passed
    if all(m["upper_pp"] < 5 and m["discordant_pairs"] > 5 for m in metrics.values()):
        return "STOP_SMALL_EFFECT", []
    return "INCONCLUSIVE_HOLD", []


def metrics_from_scores(records):
    from run_benchmark import frozen_panel
    _, panel, items = frozen_panel()
    assert len(records) == len({r["id"] for r in records}) == 1400
    assert {r["id"] for r in records} == {r["id"] for group in items.values() for r in group}
    return {task: interval([r for r in records if r["benchmark"] == task],
        panel["mmlu_population_subject_counts"] if task == "mmlu" else None) for task in TASKS}


def run(args):
    verify_freeze(args.freeze)
    root = Path(args.run)
    directory = root / f"stage{args.stage}/benchmark/finish-r01"
    summary, receipt = read(directory / "summary.json"), read(directory / "receipt.json")
    assert summary["status"] == receipt["status"] == "completed"
    assert summary["technical_failures"] == 0 and summary["arm_bindings"] == {"baseline": "T_0", "evo": BENCHMARK_ARMS[args.stage]}
    assert summary["stage"] == receipt["stage"] == args.stage
    assert summary["freeze_sha256"] == receipt["freeze_sha256"] == sha(args.freeze)
    assert summary["conditions_sha256"] == sha(root / "mapping/bundle.pt")
    for name, digest in receipt["artifacts_sha256"].items():
        assert sha(directory / name) == digest
    quality = read(root / "mapping/quality.json")
    assert quality["status"] == "PASS" and quality["freeze_sha256"] == sha(args.freeze)
    assert quality["bundle_sha256"] == sha(root / "mapping/bundle.pt")
    metrics = metrics_from_scores(rows(directory / "scores.jsonl"))
    decision, passed = decide(metrics)
    evidence = [directory / n for n in ("scores.jsonl", "summary.json", "receipt.json")] + [root / "mapping/quality.json"]
    result = {"decision": decision, "stage": args.stage, "qualifying_tasks": passed, "metrics": metrics,
        "primary_arm": BENCHMARK_ARMS[args.stage], "threshold_pp": 5, "bootstrap_repeats": 10000,
        "multiplicity": "Bonferroni 4 x nominal 98.75% paired percentile intervals; approximate coverage",
        "scope": "Operational gate for this fixed recipe and panel, not proof of a shared mechanism or global impossibility",
        "bundle_sha256": sha(root / "mapping/bundle.pt"), "freeze_sha256": sha(args.freeze),
        "evidence_sha256": {str(p.relative_to(root)): sha(p) for p in evidence}}
    assert not (root / f"stage{args.stage}/gate.json").exists(), "Gate is immutable; use a new versioned run for repairs"
    write(root / f"stage{args.stage}/gate.json", result)
    print(decision)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", required=True); p.add_argument("--freeze", required=True)
    p.add_argument("--stage", type=int, choices=(1, 2), required=True)
    run(p.parse_args())
