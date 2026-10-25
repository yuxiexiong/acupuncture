"""Bounded batch-one check of removing an empty per-token text-stop callback."""
import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from run_benchmark import sha, utc, write
from transfer_engine import TransferEngine, text_hash, token_hash

PROMPTS = (
    "Explain in one short paragraph why a library sorts books into categories.",
    "请用一小段话解释，为什么记录每天的天气有助于安排户外活动。",
)
ARMS = ("T_0", "true_S_recipe", "true_D_match")
BUDGET = 128


@contextmanager
def omit_empty_task_stops(model):
    """Only use around Engine.generate(..., stops=[]); restore even on failure."""
    original = model.generate
    missing = object()
    prior_override = model.__dict__.get("generate", missing)
    audit = {"removed_callbacks": 0}

    def generate(*args, **kwargs):
        criteria = kwargs.pop("stopping_criteria")
        assert len(criteria) == 1 and all(step is None for step in criteria[0].steps)
        audit["removed_callbacks"] += 1
        result = original(*args, **kwargs)
        assert all(step is None for step in criteria[0].steps)
        return result

    model.generate = generate
    try:
        yield audit
    finally:
        if prior_override is missing:
            del model.generate
        else:
            model.generate = prior_override
        assert model.generate == original, "Model generation method was not restored"


def run(args):
    args.output.mkdir(parents=True, exist_ok=False)
    path = args.output / "receipt.json"
    started = time.monotonic()
    freeze = json.loads((ROOT / "freeze.json").read_text())
    files = {str((ROOT / name).resolve()): digest for name, digest in freeze["files"].items()}
    for source in (Path(__file__), ROOT / "freeze.json", args.bundle):
        files[str(source.resolve())] = sha(source)
    receipt = {"status": "started", "started_utc": utc(), "model": str(args.model.resolve()),
               "bundle": str(args.bundle.resolve()), "source_sha256_before": files,
               "budget": {"contexts": 2, "conditions": list(ARMS), "variants": 2,
                          "max_new_tokens": BUDGET, "calls": 12, "maximum_generated_tokens": 1536},
               "scope": "Synthetic empty-stops implementation/performance check; not formal behavior evidence.",
               "load_context": "Co-loaded with an existing 4B source worker on the same GPU; timing is not isolated throughput.",
               "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
               "limits": "Two short prompts at 128 tokens; does not validate nonempty task stops, long contexts, batching, or concurrent processes.",
               "cases": []}
    write(path, receipt)
    engine = None
    try:
        assert all(sha(name) == digest for name, digest in files.items()), "Frozen source hash mismatch"
        engine = TransferEngine(args.model, device="cuda:0", batch_size=1, bundle=args.bundle)
        assert engine.metadata["hidden_size"] == 4096 and engine.metadata["intermediate_size"] == 12288, "This bounded probe is frozen for 9B"
        assert all(spec["scale"] == "target" for arm in ARMS for spec in engine.conditions[arm].values()), "Source-scale arms need genuine source calibration"
        receipt["engine"] = engine.metadata
        receipt["setup_seconds"] = time.monotonic() - started
        for prompt_index, prompt in enumerate(PROMPTS):
            rendered = engine.tokenizer.apply_chat_template([{"role": "user", "content": prompt}],
                tokenize=False, add_generation_prompt=True, enable_thinking=False)
            calibration_started = time.monotonic()
            calibration = engine.calibrate([rendered])[0]
            calibration_seconds = time.monotonic() - calibration_started
            for arm_index, arm in enumerate(ARMS):
                case_index = prompt_index * len(ARMS) + arm_index
                order = ("original", "omit_empty_stop") if case_index % 2 == 0 else ("omit_empty_stop", "original")
                case = {"id": case_index, "prompt": prompt, "rendered_prompt": rendered,
                        "rendered_prompt_sha256": text_hash(rendered), "condition": arm,
                        "calibration": calibration, "calibration_seconds": calibration_seconds,
                        "order": order, "outputs": {}}
                receipt["cases"].append(case)
                for variant in order:
                    call_started = time.monotonic()
                    if variant == "omit_empty_stop":
                        with omit_empty_task_stops(engine.model) as audit:
                            result = engine.generate([rendered], arm, [calibration], BUDGET, [])[0]
                        assert audit["removed_callbacks"] == 1
                    else:
                        result = engine.generate([rendered], arm, [calibration], BUDGET, [])[0]
                    result["process_wall_seconds"] = time.monotonic() - call_started
                    result["token_sha256"] = token_hash(result["token_ids"])
                    result["raw_text_sha256"] = text_hash(result["raw_text"])
                    result["answer_text_sha256"] = text_hash(result["answer_text"])
                    assert all(not module._forward_pre_hooks for module in engine.modules.values())
                    assert all(not engine.layers[layer]._forward_hooks for layer in engine.modules)
                    case["outputs"][variant] = result
                    write(path, receipt)
                left, right = (case["outputs"][variant] for variant in ("original", "omit_empty_stop"))
                compared = ("token_ids", "token_sha256", "end_reason", "input_token_sha256",
                            "raw_text_sha256", "answer_text_sha256", "generated_token_count",
                            "returned_padding_count", "max_new_tokens", "batch_size")
                case["equal_fields"] = {field: left[field] == right[field] for field in compared}
                case["exact_match"] = all(case["equal_fields"].values())
                write(path, receipt)
        totals = {}
        for variant in ("original", "omit_empty_stop"):
            outputs = [case["outputs"][variant] for case in receipt["cases"]]
            seconds = sum(value["process_wall_seconds"] for value in outputs)
            tokens = sum(value["generated_token_count"] for value in outputs)
            totals[variant] = {"calls": len(outputs), "generated_tokens": tokens,
                               "generation_wall_seconds": seconds, "tokens_per_wall_second": tokens / seconds}
        assert sum(row["calls"] for row in totals.values()) == 12
        assert sum(row["generated_tokens"] for row in totals.values()) <= 1536
        receipt["totals"] = totals
        receipt["generation_wall_speedup"] = totals["original"]["generation_wall_seconds"] / totals["omit_empty_stop"]["generation_wall_seconds"]
        receipt["all_exact_matches"] = all(case["exact_match"] for case in receipt["cases"])
        receipt.update(engine.verify_unchanged())
        receipt["source_sha256_after"] = {name: sha(name) for name in files}
        assert receipt["source_sha256_after"] == files, "Frozen source changed during probe"
        assert receipt["all_exact_matches"], "Candidate changed tokens or generation metadata"
        receipt["status"] = "completed"
    except Exception as error:
        receipt.update(status="failed", error=str(error), traceback=traceback.format_exc())
        raise
    finally:
        receipt.update(ended_utc=utc(), wall_seconds=time.monotonic() - started)
        write(path, receipt)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args())
