"""Export every completed paired raw response, without inspecting its meaning."""
import argparse
import hashlib
import html
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def escape(text):
    # Character references preserve CR; div avoids pre's leading-newline removal.
    return html.escape(text, quote=True).replace("\r", "&#13;")


def export(directory, stop_receipt=None):
    receipt_path, questions_path = directory / "receipt.json", directory / "questions.json"
    receipt = json.loads(receipt_path.read_text())
    questions = json.loads(questions_path.read_text())["questions"]
    ids = [f"Q{number:02d}" for number in range(1, 41)]
    assert [question["id"] for question in questions] == ids
    assert receipt["expected_question_ids"] == ids
    assert digest(questions_path) == receipt["question_file_sha256"]
    assert sorted(path.stem for path in directory.glob("Q[0-9][0-9].json")) == ids
    source_hashes = {"receipt.json": digest(receipt_path), "questions.json": digest(questions_path)}
    if stop_receipt is None:
        assert receipt["status"] == "completed", "Collection is not complete"
        assert receipt["completed_questions"] == ids
        assert receipt["question_statuses"] == dict.fromkeys(ids, "completed")
        record_hashes = receipt["question_record_sha256"]
        title = "原版与修改版模型：全部原始回答"
    else:
        stopped = json.loads(stop_receipt.read_text())
        assert stopped["status"] == "stopped_after_Q24"
        assert stopped["completed_questions"] == receipt["completed_questions"] == ids[:24]
        assert stopped["Q25_Q40_not_started"] is True
        assert stopped["Q25_original_restored"] is True
        record_hashes = stopped["question_record_sha256"]
        assert set(record_hashes) == set(ids)
        source_hashes["stop_receipt.json"] = digest(stop_receipt)
        for question in questions:
            path = directory / f'{question["id"]}.json'
            source_hashes[path.name] = digest(path)
            assert source_hashes[path.name] == record_hashes[question["id"]]
        for question in questions[24:]:
            pending = json.loads((directory / f'{question["id"]}.json').read_text())
            assert pending["id"] == question["id"] and pending["prompt"] == question["prompt"]
            assert pending["status"] == "pending" and pending["attempts"] == []
        questions = questions[:24]
        title = "原版与修改版模型：前24题全部原始回答"
    sections, records = [], {"baseline": [], "modified": []}
    attempt_count = 0
    for question in questions:
        identifier = question["id"]
        path = directory / f"{identifier}.json"
        source_hashes[path.name] = digest(path)
        assert source_hashes[path.name] == record_hashes[identifier]
        record = json.loads(path.read_text())
        assert record["id"] == identifier and record["prompt"] == question["prompt"]
        assert record["status"] == "completed"
        assert [attempt["max_new_tokens"] for attempt in record["attempts"]] in ([512], [512, 1024])
        sections.append(f'<section id="{identifier}"><h2>{identifier}</h2><div class="question">{escape(record["prompt"])}</div>')
        common = {key: value for key, value in record.items() if key != "attempts"}
        for index, attempt in enumerate(record["attempts"], 1):
            attempt_count += 1
            attempt_metadata = {key: value for key, value in attempt.items() if key not in ("baseline", "modified")}
            sections.append(f'<h3>第 {index} 次（生成上限 {attempt["max_new_tokens"]} token）</h3><table><thead><tr><th>原版模型回答原文</th><th>修改版模型回答原文</th></tr></thead><tbody><tr>')
            for arm in ("baseline", "modified"):
                response = attempt[arm]
                assert response["status"] == "completed" and isinstance(response["raw_text"], str)
                assert isinstance(response["token_ids"], list)
                token_hash = hashlib.sha256(json.dumps(response["token_ids"], ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
                assert token_hash == response["token_sha256"]
                assert len(response["token_ids"]) == response["generated_token_count"]
                ending = {"eos_token": "模型结束标记", "length_limit": "达到长度上限", "other_stop": "其他停止"}.get(response.get("end_reason"), "未记录")
                sections.append(f'<td><div class="raw" data-question="{identifier}" data-attempt="{index}" data-arm="{arm}">{escape(response["raw_text"])}</div><p>技术结束状态：{ending}</p></td>')
                records[arm].append({"question": common, "attempt_index": index, "attempt": attempt_metadata,
                                     "arm": arm, "response": response, "source_question_record_sha256": source_hashes[path.name]})
            sections.append("</tr></tbody></table>")
        sections.append("</section>")

    document = '''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>EXPORT_TITLE</title>
<style>
body{margin:24px;font-family:system-ui,sans-serif;color:#111;background:#fff;line-height:1.6}
h1{font-size:24px}h2{font-size:21px}h3{font-size:16px;font-weight:normal}
section{margin:36px 0}table{width:100%;table-layout:fixed;border-collapse:collapse}
th,td{width:50%;border:1px solid #bbb;padding:12px;text-align:left;vertical-align:top}
.question,.raw{white-space:pre-wrap;overflow-wrap:anywhere;tab-size:8}
.raw{font-family:ui-monospace,monospace}
</style></head><body><h1>EXPORT_TITLE</h1>
'''.replace("EXPORT_TITLE", title) + "\n".join(sections) + "\n</body></html>\n"
    outputs = {"paired_raw.html": document}
    for arm, name in (("baseline", "original.raw.jsonl"), ("modified", "modified.raw.jsonl")):
        outputs[name] = "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records[arm])
    for name, content in outputs.items():
        (directory / name).write_text(content)
    export_receipt = {"question_count": len(questions), "attempt_count": attempt_count,
                      "responses_per_model": attempt_count, "raw_response_count": attempt_count * 2,
                      "source_sha256": source_hashes,
                      "output_sha256": {name: digest(directory / name) for name in outputs}}
    if stop_receipt is not None:
        export_receipt.update({"run_receipt_sha256": source_hashes["receipt.json"],
                               "stop_receipt_sha256": source_hashes["stop_receipt.json"],
                               "effective_scope": {"original_question_count": 40, "first_question_number": 1,
                                                   "last_question_number": 24, "question_count": 24}})
    (directory / "export_receipt.json").write_text(json.dumps(export_receipt, ensure_ascii=False, indent=2) + "\n")
    return export_receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="Completed collect_raw.py output directory")
    parser.add_argument("--stop-receipt", type=Path, help="Verified stopped_after_Q24 receipt; explicitly limits export to Q01–Q24")
    args = parser.parse_args()
    print(json.dumps(export(args.directory, args.stop_receipt), ensure_ascii=False))
