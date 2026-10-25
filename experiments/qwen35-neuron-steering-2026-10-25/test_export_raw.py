"""Synthetic data only: escaping, whitespace, all attempts, provenance and incomplete rejection."""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from export_raw import digest, export


class RawParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.values, self.active = [], None

    def handle_starttag(self, tag, attrs):
        if tag == "div" and dict(attrs).get("class") == "raw":
            self.active = ""

    def handle_data(self, data):
        if self.active is not None:
            self.active += data

    def handle_endtag(self, tag):
        if tag == "div" and self.active is not None:
            self.values.append(self.active)
            self.active = None


def main():
    with TemporaryDirectory(prefix="qwen-raw-export-synthetic-") as temporary:
        directory = Path(temporary)
        ids = [f"Q{index:02d}" for index in range(1, 41)]
        questions = [{"id": identifier, "prompt": f"合成问题 {identifier} <tag> &", "topic": "合成"} for identifier in ids]
        (directory / "questions.json").write_text(json.dumps({"questions": questions}, ensure_ascii=False))
        source_hashes, expected_texts, expected_by_arm = {}, [], {"baseline": [], "modified": []}
        for question in questions:
            record = {**question, "status": "completed", "input": {"synthetic": True}, "attempts": []}
            for index, budget in enumerate((512, 1024) if question["id"] == "Q01" else (512,), 1):
                attempt = {"max_new_tokens": budget}
                for arm in ("baseline", "modified"):
                    text = f'\n  {question["id"]} {arm} {index}\t<script>alert("x")</script> & <think>\r\n第二行  \n'
                    response = {"status": "completed", "raw_text": text, "token_ids": [1, budget],
                                "token_sha256": hashlib.sha256(f"[1,{budget}]".encode()).hexdigest(),
                                "generated_token_count": 2, "synthetic_extra_field": {"kept": True}}
                    attempt[arm] = response
                    expected_texts.append(text)
                    expected_by_arm[arm].append(response)
                record["attempts"].append(attempt)
            path = directory / f'{question["id"]}.json'
            path.write_text(json.dumps(record, ensure_ascii=False))
            source_hashes[question["id"]] = digest(path)
        receipt = {"status": "completed", "expected_question_ids": ids, "completed_questions": ids,
                   "question_statuses": dict.fromkeys(ids, "completed"), "question_record_sha256": source_hashes,
                   "question_file_sha256": digest(directory / "questions.json")}
        (directory / "receipt.json").write_text(json.dumps(receipt))
        result = export(directory)
        assert (result["question_count"], result["attempt_count"], result["raw_response_count"]) == (40, 41, 82)
        document = (directory / "paired_raw.html").read_text()
        assert "<script>" not in document and "&lt;script&gt;" in document
        assert '<section id="Q01">' in document and "技术结束状态：未记录" in document
        parser = RawParser()
        parser.feed(document)
        assert parser.values == expected_texts
        for arm, name in (("baseline", "original.raw.jsonl"), ("modified", "modified.raw.jsonl")):
            rows = [json.loads(line) for line in (directory / name).read_text().splitlines()]
            assert [row["response"] for row in rows] == expected_by_arm[arm]
            assert [row["question"]["id"] for row in rows] == ["Q01", *ids]
            assert rows[0]["attempt_index"] == 1 and rows[1]["attempt_index"] == 2
        receipt["status"] = "failed"
        (directory / "receipt.json").write_text(json.dumps(receipt))
        try:
            export(directory)
            raise RuntimeError("Incomplete collection was accepted")
        except AssertionError:
            pass
        # A separate stop receipt may authorize precisely the completed first 24.
        for question in questions[24:]:
            (directory / f'{question["id"]}.json').write_text(json.dumps({**question, "status": "pending", "attempts": []}))
        receipt.update({"status": "started", "completed_questions": ids[:24]})
        receipt.pop("question_statuses")
        receipt.pop("question_record_sha256")
        (directory / "receipt.json").write_text(json.dumps(receipt))
        stop_directory = directory / "stop-after-q24"
        stop_directory.mkdir()
        stop_path = stop_directory / "receipt.json"
        stopped = {"status": "stopped_after_Q24", "completed_questions": ids[:24],
                   "Q25_Q40_not_started": True, "Q25_original_restored": True,
                   "question_record_sha256": {identifier: digest(directory / f"{identifier}.json") for identifier in ids}}
        stop_path.write_text(json.dumps(stopped))
        untouched = {path: path.read_bytes() for path in [directory / "receipt.json", directory / "questions.json", stop_path,
                                                         *(directory / f"{identifier}.json" for identifier in ids)]}
        try:
            export(directory)
            raise RuntimeError("Partial collection accepted without explicit stop receipt")
        except AssertionError:
            pass
        result = export(directory, stop_path)
        assert (result["question_count"], result["attempt_count"], result["raw_response_count"]) == (24, 25, 50)
        assert result["effective_scope"]["last_question_number"] == 24
        assert result["run_receipt_sha256"] == digest(directory / "receipt.json")
        assert result["stop_receipt_sha256"] == digest(stop_path)
        document = (directory / "paired_raw.html").read_text()
        assert "前24题全部原始回答" in document and "Q25" not in document
        parser = RawParser()
        parser.feed(document)
        assert parser.values == expected_texts[:50]
        for arm, name in (("baseline", "original.raw.jsonl"), ("modified", "modified.raw.jsonl")):
            rows = [json.loads(line) for line in (directory / name).read_text().splitlines()]
            assert [row["response"] for row in rows] == expected_by_arm[arm][:25]
            assert [row["question"]["id"] for row in rows] == ["Q01", *ids[:24]]
        assert all(path.read_bytes() == content for path, content in untouched.items())
        # A changed pending record must fail the recorded hash check.
        q25 = directory / "Q25.json"
        pending = json.loads(q25.read_text())
        pending["status"] = "running"
        q25.write_text(json.dumps(pending))
        try:
            export(directory, stop_path)
            raise RuntimeError("Changed pending record accepted")
        except AssertionError:
            pass
        # Even a matching hash cannot authorize a later question that has started.
        stopped["question_record_sha256"]["Q25"] = digest(q25)
        stop_path.write_text(json.dumps(stopped))
        try:
            export(directory, stop_path)
            raise RuntimeError("Started Q25 accepted")
        except AssertionError:
            pass
    print("PASS: synthetic escaping/whitespace, all attempts, exact JSONL fields, full40 and explicit stopped24 scopes, untouched sources, invalid-stop rejection")


if __name__ == "__main__":
    main()
