"""Run the frozen 1,400-pair capability panel for one transfer target, two shards."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parent
V3 = ROOT.parent / "capability-screen-v3-2026-10-26"
COUNTS = {"mmlu": 1000, "arc_challenge": 200, "gsm8k": 100, "humaneval": 100}
ORDER = (("gsm8k", "humaneval", "mmlu", "arc_challenge"),
         ("humaneval", "gsm8k", "arc_challenge", "mmlu"))
ARM_NAMES = {"baseline": "T_0", "evo": "true_S_recipe"}
PROTOCOL_SHA = "07cb8ca1b2b2504eccaeeb3fc2b751f0ed62192d316c86a5ff7a0b86edd52cd8"
PANEL_SHA = "1ab21b595e3a5ef96d34bd3e487b81158bb4c2b961da4d863847daa4870afcbc"


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def load_v3(name):
    # Explicit module names avoid importing another experiment's identically named helper.
    sys.path.insert(0, str(V3))
    specification = importlib.util.spec_from_file_location("transfer_frozen_" + name, V3 / (name + ".py"))
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def frozen_panel():
    assert sha(V3 / "protocol.json") == PROTOCOL_SHA
    assert sha(V3 / "panel_manifest.json") == PANEL_SHA
    protocol, panel = read(V3 / "protocol.json"), read(V3 / "panel_manifest.json")
    assert protocol["counts"] == panel["counts"] == COUNTS
    for name, digest in protocol["source_sha256"].items():
        assert sha(V3 / name) == digest, f"Frozen v3 implementation changed: {name}"
    assert protocol["generation"]["chat_template"] is False
    assert protocol["max_new_tokens"] == {"gsm8k": 2048, "humaneval": 1024}
    items = {}
    for task, count in COUNTS.items():
        entry = panel["files"][task]
        path = V3 / entry["file"]
        assert sha(path) == entry["sha256"]
        items[task] = rows(path)
        assert len(items[task]) == count
        assert [item["id"] for item in items[task]] == panel["selected_ids"][task]
    return protocol, panel, items


class BenchmarkEngine:
    """Keep legacy output labels while explicitly binding their transfer meaning."""
    def __init__(self, engine):
        self.engine = engine

    def calibrate(self, contexts):
        return self.engine.calibrate(contexts)

    def score(self, contexts, continuations, arm, calibrations):
        return self.engine.score(contexts, continuations, ARM_NAMES[arm], calibrations)

    def generate(self, contexts, arm, calibrations, budget, stops):
        return self.engine.generate(contexts, ARM_NAMES[arm], calibrations, budget, stops)


def validate_pair(row, item):
    assert row["status"] == "completed" and row["id"] == item["id"]
    assert row["item"] == item and row["benchmark"] == item["benchmark"]
    assert row["calibration"]["context_sha256"] == item["context_sha256"]
    assert set(row["outputs"]) == {"baseline", "evo"}
    for output in row["outputs"].values():
        assert output["status"] == "completed"
        if item["request_type"] == "loglikelihood":
            assert len(output["choice_loglikelihoods"]) == len(item["continuations"])
        else:
            assert output["max_new_tokens"] == item["gen_kwargs"]["max_gen_toks"]
            assert output["generated_token_count"] == len(output["token_ids"])


def run(args):
    protocol, panel, items = frozen_panel()
    engine_source = ROOT / "transfer_engine.py"
    frozen = {str(path): sha(path) for path in (Path(__file__), engine_source, args.conditions)}
    destination = args.output / f"shard-{args.shard_index}"
    destination.mkdir(parents=True, exist_ok=False)
    receipt_path = destination / "receipt.json"
    started = time.monotonic()
    receipt = {"status": "started", "started_utc": utc(), "pid": os.getpid(),
               "model": str(args.model.resolve()), "conditions": str(args.conditions.resolve()),
               "conditions_sha256": sha(args.conditions), "shard_index": args.shard_index,
               "shard_count": 2, "expected_pairs": 700, "completed_pairs": 0,
               "protocol_sha256": PROTOCOL_SHA, "panel_manifest_sha256": PANEL_SHA,
               "source_sha256": frozen, "arm_bindings": ARM_NAMES,
               "task_order": ORDER[args.shard_index], "tasks": {}, "inference_seconds": 0.0,
               "prior_4b_outputs_reused": False}
    write(receipt_path, receipt)
    try:
        from transfer_engine import TransferEngine
        engine = TransferEngine(args.model, device="cuda:0", batch_size=1, bundle=args.conditions)
        assert engine.stop_ids == protocol["generation"]["eos_token_ids"]
        assert engine.batch_size == 1
        receipt["engine"] = json.loads(json.dumps(engine.metadata))
        receipt["model_small_file_sha256"] = {path.name: sha(path) for path in args.model.iterdir()
                                               if path.is_file() and path.name in
                                               {"config.json", "generation_config.json", "tokenizer_config.json", "tokenizer.json"}}
        receipt["setup_seconds"] = time.monotonic() - started
        adapter = BenchmarkEngine(engine)
        evaluate = load_v3("run_panel").evaluate_pair
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
                row["transfer_provenance"] = {"model": receipt["model"],
                    "conditions_sha256": receipt["conditions_sha256"], "arm_bindings": ARM_NAMES}
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
                print(json.dumps({"phase": "benchmark", "task": task, "shard": args.shard_index,
                      "completed_pairs": receipt["completed_pairs"], "expected_pairs": 700,
                      "task_completed": state["completed_pairs"], "pair_seconds": elapsed,
                      "generated_tokens": {arm: value.get("generated_token_count") for arm, value in row["outputs"].items()}}), flush=True)
            state.update(status="completed", ended_utc=utc())
            write(receipt_path, receipt)
        receipt.update(engine.verify_unchanged())
        for path, digest in frozen.items():
            assert sha(path) == digest, f"Execution source changed during run: {path}"
        assert receipt["completed_pairs"] == receipt["expected_pairs"]
        receipt.update(status="completed", records_sha256={str(p.relative_to(destination)): sha(p)
                       for p in sorted(destination.glob("*/[0-9]*.jsonl"))})
    except Exception as error:
        receipt.update(status="failed", error=str(error), traceback=traceback.format_exc())
        raise
    finally:
        receipt.update(ended_utc=utc(), wall_seconds=time.monotonic() - started)
        write(receipt_path, receipt)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--conditions", type=Path, required=True, help="Frozen target bundle.pt")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--shard-index", type=int, choices=(0, 1), required=True)
    run(parser.parse_args())


if __name__ == "__main__":
    main()
