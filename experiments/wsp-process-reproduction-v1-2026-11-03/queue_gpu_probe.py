"""Wait for a free GPU, then run only the two bounded engineering probes."""
import argparse
import fcntl
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path


def gpu_state(gpu):
    raw = subprocess.check_output(["nvidia-smi", f"--id={gpu}",
        "--query-gpu=uuid,memory.used,utilization.gpu", "--format=csv,noheader,nounits"], text=True, timeout=20)
    uuid, memory, utilization = [s.strip() for s in raw.strip().split(",")]
    processes = subprocess.check_output(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid",
        "--format=csv,noheader,nounits"], text=True, timeout=20)
    pids = [row.split(",")[1].strip() for row in processes.splitlines() if row.split(",")[0].strip() == uuid]
    return {"uuid": uuid, "memory_mib": int(memory), "utilization": int(utilization), "pids": pids}


def idle(state):
    return state["memory_mib"] < 128 and state["utilization"] == 0 and not state["pids"]


def stop_child(process):
    # Only the process group started by this queue is eligible for termination.
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=15)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    # One WSP queue on this machine; other projects still require observed idle checks.
    lock = (args.root / "preflight-queue.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    started = time.time()
    digest = hashlib.sha256(args.probe.read_bytes()).hexdigest()
    state = {"status": "waiting", "pid": os.getpid(), "physical_gpu": 1,
             "started_unix": started, "max_wait_seconds": 21600, "per_model_timeout_seconds": 600,
             "scope": "synthetic generation smoke only; no search or final evaluation", "probe_sha256": digest,
             "runs": []}

    def write():
        state["updated_unix"] = time.time()
        temporary = args.out / "state.pending"
        temporary.write_text(json.dumps(state, indent=2) + "\n")
        temporary.replace(args.out / "state.json")

    def terminate(*_):
        raise KeyboardInterrupt("Queue termination requested")

    signal.signal(signal.SIGTERM, terminate)
    write()
    try:
        for label, model in (("0p8b", "text-Qwen3.5-0.8B"), ("4b", "text-Qwen3.5-4B-r2")):
            idle_samples = 0
            state.update(status="waiting", next_model=label)
            while idle_samples < 2:
                if time.time() - started > 21600:
                    raise TimeoutError("GPU queue expired after 6 hours")
                state["gpu"] = gpu_state(1)
                idle_samples = idle_samples + 1 if idle(state["gpu"]) else 0
                write()
                if idle_samples < 2:
                    time.sleep(60)
            assert hashlib.sha256(args.probe.read_bytes()).hexdigest() == digest, "Probe changed while queued"
            model_out = args.out / label
            cmd = [str(args.python), str(args.probe), "--model", str(args.root/model), "--out", str(model_out)]
            state.update(status="running", command=cmd)
            write()
            before = time.time()
            with (args.out / (label + ".log")).open("w") as log:
                process = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                timed_out = False
                try:
                    process.wait(timeout=600)
                except subprocess.TimeoutExpired:
                    timed_out = True
                finally:
                    stop_child(process)
                    run = {"model": label, "exit_code": process.returncode, "timed_out": timed_out,
                           "wall_seconds": time.time()-before, "output": str(model_out)}
                    state["runs"].append(run)
                    write()
            receipt = json.loads((model_out / "receipt.json").read_text()) if (model_out / "receipt.json").exists() else {}
            if process.returncode != 0 or timed_out or receipt.get("status") != "smoke_passed_not_full_forward_acceptance":
                raise RuntimeError(f"{label} probe failed; queue stopped without proceeding to next model")
        state["status"] = "smoke_completed_not_full_acceptance"
    except BaseException as error:
        state.update(status="stopped", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        write()


if __name__ == "__main__":
    main()
