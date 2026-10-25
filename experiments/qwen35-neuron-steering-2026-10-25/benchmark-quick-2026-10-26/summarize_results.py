"""Verify completed local benchmark artifacts, then export scores and paired answers."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
from html import escape
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from benchmark_quick import forced_letter_result, parse_answer, summarize

NAMES = {"race": "RACE", "gsm8k": "GSM8K", "logiqa2": "LogiQA 2.0"}
STOPS = {"248044": "<|endoftext|>", "248046": "<|im_end|>"}


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def object_sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def verify(root):
    manifest, items = read(root / "data_manifest.json"), read(root / "items.json")
    assert manifest["status"] == "fixed_before_model_outputs" and manifest["seed"] == 20261026
    assert sha(root / "items.json") == manifest["items_sha256"]
    assert sha(root / "prepare_data.py") == manifest["preparation_source_sha256"]
    for source in manifest["sources"]:
        assert sha(root / source["file"]) == source["sha256"]
    ids = [item["id"] for item in items]
    assert len(ids) == len(set(ids)) == 300 and ids == manifest["selected_ids"]
    full_items = {item["id"]: item for item in items}
    expected = {"race": 100, "gsm8k": 100, "logiqa2": 100}
    assert dict(Counter(item["benchmark"] for item in items)) == expected
    records, receipts, hashes = [], {}, {}
    for suffix in ("math", "reading-logic"):
        folder = root / f"results-{suffix}"
        receipt, partition = read(folder / "receipt.json"), read(root / f"items-{suffix}.json")
        assert receipt["status"] == "completed" and receipt["hooks_removed"] is True
        assert all(item == full_items[item["id"]] for item in partition)
        assert receipt["targets"] == [[14, 8949, 1.0], [13, 7956, -1.0]]
        assert receipt["items_sha256"] == sha(root / f"items-{suffix}.json") == sha(folder / "items.json")
        counts = dict(Counter(item["benchmark"] for item in partition))
        assert receipt["expected_counts"] == counts and receipt["completed_items"] == [item["id"] for item in partition]
        for name, digest in receipt["source_sha256"].items():
            assert sha(root.parent / name) == digest, f"Changed runner source: {name}"
        assert receipt["target_weight_sha256_before"] == receipt["target_weight_sha256_after"]
        assert receipt["identity_checks"]["initial_parameters_equal"] and receipt["identity_checks"]["parameter_storages_disjoint"]
        assert receipt["effective_stop_tokens"] == STOPS
        settings = receipt["settings"]
        assert settings["dtype"] == "bfloat16" and settings["attention_backend"] == "eager" and settings["seed"] == 0
        assert settings["do_sample"] is False and settings["enable_thinking"] is False
        assert settings.get("mcq_tokens", 64) == 64 and settings["gsm_tokens"] == 512
        checks = read(folder / "mechanical_checks.json")
        assert checks["status"] == "completed"
        if "batch_size" in settings:
            assert suffix == "math" and settings["batch_size"] == 16 and settings["padding_side"] == "left"
            assert checks["single_vs_batch_exact"] and not checks["single_vs_batch_mismatches"]
            for index in range(settings["batch_size"]):
                for label, outputs in checks["batched"].items():
                    assert outputs[index]["status"] == "completed" and outputs[index]["token_ids"] == checks["single"][index % 2][label][0]["token_ids"]
                assert all(checks["batched"][arm][index]["token_ids"] == checks["batched"]["baseline"][index]["token_ids"] for arm in ("unmodified_clone", "zero_dose_clone", "restored_clone"))
        else:
            assert all(value["status"] == "completed" for value in checks["outputs"].values())
            reference = checks["outputs"]["baseline"]["token_ids"]
            assert all(checks["outputs"][arm]["token_ids"] == reference for arm in ("unmodified_clone", "zero_dose_clone", "restored_clone"))
        paths = sorted(folder.glob("[0-9][0-9][0-9][0-9].json"))
        assert len(paths) == len(partition)
        local = []
        for index, (path, item) in enumerate(zip(paths, partition)):
            assert path.name == f"{index:04d}.json"
            row = read(path)
            assert row["status"] == "completed" and all(row[key] == value for key, value in item.items())
            assert set(row["outputs"]) == {"baseline", "evo"}
            input_hash = object_sha(row["input"]["tensors"])
            assert row["input"]["input_sha256"] == input_hash
            if "batch_size" in settings:
                mask = row["input"]["tensors"]["attention_mask"][0]
                assert mask == sorted(mask) and set(mask) <= {0, 1}
                assert [token for token, keep in zip(row["input"]["tensors"]["input_ids"][0], mask) if keep] == row["input"]["calibration_input_tensors"]["input_ids"][0]
            for output in row["outputs"].values():
                assert output["status"] == "completed" and output["input_sha256"] == input_hash
                tokens, budget = output["token_ids"], 512 if row["benchmark"] == "gsm8k" else 64
                assert 0 < len(tokens) == output["generated_token_count"] <= budget == output["max_new_tokens"]
                assert not any(str(token) in STOPS for token in tokens[:-1])
                ended = str(tokens[-1]) in STOPS
                assert output["end_reason"] == ("eos_token" if ended else "length_limit")
                assert ended or len(tokens) == budget
                if "batch_size" in settings:
                    returned, pad_count = output["batched_returned_token_ids"], output["returned_padding_count"]
                    assert returned == tokens + [receipt["pad_token_id"]] * pad_count and pad_count == len(returned) - len(tokens)
                assert output["raw_text"] == output["answer_text"] + (STOPS[str(tokens[-1])] if ended else "")
                parsed = parse_answer(output["answer_text"], row["benchmark"])
                assert output["parsed_answer"] == parsed
                assert output["correct"] == (parsed is not None and parsed == parse_answer(row["target"], row["benchmark"]))
                if row["benchmark"] != "gsm8k":
                    forced = output["first_token_forced_letter"]
                    logits = [forced["logits"][letter] for letter in "ABCD"]
                    assert all(math.isfinite(value) for value in logits)
                    assert forced == forced_letter_result(logits, row["target"])
                else:
                    assert "first_token_forced_letter" not in output
            local.append(row)
            hashes[str(path.relative_to(root))] = sha(path)
        assert summarize(local, counts) == read(folder / "summary.json")
        for name in ("receipt.json", "items.json", "mechanical_checks.json", "summary.json"):
            hashes[str((folder / name).relative_to(root))] = sha(folder / name)
        records.extend(local)
        receipts[suffix] = receipt
    assert len(records) == len({row["id"] for row in records}) == 300 and {r["id"] for r in records} == set(ids)
    assert receipts["math"]["base_revision"] == receipts["reading-logic"]["base_revision"] == "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"
    assert receipts["math"]["assets"] == receipts["reading-logic"]["assets"]
    records.sort(key=lambda row: ids.index(row["id"]))
    result = {"verification_status": "VERIFIED", "verified_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "100 fixed test items per benchmark; subset scores, not full benchmark scores", "seed": manifest["seed"],
              "question_count": 300, "response_count": 600, "benchmarks": summarize(records, expected)["benchmarks"],
              "run_elapsed_seconds": {name: r["elapsed_seconds"] for name, r in receipts.items()},
              "process_elapsed_seconds_sum": sum(r["elapsed_seconds"] for r in receipts.values()),
              "parallel_wall_span_seconds": (max(datetime.fromisoformat(r["ended_utc"]) for r in receipts.values()) - min(datetime.fromisoformat(r["started_utc"]) for r in receipts.values())).total_seconds(),
              "generation_seconds": {arm: sum(r["outputs"][arm]["seconds"] for r in records) for arm in ("baseline", "evo")},
              "receipts": receipts, "evidence_sha256": hashes, "summarizer_sha256": sha(Path(__file__))}
    return result, records


def render_html(records):
    cards = []
    for row in records:
        columns = []
        for arm, title in (("baseline", "原版"), ("evo", "EVO 动态干预版")):
            out = row["outputs"][arm]
            badge = "正确" if out["correct"] else "未解析" if out["parsed_answer"] is None else "错误"
            columns.append(f'<section><h3>{title} · {badge}</h3><p>{out["generated_token_count"]} tokens · {escape(out["end_reason"])}</p><pre>{escape(out["raw_text"])}</pre></section>')
        cards.append(f'<details><summary>{escape(row["id"])} · 标准答案：{escape(row["target"])}</summary><pre class="question">{escape(row["prompt"])}</pre><div class="pair">{"".join(columns)}</div></details>')
    return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Qwen3.5-4B 三基准原文对照</title><style>body{font:16px/1.6 system-ui;max-width:1400px;margin:24px auto;padding:0 16px;background:#f6f7f9;color:#19212d}details{background:white;border:1px solid #d5dae2;border-radius:8px;margin:12px 0;padding:14px}summary{cursor:pointer;font-weight:600;overflow-wrap:anywhere}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}section{min-width:0;padding:12px;border:1px solid #e0e4eb}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:14px/1.6 ui-monospace,monospace}.question{background:#eff3f8;padding:12px}@media(max-width:800px){.pair{grid-template-columns:1fr}}</style><h1>原版与 EVO：300 题完整原文</h1><p>每基准 100 题的固定英文子集；全部 600 条回答均保留。点击题目展开。徽标来自预先固定的严格答案解析，不是人工语义评分。</p>' + ''.join(cards) + '</html>'


def render_markdown(result):
    lines = ["# 三项英文基准快速对照", "", "## Material Passport", "", "Verification Status: VERIFIED", "Task: 2026-10-26 固定英文测试子集对照", "Evidence: 已复核输入、脚本、收据、逐题输出、停止条件与评分；不代表独立重跑。", "",
             "原版与 EVO 均从相同 Qwen3.5-4B 固定权重加载为独立实例。EVO 使用既定的 L14 N8949 +1、L13 N7956 −1 动态激活干预；原权重未改写。", "",
             "每基准 100 题，抽样种子 20261026。RACE 为 29 道初中与 71 道高中题，每篇文章最多一题；它不是对全部题目的均匀抽样。GSM8K、LogiQA 2.0 为测试行无放回抽样。以下均为子集成绩，不是完整官方基准成绩。", "",
             "BF16、eager attention、greedy、thinking 关闭、生成种子 0；选择题最多 64 token，数学题最多 512 token。停止条件同时包含 endoftext（248044）与 im_end（248046）。无效输出及截断保留在总分母中，无答案重试。",
             f'数学 batch size={result["receipts"]["math"]["settings"].get("batch_size", 1)}；阅读与逻辑 batch size=1。各基准内原版与 EVO 条件相同；批量数学逐题独立校准，EOS 后的返回填充不计入生成。', "",
             "| 基准 | 原版正确 / 总数 | EVO 正确 / 总数 | 原版准确率 | EVO 准确率 | EVO − 原版（百分点） |", "|---|---:|---:|---:|---:|---:|"]
    for key in NAMES:
        b = result["benchmarks"][key]
        lines.append(f'| {NAMES[key]} | {b["baseline"]["correct"]}/{b["n"]} | {b["evo"]["correct"]}/{b["n"]} | {b["baseline"]["accuracy"]:.1%} | {b["evo"]["accuracy"]:.1%} | {b["evo_minus_baseline_percentage_points"]:+.1f} |')
    lines += ["", "选择题首 token 诊断只读取首次 forward 的 A/B/C/D logits 并取其中最大值，不改变生成。这不是官方完整答案似然评测，也不是实际生成答案的正确率。", "", "| 基准 | 原版首 token 四选一 | EVO 首 token 四选一 | 原版无效 / 截断 | EVO 无效 / 截断 |", "|---|---:|---:|---:|---:|"]
    for key in NAMES:
        b = result["benchmarks"][key]
        def forced(arm):
            f = b[arm].get("first_token_forced_letter_accuracy")
            return f'{f["correct"]}/{f["n"]} ({f["correct"]/f["n"]:.1%})' if f else "不适用"
        lines.append(f'| {NAMES[key]} | {forced("baseline")} | {forced("evo")} | {b["baseline"]["invalid"]} / {b["baseline"]["truncated"]} | {b["evo"]["invalid"]} / {b["evo"]["truncated"]} |')
    lines += ["", "| 基准 | 原版对 → EVO 对 | 对 → 错 | 错 → 对 | 错 → 错 |", "|---|---:|---:|---:|---:|"]
    for key in NAMES:
        t = result["benchmarks"][key]["paired_transitions"]
        lines.append(f'| {NAMES[key]} | {t["1->1"]} | {t["1->0"]} | {t["0->1"]} | {t["0->0"]} |')
    lines += ["", f'两任务覆盖的实际墙钟跨度：{result["parallel_wall_span_seconds"] / 60:.2f} 分钟；两个进程各自耗时之和：{result["process_elapsed_seconds_sum"] / 60:.2f} 分钟（含加载、校验与机械检查，不能当作并行墙钟时间）。', "", "本表衡量当前设定下完成正常任务的表现；这些分数不能单独判定恶意、意图或所有数学／逻辑能力是否消失。", "", "[全部原文对照](paired_answers.html) · [结构化结果与证据哈希](RESULTS.json) · [数学原始结果](results-math/) · [阅读与逻辑原始结果](results-reading-logic/)", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    root = parser.parse_args().root.resolve()
    result, records = verify(root)
    (root / "RESULTS.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    (root / "RESULTS.zh-CN.md").write_text(render_markdown(result))
    (root / "paired_answers.html").write_text(render_html(records))
    print(json.dumps({"verification_status": result["verification_status"], "benchmarks": result["benchmarks"]}, ensure_ascii=False))
