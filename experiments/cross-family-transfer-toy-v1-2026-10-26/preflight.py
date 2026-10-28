"""Future GPU check on synthetic inputs, not scientific test questions."""
import argparse
from pathlib import Path
import time
import traceback

from common import BENCHMARK_ARMS, read, sha, write, utc, verify_freeze, require_stage


def checks(engine, stage):
    import torch
    from engine import encode_text, encode_pair
    text = "A library has three shelves with ten books each. Five are borrowed. Answer:"
    continuation = " Twenty-five books remain."
    calibration = engine.calibrate([text])
    inputs = engine._inputs([encode_text(engine.tokenizer, text)])
    labels = ("T_0", "zero_channel", "zero_vector", BENCHMARK_ARMS[stage], "restored")
    logits, scores, tokens = {}, {}, {}
    with torch.inference_mode():
        for label in labels:
            arm = "T_0" if label == "restored" else label
            with engine._intervention(arm, calibration, inputs["attention_mask"]):
                logits[label] = engine.model(**inputs, use_cache=False, logits_to_keep=1).logits.detach().cpu()
            scores[label] = engine.score([text], [continuation], arm, calibration)[0]
            tokens[label] = engine.generate([text], arm, calibration, 16, [])[0]["token_ids"]
        for label in ("zero_channel", "zero_vector", "restored"):
            assert torch.equal(logits[label], logits["T_0"]), "Zero/restored hook changed logits"
            assert scores[label] == scores["T_0"] and tokens[label] == tokens["T_0"]
        # Full logits independently check suffix indexing for baseline and real arm.
        context_ids, continuation_ids = encode_pair(engine.tokenizer, text, continuation)
        full_inputs = engine._inputs([context_ids + continuation_ids[:-1]])
        errors = {}
        for arm in ("T_0", BENCHMARK_ARMS[stage]):
            with engine._intervention(arm, calibration, full_inputs["attention_mask"]):
                full = engine.model(**full_inputs, use_cache=False).logits[0, -len(continuation_ids):]
            prob = torch.log_softmax(full, -1, dtype=torch.float32)
            expected = prob.gather(-1, torch.tensor(continuation_ids, device=engine.device)[:, None]).flatten().tolist()
            errors[arm] = max(abs(a - b) for a, b in zip(expected, scores[arm]["token_logprobs"]))
            assert errors[arm] <= .02, "Full/suffix likelihood mismatch"
    assert torch.isfinite(logits[BENCHMARK_ARMS[stage]]).all()
    return {"scores": scores, "tokens": tokens, "calibration": calibration,
        "full_suffix_error_nats": errors, "zero_and_restoration_exact": True,
        "real_arm": BENCHMARK_ARMS[stage], "real_arm_changed_logits": not torch.equal(logits["T_0"], logits[BENCHMARK_ARMS[stage]])}


def run(args):
    verify_freeze(args.freeze)
    require_stage(args.stage, args.run, args.conditions, args.freeze)
    args.output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    receipt = {"status": "running", "started_utc": utc(), "stage": args.stage,
        "freeze_sha256": sha(args.freeze), "conditions_sha256": sha(args.conditions)}
    write(args.output / "receipt.json", receipt)
    try:
        from engine import CrossFamilyEngine
        engine = CrossFamilyEngine(args.model, bundle=args.conditions)
        receipt["engine"] = engine.metadata
        receipt["checks"] = checks(engine, args.stage)
        receipt.update(engine.verify_unchanged())
        verify_freeze(args.freeze)
        receipt["status"] = "completed"
    except Exception as error:
        receipt.update(status="failed", error=str(error), traceback=traceback.format_exc())
        raise
    finally:
        receipt.update(ended_utc=utc(), wall_seconds=time.monotonic() - started)
        write(args.output / "receipt.json", receipt)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("run", "model", "conditions", "freeze", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--stage", type=int, choices=(1, 2), required=True)
    run(p.parse_args())
