"""CPU-only readiness and input freeze; never loads experiment weights or starts GPUs."""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from common import ROOT, PROJECT, LEGACY, DATA, SOURCE_CALIBRATIONS, read, rows, sha, write, utc, source_hashes


def verify_assets(path, manifest):
    path = Path(path).resolve()
    assert path.is_dir(), f"Missing exact asset: {path}"
    assert not (path / "adapter_config.json").exists(), "Adapter checkpoint is outside this protocol"
    files = {v["rfilename"]: v for v in manifest["files"]}
    required = {n for n in files if n.endswith((".safetensors", ".json", ".jinja", ".txt"))}
    assert {"config.json", "tokenizer.json", "tokenizer_config.json", "model.safetensors.index.json"} <= required
    observed = {}
    for name in sorted(required):
        entry, item = files[name], path / name
        assert item.is_file() and item.stat().st_size == entry["size"], f"Missing/incomplete asset: {item}"
        digest = hashlib.sha256()
        blob = hashlib.sha1(f"blob {entry['size']}\0".encode())
        with item.open("rb") as handle:
            for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
                digest.update(chunk)
                if "lfs" not in entry:
                    blob.update(chunk)
        if "lfs" in entry:
            assert digest.hexdigest() == entry["lfs"]["sha256"], f"Official LFS hash mismatch: {item}"
        else:
            assert blob.hexdigest() == entry["blobId"], f"Official Git blob mismatch: {item}"
        observed[name] = digest.hexdigest()
    # An unexpected generation/chat config can silently override the official files.
    for name in ("generation_config.json", "chat_template.jinja", "special_tokens_map.json"):
        assert not (path / name).exists() or name in required, f"Unpinned override: {name}"
    shards = set(read(path / "model.safetensors.index.json")["weight_map"].values())
    assert shards == {n for n in required if n.endswith(".safetensors")}
    return {"path": str(path), "repo": manifest["repo"], "revision": manifest["revision"], "files_sha256": observed}


def freeze_files():
    paths = {Path(name) for name in source_hashes()}
    paths.update(ROOT / name for name in ("PROTOCOL.zh-CN.md", "CONTRACT.zh-CN.md", "EXECUTION.zh-CN.md"))
    paths.update(ROOT / "assets" / name for name in ("source-official-manifest.json", "official-source-manifest.json"))
    paths.update(DATA.glob("*.jsonl"))
    paths.add(LEGACY / "RATING_MANUAL.zh-CN.md")
    from run_benchmark import V3, frozen_panel
    _, panel, _ = frozen_panel()
    paths.update((V3 / "protocol.json", V3 / "panel_manifest.json"))
    paths.update(V3 / entry["file"] for entry in panel["files"].values())
    for shard in (0, 1):
        directory = SOURCE_CALIBRATIONS / f"shard{shard}"
        paths.add(directory / "receipt.json")
        receipt = read(directory / "receipt.json")
        assert receipt["status"] == "completed"
        assert receipt["data_sha256"] == {name: sha(DATA / f"{name}.jsonl") for name in ("confirm", "ability_diag")}
        for split, filename in (("behavior", "confirm"), ("ability", "ability_diag")):
            items = rows(DATA / f"{filename}.jsonl")
            for index in range(shard, 64, 2):
                calibration = directory / f"calibrations/{split}-{index:03d}.json"
                assert read(calibration)["item_id"] == items[index]["id"]
                paths.add(calibration)
    return {str(p.relative_to(PROJECT)): sha(p) for p in sorted(paths)}


def tokenizer_checks(source, target):
    from transformers import AutoConfig, GenerationConfig
    from collect import aligned_tokens, native_contrast_tokens
    from engine import load_tokenizer, encode_text, encode_pair, stop_tokens
    from run_benchmark import frozen_panel
    a, b = load_tokenizer(source), load_tokenizer(target)
    config = AutoConfig.from_pretrained(target, local_files_only=True)
    assert config.model_type == "llama" and config.hidden_size == 4096 and config.num_hidden_layers == 32
    stops, pad = stop_tokens(b, GenerationConfig.from_pretrained(target, local_files_only=True), config)
    pairs = [aligned_tokens(a, b, row)[3] for name in ("map_train", "map_val") for row in rows(DATA / f"{name}.jsonl")]
    for row in rows(DATA / "contrast.jsonl"):
        _, tokens, positions, _ = native_contrast_tokens(b, row, contrast=True)
        assert tokens[0] == b.bos_token_id and positions
    _, _, items = frozen_panel()
    lengths = {}
    for task, group in items.items():
        sizes = []
        for row in group:
            tokens = encode_text(b, row["context"])
            assert tokens[0] == b.bos_token_id and tokens.count(b.bos_token_id) == 1
            if row["request_type"] == "loglikelihood":
                size = max(len(c) + len(s) for c, s in [encode_pair(b, row["context"], v) for v in row["continuations"]])
            else:
                size = len(tokens) + row["gen_kwargs"]["max_gen_toks"]
            assert size <= config.max_position_embeddings, f"Context truncation would be required: {row['id']}"
            sizes.append(size)
        lengths[task] = max(sizes)
    return {"aligned_documents": len(pairs), "aligned_positions": sum(len(p["char_end"]) for p in pairs),
        "alignment_hashes": [p["alignment_sha256"] for p in pairs], "max_benchmark_total_tokens": lengths,
        "stop_ids": stops, "pad_id": pad, "bos_id": b.bos_token_id, "model_weights_loaded": False}


def prepare(args):
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == "", "Run readiness with CUDA_VISIBLE_DEVICES=''"
    args.output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    report = {"status": "preparing_cpu_only", "started_utc": utc(), "gpu_experiment_started": False,
        "experiment_weights_loaded": False, "gpu_preflight": "pending_future_run_authorization", "tests": [], "assets": {}}
    write(args.output / "GPU_READY.json", report)
    try:
        import torch
        import transformers
        assert not torch.cuda.is_initialized()
        report["runtime"] = {"python": sys.version, "torch": str(torch.__version__), "transformers": str(transformers.__version__)}
        for test in sorted(ROOT.glob("test_*.py")):
            result = subprocess.run([sys.executable, "-B", str(test)], cwd=PROJECT,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "HF_HUB_OFFLINE": "1"},
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=180)
            log = args.output / (test.stem + ".log")
            log.write_text(result.stdout)
            report["tests"].append({"test": test.name, "sha256": sha(test), "exit_code": result.returncode, "log_sha256": sha(log)})
            assert result.returncode == 0, f"CPU test failed: {test.name}; preserve the log"
        files = freeze_files()
        report["frozen_input_file_count"] = len(files)
        report["assets"]["source"] = verify_assets(args.source, read(ROOT / "assets/source-official-manifest.json"))
        manifest = read(ROOT / "assets/official-source-manifest.json")
        if not args.target.is_dir():
            report.update(status="CODE_READY_ASSET_BLOCKED", blocker="Exact authorized target weights absent", target_repo=manifest["repo"], target_revision=manifest["revision"])
            return
        report["assets"]["target"] = verify_assets(args.target, manifest)
        report["tokenizer_checks"] = tokenizer_checks(args.source, args.target)
        from run_benchmark import V3
        command = [sys.executable, "-B", str(V3 / "humaneval_sandbox.py"), "--self-test",
            "--bwrap", str(PROJECT / ".runtime/bubblewrap/root/usr/bin/bwrap"),
            "--official", str(PROJECT / ".runtime/human-eval"), "--python-prefix", "/workspace/miniconda/envs/amic-q3",
            "--output", str(args.output / "sandbox-controls.jsonl")]
        result = subprocess.run(command, capture_output=True, text=True, timeout=90)
        (args.output / "sandbox.log").write_text(result.stdout + result.stderr)
        assert result.returncode == 0, "HumanEval sandbox controls failed"
        # Official scorer and offline cache must be usable before GPU work begins.
        from run_benchmark import load_v3, frozen_panel
        scorer = load_v3("score_results").OfficialScorer(PROJECT / ".runtime/lm-evaluation-harness", PROJECT / ".cache/hf/datasets")
        _, _, panel_items = frozen_panel()
        for name in sorted({row["task_name"] for task, group in panel_items.items() if task != "humaneval" for row in group}):
            scorer.task(name)
        report["official_scorer"] = type(scorer).__name__
        assert freeze_files() == files, "Inputs changed during preparation"
        frozen = {"status": "inputs_frozen_gpu_not_run", "created_utc": utc(), "files": files,
            "source_model": str(args.source.resolve()), "target_model": str(args.target.resolve()),
            "target_repo": manifest["repo"], "target_revision": manifest["revision"], "root_cause": "paused"}
        write(args.output / "freeze.json", frozen)
        report.update(status="GPU_READY", freeze_sha256=sha(args.output / "freeze.json"))
    except Exception as error:
        report.update(status="PREPARATION_FAILED", error=str(error), traceback=traceback.format_exc())
        raise
    finally:
        report.update(ended_utc=utc(), wall_seconds=time.monotonic() - started)
        write(args.output / "GPU_READY.json", report)
        print(report["status"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default="/data/models/Qwen3.5-4B-851bf6e")
    parser.add_argument("--target", type=Path, default="/workspace/models/Llama-3.1-8B-Instruct-0e9e39f2")
    parser.add_argument("--output", type=Path, required=True)
    prepare(parser.parse_args())
