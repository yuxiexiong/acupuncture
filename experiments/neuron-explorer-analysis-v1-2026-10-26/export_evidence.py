#!/usr/bin/env python3
"""Export existing Acupuncture records for the local, read-only analysis page.

No model imports, tensor loading, network access, or writes to source experiments.
refs use JSON Pointer; for JSONL, the document is the array of nonempty lines.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = "experiments/root-cause-toy-v1-2026-10-26"
TRANSFER = "experiments/transfer-toy-v1-2026-10-26"
RUN = f"{TRANSFER}/runs/transfer-9b-2b-r01"
SCORE_FIELDS = ("scores", "margin", "prediction", "correct", "strongest_wrong")
SIX_CONDITIONS = ("clean", "AB_d1", "repair", "replay", "control_repair", "control_replay")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def pointer_key(value):
    return str(value).replace("~", "~0").replace("/", "~1")


class Sources:
    def __init__(self, repo):
        self.repo = repo
        self.records = {}
        self.documents = {}

    def read(self, path):
        if path not in self.records:
            source = self.repo / path
            if not source.is_file():
                self.records[path] = dict(path=path, sha256=None, bytes=None,
                                          href=None, status="missing")
                self.documents[path] = None
                return None
            raw = source.read_bytes()
            self.records[path] = dict(path=path, sha256=sha256(raw), bytes=len(raw),
                                      href="/" + path, status="available")
            if source.suffix == ".json":
                self.documents[path] = json.loads(raw)
            elif source.suffix == ".jsonl":
                self.documents[path] = [json.loads(line) for line in raw.splitlines() if line.strip()]
            else:
                self.documents[path] = raw.decode("utf-8")
        return self.documents[path]

    def ref(self, path, pointer=""):
        self.read(path)
        return dict(path=path, pointer=pointer)

    def documents_for(self, paths):
        return [self.ref(path) for path in paths]


def scored_item(sources, path, expected_conditions):
    raw = sources.read(path)
    if raw is None:
        return dict(id=None, benchmark=None, item_sha256=None, conditions=None,
                    status="missing", ref=sources.ref(path))
    conditions = {}
    for name in expected_conditions:
        record = raw.get("conditions", {}).get(name)
        conditions[name] = {key: record.get(key) if record else None for key in SCORE_FIELDS}
        conditions[name].update(
            status="available" if record is not None else "missing",
            ref=sources.ref(path, "/conditions/" + pointer_key(name)),
        )
    return dict(id=raw.get("id"), benchmark=raw.get("benchmark"),
                item_sha256=raw.get("item_sha256"), conditions=conditions,
                status="available", ref=sources.ref(path))


def export(repo=REPO):
    sources = Sources(repo)
    summary_path = f"{ROOT}/first-round-results.json"
    summary = sources.read(summary_path) or {}
    contract_path = f"{ROOT}/contract.json"
    contract = sources.read(contract_path) or {}
    questions_path = f"{ROOT}/data/ability_dev.jsonl"
    questions = sources.read(questions_path) or []
    item_count = sum((contract.get("dev_counts") or {}).values())
    decomposition_conditions = list(next(iter(summary.get("decomposition_correct_counts", {}).values()), {}))
    decomposition = {
        "correct_counts": summary.get("decomposition_correct_counts"),
        "correct_counts_ref": sources.ref(summary_path, "/decomposition_correct_counts"),
        "comparisons": summary.get("decomposition_comparisons"),
        "comparisons_ref": sources.ref(summary_path, "/decomposition_comparisons"),
        "items": [scored_item(sources, f"{ROOT}/runs/root-r01/decompose-r01/item-{i:03d}.json",
                              decomposition_conditions) for i in range(item_count)],
        "ref": sources.ref(f"{ROOT}/runs/root-r01/decompose-r01/receipt.json"),
    }
    candidates = []
    for index, candidate in enumerate(summary.get("candidate_results", [])):
        meta = candidate["candidate"]
        candidates.append({
            **{key: meta.get(key) for key in ("id", "component", "positions", "selection")},
            "metadata": meta,
            "metadata_ref": sources.ref(summary_path, f"/candidate_results/{index}/candidate"),
            "tasks": candidate.get("tasks"),
            "tasks_ref": sources.ref(summary_path, f"/candidate_results/{index}/tasks"),
            "items": [scored_item(sources,
                                  f"{ROOT}/runs/root-parallel-r01/{meta['id']}/ability-{i:03d}.json",
                                  SIX_CONDITIONS) for i in range(item_count)],
            "ref": sources.ref(summary_path, f"/candidate_results/{index}"),
        })
    ranking = []
    for i in range(item_count):
        path = f"{ROOT}/runs/root-r01/rank-r01/item-{i:03d}.json"
        raw = sources.read(path)
        ranking.append({**{key: raw.get(key) if raw else None
                           for key in ("id", "benchmark", "item_sha256", "ranking")},
                        "status": "available" if raw is not None else "missing", "ref": sources.ref(path)})
    targets = []
    for model in ("2b", "9b"):
        base = f"{RUN}/target{model}"
        mapping_path = f"{base}/mapping/conditions.json"
        benchmark_path = f"{base}/benchmark/finish-r01/summary.json"
        diagnostic_path = f"{base}/export-r01/diagnostic.summary.json"
        collection_path = f"{RUN}/collection-target{model}/receipt.json"
        mapping = sources.read(mapping_path)
        benchmark = sources.read(benchmark_path) or {}
        diagnostic = sources.read(diagnostic_path)
        collection = sources.read(collection_path) or {}
        targets.append({
            "id": model, "label": "Qwen3.5-" + model.upper(),
            "scientific_status": "exploratory_pending_confirmation",
            "model": collection.get("engine"), "model_ref": sources.ref(collection_path, "/engine"),
            "mapping": {**(mapping or {}), "status": "available" if mapping is not None else "missing",
                        "ref": sources.ref(mapping_path)},
            "benchmarks": benchmark.get("benchmarks"),
            "benchmarks_ref": sources.ref(benchmark_path, "/benchmarks"),
            "benchmark_scope": benchmark.get("scope"),
            "benchmark_status": benchmark.get("status", "missing"),
            "benchmark_metadata": {key: benchmark.get(key) for key in
                                   ("status", "created_utc", "model", "arm_bindings", "technical_failures",
                                    "harness_commit", "fixed_panel_manifest_sha256", "source_scorer_sha256", "scope")},
            "benchmark_metadata_ref": sources.ref(benchmark_path),
            "diagnostic": {**(diagnostic or {"conditions": None, "scope": None, "status": "missing"}),
                           "ref": sources.ref(diagnostic_path)},
            "documents": sources.documents_for([
                f"{base}/mapping/receipt.json", collection_path, benchmark_path, diagnostic_path,
            ]),
        })
    evidence = {
        "metadata": {
            "schema_version": 1,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "read_only": True,
            "scientific_status": "exploratory_pending_confirmation",
            "scope": "Existing records only; no new inference or activation reconstruction.",
            "provenance": "Each ref selects a source subtree; sources contains exact byte SHA-256 and local URL. JSONL pointers index nonempty lines.",
            "missing_value_policy": "Missing observations are null with missing status; measured zeros remain zeros.",
            "boundaries": [
                "Root-cause candidates were selected and tested on the same 64 development items; independent confirmation was not run.",
                "Module contribution replacement is not a single-neuron intervention, and a repair site is not necessarily the earliest damage site.",
                "Accuracy and margin are separate readings, not independent replications; all candidates and controls are retained.",
                "Transfer mapping and single-column reconstruction are geometrical diagnostics, not proof of functional identity.",
                "The four-benchmark panel and the 19-condition diagnostic have different sample sizes and purposes.",
                "Behavioral blind ratings and a shared causal mechanism remain unconfirmed; private rating identity keys are excluded.",
                "No token activation trajectories are present in this export. Ranking scores and score differences must not be drawn as observed activation traces.",
            ],
        },
        "root_cause": {
            "status": summary.get("status", "missing"),
            "scientific_status": "exploratory_pending_confirmation",
            "question_count_per_task": summary.get("question_count_per_task"),
            "independent_confirmation_run": summary.get("independent_confirmation_run"),
            "model": contract.get("source"), "model_ref": sources.ref(contract_path, "/source"),
            "needles": contract.get("needles"), "needles_ref": sources.ref(contract_path, "/needles"),
            "decomposition": decomposition,
            "candidates": candidates,
            "ranking": {"items": ranking, "ref": sources.ref(f"{ROOT}/runs/root-r01/rank-r01/receipt.json")},
            "questions": [{**q, "ref": sources.ref(questions_path, f"/{i}")} for i, q in enumerate(questions)],
            "timing": summary.get("timing"), "boundaries": summary.get("boundaries"),
            "ref": sources.ref(summary_path),
            "documents": sources.documents_for([
                f"{ROOT}/RESULTS.zh-CN.md", f"{ROOT}/CONTRACT.zh-CN.md", contract_path,
                f"{ROOT}/runs/root-parallel-r01/receipt.json", f"{ROOT}/root_engine.py",
            ]),
        },
        "transfer": {
            "scientific_status": "exploratory_pending_confirmation",
            "behavioral_ratings_status": "pending_not_imported",
            "targets": targets,
            "documents": sources.documents_for([
                f"{TRANSFER}/RESULTS.zh-CN.md", f"{TRANSFER}/PROTOCOL.zh-CN.md",
                f"{TRANSFER}/EXECUTION.zh-CN.md", f"{TRANSFER}/BENCHMARK_FOLLOWUP.zh-CN.md",
                f"{TRANSFER}/fit_mapping.py", f"{TRANSFER}/transfer_engine.py",
            ]),
        },
        "sources": sources.records,
    }
    evidence["metadata"]["source_status"] = "complete" if all(
        s["status"] == "available" for s in sources.records.values()) else "missing_sources"
    return evidence


def main():
    evidence = export()
    raw = (json.dumps(evidence, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()
    (HERE / "evidence.json").write_bytes(raw)
    manifest = {
        "schema_version": 1,
        "exported_at": evidence["metadata"]["exported_at"],
        "read_only": True,
        "scientific_status": evidence["metadata"]["scientific_status"],
        "source_status": evidence["metadata"]["source_status"],
        "exporter_sha256": sha256(Path(__file__).read_bytes()),
        "outputs": [{"path": (HERE / "evidence.json").relative_to(REPO).as_posix(),
                     "sha256": sha256(raw), "bytes": len(raw)}],
        "sources": [{key: value[key] for key in ("path", "sha256", "bytes")}
                    for value in evidence["sources"].values() if value["status"] == "available"],
        "missing_sources": [s["path"] for s in evidence["sources"].values() if s["status"] != "available"],
    }
    (HERE / "evidence-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"Exported {len(manifest['sources'])} existing source files; {len(raw):,} bytes; {manifest['source_status']}.")


if __name__ == "__main__":
    main()
