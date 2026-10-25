"""Verify both transfer benchmark shards, sandbox HumanEval, then reuse v3 scoring."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from run_benchmark import (ARM_NAMES, COUNTS, ORDER, PANEL_SHA, PROTOCOL_SHA, ROOT, V3,
                           frozen_panel, load_v3, read, rows, sha, utc, validate_pair, write)


def verified_records(output, items):
    frozen = {item["id"]: item for group in items.values() for item in group}
    records, paths, receipts = [], [], []
    for index in range(2):
        directory = output / f"shard-{index}"
        receipt_path = directory / "receipt.json"
        receipt = read(receipt_path)
        assert receipt["status"] == "completed" and receipt["completed_pairs"] == receipt["expected_pairs"] == 700
        assert receipt["shard_index"] == index and receipt["shard_count"] == 2
        assert receipt["protocol_sha256"] == PROTOCOL_SHA and receipt["panel_manifest_sha256"] == PANEL_SHA
        assert receipt["arm_bindings"] == ARM_NAMES and receipt["task_order"] == list(ORDER[index])
        assert receipt["hooks_removed"]
        assert receipt["target_weight_sha256_after"] == receipt["engine"]["target_weight_sha256_before"]
        for path, digest in receipt["source_sha256"].items():
            assert sha(path) == digest, f"Execution source or conditions changed: {path}"
        assert not list(directory.glob("*/*.partial.json")), "Unfinished pairs remain"
        for task, count in COUNTS.items():
            state = receipt["tasks"][task]
            assert state["status"] == "completed" and state["completed_pairs"] == count // 2
            files = sorted((directory / task).glob("[0-9]*.jsonl"))
            assert len(files) == count // 2
            expected = items[task][index::2]
            for path, item in zip(files, expected):
                assert sha(path) == receipt["records_sha256"][str(path.relative_to(directory))]
                content = rows(path)
                assert len(content) == 1
                row = content[0]
                validate_pair(row, item)
                assert row["transfer_provenance"] == {"model": receipt["model"],
                    "conditions_sha256": receipt["conditions_sha256"], "arm_bindings": ARM_NAMES}
                paths.append(path)
                records.append(row)
        receipts.append(receipt)
    for key in ("model", "conditions_sha256", "model_small_file_sha256", "source_sha256"):
        assert receipts[0][key] == receipts[1][key], f"Shard identity mismatch: {key}"
    assert len(records) == len({row["id"] for row in records}) == 1400
    assert set(frozen) == {row["id"] for row in records}
    assert Counter(row["benchmark"] for row in records) == COUNTS
    return records, paths, receipts


def sandbox_command(project, paths, execution):
    human = [path for path in paths if path.parent.name == "humaneval"]
    assert len(human) == 100
    return [sys.executable, "-u", str(V3 / "humaneval_sandbox.py"),
            "--bwrap", str(project / ".runtime/bubblewrap/root/usr/bin/bwrap"),
            "--official", str(project / ".runtime/human-eval"),
            "--python-prefix", "/workspace/miniconda/envs/amic-q3",
            "--records", *map(str, human), "--output", str(execution)]


def score_records(records, manifest, execution, harness, cache_dir):
    score = load_v3("score_results")
    score.validate_records(records)
    human_receipt = read(execution.with_suffix(execution.suffix + ".receipt.json"))
    assert human_receipt["status"] == "completed" and human_receipt["controls_passed"]
    assert human_receipt["count"] == 200 and not human_receipt["self_test"]
    assert human_receipt["humaneval_commit"] == score.HUMANEVAL_COMMIT
    assert human_receipt["output_sha256"] == sha(execution)
    assert human_receipt["driver_sha256"] == sha(V3 / "humaneval_sandbox.py")
    assert human_receipt["worker_sha256"] == sha(V3 / "humaneval_worker.py")
    controls = execution.with_suffix(execution.suffix + ".controls.jsonl")
    assert human_receipt["controls_sha256"] == sha(controls)
    human_rows = rows(execution)
    human = {(row["id"], row["arm"]): row for row in human_rows}
    assert len(human) == len(human_rows) == 200
    official, scored = score.OfficialScorer(harness, cache_dir), []
    for row in records:
        item = row["item"]
        result = {"id": row["id"], "benchmark": row["benchmark"],
                  "cluster_id": item["context_sha256"], "outputs": {}}
        for key in ("subject", "exposed_in_quick_eval"):
            if key in item:
                result[key] = item[key]
        for arm in score.ARMS:
            output = row["outputs"][arm]
            if item["benchmark"] == "humaneval":
                tested = human[row["id"], arm]
                assert tested["status"] == "completed", "Infrastructure failure cannot be scored as model error"
                assert tested["completion_sha256"] == score.completion_sha(output["answer_text"])
                assert tested["problem_sha256"] == score.completion_sha(json.dumps(item["doc"], ensure_ascii=False, sort_keys=True, separators=(",", ":")))
                parsed = {"correct": tested["passed"], "metric": "pass@1", "parse_failed": False,
                          "execution_category": tested["category"], "execution_result": tested["result"]}
            else:
                parsed = official.score(item, output)
            result["outputs"][arm] = {**parsed, "end_reason": output.get("end_reason", "loglikelihood")}
        scored.append(result)
    summaries = {}
    for task in COUNTS:
        selected = [row for row in scored if row["benchmark"] == task]
        summaries[task] = {"metric": score.METRICS[task], "expected_n": COUNTS[task],
            **score.summarize(selected, manifest["mmlu_population_subject_counts"] if task == "mmlu" else None)}
    return scored, summaries


def run(args):
    protocol, panel, items = frozen_panel()
    records, paths, workers = verified_records(args.output, items)
    destination = args.output / args.finish_name
    destination.mkdir(exist_ok=False)
    receipt_path = destination / "receipt.json"
    started = time.monotonic()
    receipt = {"status": "started", "started_utc": utc(), "pid": os.getpid(),
               "model": workers[0]["model"], "conditions_sha256": workers[0]["conditions_sha256"],
               "arm_bindings": ARM_NAMES, "protocol_sha256": PROTOCOL_SHA,
               "panel_manifest_sha256": PANEL_SHA, "source_sha256": sha(Path(__file__)),
               "worker_receipts_sha256": {str(index): sha(args.output / f"shard-{index}/receipt.json") for index in range(2)},
               "inference_pairs": 1400, "condition_units": 2800, "steps": []}
    write(receipt_path, receipt)
    try:
        execution = destination / "humaneval-execution.jsonl"
        command = sandbox_command(args.project, paths, execution)
        step = {"name": "humaneval", "started_utc": utc(), "command": command}
        receipt["steps"].append(step)
        write(receipt_path, receipt)
        environment = {**os.environ, "HF_HOME": str(args.project / ".cache/hf"),
            "HF_HUB_OFFLINE": "1", "HF_DATASETS_OFFLINE": "1", "CUDA_VISIBLE_DEVICES": "",
            "OMP_NUM_THREADS": "4", "PYTHONDONTWRITEBYTECODE": "1"}
        with (destination / "humaneval.log").open("xb") as stream:
            process = subprocess.run(command, cwd=ROOT, env=environment, stdout=stream, stderr=subprocess.STDOUT)
        step.update(exit_code=process.returncode, ended_utc=utc())
        write(receipt_path, receipt)
        assert process.returncode == 0, "HumanEval sandbox failed; all records retained"
        os.environ.update({key: environment[key] for key in ("HF_HOME", "HF_HUB_OFFLINE", "HF_DATASETS_OFFLINE")})
        step = {"name": "official_scoring", "started_utc": utc(),
                "official_scorer_sha256": sha(V3 / "score_results.py")}
        receipt["steps"].append(step)
        write(receipt_path, receipt)
        scored, summaries = score_records(records, panel, execution,
            args.project / ".runtime/lm-evaluation-harness", args.project / ".cache/hf/datasets")
        (destination / "scores.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in scored))
        summary = {"status": "completed", "created_utc": utc(), "model": receipt["model"],
                   "conditions_sha256": receipt["conditions_sha256"], "arm_bindings": ARM_NAMES,
                   "benchmarks": summaries, "technical_failures": 0,
                   "harness_commit": protocol["scoring"]["harness_commit"],
                   "fixed_panel_manifest_sha256": PANEL_SHA,
                   "source_scorer_sha256": sha(V3 / "score_results.py"),
                   "scope": "Fixed latest 1400-item capability panel; behavior ratings are separate."}
        write(destination / "summary.json", summary)
        step.update(status="completed", ended_utc=utc())
        frozen_panel()
        verified_records(args.output, items)
        receipt.update(status="completed", input_sha256={str(path): sha(path) for path in paths})
    except Exception as error:
        receipt.update(status="failed", error=str(error), traceback=traceback.format_exc())
        raise
    finally:
        receipt.update(ended_utc=utc(), wall_seconds=time.monotonic() - started,
                       artifacts_sha256={str(path.relative_to(destination)): sha(path)
                           for path in sorted(destination.rglob("*")) if path.is_file() and path != receipt_path})
        write(receipt_path, receipt)
        print(json.dumps({"status": receipt["status"], "receipt": str(receipt_path)}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Shared benchmark output directory")
    parser.add_argument("--project", type=Path, default=ROOT.parents[1])
    parser.add_argument("--finish-name", default="finish-r01", help="New directory for each explicit technical retry")
    run(parser.parse_args())


if __name__ == "__main__":
    main()
