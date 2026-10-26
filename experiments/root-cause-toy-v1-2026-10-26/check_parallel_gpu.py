"""Compare GPU 1 against two preserved GPU 0 records before parallel dispatch."""
import argparse
import time
from pathlib import Path

from run_root import (HERE, read, write, sha, verify, digest, read_rows, check_launch,
                      completed_receipt, conditions, patched_conditions, row_envelope, utc)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rank", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    verify()
    contract = read(HERE / "contract.json")
    auth = check_launch(args.authorization, contract)
    assert auth["maximum_model_workers"] == 2
    completed_receipt(args.rank, "rank", sha(HERE / "freeze.json"))
    candidate = read(args.rank.parent / "candidates.json")[0]
    items = read_rows(HERE / "data/ability_dev.jsonl")[:2]
    args.output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    receipt = {"status": "running", "stage": "parallel-gpu-check", "started_at": utc(),
               "base_freeze_sha256": sha(HERE / "freeze.json"),
               "check_code_sha256": sha(__file__), "authorization_sha256": sha(args.authorization),
               "rank_receipt_sha256": sha(args.rank), "comparisons": []}
    write(args.output / "receipt.json", receipt)
    try:
        from root_engine import RootEngine
        engine = RootEngine(contract["source"]["model_path"], device="cuda:0", threads=contract["torch_threads"])
        assert engine.weight_hashes == contract["source"]["target_weight_sha256"]
        assert engine.metadata["dtype"] == contract["source"]["dtype"]
        for package in ("torch", "transformers"):
            assert engine.metadata["versions"][package] == contract["source"][package + "_version"]
        arms = conditions(engine, contract)
        for number, item in enumerate(items):
            path = args.reference / candidate["id"] / f"ability-{number:03d}.json"
            expected = read(path)
            assert expected["item_sha256"] == digest(item)
            observed = row_envelope(item, expected["calibration"],
                patched_conditions(engine, item, expected["calibration"], arms, candidate))
            receipt["comparisons"].append({"item_id": item["id"], "reference": str(path),
                "reference_file_sha256": sha(path), "expected_scientific_sha256": digest(expected),
                "observed_scientific_sha256": digest(observed), "exact": observed == expected})
            assert observed == expected, "GPU 1 output differs from preserved GPU 0 record"
        receipt["model_metadata"] = engine.metadata
        receipt["verification"] = engine.verify_unchanged()
        receipt["status"] = "completed"
    except Exception as error:
        receipt.update(status="failed", error=str(error))
        raise
    finally:
        receipt.update(finished_at=utc(), wall_seconds=time.monotonic() - started)
        write(args.output / "receipt.json", receipt)
    print({"status": receipt["status"], "exact_comparisons": len(receipt["comparisons"]),
           "wall_seconds": receipt["wall_seconds"]})


if __name__ == "__main__":
    main()
