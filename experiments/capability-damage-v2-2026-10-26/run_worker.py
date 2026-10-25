"""Run one of two disjoint, paired task shards on its assigned H20."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

from run_benchmarks import write

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--gpu", type=int, choices=(0, 1), required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parent
receipt_path = root / f"worker-{args.gpu}.json"
assert not receipt_path.exists(), "Preserve any existing worker attempt"
receipt = {"status": "started", "started_utc": datetime.now(timezone.utc).isoformat(),
           "gpu": args.gpu, "shard_index": args.gpu, "shard_count": 2, "pid": os.getpid(), "tasks": []}
write(receipt_path, receipt)
environment = dict(os.environ, CUDA_VISIBLE_DEVICES=str(args.gpu),
                   PYTHONDONTWRITEBYTECODE="1", TOKENIZERS_PARALLELISM="false")
for task in ("mmlu", "arc_challenge", "humaneval", "gsm8k"):
    output = root / "outputs" / f"{task}-shard{args.gpu}-r01"
    log = root / f"{task}-shard{args.gpu}-r01.log"
    command = [sys.executable, "-u", str(root / "run_benchmarks.py"), "--task", task,
               "--model", "/data/models/Qwen3.5-4B-851bf6e", "--items", str(root / "items" / f"{task}.jsonl"),
               "--output", str(output), "--validation", str(root / "validation" / f"preflight-gpu{args.gpu}-b1-r01" / "receipt.json"),
               "--batch-size", "1", "--shard-count", "2", "--shard-index", str(args.gpu)]
    entry = {"task": task, "command": command, "log": str(log), "status": "started"}
    receipt["tasks"].append(entry)
    write(receipt_path, receipt)
    with log.open("xb") as stream:
        result = subprocess.run(command, cwd=root, env=environment, stdout=stream, stderr=subprocess.STDOUT)
    entry.update(exit_code=result.returncode, status="completed" if result.returncode == 0 else "failed")
    write(receipt_path, receipt)
    if result.returncode:
        receipt["status"] = "failed"
        break
else:
    receipt["status"] = "completed"
receipt["ended_utc"] = datetime.now(timezone.utc).isoformat()
write(receipt_path, receipt)
raise SystemExit(0 if receipt["status"] == "completed" else 1)
