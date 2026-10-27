"""Frozen per-layer survey with separate preflight and formal launch permissions."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import random
from pathlib import Path
import time
import traceback

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
io_spec = importlib.util.spec_from_file_location("survey_io", HERE.parent / "transfer-toy-v1-2026-10-26/run_io.py")
io = importlib.util.module_from_spec(io_spec)
io_spec.loader.exec_module(io)


def token_hash(tokens):
    return hashlib.sha256(json.dumps(tokens, separators=(",", ":")).encode()).hexdigest()


def load_design():
    contract = io.read(HERE / "contract.json")
    questions = io.read(HERE / "questions.json")
    samples = io.read(HERE / "samples.json")
    assert [q["id"] for q in questions] == [f"Q{i:02}" for i in range(1, 9)]
    assert len({q["prompt"] for q in questions}) == 8
    for model in contract["models"]:
        selected = samples[model["id"]]
        assert len(selected) == model["layers"] * 10
        assert Counter(c["layer"] for c in selected) == Counter({i: 10 for i in range(model["layers"])})
        assert len({(c["layer"], c["channel"]) for c in selected}) == len(selected)
        for layer in range(model["layers"]):
            rng = random.Random(f'acupuncture-layer-survey-v1:{model["id"]}:{layer}')
            assert [c["channel"] for c in selected if c["layer"] == layer] == sorted(rng.sample(range(model["intermediate_size"]), 10))
        for c in selected:
            assert 0 <= c["channel"] < model["intermediate_size"]
            assert c["id"] == f'L{c["layer"]:02}-N{c["channel"]:06}'
    return contract, questions, samples


def freeze():
    load_design()
    files = [HERE / name for name in ("contract.json", "questions.json", "samples.json", "asset_manifest.json", "survey.py",
             "survey_engine.py", "test_survey.py", "export_survey.py", "test_export_survey.py", "PROTOCOL.zh-CN.md")]
    files += [HERE.parent / "transfer-toy-v1-2026-10-26" / name for name in ("transfer_engine.py", "run_io.py")]
    files += [HERE.parent / "capability-damage-v2-2026-10-26/model_engine.py"]
    io.immutable(HERE / "freeze.json", {"experiment": HERE.name, "created_utc": io.utc(),
                 "files": {str(p.relative_to(REPO)): io.sha(p) for p in files}})


def check_freeze():
    value = io.read(HERE / "freeze.json")
    assert value["experiment"] == HERE.name
    for name, digest in value["files"].items():
        assert io.sha(REPO / name) == digest, f"Frozen input changed: {name}"
    return io.sha(HERE / "freeze.json")


def check_authorization(path, mode, model_id, gpu, execute):
    assert execute, "Explicit --execute is required; no model has been loaded"
    identity = check_freeze()
    auth = io.read(path)
    assert auth["experiment"] == HERE.name and auth["freeze_sha256"] == identity
    assert auth["status"] == "authorized" and auth["purpose"] == mode, "Preflight permission is NOT formal launch permission"
    assert model_id in auth["models"] and gpu in auth["gpus"]
    assert auth["user_instruction"] and auth["recorded_utc"]
    if mode == "survey":
        assert auth["formal_launch_confirmed"] is True
        assert len(auth["preflight_runs"]) == 3
        receipts = [verify(REPO / p) for p in auth["preflight_runs"]]
        assert {r["model_id"] for r in receipts} == {"2b", "4b", "9b"}
        assert all(r["mode"] == "preflight" and r["checks_passed"] for r in receipts)
    return identity, auth


def check_model_assets(model):
    expected = io.read(HERE / "asset_manifest.json")[model["id"]]
    assert expected["revision"] == model["revision"]
    started = time.monotonic()
    for name, identity in expected["files"].items():
        path = Path(model["remote_path"]) / name
        assert path.stat().st_size == identity["bytes"], f"Model file size changed: {name}"
        assert io.sha(path) == identity["sha256"], f"Model file hash changed: {name}"
    return {"status": "verified", "manifest_sha256": io.sha(HERE / "asset_manifest.json"),
            "files": len(expected["files"]), "seconds": time.monotonic() - started}


def schedule(mode, model, questions, samples, shard, shards):
    assert shards in (1, 2) and 0 <= shard < shards
    jobs = []
    if mode == "preflight":
        assert shard == 0 and shards == 1
        jobs.extend(("baseline", None, q, None) for q in questions)
        layers = [0, model["layers"] // 2, model["layers"] - 1]
        for j, layer in enumerate(layers):
            c = next(c for c in samples if c["layer"] == layer)
            jobs.extend((c["id"], c, q, 1.0) for i, q in enumerate(questions) if i % 3 == j)
            jobs += [(f'zero-{layer:02}', c, questions[0], 0.0),
                     (f'restored-{layer:02}', None, questions[0], None)]
        assert len(jobs) == 22
    else:
        assert shards == 2, "Formal execution is frozen to two shards"
        if shard == 0:
            jobs.extend(("baseline", None, q, None) for q in questions)
        for i, c in enumerate(samples):
            if i % shards == shard:
                jobs.extend((c["id"], c, q, 1.0) for q in questions)
    return jobs


def verify(run):
    run = Path(run)
    receipt = io.read(run / "receipt.json")
    assert receipt["status"] == "completed"
    assert receipt["freeze_sha256"] == check_freeze()
    contract, questions, samples = load_design()
    model = next(m for m in contract["models"] if m["id"] == receipt["model_id"])
    jobs = schedule(receipt["mode"], model, questions, samples[model["id"]], receipt["shard"], receipt["shards"])
    expected = {f"records/{name}__{q['id']}.json": (name, c, q, dose) for name, c, q, dose in jobs}
    assert set(receipt["record_hashes"]) == set(expected)
    assert set(receipt["expected_record_ids"]) == {Path(n).stem for n in expected}
    assert {str(p.relative_to(run)) for p in (run / "records").glob("*.json")} == set(expected)
    calibrations = io.read(run / "calibrations.json")
    for name, (condition, c, q, dose) in expected.items():
        assert io.sha(run / name) == receipt["record_hashes"][name]
        row = io.read(run / name)
        assert row["status"] == "completed" and row["model_id"] == model["id"]
        assert row["question_id"] == q["id"] and row["prompt"] == q["prompt"]
        assert row["condition_id"] == condition
        assert row["layer"] == (c["layer"] if c else None)
        assert row["channel"] == (c["channel"] if c else None)
        output = row["output"]
        assert output["token_sha256"] == token_hash(output["token_ids"])
        assert output["generated_token_count"] == len(output["token_ids"]) <= 128
        assert output["max_new_tokens"] == 128
        assert output["end_reason"] in ("eos_token", "length_limit")
        assert output["end_reason"] != "length_limit" or len(output["token_ids"]) == 128
        assert row["calibration"]["context_sha256"] == hashlib.sha256(row["context"].encode()).hexdigest()
        assert row["calibration"] == calibrations[q["id"]]
        assert output["input_token_sha256"] == row["calibration"]["input_token_sha256"]
        assert (output["end_reason"] == "eos_token") == (output["token_ids"][-1] in [248044, 248046])
        assert not any(t in [248044, 248046] for t in output["token_ids"][:-1])
        if c:
            hook = row["intervention"]
            assert (hook["layer"], hook["channel"], hook["dose"]) == (c["layer"], c["channel"], dose)
            assert hook["calls"] == len(output["token_ids"])
            assert hook["positions"] == row["calibration"]["input_token_count"] + len(output["token_ids"]) - 1
        else:
            assert row["intervention"] is None
    assert set(receipt["asset_hashes"]) == {"metadata.json", "calibrations.json", "sampled_columns.pt"}
    for name, digest in receipt["asset_hashes"].items():
        assert io.sha(run / name) == digest
    assert receipt["integrity"]["hooks_removed"] is True
    metadata = io.read(run / "metadata.json")
    assert metadata["model_id"] == model["id"] and metadata["revision"] == model["revision"]
    assert metadata["hidden_size"] == model["hidden_size"] and metadata["intermediate_size"] == model["intermediate_size"]
    assert metadata["layers"] == list(range(model["layers"]))
    assert metadata["target_weight_sha256_before"] == receipt["integrity"]["target_weight_sha256_after"]
    assert receipt["model_asset_verification"]["status"] == "verified"
    assert receipt["model_asset_verification"]["manifest_sha256"] == io.sha(HERE / "asset_manifest.json")
    if receipt["mode"] == "preflight":
        assert receipt["checks_passed"] is True
        baseline = io.read(run / "records/baseline__Q01.json")["output"]["token_ids"]
        for name, (condition, _, _, _) in expected.items():
            if condition.startswith(("zero-", "restored-")):
                assert io.read(run / name)["output"]["token_ids"] == baseline
    return receipt


def run(args):
    # Permissions and identities are checked before importing Torch or constructing a model.
    identity, auth = check_authorization(args.authorization, args.mode, args.model, args.gpu, args.execute)
    contract, questions, samples = load_design()
    model = next(m for m in contract["models"] if m["id"] == args.model)
    jobs = schedule(args.mode, model, questions, samples[args.model], args.shard, args.shards)
    destination = Path(args.output)
    assert not destination.exists(), "Partial evidence is immutable; use a fresh output directory"
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
               "started_utc": io.utc(), "expected_records": len(jobs), "record_hashes": {}, "asset_hashes": {}}
    receipt["expected_record_ids"] = [f"{name}__{q['id']}" for name, _, q, _ in jobs]
    io.write(destination / "receipt.json", receipt)
    try:
        receipt["model_asset_verification"] = check_model_assets(model)
        from survey_engine import SurveyEngine
        engine = SurveyEngine(model["remote_path"], model, f"cuda:{args.gpu}")
        receipt["load_seconds"] = time.monotonic() - started
        io.immutable(destination / "metadata.json", engine.metadata)
        contexts = {q["id"]: engine.tokenizer.apply_chat_template(
            [{"role": "user", "content": contract["instruction"] + "\n\n" + q["prompt"]}],
            tokenize=False, add_generation_prompt=True, enable_thinking=False) for q in questions}
        cal_start = time.monotonic()
        calibrations = dict(zip(contexts, engine.calibrate(list(contexts.values()))))
        receipt["calibration_seconds"] = time.monotonic() - cal_start
        io.immutable(destination / "calibrations.json", calibrations)
        # Only the sampled columns (about 10 MB across all three models), not bulk model weights.
        directions = {c["id"]: engine.modules[c["layer"]].weight[:, c["channel"]].detach().float().cpu()
                      for c in samples[args.model]}
        engine.torch.save(directions, destination / "sampled_columns.pt")
        for name in ("metadata.json", "calibrations.json", "sampled_columns.pt"):
            receipt["asset_hashes"][name] = io.sha(destination / name)
        baseline_tokens = {}
        for condition, c, question, dose in jobs:
            qid = question["id"]
            arm = (c["layer"], c["channel"], dose) if c else "baseline"
            output = engine.generate([contexts[qid]], arm, [calibrations[qid]], 128, [])[0]
            output["token_sha256"] = token_hash(output["token_ids"])
            hook = engine.last_hook
            row = {"status": "completed", "model_id": args.model, "condition_id": condition,
                   "layer": c["layer"] if c else None, "channel": c["channel"] if c else None,
                   "question_id": qid, "prompt": question["prompt"], "context": contexts[qid],
                   "calibration": calibrations[qid], "intervention": hook, "output": output, "ended_utc": io.utc()}
            name = f"records/{condition}__{qid}.json"
            io.immutable(destination / name, row)
            receipt["record_hashes"][name] = io.sha(destination / name)
            if condition == "baseline":
                baseline_tokens[qid] = output["token_ids"]
            if condition.startswith(("zero-", "restored-")):
                assert output["token_ids"] == baseline_tokens[qid], f"Zero/restoration mismatch: {condition}"
            assert all(not m._forward_pre_hooks for m in engine.modules.values())
            receipt["completed_records"] = len(receipt["record_hashes"])
            io.write(destination / "receipt.json", receipt)
            print(json.dumps({"completed": len(receipt["record_hashes"]), "total": len(jobs),
                              "tokens": len(output["token_ids"]), "seconds": output["batch_seconds"]}), flush=True)
        receipt["integrity"] = engine.verify_unchanged()
        receipt.update(status="completed", checks_passed=True, ended_utc=io.utc(), wall_seconds=time.monotonic()-started)
        io.write(destination / "receipt.json", receipt)
        verify(destination)
    except BaseException:
        receipt.update(status="failed", ended_utc=io.utc(), wall_seconds=time.monotonic()-started,
                       error=traceback.format_exc())
        io.write(destination / "receipt.json", receipt)
        raise
    finally:
        lock.close()


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("freeze")
    check = commands.add_parser("verify")
    check.add_argument("run")
    launch = commands.add_parser("run")
    launch.add_argument("--mode", choices=["preflight", "survey"], required=True)
    launch.add_argument("--model", choices=["2b", "4b", "9b"], required=True)
    launch.add_argument("--gpu", type=int, choices=[0, 1], required=True)
    launch.add_argument("--shard", type=int, default=0)
    launch.add_argument("--shards", type=int, choices=[1, 2], default=1)
    launch.add_argument("--output", required=True)
    launch.add_argument("--authorization", required=True)
    launch.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.command == "freeze":
        freeze()
    elif args.command == "verify":
        receipt = verify(args.run)
        print(json.dumps({"status": receipt["status"], "records": len(receipt["record_hashes"])}))
    else:
        run(args)


if __name__ == "__main__":
    main()
