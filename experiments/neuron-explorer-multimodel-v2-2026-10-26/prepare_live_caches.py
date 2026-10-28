#!/usr/bin/env python3
"""Build model-specific logit lens and activation scales from recorded public text."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument("model", choices=["2b", "9b"])
ap.add_argument("--calibration", type=Path)
a = ap.parse_args()
m = next(m for m in json.loads((ROOT / "models.json").read_text()) if m["id"] == a.model)
data = ROOT / "data" / a.model
cache = data / "cache"
cache.mkdir(parents=True, exist_ok=True)
(data / "stats").mkdir(exist_ok=True)
identity = {k: m[k] for k in ("repo", "revision", "layers", "hidden", "inter")}
identity_path = cache / "model.json"
if identity_path.exists():
    assert json.loads(identity_path.read_text()) == identity
else:
    identity_path.write_text(json.dumps(identity, indent=2) + "\n")
os.environ.update(EXPLORER_MODEL=m["path"], EXPLORER_MODEL_ID=m["repo"], EXPLORER_PROFILE=m["id"],
                  EXPLORER_DATA=str(data), CUDA_VISIBLE_DEVICES=str(m["gpu"]),
                  HF_HUB_OFFLINE="1", HF_DATASETS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
sys.path.insert(0, str(ROOT / "upstream" / "explorer"))
from runtime import Runtime
import numpy as np

rt = Runtime(str(data / "stats"))
start = time.time()
rt.ensure_loaded()
rt.vocab_strings()
path = cache / "lens_index.npz"
if not path.exists():
    print("building logit lens", flush=True)
    rt.build_lens_index(str(path))
print(json.dumps({"phase": "lens_ready", "seconds": time.time() - start}), flush=True)
path = cache / "act_scale.npz"
if a.calibration is not None and not path.exists():
    from datasets import IterableDataset
    records = [json.loads(line) for line in a.calibration.read_text().splitlines()]
    dataset = IterableDataset.from_generator(lambda: iter(records)).shuffle(seed=0, buffer_size=1000)
    pos = np.zeros((m["layers"], m["inter"]), np.float32)
    neg = np.zeros_like(pos)
    buf, seen, used_ids = [], 0, []
    for record in dataset:
        buf += rt.tok(record["row"]["text"], add_special_tokens=False).input_ids + [rt.tok.eos_token_id]
        while len(buf) >= 512 and seen < 10000:
            chunk, buf = buf[:512], buf[512:]
            acts = rt.all_activations(chunk, skip_first=True)
            for layer, (mx, _, mn, _) in acts.items():
                pos[layer] = np.maximum(pos[layer], mx.numpy())
                neg[layer] = np.minimum(neg[layer], mn.numpy())
            used_ids.append(chunk)
            seen += 512
            print(json.dumps({"phase": "activation_scale", "tokens": seen}), flush=True)
        if seen >= 10000:
            break
    assert seen == 10240 and np.isfinite(pos).all() and np.isfinite(neg).all()
    np.savez(path, pos=pos, neg=neg, tokens=seen)
    (data / "calibration-token-ids.json").write_text(json.dumps(used_ids) + "\n")
    (data / "calibration-receipt.json").write_text(json.dumps({
        "model": identity, "source_file": str(a.calibration),
        "source_sha256": hashlib.sha256(a.calibration.read_bytes()).hexdigest(),
        "source": "FineWeb-Edu sample-10BT fixed public rows subset",
        "records": len(records), "shuffle_seed": 0, "shuffle_buffer_size": 1000,
        "sequence_length": 512, "tokens": seen, "skip_first_position": True,
        "matches_author_exact_sample": False,
        "total_elapsed_seconds": time.time() - start}, indent=2) + "\n")
print(json.dumps({"phase": "done", "seconds": time.time() - start}), flush=True)
