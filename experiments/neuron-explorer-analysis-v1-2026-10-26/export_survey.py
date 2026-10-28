"""Export existing full-layer and positive-dose responses; never load a model."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
SURVEY = REPO / "experiments/layer-survey-toy-v1-2026-10-27"
DOSE = REPO / "experiments/layer-dose-survey-toy-v1-2026-10-27"
LAYERS = {"2b": 24, "4b": 32, "9b": 32}
DOSES = {"0.0625", "0.125", "0.25", "0.5", "1"}
LABELS = ["图书馆", "糖果", "沟通改写", "两步整理", "朋友消息", "贡献登记", "带伞", "月份纠错"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def relative_source(value):
    # Historical exports contain either the local checkout or remote run root.
    name = str(value)
    if "/experiments/" in name:
        name = "experiments/" + name.split("/experiments/", 1)[1]
    candidate = (REPO / name).resolve()
    if not candidate.is_relative_to(REPO) or not any(
        candidate.is_relative_to(root / "survey-r01") for root in (SURVEY, DOSE)
    ) or candidate.suffix != ".json":
        raise ValueError(f"Unexpected source path: {name}")
    return candidate.relative_to(REPO).as_posix()


def build():
    questions = read_json(SURVEY / "questions.json")
    assert questions == read_json(DOSE / "questions.json")
    assert [q["id"] for q in questions] == [f"Q{i:02d}" for i in range(1, 9)]
    prompts = {q["id"]: q["prompt"] for q in questions}
    questions = [{**q, "label": label} for q, label in zip(questions, LABELS)]
    models = {m: {"id": m, "layers": n, "channels_per_layer": 10,
                  "baseline": {}, "points": []} for m, n in LAYERS.items()}
    points, sources, seen, originals = {}, {}, {}, {}
    context_by_question = {}
    survey_hashes = {}

    def add_manifest(path):
        sources[path.relative_to(REPO).as_posix()] = {"path": path.relative_to(REPO).as_posix(),
                                                    "sha256": sha(path), "bytes": path.stat().st_size}

    for root in (SURVEY, DOSE):
        add_manifest(root / "questions.json")
        receipt_path = root / "delivery-r01/export_receipt.json"
        receipt = read_json(receipt_path)
        assert receipt["status"] == "completed" and receipt["mode"] == "survey"
        assert receipt["whole_survey_complete"] is True
        add_manifest(receipt_path)
        records_path = root / "delivery-r01/all.records.jsonl"
        assert sha(records_path) == receipt["files"]["all.records.jsonl"]
        add_manifest(records_path)
        for entry in receipt["source_receipts"]:
            worker = entry["receipt"]
            assert worker["status"] == "completed" and worker["checks_passed"] is True
            if root == SURVEY:
                for relative, digest in worker["record_hashes"].items():
                    key = relative_source(str(Path(entry["run"]) / relative))
                    survey_hashes[key] = digest
        for line in records_path.read_text().splitlines():
            row = json.loads(line)
            assert row["status"] == "completed"
            model, qid = row["model_id"], row["question_id"]
            assert model in models and row["prompt"] == prompts[qid]
            context_key = (model, qid)
            if context_key in context_by_question:
                assert context_by_question[context_key] == row["context"]
            context_by_question[context_key] = row["context"]
            if root == SURVEY:
                path = relative_source(str(Path(row["source_run"]) / row["source_record"]))
                expected_hash = survey_hashes[path]
                extra = {"source_run", "source_record"}
            else:
                path = relative_source(row["export_source"]["record"])
                expected_hash = row["export_source"]["record_sha256"]
                extra = {"export_source"}
            original = {k: v for k, v in row.items() if k not in extra}
            if path in seen:
                assert root == DOSE and row["export_source"]["origin"] == "reused"
                assert expected_hash == seen[path] and original == originals[path]
                continue
            disk = REPO / path
            assert sha(disk) == expected_hash and read_json(disk) == original
            seen[path], originals[path] = expected_hash, original
            output = row["output"]
            token_digest = hashlib.sha256(json.dumps(output["token_ids"], separators=(",", ":")).encode()).hexdigest()
            assert token_digest == output["token_sha256"]
            assert len(output["token_ids"]) == output["generated_token_count"] <= 128
            assert output["end_reason"] in {"eos_token", "length_limit"}
            record = {"text": output["answer_text"], "raw_text": output["raw_text"],
                      "tokens": output["generated_token_count"], "stop_reason": output["end_reason"],
                      "source": path}
            if row["condition_id"] == "baseline":
                assert root == SURVEY and qid not in models[model]["baseline"]
                models[model]["baseline"][qid] = record
                continue
            layer, channel = row["layer"], row["channel"]
            assert type(layer) is int and 0 <= layer < LAYERS[model]
            assert type(channel) is int and channel >= 0
            value = row["intervention"]["dose"]
            dose = format(value, "g")
            assert dose in DOSES and (dose == "1") == (root == SURVEY)
            if root == DOSE:
                assert row["dose"] == value and row["export_source"]["origin"] == "new"
            point = points.setdefault((model, layer, channel), {"layer": layer, "channel": channel, "doses": {}})
            answers = point["doses"].setdefault(dose, {})
            assert qid not in answers
            answers[qid] = record

    qids = set(prompts)
    dose_points = 0
    for (model, layer, channel), point in sorted(points.items()):
        assert set(point["doses"]) in ({"1"}, DOSES)
        assert all(set(rows) == qids for rows in point["doses"].values())
        dose_points += len(point["doses"]) == 5
        models[model]["points"].append(point)
    for model in models.values():
        assert set(model["baseline"]) == qids
        for layer in range(model["layers"]):
            group = [p for p in model["points"] if p["layer"] == layer]
            assert len(group) == 10 and sum(len(p["doses"]) == 5 for p in group) == 1
    assert len(seen) == 9880 and len(points) == 880 and dose_points == 88
    counts = {"models": 3, "layers": 88, "points": 880, "dose_points": 88,
              "baseline": 24, "dose_1": 7040, "additional_dose": 2816, "records": 9880}
    data = {"metadata": {"schema_version": 1, "exported_at": datetime.now(timezone.utc).isoformat(),
                         "max_new_tokens": 128, "new_model_inference": False, "counts": counts},
            "questions": questions, "models": [models[m] for m in LAYERS]}
    manifest = {"schema_version": 1, "counts": counts, "sources": list(sources.values()),
                "record_paths": sorted(seen)}
    return data, manifest


def main():
    data, manifest = build()
    evidence = ROOT / "survey-evidence.json"
    evidence.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n")
    manifest["export_sha256"] = sha(evidence)
    (ROOT / "survey-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": "complete", "counts": data["metadata"]["counts"],
                      "bytes": evidence.stat().st_size}, ensure_ascii=False))


if __name__ == "__main__":
    main()
