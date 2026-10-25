"""Run disjoint paired shards; expose both generation-task timings early."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

from prepare_panel import read, sha, utc, write


def main(gpu):
    root = Path(__file__).resolve().parent
    protocol = read(root / "protocol.json")
    assert protocol["status"] == "frozen_before_formal_inference"
    assert sha(Path(__file__).resolve()) == protocol["source_sha256"]["run_worker.py"]
    path = root / f"worker-{gpu}.json"
    assert not path.exists(), "Preserve any existing attempt"
    receipt = {"status": "started", "started_utc": utc(), "gpu": gpu, "shard_index": gpu,
               "shard_count": 2, "pid": os.getpid(), "protocol_sha256": sha(root / "protocol.json"), "tasks": []}
    write(path, receipt)
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=str(gpu), PYTHONDONTWRITEBYTECODE="1",
                       TOKENIZERS_PARALLELISM="false")
    for task in protocol["task_orders"][str(gpu)]:
        log = root / f"{task}-shard{gpu}-r01.log"
        command = [sys.executable, "-u", str(root / "run_panel.py"), "--task", task, "--shard-index", str(gpu)]
        entry = {"task": task, "command": command, "log": str(log), "status": "started"}
        receipt["tasks"].append(entry)
        write(path, receipt)
        with log.open("xb") as stream:
            result = subprocess.run(command, cwd=root, env=environment, stdout=stream, stderr=subprocess.STDOUT)
        entry.update(exit_code=result.returncode, status="completed" if result.returncode == 0 else "failed")
        write(path, receipt)
        if result.returncode:
            receipt["status"] = "failed"
            break
    else:
        receipt["status"] = "completed"
    receipt["ended_utc"] = utc()
    write(path, receipt)
    return 0 if receipt["status"] == "completed" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gpu", type=int, choices=(0, 1), required=True)
    raise SystemExit(main(parser.parse_args().gpu))
