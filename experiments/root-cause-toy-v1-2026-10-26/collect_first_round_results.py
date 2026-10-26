"""Read completed evidence into a compact report; never load or rerun a model."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def seconds(start, end):
    return (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds()


def counts(rows, task):
    selected = [row for row in rows if row["benchmark"] == task]
    return {arm: sum(row["conditions"][arm]["correct"] for row in selected)
            for arm in selected[0]["conditions"]}


def main():
    run = HERE / "runs/root-parallel-r01"
    controller = read(HERE / "runs/root-parallel-r01-controller.json")
    receipt = read(run / "receipt.json")
    assert controller["status"] == receipt["status"] == "completed"
    assert controller["worker_exit_codes"] == [0, 0]
    output = {"status": "completed_development_results_not_mechanism_confirmation",
              "source_receipt_sha256": hashlib.sha256((run / "receipt.json").read_bytes()).hexdigest(),
              "question_count_per_task": 32, "independent_confirmation_run": False,
              "candidate_results": []}
    for cid in receipt["candidate_ids"]:
        folder = run / cid
        candidate = read(folder / "candidate.json")
        summary = read(folder / "ability-summary.json")
        rows = [read(folder / f"ability-{i:03d}.json") for i in range(64)]
        result = {"candidate": candidate, "tasks": {}}
        for task, comparisons in summary.items():
            result["tasks"][task] = {
                "correct_counts": counts(rows, task), "comparisons": comparisons,
                "all_four_lower_bounds_positive": {
                    metric: all(c[metric]["ci95"][0] > 0 for c in comparisons.values())
                    for metric in ("margin", "correct")}}
        output["candidate_results"].append(result)
    old = HERE / "runs/root-r01"
    decompose = read(old / "decompose-r01/receipt.json")
    rank = read(old / "rank-r01/receipt.json")
    rows = [read(old / "decompose-r01" / f"item-{i:03d}.json") for i in range(64)]
    output["decomposition_correct_counts"] = {task: counts(rows, task) for task in ("mmlu", "arc_challenge")}
    output["decomposition_comparisons"] = read(old / "decompose-r01/summary.json")
    output["timing"] = {
        "formal_started_at": decompose["started_at"], "completed_at": controller["finished_at"],
        "formal_elapsed_seconds_including_handoff": seconds(decompose["started_at"], controller["finished_at"]),
        "decompose_seconds": decompose["wall_seconds"], "rank_seconds": rank["wall_seconds"],
        "dual_candidate_seconds_including_merge": seconds(controller["started_at"], controller["finished_at"]),
        "dual_worker_seconds_sum_not_gpu_kernel_time": receipt["worker_seconds_sum"],
        "latest_eta_was_beijing": ["2026-10-26 15:52:00", "2026-10-26 16:00:00"],
        "remaining_seconds": 0}
    output["boundaries"] = [
        "Development items were used for ranking and intervention; these intervals are exploratory.",
        "Report all ten candidates and both tasks; no familywise error control is claimed.",
        "Margin changes and accuracy changes are separate readings, not independent replications.",
        "Empty answer-tail positions remain in the fixed denominator and do not demonstrate module irrelevance.",
        "No functional explanation, reader relation, or cross-model mechanism has been confirmed."]
    target = HERE / "first-round-results.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(target), "timing": output["timing"],
                      "all_four": {metric: [(r["candidate"]["id"], task)
                          for r in output["candidate_results"] for task, v in r["tasks"].items()
                          if v["all_four_lower_bounds_positive"][metric]]
                          for metric in ("margin", "correct")}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
