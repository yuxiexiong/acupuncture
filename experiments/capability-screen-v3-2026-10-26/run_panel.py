"""Evaluate only missing selected pairs using the unchanged frozen v2 engine."""
import argparse
import json
from pathlib import Path
import sys
import time
import traceback

from prepare_panel import COUNTS, read, read_rows, sha, utc, validate_pair, verify_source, write

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "capability-damage-v2-2026-10-26"
sys.path.insert(0, str(SOURCE))
from model_engine import Engine, encode_pair, encode_text, token_hash


def json_metadata(metadata):
    """Match JSON receipt representation without relaxing any value comparisons."""
    return json.loads(json.dumps(metadata))


def verify_reused_tokens(row, tokenizer):
    item, calibration = row["item"], row["calibration"]
    tokens = encode_text(tokenizer, item["context"])
    assert calibration["input_token_count"] == len(tokens)
    assert calibration["input_token_sha256"] == token_hash(tokens)
    for output in row["outputs"].values():
        if item["request_type"] == "loglikelihood":
            for continuation, detail in zip(item["continuations"], output["choice_details"]):
                context_ids, continuation_ids = encode_pair(tokenizer, item["context"], continuation)
                assert detail["continuation_token_ids"] == continuation_ids
                assert detail["context_token_count"] == len(context_ids)
                assert detail["input_token_sha256"] == token_hash(context_ids + continuation_ids[:-1])
        else:
            assert output["input_token_sha256"] == token_hash(tokens)


def evaluate_pair(engine, item, index, protocol, partial, progress=None):
    started = time.monotonic()
    calibration_started = time.monotonic()
    calibration = engine.calibrate([item["context"]])[0]
    calibration_seconds = time.monotonic() - calibration_started
    row = {"id": item["id"], "benchmark": item["benchmark"], "item": item,
           "status": "started", "calibration": calibration, "outputs": {}}
    write(partial, [row])
    order = ("baseline", "evo") if index % 2 == 0 else ("evo", "baseline")
    for arm in order:
        arm_started = time.monotonic()
        if item["request_type"] == "loglikelihood":
            choices = engine.score([item["context"]] * len(item["continuations"]),
                item["continuations"], arm, [calibration] * len(item["continuations"]))
            output = {"status": "completed", "choice_loglikelihoods": [x["loglikelihood"] for x in choices],
                      "choice_details": choices}
        else:
            generation = item["gen_kwargs"]
            budget = protocol["max_new_tokens"][item["benchmark"]]
            assert generation["max_gen_toks"] == budget
            output = {"status": "completed", **engine.generate([item["context"]], arm, [calibration],
                       budget, generation["until"])[0]}
        output["arm_batch_seconds"] = time.monotonic() - arm_started
        row["outputs"][arm] = output
        write(partial, [row])
        if progress:
            progress({"id": item["id"], "arm": arm, "arm_seconds": output["arm_batch_seconds"],
                      "generated_tokens": output.get("generated_token_count"), "end_reason": output.get("end_reason")})
    row.update(status="completed", arm_order=list(order), ended_utc=utc(),
               timing={"calibration_seconds": calibration_seconds, "pair_seconds": time.monotonic() - started})
    return row


def run(args):
    protocol = read(ROOT / "protocol.json")
    panel = read(ROOT / "panel_manifest.json")
    reuse = read(ROOT / "reuse_manifest.json")
    assert protocol["status"] == "frozen_before_formal_inference"
    assert protocol["counts"] == panel["counts"] == COUNTS
    assert protocol["batch_sizes"] == {task: 1 for task in COUNTS} and protocol["shard_count"] == 2
    assert sha(ROOT / "panel_manifest.json") == protocol["panel_manifest_sha256"]
    assert sha(ROOT / "reuse_manifest.json") == protocol["reuse_manifest_sha256"]
    assert reuse["panel_manifest_sha256"] == protocol["panel_manifest_sha256"]
    assert {"prepare_panel.py", "run_panel.py", "run_worker.py"}.issubset(protocol["source_sha256"])
    for name, digest in protocol["source_sha256"].items():
        assert sha(ROOT / name) == digest, f"Changed frozen v3 source: {name}"
    old_protocol, _ = verify_source(SOURCE)
    assert (ROOT / panel["source_root"]).resolve() == SOURCE.resolve()
    assert sha(SOURCE / "protocol.json") == protocol["source_protocol_sha256"] == reuse["source_protocol_sha256"]
    for key in ("model", "arms", "intervention", "generation", "max_new_tokens"):
        assert protocol[key] == old_protocol[key], f"Changed inference condition: {key}"
    stop_path = ROOT / reuse["stop_receipt"]["file"]
    assert sha(stop_path) == reuse["stop_receipt"]["sha256"]
    stop = read(stop_path)
    assert stop["status"] == "stopped_by_user" and stop["remaining_live_processes"] == []
    specification = panel["files"][args.task]
    item_path = ROOT / specification["file"]
    assert sha(item_path) == specification["sha256"]
    all_items = read_rows(item_path)
    assert len(all_items) == specification["count"] == COUNTS[args.task]
    assert [item["id"] for item in all_items] == panel["selected_ids"][args.task]
    items = all_items[args.shard_index::2]
    validation_path = ROOT / protocol["preflight"][args.shard_index]["file"]
    assert sha(validation_path) == protocol["preflight"][args.shard_index]["sha256"]
    validation = read(validation_path)
    assert validation["status"] == "completed"
    assert validation["source_sha256"]["model_engine.py"] == sha(SOURCE / "model_engine.py")
    model = Path(protocol["model"]["remote_path"])
    assert model.resolve() == Path(validation["arguments"]["model"]).resolve()
    output = ROOT / "outputs" / f"{args.task}-shard{args.shard_index}-r01"
    output.mkdir(parents=True, exist_ok=False)
    receipt = {"status": "started", "started_utc": utc(), "task": args.task,
        "expected_pairs": len(items), "completed_pairs": 0, "new_pairs": 0, "reused_pairs": 0,
        "reused_ids": [], "new_ids": [], "execution_order": [item["id"] for item in items],
        "shard_index": args.shard_index, "shard_count": 2,
        "protocol_sha256": sha(ROOT / "protocol.json"), "panel_manifest_sha256": sha(ROOT / "panel_manifest.json"),
        "reuse_manifest_sha256": sha(ROOT / "reuse_manifest.json"), "items_sha256": sha(item_path),
        "source_sha256": protocol["source_sha256"], "source_engine_sha256": sha(SOURCE / "model_engine.py"),
        "validation_receipt_sha256": sha(validation_path), "new_inference_seconds": 0.0,
        "reuse_limit": reuse["limitation"]}
    started = time.monotonic()
    write(output / "receipt.json", receipt)
    try:
        legacy = ROOT.parent / "qwen35-neuron-steering-2026-10-25"
        sys.path.insert(0, str(legacy))
        from collect_raw import verify_assets
        assert sha(legacy / "collect_raw.py") == validation["asset_checker_sha256"]
        receipt["assets"] = verify_assets(model)
        assert receipt["assets"] == validation["assets"]
        engine = Engine(model, "cuda:0", batch_size=1)
        metadata = json_metadata(engine.metadata)
        receipt["engine"] = metadata
        assert metadata == validation["engine"], "Environment differs from accepted v2 preflight"
        engine.verify_unchanged()
        receipt["setup_seconds"] = time.monotonic() - started
        for index, item in enumerate(items):
            entry = reuse["entries"].get(item["id"])
            if entry is None:
                continue
            assert entry["task"] == args.task
            source_path, source_receipt = SOURCE / entry["source_file"], SOURCE / entry["source_receipt_file"]
            assert sha(source_receipt) == entry["source_receipt_sha256"]
            old = read(source_receipt)
            assert old["engine"] == metadata and old["assets"] == receipt["assets"]
            assert old["protocol_sha256"] == protocol["source_protocol_sha256"]
            assert sha(source_path) == entry["sha256"]
            rows = read_rows(source_path)
            assert len(rows) == 1
            validate_pair(rows[0], item, engine.metadata)
            verify_reused_tokens(rows[0], engine.tokenizer)
            target = output / f"{index:05d}.jsonl"
            target.write_bytes(source_path.read_bytes())
            assert sha(target) == entry["sha256"]
            receipt["reused_ids"].append(item["id"])
        receipt["reused_pairs"] = len(receipt["reused_ids"])
        receipt["completed_pairs"] = receipt["reused_pairs"]
        write(output / "receipt.json", receipt)
        def progress(value):
            print(json.dumps({"task": args.task, "shard": args.shard_index, **value}), flush=True)
        progress({"phase": "ready", "expected_pairs": len(items), "reused_pairs": receipt["reused_pairs"]})
        for index, item in enumerate(items):
            if item["id"] in reuse["entries"]:
                continue
            partial = output / f"{index:05d}.partial.json"
            row = evaluate_pair(engine, item, index, protocol, partial, progress)
            validate_pair(row, item, engine.metadata)
            completed = output / f"{index:05d}.jsonl"
            assert not completed.exists()
            completed.write_text(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
            partial.unlink()
            receipt["completed_pairs"] += 1
            receipt["new_pairs"] += 1
            receipt["new_ids"].append(item["id"])
            receipt["new_inference_seconds"] += row["timing"]["pair_seconds"]
            receipt["last_pair_seconds"] = row["timing"]["pair_seconds"]
            write(output / "receipt.json", receipt)
            progress({key: receipt[key] for key in ("completed_pairs", "expected_pairs", "new_pairs", "reused_pairs", "new_inference_seconds", "last_pair_seconds")})
        assert receipt["completed_pairs"] == len(items)
        receipt.update(engine.verify_unchanged())
        receipt["status"] = "completed"
    except Exception as error:
        receipt.update(status="failed", error=str(error), traceback=traceback.format_exc())
        raise
    finally:
        receipt.update(ended_utc=utc(), elapsed_seconds=time.monotonic() - started)
        write(output / "receipt.json", receipt)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=tuple(COUNTS), required=True)
    parser.add_argument("--shard-index", type=int, choices=(0, 1), required=True)
    run(parser.parse_args())
