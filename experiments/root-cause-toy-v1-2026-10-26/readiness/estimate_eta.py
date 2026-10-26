"""Read-only ETA from a completed cProfile preflight and frozen token lengths.

No model imports, runs, candidate selection, or scientific outcomes are involved.
The range is a sensitivity range, not a statistical confidence interval.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import pstats
import statistics


HERE = Path(__file__).resolve().parent


def load(path):
    return json.loads(Path(path).read_text())


def profile_entry(stats, filename, function):
    matches = [value for key, value in stats.items()
               if key[0].endswith(filename) and key[2] == function]
    if len(matches) != 1:
        raise ValueError(f"Expected one profile entry for {filename}:{function}")
    return matches[0]


def lengths(rows):
    return [n for row in rows for n in row["input_tokens"]]


def describe(rows):
    values = lengths(rows)
    return {"questions": len(rows), "options": len(values),
            "mean_input_tokens": statistics.mean(values),
            "median_input_tokens": statistics.median(values),
            "min_input_tokens": min(values), "max_input_tokens": max(values)}


def estimate(profile, receipt, metadata, cpu, contract):
    if receipt["status"] != "completed" or receipt["stage"] != "preflight":
        raise ValueError("ETA requires a successfully completed technical preflight")
    stats = pstats.Stats(str(profile)).stats
    score = profile_entry(stats, "root_engine.py", "score_item")
    # The score_item calls made by rank_item are complete, unpatched option
    # scores. Calls from patched_conditions include donor/recipient pairs.
    plain = [value for key, value in score[4].items() if key[2] == "rank_item"]
    if len(plain) != 1:
        raise ValueError("Missing unpatched scoring timing")
    plain_n, plain_seconds = plain[0][1], plain[0][3]
    patch = profile_entry(stats, "run_root.py", "patched_conditions")
    rank = profile_entry(stats, "root_engine.py", "rank_item")
    calibration = profile_entry(stats, "root_engine.py", "calibrate")
    loading = profile_entry(stats, "root_engine.py", "__init__")[3]
    verification = profile_entry(stats, "root_engine.py", "verify_unchanged")[3]
    sets = metadata["sets"]
    dev = sets["dev"]
    sample = [next(row for row in dev if row["benchmark"] == task)
              for task in ("mmlu", "arc_challenge")]
    if plain_n != len(sample) or patch[1] != len(sample) or rank[1] != len(sample):
        raise ValueError("Preflight call counts differ from the frozen two-task design")
    sample_lengths = lengths(sample)
    target_lengths = lengths(dev)
    sample_options = len(sample_lengths)
    options = len(target_lengths)
    linear = statistics.mean(target_lengths) / statistics.mean(sample_lengths)
    quadratic = (statistics.mean(n*n for n in target_lengths) /
                 statistics.mean(n*n for n in sample_lengths))
    boot32 = cpu["cpu_bootstrap"]["32"]["mean_seconds"]
    boot16 = cpu["cpu_bootstrap"]["16"]["mean_seconds"]
    arm_count = 1 + len(contract["diagnostic_doses"]) * (3 + contract["random_pairs"])
    candidates = contract["candidate_budget"]["total"]
    decompose_comparisons = arm_count - 1 + 2 * len(contract["diagnostic_doses"])
    bootstrap_decompose = decompose_comparisons * 2 * 2
    bootstrap_validate = candidates * 4 * 2 * 2

    def stage(name, forward, backward, calibration_count, timed, stats_seconds):
        fixed = loading + verification + stats_seconds
        # Short scoring contexts and patched module positions can change the
        # cost. This explicit sensitivity envelope avoids a blanket 2x buffer.
        central = fixed + timed * linear
        low = fixed + timed * min(1.0, linear, quadratic) * .9
        high = fixed + timed * max(1.0, linear, quadratic) * 1.1
        return {"stage": name, "forward": forward, "backward": backward,
                "calibration_forward": calibration_count,
                "load_and_final_integrity_seconds": loading + verification,
                "statistics_seconds": stats_seconds,
                "estimated_seconds": central, "range_seconds": [low, high]}

    cal_seconds = calibration[3] / calibration[1] * len(dev)
    decompose = stage("decompose", arm_count * options, 0, len(dev),
                      plain_seconds / sample_options * arm_count * options + cal_seconds,
                      bootstrap_decompose * boot32)
    # rank_item includes option scoring, two clean donor forwards, two gradient
    # forwards and two backwards; rank is therefore timed as a complete unit.
    ranking = stage("rank", options + 4 * len(dev), 2 * len(dev), 0,
                    rank[3] / rank[1] * len(dev), 0)
    validation = stage("validate", candidates * 10 * options, 0, 0,
                       patch[3] / sample_options * options * candidates,
                       bootstrap_validate * boot32)
    stages = [decompose, ranking, validation]
    later = {}
    for family in contract["functional"]["families"]:
        function = sets[f"{family}_dev"]
        confirm = sets[f"{family}_confirm"]
        later[family] = {
            "function_dev_per_candidate": {"forward": 14 * len(lengths(function)),
                "bootstrap_calls_16_units": 62, "statistics_seconds": 62 * boot16},
            "confirmation_per_candidate": {
                "forward": 14 * len(lengths(confirm)) + 10 * len(lengths(sets["confirm"])),
                "bootstrap_calls_16_units": 62, "bootstrap_calls_32_units": 16,
                "statistics_seconds": 62 * boot16 + 16 * boot32},
            "function_dev_calibration_shared_across_candidates": len(function),
            "confirmation_calibration_shared_across_candidates": len(confirm) + len(sets["confirm"]),
            "timing_status": "not calibrated: 60-90 token functional inputs differ greatly from the measured long ability prompts"}
    return {"created_at": datetime.now(timezone.utc).isoformat(),
            "status": "measured_preflight_extrapolation_not_a_completion_claim",
            "preflight_wall_seconds": receipt["wall_seconds"],
            "measured_seconds": {"model_load": loading,
                "plain_option_score_per_question": plain_seconds / plain_n,
                "six_condition_validation_per_question": patch[3] / patch[1],
                "ranking_per_question": rank[3] / rank[1],
                "calibration_per_question": calibration[3] / calibration[1]},
            "length_metadata": {"preflight": describe(sample), "dev": describe(dev),
                "linear_multiplier": linear, "quadratic_multiplier": quadratic},
            "stages": stages,
            "first_decision_stage_total": {
                "estimated_seconds": sum(row["estimated_seconds"] for row in stages),
                "range_seconds": [sum(row["range_seconds"][i] for row in stages) for i in (0, 1)],
                "ends_after": "10 candidate validation; scientific interpretation and function hypothesis freeze are not timed"},
            "conditional_later_work": later,
            "limits": [
                "Two preflight questions; range is sensitivity to sequence scaling and 10% run variation, not a confidence interval.",
                "Model loading and final integrity checks are charged separately for each stage; statistics use measured server CPU timing.",
                "Calibration is reused by rank and validate exactly as the existing stage code permits.",
                "Current implementation scores each MMLU option separately; no legacy same-prefix grouping speedup is assumed.",
                "cProfile overhead is retained; no unmeasured speedup is subtracted.",
                "Manual hypothesis choice, later-stage timing calibration, transfers and exceptional failures are not assigned invented durations.",
                "Later functional/confirmation work requires one or two frozen scientific explanations; no automatic scientific decision is implied."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--tokens", type=Path, default=HERE / "eta-token-lengths.json")
    parser.add_argument("--cpu", type=Path, default=HERE / "eta-cpu-timing.json")
    parser.add_argument("--contract", type=Path, default=HERE.parent / "contract.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = estimate(args.profile, load(args.receipt), load(args.tokens), load(args.cpu), load(args.contract))
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"stages": result["stages"], "total": result["first_decision_stage_total"]}))


if __name__ == "__main__":
    main()
