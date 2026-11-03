"""Freeze independent search prompts before either search sees any new results."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--original", type=Path, required=True)
    p.add_argument("--four-b-config", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    original = args.original.read_text()
    blob = hashlib.sha1(f"blob {len(original.encode())}\0".encode() + original.encode()).hexdigest()
    assert blob == "5350f8c0cde31d5760c82e929bd1eb24685cbf60"
    c = json.loads(args.four_b_config.read_text())
    assert (c["num_hidden_layers"], c["hidden_size"], c["intermediate_size"]) == (32, 2560, 9216)
    assert (c["linear_num_key_heads"], c["linear_num_value_heads"]) == (16, 32)
    first = ("TASK. You are given the weights of a language model, Qwen3.5-4B "
             "(text part: 32 layers of width 2,560; layers 3, 7, 11, 15, 19, 23, 27 and 31 "
             "are full-attention layers with 16 query heads and 4 key/value heads of size 256 "
             "and a gated output, the other 24 are Gated DeltaNet linear-attention layers "
             "with 16 key heads and 32 value heads, both of size 128; each layer has a "
             "SwiGLU MLP of width 9,216; RMSNorm; vocabulary 248,320; input embedding and "
             "output layer tied). Your job is to make it better at mathematics by EDITING "
             "ITS WEIGHTS DIRECTLY: find out what goes wrong inside the network when it "
             "fails at math problems and repair that with targeted changes.")
    _, remainder = original.split("\n\n", 1)
    assert remainder.count("0..24") == 2
    four_b = first + "\n\n" + remainder.replace("0..24", "0..32")
    args.out.mkdir(parents=True, exist_ok=True)
    manifest = {"status": "frozen_before_search", "upstream_prompt_git_blob_sha1": blob,
                "changes_4b": "Architecture paragraph and two residual index bounds only",
                "author_results_included": False, "searches_started": False, "files": {}}
    for name, content in (("0p8b.initial.txt", original), ("4b.initial.txt", four_b)):
        path = args.out / name
        if path.exists():
            assert path.read_text() == content, "Refusing to change an already frozen prompt"
        else:
            path.write_text(content)
        manifest["files"][name] = hashlib.sha256(content.encode()).hexdigest()
    diff = "".join(difflib.unified_diff(original.splitlines(True), four_b.splitlines(True),
                                       fromfile="author-0p8b", tofile="independent-4b"))
    (args.out / "4b-prompt.diff").write_text(diff)
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest))


if __name__ == "__main__":
    main()
