"""Read-only audit of existing outputs. Never loads a model or executes completions."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
import score_results as scorer
from prepare_panel import validate_pair

read = lambda p: json.loads(p.read_text())
sha = scorer.sha
protocol = read(root / "protocol.json")
manifest = read(root / "panel_manifest.json")
finish = read(root / "finish-r01/receipt.json")
summary_path = root / "finish-r01/scores/summary.json"
summary = read(summary_path)
assert finish["status"] == summary["status"] == "completed"
assert all(step["status"] == "completed" and step["exit_code"] == 0 for step in finish["steps"])
assert [step["name"] for step in finish["steps"]] == ["humaneval", "scoring"]
for name, digest in finish["frozen_sha256"].items():
    assert sha(root / name) == digest
for name, digest in finish["artifacts_sha256"].items():
    assert sha(root / "finish-r01" / name) == digest
for name, digest in summary["inputs_sha256"].items():
    assert sha(Path(name)) == digest
assert sha(root / "panel_manifest.json") == protocol["panel_manifest_sha256"]
items = {}
for task, entry in manifest["files"].items():
    path = root / entry["file"]
    assert sha(path) == entry["sha256"]
    selected = scorer.read_rows(path)
    assert len(selected) == entry["count"] == protocol["counts"][task]
    items.update({item["id"]: item for item in selected})

paths = scorer.record_paths([root / "outputs"])
rows = [row for path in paths for row in scorer.read_rows(path)]
scorer.validate_records(rows)
reuse = scorer.validate_reuse(paths, rows, root)
raw = {row["id"]: row for row in rows}
assert len(items) == len(raw) == 1400 and set(raw) == set(items)
assert all(row["item"] == items[row["id"]] for row in rows)
assert sum(len(row["outputs"]) for row in rows) == 2800
receipt_checks, reused_ids, new_ids = [], [], []
for path in sorted((root / "outputs").glob("*-shard*-r01/receipt.json")):
    receipt = read(path)
    assert receipt["status"] == "completed" and receipt["hooks_removed"] is True
    assert receipt["target_weight_sha256_after"] == receipt["engine"]["target_weight_sha256_before"]
    assert receipt["completed_pairs"] == receipt["expected_pairs"] == receipt["new_pairs"] + receipt["reused_pairs"]
    assert len(receipt["new_ids"]) == receipt["new_pairs"] and len(receipt["reused_ids"]) == receipt["reused_pairs"]
    assert receipt["protocol_sha256"] == sha(root / "protocol.json")
    assert receipt["panel_manifest_sha256"] == sha(root / "panel_manifest.json")
    assert receipt["reuse_manifest_sha256"] == sha(root / "reuse_manifest.json")
    assert receipt["source_sha256"] == protocol["source_sha256"]
    preflight = read(root / protocol["preflight"][receipt["shard_index"]]["file"])
    assert receipt["engine"] == preflight["engine"] and receipt["assets"] == preflight["assets"]
    ids = receipt["new_ids"] + receipt["reused_ids"]
    assert len(ids) == len(set(ids)) == receipt["completed_pairs"]
    for identity in ids:
        validate_pair(raw[identity], items[identity], receipt["engine"])
    reused_ids += receipt["reused_ids"]
    new_ids += receipt["new_ids"]
    receipt_checks.append({"file": str(path.relative_to(root)), "sha256": sha(path), "n": len(ids),
                           "new": receipt["new_pairs"], "reused": receipt["reused_pairs"], "hooks_removed": True,
                           "target_weights_unchanged": True})
assert len(receipt_checks) == 8 and set(reused_ids + new_ids) == set(raw)
assert len(reused_ids + new_ids) == len(set(reused_ids + new_ids)) == 1400
assert set(reused_ids) == set(read(root / "reuse_manifest.json")["entries"])
for index in range(2):
    worker = read(root / f"worker-{index}.json")
    assert worker["status"] == "completed"
    assert [task["task"] for task in worker["tasks"]] == protocol["task_orders"][str(index)]
    assert all(task["status"] == "completed" and task["exit_code"] == 0 for task in worker["tasks"])

human_path = root / "finish-r01/humaneval-execution.jsonl"
human_receipt = read(human_path.with_suffix(".jsonl.receipt.json"))
human = {(r["id"], r["arm"]): r for r in scorer.read_rows(human_path)}
assert len(human) == human_receipt["count"] == 200
assert human_receipt["status"] == "completed" and human_receipt["controls_passed"] and not human_receipt["self_test"]
assert human_receipt["checker_timeout_seconds"] == 3
assert human_receipt["output_sha256"] == sha(human_path)
for name, key in (("humaneval_sandbox.py", "driver_sha256"), ("humaneval_worker.py", "worker_sha256")):
    assert sha(root / name) == human_receipt[key]
official = root.parents[1] / ".runtime/human-eval"
assert subprocess.check_output(["git", "-C", str(official), "rev-parse", "HEAD"], text=True).strip() == human_receipt["humaneval_commit"] == scorer.HUMANEVAL_COMMIT
checker = official / "human_eval/execution.py"
assert sha(checker) == human_receipt["execution_sha256"]
assert checker.read_bytes() == subprocess.check_output(["git", "-C", str(official), "show", scorer.HUMANEVAL_COMMIT + ":human_eval/execution.py"])
assert sha(root.parents[1] / ".runtime/bubblewrap/root/usr/bin/bwrap") == human_receipt["bwrap_sha256"]
control_path = human_path.with_suffix(".jsonl.controls.jsonl")
assert sha(control_path) == human_receipt["controls_sha256"]
controls = scorer.read_rows(control_path)
expected = {"success": "passed", "wrong": "test_failure", "syntax": "syntax_error", "timeout": "timeout", "isolation": "passed"}
assert len(controls) == 5 and {r["id"]: r["category"] for r in controls} == expected
assert all(r["status"] == "completed" for r in controls)
for (identity, arm), execution in human.items():
    assert execution["status"] == "completed"
    assert execution["completion_sha256"] == scorer.completion_sha(raw[identity]["outputs"][arm]["answer_text"])
    assert execution["problem_sha256"] == scorer.completion_sha(json.dumps(items[identity]["doc"], ensure_ascii=False, sort_keys=True, separators=(",", ":")))

def normalize(text):
    for pattern in (",", r"\$", "(?s).*#### ", r"\.$"):
        text = re.sub(pattern, "", text)
    return text.lower()

scores = scorer.read_rows(root / "finish-r01/scores/scores.jsonl")
assert len(scores) == len({row["id"] for row in scores}) == 1400
assert {row["id"] for row in scores} == set(raw)
for row in scores:
    item = items[row["id"]]
    for arm, result in row["outputs"].items():
        output = raw[row["id"]]["outputs"][arm]
        if row["benchmark"] in ("mmlu", "arc_challenge"):
            values = output["choice_loglikelihoods"]
            assert all(math.isfinite(value) for value in values)
            if row["benchmark"] == "arc_challenge":
                values = [value / len(choice) for value, choice in zip(values, item["choices"])]
            prediction = max(range(len(values)), key=values.__getitem__)
            assert prediction == result["prediction"]
            correct = prediction == item["target_index"]
        elif row["benchmark"] == "gsm8k":
            matches = re.findall(r"#### (\-?[0-9\.\,]+)", output["answer_text"])
            prediction = matches[0].strip() if matches else "[invalid]"
            assert prediction == result["prediction"]
            correct = normalize(prediction) == normalize(item["target"])
            matches = re.findall(r"(-?[$0-9.,]{2,})|(-?[0-9]+)", output["answer_text"])
            flexible = next((value for value in matches[-1] if value), "[invalid]").strip() if matches else "[invalid]"
            assert flexible == result["auxiliary_flexible_prediction"]
            assert (normalize(flexible) == normalize(item["target"])) == result["auxiliary_flexible_correct"]
        else:
            correct = human[row["id"], arm]["passed"]
        assert correct == result["correct"]
        assert output.get("end_reason", "loglikelihood") == result["end_reason"]

population = manifest["mmlu_population_subject_counts"]
assert len(population) == 57 and sum(population.values()) == 14042
full_counts = Counter(row["subject"] for row in scorer.read_rows(scorer.V2 / "items/mmlu.jsonl"))
assert full_counts == population
for task in scorer.EXPECTED:
    selected = [row for row in scores if row["benchmark"] == task]
    # Arithmetic on saved scores only; no official task or generated code is run.
    recomputed = scorer.summarize(selected, population if task == "mmlu" else None)
    assert all(summary["benchmarks"][task][key] == value for key, value in recomputed.items())
for exposure, name in ((False, "gsm8k_unexposed"), (True, "gsm8k_exposed")):
    selected = [row for row in scores if row["benchmark"] == "gsm8k" and row["exposed_in_quick_eval"] == exposure]
    assert scorer.summarize(selected) == summary[name]

compact = {task: {"n": result["n"], "metric": result["metric"], "baseline": result["baseline"], "evo": result["evo"],
                 "damage_percentage_points": result["damage_percentage_points"],
                 "paired_ci95_pp": [result["paired_interval"]["lower_pp"], result["paired_interval"]["upper_pp"]]}
           for task, result in summary["benchmarks"].items()}
report = {"status": "passed", "audit_utc": datetime.now(timezone.utc).isoformat(), "remote_root": str(root),
          "read_only": True, "model_loaded": False, "generated_code_executed": False, "tasks_restarted": False,
          "summary_sha256": sha(summary_path), "scores_sha256": sha(root / "finish-r01/scores/scores.jsonl"),
          "protocol_sha256": sha(root / "protocol.json"), "pairs": 1400, "condition_units": 2800,
          "all_frozen_and_input_artifact_hashes_verified": True, "raw_prediction_crosscheck": "2800/2800 matched",
          "paired_bootstrap_recomputed_from_saved_scores": "Exact match; 10000 repeats; seed 20261026; full MMLU subject weights",
          "humaneval": {"executions": 200, "infrastructure_failures": 0, "controls": expected, "official_commit": scorer.HUMANEVAL_COMMIT,
                        "receipt_sha256": sha(human_path.with_suffix(".jsonl.receipt.json"))},
          "receipts": receipt_checks, "reuse": reuse, "new_pairs": len(new_ids), "reused_pairs": len(reused_ids),
          "benchmarks": compact, "gsm8k_unexposed": summary["gsm8k_unexposed"], "gsm8k_exposed": summary["gsm8k_exposed"],
          "anomalies": [], "limitations": ["Fixed screening panel, not full benchmark scores.",
              "718 MMLU pairs reused byte-identically from interrupted v2; that source run has no final whole-run immutability attestation.",
              "Eight new shard receipts attest target down-projection weight hashes and hook removal, not a new hash of every model tensor.",
              "GSM8K includes 9 historically exposed questions; separate unexposed 91-question scores are preserved.",
              "Capability scores quantify task damage; they do not establish what evil means or a moral-neuron mechanism."]}
print(json.dumps(report, ensure_ascii=False, indent=2))
