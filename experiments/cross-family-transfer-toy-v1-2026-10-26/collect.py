"""Clean paired character-boundary collection; no token-ordinal alignment fallback."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback

from engine import CrossFamilyEngine, LAYERS, LlamaTokenizer, LEGACY, load_tokenizer, text_hash, token_hash

# Reuse only the frozen target-contrast rendering/selection, not its map alignment.
sys.path.insert(0, str(LEGACY))
from collect_activations import prepare_tokens as native_contrast_tokens

ALIGNMENT_VERSION = "common-plain-character-boundaries-v1"


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    temporary = Path(str(path) + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def read_rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def plain_text(row):
    if row["kind"] != "dialogue":
        return row["text"]
    assert all(message["role"] in ("system", "user", "assistant") for message in row["messages"])
    return "\n\n".join(message["role"] + ":\n" + message["content"] for message in row["messages"])


def token_boundaries(tokenizer, text, limit=512):
    encoded = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)
    tokens, offsets = list(encoded["input_ids"]), [tuple(pair) for pair in encoded["offset_mapping"]]
    assert len(tokens) == len(offsets) and tokens
    assert all(0 <= left <= right <= len(text) for left, right in offsets), "Offsets must index Unicode characters"
    prefix = [tokenizer.bos_token_id] if isinstance(tokenizer, LlamaTokenizer) else []
    boundaries = {}
    # Inspect the full sequence: a duplicate/overlapping successor beyond the token cap
    # must not make a truncated byte fragment look like a complete character boundary.
    for i, (left, right) in enumerate(offsets):
        if i + len(prefix) >= limit:
            break
        if right <= left:
            continue
        successor = next((a for a, b in offsets[i + 1:] if b > a), len(text))
        if successor < right:
            continue
        decoded = tokenizer.decode(tokens[:i + 1], skip_special_tokens=False, clean_up_tokenization_spaces=False)
        if decoded == text[:right]:
            boundaries[right] = i + len(prefix)
    assert boundaries, "No complete round-tripping text boundaries inside token budget"
    return prefix + tokens, boundaries


def aligned_tokens(source_tokenizer, target_tokenizer, row, limit=512, count=128):
    text = plain_text(row)
    source, sb = token_boundaries(source_tokenizer, text, limit)
    target, tb = token_boundaries(target_tokenizer, text, limit)
    common = sorted(sb.keys() & tb.keys())
    assert common, f"No common character boundary for {row['id']}"
    count = min(count, len(common))
    ends = [common[len(common) // 2]] if count == 1 else [common[i * (len(common) - 1) // (count - 1)] for i in range(count)]
    source_positions, target_positions = [sb[end] for end in ends], [tb[end] for end in ends]
    source, target = source[:source_positions[-1] + 1], target[:target_positions[-1] + 1]
    assert len(source) <= limit and len(target) <= limit
    alignment = {"version": ALIGNMENT_VERSION, "text_sha256": text_hash(text), "char_end": ends,
        "source_positions": source_positions, "target_positions": target_positions,
        "source_token_sha256": token_hash(source), "target_token_sha256": token_hash(target)}
    alignment["alignment_sha256"] = text_hash(json.dumps(alignment, sort_keys=True, separators=(",", ":")))
    return text, source, target, alignment


def tokenizer_identity(path):
    root = Path(path)
    names = ("config.json", "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json", "generation_config.json")
    return {"path": str(root.resolve()), "files": {name: sha(root / name) for name in names if (root / name).is_file()}}


def run(args):
    import torch
    output, data = Path(args.output), Path(args.data)
    output.mkdir(parents=True, exist_ok=True)
    receipt_path = output / "receipt.json"
    if receipt_path.exists() or any(output.iterdir()):
        raise RuntimeError("Collection output is not empty; preserve it and use a separate attempt directory")
    receipt = {"status": "running", "started_utc": utc(), "arguments": vars(args), "completed_documents": 0,
        "files": {}, "alignment_version": ALIGNMENT_VERSION,
        "source_sha256": {name: sha(Path(__file__).parent / name) for name in ("engine.py", "collect.py")},
        "inherited_source_sha256": {name: sha(LEGACY / name) for name in ("transfer_engine.py", "collect_activations.py")}}
    receipt["inherited_source_sha256"]["../capability-damage-v2-2026-10-26/model_engine.py"] = sha(
        LEGACY.parent / "capability-damage-v2-2026-10-26/model_engine.py")
    write_json(receipt_path, receipt)
    started = time.monotonic()
    try:
        source_tokenizer, target_tokenizer = load_tokenizer(args.source_tokenizer), load_tokenizer(args.target_tokenizer)
        assert not isinstance(source_tokenizer, LlamaTokenizer) and isinstance(target_tokenizer, LlamaTokenizer)
        selected_path = args.source_tokenizer if args.role == "source" else args.target_tokenizer
        assert Path(args.model).resolve() == Path(selected_path).resolve(), "Model/tokenizer checkpoint mismatch"
        receipt["tokenizers"] = {"source": tokenizer_identity(args.source_tokenizer), "target": tokenizer_identity(args.target_tokenizer)}
        engine = CrossFamilyEngine(args.model, args.device)
        receipt["engine"] = engine.metadata
        columns = {str(l): engine.modules[l].weight.detach().float().cpu() for l in LAYERS}
        torch.save({"columns": columns, "metadata": engine.metadata}, output / "columns.pt")
        receipt["files"]["columns.pt"] = sha(output / "columns.pt")
        rms = {str(l): torch.zeros(columns[str(l)].shape[1], dtype=torch.float64) for l in LAYERS}
        sets = ["map_train", "map_val"] + (["contrast"] if args.role == "target" else [])
        index = {}
        for split in sets:
            rows = read_rows(data / (split + ".jsonl"))
            assert len(rows) == {"map_train": 256, "map_val": 64, "contrast": 128}[split]
            assert len({row["id"] for row in rows}) == len(rows)
            receipt.setdefault("data_sha256", {})[split] = sha(data / (split + ".jsonl"))
            index[split] = []
            (output / split).mkdir()
            for row in rows:
                row_started = time.monotonic()
                alignment = {}
                if split == "contrast":
                    text, tokens, positions, _ = native_contrast_tokens(engine.tokenizer, row, contrast=True)
                    if isinstance(engine.tokenizer, LlamaTokenizer):
                        assert tokens[0] == engine.tokenizer.bos_token_id, "Native LLaMA contrast template lacks BOS"
                else:
                    text, source_ids, target_ids, alignment = aligned_tokens(source_tokenizer, target_tokenizer, row)
                    tokens = source_ids if args.role == "source" else target_ids
                    positions = alignment[args.role + "_positions"]
                inputs = engine._inputs([tokens])
                captured, handles = {}, []
                try:
                    for layer in LAYERS:
                        def residual_hook(_module, _args, value, layer=layer):
                            residual = value[0] if isinstance(value, tuple) else value
                            captured.setdefault(str(layer), {})["residual"] = residual[0, positions].detach().float().cpu()
                        def channel_hook(_module, values, layer=layer):
                            captured.setdefault(str(layer), {})["activation"] = values[0][0, positions].detach().float().cpu()
                        handles.append(engine.layers[layer].register_forward_hook(residual_hook))
                        handles.append(engine.modules[layer].register_forward_pre_hook(channel_hook))
                    with torch.inference_mode():
                        engine.model(**inputs, use_cache=False, logits_to_keep=1)
                finally:
                    for handle in handles:
                        handle.remove()
                payload = {"id": row["id"], "role": args.role, "text_sha256": text_hash(text),
                    "input_token_sha256": token_hash(tokens), "tokens": tokens, "positions": positions,
                    **alignment, "layers": {}}
                for layer in LAYERS:
                    key = str(layer)
                    state, activation = captured[key]["residual"], captured[key]["activation"]
                    assert torch.isfinite(state).all() and torch.isfinite(activation).all()
                    if split == "contrast":
                        payload["layers"][key] = {"residual_mean": state.mean(0), "activation_mean": activation.mean(0)}
                    else:
                        payload["layers"][key] = {"residual": state}
                        if split == "map_train":
                            rms[key] += activation.double().square().mean(0) / len(rows)
                if split == "contrast":
                    payload.update({key: row[key] for key in ("scenario_id", "stance", "style")})
                assert Path(row["id"]).name == row["id"] and row["id"] not in (".", "..")
                path = output / split / (row["id"] + ".pt")
                torch.save(payload, path)
                entry = {"id": row["id"], "file": str(path.relative_to(output)), "sha256": sha(path),
                    "tokens": len(tokens), "positions": len(positions), "seconds": time.monotonic() - row_started}
                if alignment:
                    entry["alignment_sha256"] = alignment["alignment_sha256"]
                index[split].append(entry)
                receipt["completed_documents"] += 1
                receipt.update(current_split=split, last_document_id=row["id"], elapsed_seconds=time.monotonic() - started)
                write_json(receipt_path, receipt)
                print(json.dumps({"phase": split, "id": row["id"], "completed": receipt["completed_documents"]}), flush=True)
        torch.save({layer: values.sqrt().float() for layer, values in rms.items()}, output / "natural_rms.pt")
        receipt["files"]["natural_rms.pt"] = sha(output / "natural_rms.pt")
        write_json(output / "index.json", index)
        receipt["files"]["index.json"] = sha(output / "index.json")
        receipt.update(engine.verify_unchanged())
        receipt.update(status="completed", ended_utc=utc(), elapsed_seconds=time.monotonic() - started)
    except Exception as error:
        receipt.update(status="failed", ended_utc=utc(), error=str(error), traceback=traceback.format_exc())
        raise
    finally:
        write_json(receipt_path, receipt)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("model", "source-tokenizer", "target-tokenizer", "data", "output"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--role", choices=("source", "target"), required=True)
    parser.add_argument("--device", default="cuda:0")
    run(parser.parse_args())
