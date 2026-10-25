"""Read-only first-three-record audit for each shard; tokenizer only, no model."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import traceback

ROOT = Path("/workspace/acupuncture/experiments/capability-damage-v2-2026-10-26")
sys.path.insert(0, str(ROOT))
from model_engine import encode_pair, encode_text, text_hash, token_hash


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


audit = {"status": "started", "started_utc": datetime.now(timezone.utc).isoformat(),
         "scope": "First three completed MMLU pairs per shard; no score interpretation or GPU inference",
         "check_count": 0, "records": [], "shards": [], "failures": []}


def check(condition, name):
    audit["check_count"] += 1
    if not condition:
        raise AssertionError(name)


try:
    protocol = read(ROOT / "protocol.json")
    manifest = read(ROOT / "task_manifest.json")
    audit["protocol_sha256"] = sha(ROOT / "protocol.json")
    audit["manifest_sha256"] = sha(ROOT / "task_manifest.json")
    check(audit["manifest_sha256"] == protocol["task_manifest_sha256"], "protocol binds manifest")
    for name, expected in protocol["source_sha256"].items():
        check(sha(ROOT / name) == expected, "frozen source:" + name)
    audit["source_sha256"] = protocol["source_sha256"]
    item_path = ROOT / manifest["files"]["mmlu"]["file"]
    check(sha(item_path) == manifest["files"]["mmlu"]["sha256"], "frozen MMLU items hash")
    items = [json.loads(line) for line in item_path.read_text().splitlines()]
    by_id = {row["id"]: row for row in items}
    check(len(items) == len(by_id) == protocol["counts"]["mmlu"] == 14042, "frozen MMLU count and unique identities")
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(protocol["model"]["remote_path"], local_files_only=True, trust_remote_code=False)
    seen, orders, engines = set(), [], []
    for shard in range(2):
        directory = ROOT / "outputs" / f"mmlu-shard{shard}-r01"
        receipt_bytes = (directory / "receipt.json").read_bytes()
        receipt = json.loads(receipt_bytes)
        preflight = protocol["preflight"][shard]
        preflight_path = ROOT / preflight["file"]
        validation = read(preflight_path)
        check(sha(preflight_path) == preflight["sha256"] == receipt["validation_receipt_sha256"], f"shard{shard}: frozen preflight")
        check(validation["status"] == "completed", f"shard{shard}: preflight passed")
        check(receipt["protocol_sha256"] == audit["protocol_sha256"] and receipt["task_manifest_sha256"] == audit["manifest_sha256"], f"shard{shard}: protocol and manifest binding")
        check(receipt["source_sha256"] == protocol["source_sha256"], f"shard{shard}: source binding")
        check(receipt["items_sha256"] == manifest["files"]["mmlu"]["sha256"], f"shard{shard}: items binding")
        check(receipt["assets"] == validation["assets"], f"shard{shard}: complete model asset receipt equality")
        check(receipt["engine"] == validation["engine"], f"shard{shard}: runtime matches own preflight")
        check(receipt["arguments"]["batch_size"] == "1" and receipt["engine"]["batch_size"] == 1, f"shard{shard}: batch1")
        check(receipt["arguments"]["shard_index"] == str(shard) and receipt["arguments"]["shard_count"] == "2", f"shard{shard}: shard identity")
        order = receipt["execution_order"]
        check(len(order) == len(set(order)) == receipt["expected_pairs"] == 7021, f"shard{shard}: complete unique assigned IDs")
        orders.append(set(order))
        engines.append(receipt["engine"])
        worker = read(ROOT / f"worker-{shard}.json")
        check(worker["gpu"] == worker["shard_index"] == shard, f"shard{shard}: worker assignment")
        children_path = Path(f"/proc/{worker['pid']}/task/{worker['pid']}/children")
        observed_gpu = []
        if children_path.exists():
            for child in children_path.read_text().split():
                process = Path("/proc") / child
                if "run_benchmarks.py" in (process / "cmdline").read_bytes().decode().replace("\0", " "):
                    environment = (process / "environ").read_bytes().split(b"\0")
                    observed_gpu.extend(value.decode().split("=", 1)[1] for value in environment if value.startswith(b"CUDA_VISIBLE_DEVICES="))
        check(observed_gpu == [str(shard)], f"shard{shard}: live process physical GPU visibility")
        files = sorted(directory.glob("*.jsonl"))[:3]
        check(len(files) == 3, f"shard{shard}: three completed files available")
        audit["shards"].append({"shard": shard, "physical_gpu_visible": observed_gpu,
            "receipt_sha256_at_read": hashlib.sha256(receipt_bytes).hexdigest(),
            "completed_pairs_at_receipt_read": receipt["completed_pairs"], "expected_pairs": receipt["expected_pairs"],
            "engine": receipt["engine"], "files_checked": [p.name for p in files]})
        for path in files:
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            check(len(rows) == 1, path.name + ": one pair per file")
            row = rows[0]
            identity, item = row["id"], row["item"]
            check(identity not in seen, identity + ": one pair across audited shards")
            seen.add(identity)
            check(row["status"] == "completed" and row["benchmark"] == "mmlu", identity + ": completed task")
            check(item == by_id[identity] and item["id"] == identity, identity + ": exact frozen item")
            index = int(path.stem)
            check(order[index] == identity, identity + ": execution order")
            check(row["arm_order"] == (["baseline", "evo"] if index % 2 == 0 else ["evo", "baseline"]), identity + ": paired arm order")
            check(item["continuations"] == [" A", " B", " C", " D"], identity + ": exact ordered MMLU letters")
            calibration = row["calibration"]
            tokens = encode_text(tokenizer, item["context"])
            check(calibration["context_sha256"] == text_hash(item["context"]), identity + ": calibration context hash")
            check(calibration["input_token_sha256"] == token_hash(tokens) and calibration["input_token_count"] == len(tokens), identity + ": unmodified common prompt tokens")
            check(set(calibration["residual_scales"]) == set(calibration["activation_offsets"]) == {"13", "14"}, identity + ": exact intervention layers")
            for layer, neuron, dose in protocol["intervention"]["zero_based_targets"]:
                scale = calibration["residual_scales"][str(layer)]
                expected = dose * scale / receipt["engine"]["column_norms"][str(layer)]
                check(math.isfinite(scale) and scale > 0 and math.isclose(expected, calibration["activation_offsets"][str(layer)], rel_tol=1e-12), identity + f": offset formula layer{layer}")
            check(set(row["outputs"]) == {"baseline", "evo"}, identity + ": exactly two conditions")
            for arm in ("baseline", "evo"):
                output = row["outputs"][arm]
                check(output["status"] == "completed" and len(output["choice_details"]) == len(output["choice_loglikelihoods"]) == 4, identity + f": {arm} four candidates")
                for candidate, (continuation, detail, total) in enumerate(zip(item["continuations"], output["choice_details"], output["choice_loglikelihoods"])):
                    context_ids, continuation_ids = encode_pair(tokenizer, item["context"], continuation)
                    check(detail["continuation_token_ids"] == continuation_ids, identity + f": {arm} candidate{candidate} ordered tokens")
                    check(detail["context_token_count"] == len(context_ids) and detail["input_token_sha256"] == token_hash(context_ids + continuation_ids[:-1]), identity + f": {arm} candidate{candidate} actual input hash")
                    check(math.isfinite(total) and total == detail["loglikelihood"] and len(detail["token_logprobs"]) == len(continuation_ids) and math.isclose(total, sum(detail["token_logprobs"]), rel_tol=1e-6, abs_tol=1e-6), identity + f": {arm} candidate{candidate} score field consistency")
            audit["records"].append({"id": identity, "shard": shard, "file": str(path.relative_to(ROOT)),
                "sha256": sha(path), "context_sha256": calibration["context_sha256"],
                "input_token_sha256": calibration["input_token_sha256"], "input_token_count": len(tokens),
                "candidate_count": 4, "conditions": ["baseline", "evo"]})
    check(not orders[0] & orders[1] and orders[0] | orders[1] == set(by_id), "shards are disjoint and cover full frozen task")
    check(engines[0] == engines[1], "both GPU engine versions, hardware type, weights, doses and numerical settings match")
    audit["status"] = "completed"
except Exception as error:
    audit["status"] = "failed"
    audit["failures"].append(str(error))
    audit["traceback"] = traceback.format_exc()
finally:
    audit["ended_utc"] = datetime.now(timezone.utc).isoformat()
    audit["limit"] = "Six early records only; no final completeness, outcome, hidden activation or capability-score claim. Model weights were not reloaded or rehashed in this audit; the verified frozen asset receipt chain was checked."
    print(json.dumps(audit, ensure_ascii=False, indent=2))
