"""Tiny CPU fixtures verify the boundary against directly written edit files."""
import json
import tempfile
from pathlib import Path

import numpy as np
import torch
from safetensors.torch import save_file

from snapshot_edits import snapshot, sha256


def main():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        model, edits = root / "model", root / "edits"
        model.mkdir(); edits.mkdir()
        name = "model.language_model.layers.0.mlp.down_proj.weight"
        frozen = "model.language_model.norm.weight"
        original = torch.arange(1, 7, dtype=torch.bfloat16).reshape(2, 3)
        save_file({name: original, frozen: torch.ones(2)}, str(model / "model.safetensors"))
        assert snapshot(model, edits, root / "empty")["tensors"] == []
        valid = original.float().numpy().copy(); valid[0, 0] += 1
        np.save(edits / (name + ".npy"), valid)
        result = snapshot(model, edits, root / "valid")
        saved = root / "valid" / (name + ".npy")
        digest = sha256(saved)
        np.save(edits / (name + ".npy"), valid * 3)
        assert sha256(saved) == digest == result["tensors"][0]["snapshot_sha256"]
        cases = [
            (name, original.float().numpy()*2), (name, np.zeros((1, 3))),
            (name, np.full((2, 3), np.nan)), (name, np.full((2, 3), np.inf)),
            (name, np.ones((2, 3), dtype=np.int32)), (frozen, np.ones(2)),
            ("unknown", valid),
        ]
        for index, (key, values) in enumerate(cases):
            for path in edits.iterdir(): path.unlink()
            np.save(edits / (key + ".npy"), values)
            try:
                snapshot(model, edits, root / f"rejected-{index}")
                raise AssertionError("Invalid edit accepted")
            except ValueError:
                assert json.loads((root / f"rejected-{index}" / "manifest.json").read_text())["status"] == "rejected"
        for path in edits.iterdir(): path.unlink()
        (edits / (name + ".npy")).symlink_to(saved)
        try:
            snapshot(model, edits, root / "symlink")
            raise AssertionError("Symlink accepted")
        except ValueError:
            pass
        try:
            snapshot(model, edits, root / "valid")
            raise AssertionError("Existing snapshot overwritten")
        except FileExistsError:
            pass
        assert sha256(saved) == digest
    print(json.dumps({"status": "passed", "scope": "CPU synthetic edits; no model forward",
                      "checks": ["empty", "valid", "snapshot independent", "scalar", "shape", "nan", "inf", "dtype", "frozen", "unknown", "symlink", "no overwrite"]}))


if __name__ == "__main__":
    main()
