"""Freeze the random panel first; only then inventory reusable stopped-v2 pairs."""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import gzip
import io
import json
import math
import os
from pathlib import Path
import random

COUNTS = {"mmlu": 1000, "arc_challenge": 200, "gsm8k": 100, "humaneval": 100}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def read_rows(path):
    with Path(path).open() as stream:
        return [json.loads(line) for line in stream if line.strip()]


def write(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def utc():
    return datetime.now(timezone.utc).isoformat()


def sample_items(items, n, seed, benchmark):
    """Proportional largest-remainder allocation; sample from IDs, never outputs."""
    items = sorted(items, key=lambda row: row["id"])
    assert n <= len(items) and len({row["id"] for row in items}) == len(items)
    population, allocation = {}, {}
    if benchmark == "mmlu":
        groups = defaultdict(list)
        for item in items:
            groups[item["subject"]].append(item)
        population = {subject: len(rows) for subject, rows in sorted(groups.items())}
        allocation = {subject: n * size // len(items) for subject, size in population.items()}
        ranked = sorted(population, key=lambda subject: (-(n * population[subject] % len(items)), subject))
        for subject in ranked[:n - sum(allocation.values())]:
            allocation[subject] += 1
        assert all(allocation.values())
        selected = []
        for subject, size in allocation.items():
            selected.extend(random.Random(f"{seed}:{benchmark}:{subject}").sample(groups[subject], size))
    else:
        selected = random.Random(f"{seed}:{benchmark}:selection").sample(items, n)
    random.Random(f"{seed}:{benchmark}:execution").shuffle(selected)
    assert len(selected) == n
    return selected, population, allocation


def verify_source(source):
    protocol = read(source / "protocol.json")
    manifest = read(source / "task_manifest.json")
    assert sha(source / "task_manifest.json") == protocol["task_manifest_sha256"]
    for name, digest in protocol["source_sha256"].items():
        assert sha(source / name) == digest, f"Changed v2 source: {name}"
    return protocol, manifest


def select_panel(source, root, seed):
    assert not (root / "panel_manifest.json").exists()
    protocol, source_manifest = verify_source(source)
    root.mkdir(parents=True, exist_ok=True)
    (root / "items").mkdir(exist_ok=True)
    assert not any((root / "items").iterdir()), "Preserve an existing selection attempt"
    manifest = {"status": "frozen_before_inference", "selection_phase": "before_reuse_inspection", "created_utc": utc(), "seed": seed,
        "counts": COUNTS, "source_root": os.path.relpath(source, root),
        "harness_commit": source_manifest["harness_commit"],
        "source_protocol_sha256": sha(source / "protocol.json"),
        "source_task_manifest_sha256": sha(source / "task_manifest.json"),
        "selection": "Sorted IDs, fixed per-task/per-subject RNG seeds; MMLU proportional largest remainders; no output, target or length used",
        "execution_order": "Independent seeded shuffle, then alternate items across two shards; no length sorting",
        "files": {}, "selected_ids": {}}
    for task, count in COUNTS.items():
        specification = source_manifest["files"][task]
        path = source / specification["file"]
        raw = path.read_bytes() if path.exists() else gzip.decompress(Path(str(path) + ".gz").read_bytes())
        assert hashlib.sha256(raw).hexdigest() == specification["sha256"]
        items = [json.loads(line) for line in io.StringIO(raw.decode()) if line.strip()]
        assert len(items) == specification["count"] == protocol["counts"][task]
        selected, population, allocation = sample_items(items, count, seed, task)
        output = root / "items" / f"{task}.jsonl"
        output.write_text("".join(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n" for item in selected))
        manifest["files"][task] = {"file": f"items/{task}.jsonl", "count": count, "sha256": sha(output)}
        manifest["selected_ids"][task] = [row["id"] for row in selected]
        if task == "mmlu":
            assert len(population) == 57 and sum(population.values()) == 14042
            manifest["mmlu_population_subject_counts"] = population
            manifest["mmlu_sample_subject_counts"] = allocation
            manifest["mmlu_population_total"] = 14042
            manifest["mmlu_aggregation"] = "sum_subject(full_subject_n / 14042 * sample_subject_accuracy)"
    write(root / "panel_manifest.json", manifest)
    draft = {key: protocol[key] for key in ("model", "arms", "intervention", "generation", "max_new_tokens", "scoring")}
    draft.update(status="draft_before_source_freeze", created_utc=utc(), counts=COUNTS,
        batch_sizes={task: 1 for task in COUNTS}, shard_count=2, source_root=manifest["source_root"],
        source_protocol_sha256=manifest["source_protocol_sha256"],
        panel_manifest_sha256=sha(root / "panel_manifest.json"), reuse_manifest_sha256=None, source_sha256={},
        task_orders={"0": ["gsm8k", "humaneval", "mmlu", "arc_challenge"],
                     "1": ["humaneval", "gsm8k", "arc_challenge", "mmlu"]},
        preflight=[{**entry, "file": os.path.relpath(source / entry["file"], root)} for entry in protocol["preflight"]],
        inference="Unchanged v2 Engine; BF16/eager/batch1; original per-item calibration, stops and generation budgets",
        reuse="Only byte-preserved complete pairs selected independently before reuse inspection",
        timing="New inference excludes reused pairs; fixed sample counts are not cut by an ETA or deadline")
    draft["scoring"] = {**draft["scoring"], "mmlu_aggregation": manifest["mmlu_aggregation"]}
    write(root / "protocol.json", draft)
    return manifest


def validate_pair(row, item, metadata):
    assert row["id"] == item["id"] and row["item"] == item
    assert row["status"] == "completed" and row["benchmark"] == item["benchmark"]
    assert set(row["outputs"]) == {"baseline", "evo"}
    assert set(row["arm_order"]) == {"baseline", "evo"}
    calibration = row["calibration"]
    assert calibration["context_sha256"] == item["context_sha256"] == hashlib.sha256(item["context"].encode()).hexdigest()
    assert calibration["input_token_count"] >= 2
    assert set(calibration["residual_scales"]) == set(calibration["activation_offsets"]) == {"13", "14"}
    for layer, _, dose in metadata["targets"]:
        scale = calibration["residual_scales"][str(layer)]
        assert math.isfinite(scale) and scale > 0
        assert math.isclose(calibration["activation_offsets"][str(layer)], dose * scale / metadata["column_norms"][str(layer)], rel_tol=1e-12)
    for arm in ("baseline", "evo"):
        output = row["outputs"][arm]
        assert output["status"] == "completed"
        if item["request_type"] == "loglikelihood":
            assert len(output["choice_details"]) == len(output["choice_loglikelihoods"]) == len(item["continuations"])
            for detail, value in zip(output["choice_details"], output["choice_loglikelihoods"]):
                assert math.isfinite(value) and value == detail["loglikelihood"]
                assert len(detail["token_logprobs"]) == len(detail["continuation_token_ids"])
        else:
            assert output["max_new_tokens"] == item["gen_kwargs"]["max_gen_toks"]
            assert 0 < output["generated_token_count"] == len(output["token_ids"]) <= output["max_new_tokens"]
            assert output["end_reason"] in ("task_stop", "eos_token", "length_limit")
            assert isinstance(output["raw_text"], str) and isinstance(output["answer_text"], str)


def freeze_reuse(source, root, stop_receipt):
    assert not (root / "reuse_manifest.json").exists()
    protocol, source_manifest = verify_source(source)
    panel = read(root / "panel_manifest.json")
    assert panel["source_protocol_sha256"] == sha(source / "protocol.json")
    stop = read(stop_receipt)
    assert stop["status"] == "stopped_by_user" and stop["remaining_live_processes"] == []
    assert stop["protocol_sha256"] == panel["source_protocol_sha256"]
    entries, receipts = {}, {}
    for task, specification in panel["files"].items():
        assert sha(root / specification["file"]) == specification["sha256"]
        selected = {row["id"]: row for row in read_rows(root / specification["file"])}
        for directory in sorted((source / "outputs").glob(f"{task}-shard[01]-r01")):
            receipt_path = directory / "receipt.json"
            receipt = read(receipt_path)
            assert receipt["protocol_sha256"] == panel["source_protocol_sha256"]
            assert receipt["source_sha256"] == protocol["source_sha256"]
            assert receipt["items_sha256"] == source_manifest["files"][task]["sha256"]
            assert receipt["engine"]["batch_size"] == 1
            receipt_name = str(receipt_path.relative_to(source))
            receipts[receipt_name] = {"sha256": sha(receipt_path), "engine": receipt["engine"], "assets": receipt["assets"],
                "original_status": receipt["status"], "final_immutability_check_present": "target_weight_sha256_after" in receipt}
            for path in sorted(directory.glob("*.jsonl")):
                rows = read_rows(path)
                assert len(rows) == 1
                row = rows[0]
                if row["id"] not in selected:
                    continue
                validate_pair(row, selected[row["id"]], receipt["engine"])
                assert row["id"] not in entries, "Duplicate old complete pair"
                entries[row["id"]] = {"task": task, "source_file": str(path.relative_to(source)), "sha256": sha(path),
                    "source_receipt_file": receipt_name, "source_receipt_sha256": sha(receipt_path)}
    manifest = {"status": "reuse_frozen_after_user_stop", "created_utc": utc(),
        "source_root": panel["source_root"], "source_protocol_sha256": panel["source_protocol_sha256"],
        "panel_manifest_sha256": sha(root / "panel_manifest.json"),
        "stop_receipt": {"file": os.path.relpath(stop_receipt, root), "sha256": sha(stop_receipt)},
        "counts": {task: sum(row["task"] == task for row in entries.values()) for task in COUNTS},
        "entries": entries, "source_receipts": receipts,
        "limitation": "Interrupted v2 has no final whole-run immutability attestation. Reuse checks completed pairs and frozen source/assets; new Engine metadata/target hashes are compared before copying, without claiming the old run completed."}
    write(root / "reuse_manifest.json", manifest)
    draft = read(root / "protocol.json")
    assert draft["status"] == "draft_before_source_freeze"
    draft["reuse_manifest_sha256"] = sha(root / "reuse_manifest.json")
    write(root / "protocol.json", draft)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("select", "reuse"), required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--seed", type=int, default=20261026)
    parser.add_argument("--stop-receipt", type=Path)
    args = parser.parse_args()
    if args.mode == "select":
        result = select_panel(args.source_root.resolve(), args.output_root.resolve(), args.seed)
    else:
        assert args.stop_receipt
        result = freeze_reuse(args.source_root.resolve(), args.output_root.resolve(), args.stop_receipt.resolve())
    print(json.dumps({"status": result["status"], "counts": result["counts"]}, ensure_ascii=False))
