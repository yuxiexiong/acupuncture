"""Check every frozen request's token budget without loading model weights."""
import argparse
import json
import math
from pathlib import Path

from model_engine import encode_pair, encode_text
from prepare_tasks import encode, save_once, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(args.model, local_files_only=True, trust_remote_code=False)
    config = json.loads((args.model / "config.json").read_text())
    limit = config.get("text_config", config)["max_position_embeddings"]
    manifest = json.loads(args.manifest.read_text())
    records, summary = [], {}
    entries = {**manifest["files"], "development": manifest["development"]}
    for task, meta in entries.items():
        path = args.manifest.parent / meta["file"]
        assert sha(path) == meta["sha256"]
        lengths = []
        for line in path.read_text().splitlines():
            item = json.loads(line)
            context_length = len(encode_text(tokenizer, item["context"]))
            assert context_length > 1
            row = {"id": item["id"], "context_tokens": context_length}
            if item["request_type"] == "loglikelihood":
                pairs = [encode_pair(tokenizer, item["context"], choice) for choice in item["continuations"]]
                row["continuation_tokens"] = [len(pair[1]) for pair in pairs]
                row["max_total_tokens"] = max(len(a) + len(b) for a, b in pairs)
            else:
                row["max_new_tokens"] = item["gen_kwargs"]["max_gen_toks"]
                row["max_total_tokens"] = context_length + row["max_new_tokens"]
            assert row["max_total_tokens"] <= limit, row
            lengths.append(row)
        assert len(lengths) == meta["count"]
        contexts = sorted(row["context_tokens"] for row in lengths)
        summary[task] = {"count": len(lengths), "context_min": contexts[0],
                         "context_p95": contexts[math.ceil(len(contexts) * .95) - 1],
                         "context_max": contexts[-1],
                         "max_total_tokens": max(row["max_total_tokens"] for row in lengths)}
        records.extend(lengths)
        print(task, summary[task], flush=True)
    args.output.mkdir(parents=True, exist_ok=True)
    data_path = args.output / "token_lengths.jsonl"
    save_once(data_path, b"".join(encode(row) + b"\n" for row in records))
    receipt = {"status": "all_requests_fit_without_truncation", "model_path": str(args.model),
               "max_position_embeddings": limit, "summary": summary,
               "token_lengths_sha256": sha(data_path), "task_manifest_sha256": sha(args.manifest),
               "source_sha256": sha(__file__), "model_engine_sha256": sha(Path(__file__).with_name("model_engine.py")),
               "tokenizer_source_sha256": {p.name: sha(p) for p in args.model.glob("*.json")
                                          if p.name in ("config.json", "tokenizer.json", "tokenizer_config.json")}}
    save_once(args.output / "token_length_audit.json", json.dumps(receipt, indent=2, sort_keys=True).encode() + b"\n")


if __name__ == "__main__":
    main()
