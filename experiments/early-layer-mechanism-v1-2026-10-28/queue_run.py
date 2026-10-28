"""Run the frozen trace collection after the recorded predecessor exits cleanly."""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
MODELS = ("4b", "2b", "9b")
TOTAL = 2152


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def write(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def process_alive(identity):
    """Bind a Linux PID to its start tick, so PID reuse does not block the queue."""
    try:
        fields = Path(f"/proc/{int(identity['pid'])}/stat").read_text().rsplit(") ", 1)[1].split()
    except FileNotFoundError:
        return False
    return fields[0] != "Z" and fields[19] == str(identity["start_ticks"])


def predecessor_ready(auth):
    source = auth["predecessor"]
    run = Path(source["run"])
    assert sha(run / "execution.json") == source["execution_sha256"], "Predecessor execution changed"
    state = read(run / "controller.json")
    assert state["freeze_sha256"] == source["freeze_sha256"], "Predecessor freeze changed"
    assert state["status"] in ("running", "completed"), "Predecessor failed or stopped"
    if state["status"] != "completed":
        return False, "predecessor_running"
    keys = source["worker_keys"]
    assert set(state["worker_pids"]) == set(keys), "Predecessor worker identities changed"
    assert state["worker_exit_codes"] == {key: 0 for key in keys}, "Predecessor worker failure"
    for key in keys:
        assert (run / f"{key}.exit").read_text().strip() == "0", "Predecessor exit receipt failed"
        assert read(run / key / "receipt.json")["status"] == "completed", "Predecessor receipt incomplete"
    pids = {item["pid"] for item in source["processes"]}
    assert {state["controller_pid"], *state["worker_pids"].values()} <= pids
    if any(process_alive(item) for item in source["processes"]):
        return False, "predecessor_processes_exiting"
    return True, "predecessor_completed"


def gpu_processes():
    result = subprocess.run(
        ["nvidia-smi", "--id=0,1", "--query-compute-apps=pid,gpu_uuid,process_name", "--format=csv,noheader,nounits"],
        check=True, capture_output=True, text=True, timeout=20,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def prerequisites(path, expected_hash=None):
    import trace_run
    if expected_hash is not None:
        assert sha(path) == expected_hash, "Authorization changed while queued"
    auth = trace_run.validate_authorization(Path(path))
    assert auth["status"] == "authorized" and auth["purpose"] == "early_layer_trace_queue"
    assert auth["experiment"] == ROOT.name and auth["user_instruction"]
    assert auth["queue_sha256"] == sha(__file__), "Queue code changed"
    assert auth["models"] == list(MODELS)
    assert auth["maximum_generations"] == {"preflight": 114, "survey": 4304}
    assert auth["maximum_records"] == {"preflight": 42, "survey": TOTAL}
    evidence = auth["cpu_test_receipt"]
    evidence_path = ROOT / evidence["path"]
    assert sha(evidence_path) == evidence["sha256"], "CPU test evidence changed"
    cpu = read(evidence_path)
    assert cpu["status"] == "passed", "CPU checks did not pass"
    return auth


def progress(output):
    workers = {}
    for path in sorted((output / "survey").glob("*/receipt.json")):
        receipt = read(path)
        workers[path.parent.name] = {
            "status": receipt["status"], "completed_records": receipt.get("completed_records", 0),
            "expected_records": receipt.get("expected_records"),
        }
    return workers


def save_state(output, state):
    state["workers"] = progress(output)
    state["completed_records"] = sum(row["completed_records"] for row in state["workers"].values())
    state["updated_utc"] = utc()
    write(output / "queue-state.json", state)


def wait_ready(path, digest, output, state):
    while True:
        auth = prerequisites(path, digest)
        ready, reason = predecessor_ready(auth)
        apps = gpu_processes() if ready else []
        state.update(wait_reason="gpu_compute_processes" if apps else reason, gpu_compute_processes=apps)
        save_state(output, state)
        if ready and not apps:
            return auth
        time.sleep(10)


def run_pair(mode, model, authorization, digest, output, state):
    import trace_run
    processes, logs = {}, []
    stage = output / mode
    stage.mkdir(exist_ok=True)
    try:
        # Recheck immediately before dispatch; another user's processes are never stopped.
        wait_ready(authorization, digest, output, state)
        for shard in (0, 1):
            key = f"{model}-shard-{shard}"
            log = (stage / f"{key}.log").open("x")
            logs.append(log)
            command = [sys.executable, "-B", str(ROOT / "trace_run.py"), "worker", "--mode", mode,
                       "--model", model, "--shard", str(shard), "--gpu", str(shard),
                       "--output", str(stage / key), "--authorization", str(authorization), "--execute"]
            process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            processes[key] = process
            state["stages"].setdefault(mode, {})[key] = {
                "pid": process.pid, "command": command, "started_utc": utc(), "status": "running",
            }
            save_state(output, state)
        while True:
            prerequisites(authorization, digest)
            codes = {key: process.poll() for key, process in processes.items()}
            if any(code is not None and code != 0 for code in codes.values()):
                raise RuntimeError(f"{mode} {model} worker failure: {codes}")
            save_state(output, state)
            if all(code == 0 for code in codes.values()):
                break
            time.sleep(10)
        for shard in (0, 1):
            key = f"{model}-shard-{shard}"
            receipt = trace_run.verify_worker(stage / key, mode, model, shard)
            assert receipt["status"] == "completed" and receipt["checks_passed"] is True
            state["stages"][mode][key].update(status="completed", receipt_sha256=sha(stage / key / "receipt.json"))
    finally:
        # Only Popen objects created above can be signalled, never predecessor or unrelated PIDs.
        for key, process in processes.items():
            if process.poll() is None:
                process.terminate()
            try:
                code = process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()
                code = process.wait()
            (stage / f"{key}.exit").write_text(str(code) + "\n")
            state["stages"][mode][key].update(exit_code=code, ended_utc=utc())
            if state["stages"][mode][key]["status"] != "completed":
                state["stages"][mode][key]["status"] = "failed" if code else "exited_unverified"
        for log in logs:
            log.close()
        save_state(output, state)


def main(authorization, output, execute=False):
    authorization, output = Path(authorization).resolve(), Path(output).resolve()
    auth = prerequisites(authorization)
    assert str(output) == auth["remote_output"], "Output differs from authorization"
    assert not output.exists(), "Do not overwrite or resume partial evidence"
    if not execute:
        ready, reason = predecessor_ready(auth)
        return {"status": "ready", "predecessor_ready": ready, "wait_reason": reason, "expected_records": TOTAL}
    # ponytail: one lock for this experiment; no general-purpose scheduler is needed.
    with (ROOT / ".queue.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        output.mkdir(parents=True)
        digest = sha(authorization)
        state = {"status": "waiting", "experiment": ROOT.name, "pid": os.getpid(), "started_utc": utc(),
                 "authorization_sha256": digest, "freeze_sha256": auth["freeze_sha256"],
                 "expected_records": TOTAL, "completed_records": 0, "stages": {}}
        write(output / "execution.json", state.copy())
        save_state(output, state)
        try:
            wait_ready(authorization, digest, output, state)
            for mode in ("preflight", "survey"):
                state.update(status=f"running_{mode}", mode=mode)
                for model in MODELS:
                    state["model"] = model
                    run_pair(mode, model, authorization, digest, output, state)
                if mode == "preflight":
                    assert len(state["stages"][mode]) == 6
                    assert all(row["status"] == "completed" and row["exit_code"] == 0 for row in state["stages"][mode].values())
                    write(output / "preflight-accepted.json", {
                        "status": "passed", "freeze_sha256": auth["freeze_sha256"], "accepted_utc": utc(),
                        "workers": state["stages"][mode],
                    })
            save_state(output, state)
            assert state["completed_records"] == TOTAL, "Formal coverage incomplete"
            state["status"] = "completed"
        except BaseException as exc:
            state.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            raise
        finally:
            state["ended_utc"] = utc()
            save_state(output, state)
        return state


def stop(_signum, _frame):
    raise KeyboardInterrupt("Queue stop requested; retain partial evidence")


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, stop)
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorization", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--execute", action="store_true")
    arguments = parser.parse_args()
    print(json.dumps(main(arguments.authorization, arguments.output, arguments.execute)))
