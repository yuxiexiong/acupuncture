"""Pin the prepared experiment without importing a model runtime."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def frozen_files():
    local = ["contract.json", "CONTRACT.zh-CN.md", "RUNBOOK.zh-CN.md", "root_engine.py", "run_root.py", "freeze.py",
             "prepare_data.py", "metrics.py", "check_ready.py", "test_root_engine.py", "test_run_root.py", "test_data_metrics.py",
             "data/ability_dev.jsonl", "data/ability_confirm.jsonl", "data/ability_manifest.json", "data/excluded_ids.jsonl"]
    return [HERE / name for name in local] + [
        REPO / "docs/root-cause-localization-plan-v1.zh-CN.md",
        HERE.parent / "transfer-toy-v1-2026-10-26/transfer_engine.py",
        HERE.parent / "capability-damage-v2-2026-10-26/model_engine.py"]


def build(path=HERE / "freeze.json"):
    path = Path(path)
    if path.exists():
        raise ValueError("Do not overwrite a frozen contract; finish preparation before freezing")
    value = {"schema_version": 1, "status": "prepared_not_model_validated",
             "model_execution_authorized": False,
             "files": {str(p.relative_to(REPO)): sha(p) for p in frozen_files()}}
    write(path, value)
    return value


def verify(path=HERE / "freeze.json"):
    value = read(path)
    expected_names = {str(p.relative_to(REPO)) for p in frozen_files()}
    if value.get("schema_version") != 1 or value.get("status") != "prepared_not_model_validated":
        raise ValueError("Unsupported freeze schema/status")
    if set(value.get("files", {})) != expected_names:
        raise ValueError("Frozen file set is incomplete or contains undeclared files")
    if value.get("model_execution_authorized") is not False:
        raise ValueError("Preparation freeze is not a launch authorization")
    for name, expected in value["files"].items():
        if sha(REPO / name) != expected:
            raise ValueError(f"Frozen file changed: {name}")
    return value


def seal(function_dev, output):
    """Copy completed development hypotheses with their final receipt identity."""
    function_dev, output = Path(function_dev), Path(output)
    if output.exists():
        raise ValueError("Sealing never overwrites an explanation")
    receipt_path = function_dev / "receipt.json"
    receipt = read(receipt_path)
    if receipt.get("stage") != "function-dev" or receipt.get("status") != "completed":
        raise ValueError("Only completed functional development can be sealed")
    verify()
    if receipt["freeze_sha256"] != sha(HERE / "freeze.json"):
        raise ValueError("Development belongs to another frozen implementation")
    for name, expected in receipt["files"].items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or sha(function_dev / relative) != expected:
            raise ValueError("Functional development evidence changed")
    if "explanations.frozen.json" not in receipt["files"]:
        raise ValueError("Development did not produce frozen explanations")
    value = read(function_dev / "explanations.frozen.json")
    if value.get("status") != "frozen_before_confirmation":
        raise ValueError("Wrong explanation freeze status")
    value["function_dev_receipt_sha256"] = sha(receipt_path)
    with output.open("x") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    return value


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("build", "verify", "seal"))
    parser.add_argument("--function-dev", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.mode == "seal":
        if not args.function_dev or not args.output:
            parser.error("seal requires --function-dev and --output")
        result = seal(args.function_dev, args.output)
    else:
        result = build() if args.mode == "build" else verify()
    print(json.dumps({"status": result["status"], "file_count": len(result.get("files", {})),
                     "model_loaded": False}))
