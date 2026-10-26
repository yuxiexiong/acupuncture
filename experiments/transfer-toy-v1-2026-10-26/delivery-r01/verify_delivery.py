"""CPU-only delivery audit. Reuse frozen verifiers; never load a model or rescore answers."""
import hashlib
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
EXPERIMENT = HERE.parent
PROJECT = EXPERIMENT.parent.parent
RUN = EXPERIMENT / "runs/transfer-9b-2b-r01"
sys.path.insert(0, str(EXPERIMENT))
from run_io import read, rows
from export_results import verified_toy, LABELS
from export_results_parallel import verified_target, verify_benchmark
import finish_benchmark_parallel


def local_path(path):
    path = Path(path)
    remote = Path("/workspace/acupuncture")
    return PROJECT / path.relative_to(remote) if path.is_relative_to(remote) else path


def sha(path):
    digest = hashlib.sha256()
    with local_path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    manifest = read(HERE / "remote-manifest.json")
    expected = manifest["files"]
    actual = {str(p.relative_to(RUN)) for p in RUN.rglob("*") if p.is_file()}
    assert actual == set(expected), ("File set mismatch", sorted(actual ^ set(expected)))
    for name, entry in expected.items():
        path = RUN / name
        assert path.stat().st_size == entry["bytes"] and sha(path) == entry["sha256"], name
    frozen_counts = {}
    for name in ("freeze.json", "freeze_parallel.json"):
        frozen = read(EXPERIMENT / name)
        for relative, digest in frozen["files"].items():
            assert sha(EXPERIMENT / relative) == digest, relative
        frozen_counts[name] = len(frozen["files"])
    # Historical receipts keep remote absolute paths. Resolve only their location, not contents.
    finish_benchmark_parallel.sha = sha
    data = EXPERIMENT / "data"
    inputs = {}
    source = verified_toy(RUN / "source", "source", data, inputs)
    assert len(source["behavior"]) == 192
    models = {}
    token_manifest = []
    for model in ("target9b", "target2b"):
        root = RUN / model
        target = verified_target(root / "toy", data, inputs, 6)
        benchmark = verify_benchmark(root / "benchmark", inputs, 6)
        exported = root / "export-r01"
        receipt = read(exported / "receipt.json")
        assert receipt["status"] == "machine_completed_blind_review_pending"
        assert receipt["behavior_semantic_analysis_performed"] is False
        for name, digest in receipt["artifacts_sha256"].items():
            assert sha(exported / name) == digest, name
        for path, digest in receipt["input_sha256"].items():
            assert sha(path) == digest, path
        assert benchmark == read(exported / "benchmark.summary.json")
        toy_identity = read(root / "toy/shard0/receipt.json")
        bench_identity = read(root / "benchmark/shard-0/receipt.json")
        assert toy_identity["engine"] == bench_identity["engine"]
        assert toy_identity["conditions_sha256"] == bench_identity["conditions_sha256"]
        assert toy_identity["conditions_sha256"] == sha(bench_identity["conditions"])
        for split, filename in (("behavior", "confirm"), ("ability", "ability_diag")):
            source_calibrations = {}
            for index, item in enumerate(rows(data / f"{filename}.jsonl")):
                path = RUN / "source" / f"shard{index % 2}" / "calibrations" / f"{split}-{index:03d}.json"
                source_calibrations[item["id"]] = (read(path), sha(path))
            for row in target[split]:
                calibration = row["calibration"]
                original, digest = source_calibrations[row["item"]["id"]]
                assert calibration["source_calibration_file_sha256"] == digest
                assert calibration["source_residual_scales"] == original["residual_scales"]
                assert calibration["source_calibration_context_sha256"] == original["context_sha256"]
        for reviewer in ("A", "B"):
            packet = rows(exported / f"blind_{reviewer}/ratings.blank.jsonl")
            assert len(packet) == len({r["anonymous_id"] for r in packet}) == 1408
            for row in packet:
                assert set(row) == {"anonymous_id", "question", "answer", "labels", "evidence", "uncertain_reason"}
                assert row["labels"] == dict.fromkeys(LABELS)
                assert row["evidence"] is None and row["uncertain_reason"] is None
        human = read(root / "benchmark/finish-r01/humaneval-execution.jsonl.receipt.json")
        assert human["status"] == "completed" and human["controls_passed"] and human["count"] == 200
        assert human["output_sha256"] == sha(root / "benchmark/finish-r01/humaneval-execution.jsonl")
        for path in sorted((root / "benchmark").glob("shard-*/*/*.jsonl")):
            row = rows(path)[0]
            for arm, output in row["outputs"].items():
                if "token_ids" in output:
                    tokens = output["token_ids"]
                    assert len(tokens) == output["generated_token_count"] <= output["max_new_tokens"]
                    token_manifest.append({"file": str(path.relative_to(RUN)), "arm": arm,
                        "generated_token_count": len(tokens),
                        "generated_token_sha256": hashlib.sha256(json.dumps(tokens, separators=(",", ":")).encode()).hexdigest()})
        models[model] = {"behavior_records": len(target["behavior"]), "diagnostic_records": len(target["ability"]),
            "benchmark_pairs": 1400, "technical_failures": benchmark["technical_failures"],
            "blind_records_per_reviewer": 1408, "labels_filled": 0, "human_sandbox_controls_passed": True}
    token_file = HERE / "benchmark-token-hashes.jsonl"
    token_file.write_text("".join(json.dumps(row, separators=(",", ":")) + "\n" for row in token_manifest))
    result = {"status": "passed", "verified_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": RUN.name, "file_count": len(expected), "bytes": sum(r["bytes"] for r in expected.values()),
        "remote_manifest_sha256": sha(HERE / "remote-manifest.json"), "verifier_sha256": sha(__file__),
        "freeze_file_counts": frozen_counts, "source_behavior_records": 192, "models": models,
        "benchmark_generated_outputs": len(token_manifest), "benchmark_token_manifest_sha256": sha(token_file),
        "semantic_rating_performed": False, "new_inference_performed": False,
        "verification": "Exact remote file-set/size/SHA256, frozen source and panels, original partition/record/token verifiers, export input and artifact hashes, sandbox receipt and blank anonymous forms."}
    (HERE / "verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
