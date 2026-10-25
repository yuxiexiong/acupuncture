"""Wait for both frozen inference workers, then run the existing CPU scorers once."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import traceback

TASKS = ("mmlu", "arc_challenge", "humaneval", "gsm8k")


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def dependency_state(workers):
    for index, worker in enumerate(workers):
        if worker is None:
            continue
        if worker["status"] not in ("started", "completed") or any(task["status"] == "failed" for task in worker["tasks"]):
            return "failed", f"worker-{index} reported failure"
        if worker["status"] == "completed":
            tasks = worker["tasks"]
            if [task["task"] for task in tasks] != list(TASKS) or not all(task["status"] == "completed" and task["exit_code"] == 0 for task in tasks):
                return "failed", f"worker-{index} has an incomplete success receipt"
    if all(worker is not None and worker["status"] == "completed" for worker in workers):
        return "ready", None
    return "waiting", None


def dependencies(root):
    workers, hashes = [], {}
    for index in range(2):
        path = root / f"worker-{index}.json"
        raw = path.read_bytes() if path.exists() else None
        workers.append(json.loads(raw) if raw else None)
        if raw:
            hashes[path.name] = hashlib.sha256(raw).hexdigest()
    state, error = dependency_state(workers)
    if state == "waiting":
        for index, worker in enumerate(workers):
            if worker is not None and worker["status"] == "started":
                proc = Path(f'/proc/{worker["pid"]}/cmdline')
                try:
                    alive = b"run_worker.py" in proc.read_bytes()
                except FileNotFoundError:
                    alive = False
                if not alive:
                    # Check once more: the process may have just written its final receipt.
                    latest = json.loads((root / f"worker-{index}.json").read_bytes())
                    if latest["status"] == "started":
                        return "failed", f"worker-{index} exited without a terminal receipt", hashes
    return state, error, hashes


def commands(root):
    project, finish = root.parents[1], root / "finish-r01"
    python = str(project / ".venv-bench/bin/python")
    human_files = sorted((root / "outputs").glob("humaneval-shard*-r01/[0-9]*.jsonl*"))
    execution = finish / "humaneval-execution.jsonl"
    return [
        [python, "-u", str(root / "humaneval_sandbox.py"),
         "--bwrap", str(project / ".runtime/bubblewrap/root/usr/bin/bwrap"),
         "--official", str(project / ".runtime/human-eval"),
         "--python-prefix", "/workspace/miniconda/envs/amic-q3",
         "--records", *map(str, human_files), "--output", str(execution)],
        [python, "-u", str(root / "score_results.py"), "--records", str(root / "outputs"),
         "--manifest", str(root / "task_manifest.json"), "--human-results", str(execution),
         "--harness", str(project / ".runtime/lm-evaluation-harness"),
         "--cache-dir", str(project / ".cache/hf/datasets"), "--out-dir", str(finish / "scores")],
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    if args.dry_run:
        state, error, hashes = dependencies(root)
        print(json.dumps({"dependency_state": state, "error": error, "worker_sha256": hashes,
                          "commands": commands(root), "executes_commands": False}, indent=2))
        return

    # A permanent exclusive directory prevents concurrent starts and automatic retries.
    finish = root / "finish-r01"
    finish.mkdir(exist_ok=False)
    path = finish / "receipt.json"
    receipt = {"status": "waiting", "pid": os.getpid(), "started_utc": utc(),
               "helper_sha256": sha(Path(__file__)), "steps": [], "poll_seconds": 60,
               "automatic_retries": False}
    write(path, receipt)
    try:
        protocol_path, manifest = root / "protocol.json", root / "task_manifest.json"
        protocol = json.loads(protocol_path.read_text())
        frozen = {**protocol["source_sha256"], "protocol.json": sha(protocol_path),
                  "task_manifest.json": protocol["task_manifest_sha256"]}
        receipt["frozen_sha256"] = frozen

        def check_frozen():
            for name, digest in frozen.items():
                if sha(root / name) != digest:
                    raise RuntimeError(f"Frozen file changed: {name}")

        check_frozen()
        while True:
            state, error, hashes = dependencies(root)
            receipt.update(status=state, checked_utc=utc(), worker_sha256=hashes)
            write(path, receipt)
            if state == "failed":
                raise RuntimeError(error)
            if state == "ready":
                break
            time.sleep(60)

        environment = {"HF_HOME": str(root.parents[1] / ".cache/hf"), "HF_ENDPOINT": "https://hf-mirror.com",
                       "HF_HUB_OFFLINE": "1", "HF_DATASETS_OFFLINE": "1", "CUDA_VISIBLE_DEVICES": "",
                       "PYTHONDONTWRITEBYTECODE": "1", "OMP_NUM_THREADS": "4"}
        receipt["environment_overrides"] = environment
        for name, command in zip(("humaneval", "scoring"), commands(root)):
            check_frozen()
            log = finish / f"{name}.log"
            step = {"name": name, "command": command, "status": "running", "started_utc": utc(), "log": str(log)}
            receipt["steps"].append(step)
            receipt["status"] = "running"
            write(path, receipt)
            with log.open("xb") as stream:
                completed = subprocess.run(command, cwd=root, env={**os.environ, **environment}, stdout=stream, stderr=subprocess.STDOUT)
            step.update(exit_code=completed.returncode, ended_utc=utc(), log_sha256=sha(log),
                        status="completed" if completed.returncode == 0 else "failed")
            write(path, receipt)
            if completed.returncode:
                raise RuntimeError(f"{name} exited {completed.returncode}; no retry")
        check_frozen()
        receipt["status"] = "completed"
    except Exception as error:
        receipt.update(status="failed", error=str(error), traceback=traceback.format_exc())
    finally:
        receipt["ended_utc"] = utc()
        receipt["artifacts_sha256"] = {str(p.relative_to(finish)): sha(p) for p in sorted(finish.rglob("*")) if p.is_file() and p != path}
        write(path, receipt)
        print(json.dumps({"status": receipt["status"], "receipt": str(path)}, indent=2), flush=True)
    raise SystemExit(0 if receipt["status"] == "completed" else 1)


if __name__ == "__main__":
    main()
