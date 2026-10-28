#!/usr/bin/env python3
"""Read this run's logs/PIDs; do not load models or change any jobs."""
import json
from pathlib import Path
import re
import statistics
import time

ROOT = Path(__file__).resolve().parent


def worker(name, start_layer, layers, neurons):
    path = ROOT / "runtime" / (name + "-r01.log")
    batches = []
    if path.exists():
        for line in path.read_text().splitlines():
            if line.startswith('{"layer":'):
                batches.append(json.loads(line))
    count = 0
    seconds = None
    if batches:
        last = batches[-1]
        count = (last["layer"] - start_layer) * neurons + last["neuron_stop"]
        seconds = statistics.median(b["batch_seconds"] for b in batches[-20:])
    pid_file = ROOT / "runtime" / (name + ".pid")
    alive = False
    if pid_file.exists():
        try:
            alive = b"steer_lens.py" in Path(f"/proc/{int(pid_file.read_text())}/cmdline").read_bytes()
        except (FileNotFoundError, ProcessLookupError):
            pass
    return {"channels_processed": count, "total_channels": layers * neurons,
            "recent_seconds_per_96_channels": seconds, "alive": alive,
            "remaining_seconds_at_recent_rate": (layers * neurons - count) / 96 * seconds if seconds else None}


out = {"at_unix": time.time(), "workers": {
    "2b": worker("steer-full-2b", 0, 24, 6144),
    "9b_part1": worker("steer-full-9b-part1", 0, 16, 12288),
    "9b_part2": worker("steer-full-9b-part2", 16, 16, 12288)}, "layout_layers": {}, "full_index_exists": {}}
for profile in ("2b", "9b"):
    path = ROOT / "runtime" / f"layout-{profile}-r01.log"
    matches = re.findall(r"^L(\d+) done", path.read_text(), flags=re.M) if path.exists() else []
    out["layout_layers"][profile] = max(map(int, matches)) + 1 if matches else 0
    out["full_index_exists"][profile] = (ROOT / "data" / profile / "cache" / "steer_index.npz").exists()
print(json.dumps(out))
