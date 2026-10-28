#!/usr/bin/env python3
"""Prepare by default. Four fixed-input forwards require --execute and new authorization."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
MODEL = "Qwen/Qwen3.5-4B"
REVISION = "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"
ORDER = ["clean", "A", "B", "AB"]
ROOT_ENGINE = HERE.parent / "root-cause-toy-v1-2026-10-26/root_engine.py"
ASSETS = HERE / "model-assets.json"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def token_hash(tokens):
    return hashlib.sha256(json.dumps(tokens, separators=(",", ":")).encode()).hexdigest()


def source_hashes():
    paths = [Path(__file__), HERE / "trace-format.json", ROOT_ENGINE, ASSETS,
             HERE.parent / "transfer-toy-v1-2026-10-26/transfer_engine.py",
             HERE.parent / "capability-damage-v2-2026-10-26/model_engine.py"]
    return {str(p.relative_to(REPO)): sha(p) for p in paths}


def load_root_module():
    spec = importlib.util.spec_from_file_location("trace_root_engine", ROOT_ENGINE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_input(spec):
    assert set(spec) == {"text", "dose", "channels", "vectors"}
    assert isinstance(spec["text"], str) and spec["text"]
    assert type(spec["dose"]) in (int, float) and spec["dose"] in (0.5, 1.0)
    assert isinstance(spec["channels"], list) and len(spec["channels"]) <= 8
    channels = []
    for row in spec["channels"]:
        assert set(row) == {"layer", "index"}
        assert type(row["layer"]) is int and 0 <= row["layer"] < 32
        assert type(row["index"]) is int and 0 <= row["index"] < 9216
        channels.append((row["layer"], row["index"]))
    assert len(channels) == len(set(channels))
    assert isinstance(spec["vectors"], list) and len(spec["vectors"]) <= 4
    names = []
    for row in spec["vectors"]:
        assert set(row) == {"site", "positions"}
        match = re.fullmatch(r"L(\d+)\.(attention|mlp|residual)", row["site"])
        assert match and int(match[1]) < 32
        positions = row["positions"]
        assert isinstance(positions, list) and 0 < len(positions) <= 8
        assert all(type(p) is int and 0 <= p < 512 for p in positions)
        assert len(positions) == len(set(positions))
        names.append(row["site"])
    assert len(names) == len(set(names))


def ratios(values, reference):
    assert len(values) == len(reference)
    assert all(math.isfinite(x) and x >= 0 for x in values + reference)
    result = [v / r if r else None for v, r in zip(values, reference)]
    assert all(x is None or math.isfinite(x) for x in result)
    return result


def matched_tokens(actual, expected):
    assert actual == expected, "Condition input token identities differ"


def observation_sites(engine):
    sites = {}
    for layer, block in enumerate(engine.layers):
        attention = "linear_attn" if hasattr(block, "linear_attn") else "self_attn"
        for kind, module, position in [
            ("attention", getattr(block, attention), f"{attention}.forward_output before attention residual addition"),
            ("mlp", block.mlp, "mlp.forward_output before MLP residual addition"),
            ("residual", block, "decoder.forward_output after both residual additions")]:
            sites[f"L{layer}.{kind}"] = (module, {"id": f"L{layer}.{kind}", "layer": layer,
                "component": kind, "hook": f"language_model.layers[{layer}].{position}"})
    return sites


def capture_forward(engine, tokens, arm, calibration, channels):
    """Read-only hooks, including channel reads registered after the intervention hooks."""
    torch, saved, selected, handles = engine.torch, {}, {}, []
    inputs = engine._inputs([tokens])
    actual = inputs["input_ids"][0].tolist()
    matched_tokens(actual, tokens)
    try:
        for name, (module, _) in observation_sites(engine).items():
            def capture(_module, _args, output, name=name):
                value = output[0] if isinstance(output, tuple) else output
                assert value.ndim == 3 and tuple(value.shape[:2]) == (1, len(tokens))
                assert torch.isfinite(value).all(), f"Nonfinite output at {name}"
                saved[name] = value[0].detach().float().cpu().clone()
            handles.append(module.register_forward_hook(capture))
        with torch.inference_mode(), engine._intervention(arm, [calibration], inputs["attention_mask"]):
            for row in channels:
                layer, index = row["layer"], row["index"]
                module = engine.layers[layer].mlp.down_proj
                assert index < module.in_features
                def capture_channel(_module, args, key=(layer, index), index=index):
                    value = args[0][0, :, index].detach().float().cpu().clone()
                    assert torch.isfinite(value).all()
                    selected[key] = value.tolist()
                handles.append(module.register_forward_pre_hook(capture_channel))
            engine.counts["forward"] += 1
            logits = engine.model(**inputs, use_cache=False, logits_to_keep=1).logits.detach().cpu().clone()
            assert torch.isfinite(logits).all()
        assert set(saved) == set(observation_sites(engine)), "Missing module observations"
        assert len(selected) == len(channels), "Missing channel observations"
        return saved, selected, logits, dict(engine.last_source_audit)
    finally:
        for handle in handles:
            handle.remove()


def collect_trace(engine, spec, provenance):
    validate_input(spec)
    module = load_root_module()
    tokens = module._transfer.encode_text(engine.tokenizer, spec["text"])
    assert 2 <= len(tokens) <= 512, "Require 2..512 tokens; no implicit truncation"
    assert all(p < len(tokens) for row in spec["vectors"] for p in row["positions"])
    calibration = engine.calibrate([spec["text"]])[0]
    assert calibration["input_token_sha256"] == token_hash(tokens)
    frozen_calibration = json.dumps(calibration, sort_keys=True)
    sites = {name: {**meta, "series": {}} for name, (_, meta) in observation_sites(engine).items()}
    assert all(row["site"] in sites for row in spec["vectors"])
    details = {"channels": [{**row, "hook": "mlp.down_proj input after condition intervention",
                              "values": {}} for row in spec["channels"]],
               "vectors": [{**row, "values": {}} for row in spec["vectors"]]}
    conditions, baseline, interaction = {}, {}, {}
    norm = lambda value: value.double().norm(dim=-1).tolist()
    for condition in ORDER:
        arm = engine.make_condition(condition, dose=spec["dose"])
        values, channels, logits, audit = capture_forward(engine, tokens, arm, calibration, spec["channels"])
        assert json.dumps(calibration, sort_keys=True) == frozen_calibration
        conditions[condition] = {"arm": arm, "recipe": engine.conditions[arm],
            "calibration": json.loads(frozen_calibration), "input_token_sha256": token_hash(tokens),
            "source_write_audit": audit,
            "last_token_logits_sha256": hashlib.sha256(logits.contiguous().view(engine.torch.uint8).numpy().tobytes()).hexdigest()}
        if condition == "clean":
            baseline = values
            interaction = {name: value.clone() for name, value in values.items()}
        for name, value in values.items():
            clean_norm, delta_norm = norm(baseline[name]), norm(value - baseline[name])
            sites[name]["dimension"] = value.shape[-1]
            sites[name]["series"][condition] = {"norm": norm(value), "delta_norm": delta_norm,
                "relative_delta_norm": ratios(delta_norm, clean_norm)}
            if condition != "clean":
                interaction[name] += value * (1 if condition == "AB" else -1)
        for row in details["channels"]:
            row["values"][condition] = channels[(row["layer"], row["index"])]
        for row in details["vectors"]:
            row["values"][condition] = values[row["site"]][row["positions"]].tolist()
    for name, value in interaction.items():
        sizes = norm(value)
        sites[name]["interaction"] = {"definition": "AB-A-B+clean",
            "interpretation": "algebraic_interaction_difference_not_mechanism",
            "norm": sizes, "relative_clean_norm": ratios(sizes, norm(baseline[name]))}
    provenance = {**provenance, "interaction_arithmetic": "float32, evaluated clean-A-B+AB"}
    trace = {"format": "acupuncture.trace.v1", "status": "complete",
        "model": {"repo": MODEL, "revision": REVISION, "metadata": {**engine.metadata,
            "num_hidden_layers": len(engine.layers)}},
        "input": {"text": spec["text"], "text_sha256": hashlib.sha256(spec["text"].encode()).hexdigest(),
            "token_ids": tokens, "token_texts": [engine.tokenizer.decode([t]) for t in tokens],
            "token_sha256": token_hash(tokens)}, "condition_order": ORDER, "conditions": conditions,
        "sites": list(sites.values()), "details": details, "provenance": provenance}
    validate_trace(trace)
    return trace


def validate_trace(trace):
    assert trace["format"] == "acupuncture.trace.v1" and trace["status"] == "complete"
    assert trace["condition_order"] == ORDER and set(trace["conditions"]) == set(ORDER)
    count = len(trace["input"]["token_ids"])
    assert 2 <= count <= 512 and len(trace["input"]["token_texts"]) == count
    token_sha = token_hash(trace["input"]["token_ids"])
    assert token_sha == trace["input"]["token_sha256"]
    calibrations = [row["calibration"] for row in trace["conditions"].values()]
    assert all(row == calibrations[0] for row in calibrations)
    assert calibrations[0]["input_token_sha256"] == token_sha
    assert all(row["input_token_sha256"] == token_sha for row in trace["conditions"].values())
    for site in trace["sites"]:
        assert set(site["series"]) == set(ORDER)
        for condition, series in site["series"].items():
            assert all(len(values) == count for values in series.values())
            assert ratios(series["delta_norm"], site["series"]["clean"]["norm"]) == series["relative_delta_norm"]
            assert all(math.isfinite(x) and x >= 0 for x in series["norm"])
            if condition == "clean":
                assert all(x == 0 for x in series["delta_norm"])
        interaction = site["interaction"]
        assert len(interaction["norm"]) == count and interaction["definition"] == "AB-A-B+clean"
        assert ratios(interaction["norm"], site["series"]["clean"]["norm"]) == interaction["relative_clean_norm"]
    json.dumps(trace, allow_nan=False)


def run(args, engine_factory=None):
    spec = json.loads(args.input.read_text())
    validate_input(spec)
    provenance = {"input_file_sha256": sha(args.input), "source_hashes": source_hashes()}
    if args.execute:
        assert args.authorization, "A new explicit authorization file is required"
        auth = json.loads(args.authorization.read_text())
        assert auth.get("approved") is True and auth.get("scope") == "acupuncture.fixed_input_trace.v1"
        assert auth.get("input_sha256") == provenance["input_file_sha256"]
        assert auth.get("model_revision") == REVISION
        assert auth.get("output") == str(args.output.resolve())
        provenance["authorization_file_sha256"] = sha(args.authorization)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "input.json").write_bytes(args.input.read_bytes())
    receipt = {"started_at": datetime.now(timezone.utc).isoformat(), "status": "prepared",
        "model_loaded": False, "model_repo": MODEL, "model_revision": REVISION, **provenance,
        "conditions": ORDER, "dose": spec["dose"], "token_validation": "pending_execution"}
    engine = None
    try:
        if args.execute:
            assets = json.loads(ASSETS.read_text())
            assert assets["model_revision"] == REVISION and assets["model_repo"] == MODEL
            for row in assets["files"]:
                path = args.model_path / row["file"]
                assert path.stat().st_size == row["expected_bytes"] and sha(path) == row["expected_sha256"]
            factory = engine_factory or load_root_module().RootEngine
            engine = factory(args.model_path, device=args.device)
            receipt["model_loaded"] = True
            trace = collect_trace(engine, spec, provenance)
            receipt["cleanup"] = engine.verify_unchanged()
            (args.output / "trace.json").write_text(json.dumps(trace, ensure_ascii=False, allow_nan=False) + "\n")
            receipt.update(status="complete", token_validation="passed", trace_sha256=sha(args.output / "trace.json"))
    except Exception as error:
        receipt.update(status="failed", error=repr(error))
        raise
    finally:
        if engine is not None and "cleanup" not in receipt:
            try:
                receipt["cleanup"] = engine.verify_unchanged()
            except Exception as error:
                receipt.update(status="failed", cleanup_error=repr(error))
        receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
        (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    assert receipt["status"] != "failed", receipt
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, default=Path("/data/models/Qwen3.5-4B-851bf6e"))
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--authorization", type=Path)
    result = run(parser.parse_args())
    print(json.dumps({"status": result["status"], "model_loaded": result["model_loaded"]}))
