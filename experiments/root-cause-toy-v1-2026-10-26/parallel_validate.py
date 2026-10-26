"""Two fixed validation shards; the original scientific implementation stays frozen."""
import argparse
from collections import Counter
from datetime import datetime
from pathlib import Path
import shutil
import time
import traceback

import run_root as r

CONDITIONS = {"clean", "AB_d1", "repair", "replay", "control_repair", "control_replay"}


def ref(path):
    return str(Path(path).resolve().relative_to(r.HERE.resolve()))


def auth(path, contract):
    value = r.check_launch(path, contract)
    if value.get("maximum_model_workers") != 2:
        raise ValueError("Explicit two-worker validation authorization is required")
    return value


def inputs(preflight, rank):
    r.verify(r.HERE / "freeze.json")
    base = r.sha(r.HERE / "freeze.json")
    r.completed_receipt(preflight, "preflight", base)
    r.completed_receipt(rank, "rank", base)
    contract = r.read(r.HERE / "contract.json")
    items = r.read_rows(r.HERE / "data/ability_dev.jsonl")
    if Counter(row["benchmark"] for row in items) != contract["dev_counts"] or len({x["id"] for x in items}) != len(items):
        raise ValueError("Development data identity/count changed")
    candidates = r.read(Path(rank).parent / "candidates.json")
    ids = [x["id"] for x in candidates]
    if not 1 <= len(ids) <= contract["candidate_budget"]["total"] or len(set(ids)) != len(ids):
        raise ValueError("Candidate budget or uniqueness violated")
    calibrations = {}
    for number, item in enumerate(items):
        row = r.read(Path(rank).parent / f"item-{number:03d}.json")
        if row["id"] != item["id"] or row["item_sha256"] != r.digest(item) or row["calibration"]["context_sha256"] != item["context_sha256"]:
            raise ValueError("Ranking calibration does not match the frozen question")
        calibrations[item["id"]] = row["calibration"]
    return contract, items, candidates, calibrations


def prepare(preflight, rank, authorization, output):
    preflight, rank, authorization, output = map(Path, (preflight, rank, authorization, output))
    contract, items, candidates, _ = inputs(preflight, rank)
    auth(authorization, contract)
    ids = [x["id"] for x in candidates]
    cut = (len(ids) + 1) // 2
    plan = {"schema_version": 1, "status": "prepared", "created_at": r.utc(),
            "base_freeze_sha256": r.sha(r.HERE / "freeze.json"),
            "extension_sha256": r.sha(__file__), "authorization": ref(authorization),
            "authorization_sha256": r.sha(authorization),
            "parents": {stage: {"path": ref(path), "sha256": r.sha(path)}
                        for stage, path in (("preflight", preflight), ("rank", rank))},
            "candidate_file_sha256": r.sha(rank.parent / "candidates.json"),
            "candidate_sha256": {x["id"]: r.digest(x) for x in candidates},
            "shards": [ids[:cut], ids[cut:]], "question_count": len(items),
            "execution_change": {"maximum_model_workers": [1, 2], "scientific_settings_changed": False}}
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(rank.parent / "candidates.json", output / "candidates.json")
    r.write(output / "execution.json", plan)
    return plan


def load_run(run):
    run = Path(run)
    plan = r.read(run / "execution.json")
    if plan.get("schema_version") != 1 or plan.get("status") != "prepared" or plan["extension_sha256"] != r.sha(__file__):
        raise ValueError("Parallel execution extension changed")
    if plan["base_freeze_sha256"] != r.sha(r.HERE / "freeze.json"):
        raise ValueError("Base freeze changed")
    paths = {}
    for stage in ("preflight", "rank"):
        relative = Path(plan["parents"][stage]["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Unsafe parent path")
        paths[stage] = r.HERE / relative
        if r.sha(paths[stage]) != plan["parents"][stage]["sha256"]:
            raise ValueError("Original parent receipt changed")
    contract, items, candidates, calibrations = inputs(paths["preflight"], paths["rank"])
    authorization = Path(plan["authorization"])
    if authorization.is_absolute() or ".." in authorization.parts:
        raise ValueError("Unsafe authorization path")
    if r.sha(r.HERE / authorization) != plan["authorization_sha256"]:
        raise ValueError("Authorization changed")
    auth(r.HERE / authorization, contract)
    ids = [x["id"] for x in candidates]
    cut = (len(ids) + 1) // 2
    if plan["shards"] != [ids[:cut], ids[cut:]] or plan["question_count"] != len(items):
        raise ValueError("Shard assignment changed")
    if (r.sha(run / "candidates.json") != plan["candidate_file_sha256"] or
            r.read(run / "candidates.json") != candidates or
            plan["candidate_sha256"] != {x["id"]: r.digest(x) for x in candidates}):
        raise ValueError("Frozen candidates changed")
    if plan["execution_change"] != {"maximum_model_workers": [1, 2], "scientific_settings_changed": False}:
        raise ValueError("Unexpected execution amendment")
    return plan, contract, items, candidates, calibrations


def worker(run, shard, device="cuda:0", engine_factory=None):
    run = Path(run)
    if shard not in (0, 1):
        raise ValueError("Only the two prepared shards are permitted")
    plan, contract, items, candidates, calibrations = load_run(run)
    output = run / f"shard-{shard}"
    output.mkdir(exist_ok=False)
    started = time.monotonic()
    receipt = {"stage": "validate-shard", "status": "running", "started_at": r.utc(),
               "execution_sha256": r.sha(run / "execution.json"),
               "base_freeze_sha256": plan["base_freeze_sha256"],
               "extension_sha256": plan["extension_sha256"], "shard": shard,
               "candidate_ids": plan["shards"][shard], "model_loaded": False}
    r.write(output / "receipt.json", receipt)
    engine = None
    try:
        if engine_factory is None:
            from root_engine import RootEngine
            engine_factory = RootEngine
        engine = engine_factory(contract["source"].get("model_path", "unused"), device=device,
                                threads=contract["torch_threads"])
        receipt["model_loaded"] = True
        source = contract["source"]
        if engine.metadata["dtype"] != source["dtype"] or engine.weight_hashes != source["target_weight_sha256"]:
            raise ValueError("Model precision or needle weights changed")
        if any(engine.metadata["versions"][p] != source[p + "_version"] for p in ("torch", "transformers")):
            raise ValueError("Unvalidated runtime version")
        receipt["model_metadata"] = engine.metadata
        arms = r.conditions(engine, contract)
        r.write(output / "conditions.json", {"arms": arms, "random_pairs": r.random_pairs(contract)})
        for candidate in candidates:
            if candidate["id"] not in receipt["candidate_ids"]:
                continue
            folder = output / candidate["id"]
            folder.mkdir()
            r.write(folder / "candidate.json", candidate)
            rows = []
            for number, item in enumerate(items):
                calibration = calibrations[item["id"]]
                values = r.patched_conditions(engine, item, calibration, arms, candidate)
                row = r.row_envelope(item, calibration, values)
                r.write(folder / f"ability-{number:03d}.json", row)
                rows.append(row)
                print(f"shard={shard} candidate={candidate['id']} completed={number+1}/{len(items)}", flush=True)
            r.write(folder / "ability-summary.json", r.summarize(rows, r.candidate_comparisons()))
        receipt["verification"] = engine.verify_unchanged()
        receipt["status"] = "completed"
    except Exception as exc:
        receipt["status"] = "failed"
        receipt["error"] = {"type": type(exc).__name__, "message": str(exc)}
        if hasattr(exc, "evidence"):
            r.write(output / "technical-failure-evidence.json", exc.evidence)
        (output / "failure.log").write_text(traceback.format_exc())
        raise
    finally:
        receipt["finished_at"] = r.utc()
        receipt["wall_seconds"] = time.monotonic() - started
        receipt["counts"] = engine.counts if engine is not None else {}
        receipt["files"] = r.evidence_manifest(output)
        r.write(output / "receipt.json", receipt)
    return receipt


def checked_shards(run, plan, items, candidates, calibrations):
    receipts = []
    for shard in (0, 1):
        folder = run / f"shard-{shard}"
        receipt = r.read(folder / "receipt.json")
        if (receipt.get("stage") != "validate-shard" or receipt.get("status") != "completed" or
                receipt.get("shard") != shard or receipt.get("candidate_ids") != plan["shards"][shard] or
                receipt.get("execution_sha256") != r.sha(run / "execution.json") or
                receipt.get("extension_sha256") != plan["extension_sha256"] or
                receipt.get("base_freeze_sha256") != plan["base_freeze_sha256"]):
            raise ValueError("Incomplete or mismatched validation shard")
        if receipt["files"] != r.evidence_manifest(folder):
            raise ValueError("Shard evidence changed or incomplete")
        if {p.name for p in folder.iterdir() if p.is_dir()} != set(plan["shards"][shard]):
            raise ValueError("Unexpected/missing candidate directory")
        for candidate in candidates:
            if candidate["id"] not in plan["shards"][shard]:
                continue
            path = folder / candidate["id"]
            if r.read(path / "candidate.json") != candidate:
                raise ValueError("Candidate identity changed")
            if {p.name for p in path.glob("ability-[0-9]*.json")} != {f"ability-{i:03d}.json" for i in range(len(items))}:
                raise ValueError("Candidate question coverage changed")
            for number, item in enumerate(items):
                row = r.read(path / f"ability-{number:03d}.json")
                if (row["id"] != item["id"] or row["benchmark"] != item["benchmark"] or
                        row["item_sha256"] != r.digest(item) or row["calibration"] != calibrations[item["id"]] or
                        set(row["conditions"]) != CONDITIONS):
                    raise ValueError("Question, calibration, or six-condition identity changed")
            if not (path / "ability-summary.json").is_file():
                raise ValueError("Missing candidate summary")
        receipts.append(receipt)
    if receipts[0]["model_metadata"] != receipts[1]["model_metadata"]:
        raise ValueError("The two model runtimes differ")
    return receipts


def merge(run):
    run = Path(run)
    if (run / "receipt.json").exists():
        raise FileExistsError("Never overwrite a merged receipt")
    plan, _, items, candidates, calibrations = load_run(run)
    receipts = checked_shards(run, plan, items, candidates, calibrations)
    for shard, ids in enumerate(plan["shards"]):
        for identity in ids:
            shutil.copytree(run / f"shard-{shard}" / identity, run / identity)
    receipt = {"stage": "validate-parallel", "status": "completed", "finished_at": r.utc(),
               "started_at": min(x["started_at"] for x in receipts),
               "execution_sha256": r.sha(run / "execution.json"),
               "base_freeze_sha256": plan["base_freeze_sha256"], "extension_sha256": plan["extension_sha256"],
               "parents": plan["parents"], "candidate_ids": [x["id"] for x in candidates],
               "shard_receipts": {f"shard-{i}/receipt.json": r.sha(run / f"shard-{i}/receipt.json") for i in (0, 1)},
               "model_metadata": receipts[0]["model_metadata"],
               "worker_seconds_sum": sum(x["wall_seconds"] for x in receipts),
               "counts": dict(sum((Counter(x["counts"]) for x in receipts), Counter()))}
    receipt["wall_seconds"] = (max(datetime.fromisoformat(x["finished_at"]) for x in receipts) -
                               min(datetime.fromisoformat(x["started_at"]) for x in receipts)).total_seconds()
    receipt["files"] = r.evidence_manifest(run)
    r.write(run / "receipt.json", receipt)
    return receipt


def verify_merged(run):
    run = Path(run)
    plan, _, items, candidates, calibrations = load_run(run)
    checked_shards(run, plan, items, candidates, calibrations)
    receipt = r.read(run / "receipt.json")
    if (receipt.get("stage") != "validate-parallel" or receipt.get("status") != "completed" or
            receipt.get("execution_sha256") != r.sha(run / "execution.json") or
            receipt.get("candidate_ids") != [x["id"] for x in candidates] or
            receipt.get("base_freeze_sha256") != plan["base_freeze_sha256"] or
            receipt.get("extension_sha256") != plan["extension_sha256"] or
            receipt.get("parents") != plan["parents"] or
            set(receipt.get("shard_receipts", {})) != {"shard-0/receipt.json", "shard-1/receipt.json"} or
            receipt.get("files") != r.evidence_manifest(run)):
        raise ValueError("Parallel aggregate identity or evidence changed")
    for path, expected in receipt["shard_receipts"].items():
        if r.sha(run / path) != expected:
            raise ValueError("Shard receipt changed after aggregation")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare")
    for name in ("preflight", "rank", "authorization", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    p = sub.add_parser("worker")
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--shard", type=int, choices=(0, 1), required=True)
    p.add_argument("--device", default="cuda:0")
    for name in ("merge", "verify"):
        p = sub.add_parser(name)
        p.add_argument("--run", type=Path, required=True)
    args = vars(parser.parse_args())
    command = args.pop("command")
    result = {"prepare": prepare, "worker": worker, "merge": merge, "verify": verify_merged}[command](**args)
    print(r.json.dumps({"status": result["status"], "stage": result.get("stage")}))


if __name__ == "__main__":
    main()
