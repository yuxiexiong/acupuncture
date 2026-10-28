"""Standalone CPU-only scoring readiness; no experimental model loads."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

os.environ.update(CUDA_VISIBLE_DEVICES="", HF_HUB_OFFLINE="1", HF_DATASETS_OFFLINE="1",
                  TRANSFORMERS_OFFLINE="1", PYTHONDONTWRITEBYTECODE="1", OMP_NUM_THREADS="4")
OUT = Path(__file__).resolve().parent
PROJECT = OUT.parents[2]
LEGACY = PROJECT / "experiments/transfer-toy-v1-2026-10-26"
sys.path.insert(0, str(LEGACY))
from run_benchmark import V3, frozen_panel, load_v3, read, sha, utc, write

os.environ["HF_HOME"] = str(PROJECT / ".cache/hf")
receipt_path = OUT / "receipt.json"
assert not receipt_path.exists(), "Preserve any previous attempt"
started = time.monotonic()
receipt = {"status": "running", "started_utc": utc(), "model_weights_loaded": False,
    "gpu_work_started": False, "offline": True, "tasks": [],
    "source_sha256": {str(path): sha(path) for path in
        (Path(__file__), V3 / "score_results.py", V3 / "humaneval_sandbox.py", V3 / "humaneval_worker.py")}}
write(receipt_path, receipt)
try:
    import torch
    assert not torch.cuda.is_available() and not torch.cuda.is_initialized()
    command = [sys.executable, "-B", str(V3 / "humaneval_sandbox.py"), "--self-test",
        "--bwrap", str(PROJECT / ".runtime/bubblewrap/root/usr/bin/bwrap"),
        "--official", str(PROJECT / ".runtime/human-eval"), "--python-prefix", "/workspace/miniconda/envs/amic-q3",
        "--output", str(OUT / "sandbox-controls.jsonl")]
    begin = time.monotonic()
    result = subprocess.run(command, capture_output=True, text=True, timeout=90, cwd=PROJECT)
    (OUT / "sandbox.log").write_text(result.stdout + result.stderr)
    receipt["sandbox"] = {"command": command, "exit_code": result.returncode,
                          "wall_seconds": time.monotonic() - begin}
    write(receipt_path, receipt)
    assert result.returncode == 0, "HumanEval sandbox self-test failed"
    sandbox = read(OUT / "sandbox-controls.jsonl.receipt.json")
    assert sandbox["status"] == "completed" and sandbox["controls_passed"] and sandbox["self_test"]
    receipt["sandbox"]["receipt_sha256"] = sha(OUT / "sandbox-controls.jsonl.receipt.json")
    scorer = load_v3("score_results").OfficialScorer(PROJECT / ".runtime/lm-evaluation-harness", PROJECT / ".cache/hf/datasets")
    _, _, items = frozen_panel()
    required = sorted({row["task_name"] for task, group in items.items() if task != "humaneval" for row in group})
    receipt["required_tasks"] = required
    for name in required:
        begin = time.monotonic()
        task = scorer.task(name)
        receipt["tasks"].append({"name": name, "status": "loaded_offline", "class": type(task).__name__,
                                 "wall_seconds": time.monotonic() - begin})
        write(receipt_path, receipt)
        print(json.dumps(receipt["tasks"][-1]), flush=True)
    assert not torch.cuda.is_initialized()
    assert len(receipt["tasks"]) == len(required)
    receipt.update(status="completed", official_scorer=type(scorer).__name__,
                   completed_task_count=len(required), cuda_initialized=False)
except Exception as error:
    receipt.update(status="failed", error=str(error), traceback=traceback.format_exc())
    raise
finally:
    receipt.update(ended_utc=utc(), wall_seconds=time.monotonic() - started,
        artifacts_sha256={path.name: sha(path) for path in OUT.iterdir() if path.is_file()
                          and path.name not in ("receipt.json", "run.log")})
    write(receipt_path, receipt)
    print(json.dumps({"status": receipt["status"], "wall_seconds": receipt["wall_seconds"]}), flush=True)
