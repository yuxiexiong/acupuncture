"""Observer-side edit validation. Call only while the CPU kernel is idle.

Snapshots live outside the kernel mounts. No GPU access or model forward.
The author's validator is unpublished; tolerances match our CPU interface.
"""
import argparse
import hashlib
import json
import stat
from pathlib import Path

import numpy as np
import torch
from safetensors import safe_open

FROZEN = {"model.language_model.norm.weight", "model.language_model.embed_tokens.weight", "lm_head.weight"}


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def snapshot(model, edits, destination):
    model, edits, destination = map(Path, (model, edits, destination))
    if not stat.S_ISDIR(edits.lstat().st_mode):
        raise ValueError("Edit directory must be a real directory, not a symlink")
    destination.mkdir(parents=True, exist_ok=False)
    manifest = {"status": "validating", "model": str(model), "source": str(edits),
                "scalar_tolerance": {"rtol": 1e-5, "atol": 1e-7}, "tensors": []}
    receipt = destination / "manifest.json"
    try:
        with safe_open(str(model / "model.safetensors"), framework="pt", device="cpu") as base:
            names = set(base.keys())
            for path in sorted(edits.iterdir()):
                if not stat.S_ISREG(path.lstat().st_mode) or path.suffix != ".npy":
                    raise ValueError(f"Unexpected edit entry: {path.name}")
                name = path.name[:-4]
                if name not in names or name in FROZEN:
                    raise ValueError(f"Unknown or frozen tensor: {name}")
                # Reading a complete private copy breaks aliasing to the writable work directory.
                array = np.load(path, allow_pickle=False)
                if array.dtype.kind != "f":
                    raise ValueError(f"Edit must contain floating-point values: {name}")
                candidate = torch.tensor(array, dtype=torch.float32)
                del array
                original_native = base.get_tensor(name)
                original = original_native.float()
                if candidate.shape != original.shape or not torch.isfinite(candidate).all():
                    raise ValueError(f"Invalid shape or nonfinite edit: {name}")
                denominator = torch.sum(original.double() ** 2)
                alpha = torch.sum(candidate.double() * original.double()) / denominator if denominator else 0.0
                if torch.allclose(candidate, original * float(alpha), rtol=1e-5, atol=1e-7):
                    raise ValueError(f"Whole-tensor scalar multiplication: {name}")
                effective = candidate.to(original_native.dtype)
                if not torch.isfinite(effective).all():
                    raise ValueError(f"Edit overflows model dtype: {name}")
                target = destination / path.name
                np.save(target, candidate.numpy(), allow_pickle=False)
                target.chmod(0o444)
                manifest["tensors"].append({"name": name, "shape": list(candidate.shape),
                    "snapshot_dtype": "float32", "model_dtype": str(original_native.dtype),
                    "snapshot_sha256": sha256(target),
                    "effective_tensor_sha256": hashlib.sha256(effective.contiguous().view(torch.uint8).numpy().tobytes()).hexdigest(),
                    "relative_change": float((candidate-original).norm() / original.norm()) if denominator else None,
                    "effective_changed_values": int((effective != original_native).sum())})
        manifest["status"] = "validated"
    except BaseException as error:
        manifest.update(status="rejected", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        receipt.write_text(json.dumps(manifest, indent=2) + "\n")
        receipt.chmod(0o444)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for argument in ("model", "edits", "destination"):
        parser.add_argument("--" + argument, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(snapshot(args.model, args.edits, args.destination)))
