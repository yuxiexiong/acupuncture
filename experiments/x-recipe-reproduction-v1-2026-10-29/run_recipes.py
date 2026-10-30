"""Collect fixed recipe/question pairs without changing or filtering model answers."""
import argparse
import ast
from copy import deepcopy
import importlib.util
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import time
import traceback

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
spec = importlib.util.spec_from_file_location("recipe_io", HERE.parent / "transfer-toy-v1-2026-10-26/run_io.py")
io = importlib.util.module_from_spec(spec)
spec.loader.exec_module(io)


def effective_generation(recipe):
    value = {"do_sample": False, "temperature": 1.0, "top_p": 1.0, "top_k": 0, "min_p": 0.0,
             "repetition_penalty": 1.0, "seed": 0}
    supplied = recipe.get("generation", {})
    assert set(supplied) <= set(value), "Unknown generation option"
    value.update(supplied)
    assert type(value["do_sample"]) is bool
    assert type(value["seed"]) is int and 0 <= value["seed"] < 2**63
    assert type(value["top_k"]) is int and value["top_k"] >= 0
    for key in ("temperature", "top_p", "repetition_penalty"):
        assert type(value[key]) in (int, float) and math.isfinite(value[key]) and value[key] > 0
        value[key] = float(value[key])
    assert value["top_p"] <= 1
    assert type(value["min_p"]) in (int, float) and math.isfinite(value["min_p"]) and 0 <= value["min_p"] <= 1
    value["min_p"] = float(value["min_p"])
    if not value["do_sample"]:
        assert all(value[key] == expected for key, expected in (("temperature", 1.0), ("top_p", 1.0), ("top_k", 0), ("min_p", 0.0))), "Sampling options require do_sample=true"
    return value


def baseline_id(generation):
    return "baseline-" + hashlib.sha256(json.dumps(generation, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]


def design():
    contract, recipes, questions, scales = [io.read(HERE / name) for name in
        ("contract.json", "recipes.json", "questions.json", "scales.json")]
    assert contract["model"]["id"] == "4b" and contract["model"]["layers"] == 32
    assert contract["model"]["hidden_size"] == 2560 and contract["model"]["intermediate_size"] == 9216
    assert recipes and questions
    qmap = {q["id"]: q for q in questions}
    assert len(qmap) == len(questions) and len({r["id"] for r in recipes}) == len(recipes)
    assert len({q["prompt"] for q in questions}) == len(questions), "Reuse a question ID for identical prompts"
    for item in recipes + questions:
        assert re.fullmatch(r"[A-Za-z0-9_-]+", item["id"])
    assert all(q["prompt"].strip() for q in questions)
    assert set(scales["residual_scales"]) == {str(i) for i in range(32)}
    assert all(math.isfinite(v) and v > 0 for v in scales["residual_scales"].values())
    used = set()
    for recipe in recipes:
        assert recipe["id"] not in ("baseline", "zero", "restored") and not recipe["id"].startswith("baseline-")
        effective_generation(recipe)
        assert recipe.get("normalization", "fixed_reference") in ("fixed_reference", "per_prompt_median")
        assert len(recipe["question_ids"]) == len(set(recipe["question_ids"])) == 5
        assert set(recipe["question_ids"]) <= set(qmap)
        used.update(recipe["question_ids"])
        points = recipe["interventions"]
        assert points and len({(p["layer"], p["neuron"]) for p in points}) == len(points)
        for p in points:
            assert type(p["layer"]) is type(p["neuron"]) is int
            assert 0 <= p["layer"] < 32 and 0 <= p["neuron"] < 9216
            assert math.isfinite(p["dose"]) and p["dose"] != 0
    assert used == set(qmap), "Unreferenced questions would expand the requested scope"
    return contract, recipes, questions, scales


def freeze():
    design()
    files = [HERE / n for n in ("contract.json", "recipes.json", "questions.json", "scales.json",
        "recipe_engine.py", "run_recipes.py", "test_recipe_runner.py", "PROTOCOL.zh-CN.md",
        "build_manifest.py", "prior_recipes.json", "question_design.json", "catalog.json",
        "sources/neuronary_parameter_snapshot.json", "sources/additional_notes_variants.json",
        "sources/eligibility_audit.json", "public_source_updates.json")]
    files += [HERE.parent / n for n in ("layer-survey-toy-v1-2026-10-27/survey_engine.py",
        "layer-survey-toy-v1-2026-10-27/asset_manifest.json", "transfer-toy-v1-2026-10-26/transfer_engine.py",
        "transfer-toy-v1-2026-10-26/run_io.py", "capability-damage-v2-2026-10-26/model_engine.py",
        "neuron-explorer-multimodel-v2-2026-10-26/upstream/explorer/runtime.py")]
    io.immutable(HERE / "freeze.json", {"experiment": HERE.name, "created_utc": io.utc(),
        "files": {str(p.relative_to(REPO)): io.sha(p) for p in files}})


def check_freeze():
    frozen = io.read(HERE / "freeze.json")
    assert frozen["experiment"] == HERE.name
    for path, digest in frozen["files"].items():
        assert io.sha(REPO / path) == digest, f"Frozen source changed: {path}"
    return io.sha(HERE / "freeze.json")


def schedule(recipes, questions, shard=0, shards=1):
    assert 0 <= shard < shards <= 2
    baselines = {}
    for recipe in recipes:
        generation = effective_generation(recipe)
        bid = baseline_id(generation)
        for qid in recipe["question_ids"]:
            key = (bid, qid)
            if key in baselines:
                assert baselines[key][3] == generation, "Baseline ID collision"
            baselines[key] = (bid, [], qid, generation)
    jobs = [job for i, job in enumerate(baselines.values()) if i % shards == shard]
    for i, recipe in enumerate(recipes):
        if i % shards == shard:
            jobs += [(recipe["id"], recipe["interventions"], qid, effective_generation(recipe)) for qid in recipe["question_ids"]]
    return jobs


def preflight_jobs(recipes):
    qid, points = recipes[0]["question_ids"][0], recipes[0]["interventions"]
    zero = [dict(p, dose=0.0) for p in points]
    generation = effective_generation(recipes[0])
    jobs = [(baseline_id(generation), [], qid, generation), ("zero", zero, qid, generation),
            (recipes[0]["id"], points, qid, generation), ("restored", [], qid, generation)]
    representatives = {}
    for recipe in recipes:
        representatives.setdefault(baseline_id(effective_generation(recipe)), recipe)
    extras = list(representatives.values())
    for predicate in (
        lambda r: r.get("normalization") == "per_prompt_median",
        lambda r: len({p["layer"] for p in r["interventions"]}) < len(r["interventions"]),
    ):
        extras += next(([r] for r in recipes if predicate(r)), [])
    seen = {(r, q) for r, _, q, _ in jobs}
    for recipe in extras:
        qid, generation = recipe["question_ids"][0], effective_generation(recipe)
        for rid, points in ((baseline_id(generation), []), (recipe["id"], recipe["interventions"])):
            if (rid, qid) not in seen:
                jobs.append((rid, points, qid, generation))
                seen.add((rid, qid))
    return jobs


def normalization_modes(recipes):
    result = {r["id"]: r.get("normalization", "fixed_reference") for r in recipes}
    result["zero"] = recipes[0].get("normalization", "fixed_reference")
    return result


def check_assets(model):
    manifest = HERE.parent / "layer-survey-toy-v1-2026-10-27/asset_manifest.json"
    expected = io.read(manifest)["4b"]
    assert expected["revision"] == model["revision"]
    for name, value in expected["files"].items():
        path = Path(model["model_path"]) / name
        assert path.stat().st_size == value["bytes"] and io.sha(path) == value["sha256"], name
    return {"manifest_sha256": io.sha(manifest), "files": len(expected["files"]), "status": "verified"}


def lock_gpu(gpu):
    import fcntl
    lock = open(f"/tmp/acupuncture-recipe-gpu{gpu}.lock", "w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    memory = subprocess.check_output(["nvidia-smi", f"--id={gpu}", "--query-gpu=memory.used", "--format=csv,noheader,nounits"], text=True)
    assert int(memory.strip()) < 256, "GPU occupied; do not disturb another task"
    return lock


def calibrate(args):
    """Author's fixed-text fallback, once for all layers, before the design is frozen."""
    assert args.execute
    output = Path(args.output)
    assert not output.exists(), "Never overwrite an existing scale source"
    contract = io.read(HERE / "contract.json")
    lock = lock_gpu(args.gpu)
    started = time.monotonic()
    assets = check_assets(contract["model"])
    source = HERE.parent / "neuron-explorer-multimodel-v2-2026-10-26/upstream/explorer/runtime.py"
    values = [ast.literal_eval(node.value) for node in ast.parse(source.read_text()).body
              if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "REFERENCE_TEXT" for t in node.targets)]
    assert len(values) == 1 and isinstance(values[0], str)
    text = values[0]
    from recipe_engine import RecipeEngine, survey
    engine = RecipeEngine(contract["model"]["model_path"], contract["model"], f"cuda:{args.gpu}")
    assert all(engine.metadata["versions"][key] == val for key, val in contract["versions"].items())
    ids = engine.tokenizer(text, return_tensors="pt").input_ids.to(engine.device)
    scales, handles = {}, []
    try:
        for layer, block in enumerate(engine.layers):
            def capture(_module, _args, output, layer=layer):
                residual = output[0] if isinstance(output, tuple) else output
                value = float(residual[0, 1:].float().norm(dim=-1).median())
                assert math.isfinite(value) and value > 0
                scales[str(layer)] = value
            handles.append(block.register_forward_hook(capture))
        with engine.torch.inference_mode():
            engine.model(input_ids=ids, use_cache=False, logits_to_keep=1)
    finally:
        for handle in handles:
            handle.remove()
    assert set(scales) == {str(i) for i in range(32)}
    io.immutable(output, {"residual_scales": scales, "source": {
        "method": "Lyra fixed REFERENCE_TEXT fallback; raw text, no chat template; skip first token; torch.median of post-layer L2 norms",
        "source_file": str(source.relative_to(REPO)), "source_sha256": io.sha(source),
        "author_private_stats_identity": "not_available; not claimed numerically identical",
        "reference_text": text, "reference_token_ids": ids[0].tolist(),
        "reference_text_sha256": survey.transfer.text_hash(text),
        "reference_token_sha256": survey.transfer.token_hash(ids[0].tolist()),
        "model_revision": contract["model"]["revision"], "metadata": engine.metadata,
        "asset_verification": assets, "integrity": engine.verify_unchanged(),
        "ended_utc": io.utc(), "wall_seconds": time.monotonic() - started}})
    print(f"Saved 32 fixed scales to {output}")


def verify(run):
    from recipe_engine import validate_hook, survey
    run = Path(run)
    receipt = io.read(run / "receipt.json")
    assert receipt["status"] == "completed" and receipt["freeze_sha256"] == check_freeze()
    contract, recipes, questions, scales = design()
    qmap = {q["id"]: q for q in questions}
    modes = normalization_modes(recipes)
    jobs = receipt["jobs"]
    if receipt["mode"] == "run":
        assert jobs == [list(j) for j in schedule(recipes, questions, receipt["shard"], receipt["shards"])]
    else:
        assert receipt["mode"] == "preflight" and jobs == [list(j) for j in preflight_jobs(recipes)]
    assert receipt["scales_sha256"] == io.sha(HERE / "scales.json")
    expected = {f"records/{rid}__{qid}.json" for rid, _, qid, _ in jobs}
    assert set(receipt["record_hashes"]) == expected
    assert {str(p.relative_to(run)) for p in (run / "records").glob("*.json")} == expected
    for rid, points, qid, generation in jobs:
        path = f"records/{rid}__{qid}.json"
        assert io.sha(run / path) == receipt["record_hashes"][path]
        row = io.read(run / path)
        out, cal = row["output"], row["calibration"]
        assert row["recipe_id"] == rid and row["question_id"] == qid and row["prompt"] == qmap[qid]["prompt"]
        assert row["baseline_id"] == baseline_id(generation)
        assert out["effective_generation"] == generation
        assert row["interventions"] == points
        assert cal["normalization"] == modes.get(rid, "fixed_reference")
        assert set(cal["residual_scales"]) == {str(i) for i in range(32)}
        assert all(math.isfinite(v) and v > 0 for v in cal["residual_scales"].values())
        if cal["normalization"] == "fixed_reference":
            assert cal["residual_scales"] == scales["residual_scales"]
            assert cal["scales_sha256"] == receipt["scales_sha256"]
        assert cal["context_sha256"] == survey.transfer.text_hash(row["context"])
        assert out["input_token_sha256"] == cal["input_token_sha256"]
        assert out["token_sha256"] == survey.transfer.token_hash(out["token_ids"])
        assert out["generated_token_count"] == len(out["token_ids"]) <= out["max_new_tokens"] == 128
        assert out["end_reason"] in ("eos_token", "length_limit") and out["token_ids"]
        assert not any(t in [248044, 248046] for t in out["token_ids"][:-1])
        assert (out["end_reason"] == "eos_token") == (out["token_ids"][-1] in [248044, 248046])
        assert out["end_reason"] != "length_limit" or len(out["token_ids"]) == 128
        validate_hook(row["hook_audit"], points, cal, len(out["token_ids"]))
    metadata = io.read(run / "metadata.json")
    assert io.sha(run / "metadata.json") == receipt["metadata_sha256"]
    assert metadata["target_weight_sha256_before"] == receipt["integrity"]["target_weight_sha256_after"]
    assert receipt["integrity"]["hooks_removed"] is True
    if receipt["mode"] == "preflight":
        qid = recipes[0]["question_ids"][0]
        bid = baseline_id(effective_generation(recipes[0]))
        rows = [io.read(run / f"records/{rid}__{qid}.json")["output"]["token_ids"] for rid in (bid, "zero", "restored")]
        assert rows[0] == rows[1] == rows[2]
    return receipt


def run(args):
    assert args.execute, "Explicit --execute required before loading a model"
    identity = check_freeze()
    contract, recipes, questions, scales = design()
    if args.mode == "run":
        approval = io.read(HERE / "formal_approval.json")
        assert approval["status"] == "approved" and approval["freeze_sha256"] == identity, "Formal collection requires user approval after GPU Ready discussion"
        assert args.preflight, "A completed preflight is required"
        previous = verify(args.preflight)
        assert previous["mode"] == "preflight" and previous["freeze_sha256"] == identity
        assert previous["gpu"] == args.gpu, "Use the preflight from this GPU"
    destination = Path(args.output)
    assert not destination.exists(), "Preserve partial attempts; choose a new output directory"
    lock = lock_gpu(args.gpu)
    jobs = schedule(recipes, questions, args.shard, args.shards)
    if args.mode == "preflight":
        assert args.shard == 0 and args.shards == 1
        jobs = preflight_jobs(recipes)
    destination.mkdir(parents=True)
    started = time.monotonic()
    receipt = {"status": "running", "mode": args.mode, "experiment": HERE.name, "gpu": args.gpu,
        "shard": args.shard, "shards": args.shards, "freeze_sha256": identity, "started_utc": io.utc(),
        "jobs": jobs, "record_hashes": {}, "expected_records": len(jobs), "scales_sha256": io.sha(HERE / "scales.json")}
    io.write(destination / "receipt.json", receipt)
    try:
        receipt["model_asset_verification"] = check_assets(contract["model"])
        from recipe_engine import RecipeEngine, survey, validate_hook
        engine = RecipeEngine(contract["model"]["model_path"], contract["model"], f"cuda:{args.gpu}")
        assert all(engine.metadata["versions"][key] == val for key, val in contract["versions"].items())
        receipt["load_seconds"] = time.monotonic() - started
        io.immutable(destination / "metadata.json", engine.metadata)
        receipt["metadata_sha256"] = io.sha(destination / "metadata.json")
        qmap = {q["id"]: q for q in questions}
        modes, prompt_calibrations = normalization_modes(recipes), {}
        for rid, points, qid, generation in jobs:
            prompt = qmap[qid]["prompt"]
            context = engine.tokenizer.apply_chat_template([{"role": "user", "content": prompt}],
                tokenize=False, add_generation_prompt=True, enable_thinking=False)
            tokens = survey.transfer.encode_text(engine.tokenizer, context)
            calibration = {"context_sha256": survey.transfer.text_hash(context),
                "input_token_sha256": survey.transfer.token_hash(tokens), "input_token_count": len(tokens),
                "normalization": "fixed_reference", "residual_scales": scales["residual_scales"],
                "scales_sha256": io.sha(HERE / "scales.json")}
            if modes.get(rid, "fixed_reference") == "per_prompt_median":
                if context not in prompt_calibrations:
                    prompt_calibrations[context] = engine.prompt_calibration(context)
                calibration = prompt_calibrations[context]
            output = engine.generate_recipe(context, points, calibration, generation)
            output["token_sha256"] = survey.transfer.token_hash(output["token_ids"])
            audit = deepcopy(engine.last_hook)
            row = {"recipe_id": rid, "baseline_id": baseline_id(generation), "question_id": qid, "prompt": prompt, "context": context,
                "interventions": points, "calibration": calibration, "hook_audit": audit,
                "output": output, "ended_utc": io.utc()}
            name = f"records/{rid}__{qid}.json"
            io.immutable(destination / name, row)
            receipt["record_hashes"][name] = io.sha(destination / name)
            validate_hook(audit, points, calibration, len(output["token_ids"]))
            receipt["completed_records"] = len(receipt["record_hashes"])
            io.write(destination / "receipt.json", receipt)
            print(f"{receipt['completed_records']}/{len(jobs)} {rid}/{qid} {len(output['token_ids'])} tokens", flush=True)
        receipt["integrity"] = engine.verify_unchanged()
        receipt.update(status="completed", ended_utc=io.utc(), wall_seconds=time.monotonic()-started)
        io.write(destination / "receipt.json", receipt)
        verify(destination)
    except BaseException:
        receipt.update(status="failed", ended_utc=io.utc(), traceback=traceback.format_exc(), wall_seconds=time.monotonic()-started)
        io.write(destination / "receipt.json", receipt)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("freeze", "verify", "calibrate", "preflight", "run"))
    parser.add_argument("--output")
    parser.add_argument("--gpu", type=int, default=0)
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--shards", type=int, default=1)
    parser.add_argument("--preflight")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.mode == "freeze":
        freeze()
    elif args.mode == "calibrate":
        calibrate(args)
    elif args.mode == "verify":
        print(verify(args.output)["status"])
    else:
        run(args)
