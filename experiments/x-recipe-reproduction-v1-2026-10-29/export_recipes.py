"""Validate a complete frozen collection and export every raw response; stdlib only."""
import argparse
import html
import json
from pathlib import Path

import run_recipes as runner

OUTPUTS = ("paired_raw.html", "original.raw.jsonl", "modified.raw.jsonl", "export_receipt.json")


def load_complete(runs):
    if not __debug__:
        raise RuntimeError("Run without -O: the frozen runner's integrity checks use assertions")
    runs = [Path(path).resolve() for path in runs]
    assert 1 <= len(runs) <= 2 and len(set(runs)) == len(runs), "Supply one complete run or two distinct shards"
    contract, recipes, questions, _ = runner.design()
    identity = runner.check_freeze()
    records, receipts, metadata, evidence, shards = {}, [], [], {}, set()
    for run in runs:
        assert (run / "receipt.json").is_file(), f"Missing run receipt: {run}"
        receipt = runner.verify(run)  # Imports only class definitions, never constructs/loads a model.
        assert receipt["mode"] == "run" and receipt["experiment"] == runner.HERE.name
        assert receipt["freeze_sha256"] == identity
        assert receipt["shards"] == len(runs) and receipt["shard"] not in shards, "Duplicate/missing shard"
        shards.add(receipt["shard"])
        assert receipt["expected_records"] == receipt["completed_records"] == len(receipt["jobs"])
        receipts.append({"run": str(run), "receipt_sha256": runner.io.sha(run / "receipt.json"), "receipt": receipt})
        metadata.append(runner.io.read(run / "metadata.json"))
        for relative in ["receipt.json", "metadata.json", *receipt["record_hashes"]]:
            evidence[str(run / relative)] = runner.io.sha(run / relative)
        for rid, _, qid, _ in receipt["jobs"]:
            key = (rid, qid)
            assert key not in records, f"Duplicate record: {key}"
            relative = f"records/{rid}__{qid}.json"
            row = runner.io.read(run / relative)
            out = row["output"]
            assert all(type(token) is int and token >= 0 for token in out["token_ids"])
            assert isinstance(out["raw_text"], str) and isinstance(out["answer_text"], str)
            assert type(out["returned_padding_count"]) is int and out["returned_padding_count"] >= 0
            records[key] = {**row, "source_run": str(run), "source_record": relative,
                            "source_sha256": receipt["record_hashes"][relative]}
    assert shards == set(range(len(runs))), "Incomplete shard set"
    jobs = runner.schedule(recipes, questions)
    assert set(records) == {(rid, qid) for rid, _, qid, _ in jobs}, "Collection is not the complete frozen schedule"
    for key in ("model_id", "revision", "dtype", "versions", "target_weight_sha256_before",
                "effective_stop_tokens", "enable_thinking", "attention_backend"):
        assert all(item[key] == metadata[0][key] for item in metadata), f"Different shard metadata: {key}"
    assert metadata[0]["model_id"] == contract["model"]["id"]
    assert metadata[0]["revision"] == contract["model"]["revision"]
    assert metadata[0]["dtype"] == contract["model"]["dtype"]
    assert metadata[0]["attention_backend"] == contract["model"]["attention"]
    assert all(metadata[0]["versions"][key] == value for key, value in contract["versions"].items())
    assert metadata[0]["enable_thinking"] is contract["generation"]["enable_thinking"] is False
    assert contract["generation"]["max_new_tokens"] == 128
    assert set(metadata[0]["effective_stop_tokens"]) == {str(token) for token in contract["generation"]["eos_token_ids"]}
    pairs = []
    for recipe in recipes:
        bid = runner.baseline_id(runner.effective_generation(recipe))
        for qid in recipe["question_ids"]:
            original, modified = records[(bid, qid)], records[(recipe["id"], qid)]
            assert all(original[key] == modified[key] for key in ("prompt", "context", "baseline_id")), "Mismatched paired input"
            assert all(original["output"][key] == modified["output"][key] for key in
                       ("input_token_sha256", "effective_generation", "max_new_tokens")), "Mismatched paired settings"
            assert original["calibration"]["input_token_count"] == modified["calibration"]["input_token_count"]
            pairs.append((recipe, original, modified))
    frozen = runner.io.read(runner.HERE / "freeze.json")
    evidence.update({str(runner.REPO / name): digest for name, digest in frozen["files"].items()})
    evidence[str(runner.HERE / "freeze.json")] = identity
    ordered = [records[(rid, qid)] for rid, _, qid, _ in jobs]
    return recipes, ordered, pairs, receipts, evidence


def render(recipes, pairs):
    escape = html.escape
    parts = ['''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Acupuncture 配方并排原文</title>
<style>body{font:16px/1.6 system-ui,sans-serif;max-width:1500px;margin:auto;padding:24px;color:#17212b}input{font:inherit;padding:8px;width:min(95%,650px)}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit;background:#f3f5f7;padding:14px}article{border-top:1px solid #ddd;margin-top:20px}summary{cursor:pointer;font-weight:600}small{color:#536273}details.recipe{margin:28px 0}details[hidden]{display:none}@media(max-width:700px){.pair{grid-template-columns:1fr}body{padding:12px}}</style>
<h1>Acupuncture：全部配方并排原文</h1>''',
             f'<p>{len(recipes)} 个配方条件，每个 5 道题，共 {len(pairs)} 对回答；每次最多 128 个新 token。全部原样保留，不进行内容分析、评分或筛选。</p>',
             '<p>左侧是相同题目、相同解码设置的原版；右侧是配方版。length_limit 表示达到输出上限。原文包括生成记录中的特殊 token。</p>',
             '<p><a href="original.raw.jsonl">原版完整记录</a> · <a href="modified.raw.jsonl">配方完整记录</a> · <a href="export_receipt.json">完整性回执</a></p>',
             '<label for="filter">按配方 ID 或标签查找</label><br><input id="filter" type="search" placeholder="输入 ID 或标签；留空显示全部"><p id="visible"></p>']
    grouped = {recipe["id"]: [] for recipe in recipes}
    for recipe, original, modified in pairs:
        grouped[recipe["id"]].append((original, modified))
    for recipe in recipes:
        rid, label = recipe["id"], recipe.get("label", recipe.get("name", recipe["id"]))
        parts.append(f'<details class="recipe" data-search="{escape(rid + " " + label, quote=True)}" open><summary>{escape(rid)} · {escape(label)}</summary>')
        settings = {"interventions": recipe["interventions"], "normalization": recipe.get("normalization", "fixed_reference"),
                    "generation": runner.effective_generation(recipe)}
        parts.append('<details><summary>固定设置</summary><pre>' + escape(json.dumps(settings, ensure_ascii=False, indent=2)) + '</pre></details>')
        for original, modified in grouped[rid]:
            parts.append(f'<article><h3>{escape(modified["question_id"])}</h3><pre>{escape(modified["prompt"])}</pre><div class="pair">')
            for title, row in (("原版", original), ("配方版", modified)):
                out = row["output"]
                parts.append(f'<section><b>{title}</b><pre>{escape(out["raw_text"])}</pre><small>{out["generated_token_count"]} token · {escape(out["end_reason"])}</small></section>')
            parts.append('</div></article>')
        parts.append('</details>')
    parts.append('''<script>
const filter=document.getElementById('filter'), cards=[...document.querySelectorAll('details.recipe')];
function search(){const query=filter.value.toLocaleLowerCase();let count=0;for(const card of cards){card.hidden=!card.dataset.search.toLocaleLowerCase().includes(query);count+=!card.hidden;}document.getElementById('visible').textContent=`显示 ${count} / ${cards.length} 个配方`;}
filter.addEventListener('input',search);search();
</script></html>''')
    return "\n".join(parts)


def export(runs, output):
    destination = Path(output).resolve()
    assert not any((destination / name).exists() for name in OUTPUTS), "Export files already exist; never overwrite"
    recipes, records, pairs, receipts, evidence = load_complete(runs)
    original = [row for row in records if row["recipe_id"].startswith("baseline-")]
    modified = [row for row in records if not row["recipe_id"].startswith("baseline-")]
    payloads = {"paired_raw.html": render(recipes, pairs)}
    for name, rows in (("original.raw.jsonl", original), ("modified.raw.jsonl", modified)):
        payloads[name] = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows)
    destination.mkdir(parents=True, exist_ok=True)
    for name, text in payloads.items():
        with (destination / name).open("x", encoding="utf-8") as stream:
            stream.write(text)
    receipt = {"status": "completed", "exported_utc": runner.io.utc(), "whole_frozen_schedule_complete": True,
               "counts": {"recipes": len(recipes), "questions_per_recipe": 5, "pairs": len(pairs),
                          "original_records": len(original), "modified_records": len(modified), "all_records": len(records)},
               "scope": "All records from the complete frozen schedule; no semantic selection or scoring",
               "source_receipts": receipts, "input_file_sha256": evidence,
               "exporter_sha256": runner.io.sha(Path(__file__)),
               "files": {name: runner.io.sha(destination / name) for name in payloads}}
    runner.io.immutable(destination / "export_receipt.json", receipt)
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", nargs="+", default=[runner.HERE / "run-gpu0-r01", runner.HERE / "run-gpu1-r01"])
    parser.add_argument("--output", type=Path, default=runner.HERE)
    args = parser.parse_args()
    try:
        result = export(args.runs, args.output)
    except (AssertionError, KeyError, OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"Export failed: {error}\n")
    print(json.dumps({"status": result["status"], "counts": result["counts"], "output": str(args.output)}, ensure_ascii=False))
