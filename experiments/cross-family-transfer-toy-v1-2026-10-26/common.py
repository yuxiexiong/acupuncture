"""Small shared contract and immutable-input checks for the two-stage experiment."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
LEGACY = ROOT.parent / "transfer-toy-v1-2026-10-26"
sys.path.append(str(LEGACY))
from run_io import sha, read, rows, write, immutable, utc

DATA = LEGACY / "data"
SOURCE_CALIBRATIONS = LEGACY / "runs/transfer-9b-2b-r01/source"
BENCHMARK_ARMS = {1: "true_D_match", 2: "true_S_recipe"}


def conditions(stage):
    arms = ("D_raw", "D_match") if stage == 1 else ("S_proj", "S_recipe")
    return (["T_0"] if stage == 1 else []) + [f"{pair}_{arm}" for pair in
        ("true", "random1", "random2", "random3") for arm in arms] + ["T_dense" if stage == 1 else "T_sparse"]


def source_hashes():
    paths = list(ROOT.glob("*.py")) + list(LEGACY.glob("*.py"))
    for name in ("capability-screen-v3-2026-10-26", "capability-damage-v2-2026-10-26"):
        paths += list((ROOT.parent / name).glob("*.py"))
    return {str(p.resolve()): sha(p) for p in sorted(paths)}


def verify_freeze(path):
    frozen = read(path)
    assert frozen["target_repo"] == "meta-llama/Llama-3.1-8B-Instruct"
    assert frozen["status"] == "inputs_frozen_gpu_not_run"
    for name, digest in frozen["files"].items():
        assert sha(PROJECT / name) == digest, f"Frozen input changed: {name}"
    return frozen


def require_stage(stage, run, bundle=None, freeze=None):
    if stage == 1:
        return
    gate_path = Path(run) / "stage1/gate.json"
    gate = read(gate_path)
    assert gate["decision"] == "PASS", "Stage 2 is closed: stage 1 did not PASS"
    assert gate["stage"] == 1 and gate["primary_arm"] == "true_D_match"
    if bundle is not None:
        assert gate["bundle_sha256"] == sha(bundle), "Gate is for another mapping"
    if freeze is not None:
        assert gate["freeze_sha256"] == sha(freeze), "Gate is for another frozen protocol"
    for name, digest in gate["evidence_sha256"].items():
        assert sha(Path(run) / name) == digest, f"Gate evidence changed: {name}"
    expected = {"stage1/benchmark/finish-r01/" + name for name in ("scores.jsonl", "summary.json", "receipt.json")}
    assert set(gate["evidence_sha256"]) == expected | {"mapping/quality.json"}
    quality = read(Path(run) / "mapping/quality.json")
    assert quality["status"] == "PASS", "Stage 2 is closed: mapping quality did not PASS"
    for key in ("bundle_sha256", "freeze_sha256"):
        assert quality[key] == gate[key], f"Mapping quality and gate differ: {key}"
    from gate import decide, metrics_from_scores
    measured = metrics_from_scores(rows(Path(run) / "stage1/benchmark/finish-r01/scores.jsonl"))
    assert measured == gate["metrics"], "Gate metrics do not match frozen scored pairs"
    assert decide(measured) == (gate["decision"], gate["qualifying_tasks"])
