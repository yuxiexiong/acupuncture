"""Bounded cached-generation zero-hook controls and end-to-end throughput timing."""
import argparse
from pathlib import Path
import time
import traceback

from run_benchmark import sha, utc, write
from transfer_engine import TransferEngine, text_hash, token_hash

PROMPTS = (
    "Explain in one short paragraph why a library sorts books into categories.",
    "请用一小段话解释，为什么记录每天的天气有助于安排户外活动。",
)
ARMS = (("baseline", "T_0"), ("zero_channel", "zero_channel"),
        ("zero_vector", "zero_vector"), ("restored", "T_0"))


def run(args):
    output = args.output
    output.mkdir(parents=True, exist_ok=False)
    path = output / "receipt.json"
    started = time.monotonic()
    receipt = {"status": "started", "started_utc": utc(), "model": args.model,
               "source_sha256": {name: sha(Path(__file__).with_name(name))
                                  for name in ("run_decode_check.py", "transfer_engine.py")},
               "budget": {"contexts": 2, "arms_per_context": 4, "max_new_tokens": 32,
                          "maximum_total_generated_tokens": 256},
               "results": [], "scope": "Cached-generation zero-hook and restoration controls; not behavior evaluation."}
    write(path, receipt)
    try:
        engine = TransferEngine(args.model, device="cuda:0", batch_size=1)
        receipt["engine"] = engine.metadata
        receipt["setup_seconds"] = time.monotonic() - started
        for index, prompt in enumerate(PROMPTS):
            rendered = engine.tokenizer.apply_chat_template([{"role": "user", "content": prompt}],
                tokenize=False, add_generation_prompt=True, enable_thinking=False)
            calibration_started = time.monotonic()
            calibration = engine.calibrate([rendered])[0]
            row = {"id": f"decode-control-{index}", "prompt": prompt,
                   "rendered_prompt_sha256": text_hash(rendered), "calibration": calibration,
                   "calibration_seconds": time.monotonic() - calibration_started, "outputs": {}}
            receipt["results"].append(row)
            for label, arm in ARMS:
                inference_started = time.monotonic()
                result = engine.generate([rendered], arm, [calibration], 32, [])[0]
                result["process_wall_seconds"] = time.monotonic() - inference_started
                result["token_sha256"] = token_hash(result["token_ids"])
                result["tokens_per_wall_second_including_prefill"] = result["generated_token_count"] / result["process_wall_seconds"]
                result["tokens_per_synchronized_generation_second"] = result["generated_token_count"] / result["batch_seconds"]
                row["outputs"][label] = result
                write(path, receipt)
            baseline = row["outputs"]["baseline"]["token_ids"]
            assert all(value["token_ids"] == baseline for value in row["outputs"].values()), "Zero hook or restored cached generation changed tokens"
            row["exact_token_control_passed"] = True
            write(path, receipt)
        results = [result for row in receipt["results"] for result in row["outputs"].values()]
        total_tokens = sum(result["generated_token_count"] for result in results)
        total_seconds = sum(result["process_wall_seconds"] for result in results)
        assert len(results) == 8 and total_tokens <= 256
        receipt.update(engine.verify_unchanged())
        for name, digest in receipt["source_sha256"].items():
            assert sha(Path(__file__).with_name(name)) == digest
        receipt.update(status="completed", completed_generation_calls=8, generated_tokens=total_tokens,
                       generation_wall_seconds=total_seconds,
                       tokens_per_wall_second_including_prefill=total_tokens / total_seconds,
                       throughput_limit="Two short synthetic contexts, 32-token cap; includes prefill, not a full-run ETA or a bound on long-context speed.")
    except Exception as error:
        receipt.update(status="failed", error=str(error), traceback=traceback.format_exc())
        raise
    finally:
        receipt.update(ended_utc=utc(), wall_seconds=time.monotonic() - started)
        write(path, receipt)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args())
