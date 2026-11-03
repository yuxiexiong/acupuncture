"""Extract original text tensors, preserving names, dtypes and exact bytes."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

import torch
from safetensors import safe_open
from safetensors.torch import save_file


def tensor_hash(t):
    return hashlib.sha256(t.contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--raw", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--author-config", type=Path)
    args = p.parse_args()
    if args.out.exists():
        raise FileExistsError("Use a new export directory; never overwrite an existing model")
    args.out.mkdir(parents=True)
    original_config = json.loads((args.raw / "config.json").read_text())
    if args.author_config:
        shutil.copyfile(args.author_config / "config.json", args.out / "config.json")
    else:
        config = original_config["text_config"].copy()
        config["architectures"] = ["Qwen3_5ForCausalLM"]
        (args.out / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    for name in ("LICENSE", "tokenizer.json", "tokenizer_config.json", "chat_template.jinja",
                 "merges.txt", "vocab.json", "generation_config.json"):
        source = args.raw / name
        if args.author_config and (args.author_config / name).exists():
            source = args.author_config / name
        if source.exists():
            shutil.copyfile(source, args.out / name)
    ix = json.loads((args.raw / "model.safetensors.index.json").read_text())["weight_map"]
    names = sorted(n for n in ix if n.startswith("model.language_model.") or n == "lm_head.weight")
    assert names and "model.language_model.embed_tokens.weight" in names
    tensors, records = {}, {}
    for shard in sorted({ix[n] for n in names}):
        with safe_open(str(args.raw / shard), framework="pt", device="cpu") as source:
            for name in names:
                if ix[name] != shard:
                    continue
                t = source.get_tensor(name)
                tensors[name] = t
                records[name] = {"shape": list(t.shape), "dtype": str(t.dtype),
                                 "sha256": tensor_hash(t), "source_shard": shard}
    output = args.out / "model.safetensors"
    save_file(tensors, str(output), metadata={"format": "pt"})
    del tensors
    with safe_open(str(output), framework="pt", device="cpu") as exported:
        assert sorted(exported.keys()) == names
        for name in names:
            t = exported.get_tensor(name)
            assert tensor_hash(t) == records[name]["sha256"], name
    receipt = {"raw": str(args.raw), "export": str(args.out), "status": "all_text_tensors_bitwise_verified",
               "excluded_non_text_names": sorted(set(ix) - set(names)), "tensors": records,
               "config_origin": str(args.author_config) if args.author_config else "original text_config; architectures added"}
    (args.out / "text_export_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    for path in args.out.iterdir():
        path.chmod(0o444)
    print(json.dumps({"export": str(args.out), "tensors": len(names), "status": receipt["status"]}))


if __name__ == "__main__":
    main()
