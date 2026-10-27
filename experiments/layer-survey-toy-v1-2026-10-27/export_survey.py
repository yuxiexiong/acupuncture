"""Verify completed run records and export every raw response without judging it."""
import argparse
import csv
import hashlib
import html
import json
from pathlib import Path

import survey


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def token_hash(tokens):
    return hashlib.sha256(json.dumps(tokens, separators=(",", ":")).encode()).hexdigest()


def load_runs(runs):
    records, receipts, identities = [], [], set()
    for run in runs:
        run = Path(run).resolve()
        survey.verify(run)
        receipt = json.loads((run / "receipt.json").read_text())
        if receipt.get("status") != "completed" or receipt.get("mode") not in ("survey", "preflight"):
            raise ValueError(f"Not a completed survey/preflight run: {run}")
        hashes = receipt["record_hashes"]
        actual = {p.relative_to(run).as_posix() for p in (run / "records").glob("*.json")}
        if set(hashes) != actual:
            raise ValueError(f"Record manifest coverage mismatch: {run}")
        expected = receipt["expected_record_ids"]
        if len(expected) != len(set(expected)) or set(expected) != {Path(p).stem for p in actual}:
            raise ValueError(f"Expected record identities mismatch: {run}")
        for relative in sorted(hashes):
            path = run / relative
            if sha(path) != hashes[relative]:
                raise ValueError(f"Record hash mismatch: {path}")
            row = json.loads(path.read_text())
            identity = (row["model_id"], row["condition_id"], row["question_id"])
            if row["status"] != "completed" or row["model_id"] != receipt["model_id"]:
                raise ValueError(f"Record status/model mismatch: {path}")
            if path.stem != f'{row["condition_id"]}__{row["question_id"]}':
                raise ValueError(f"Record filename/identity mismatch: {path}")
            output = row["output"]
            tokens = output["token_ids"]
            if not isinstance(tokens, list) or any(type(t) is not int or t < 0 for t in tokens):
                raise ValueError(f"Invalid tokens: {path}")
            if token_hash(tokens) != output["token_sha256"] or len(tokens) > 128:
                raise ValueError(f"Token hash/budget mismatch: {path}")
            if identity in identities and row["condition_id"] != "baseline":
                raise ValueError(f"Duplicate intervention identity: {identity}")
            identities.add(identity)
            records.append({"source_run": str(run), "source_record": relative, **row})
        receipts.append({"run": str(run), "receipt_sha256": sha(run / "receipt.json"), "receipt": receipt})
    modes = {r["receipt"]["mode"] for r in receipts}
    if len(modes) != 1:
        raise ValueError("Preflight and survey records must be exported separately")
    freezes = {r["receipt"].get("freeze_sha256") for r in receipts}
    if len(freezes) != 1:
        raise ValueError("Runs have different frozen identities")
    baselines = {}
    for row in records:
        if row["condition_id"] == "baseline":
            key = (row["model_id"], row["question_id"])
            previous = baselines.get(key)
            if previous is not None and any(previous[field] != row[field] for field in ("prompt", "context")):
                raise ValueError(f"Conflicting baseline input: {key}")
            if previous is not None and any(previous["output"][field] != row["output"][field]
                                            for field in ("token_ids", "raw_text", "answer_text", "end_reason")):
                raise ValueError(f"Conflicting baseline output: {key}")
            baselines[key] = row
    for row in records:
        if row["condition_id"] != "baseline":
            baseline = baselines.get((row["model_id"], row["question_id"]))
            if baseline is None or any(baseline[field] != row[field] for field in ("prompt", "context")):
                raise ValueError(f"Missing/mismatched baseline for {row['condition_id']} {row['question_id']}")
    return records, receipts, baselines


def record_kind(row):
    if row["condition_id"] == "baseline":
        return "原版"
    if row["condition_id"].startswith(("zero-", "restored-")):
        return "技术对照"
    return "单针"


def export(runs, output):
    records, receipts, baselines = load_runs(runs)
    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=False)
    original = [row for row in records if row["condition_id"] == "baseline"]
    modified = [row for row in records if row["condition_id"] != "baseline"]
    for name, rows in (("all.records.jsonl", records), ("original.raw.jsonl", original), ("modified.raw.jsonl", modified)):
        with (destination / name).open("w") as stream:
            for row in rows:
                stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

    # Fixed identity hash order avoids exposing layer ordering in the initial view.
    conditions = sorted({(r["model_id"], r["condition_id"]) for r in modified},
                        key=lambda key: hashlib.sha256("/".join(key).encode()).hexdigest())
    samples = {key: f"S{i + 1:04d}" for i, key in enumerate(conditions)}
    mode = receipts[0]["receipt"]["mode"]
    full_survey = mode == "survey" and len(receipts) == 6 and len(records) == 7064 and {
        (r["receipt"]["model_id"], r["receipt"]["shard"], r["receipt"]["shards"]) for r in receipts
    } == {(model, shard, 2) for model in ("2b", "4b", "9b") for shard in (0, 1)}
    title = ("GPU 验收原文（非正式调查结果）" if mode == "preflight" else
             "逐层单针调查：全部并排原文" if full_survey else "逐层单针调查：部分运行原文预览")
    e = html.escape
    parts = [f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>{e(title)}</title>
<style>body{{font:16px/1.6 system-ui,sans-serif;max-width:1440px;margin:auto;padding:24px;color:#1f2937}}button{{padding:8px 14px}}.identity{{display:none}}body.reveal .identity{{display:block}}.pair{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit;background:#f3f4f6;padding:16px;margin-top:4px}}article{{border-top:1px solid #ccc;margin-top:20px}}small{{color:#596272}}details{{margin-top:18px}}@media(max-width:720px){{.pair{{grid-template-columns:1fr}}}}</style>
<h1>{e(title)}</h1><p>本页只保存和展示原文，不进行分析、评分或筛选。共 {len(conditions)} 个条件、{len(modified)} 份条件回答；原版记录 {len(original)} 份（分片重复记录也完整保留于原始文件）。{'三模型全部六个分片与 7064 份记录核验完整。' if full_survey else '此计数仅覆盖所提供且已核验的运行，不表示三模型全量实验均完成。'}</p>
<p>默认隐藏模型、层和通道。隐藏仅用于阅读，原始文件仍保留完整身份。每个条件中的所有题目均可展开。</p>
<button onclick="document.body.classList.toggle('reveal')">显示 / 隐藏模型与位置</button>
<p><a href="original.raw.jsonl">原版原始记录</a> · <a href="modified.raw.jsonl">条件原始记录</a> · <a href="all.records.jsonl">全部逐次记录</a> · <a href="annotations.blank.csv">空白观察表</a></p>''']
    ordered = sorted(modified, key=lambda r: (samples[(r["model_id"], r["condition_id"])], r["question_id"]))
    grouped = {key: [] for key in conditions}
    for row in ordered:
        grouped[(row["model_id"], row["condition_id"])].append(row)
    for key, rows in grouped.items():
        sample = samples[key]
        parts.append(f'<details><summary>{sample} · {record_kind(rows[0])} · {len(rows)} 道题</summary>')
        parts.append(f'<p class="identity">模型 {e(key[0])} · 条件 {e(key[1])}</p>')
        for row in rows:
            baseline = baselines[(row["model_id"], row["question_id"])]
            parts.append(f'<article><p><b>{e(row["question_id"])}</b> {e(row["prompt"])}</p><div class="pair">')
            for label, record in (("原版", baseline), ("该条件", row)):
                out = record["output"]
                end = "达到 128 token 上限，未观察到正常结束" if out["end_reason"] == "length_limit" else str(out["end_reason"])
                parts.append(f'<section><b>{label}</b><pre>{e(out["raw_text"])}</pre><small>{len(out["token_ids"])} token · {e(end)}</small></section>')
            parts.append('</div></article>')
        parts.append('</details>')
    parts.append('</html>')
    (destination / "paired_raw.html").write_text("\n".join(parts))
    with (destination / "annotations.blank.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(["sample", "question_id", "任务完成与正确性", "内容变化", "语气与格式变化", "重复或乱码", "无明显变化或无法判断", "备注"])
        writer.writerows([[samples[(r["model_id"], r["condition_id"])], r["question_id"], "", "", "", "", "", ""] for r in ordered])
    with (destination / "sample_key.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(["sample", "model_id", "condition_id", "layer", "channel"])
        writer.writerows([[samples[key], *key, grouped[key][0]["layer"], grouped[key][0]["channel"]] for key in conditions])
    receipt = {"status": "completed", "mode": mode, "whole_survey_complete": full_survey, "source_receipts": receipts,
               "counts": {"records": len(records), "original": len(original), "modified": len(modified), "conditions": len(conditions)},
               "positive_needle_answers": sum(record_kind(row) == "单针" for row in modified),
               "technical_control_answers": sum(record_kind(row) == "技术对照" for row in modified),
               "scope": "whole survey" if full_survey else "all supplied completed runs; no claim of whole-survey completion",
               "files": {p.name: sha(p) for p in sorted(destination.iterdir())}}
    (destination / "export_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = export(args.runs, args.output)
    print(json.dumps({"status": result["status"], "mode": result["mode"], "counts": result["counts"]}))
