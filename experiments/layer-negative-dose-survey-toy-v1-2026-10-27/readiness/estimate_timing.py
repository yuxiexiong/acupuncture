"""Offline, source-verified timing scenarios; never loads a model or runs inference."""
import json
from pathlib import Path
from statistics import median
import sys

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import dose_survey as survey


def estimate():
    preflight = HERE / "preflight-r01"
    controller = survey.io.read(preflight / "controller.json")
    assert controller["status"] == "completed"
    assert controller["experiment"] == HERE.name
    assert controller["freeze_sha256"] == survey.check_freeze()
    assert controller["expected_records"] == 138
    keys = [f"{model}-shard-{shard}" for model in ("2b", "4b", "9b") for shard in (0, 1)]
    assert controller["worker_exit_codes"] == dict.fromkeys(keys, 0)
    assert all((preflight / f"{key}.exit").read_text().strip() == "0" for key in keys)
    positive_path = survey.POSITIVE / "delivery-r01/all.records.jsonl"
    positive = {}
    for row in survey.io.rows(positive_path):
        if row["intervention"] is None:
            continue
        dose = row["intervention"]["dose"]
        key = (row["model_id"], row["layer"], row["channel"], row["question_id"], dose)
        assert key not in positive and -dose in survey.NEW_DOSES
        survey.check_output(row["output"])
        positive[key] = row["output"]["generated_token_count"]
    assert len(positive) == 3520
    sources = {str(p.relative_to(survey.REPO)): survey.io.sha(p) for p in
               (Path(__file__), preflight / "controller.json", positive_path)}
    workers, expected_positive = [], set()
    for model in ("2b", "4b", "9b"):
        for shard in (0, 1):
            run = preflight / f"{model}-shard-{shard}"
            receipt = survey.verify(run)
            assert receipt["mode"] == "preflight" and receipt["completed_records"] == 23
            sources[str((run / "receipt.json").relative_to(survey.REPO))] = survey.io.sha(run / "receipt.json")
            rows = [survey.io.read(run / name) for name in receipt["record_hashes"]]
            tokens = sum(r["output"]["generated_token_count"] for r in rows)
            generation_seconds = sum(r["output"]["batch_seconds"] for r in rows)
            overhead = receipt["wall_seconds"] - generation_seconds
            assert overhead >= 0 and tokens > 0
            long_rows = [r for r in rows if 120 <= r["output"]["generated_token_count"] <= 128]
            if long_rows:
                rate = median(r["output"]["batch_seconds"] / r["output"]["generated_token_count"] for r in long_rows)
                rate_method = "median_seconds_per_token_on_actual_120_to_128_token_outputs"
            else:
                rate = generation_seconds / tokens
                rate_method = "no_long_sample_available_weighted_all_output_seconds_per_token_short_output_extrapolation"
            jobs = survey.make_specs("survey", model, shard)
            positive_keys = {(model, c["layer"], c["channel"], q["id"], -dose) for _, c, q, dose in jobs}
            assert len(positive_keys) == len(jobs)
            expected_positive |= positive_keys
            positive_tokens = sum(positive[key] for key in positive_keys)
            smoke = sorted((r for r in rows if r["kind"] == "dose"), key=lambda r: r["dose"], reverse=True)
            assert tuple(r["dose"] for r in smoke) == survey.NEW_DOSES
            workers.append({
                "model_id": model, "shard": shard, "preflight_records": len(rows),
                "preflight_seconds": receipt["wall_seconds"],
                "load_including_asset_check_seconds": receipt["load_seconds"],
                "asset_check_seconds": receipt["model_asset_verification"]["seconds"],
                "calibration_seconds": receipt["calibration_seconds"],
                "generation_seconds": generation_seconds, "non_generation_seconds": overhead,
                "total_generated_tokens": tokens,
                "negative_smoke": [{"dose": r["dose"], "tokens": r["output"]["generated_token_count"],
                                    "seconds": r["output"]["batch_seconds"]} for r in smoke],
                "long_output_samples": [{"record_id": f'{r["condition_id"]}__{r["question_id"]}',
                                         "tokens": r["output"]["generated_token_count"],
                                         "seconds": r["output"]["batch_seconds"]} for r in long_rows],
                "seconds_per_token": rate, "rate_method": rate_method,
                "formal_new_records": len(jobs), "positive_five_dose_actual_tokens": positive_tokens,
                "formal_all128_tokens": len(jobs) * 128,
                "formal_seconds_positive_five_dose_lengths": overhead + rate * positive_tokens,
                "formal_seconds_all128": overhead + rate * len(jobs) * 128,
            })
    assert expected_positive == set(positive)
    assert sum(w["preflight_records"] for w in workers) == 138
    assert sum(w["formal_new_records"] for w in workers) == 3520
    scenarios = ("formal_seconds_positive_five_dose_lengths", "formal_seconds_all128")
    models = [{"model_id": model, "formal_new_records": sum(w["formal_new_records"] for w in workers if w["model_id"] == model),
               **{scenario: max(w[scenario] for w in workers if w["model_id"] == model) for scenario in scenarios}}
              for model in ("2b", "4b", "9b")]
    return {
        "status": "measured_preflight_and_conditional_formal_estimates", "created_utc": survey.io.utc(),
        "freeze_sha256": controller["freeze_sha256"], "source_file_sha256": sources,
        "preflight": {
            "started_utc": controller["started_utc"], "ended_utc": controller["ended_utc"],
            "controller_wall_seconds": controller["wall_seconds"],
            "worker_wall_sum_seconds": sum(w["preflight_seconds"] for w in workers),
            "worker_allocated_gpu_hours": sum(w["preflight_seconds"] for w in workers) / 3600,
            "two_gpu_reserved_hours": 2 * controller["wall_seconds"] / 3600,
            "total_generated_tokens": sum(w["total_generated_tokens"] for w in workers),
            "negative_smoke_generated_tokens": sum(r["tokens"] for w in workers for r in w["negative_smoke"]),
            "failures": 0, "retries": 0,
        },
        "workers": workers, "models": models,
        "formal_estimated_seconds": {scenario: sum(m[scenario] for m in models) for scenario in scenarios},
        "methodology": [
            "Each worker has 23 verified preflight records; all six total 138, separate from the 3520 formal answers.",
            "O = measured worker receipt wall seconds minus all 23 output.batch_seconds; includes measured asset/model loading, calibration and non-generation checks.",
            "r = median batch_seconds/generated_token_count on actual 120-to-128-token outputs of the same worker/model. When absent, explicitly use its all-output weighted rate, a short-output extrapolation.",
            "Positive-length scenario: O + r * sum of actual positive five-dose token lengths at precisely the same model/layer/channel/question/absolute-dose keys; all128: O + r * 128 * formal record count.",
            "Take the slower of two workers for each model, then sum 2B, 4B and 9B in serial; no arbitrary safety multiplier.",
            "Preflight is already measured and is not added to remaining formal runtime. GPU hours describe worker allocation or two-card reservation, not measured GPU busy time.",
        ],
        "limitations": [
            "These are conditional runtime scenarios, not confidence intervals or hard upper bounds; negative outputs may have different lengths and depth/question mix may change observed throughput.",
            "Long-output samples include repeated controls and are not independent; per-token extrapolation also approximates per-prompt overhead. Only five new negative smoke outputs per worker are available, all at middle-layer Q04.",
            "Queueing, failures, transfer/export/archive and reading are excluded and must be reported separately. Reading has not been timed.",
            "This offline helper was added after the scientific freeze; its own hash is recorded here and no frozen file is changed.",
        ],
    }


if __name__ == "__main__":
    result = estimate()
    destination = HERE / "readiness/timing-estimate-r01.json"
    survey.io.immutable(destination, result)
    print(json.dumps({"output": str(destination), "formal_estimated_seconds": result["formal_estimated_seconds"]}, ensure_ascii=False))
