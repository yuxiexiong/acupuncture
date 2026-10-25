"""Honor the user's Q24 boundary without changing the running model or its outputs."""
import hashlib
import json
import os
from pathlib import Path
import signal
import time
from datetime import datetime, timezone

root = Path("raw-corpus-cpu-bf16-r01").resolve()
control = root.parent / "stop-after-q24"
control.mkdir(exist_ok=True)
assert not (control / "receipt.json").exists(), "Boundary control already exists"

def save(value):
    temporary = control / "receipt.tmp"
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(control / "receipt.json")

matches = []
for entry in Path("/proc").iterdir():
    if not entry.name.isdigit():
        continue
    try:
        args = (entry / "cmdline").read_bytes().split(b"\0")
        if b"collect_raw.py" in args and b"raw-corpus-cpu-bf16-r01" in args and (entry / "cwd").resolve() == root.parent:
            matches.append(int(entry.name))
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        pass
assert len(matches) == 1, matches
pid = matches[0]
start_time = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
def send_signal(value):
    assert Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19] == start_time
    os.kill(pid, value)
state = {"status": "installing_boundary", "pid": pid,
         "requested_at": datetime.now(timezone.utc).isoformat(),
         "user_request": "Complete Q24, do not process Q25-Q40, then analyze Q01-Q24.",
         "method": "Temporarily block the pending Q25 record read with a FIFO; terminate only after all Q01-Q24 answers and the progress receipt are saved; restore the exact pending Q25 record."}
save(state)
send_signal(signal.SIGSTOP)
try:
    for _ in range(500):
        if any(line.startswith("State:") and line.split()[1] in ("T", "t") for line in Path(f"/proc/{pid}/status").read_text().splitlines()):
            break
        time.sleep(0.01)
    else:
        raise RuntimeError("Collector did not enter the stopped state")
    receipt = json.loads((root / "receipt.json").read_text())
    assert receipt.get("current_question") == "Q24", receipt.get("current_question")
    assert json.loads((root / "Q24.json").read_text())["status"] == "running", "Q24 is already complete: stop directly instead of installing a late boundary"
    target = root / "Q25.json"
    original = target.read_bytes()
    pending = json.loads(original)
    assert pending["status"] == "pending" and pending["attempts"] == []
    (control / "Q25.original.json").write_bytes(original)
    barrier = control / "Q25.barrier"
    os.mkfifo(barrier, 0o600)
    os.replace(barrier, target)
    state.update({"status": "waiting_for_Q24", "Q25_original_sha256": hashlib.sha256(original).hexdigest()})
    save(state)
finally:
    send_signal(signal.SIGCONT)

while True:
    receipt = json.loads((root / "receipt.json").read_text())
    question = json.loads((root / "Q24.json").read_text())
    if question["status"] == "completed" and receipt["completed_questions"] == [f"Q{i:02d}" for i in range(1, 25)]:
        break
    time.sleep(0.25)

for number in range(1, 25):
    question = json.loads((root / f"Q{number:02d}.json").read_text())
    assert question["status"] == "completed" and question["attempts"]
    assert all(attempt[arm]["status"] == "completed" for attempt in question["attempts"] for arm in ("baseline", "modified"))
send_signal(signal.SIGTERM)
for _ in range(100):
    if not Path(f"/proc/{pid}").exists():
        break
    time.sleep(0.1)
assert not Path(f"/proc/{pid}").exists(), "Collector has not exited; leave Q25 blocked"
restored = control / "Q25.restore"
restored.write_bytes(original)
os.replace(restored, root / "Q25.json")
assert (root / "Q25.json").read_bytes() == original
assert all(json.loads((root / f"Q{number:02d}.json").read_text())["attempts"] == [] for number in range(25, 41))
state.update({"status": "stopped_after_Q24", "ended_at": datetime.now(timezone.utc).isoformat(),
              "completed_questions": receipt["completed_questions"], "Q25_Q40_not_started": True,
              "Q25_original_restored": True, "final_all_40_weight_hash_check_executed": False,
              "question_record_sha256": {f"Q{number:02d}": hashlib.sha256((root / f"Q{number:02d}.json").read_bytes()).hexdigest() for number in range(1, 41)}})
save(state)
print(json.dumps({"status": state["status"], "completed_questions": 24, "later_questions_started": 0}), flush=True)
