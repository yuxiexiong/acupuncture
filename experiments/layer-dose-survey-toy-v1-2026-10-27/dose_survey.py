"""Source-bound dose survey; bounded preflight never authorizes formal generation."""
import argparse
from functools import lru_cache
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import struct
import time
import traceback

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
OLD = HERE.parent / "layer-survey-toy-v1-2026-10-27"
spec = importlib.util.spec_from_file_location("dose_io", HERE.parent / "transfer-toy-v1-2026-10-26/run_io.py")
io = importlib.util.module_from_spec(spec)
spec.loader.exec_module(io)
DOSES = (0.0625, 0.125, 0.25, 0.5, 1.0)
NEW_DOSES = DOSES[:-1]


def token_hash(tokens):
    return hashlib.sha256(json.dumps(tokens, separators=(",", ":")).encode()).hexdigest()


def bf16_round(value):
    """Independent round-to-nearest-even check for finite scalar BF16 offsets."""
    bits = struct.unpack("I", struct.pack("f", value))[0]
    rounded = (bits + 0x7fff + ((bits >> 16) & 1)) & 0xffff0000
    return struct.unpack("f", struct.pack("I", rounded))[0]


def dose_id(dose):
    assert dose in DOSES
    return "D" + str(float(dose)).replace(".", "p")


def load_design():
    contract, questions, selection = (io.read(HERE / name) for name in ("contract.json", "questions.json", "selection.json"))
    assert contract["experiment"] == HERE.name
    assert contract["models"] == io.read(OLD / "contract.json")["models"] == selection["models"]
    old_generation = io.read(OLD / "contract.json")["generation"]
    assert all(contract["generation"][k] == v for k, v in old_generation.items())
    assert contract["instruction"] == io.read(OLD / "contract.json")["instruction"]
    assert tuple(contract["nonzero_doses"]) == tuple(selection["nonzero_doses"]) == DOSES
    assert tuple(contract["new_doses"]) == NEW_DOSES
    assert contract["selection_sha256"] == io.sha(HERE / "selection.json")
    assert [q["id"] for q in questions] == [f"Q{i:02}" for i in range(1, 9)]
    assert io.sha(HERE / "questions.json") == io.sha(OLD / "questions.json")
    assert io.sha(HERE / "asset_manifest.json") == io.sha(OLD / "asset_manifest.json")
    old_samples = io.read(OLD / "samples.json")
    points = selection["selected_channels"]
    assert len(points) == 88
    for model in contract["models"]:
        selected = [c for c in points if c["model_id"] == model["id"]]
        assert [c["layer"] for c in selected] == list(range(model["layers"]))
        for c in selected:
            candidates = [p for p in old_samples[model["id"]] if p["layer"] == c["layer"]]
            candidates.sort(key=lambda p: p["channel"])
            assert c["candidate_channels"] == [p["channel"] for p in candidates]
            seed = f'acupuncture-layer-dose-v1:{model["id"]}:{c["layer"]}'
            chosen = random.Random(seed).choice(candidates)
            assert c["seed"] == seed and c["channel"] == chosen["channel"]
            assert c["condition_id"] == chosen["id"]
            source_shard = old_samples[model["id"]].index(chosen) % 2
            assert c["source_run"] == str((OLD / f'survey-r01/{model["id"]}-shard-{source_shard}').relative_to(REPO))
            assert c["proposed_worker"] == c["layer"] % 2
    for name, digest in selection["source_files_sha256"].items():
        assert io.sha(REPO / name) == digest, f"Selection source changed: {name}"
    return contract, questions, selection


@lru_cache(maxsize=32)
def source_asset(path):
    return io.read(path)


def check_output(output):
    tokens = output["token_ids"]
    assert output["token_sha256"] == token_hash(tokens)
    assert output["generated_token_count"] == len(tokens) and 0 < len(tokens) <= 128
    assert output["max_new_tokens"] == 128 and output["returned_padding_count"] == 0
    assert output["batch_size"] == 1 and output["end_reason"] in ("eos_token", "length_limit")
    assert output["end_reason"] != "length_limit" or len(tokens) == 128
    assert (output["end_reason"] == "eos_token") == (tokens[-1] in (248044, 248046))
    assert not any(t in (248044, 248046) for t in tokens[:-1])


def source_record(model_id, point, qid):
    run = REPO / point["source_run"] if point else OLD / f"survey-r01/{model_id}-shard-0"
    condition = point["condition_id"] if point else "baseline"
    name = f"records/{condition}__{qid}.json"
    receipt = source_asset(run / "receipt.json")
    assert receipt["status"] == "completed" and receipt["checks_passed"] is True
    assert receipt["integrity"]["hooks_removed"] is True and receipt["model_id"] == model_id
    assert receipt["mode"] == "survey" and receipt["freeze_sha256"] == io.sha(OLD / "freeze.json")
    for asset in ("metadata.json", "calibrations.json"):
        assert io.sha(run / asset) == receipt["asset_hashes"][asset]
    metadata = source_asset(run / "metadata.json")
    assert metadata["target_weight_sha256_before"] == receipt["integrity"]["target_weight_sha256_after"]
    row = io.read(run / name)
    digest = io.sha(run / name)
    assert digest == receipt["record_hashes"][name]
    assert row["status"] == "completed" and row["model_id"] == model_id
    assert row["condition_id"] == condition and row["question_id"] == qid
    assert row["layer"] == (point["layer"] if point else None)
    assert row["channel"] == (point["channel"] if point else None)
    assert row["calibration"] == source_asset(run / "calibrations.json")[qid]
    assert row["calibration"]["context_sha256"] == hashlib.sha256(row["context"].encode()).hexdigest()
    assert row["output"]["input_token_sha256"] == row["calibration"]["input_token_sha256"]
    check_output(row["output"])
    if point:
        hook = row["intervention"]
        assert (hook["layer"], hook["channel"], hook["dose"]) == (point["layer"], point["channel"], 1.0)
        assert hook["requested_offset"] == row["calibration"]["residual_scales"][str(point["layer"])] / hook["column_norm"]
        assert hook["bf16_offset"] == bf16_round(hook["requested_offset"])
    else:
        assert row["intervention"] is None
    return row, {"run": str(run.relative_to(REPO)), "record": str((run / name).relative_to(REPO)), "record_sha256": digest}


def schedule(mode, model, questions, selection, shard, shards=2):
    assert mode in ("preflight", "survey") and shards == 2 and shard in (0, 1)
    points = [c for c in selection["selected_channels"] if c["model_id"] == model["id"] and c["layer"] % 2 == shard]
    assert len(points) == model["layers"] // 2
    if mode == "survey":
        return [(f'{c["condition_id"]}-{dose_id(dose)}', c, q, dose) for c in points for q in questions for dose in NEW_DOSES]
    jobs = [("baseline", None, q, None) for q in questions]
    anchors = [points[0], points[len(points) // 2], points[-1]]
    for c, q in zip(anchors, (questions[0], questions[3], questions[7])):
        jobs += [(f'replay-{c["condition_id"]}', c, q, 1.0),
                 (f'zero-{c["condition_id"]}', c, q, 0.0),
                 (f'restored-{c["condition_id"]}', c, q, None)]
    c = anchors[1]
    jobs += [(f'{c["condition_id"]}-{dose_id(dose)}', c, questions[3], dose) for dose in NEW_DOSES]
    assert len(jobs) == 21
    return jobs


def make_specs(mode, model_id, shard, shards=2):
    contract, questions, selection = load_design()
    model = next(m for m in contract["models"] if m["id"] == model_id)
    return schedule(mode, model, questions, selection, shard, shards)


def freeze():
    contract, questions, selection = load_design()
    files = set(HERE.glob("*.py")) | {HERE / n for n in ("contract.json", "questions.json", "selection.json", "asset_manifest.json", "PROTOCOL.zh-CN.md")}
    files |= {REPO / p for p in selection["source_files_sha256"]}
    # Bind all transitive dependencies already frozen by the source survey.
    files |= {REPO / p for p in io.read(OLD / "freeze.json")["files"]}
    for model in contract["models"]:
        points = [None] + [c for c in selection["selected_channels"] if c["model_id"] == model["id"]]
        for c in points:
            for q in questions:
                _, source = source_record(model["id"], c, q["id"])
                files.add(REPO / source["record"])
                files |= {REPO / source["run"] / n for n in ("receipt.json", "metadata.json", "calibrations.json")}
    io.immutable(HERE / "freeze.json", {"experiment": HERE.name, "created_utc": io.utc(),
                 "files": {str(p.relative_to(REPO)): io.sha(p) for p in sorted(files)}})


def check_freeze():
    value = io.read(HERE / "freeze.json")
    assert value["experiment"] == HERE.name
    for name, digest in value["files"].items():
        assert io.sha(REPO / name) == digest, f"Frozen input changed: {name}"
    return io.sha(HERE / "freeze.json")


def check_authorization(path, mode, model_id, gpu, execute):
    assert execute, "Explicit --execute required; no model has been loaded"
    identity, auth = check_freeze(), io.read(path)
    assert auth["experiment"] == HERE.name and auth["freeze_sha256"] == identity
    assert auth["status"] == "authorized" and auth["purpose"] == mode, "Preflight does not authorize formal generation"
    assert model_id in auth["models"] and gpu in auth["gpus"]
    assert auth["user_instruction"] and auth["recorded_utc"]
    if mode == "preflight":
        assert auth["maximum_generations"] == 126 and auth["formal_launch_confirmed"] is False
    if mode == "survey":
        assert auth["formal_launch_confirmed"] is True
        receipts = [verify(REPO / p) for p in auth["preflight_runs"]]
        assert len(receipts) == 6 and {(r["model_id"], r["shard"]) for r in receipts} == {(m, s) for m in ("2b", "4b", "9b") for s in (0, 1)}
        assert all(r["mode"] == "preflight" and r["checks_passed"] for r in receipts)
    return identity, auth


def check_model_assets(model):
    expected = io.read(HERE / "asset_manifest.json")[model["id"]]
    assert expected["revision"] == model["revision"]
    started = time.monotonic()
    for name, identity in expected["files"].items():
        path = Path(model["remote_path"]) / name
        assert path.stat().st_size == identity["bytes"], f"Model size changed: {name}"
        assert io.sha(path) == identity["sha256"], f"Model hash changed: {name}"
    return {"status": "verified", "manifest_sha256": io.sha(HERE / "asset_manifest.json"),
            "files": len(expected["files"]), "seconds": time.monotonic() - started}


def compatible_metadata(current, source):
    # Workers move selected points between GPUs; all scientific/runtime fields stay exact.
    assert {k: v for k, v in current.items() if k != "device"} == {k: v for k, v in source.items() if k != "device"}, "Source runtime/model metadata mismatch"


def kind_for(condition):
    return condition.split("-", 1)[0] if condition.startswith(("replay-", "zero-", "restored-")) else "baseline" if condition == "baseline" else "dose"


def check_record(row, model, condition, point, question, dose, calibrations):
    old, source = source_record(model["id"], point, question["id"])
    kind = kind_for(condition)
    assert row["status"] == "completed" and row["model_id"] == model["id"]
    assert row["condition_id"] == condition and row["kind"] == kind
    assert row["question_id"] == question["id"] and row["prompt"] == question["prompt"] == old["prompt"]
    assert row["point_id"] == (point["condition_id"] if point else None)
    assert row["layer"] == (point["layer"] if point else None) and row["channel"] == (point["channel"] if point else None)
    assert row["dose"] == (dose if dose is not None else 0.0)
    assert row["source"] == source and row["context"] == old["context"]
    assert row["calibration"] == old["calibration"] == calibrations[question["id"]]
    output = row["output"]
    check_output(output)
    assert output["input_token_sha256"] == row["calibration"]["input_token_sha256"]
    if dose is not None:
        hook, previous = row["intervention"], old["intervention"]
        assert (hook["layer"], hook["channel"], hook["dose"]) == (point["layer"], point["channel"], dose)
        assert hook["column_norm"] == previous["column_norm"] and math.isfinite(hook["column_norm"]) and hook["column_norm"] > 0
        assert hook["clean_residual_scale"] == row["calibration"]["residual_scales"][str(point["layer"])]
        assert hook["requested_offset"] == dose * hook["clean_residual_scale"] / hook["column_norm"]
        assert hook["bf16_offset"] == bf16_round(hook["requested_offset"])
        assert hook["calls"] == len(output["token_ids"])
        assert hook["positions"] == row["calibration"]["input_token_count"] + len(output["token_ids"]) - 1
        assert hook["prefill_target_values_checked"] is True
        assert hook["prefill_first_changed"] == bf16_round(hook["prefill_first_original"] + hook["bf16_offset"])
        assert hook["prefill_first_actual_delta"] == hook["prefill_first_changed"] - hook["prefill_first_original"]
    else:
        assert row["intervention"] is None
    if kind in ("baseline", "replay"):
        assert output["token_ids"] == old["output"]["token_ids"], f"Historical token replay mismatch: {condition}/{question['id']}"
    if kind in ("zero", "restored"):
        baseline, _ = source_record(model["id"], None, question["id"])
        assert output["token_ids"] == baseline["output"]["token_ids"], f"Zero/restoration mismatch: {condition}"


def verify(run):
    run = Path(run)
    receipt = io.read(run / "receipt.json")
    assert receipt["status"] == "completed" and receipt["experiment"] == HERE.name
    assert receipt["freeze_sha256"] == check_freeze() and receipt["checks_passed"] is True
    contract, questions, selection = load_design()
    model = next(m for m in contract["models"] if m["id"] == receipt["model_id"])
    assert receipt["gpu"] == receipt["shard"]
    jobs = schedule(receipt["mode"], model, questions, selection, receipt["shard"], receipt["shards"])
    expected = {f"records/{name}__{q['id']}.json": (name, c, q, dose) for name, c, q, dose in jobs}
    assert receipt["expected_records"] == receipt["completed_records"] == len(jobs)
    assert len(expected) == len(jobs) and set(receipt["record_hashes"]) == set(expected)
    assert receipt["expected_record_ids"] == [f"{name}__{q['id']}" for name, _, q, _ in jobs]
    assert {str(p.relative_to(run)) for p in (run / "records").glob("*.json")} == set(expected)
    calibrations, metadata = io.read(run / "calibrations.json"), io.read(run / "metadata.json")
    for name, job in expected.items():
        assert io.sha(run / name) == receipt["record_hashes"][name]
        row = io.read(run / name)
        check_record(row, model, *job, calibrations)
        compatible_metadata(metadata, source_asset(REPO / row["source"]["run"] / "metadata.json"))
    assert set(receipt["asset_hashes"]) == {"metadata.json", "calibrations.json", "source_checks.json"}
    for name, digest in receipt["asset_hashes"].items():
        assert io.sha(run / name) == digest
    assert receipt["integrity"]["hooks_removed"] is True
    assert metadata["target_weight_sha256_before"] == receipt["integrity"]["target_weight_sha256_after"]
    assert receipt["model_asset_verification"]["status"] == "verified"
    assert receipt["model_asset_verification"]["manifest_sha256"] == io.sha(HERE / "asset_manifest.json")
    source_checks = io.read(run / "source_checks.json")
    points = [None] + [c for c in selection["selected_channels"] if c["model_id"] == model["id"] and c["layer"] % 2 == receipt["shard"]]
    sources = []
    for point in points:
        for q in questions:
            old, source = source_record(model["id"], point, q["id"])
            assert old["calibration"] == calibrations[q["id"]]
            compatible_metadata(metadata, source_asset(REPO / source["run"] / "metadata.json"))
            sources.append(source)
    assert source_checks["status"] == "passed" and source_checks["sources"] == sources
    return receipt


def run(args):
    identity, auth = check_authorization(args.authorization, args.mode, args.model, args.gpu, args.execute)
    contract, questions, selection = load_design()
    model = next(m for m in contract["models"] if m["id"] == args.model)
    assert args.gpu == args.shard, "GPU0 handles even layers, GPU1 handles odd layers"
    jobs = schedule(args.mode, model, questions, selection, args.shard, args.shards)
    destination = Path(args.output)
    assert destination.resolve() == (Path(auth["remote_output"]) / f"{args.model}-shard-{args.shard}").resolve(), "Output must match the authorized worker directory"
    assert not destination.exists(), "Keep partial evidence; use a fresh output directory"
    import fcntl
    import subprocess
    lock = open(f"/tmp/acupuncture-layer-survey-gpu{args.gpu}.lock", "w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    used = subprocess.check_output(["nvidia-smi", f"--id={args.gpu}", "--query-gpu=memory.used", "--format=csv,noheader,nounits"], text=True)
    assert int(used.strip()) < 256, "GPU occupied; do not disturb its owner"
    destination.mkdir(parents=True)
    started = time.monotonic()
    receipt = {"status": "running", "experiment": HERE.name, "mode": args.mode,
               "model_id": args.model, "shard": args.shard, "shards": args.shards,
               "freeze_sha256": identity, "authorization": auth, "gpu": args.gpu,
               "started_utc": io.utc(), "expected_records": len(jobs), "record_hashes": {}, "asset_hashes": {},
               "expected_record_ids": [f"{name}__{q['id']}" for name, _, q, _ in jobs]}
    io.write(destination / "receipt.json", receipt)
    engine = None
    try:
        receipt["model_asset_verification"] = check_model_assets(model)
        from dose_engine import DoseEngine
        engine = DoseEngine(model["remote_path"], model, f"cuda:{args.gpu}")
        receipt["load_seconds"] = time.monotonic() - started
        io.immutable(destination / "metadata.json", engine.metadata)
        contexts = {q["id"]: engine.tokenizer.apply_chat_template(
            [{"role": "user", "content": contract["instruction"] + "\n\n" + q["prompt"]}],
            tokenize=False, add_generation_prompt=True, enable_thinking=False) for q in questions}
        cal_start = time.monotonic()
        calibrations = dict(zip(contexts, engine.calibrate(list(contexts.values()))))
        receipt["calibration_seconds"] = time.monotonic() - cal_start
        io.immutable(destination / "calibrations.json", calibrations)
        source_checks = []
        points = [None] + [c for c in selection["selected_channels"] if c["model_id"] == args.model and c["layer"] % 2 == args.shard]
        for c in points:
            for q in questions:
                old, source = source_record(args.model, c, q["id"])
                assert contexts[q["id"]] == old["context"] and calibrations[q["id"]] == old["calibration"], "Source prompt/calibration mismatch"
                compatible_metadata(engine.metadata, source_asset(REPO / source["run"] / "metadata.json"))
                if c:
                    assert float(engine.column_norms[str(c["layer"])][c["channel"]]) == old["intervention"]["column_norm"], "Source column norm mismatch"
                source_checks.append(source)
        io.immutable(destination / "source_checks.json", {"status": "passed", "sources": source_checks,
                     "checks": ["metadata_except_gpu_exact", "context_exact", "clean_calibration_exact", "column_norm_exact"]})
        receipt["asset_hashes"] = {name: io.sha(destination / name) for name in ("metadata.json", "calibrations.json", "source_checks.json")}
        for condition, c, q, dose in jobs:
            qid = q["id"]
            receipt["active_record"] = f"{condition}__{qid}"
            old, source = source_record(args.model, c, qid)
            arm = (c["layer"], c["channel"], dose) if dose is not None else "baseline"
            output = engine.generate([contexts[qid]], arm, [old["calibration"]], 128, [])[0]
            output["token_sha256"] = token_hash(output["token_ids"])
            row = {"status": "completed", "model_id": args.model, "condition_id": condition,
                   "kind": kind_for(condition), "point_id": c["condition_id"] if c else None,
                   "layer": c["layer"] if c else None, "channel": c["channel"] if c else None,
                   "dose": dose if dose is not None else 0.0, "question_id": qid, "prompt": q["prompt"],
                   "context": contexts[qid], "calibration": old["calibration"], "source": source,
                   "intervention": engine.last_hook, "output": output, "ended_utc": io.utc()}
            name = f"records/{condition}__{qid}.json"
            io.immutable(destination / name, row)
            receipt["record_hashes"][name] = io.sha(destination / name)
            receipt["completed_records"] = len(receipt["record_hashes"])
            io.write(destination / "receipt.json", receipt)
            check_record(row, model, condition, c, q, dose, calibrations)
            assert all(not m._forward_pre_hooks for m in engine.modules.values())
            assert all(not block._forward_hooks for block in engine.layers)
            print(json.dumps({"completed": len(receipt["record_hashes"]), "total": len(jobs),
                              "tokens": len(output["token_ids"]), "seconds": output["batch_seconds"]}), flush=True)
        receipt["integrity"] = engine.verify_unchanged()
        receipt.pop("active_record", None)
        receipt.update(status="completed", checks_passed=True, ended_utc=io.utc(), wall_seconds=time.monotonic() - started)
        io.write(destination / "receipt.json", receipt)
        verify(destination)
    except BaseException:
        receipt.update(status="failed", checks_passed=False, error=traceback.format_exc(), ended_utc=io.utc(), wall_seconds=time.monotonic() - started)
        if engine is not None:
            try:
                receipt["integrity"] = engine.verify_unchanged()
            except BaseException:
                receipt["integrity_error"] = traceback.format_exc()
        io.write(destination / "receipt.json", receipt)
        raise
    finally:
        lock.close()


def main():
    import signal
    def stopped(_signum, _frame):
        raise KeyboardInterrupt("Worker stop requested; preserve partial evidence")
    signal.signal(signal.SIGTERM, stopped)
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("freeze")
    validation = commands.add_parser("verify")
    validation.add_argument("path")
    execution = commands.add_parser("run")
    execution.add_argument("--mode", choices=("preflight", "survey"), required=True)
    execution.add_argument("--model", choices=("2b", "4b", "9b"), required=True)
    execution.add_argument("--gpu", type=int, choices=(0, 1), required=True)
    execution.add_argument("--shard", type=int, choices=(0, 1), required=True)
    execution.add_argument("--shards", type=int, default=2, choices=(2,))
    execution.add_argument("--authorization", required=True)
    execution.add_argument("--output", required=True)
    execution.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.command == "freeze":
        freeze()
    elif args.command == "verify":
        print(json.dumps(verify(args.path), ensure_ascii=False))
    else:
        run(args)


if __name__ == "__main__":
    main()
