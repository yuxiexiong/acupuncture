"""Synthetic dependency checks; never invoke inference or code execution."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

from finish_run import TASKS, commands, dependency_state

done = {"status": "completed", "tasks": [{"task": task, "status": "completed", "exit_code": 0} for task in TASKS]}
started = {"status": "started", "tasks": [{"task": "mmlu", "status": "started"}]}
failed = {"status": "failed", "tasks": []}
assert dependency_state([None, started])[0] == "waiting"
assert dependency_state([done, started])[0] == "waiting"
assert dependency_state([done, done])[0] == "ready"
assert dependency_state([None, failed])[0] == "failed"
bad = deepcopy(done)
bad["tasks"][-1]["exit_code"] = 1
assert dependency_state([done, bad])[0] == "failed"
bad = deepcopy(done)
bad["tasks"].pop()
assert dependency_state([bad, done])[0] == "failed"
with TemporaryDirectory() as directory:
    root = Path(directory) / "experiments/run"
    for shard in range(2):
        path = root / "outputs" / f"humaneval-shard{shard}-r01"
        path.mkdir(parents=True)
        (path / "00000.jsonl").write_text("{}\n")
        (path / "partial.json").write_text("{}")
    human, score = commands(root)
    files = human[human.index("--records") + 1:human.index("--output")]
    assert len(files) == 2 and all(p.endswith("00000.jsonl") for p in files)
    assert human[2].endswith("humaneval_sandbox.py") and score[2].endswith("score_results.py")
    assert score[score.index("--records") + 1] == str(root / "outputs")
    assert not any("run_worker.py" in part or "run_benchmarks.py" in part for command in (human, score) for part in command)
print("PASS: two-worker dependency gate, failure precedence, complete task receipts, HumanEval file selection, CPU-only commands")
