"""One bounded two-GPU dispatch; logs stay outside the immutable run evidence."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import parallel_validate as parallel
import run_root as r


def main():
    os.chdir(r.HERE)
    run = r.HERE / "runs/root-parallel-r01"
    record_path = r.HERE / "runs/root-parallel-r01-controller.json"
    if record_path.exists():
        raise FileExistsError("This dispatch is already recorded; never duplicate it")
    check = r.read(r.HERE / "runs/parallel-gpu1-check-r01/receipt.json")
    assert check["status"] == "completed" and all(x["exact"] for x in check["comparisons"])
    assert check["base_freeze_sha256"] == r.sha(r.HERE / "freeze.json")
    assert check["authorization_sha256"] == r.sha(r.HERE / "parallel-authorization-20261026.json")
    assert check["check_code_sha256"] == r.sha(r.HERE / "check_parallel_gpu.py")
    assert (r.HERE / "runs/root-r01/parallel-handoff-r01.json").is_file()
    for gpu in (0, 1):
        state = subprocess.check_output(["nvidia-smi", "-i", str(gpu),
            "--query-gpu=memory.used,utilization.gpu", "--format=csv,noheader,nounits"], text=True)
        if state.replace(" ", "").strip() != "0,0":
            raise RuntimeError(f"GPU {gpu} is occupied: {state}")
    parallel.prepare(r.HERE / "runs/root-r01/preflight-r01/receipt.json",
        r.HERE / "runs/root-r01/rank-r01/receipt.json",
        r.HERE / "parallel-authorization-20261026.json", run)
    record = {"status": "running", "started_at": r.utc(), "controller_sha256": r.sha(__file__),
              "run": str(run), "workers": []}
    r.write(record_path, record)
    workers, logs = [], []
    try:
        for gpu in (0, 1):
            log = open(r.HERE / f"runs/root-parallel-r01-worker-{gpu}.log", "x")
            logs.append(log)
            process = subprocess.Popen([sys.executable, "-u", "parallel_validate.py", "worker",
                "--run", str(run), "--shard", str(gpu), "--device", "cuda:0"],
                env={**os.environ, "CUDA_VISIBLE_DEVICES": str(gpu)},
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
            workers.append(process)
            record["workers"].append({"gpu": gpu, "pid": process.pid, "log": str(Path(log.name))})
            r.write(record_path, record)
        while any(p.poll() is None for p in workers):
            if any(p.poll() not in (None, 0) for p in workers):
                raise RuntimeError("A validation worker failed; preserve both shards and stop its peer")
            time.sleep(2)
        if any(p.returncode != 0 for p in workers):
            raise RuntimeError("A validation worker failed")
        parallel.merge(run)
        parallel.verify_merged(run)
        record["status"] = "completed"
    except Exception as error:
        record.update(status="failed", error=str(error))
        for process in workers:
            if process.poll() is None:
                process.terminate()
        raise
    finally:
        for process in workers:
            process.wait()
        for log in logs:
            log.close()
        record.update(finished_at=r.utc(), worker_exit_codes=[p.returncode for p in workers])
        r.write(record_path, record)
    print(json.dumps({"status": record["status"], "finished_at": record["finished_at"]}))


if __name__ == "__main__":
    main()
