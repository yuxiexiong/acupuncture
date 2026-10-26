"""Prepare or run the bounded judgment/report diagnostic. Default is CPU-only."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import statistics
import sys
import time
import traceback
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PARENT = HERE.parent / "root-cause-toy-v1-2026-10-26"
# Reuse the frozen implementation, including its sibling imports, unchanged.
sys.path.insert(0, str(PARENT))
import run_root as old
import parallel_validate
from root_engine import RootEngine, encode_pair, text_hash, token_hash
import task_data
import analyze

read, sha, digest = old.read, old.sha, old.digest
PARENT_RUN = PARENT / "runs/root-parallel-r01"
LOCAL_FILES = ["contract.json", "CONTRACT.zh-CN.md", "RUNBOOK.zh-CN.md",
    "authorization.prepare.json", "experiment.py", "task_data.py", "analyze.py",
    "test_data.py", "test_analyze.py", "test_experiment.py",
    "data/items.jsonl", "data/manifest.json"]


def utc():
    return datetime.now(timezone.utc).isoformat()


def write(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def parent_inputs():
    receipt = parallel_validate.verify_merged(PARENT_RUN)
    contract = read(HERE / "contract.json")
    if sha(PARENT_RUN / "receipt.json") != contract["parent_receipt_sha256"]:
        raise ValueError("Parent validation receipt changed")
    previous = read(PARENT / "contract.json")
    if contract["source"] != previous["source"] or contract["needles"] != previous["needles"]:
        raise ValueError("Model identity or needles differ from the completed parent")
    for identity, spec in contract["candidates"].items():
        candidate = read(PARENT_RUN / identity / "candidate.json")
        if spec != {key: candidate[key] for key in ("component", "positions", "control_seed")}:
            raise ValueError("Candidate identity or matched-control seed changed")
    return receipt


def frozen_files():
    paths = {HERE / name for name in LOCAL_FILES}
    paths.update(REPO / name for name in read(PARENT / "freeze.json")["files"])
    paths.update([PARENT / "freeze.json", PARENT / "parallel_validate.py", PARENT_RUN / "receipt.json"])
    return sorted(paths)


def freeze():
    parent_inputs()
    task_data.verify()
    path = HERE / "freeze.json"
    if path.exists():
        raise FileExistsError("Never overwrite a freeze; finish preparation before freezing")
    value = {"schema_version": 1, "status": "prepared_not_model_validated",
        "model_execution_authorized": False,
        "files": {str(p.relative_to(REPO)): sha(p) for p in frozen_files()}}
    write(path, value)
    return {"status": value["status"], "freeze_sha256": sha(path), "model_loaded": False}


def verify():
    value = read(HERE / "freeze.json")
    if (value.get("schema_version") != 1 or value.get("status") != "prepared_not_model_validated"
            or value.get("model_execution_authorized") is not False):
        raise ValueError("Preparation is not model authorization")
    expected = {str(p.relative_to(REPO)): sha(p) for p in frozen_files()}
    if value.get("files") != expected:
        raise ValueError("Frozen contract, code, data, or parent dependency changed")
    parent_inputs()
    counts = task_data.verify()
    return {**counts, "freeze_sha256": sha(HERE / "freeze.json"), "model_loaded": False,
        "formal_run_started": False, "parent_stage": "validate-parallel"}


def tokenizer_check(tokenizer, items):
    lengths = []
    for item in items:
        pairs = [encode_pair(tokenizer, item["context"], text) for text in item["continuations"]]
        if any(len(tail) != 1 for _, tail in pairs) or len({tuple(head) for head, _ in pairs}) != 1:
            raise ValueError("All four labels must be single tokens after the same prefix")
        if len({tail[0] for _, tail in pairs}) != 4:
            raise ValueError("Labels must tokenize to four distinct tokens")
        lengths.append(len(pairs[0][0]))
    return {"status": "passed", "item_count": len(items), "single_token_labels": True,
        "context_tokens_min": min(lengths), "context_tokens_median": statistics.median(lengths),
        "context_tokens_max": max(lengths), "total_context_tokens": sum(lengths)}


def bind_calibration(item, reference, tokenizer):
    """Keep dose fixed; never relabel a reference token hash as the current input."""
    if reference["context_sha256"] != item["reference_context_sha256"]:
        raise ValueError("Calibration is not from this base's canonical clean prompt")
    scales = reference["residual_scales"]
    if set(scales) != {"13", "14"} or any(not math.isfinite(v) or v <= 0 for v in scales.values()):
        raise ValueError("Need two finite positive reference scales")
    prefix, _ = encode_pair(tokenizer, item["context"], item["continuations"][0])
    return {"context_sha256": text_hash(item["context"]), "residual_scales": deepcopy(scales),
        "reference_context_sha256": reference["context_sha256"],
        "reference_calibration_sha256": digest(reference),
        "binding_input_token_sha256": token_hash(prefix), "binding_input_token_count": len(prefix)}


def check_authorization(path, candidate, execute):
    if not execute or path is None:
        raise ValueError("Stopped before model loading: a new user launch authorization and --execute are required")
    value = read(path)
    contract = read(HERE / "contract.json")
    if (value.get("status") != "authorized" or value.get("experiment") != contract["experiment"]
            or value.get("freeze_sha256") != sha(HERE / "freeze.json")
            or value.get("candidate_ids") != ["C05", "C01"]
            or value.get("maximum_model_workers") != 2
            or not value.get("user_instruction") or not value.get("granted_at")
            or candidate not in value["candidate_ids"]):
        raise ValueError("Missing exact new-run authorization; old launch permissions do not apply")
    return value


def metadata_check(engine, source):
    if (engine.metadata["dtype"] != source["dtype"] or engine.weight_hashes != source["target_weight_sha256"]
            or engine.metadata["attention_backend"] != "eager"
            or engine.metadata["batch_size"] != 1):
        raise ValueError("Model identity, precision or backend changed")
    for package in ("torch", "transformers"):
        if engine.metadata["versions"][package] != source[package + "_version"]:
            raise ValueError("Runtime differs from the frozen experiment")


def collect(engine, items, candidate, output):
    """Exactly one candidate and all variants; no winner selection or resume."""
    arms = {"clean": engine.make_condition("clean"), "AB_d1": engine.make_condition("AB", 1.0)}
    references, rows = {}, []
    for number, item in enumerate(items):
        base = item["base_id"]
        if base not in references:
            references[base] = engine.calibrate([item["reference_context"]])[0]
        reference = references[base]
        calibration = bind_calibration(item, reference, engine.tokenizer)
        values = old.patched_conditions(engine, item, calibration, arms, candidate)
        row = {key: item[key] for key in ("id", "base_id", "pair_id", "panel", "demand", "rotation",
            "order", "target_index", "target_content_index", "context_sha256")}
        row.update(item_sha256=digest(item), calibration=calibration,
            reference_calibration=reference, conditions=values)
        write(output / f"item-{number:03d}.json", row)
        rows.append(row)
        print(f"{candidate['id']} {number+1}/{len(items)} {item['panel']}", flush=True)
    return rows


def run(candidate, output, authorization=None, execute=False, device="cuda:0", engine_factory=None):
    launch = check_authorization(authorization, candidate, execute)  # before model construction
    verify()
    contract = read(HERE / "contract.json")
    if candidate not in contract["candidates"] or device != contract["devices"][candidate]:
        raise ValueError("Use the fixed one-candidate-per-GPU assignment")
    items = task_data.read_rows(HERE / "data/items.jsonl")
    output = Path(output).resolve()
    if not output.is_relative_to((HERE / "runs").resolve()):
        raise ValueError("New evidence belongs under this experiment's runs directory")
    output.mkdir(parents=True, exist_ok=False)
    write(output / "launch-authorization.json", launch)
    start = time.monotonic()
    receipt = {"stage": "judgment-report-diagnostic", "status": "running", "started_at": utc(),
        "candidate_id": candidate, "freeze_sha256": sha(HERE / "freeze.json"),
        "authorization_sha256": sha(authorization), "parent_receipt_sha256": contract["parent_receipt_sha256"],
        "authorization_content_sha256": digest(launch),
        "model_loaded": False, "device": device, "expected_items": len(items)}
    write(output / "receipt.json", receipt)
    engine = None
    try:
        engine = (engine_factory or RootEngine)(contract["source"]["model_path"], device=device, threads=4)
        receipt["model_loaded"] = True
        metadata_check(engine, contract["source"])
        receipt["model_metadata"] = engine.metadata
        receipt["tokenizer_check"] = tokenizer_check(engine.tokenizer, items)
        if receipt["tokenizer_check"]["context_tokens_max"] > engine.max_length:
            raise ValueError("Frozen prompt exceeds model context limit")
        spec = {"id": candidate, **contract["candidates"][candidate]}
        # Small real identity check is part of the later authorized run, not preparation.
        first = items[0]
        calibration = engine.calibrate([first["reference_context"]])[0]
        bound = bind_calibration(first, calibration, engine.tokenizer)
        clean_arm = engine.make_condition("clean")
        clean = engine.score_item(first, clean_arm, bound)
        identity = engine.score_item(first, clean_arm, bound,
            patch={**spec, "donor_arm": clean_arm, "mode": "donor"})
        old.check_patch_output(identity, set(), first, "identity")
        if clean["scores"] != identity["scores"]:
            raise ValueError("Identity replacement changed scores")
        write(output / "runtime-check.json", {"identity_exact": True, "clean": clean, "identity": identity})
        rows = collect(engine, items, spec, output)
        engine_verification = engine.verify_unchanged()
        receipt["verification"] = engine_verification
        write(output / "summary.json", analyze.summarize(rows))
        receipt["status"] = "completed"
    except Exception as exc:
        receipt["status"] = "failed"
        receipt["error"] = {"type": type(exc).__name__, "message": str(exc)}
        if hasattr(exc, "evidence"):
            write(output / "technical-failure-evidence.json", exc.evidence)
        (output / "failure.log").write_text(traceback.format_exc())
        if engine is not None:
            try:
                receipt["verification_after_failure"] = engine.verify_unchanged()
            except Exception as check_error:
                receipt["verification_error"] = repr(check_error)
        raise
    finally:
        receipt.update(finished_at=utc(), wall_seconds=time.monotonic() - start,
            counts=engine.counts if engine is not None else {}, files=old.evidence_manifest(output))
        write(output / "receipt.json", receipt)
    return receipt


def verify_row(item, row, candidate, references):
    for key in ("id", "base_id", "pair_id", "panel", "demand", "rotation", "order",
                "target_index", "target_content_index", "context_sha256"):
        if row[key] != item[key]:
            raise ValueError("Saved item identity or experimental factors changed")
    if row["item_sha256"] != digest(item):
        raise ValueError("Output does not match the frozen item")
    reference, binding = row["reference_calibration"], row["calibration"]
    if (reference["context_sha256"] != item["reference_context_sha256"]
            or binding["reference_calibration_sha256"] != digest(reference)
            or binding["reference_context_sha256"] != reference["context_sha256"]
            or binding["context_sha256"] != item["context_sha256"]
            or binding["residual_scales"] != reference["residual_scales"]):
        raise ValueError("Reference calibration or current-input binding changed")
    base = item["base_id"]
    if base in references and references[base] != reference:
        raise ValueError("Variants of a base must share the exact reference calibration")
    references[base] = reference
    if set(row["conditions"]) != set(analyze.CONDITIONS):
        raise ValueError("Missing or extra condition")
    for label, output in row["conditions"].items():
        needles = {"13", "14"} if label in ("AB_d1", "repair", "control_repair") else set()
        details = output["choice_details"]
        if len(details) != 4:
            raise ValueError("Missing choice-level evidence")
        for detail in details:
            if (len(detail["continuation_token_ids"]) != 1
                    or detail["context_token_count"] != binding["binding_input_token_count"]
                    or detail["input_token_sha256"] != binding["binding_input_token_sha256"]
                    or set(detail["source_write_audit"]) != needles):
                raise ValueError("Choice input or source needle audit changed")
            for layer, write_audit in detail["source_write_audit"].items():
                sign = -1 if layer == "13" else 1
                if (write_audit["channel"] != {"13": 7956, "14": 8949}[layer]
                        or write_audit["positions"] != binding["binding_input_token_count"]
                        or write_audit["nonzero_positions"] <= 0
                        or sign * write_audit["offset_mean"] <= 0):
                    raise ValueError("Wrong source needle channel")
        if label in ("clean", "AB_d1"):
            if any(output["patch_audit"]):
                raise ValueError("Baseline must not contain a patch")
            continue
        old.check_patch_output(output, needles, item, label)
        for audits in output["patch_audit"]:
            audit = audits[0]
            if (audit["component"] != candidate["component"]
                    or audit["positions"] != [binding["binding_input_token_count"] - 1]
                    or audit["donor_positions"] != audit["positions"]
                    or audit["mode"] != ("matched" if label.startswith("control_") else "donor")
                    or audit["recipient_arm"] != ("AB@1" if needles else "clean@1")
                    or audit["donor_arm"] != ("clean@1" if needles else "AB@1")
                    or audit["recipient_input_sha256"] != binding["binding_input_token_sha256"]
                    or audit["donor_input_sha256"] != audit["recipient_input_sha256"]):
                raise ValueError("Patch component, scope, direction or donor input changed")


def verify_run(output):
    verify()
    output = Path(output)
    receipt = read(output / "receipt.json")
    contract = read(HERE / "contract.json")
    if (receipt.get("stage") != "judgment-report-diagnostic" or receipt.get("status") != "completed"
            or receipt.get("freeze_sha256") != sha(HERE / "freeze.json")
            or receipt.get("candidate_id") not in contract["candidates"]
            or receipt.get("parent_receipt_sha256") != contract["parent_receipt_sha256"]
            or receipt.get("files") != old.evidence_manifest(output)):
        raise ValueError("Incomplete or changed diagnostic evidence")
    items = task_data.read_rows(HERE / "data/items.jsonl")
    if len(list(output.glob("item-*.json"))) != len(items):
        raise ValueError("Missing or extra item outputs")
    launch_path = output / "launch-authorization.json"
    check_authorization(launch_path, receipt["candidate_id"], True)
    if digest(read(launch_path)) != receipt["authorization_content_sha256"]:
        raise ValueError("Saved launch authorization changed")
    metadata_check(SimpleNamespace(metadata=receipt["model_metadata"],
        weight_hashes=receipt["model_metadata"]["target_weight_sha256_before"]), contract["source"])
    records, references = [], {}
    for number, item in enumerate(items):
        row = read(output / f"item-{number:03d}.json")
        verify_row(item, row, contract["candidates"][receipt["candidate_id"]], references)
        records.append(row)
    analyze.validate(records)
    if (not receipt["verification"].get("hooks_removed")
            or not receipt["verification"].get("parameter_gradients_absent")
            or receipt["verification"].get("target_weight_sha256_after") != contract["source"]["target_weight_sha256"]
            or receipt["counts"].get("forward") != 10252
            or receipt["counts"].get("calibration_forward") != 49
            or receipt["counts"].get("backward") != 0):
        raise ValueError("Missing end-of-run restoration verification")
    return {"status": "completed", "candidate_id": receipt["candidate_id"], "items": len(records)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("freeze")
    p = sub.add_parser("check")
    p.add_argument("--tokenizer", action="store_true", help="CPU-only tokenizer audit; no model loading")
    p = sub.add_parser("run")
    p.add_argument("--candidate", choices=("C05", "C01"), required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--authorization", type=Path)
    p.add_argument("--execute", action="store_true")
    p.add_argument("--device", choices=("cuda:0", "cuda:1"), required=True)
    p = sub.add_parser("verify-run")
    p.add_argument("--output", type=Path, required=True)
    args = vars(parser.parse_args())
    command = args.pop("command")
    if command == "check":
        with_tokenizer = args.pop("tokenizer")
        result = verify()
        if with_tokenizer:
            from transformers import AutoTokenizer
            tokenizer = AutoTokenizer.from_pretrained(read(HERE / "contract.json")["source"]["model_path"],
                local_files_only=True, trust_remote_code=False)
            result["tokenizer_check"] = tokenizer_check(tokenizer, task_data.read_rows(HERE / "data/items.jsonl"))
    else:
        result = {"freeze": freeze, "run": run, "verify-run": verify_run}[command](**args)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
