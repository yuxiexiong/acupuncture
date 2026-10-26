"""Read-only GPU/environment/asset inventory. Never loads a model or CUDA tensors."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import time


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def command(*args):
    result = subprocess.run(args, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    start = time.monotonic()
    contract = json.loads((ROOT / "contract.json").read_text())
    source = contract["source"]
    model = Path(source["model_path"])
    config = json.loads((model / "config.json").read_text())["text_config"]
    checks = {key: config[key] == source[key]
              for key in ("hidden_size", "intermediate_size", "num_hidden_layers")}
    distribution_versions = {name: importlib.metadata.version(name) for name in ("torch", "transformers")}
    import torch
    versions = {**distribution_versions, "torch": torch.__version__}
    for name, version in versions.items():
        checks[name + "_version"] = version == source[name + "_version"]
    # Reuse the minimal identity evidence in the approved preparation package.
    # Do not require or transmit unrelated historical environment receipts.
    manifest_path = ROOT / "readiness/receipt.json"
    weight_entries = json.loads(manifest_path.read_text())["remote_read_only_verification"]["weight_sha256_verified"]
    assets = []
    for name, expected in weight_entries.items():
        path = model / name
        actual = sha(path)
        size = path.stat().st_size
        assets.append({"path": str(path), "bytes": size, "sha256": actual,
                       "expected_sha256": expected, "matches": actual == expected})
    checks["weight_files"] = bool(assets) and all(row["matches"] for row in assets)
    expected_tokenizer = json.loads((ROOT / "readiness/tokenizer-alignment.json").read_text())["tokenizer_hashes"]
    tokenizer_hashes = {name: sha(model / name) for name in expected_tokenizer}
    checks["tokenizer_files"] = tokenizer_hashes == expected_tokenizer
    installed_source = Path(importlib.metadata.distribution("transformers").locate_file(
        "transformers/models/qwen3_5/modeling_qwen3_5.py"))
    # Tokenization is CPU-only and reads no model weights into a model object.
    from transformers import AutoTokenizer
    from prepare_data import functional_rows
    from root_engine import encode_pair
    tokenizer = AutoTokenizer.from_pretrained(str(model), local_files_only=True, trust_remote_code=False)
    alignment = {}
    for family in contract["functional"]["families"]:
        mismatches = []
        rows = functional_rows(family)
        for row in rows:
            for continuation in row["continuations"]:
                recipient_ids, recipient_answer = encode_pair(tokenizer, row["context"], continuation)
                donor_ids, donor_answer = encode_pair(tokenizer, row["donor_context"], continuation)
                if len(recipient_ids) != len(donor_ids) or recipient_answer != donor_answer:
                    mismatches.append(row["id"])
        alignment[family] = {"items": len(rows), "mismatches": sorted(set(mismatches))}
    checks["functional_token_alignment"] = all(not row["mismatches"] for row in alignment.values())
    gpu_text = command("nvidia-smi", "--query-gpu=index,name,memory.total,memory.used,utilization.gpu", "--format=csv,noheader,nounits")
    processes = command("nvidia-smi", "--query-compute-apps=gpu_uuid,pid,process_name,used_memory", "--format=csv,noheader,nounits")
    gpu_rows = []
    for line in gpu_text.splitlines():
        index, name, total, used, utilization = [part.strip() for part in line.split(",")]
        gpu_rows.append({"index": int(index), "name": name, "total_mib": int(total),
                         "used_mib": int(used), "utilization_percent": int(utilization)})
    # This is availability at the timestamp, not a reservation or promise about a later run.
    available = [row["index"] for row in gpu_rows if row["used_mib"] < 1024 and row["utilization_percent"] == 0]
    receipt = {"status": "completed" if all(checks.values()) else "failed",
               "checked_at_utc": datetime.now(timezone.utc).isoformat(),
               "model_executed": False, "cuda_tensor_created": False,
               "model_preflight_passed": False, "launch_authorized": False,
               "checks": checks, "versions": versions, "distribution_versions": distribution_versions, "assets": assets,
               "manifest_sha256": sha(manifest_path), "tokenizer_sha256": tokenizer_hashes,
               "config_sha256": sha(model / "config.json"),
               "layer_types": config["layer_types"],
               "installed_model_source_sha256": sha(installed_source),
               "functional_token_alignment": alignment,
               "gpus": gpu_rows, "compute_processes": processes.splitlines() if processes else [],
               "available_gpu_indices_at_snapshot": available,
               "elapsed_seconds": time.monotonic() - start}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "checks": checks, "available_gpus": available,
                      "model_executed": False, "output": str(args.output)}))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
