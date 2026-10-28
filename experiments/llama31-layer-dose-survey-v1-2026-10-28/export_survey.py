"""Export the complete Llama signed-dose survey with full raw text and provenance."""
import argparse
import csv
import hashlib
import html
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MODEL = "llama31-8b-instruct"
DOSES = (-1.0, -0.5, -0.25, -0.125, -0.0625, 0.0, 0.0625, 0.125, 0.25, 0.5, 1.0)
WORKERS = {(MODEL, shard, 2) for shard in (0, 1)}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def token_hash(tokens):
    return hashlib.sha256(json.dumps(tokens, separators=(",", ":")).encode()).hexdigest()


def checked_row(path, digest):
    path = Path(path).resolve()
    assert sha(path) == digest, f"Record hash mismatch: {path}"
    row = json.loads(path.read_text(encoding="utf-8"))
    output, tokens = row["output"], row["output"]["token_ids"]
    assert row["status"] == "completed" and row["kind"] in ("baseline", "dose")
    assert tokens and all(type(t) is int and t >= 0 for t in tokens)
    assert token_hash(tokens) == output["token_sha256"], f"Token hash mismatch: {path}"
    assert output["generated_token_count"] == len(tokens) <= 128 and output["max_new_tokens"] == 128
    assert output["end_reason"] in ("eos_token", "length_limit")
    assert output["end_reason"] != "length_limit" or len(tokens) == 128
    try:
        name = path.relative_to(REPO).as_posix()
    except ValueError:
        name = str(path)
    return {**row, "export_source": {"origin": "new", "record": name, "record_sha256": digest}}


def check_worker_row(row, shard, point_shards):
    assert row["model_id"] == MODEL
    if row["kind"] == "baseline":
        assert shard == 0 and row["condition_id"] == "baseline"
    else:
        assert point_shards[row["point_id"]] == shard, "Wrong point worker shard"


def load_runs(runs):
    import survey

    _contract, _questions, samples = survey.load_design()
    point_shards = {point["id"]: index % 2 for index, point in enumerate(samples[MODEL])}
    records, receipts, workers = [], [], set()
    for run in runs:
        run = Path(run).resolve()
        receipt = survey.verify(run)
        assert receipt["status"] == "completed" and receipt["checks_passed"] is True
        assert receipt["mode"] == "survey", "Only complete formal survey runs can be exported"
        identity = (receipt["model_id"], receipt["shard"], receipt["shards"])
        assert identity in WORKERS and identity not in workers, f"Unexpected or duplicate worker: {identity}"
        workers.add(identity)
        actual = {p.relative_to(run).as_posix() for p in (run / "records").glob("*.json")}
        assert actual == set(receipt["record_hashes"]), "Record coverage mismatch"
        assert set(receipt["expected_record_ids"]) == {Path(p).stem for p in actual}
        assert len(receipt["expected_record_ids"]) == len(actual)
        assert len(actual) == (12808 if receipt["shard"] == 0 else 12800), "Incomplete formal worker"
        receipt_hash = sha(run / "receipt.json")
        for relative, digest in sorted(receipt["record_hashes"].items()):
            row = checked_row(run / relative, digest)
            assert Path(relative).stem == f'{row["condition_id"]}__{row["question_id"]}'
            check_worker_row(row, receipt["shard"], point_shards)
            row["export_source"].update(worker_shard=receipt["shard"], run=str(run), receipt_sha256=receipt_hash)
            records.append(row)
        assert sha(run / "receipt.json") == receipt_hash, "Receipt changed during export"
        receipts.append({"run": str(run), "receipt_sha256": receipt_hash, "receipt": receipt})
    assert workers == WORKERS, "Formal export requires both complete workers"
    assert len({r["receipt"]["freeze_sha256"] for r in receipts}) == 1, "Mixed frozen identities"
    assert len(records) == 25608 and len({r["export_source"]["record"] for r in records}) == 25608
    return records, receipts


def paired_rows(rows, point, qid):
    assert len(rows) == len(DOSES), "Incomplete eleven-column group"
    by_dose = {row["dose"]: row for row in rows}
    assert len(by_dose) == len(rows) and set(by_dose) == set(DOSES), "Duplicate or missing dose"
    ordered = [by_dose[d] for d in DOSES]
    base = by_dose[0.0]
    for row in ordered:
        assert (row["model_id"], row["question_id"]) == (MODEL, qid)
        assert row["prompt"] == base["prompt"] and row["context"] == base["context"], "Prompt mismatch"
        assert row["calibration"] == base["calibration"], "Calibration mismatch"
        assert row["output"]["input_token_sha256"] == base["output"]["input_token_sha256"]
        if row["dose"] == 0:
            assert row["kind"] == "baseline" and row["point_id"] is None
            assert row["layer"] is None and row["channel"] is None and row["intervention"] is None
        else:
            assert row["kind"] == "dose" and row["point_id"] == point["id"]
            assert (row["layer"], row["channel"]) == (point["layer"], point["channel"])
            assert row["intervention"]["dose"] == row["dose"]
    for neg, pos in zip(ordered[:5], reversed(ordered[6:])):
        a, b = neg["intervention"], pos["intervention"]
        assert a["dose"] == -b["dose"] and a["column_norm"] == b["column_norm"]
        assert a["clean_residual_scale"] == b["clean_residual_scale"]
        assert a["requested_offset"] == -b["requested_offset"], "Requested dose mismatch"
        assert a["bf16_offset"] == -b["bf16_offset"], "BF16 dose mismatch"
    return ordered


def groups_for(records, questions, samples):
    assert set(samples) == {MODEL}
    points = samples[MODEL]
    assert len(points) == 320 and len({p["id"] for p in points}) == 320
    assert {p["layer"] for p in points} == set(range(32))
    assert all(len({p["channel"] for p in points if p["layer"] == layer}) == 10 for layer in range(32))
    assert [q["id"] for q in questions] == [f"Q{i:02d}" for i in range(1, 9)]
    assert len(records) == 25608, "Incomplete formal source set"
    baseline, modified = {}, {}
    for row in records:
        assert row["model_id"] == MODEL
        if row["kind"] == "baseline":
            key = row["question_id"]
            assert key not in baseline, "Duplicate baseline"
            baseline[key] = row
        else:
            assert row["kind"] == "dose", "Technical controls are not formal answers"
            key = (row["point_id"], row["question_id"], row["dose"])
            assert key not in modified, f"Duplicate dose identity: {key}"
            modified[key] = row
    assert set(baseline) == {q["id"] for q in questions} and len(modified) == 25600
    groups = []
    for point in sorted(points, key=lambda p: (p["layer"], p["channel"])):
        for question in questions:
            qid = question["id"]
            rows = [baseline[qid]] + [modified.pop((point["id"], qid, d)) for d in DOSES if d]
            ordered = paired_rows(rows, point, qid)
            assert ordered[0]["prompt"] == question["prompt"]
            groups.append({"model_id": MODEL, "layer": point["layer"], "channel": point["channel"],
                           "point_id": point["id"], "question_id": qid, "rows": ordered})
    assert not modified and len(groups) == 2560
    return groups


def cell(row, label):
    e, output, source = html.escape, row["output"], row["export_source"]
    return (f'<section><b>{e(label)}</b><pre>{e(output["raw_text"])}</pre>'
            f'<small>{len(output["token_ids"])} token · {e(output["end_reason"])} · 本轮生成</small>'
            f'<details><summary>正文、token及来源</summary><pre>{e(output["answer_text"])}</pre>'
            f'<pre>{e(json.dumps(output["token_ids"]))}</pre><small>{e(source["record"])}<br>'
            f'文件 SHA-256: {e(source["record_sha256"])}<br>token SHA-256: {e(output["token_sha256"])}</small></details></section>')


def render(groups):
    title = f"Llama 3.1 8B 正负五档：{len(groups)}组十一栏完整原文"
    parts = [f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>{title}</title>
<style>body{{font:16px/1.6 system-ui,sans-serif;margin:24px;color:#1f2937}}.eleven{{display:grid;grid-template-columns:repeat(11,minmax(240px,1fr));gap:12px;overflow-x:auto}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit;background:#f3f4f6;padding:12px}}section{{min-width:0}}small{{color:#596272}}article{{border-top:1px solid #ccc;margin-top:24px}}nav a{{margin-right:12px}}</style>
<h1>{title}</h1><p>完整保留raw、正文和实际token，不截断显示、不评分。原版按组重复显示，但只按八份唯一来源计数。正常EOS原长保留，不补齐到128。</p>
<p>正式来源共25,608份：25,600份正负剂量回答、8份原版；全部为本轮生成。每层固定十点，每点两侧同样五档。与千问同题同剂量规则；模型原生模板/tokenizer不同，旧千问完整剂量仅每层一点，不能把覆盖差异当作模型效应。</p>
<p><a href="all.records.jsonl">全部唯一记录</a> · <a href="comparison_index.json">十一栏来源索引</a> · <a href="annotations.blank.csv">自由观察表</a></p><nav>''']
    parts.extend(f'<a href="#group-{i}">L{g["layer"]} N{g["channel"]} {html.escape(g["question_id"])}</a>' for i, g in enumerate(groups))
    parts.append("</nav>")
    for i, group in enumerate(groups):
        parts.append(f'<article id="group-{i}"><h2>{html.escape(group["model_id"])} · L{group["layer"]} / N{group["channel"]} · {html.escape(group["question_id"])}</h2><p>{html.escape(group["rows"][0]["prompt"])}</p><div class="eleven">')
        parts.extend(cell(row, "原版 0" if dose == 0 else f"剂量 {dose:g}") for dose, row in zip(DOSES, group["rows"]))
        parts.append("</div></article>")
    return "\n".join([*parts, "</html>"])


def export(runs, output):
    import survey

    records, receipts = load_runs(runs)
    _contract, questions, samples = survey.load_design()
    groups = groups_for(records, questions, samples)
    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=False)
    with (destination / "all.records.jsonl").open("w", encoding="utf-8") as stream:
        for row in records:
            stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    index = [{**{k: v for k, v in group.items() if k != "rows"},
              "doses": [{"dose": dose, **row["export_source"]} for dose, row in zip(DOSES, group["rows"])]} for group in groups]
    (destination / "comparison_index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (destination / "paired_raw.html").write_text(render(groups), encoding="utf-8")
    with (destination / "annotations.blank.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(["model_id", "layer", "channel", "question_id", "自由观察", "反例与不确定性", "来源备注"])
        writer.writerows([[g["model_id"], g["layer"], g["channel"], g["question_id"], "", "", ""] for g in groups])
    receipt = {"status": "completed", "mode": "survey", "whole_survey_complete": True,
               "counts": {"new_records": len(records), "intervention_records": 25600, "baseline_records": 8,
                          "reused_sources": 0, "unique_records": len(records), "comparison_groups": len(groups),
                          "display_cells": len(groups) * len(DOSES), "scientific_records": len(records)},
               "source_receipts": receipts, "files": {p.name: sha(p) for p in sorted(destination.iterdir())}}
    (destination / "export_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = export(args.runs, args.output)
    print(json.dumps({"status": result["status"], "counts": result["counts"]}))
