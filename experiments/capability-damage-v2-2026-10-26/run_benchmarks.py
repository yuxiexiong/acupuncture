"""Run frozen official requests through one unchanged model, paired O/EVO."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback

from model_engine import Engine, mechanical_checks


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def read_rows(path):
    with path.open() as stream:
        return [json.loads(line) for line in stream if line.strip()]


def preflight(args):
    args.output.mkdir(parents=True, exist_ok=False)
    # Reuse the verified asset checker without modifying historical code.
    legacy = Path(__file__).resolve().parent.parent / "qwen35-neuron-steering-2026-10-25"
    sys.path.insert(0, str(legacy))
    from collect_raw import verify_assets
    receipt = {"status": "started", "started_utc": utc(), "phase": "non_test_technical_validation",
               "arguments": {k: str(v) for k, v in vars(args).items()},
               "source_sha256": {p.name: sha(p) for p in Path(__file__).parent.glob("*.py")},
               "asset_checker_sha256": sha(legacy / "collect_raw.py")}
    write(args.output / "receipt.json", receipt)
    try:
        receipt["assets"] = verify_assets(args.model)
        engine = Engine(args.model, args.device, args.batch_size)
        receipt["engine"] = engine.metadata
        checks = mechanical_checks(engine, args.batch_size)
        write(args.output / "mechanical_checks.json", checks)
        assert checks["status"] == "completed", checks.get("failures")
        development = read_rows(args.items)
        source = [row for row in development if row["benchmark"] == "gsm8k"]
        assert len(source) >= 2
        contexts = [source[i % len(source)]["context"] for i in range(args.batch_size)]
        started = time.monotonic()
        scales = engine.calibrate(contexts)
        calibration_seconds = time.monotonic() - started
        throughput = {"non_test_item_ids": [row["id"] for row in source],
                      "note": "Repeated non-test GSM contexts; 128-token probe, not a full-run ETA.",
                      "batch_size": args.batch_size, "calibration_seconds": calibration_seconds,
                      "context_token_counts": [row["input_token_count"] for row in scales], "outputs": {}}
        for arm in ("baseline", "evo"):
            started = time.monotonic()
            answers = engine.generate(contexts, arm, scales, 128, source[0]["gen_kwargs"]["until"])
            elapsed = time.monotonic() - started
            throughput["outputs"][arm] = {"seconds": elapsed, "generated_tokens": sum(a["generated_token_count"] for a in answers),
                                          "answers": answers}
        write(args.output / "throughput.json", throughput)
        receipt.update(engine.verify_unchanged())
        receipt["status"] = "completed"
    except Exception as error:
        receipt.update(status="failed", error=str(error), traceback=traceback.format_exc())
        raise
    finally:
        receipt["ended_utc"] = utc()
        write(args.output / "receipt.json", receipt)
    print(json.dumps({"status": receipt["status"], "batch_size": args.batch_size,
                      "throughput": {arm: {k: v for k, v in row.items() if k != "answers"}
                                     for arm, row in throughput["outputs"].items()}}, ensure_ascii=False), flush=True)


def run(args):
    root = Path(__file__).resolve().parent
    protocol = json.loads((root / "protocol.json").read_text())
    manifest = json.loads((root / "task_manifest.json").read_text())
    specification = manifest["files"][args.task]
    assert sha(args.items) == specification["sha256"]
    items = read_rows(args.items)
    assert len(items) == specification["count"] == protocol["counts"][args.task]
    assert len({row["id"] for row in items}) == len(items)
    assert args.batch_size == protocol["batch_sizes"][args.task]
    assert args.shard_count == protocol["shard_count"] and 0 <= args.shard_index < args.shard_count
    for name, digest in protocol["source_sha256"].items():
        assert sha(root / name) == digest, f"Changed frozen source: {name}"
    validation = json.loads(args.validation.read_text())
    assert validation["status"] == "completed"
    assert validation["engine"]["batch_size"] == args.batch_size
    assert validation["source_sha256"]["model_engine.py"] == sha(root / "model_engine.py")
    assert args.model.resolve() == Path(validation["arguments"]["model"]).resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    receipt = {"status": "started", "started_utc": utc(), "task": args.task, "full_task_pairs": len(items),
               "completed_pairs": 0, "arguments": {k: str(v) for k, v in vars(args).items()},
               "protocol_sha256": sha(root / "protocol.json"), "task_manifest_sha256": sha(root / "task_manifest.json"),
               "items_sha256": sha(args.items), "validation_receipt_sha256": sha(args.validation),
               "source_sha256": protocol["source_sha256"]}
    write(args.output / "receipt.json", receipt)
    started = time.monotonic()
    try:
        legacy = root.parent / "qwen35-neuron-steering-2026-10-25"
        sys.path.insert(0, str(legacy))
        from collect_raw import verify_assets
        assert sha(legacy / "collect_raw.py") == validation["asset_checker_sha256"]
        receipt["assets"] = verify_assets(args.model)
        assert receipt["assets"] == validation["assets"]
        engine = Engine(args.model, args.device, args.batch_size)
        receipt["engine"] = engine.metadata
        # Fixed length ordering reduces padding; both arms share identical batches.
        items.sort(key=lambda row: (-len(engine.tokenizer.encode(row["context"])), row["id"]))
        # Two identical GPUs process disjoint, interleaved task items. Each item
        # still contains both arms with the same settings and calibration.
        items = items[args.shard_index::args.shard_count]
        receipt["expected_pairs"] = len(items)
        receipt["execution_order"] = [row["id"] for row in items]
        write(args.output / "receipt.json", receipt)
        for start in range(0, len(items), args.batch_size):
            selected = items[start:start + args.batch_size]
            contexts = [item["context"] for item in selected]
            batch_started = time.monotonic()
            calibrations = engine.calibrate(contexts)
            rows = [{"id": item["id"], "benchmark": args.task, "item": item, "status": "started",
                     "calibration": calibration, "outputs": {}} for item, calibration in zip(selected, calibrations)]
            partial = args.output / f"{start:05d}.partial.json"
            write(partial, rows)
            order = ("baseline", "evo") if start // args.batch_size % 2 == 0 else ("evo", "baseline")
            for arm in order:
                arm_started = time.monotonic()
                if selected[0]["request_type"] == "loglikelihood":
                    context_requests, continuation_requests, scales = [], [], []
                    for item, calibration in zip(selected, calibrations):
                        context_requests.extend([item["context"]] * len(item["continuations"]))
                        continuation_requests.extend(item["continuations"])
                        scales.extend([calibration] * len(item["continuations"]))
                    scored = engine.score(context_requests, continuation_requests, arm, scales)
                    cursor = 0
                    for row in rows:
                        count = len(row["item"]["continuations"])
                        choices = scored[cursor:cursor + count]
                        row["outputs"][arm] = {"status": "completed", "choice_loglikelihoods": [x["loglikelihood"] for x in choices],
                                               "choice_details": choices}
                        cursor += count
                    assert cursor == len(scored)
                else:
                    generation = selected[0]["gen_kwargs"]
                    assert all(row["gen_kwargs"] == generation for row in selected)
                    budget = protocol["max_new_tokens"][args.task]
                    assert generation["max_gen_toks"] == budget
                    answers = engine.generate(contexts, arm, calibrations, budget, generation["until"])
                    for row, answer in zip(rows, answers):
                        row["outputs"][arm] = {"status": "completed", **answer}
                for row in rows:
                    row["outputs"][arm]["arm_batch_seconds"] = time.monotonic() - arm_started
                write(partial, rows)
            for row in rows:
                row.update(status="completed", arm_order=order, ended_utc=utc())
            completed = args.output / f"{start:05d}.jsonl"
            assert not completed.exists()
            completed.write_text("".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows))
            partial.unlink()  # This batch's complete records supersede its temporary checkpoint.
            receipt["completed_pairs"] += len(rows)
            receipt["last_batch_seconds"] = time.monotonic() - batch_started
            write(args.output / "receipt.json", receipt)
            print(json.dumps({"task": args.task, "completed": receipt["completed_pairs"], "total": len(items),
                              "batch_seconds": receipt["last_batch_seconds"]}), flush=True)
        receipt.update(engine.verify_unchanged())
        receipt["status"] = "completed"
    except Exception as error:
        receipt.update(status="failed", error=str(error), traceback=traceback.format_exc())
        raise
    finally:
        receipt.update(ended_utc=utc(), elapsed_seconds=time.monotonic() - started)
        write(args.output / "receipt.json", receipt)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--task", choices=("mmlu", "arc_challenge", "gsm8k", "humaneval"))
    for name in ("model", "items", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--validation", type=Path)
    parser.add_argument("--batch-size", type=int, required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--shard-index", type=int, default=0)
    options = parser.parse_args()
    if options.preflight:
        preflight(options)
    else:
        assert options.task and options.validation
        run(options)
