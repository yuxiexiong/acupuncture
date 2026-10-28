"""Run only the stage's frozen conditions; export all records with blank blind labels."""
import argparse
import json
from pathlib import Path
import time
import traceback

from common import (ROOT, DATA, PROJECT, SOURCE_CALIBRATIONS, conditions, read, rows,
    write, immutable, sha, utc, source_hashes, verify_freeze, require_stage)


def run(args):
    verify_freeze(args.freeze)
    run_root = args.output.parent.parent
    require_stage(args.stage, run_root, args.conditions, args.freeze)
    destination = args.output / f"shard{args.shard_index}"
    destination.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    names = conditions(args.stage)
    rec = {"status": "running", "stage": args.stage, "conditions": names,
        "started_utc": utc(), "model": str(args.model), "shard_index": args.shard_index,
        "conditions_sha256": sha(args.conditions), "freeze_sha256": sha(args.freeze),
        "source_sha256": source_hashes(), "completed_behavior": 0, "completed_ability": 0,
        "expected_per_split": 32 * len(names), "records_sha256": {}}
    write(destination / "receipt.json", rec)
    try:
        from engine import CrossFamilyEngine
        engine = CrossFamilyEngine(args.model, bundle=args.conditions)
        rec["engine"] = engine.metadata
        source_receipt = read(SOURCE_CALIBRATIONS / f"shard{args.shard_index}/receipt.json")
        assert source_receipt["status"] == "completed"
        assert source_receipt["data_sha256"] == {name: sha(DATA / f"{name}.jsonl") for name in ("confirm", "ability_diag")}
        for split, filename in (("behavior", "confirm"), ("ability", "ability_diag")):
            items = rows(DATA / (filename + ".jsonl"))
            assert len(items) == 64
            for index in range(args.shard_index, 64, 2):
                item = items[index]
                context = engine.tokenizer.apply_chat_template([{"role": "user", "content": item["prompt"]}],
                    tokenize=False, add_generation_prompt=True, enable_thinking=False) if split == "behavior" else item["context"]
                calibration = engine.calibrate([context])[0]
                calibration["item_id"] = item["id"]
                source_path = SOURCE_CALIBRATIONS / f"shard{args.shard_index}/calibrations/{split}-{index:03d}.json"
                source = read(source_path)
                assert source["item_id"] == item["id"]
                calibration.update(source_residual_scales=source["residual_scales"],
                    source_calibration_file_sha256=sha(source_path), source_calibration_context_sha256=source["context_sha256"])
                write(destination / f"calibrations/{split}-{index:03d}.json", calibration)
                # Rotate within this stage only; never evaluate sparse arms before the gate.
                offset = index % len(names)
                for condition in names[offset:] + names[:offset]:
                    begin = time.monotonic()
                    rec.update(current_split=split, current_item=item["id"], current_condition=condition)
                    write(destination / "receipt.json", rec)
                    if split == "behavior":
                        result = engine.generate([context], condition, [calibration], 512, [])[0]
                    else:
                        details = engine.score([context] * len(item["continuations"]), item["continuations"],
                            condition, [calibration] * len(item["continuations"]))
                        result = {"choice_loglikelihoods": [d["loglikelihood"] for d in details], "choice_details": details}
                    record = {"status": "completed", "model_role": "target", "item": item,
                        "condition": condition, "context": context, "calibration": calibration,
                        "output": result, "elapsed_seconds": time.monotonic() - begin, "ended_utc": utc()}
                    path = destination / f"records/{split}/{index:03d}-{condition}.jsonl"
                    immutable(path, record)
                    rec["records_sha256"][str(path.relative_to(destination))] = sha(path)
                    rec["completed_" + split] += 1
                    rec["elapsed_seconds"] = time.monotonic() - started
                    write(destination / "receipt.json", rec)
                    print(json.dumps({"stage": args.stage, "split": split, "completed": rec["completed_" + split],
                        "expected": rec["expected_per_split"], "last_seconds": record["elapsed_seconds"]}), flush=True)
        assert rec["completed_behavior"] == rec["completed_ability"] == rec["expected_per_split"]
        verify_freeze(args.freeze)
        rec.update(status="completed", **engine.verify_unchanged())
    except Exception as error:
        rec.update(status="failed", error=str(error), traceback=traceback.format_exc())
        raise
    finally:
        rec.update(ended_utc=utc(), elapsed_seconds=time.monotonic() - started)
        write(destination / "receipt.json", rec)


def export(args):
    verify_freeze(args.freeze)
    run_root = args.output.parent.parent
    require_stage(args.stage, run_root, run_root / "mapping/bundle.pt", args.freeze)
    records = {"behavior": [], "ability": []}
    receipts = []
    for stage in range(1, args.stage + 1):
        for shard in (0, 1):
            directory = run_root / f"stage{stage}/toy/shard{shard}"
            receipt = read(directory / "receipt.json")
            assert receipt["status"] == "completed" and receipt["hooks_removed"]
            assert receipt["stage"] == stage and receipt["shard_index"] == shard
            assert receipt["freeze_sha256"] == sha(args.freeze)
            assert receipt["conditions_sha256"] == sha(run_root / "mapping/bundle.pt")
            assert receipt["target_weight_sha256_after"] == receipt["engine"]["target_weight_sha256_before"]
            receipts.append(receipt)
            for split, filename in (("behavior", "confirm"), ("ability", "ability_diag")):
                items = rows(DATA / (filename + ".jsonl"))
                paths = sorted((directory / "records" / split).glob("*.jsonl"))
                assert len(paths) == receipt["completed_" + split] == 32 * len(conditions(stage))
                expected = {(items[i]["id"], c) for i in range(shard, 64, 2) for c in conditions(stage)}
                observed = set()
                for path in paths:
                    assert sha(path) == receipt["records_sha256"][str(path.relative_to(directory))]
                    content = rows(path); assert len(content) == 1
                    row = content[0]
                    key = (row["item"]["id"], row["condition"])
                    assert key not in observed and key in expected
                    assert row["item"] == next(i for i in items if i["id"] == key[0])
                    observed.add(key)
                    if split == "behavior":
                        result = row["output"]
                        assert len(result["token_ids"]) == result["generated_token_count"] <= 512
                        assert result["max_new_tokens"] == 512
                        if result["end_reason"] == "eos_token":
                            assert str(result["token_ids"][-1]) in receipt["engine"]["effective_stop_tokens"]
                        else:
                            assert result["end_reason"] == "length_limit" and len(result["token_ids"]) == 512
                    records[split].append({**row, "source_file": str(path), "source_file_sha256": sha(path)})
                assert observed == expected
    assert all(r["engine"]["target_weight_sha256_before"] == receipts[0]["engine"]["target_weight_sha256_before"] for r in receipts)
    destination = args.output.parent / "export-r01"
    destination.mkdir(exist_ok=False)
    from export_results import blind_pack, diagnostic_scores
    import export_results as legacy_export
    legacy_export.TARGET_CONDITIONS = conditions(1) + (conditions(2) if args.stage == 2 else [])
    # The scoring implementation and blind label rubric are unchanged.
    scored, summary = diagnostic_scores(records["ability"], PROJECT)
    write(destination / "diagnostic.summary.json", summary)
    for label, content in (("behavior", records["behavior"]), ("ability", records["ability"]), ("diagnostic.scores", scored)):
        (destination / (label + ".jsonl")).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in content))
    for reviewer, seed in (("A", 20261026), ("B", 20261027)):
        packet, key = blind_pack(records["behavior"], reviewer, "Llama-3.1-8B-Instruct", seed)
        for name, value in ((f"blind-{reviewer}", packet), (f"PRIVATE-key-{reviewer}", key)):
            (destination / (name + ".jsonl")).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in value))
    write(destination / "receipt.json", {"status": "completed", "human_labels": "pending",
        "stage": args.stage, "files": {p.name: sha(p) for p in destination.iterdir() if p.is_file()},
        "freeze_sha256": sha(args.freeze), "ended_utc": utc()})


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("run", "export"))
    p.add_argument("--stage", type=int, choices=(1, 2), required=True)
    p.add_argument("--output", type=Path, required=True); p.add_argument("--freeze", required=True)
    p.add_argument("--model", type=Path); p.add_argument("--conditions", type=Path)
    p.add_argument("--shard-index", type=int, choices=(0, 1))
    args = p.parse_args()
    if args.mode == "run":
        assert args.model and args.conditions and args.shard_index is not None
        run(args)
    else:
        export(args)
