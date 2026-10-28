#!/usr/bin/env python3
"""After 2B completes, build the other half of 9B; merge only complete layers."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parent
MODELS = {m["id"]: m for m in json.loads((ROOT / "models.json").read_text())}


def layer_files(profile):
    m = MODELS[profile]
    return [ROOT / "data" / profile / "stats" / f"steer-full-r01_L{layer}.npz" for layer in range(m["layers"])]


def merge(profile):
    m, files = MODELS[profile], layer_files(profile)
    target = ROOT / "data" / profile / "cache" / "steer_index.npz"
    if target.exists():
        raise RuntimeError(f"Keep prior evidence: {target}")
    columns = {k: [] for k in ("up", "down", "up_kl", "down_kl")}
    sources = []
    contexts = context_mask = context_texts = norms = None
    for layer, path in enumerate(files):
        with np.load(path) as z:
            assert bool(z["complete_layer"]) and int(z["layer"]) == layer
            assert str(z["model"]) == m["path"] and int(z["total_neurons"]) == m["inter"]
            assert float(z["dose"]) == 0.8
            assert np.array_equal(z["neurons"], np.arange(m["inter"]))
            expected_texts = ["Who are you?", "Write whatever you like.",
                              "I think the most important thing to remember is", "Today we are going to talk about"]
            assert z["contexts"].tolist() == expected_texts
            assert z["context_ids"].shape[0] == 4
            assert z["context_mask"].shape == z["context_ids"].shape
            assert z["calibration_norms"].shape == (m["layers"],)
            assert np.isfinite(z["calibration_norms"]).all() and (z["calibration_norms"] > 0).all()
            assert float(z["residual_norm"]) == float(z["calibration_norms"][layer])
            if contexts is None:
                contexts, norms = z["context_ids"].copy(), z["calibration_norms"].copy()
                context_mask, context_texts = z["context_mask"].copy(), z["contexts"].copy()
            else:
                assert np.array_equal(contexts, z["context_ids"])
                assert np.array_equal(context_mask, z["context_mask"])
                assert np.array_equal(context_texts, z["contexts"])
                assert np.array_equal(norms, z["calibration_norms"])
            for key in columns:
                a = z[key if key.endswith("_kl") else key + "_tok"].copy()
                assert a.shape == ((m["inter"],) if key.endswith("_kl") else (m["inter"], 12))
                assert np.isfinite(a).all()
                columns[key].append(a)
        sources.append({"file": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    tmp = target.with_name("steer_index.tmp.npz")
    np.savez(tmp, **{k: np.stack(v) for k, v in columns.items()})
    os.replace(tmp, target)
    receipt = {"model": m, "status": "complete", "channels": m["layers"] * m["inter"],
               "signed_conditions": 2 * m["layers"] * m["inter"], "dose": 0.8,
               "contexts_per_condition": 4, "completed_at": time.time(), "sources": sources,
               "cache_sha256": hashlib.sha256(target.read_bytes()).hexdigest()}
    (ROOT / "data" / profile / "steer-cache-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"event": "merged", "profile": profile, "channels": receipt["channels"]}), flush=True)


def active(pid_file):
    pid = int(pid_file.read_text())
    proc = Path(f"/proc/{pid}/cmdline")
    try:
        return b"steer_lens.py" in proc.read_bytes()
    except (FileNotFoundError, ProcessLookupError):
        return False


def wait_for_layers(profile, indices, pid_file):
    paths = [layer_files(profile)[i] for i in indices]
    while True:
        running = active(pid_file)
        if all(p.exists() for p in paths) and not running:
            return
        if not running:
            raise RuntimeError(f"{profile} worker exited before all layers finished; inspect its retained log")
        time.sleep(30)


def main():
    runtime = ROOT / "runtime"
    wait_for_layers("2b", range(24), runtime / "steer-full-2b.pid")
    merge("2b")
    pid_file = runtime / "steer-full-9b-part2.pid"
    if pid_file.exists():
        raise RuntimeError("Part 2 already has a recorded PID; inspect before resuming")
    env = {**os.environ, "CUDA_VISIBLE_DEVICES": "0", "HF_HUB_OFFLINE": "1"}
    with (runtime / "steer-full-9b-part2-r01.log").open("xb") as log:
        worker = subprocess.Popen([sys.executable, str(ROOT / "upstream/sweep/steer_lens.py"),
            "--model", MODELS["9b"]["path"], "--layers", "16-31", "--neurons-per-batch", "96",
            "--out", str(ROOT / "data/9b/stats/steer-full-r01")],
            env=env, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
    pid_file.write_text(str(worker.pid) + "\n")
    print(json.dumps({"event": "started_9b_part2", "pid": worker.pid, "at": time.time()}), flush=True)
    wait_for_layers("9b", range(16), runtime / "steer-full-9b-part1.pid")
    if worker.wait() != 0:
        raise RuntimeError("9B part 2 exited with error; inspect retained log")
    merge("9b")


if __name__ == "__main__":
    main()
