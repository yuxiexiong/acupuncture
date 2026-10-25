"""CPU-only checks of panel counts, full-population weighting, reuse, and finish gates."""
import ast
from copy import deepcopy
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory

import score_results as score
from finish_run import TASKS, commands, dependency_state


def row(identity, baseline, evo, subject):
    return {"id": identity, "subject": subject, "cluster_id": identity,
            "outputs": {arm: {"correct": value, "parse_failed": False, "end_reason": "loglikelihood"}
                        for arm, value in (("baseline", baseline), ("evo", evo))}}


# The sample is 1:9, but the full subject population is 3:1.
rows = [row("0", True, False, "a")] + [row(str(i), False, True, "b") for i in range(1, 10)]
result = score.summarize(rows, {"a": 3, "b": 1})
assert result["baseline"]["score_percent"] == 75
assert result["evo"]["score_percent"] == 25
assert result["baseline"]["unweighted_score_percent"] == 10
assert result["damage_percentage_points"] == 50
assert result["paired_interval"]["lower_pp"] == result["paired_interval"]["upper_pp"] == 50
assert math.isclose(score.summarize(rows)["damage_percentage_points"], -80)
assert score.paired_interval(rows, {"a": 3, "b": 1}) == score.paired_interval(rows, {"a": 3, "b": 1})
try:
    score.summarize(rows, {"a": 3, "b": 1, "missing": 1})
except AssertionError:
    pass
else:
    raise AssertionError("Missing subject accepted")

records = [{"id": f"{task}/{i}", "benchmark": task, "status": "completed",
            "item": {"id": f"{task}/{i}", "benchmark": task},
            "outputs": {arm: {"status": "completed"} for arm in score.ARMS}}
           for task, count in score.EXPECTED.items() for i in range(count)]
assert len(records) == 1400 and sum(len(row["outputs"]) for row in records) == 2800
score.validate_records(records)
bad = deepcopy(records)
bad[0]["outputs"]["evo"]["status"] = "failed"
for candidate in (records[:-1], records + [records[0]], bad):
    try:
        score.validate_records(candidate)
    except AssertionError:
        pass
    else:
        raise AssertionError("Missing/duplicate/infrastructure failure accepted")

done = [{"status": "completed", "tasks": [{"task": task, "status": "completed", "exit_code": 0} for task in order]} for order in TASKS]
assert dependency_state(done)[0] == "ready"
assert dependency_state([done[0], {"status": "started", "tasks": []}])[0] == "waiting"
assert dependency_state([None, {"status": "failed", "tasks": []}])[0] == "failed"
assert dependency_state([done[1], done[0]])[0] == "failed"

with TemporaryDirectory() as directory:
    root, old = Path(directory) / "v3", Path(directory) / "v2"
    root.mkdir(); old.mkdir()
    (old / "protocol.json").write_text("{}")
    (old / "receipt.json").write_text('{"status":"stopped"}')
    (root / "stop.json").write_text('{"stopped":true}')
    path = root / "outputs/mmlu-shard0-r01/00000.jsonl"
    path.parent.mkdir(parents=True)
    data = json.dumps(records[0]) + "\n"
    path.write_text(data)
    (old / "00000.jsonl").write_text(data)
    reuse = {"source_root": "../v2", "source_protocol_sha256": score.sha(old / "protocol.json"),
             "stop_receipt": {"file": "stop.json", "sha256": score.sha(root / "stop.json")},
             "counts": {"mmlu": 1}, "entries": {records[0]["id"]: {"task": "mmlu", "source_file": "00000.jsonl",
                 "sha256": score.sha(path), "source_receipt_file": "receipt.json", "source_receipt_sha256": score.sha(old / "receipt.json")}}}
    (root / "reuse_manifest.json").write_text(json.dumps(reuse))
    (root / "protocol.json").write_text(json.dumps({"reuse_manifest_sha256": score.sha(root / "reuse_manifest.json")}))
    actual_v2 = score.V2
    score.V2 = old
    assert score.validate_reuse([path], [records[0]], root)["counts"] == {"mmlu": 1}
    path.write_text(data + "\n")
    try:
        score.validate_reuse([path], [records[0]], root)
    except AssertionError:
        pass
    else:
        raise AssertionError("Modified raw reuse bytes accepted")
    score.V2 = actual_v2
    human, aggregate = commands(root)
    assert "humaneval_sandbox.py" in human[2] and "score_results.py" in aggregate[2]
    assert aggregate[aggregate.index("--manifest") + 1].endswith("panel_manifest.json")
    assert all("run_benchmarks.py" not in part for command in (human, aggregate) for part in command)

for name in ("score_results.py", "humaneval_sandbox.py", "humaneval_worker.py", "finish_run.py"):
    ast.parse(Path(__file__).with_name(name).read_text())
root = Path(__file__).resolve().parent
old_scorer = ast.parse((score.V2 / "score_results.py").read_text())
new_scorer = ast.parse((root / "score_results.py").read_text())
official = lambda tree: ast.dump(next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "OfficialScorer"))
assert official(old_scorer) == official(new_scorer)
assert (root / "humaneval_sandbox.py").read_text() == (score.V2 / "humaneval_sandbox.py").read_text().replace("== 164", "== 100")
assert (root / "humaneval_worker.py").read_bytes() == (score.V2 / "humaneval_worker.py").read_bytes()
print("PASS: 1400 pairs / 2800 units, full-subject MMLU weights and paired interval, raw reuse hashes, per-worker task order, CPU-only finish")
