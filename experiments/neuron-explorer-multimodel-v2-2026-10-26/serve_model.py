#!/usr/bin/env python3
"""Run one original explorer with its own model, data, and local port."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
models = json.loads((ROOT / "models.json").read_text())
model = next((m for m in models if m["id"] == (sys.argv[1] if len(sys.argv) == 2 else "")), None)
if model is None:
    raise SystemExit("usage: serve_model.py 2b|4b|9b")
data = ROOT / "data" / model["id"]
identity = json.loads((data / "cache" / "model.json").read_text())
if any(identity.get(k) != model[k] for k in ("repo", "revision", "layers", "inter")):
    raise SystemExit("Cache identity does not match selected model")
for name in ("layout_writes.npz", "connections.npz", "lens_index.npz", "act_scale.npz", "vocab.json", "steer_index.npz"):
    if not (data / "cache" / name).is_file():
        raise SystemExit(f"Prepare this model's cache first: {name}")
import numpy as np
shape = (model["layers"], model["inter"])
for name, fields, tail in (("layout_writes", ("cell",), ()),
                           ("lens_index", ("up", "down"), (12,)),
                           ("steer_index", ("up", "down"), (12,)),
                           ("connections", ("down_z", "up_z"), (24,)),
                           ("act_scale", ("pos", "neg"), ())):
    with np.load(data / "cache" / (name + ".npz")) as arrays:
        if any(arrays[field].shape != shape + tail for field in fields):
            raise SystemExit(f"Cache dimensions do not match selected model: {name}")
for name in ("runs", "stats"):
    (data / name).mkdir(parents=True, exist_ok=True)
os.environ.update(EXPLORER_PROFILE=model["id"], EXPLORER_MODEL_ID=model["repo"],
                  EXPLORER_MODEL=model["path"], EXPLORER_DATA=str(data),
                  PORT=str(model["port"]), CUDA_VISIBLE_DEVICES=str(model["gpu"]),
                  HF_HUB_OFFLINE="1", HF_DATASETS_OFFLINE="1", TOKENIZERS_PARALLELISM="false")
os.chdir(ROOT / "upstream")
os.execv(sys.executable, [sys.executable, "explorer/server.py"])
