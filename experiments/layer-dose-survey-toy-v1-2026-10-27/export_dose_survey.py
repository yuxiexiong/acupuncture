"""Verify dose records and export complete raw text, without scores or truncation."""
import argparse
import csv
import html
import json
from pathlib import Path

import dose_survey as survey

DOSES = (0.0, *survey.DOSES)
WORKERS = {(model, shard, 2) for model in ("2b", "4b", "9b") for shard in (0, 1)}


def checked_row(path, digest, origin):
    assert survey.io.sha(path) == digest, f"Source record hash mismatch: {path}"
    row = survey.io.read(path)
    output, tokens = row["output"], row["output"]["token_ids"]
    assert row["status"] == "completed"
    assert tokens and all(type(t) is int and t >= 0 for t in tokens)
    assert survey.token_hash(tokens) == output["token_sha256"], f"Token hash mismatch: {path}"
    assert output["generated_token_count"] == len(tokens) <= 128
    assert output["max_new_tokens"] == 128
    assert output["end_reason"] in ("eos_token", "length_limit")
    assert (output["end_reason"] == "eos_token") == (tokens[-1] in (248044, 248046))
    assert not any(t in (248044, 248046) for t in tokens[:-1])
    assert output["end_reason"] != "length_limit" or len(tokens) == 128
    path = Path(path).resolve()
    try:
        name = path.relative_to(survey.REPO).as_posix()
    except ValueError:
        name = str(path)
    return {**row, "export_source": {"origin": origin, "record": name, "record_sha256": digest}}


def load_runs(runs):
    records, receipts, identities = [], [], set()
    for directory in runs:
        directory = Path(directory).resolve()
        receipt = survey.verify(directory)
        identity = (receipt["model_id"], receipt["shard"], receipt["shards"])
        assert identity not in identities, f"Duplicate worker: {identity}"
        identities.add(identity)
        actual = {p.relative_to(directory).as_posix() for p in (directory / "records").glob("*.json")}
        assert actual == set(receipt["record_hashes"]), "Record coverage mismatch"
        assert set(receipt["expected_record_ids"]) == {Path(p).stem for p in actual}
        assert len(receipt["expected_record_ids"]) == len(actual)
        for relative, digest in sorted(receipt["record_hashes"].items()):
            row = checked_row(directory / relative, digest, "new")
            assert row["model_id"] == receipt["model_id"]
            assert Path(relative).stem == f'{row["condition_id"]}__{row["question_id"]}'
            row["export_source"].update(worker_shard=receipt["shard"], run=str(directory),
                                        receipt_sha256=survey.io.sha(directory / "receipt.json"))
            records.append(row)
        receipts.append({"run": str(directory), "receipt_sha256": survey.io.sha(directory / "receipt.json"), "receipt": receipt})
    assert receipts, "No runs supplied"
    assert len({r["receipt"]["mode"] for r in receipts}) == 1, "Export preflight and survey separately"
    assert len({r["receipt"]["freeze_sha256"] for r in receipts}) == 1, "Mixed frozen identities"
    return records, receipts


def reused(model, point, qid):
    _row, source = survey.source_record(model, point, qid)
    return checked_row(survey.REPO / source["record"], source["record_sha256"], "reused")


def groups_for(records, receipts, questions, selection, mode):
    groups, originals, dose1 = [], {}, {}
    workers = {(r["receipt"]["model_id"], r["receipt"]["shard"], r["receipt"]["shards"]) for r in receipts}
    if mode == "survey":
        assert workers == WORKERS and len(records) == 2816, "Formal export requires all six complete workers"
        candidates = [(p, q["id"], None) for p in selection["selected_channels"] for q in questions]
    else:
        assert mode == "preflight"
        candidates = []
        for model, shard, _ in sorted(workers):
            points = [p for p in selection["selected_channels"] if p["model_id"] == model and p["layer"] % 2 == shard]
            candidates.append((points[len(points) // 2], "Q04", shard))
    new = {}
    for row in records:
        if row["kind"] != "dose":
            continue
        key = (row["model_id"], row["point_id"], row["question_id"], row["dose"],
               row["export_source"]["worker_shard"] if mode == "preflight" else None)
        assert key not in new, f"Duplicate dose identity: {key}"
        new[key] = row
    for point, qid, shard in candidates:
        model = point["model_id"]
        baseline_key, point_key = (model, qid), (model, point["condition_id"], qid)
        if baseline_key not in originals:
            originals[baseline_key] = reused(model, None, qid)
        if point_key not in dose1:
            dose1[point_key] = reused(model, point, qid)
        rows = [originals[baseline_key]]
        rows.extend(new.pop((model, point["condition_id"], qid, d, shard)) for d in survey.NEW_DOSES)
        rows.append(dose1[point_key])
        assert all(row["prompt"] == rows[0]["prompt"] and row["context"] == rows[0]["context"] for row in rows)
        assert all(row["output"]["input_token_sha256"] == rows[0]["output"]["input_token_sha256"] for row in rows)
        groups.append({"model_id": model, "layer": point["layer"], "channel": point["channel"],
                       "point_id": point["condition_id"], "question_id": qid, "worker_shard": shard, "rows": rows})
    assert not new, "Unexpected new-dose records"
    sources = [*originals.values(), *dose1.values()]
    if mode == "survey":
        assert len(groups) == 704 and len(originals) == 24 and len(dose1) == 704
    return groups, sources


def cell(row, label):
    e, output = html.escape, row["output"]
    source = row["export_source"]
    provenance = "旧记录复用" if source["origin"] == "reused" else "本轮生成"
    return (f'<section><b>{e(label)}</b><pre>{e(output["raw_text"])}</pre>'
            f'<small>{len(output["token_ids"])} token · {e(output["end_reason"])} · {provenance}</small>'
            f'<details><summary>正文、token及来源</summary><pre>{e(output["answer_text"])}</pre>'
            f'<pre>{e(json.dumps(output["token_ids"]))}</pre><small>{e(source["record"])}<br>'
            f'文件 SHA-256: {e(source["record_sha256"])}<br>token SHA-256: {e(output["token_sha256"])}</small></details></section>')


def export(runs, output):
    records, receipts = load_runs(runs)
    mode = receipts[0]["receipt"]["mode"]
    _contract, questions, selection = survey.load_design()
    groups, sources = groups_for(records, receipts, questions, selection, mode)
    unique = records + sources if mode == "survey" else records
    assert len({r["export_source"]["record"] for r in unique}) == len(unique), "Repeated unique source"
    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=False)
    for name, rows in (("all.records.jsonl", unique), ("reused.sources.jsonl", sources)):
        with (destination / name).open("w", encoding="utf-8") as stream:
            for row in rows:
                stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    index = [{**{k: v for k, v in group.items() if k != "rows"},
              "doses": [{"dose": dose, **row["export_source"]} for dose, row in zip(DOSES, group["rows"])]} for group in groups]
    survey.io.write(destination / "comparison_index.json", index)
    full = {(r["receipt"]["model_id"], r["receipt"]["shard"], r["receipt"]["shards"]) for r in receipts} == WORKERS
    title = "五档剂量调查：704组六栏完整原文" if mode == "survey" else "GPU 验收原文及剂量样例（非正式调查结果）"
    parts = [f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>{title}</title>
<style>body{{font:16px/1.6 system-ui,sans-serif;margin:24px;color:#1f2937}}.six{{display:grid;grid-template-columns:repeat(6,minmax(240px,1fr));gap:12px;overflow-x:auto}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit;background:#f3f4f6;padding:12px}}section{{min-width:0}}small{{color:#596272}}article{{border-top:1px solid #ccc;margin-top:24px}}nav a{{margin-right:12px}}</style>
<h1>{title}</h1><p>完整保留raw、正文和实际token，不截断显示、不评分。原版按组重复显示，但只按唯一来源计数。短于128且正常EOS结束的原文不补齐。</p>
<p>{'3544份唯一科学来源：24份旧原版、704份旧dose=1、2816份新回答。' if mode == 'survey' else f'{len(records)}份工程验收记录；{len(groups)}组六栏样例不代表正式704组完成，不作科学重复。'} </p>
<p><a href="all.records.jsonl">全部唯一记录</a> · <a href="reused.sources.jsonl">复用来源原文</a> · <a href="comparison_index.json">六栏来源索引</a> · <a href="annotations.blank.csv">自由观察表</a></p><nav>''']
    parts.extend(f'<a href="#group-{i}">{g["model_id"]} L{g["layer"]} N{g["channel"]} {g["question_id"]}</a>' for i, g in enumerate(groups))
    parts.append('</nav>')
    for i, group in enumerate(groups):
        parts.append(f'<article id="group-{i}"><h2>{group["model_id"]} · L{group["layer"]} / N{group["channel"]} · {group["question_id"]}</h2><p>{html.escape(group["rows"][0]["prompt"])}</p><div class="six">')
        parts.extend(cell(row, "原版 0" if dose == 0 else f"剂量 {dose:g}") for dose, row in zip(DOSES, group["rows"]))
        parts.append('</div></article>')
    if mode == "preflight":
        parts.append('<h2>全部工程验收记录</h2>')
        for row in records:
            parts.append(f'<details><summary>{row["model_id"]} / worker {row["export_source"]["worker_shard"]} / {html.escape(row["condition_id"])} / {row["question_id"]}</summary>')
            parts.append(cell(row, row["kind"]) + '</details>')
    parts.append('</html>')
    (destination / "paired_raw.html").write_text("\n".join(parts), encoding="utf-8")
    with (destination / "annotations.blank.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.writer(stream)
        writer.writerow(["model_id", "layer", "channel", "question_id", "自由观察", "反例与不确定性", "来源备注"])
        writer.writerows([[g["model_id"], g["layer"], g["channel"], g["question_id"], "", "", ""] for g in groups])
    receipt = {"status": "completed", "mode": mode, "whole_survey_complete": mode == "survey",
               "whole_preflight_complete": mode == "preflight" and full and len(records) == 126,
               "counts": {"new_records": len(records), "reused_sources": len(sources), "unique_records": len(unique),
                          "comparison_groups": len(groups), "scientific_records": len(unique) if mode == "survey" else 0},
               "source_receipts": receipts, "files": {p.name: survey.io.sha(p) for p in sorted(destination.iterdir())}}
    survey.io.write(destination / "export_receipt.json", receipt)
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = export(args.runs, args.output)
    print(json.dumps({"status": result["status"], "mode": result["mode"], "counts": result["counts"]}))
