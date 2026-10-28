"""Explicit two-stage launcher. Dry-run by default; no background/automatic stage 2."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

from common import ROOT, PROJECT, LEGACY, DATA, read, sha, write, utc, verify_freeze, require_stage


def commands(args):
    run = args.run.resolve()
    freeze, bundle = run / "freeze.json", run / "mapping/bundle.pt"
    def cmd(script, **kwargs):
        result = [sys.executable, "-u", str(ROOT / script)]
        mode = kwargs.pop("mode", None)
        if mode:
            result.append(mode)
        for key, value in kwargs.items():
            result += ["--" + key.replace("_", "-"), str(value)]
        return result
    groups = []
    if args.stage == 1:
        groups.append(("collect", [(gpu, cmd("collect.py", model=model, source_tokenizer=args.source,
            target_tokenizer=args.target, role=role, data=DATA, output=run / ("collection-" + role)))
            for gpu, role, model in ((0, "source", args.source), (1, "target", args.target))]))
        groups.append(("mapping", [(None, cmd("mapping.py", source=run / "collection-source",
            target=run / "collection-target", output=run / "mapping", device="cpu", freeze=freeze))]))
    base = run / f"stage{args.stage}"
    groups.append(("preflight", [(gpu, cmd("preflight.py", run=run, stage=args.stage,
        model=args.target, conditions=bundle, freeze=freeze, output=base / f"preflight-{gpu}")) for gpu in (0, 1)]))
    groups.append(("toy", [(gpu, cmd("toy.py", mode="run", stage=args.stage, model=args.target,
        conditions=bundle, output=base / "toy", freeze=freeze, shard_index=gpu)) for gpu in (0, 1)]))
    groups.append(("benchmark", [(gpu, cmd("benchmark.py", mode="run", stage=args.stage, model=args.target,
        conditions=bundle, output=base / "benchmark", freeze=freeze, shard_index=gpu)) for gpu in (0, 1)]))
    groups.append(("score", [(None, cmd("benchmark.py", mode="finish", stage=args.stage,
        output=base / "benchmark", project=PROJECT, freeze=freeze))]))
    groups.append(("export", [(None, cmd("toy.py", mode="export", stage=args.stage,
        output=base / "toy", freeze=freeze))]))
    groups.append(("gate", [(None, cmd("gate.py", run=run, freeze=freeze, stage=args.stage))]))
    return groups


def check_preflight(run, stage):
    a, b = [read(run / f"stage{stage}/preflight-{gpu}/receipt.json") for gpu in (0, 1)]
    assert a["status"] == b["status"] == "completed"
    for key in ("conditions_sha256", "freeze_sha256"):
        assert a[key] == b[key]
    assert a["engine"]["target_weight_sha256_before"] == b["engine"]["target_weight_sha256_before"]
    for key in ("scores", "tokens", "calibration"):
        assert a["checks"][key] == b["checks"][key], f"Two GPU outputs differ: {key}"


def execute(args):
    frozen = verify_freeze(args.run / "freeze.json")
    assert str(args.source.resolve()) == frozen["source_model"]
    assert str(args.target.resolve()) == frozen["target_model"]
    readiness = read(args.run / "GPU_READY.json")
    assert readiness["status"] == "GPU_READY" and readiness["freeze_sha256"] == sha(args.run / "freeze.json")
    import torch
    import transformers
    runtime = {"python": sys.version, "torch": str(torch.__version__), "transformers": str(transformers.__version__)}
    assert runtime == readiness["runtime"], "Runtime changed since CPU readiness; prepare a new run"
    from readiness import verify_assets
    for role, path in (("source", args.source), ("target", args.target)):
        assert verify_assets(path, read(ROOT / "assets" / ("source-official-manifest.json" if role == "source" else "official-source-manifest.json"))) == readiness["assets"][role]
    require_stage(args.stage, args.run, args.run / "mapping/bundle.pt", args.run / "freeze.json")
    # Do not overwrite/attach to an old attempt, and never stop another experiment.
    output = args.run / f"stage{args.stage}"
    active = subprocess.check_output(["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"], text=True).strip()
    assert not active, "GPU processes are active; preserve them and wait for an explicit launch"
    output.mkdir(exist_ok=False)
    status = {"status": "running", "started_utc": utc(), "pid": os.getpid(), "stage": args.stage, "steps": []}
    start = time.monotonic()
    write(output / "queue.json", status)
    try:
        for phase, group in commands(args):
            processes, streams = [], []
            entry = {"phase": phase, "started_utc": utc(), "workers": []}
            status["steps"].append(entry)
            try:
                for index, (gpu, command) in enumerate(group):
                    stream = (output / f"{phase}-{index}.log").open("xb")
                    streams.append(stream)
                    environment = {**os.environ, "CUDA_VISIBLE_DEVICES": "" if gpu is None else str(gpu),
                        "HF_HOME": str(PROJECT / ".cache/hf"), "HF_HUB_OFFLINE": "1", "HF_DATASETS_OFFLINE": "1",
                        "OMP_NUM_THREADS": "4", "PYTHONDONTWRITEBYTECODE": "1"}
                    process = subprocess.Popen(command, cwd=PROJECT, env=environment, stdout=stream, stderr=subprocess.STDOUT)
                    processes.append(process)
                    entry["workers"].append({"pid": process.pid, "gpu": gpu, "command": command})
                write(output / "queue.json", status)
                # Let both owned workers finish even if one fails; keep every failure.
                codes = [p.wait() for p in processes]
                entry.update(exit_codes=codes, ended_utc=utc())
                assert codes == [0] * len(codes), f"{phase} failed; no automatic retry"
            finally:
                for stream in streams:
                    stream.close()
            if phase == "preflight":
                check_preflight(args.run, args.stage)
            verify_freeze(args.run / "freeze.json")
            write(output / "queue.json", status)
        status["status"] = "completed"
        status["gate_decision"] = read(output / "gate.json")["decision"]
        status["next_stage_started"] = False
    except Exception as error:
        quality = args.run / "mapping/quality.json"
        hold = "MAPPING_QUALITY_HOLD" if quality.exists() and read(quality)["status"] != "PASS" else "TECHNICAL_HOLD"
        status.update(status="failed", decision=hold, error=str(error), traceback=traceback.format_exc())
        raise
    finally:
        status.update(ended_utc=utc(), wall_seconds=time.monotonic() - start)
        write(output / "queue.json", status)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage", type=int, choices=(1, 2), required=True)
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--source", type=Path, default="/data/models/Qwen3.5-4B-851bf6e")
    p.add_argument("--target", type=Path, required=True)
    p.add_argument("--execute", action="store_true", help="Future user-authorized GPU launch; absent means print commands only")
    args = p.parse_args()
    if args.execute:
        execute(args)
    else:
        print(json.dumps({"mode": "dry_run_no_processes_started", "stage": args.stage,
            "groups": commands(args)}, ensure_ascii=False, indent=2))
