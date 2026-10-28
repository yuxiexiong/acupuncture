"""Reuse frozen ridge fitting, replacing only cross-tokenizer pairing checks."""
import argparse
import importlib.util
from pathlib import Path
import sys

from common import LEGACY, ROOT, read, sha, write, verify_freeze

sys.path.append(str(LEGACY))
spec = importlib.util.spec_from_file_location("cross_family_frozen_mapping", LEGACY / "fit_mapping.py")
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)


def paired_arrays(source, target, layer, split, device):
    import torch
    from engine import token_hash, text_hash
    import json
    sx, ty, weights, doc_ids = [], [], [], []
    sdir, sr, si, _, _ = source
    tdir, tr, ti, _, _ = target
    assert sr["alignment_version"] == tr["alignment_version"] == "common-plain-character-boundaries-v1"
    assert sr["tokenizers"] == tr["tokenizers"]
    assert sr["data_sha256"][split] == tr["data_sha256"][split]
    assert [x["id"] for x in si[split]] == [x["id"] for x in ti[split]]
    for document, (se, te) in enumerate(zip(si[split], ti[split])):
        for directory, entry in ((sdir, se), (tdir, te)):
            assert sha(directory / entry["file"]) == entry["sha256"]
        a = torch.load(sdir / se["file"], map_location="cpu", weights_only=True)
        b = torch.load(tdir / te["file"], map_location="cpu", weights_only=True)
        keys = ("version", "text_sha256", "char_end", "source_positions", "target_positions", "source_token_sha256", "target_token_sha256")
        aligned = {key: a[key] for key in keys}
        assert aligned == {key: b[key] for key in keys}
        assert text_hash(json.dumps(aligned, sort_keys=True, separators=(",", ":"))) == a["alignment_sha256"] == b["alignment_sha256"]
        assert a["role"] == "source" and b["role"] == "target"
        for row in (a, b):
            assert row["input_token_sha256"] == row[row["role"] + "_token_sha256"] == token_hash(row["tokens"])
            assert row["positions"] == row[row["role"] + "_positions"]
        x, y = a["layers"][str(layer)]["residual"], b["layers"][str(layer)]["residual"]
        assert len(x) == len(y) == len(a["char_end"]) > 0
        sx.append(x); ty.append(y)
        weights.append(torch.full((len(x),), 1.0 / (len(si[split]) * len(x))))
        doc_ids.extend([document] * len(x))
    return torch.cat(sx).to(device), torch.cat(ty).to(device), torch.cat(weights).to(device), torch.tensor(doc_ids, device=device)


def run(args):
    verify_freeze(args.freeze)
    # This process-local replacement keeps the already validated fitting, random
    # sampling, projection and dose formulae unchanged; no historical file is edited.
    legacy.paired_arrays = paired_arrays
    legacy.run(args)
    output = Path(args.output)
    diagnostic = read(output / "conditions.json")
    failed = [layer for layer, values in diagnostic["mapping"].items() if values["validation_relative_mse"] >= 1]
    quality = {"status": "MAPPING_QUALITY_HOLD" if failed else "PASS", "failed_layers": failed,
        "criterion": "Each layer's clean validation relative MSE < 1 (training-mean predictor)",
        "mapping_wrapper_sha256": sha(__file__), "freeze_sha256": sha(args.freeze),
        "conditions_sha256": sha(output / "conditions.json"), "bundle_sha256": sha(output / "bundle.pt")}
    write(output / "quality.json", quality)
    receipt = read(output / "receipt.json")
    receipt["cross_family"] = quality
    receipt["files"]["quality.json"] = sha(output / "quality.json")
    write(output / "receipt.json", receipt)
    if failed:
        raise RuntimeError("MAPPING_QUALITY_HOLD: preserve mapping; no automatic layer/data/dose search")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "target", "output", "freeze"):
        p.add_argument("--" + name, required=True)
    p.add_argument("--device", default="cpu")
    run(p.parse_args())
