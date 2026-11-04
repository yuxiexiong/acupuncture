"""Tiny CPU-only check of unchanged upstream replacement and BF16 rounding."""
import os
os.environ["CUDA_VISIBLE_DEVICES"] = ""
import argparse
import json
from pathlib import Path
import tempfile

import numpy as np
import torch
from safetensors.torch import load_file, save_file
from build_with_author import build


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True)
    args = parser.parse_args()
    assert not torch.cuda.is_available()
    with tempfile.TemporaryDirectory(prefix="author-builder-cpu-") as tmp:
        root = Path(tmp)
        model, edits, out = root / "base", root / "edits", root / "built"
        model.mkdir(); edits.mkdir()
        name = "model.language_model.layers.0.mlp.down_proj.weight"
        original = {name: torch.ones((2, 2), dtype=torch.bfloat16),
                    "untouched": torch.tensor([2., 3.], dtype=torch.bfloat16)}
        save_file(original, str(model / "model.safetensors"))
        (model / "config.json").write_text('{"synthetic_cpu_check":true}\n')
        candidate = np.array([[1.00390625, -0.75], [0., 2.125]], dtype=np.float32)
        np.save(edits / (name + ".npy"), candidate)
        build(args.source_root, model, edits, out)
        result = load_file(str(out / "model.safetensors"))
        assert torch.equal(result[name], torch.from_numpy(candidate).to(torch.bfloat16))
        assert torch.equal(result["untouched"], original["untouched"])
        assert (model / "config.json").read_bytes() == (out / "config.json").read_bytes()
        assert torch.equal(load_file(str(model / "model.safetensors"))[name], original[name])
        assert json.loads((out / "edits.json").read_text())["edited"] == [name]
        print(json.dumps({"status": "PASS_CPU_SYNTHETIC_ONLY", "model_forward_calls": 0,
                          "gpu_used": False, "checks": ["BF16 rounding", "untouched tensor",
                          "config copied", "base unchanged", "upstream edit receipt"]}))
