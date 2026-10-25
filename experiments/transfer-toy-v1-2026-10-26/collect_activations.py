"""Collect clean paired mapping states and fixed target contrast baselines; no generation."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import traceback

from transfer_engine import TransferEngine, LAYERS, text_hash, token_hash


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def write_json(path, value):
    temporary = Path(str(path) + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def evenly(pool, count):
    count = min(count, len(pool))
    if count == 0:
        return []
    if count == 1:
        return [pool[len(pool) // 2]]
    return [pool[i * (len(pool) - 1) // (count - 1)] for i in range(count)]


def render(tokenizer, row, contrast=False):
    if contrast:
        messages = [{"role": "user", "content": row["prompt"]},
                    {"role": "assistant", "content": row["continuation"]}]
    elif row["kind"] == "dialogue":
        messages = row["messages"]
    else:
        return row["text"], None
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False, enable_thinking=False)
    spans, cursor = [], 0
    for message in messages:
        start = text.find(message["content"], cursor)
        assert start >= cursor, "Template did not preserve literal message content"
        end = start + len(message["content"])
        spans.append((start, end, message["role"]))
        cursor = end
    return text, spans


def prepare_tokens(tokenizer, row, contrast=False):
    text, spans = render(tokenizer, row, contrast)
    encoded = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)
    tokens, offsets = encoded["input_ids"][:512], encoded["offset_mapping"][:512]
    assert len(tokens) >= 2
    groups = {"user": [], "assistant": [], "template": []}
    for i, (left, right) in enumerate(offsets):
        role = next((role for a, b, role in (spans or []) if right > left and left >= a and right <= b), "template")
        groups[role].append(i)
    if contrast:
        positions = groups["assistant"]
        assert positions, f"No assistant content tokens for {row['id']}"
        # The contrast answer must fit in the frozen 512-token clean-input budget.
        assert spans[-1][1] <= offsets[-1][1] or len(encoded["input_ids"]) <= 512
    elif spans:
        budget = min(128, len(tokens))
        template_count = min(len(groups["template"]), budget // 10)
        content_budget = budget - template_count
        user_count = min(len(groups["user"]), content_budget // 2)
        assistant_count = min(len(groups["assistant"]), content_budget - user_count)
        user_count = min(len(groups["user"]), content_budget - assistant_count)
        positions = evenly(groups["user"], user_count) + evenly(groups["assistant"], assistant_count) + evenly(groups["template"], template_count)
        positions.sort()
        assert len(positions) <= 128
    else:
        positions = evenly(list(range(len(tokens))), 128)
    assert positions and len(set(positions)) == len(positions)
    return text, tokens, positions, groups


def run(args):
    import torch
    output, data = Path(args.output), Path(args.data)
    output.mkdir(parents=True, exist_ok=True)
    receipt_path = output / "receipt.json"
    if receipt_path.exists():
        previous = json.loads(receipt_path.read_text())
        if previous.get("status") == "completed":
            raise RuntimeError("Completed collection exists; root must validate and reuse it explicitly")
        raise RuntimeError("Partial collection exists; preserve it and use a separate attempt directory")
    receipt = {"status": "running", "started_utc": utc(), "arguments": vars(args), "completed_documents": 0,
               "files": {}, "source_sha256": {name: sha(Path(__file__).parent / name) for name in ("transfer_engine.py", "collect_activations.py")}}
    write_json(receipt_path, receipt)
    started = time.monotonic()
    try:
        engine = TransferEngine(args.model, args.device)
        receipt["engine"] = engine.metadata
        columns = {str(l): engine.modules[l].weight.detach().float().cpu() for l in LAYERS}
        torch.save({"columns": columns, "metadata": engine.metadata}, output / "columns.pt")
        receipt["files"]["columns.pt"] = sha(output / "columns.pt")
        rms = {str(l): torch.zeros(columns[str(l)].shape[1], dtype=torch.float64) for l in LAYERS}
        sets = ["map_train", "map_val"] + (["contrast"] if args.role == "target" else [])
        index = {}
        for split in sets:
            rows = read_rows(data / (split + ".jsonl"))
            receipt.setdefault("data_sha256", {})[split] = sha(data / (split + ".jsonl"))
            index[split] = []
            (output / split).mkdir()
            for row in rows:
                row_started = time.monotonic()
                text, tokens, positions, groups = prepare_tokens(engine.tokenizer, row, split == "contrast")
                inputs = engine._inputs([tokens])
                captured, handles = {}, []
                try:
                    for layer in LAYERS:
                        def residual_hook(_module, _args, value, layer=layer):
                            residual = value[0] if isinstance(value, tuple) else value
                            captured.setdefault(str(layer), {})["residual"] = residual[0, positions].detach().float().cpu()
                        def channel_hook(_module, args, layer=layer):
                            captured.setdefault(str(layer), {})["activation"] = args[0][0, positions].detach().float().cpu()
                        handles.append(engine.layers[layer].register_forward_hook(residual_hook))
                        handles.append(engine.modules[layer].register_forward_pre_hook(channel_hook))
                    with torch.inference_mode():
                        engine.model(**inputs, use_cache=False, logits_to_keep=1)
                finally:
                    for handle in handles:
                        handle.remove()
                payload = {"id": row["id"], "text_sha256": text_hash(text), "input_token_sha256": token_hash(tokens),
                           "tokens": tokens, "positions": positions, "layers": {}}
                for layer in LAYERS:
                    key = str(layer)
                    state, activation = captured[key]["residual"], captured[key]["activation"]
                    assert torch.isfinite(state).all() and torch.isfinite(activation).all(), "Nonfinite clean states"
                    if split == "contrast":
                        payload["layers"][key] = {"residual_mean": state.mean(0), "activation_mean": activation.mean(0)}
                    else:
                        payload["layers"][key] = {"residual": state}
                        if split == "map_train":
                            rms[key] += activation.double().square().mean(0) / len(rows)
                if split == "contrast":
                    payload.update({key: row[key] for key in ("scenario_id", "stance", "style")})
                path = output / split / (row["id"] + ".pt")
                torch.save(payload, path)
                entry = {"id": row["id"], "file": str(path.relative_to(output)), "sha256": sha(path),
                         "tokens": len(tokens), "positions": len(positions), "seconds": time.monotonic() - row_started}
                index[split].append(entry)
                receipt["completed_documents"] += 1
                receipt.update(current_split=split, last_document_id=row["id"], elapsed_seconds=time.monotonic() - started)
                write_json(receipt_path, receipt)
                print(json.dumps({"phase": split, "id": row["id"], "completed": receipt["completed_documents"], "seconds": entry["seconds"]}), flush=True)
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
    parser.add_argument("--model", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--role", choices=("source", "target"), required=True)
    parser.add_argument("--device", default="cuda:0")
    run(parser.parse_args())
