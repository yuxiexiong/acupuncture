"""Frozen 1,400-pair panel: stage 1 dense transfer, stage 2 sparse recipe."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback

from common import BENCHMARK_ARMS, LEGACY, ROOT, require_stage, source_hashes, verify_freeze
from engine import CrossFamilyEngine

sys.path.append(str(LEGACY))
from run_benchmark import (COUNTS, ORDER, PANEL_SHA, PROTOCOL_SHA, V3,
                           frozen_panel, load_v3, read, rows, sha, utc, validate_pair, write)


def arm_bindings(stage):
    return {"baseline": "T_0", "evo": BENCHMARK_ARMS[stage]}


def run_root(output, stage):
    output = Path(output)
    assert output.name == "benchmark" and output.parent.name == f"stage{stage}", "Use run/stageN/benchmark"
    return output.parent.parent


class BenchmarkEngine:
    def __init__(self, engine, stage):
        self.engine, self.bindings = engine, arm_bindings(stage)

    def calibrate(self, contexts):
        return self.engine.calibrate(contexts)

    def score(self, contexts, continuations, arm, calibrations):
        return self.engine.score(contexts, continuations, self.bindings[arm], calibrations)

    def generate(self, contexts, arm, calibrations, budget, stops):
        return self.engine.generate(contexts, self.bindings[arm], calibrations, budget, stops)


def native_metadata(engine):
    metadata = json.loads(json.dumps(engine.metadata))
    assert engine.batch_size == metadata["batch_size"] == 1
    assert metadata["dtype"] == "bfloat16" and metadata["attention_backend"] == "eager"
    assert sorted(map(int, metadata["effective_stop_tokens"])) == sorted(engine.stop_ids)
    assert metadata["pad_token_id"] == engine.pad_id and engine.stop_ids
    # Target official EOS/BOS settings come from the adapter, never the Qwen panel.
    assert metadata["bos_token_id"] is not None
    return metadata


def run(args, engine_factory=CrossFamilyEngine):
    verify_freeze(args.freeze)
    root = run_root(args.output, args.stage)
    require_stage(args.stage, root, bundle=args.conditions, freeze=args.freeze)
    protocol, panel, items = frozen_panel()
    bindings = arm_bindings(args.stage)
    frozen = source_hashes()
    frozen.update({str(Path(p).resolve()): sha(p) for p in (args.conditions, args.freeze)})
    destination = args.output / f"shard-{args.shard_index}"
    destination.mkdir(parents=True, exist_ok=False)
    receipt_path = destination / "receipt.json"
    started = time.monotonic()
    receipt = {"status": "started", "started_utc": utc(), "pid": os.getpid(), "stage": args.stage,
        "freeze_sha256": sha(args.freeze), "model": str(args.model.resolve()),
        "conditions": str(args.conditions.resolve()), "conditions_sha256": sha(args.conditions),
        "shard_index": args.shard_index, "shard_count": 2, "expected_pairs": 700, "completed_pairs": 0,
        "protocol_sha256": PROTOCOL_SHA, "panel_manifest_sha256": PANEL_SHA,
        "source_sha256": frozen, "arm_bindings": bindings, "task_order": ORDER[args.shard_index],
        "tasks": {}, "inference_seconds": 0.0, "prior_4b_outputs_reused": False,
        "generation_token_policy": "Target official EOS and explicit BOS; frozen task stops and token budgets unchanged"}
    write(receipt_path, receipt)
    try:
        engine = engine_factory(args.model, device="cuda:0", batch_size=1, bundle=args.conditions)
        assert set(bindings.values()).issubset(engine.conditions)
        receipt["engine"] = native_metadata(engine)
        receipt["model_small_file_sha256"] = {path.name: sha(path) for path in args.model.iterdir()
            if path.is_file() and path.name in {"config.json", "generation_config.json", "tokenizer_config.json", "tokenizer.json"}}
        receipt["setup_seconds"] = time.monotonic() - started
        adapter, evaluate = BenchmarkEngine(engine, args.stage), load_v3("run_panel").evaluate_pair
        for task in ORDER[args.shard_index]:
            output = destination / task
            output.mkdir()
            selected = items[task][args.shard_index::2]
            state = {"status": "started", "expected_pairs": len(selected), "completed_pairs": 0,
                "started_utc": utc(), "inference_seconds": 0.0}
            receipt["tasks"][task] = state
            write(receipt_path, receipt)
            for index, item in enumerate(selected):
                partial = output / f"{index:05d}.partial.json"
                row = evaluate(adapter, item, index, protocol, partial)
                validate_pair(row, item)
                if item["request_type"] != "loglikelihood":
                    for value in row["outputs"].values():
                        if value["end_reason"] == "eos_token":
                            assert value["token_ids"][-1] in engine.stop_ids
                row["transfer_provenance"] = {"model": receipt["model"],
                    "conditions_sha256": receipt["conditions_sha256"], "arm_bindings": bindings}
                final = output / f"{index:05d}.jsonl"
                with final.open("x") as handle:
                    handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
                partial.unlink()
                elapsed = row["timing"]["pair_seconds"]
                state["completed_pairs"] += 1
                state["inference_seconds"] += elapsed
                receipt["completed_pairs"] += 1
                receipt["inference_seconds"] += elapsed
                receipt.update(last_pair_seconds=elapsed, last_completed_id=item["id"], updated_utc=utc())
                write(receipt_path, receipt)
                print(json.dumps({"phase": "benchmark", "stage": args.stage, "task": task,
                    "shard": args.shard_index, "completed_pairs": receipt["completed_pairs"],
                    "expected_pairs": 700, "pair_seconds": elapsed}), flush=True)
            state.update(status="completed", ended_utc=utc())
            write(receipt_path, receipt)
        receipt.update(engine.verify_unchanged())
        for path, digest in frozen.items():
            assert sha(path) == digest, f"Execution source changed during run: {path}"
        verify_freeze(args.freeze)
        require_stage(args.stage, root, bundle=args.conditions, freeze=args.freeze)
        assert receipt["completed_pairs"] == receipt["expected_pairs"]
        receipt.update(status="completed", records_sha256={str(p.relative_to(destination)): sha(p)
            for p in sorted(destination.glob("*/[0-9]*.jsonl"))})
    except Exception as error:
        receipt.update(status="failed", error=str(error), traceback=traceback.format_exc())
        raise
    finally:
        receipt.update(ended_utc=utc(), wall_seconds=time.monotonic() - started)
        write(receipt_path, receipt)


def finish_module(stage):
    spec = importlib.util.spec_from_file_location(f"cross_family_finish_stage{stage}", LEGACY / "finish_benchmark.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ARM_NAMES = arm_bindings(stage)
    return module


def verified_records(output, items, stage, freeze):
    records, paths, workers = finish_module(stage).verified_records(output, items)
    for worker in workers:
        assert worker["stage"] == stage and worker["freeze_sha256"] == sha(freeze)
        metadata = worker["engine"]
        assert metadata["batch_size"] == 1 and metadata["dtype"] == "bfloat16"
        assert metadata["attention_backend"] == "eager" and metadata["bos_token_id"] is not None
        assert metadata["effective_stop_tokens"]
        stops = set(map(int, metadata["effective_stop_tokens"]))
        for row in records:
            for value in row["outputs"].values():
                if value.get("end_reason") == "eos_token":
                    assert value["token_ids"][-1] in stops
        require_stage(stage, run_root(output, stage), bundle=Path(worker["conditions"]), freeze=freeze)
    for key in ("effective_stop_tokens", "bos_token_id", "pad_token_id", "tokenization", "chat_template_date_string"):
        assert workers[0]["engine"][key] == workers[1]["engine"][key], f"Target token policy differs: {key}"
    return records, paths, workers


def finish(args):
    verify_freeze(args.freeze)
    root = run_root(args.output, args.stage)
    require_stage(args.stage, root, freeze=args.freeze)
    _, _, items = frozen_panel()
    _, _, workers = verified_records(args.output, items, args.stage, args.freeze)
    module = finish_module(args.stage)
    module.verified_records = lambda output, values: verified_records(output, values, args.stage, args.freeze)
    wrapper_hashes = source_hashes()

    def write_with_provenance(path, value):
        if value.get("status") == "completed":
            verify_freeze(args.freeze)
            for name, digest in wrapper_hashes.items():
                assert sha(name) == digest, f"Finisher source changed: {name}"
        value = {**value, "stage": args.stage, "freeze_sha256": sha(args.freeze),
            "cross_family_source_sha256": wrapper_hashes,
            "effective_stop_tokens": workers[0]["engine"]["effective_stop_tokens"],
            "bos_token_id": workers[0]["engine"]["bos_token_id"],
            "generation_token_policy": workers[0]["generation_token_policy"]}
        write(path, value)

    module.write = write_with_provenance
    module.run(args)
    verify_freeze(args.freeze)
    for path, digest in wrapper_hashes.items():
        assert sha(path) == digest, f"Finisher source changed: {path}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "finish"):
        child = sub.add_parser(name)
        child.add_argument("--stage", type=int, choices=(1, 2), required=True)
        child.add_argument("--output", type=Path, required=True)
        child.add_argument("--freeze", type=Path, required=True)
        if name == "run":
            child.add_argument("--model", type=Path, required=True)
            child.add_argument("--conditions", type=Path, required=True)
            child.add_argument("--shard-index", type=int, choices=(0, 1), required=True)
        else:
            child.add_argument("--project", type=Path, required=True)
            child.add_argument("--finish-name", default="finish-r01")
    args = parser.parse_args()
    (run if args.command == "run" else finish)(args)


if __name__ == "__main__":
    main()
