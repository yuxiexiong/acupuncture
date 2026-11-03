"""Compile the SM90a sampler without exposing any GPU."""
import argparse
import importlib.metadata
import json
import os
import time
import traceback
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--receipt", type=Path, required=True)
args = parser.parse_args()
assert not args.receipt.exists()
started = time.time()
receipt = {"status": "running", "purpose": "CPU compilation only, no model forward",
           "environment": {key: os.environ.get(key) for key in ("CUDA_VISIBLE_DEVICES", "CUDA_HOME", "LIBRARY_PATH", "LD_LIBRARY_PATH", "FLASHINFER_CUDA_ARCH_LIST", "FLASHINFER_WORKSPACE_BASE", "MAX_JOBS")},
           "versions": {name: importlib.metadata.version(name) for name in ("torch", "flashinfer-python", "nvidia-cuda-nvcc", "nvidia-cuda-crt", "nvidia-nvvm", "nvidia-cuda-runtime")}}
args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
try:
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    assert os.environ.get("FLASHINFER_CUDA_ARCH_LIST") == "9.0a"
    import torch
    assert not torch.cuda.is_available()
    from flashinfer.jit.sampling import gen_sampling_module
    gen_sampling_module().build_and_load()
    receipt["status"] = "compiled_and_loaded_no_gpu"
except BaseException:
    receipt.update(status="failed", error=traceback.format_exc())
finally:
    receipt["wall_seconds"] = time.time()-started
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
print(json.dumps({"status": receipt["status"], "wall_seconds": receipt["wall_seconds"]}))
raise SystemExit(1 if receipt["status"] == "failed" else 0)
