import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import export_survey as exporter


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.verify_patch = patch.object(exporter.survey, "verify")
        self.verify = self.verify_patch.start()

    def tearDown(self):
        self.temp.cleanup()
        self.verify_patch.stop()

    def run_fixture(self, name="run", mode="survey", modified=True):
        run = self.root / name
        (run / "records").mkdir(parents=True)
        baseline = {"status": "completed", "model_id": "2b", "condition_id": "baseline", "layer": None,
                    "channel": None, "question_id": "Q01", "prompt": "原题 <script>", "context": "模板",
                    "calibration": {}, "intervention": None,
                    "output": {"token_ids": [1, 2], "token_sha256": exporter.token_hash([1, 2]),
                               "raw_text": "原文\n<im_end>", "answer_text": "原文", "end_reason": "eos_token"}}
        rows = [baseline]
        if modified:
            row = copy.deepcopy(baseline)
            row.update(condition_id="L00-N000123", layer=0, channel=123, intervention={"dose": 1})
            row["output"]["raw_text"] = '改变 <img src=x onerror="alert(1)"> & 原样'
            rows.append(row)
        for row in rows:
            (run / "records" / f'{row["condition_id"]}__Q01.json').write_text(json.dumps(row, ensure_ascii=False))
        receipt = {"status": "completed", "mode": mode, "model_id": "2b", "shard": 0, "shards": 1,
                   "freeze_sha256": "a" * 64,
                   "expected_record_ids": [f'{r["condition_id"]}__Q01' for r in rows],
                   "record_hashes": {f'records/{p.name}': exporter.sha(p) for p in (run / "records").glob("*.json")}}
        (run / "receipt.json").write_text(json.dumps(receipt))
        return run

    def change_record(self, run, name, transform):
        path = run / "records" / name
        row = json.loads(path.read_text())
        transform(row)
        path.write_text(json.dumps(row))
        receipt = json.loads((run / "receipt.json").read_text())
        receipt["record_hashes"][f"records/{name}"] = exporter.sha(path)
        (run / "receipt.json").write_text(json.dumps(receipt))

    def test_export_preserves_text_and_blind_view(self):
        run = self.run_fixture()
        receipt = exporter.export([run], self.root / "export")
        self.assertEqual(receipt["counts"], {"records": 2, "original": 1, "modified": 1, "conditions": 1})
        rows = [json.loads(line) for line in (self.root / "export/all.records.jsonl").read_text().splitlines()]
        self.assertEqual(rows[0]["output"]["raw_text"], '改变 <img src=x onerror="alert(1)"> & 原样')
        page = (self.root / "export/paired_raw.html").read_text()
        self.assertNotIn('<img src=x', page)
        self.assertIn('&lt;img src=x', page)
        self.assertIn('.identity{display:none}', page)
        self.assertIn('部分运行原文预览', page)
        self.assertFalse(receipt["whole_survey_complete"])
        self.verify.assert_called_once_with(run.resolve())
        self.assertIn("<im_end>", rows[1]["output"]["raw_text"])
        with self.assertRaises(FileExistsError):
            exporter.export([run], self.root / "export")

    def test_rejects_hash_or_manifest_loss(self):
        run = self.run_fixture()
        path = run / "records/baseline__Q01.json"
        original = path.read_text()
        path.write_text(original + " ")
        with self.assertRaisesRegex(ValueError, "Record hash"):
            exporter.load_runs([run])
        path.unlink()
        with self.assertRaisesRegex(ValueError, "coverage"):
            exporter.load_runs([run])

    def test_rejects_token_tampering_even_with_new_file_hash(self):
        run = self.run_fixture()
        self.change_record(run, "L00-N000123__Q01.json", lambda r: r["output"].update(token_ids=[5]))
        with self.assertRaisesRegex(ValueError, "Token hash"):
            exporter.load_runs([run])

    def test_duplicate_baselines_preserved_conflicts_rejected(self):
        a, b = self.run_fixture("a"), self.run_fixture("b", modified=False)
        receipt = exporter.export([a, b], self.root / "out")
        self.assertEqual(receipt["counts"]["original"], 2)
        self.change_record(b, "baseline__Q01.json", lambda r: r["output"].update(raw_text="不同"))
        with self.assertRaisesRegex(ValueError, "Conflicting baseline output"):
            exporter.load_runs([a, b])

    def test_preflight_label_and_mixed_mode_rejected(self):
        a = self.run_fixture("a", mode="preflight")
        exporter.export([a], self.root / "out")
        self.assertIn("非正式调查结果", (self.root / "out/paired_raw.html").read_text())
        b = self.run_fixture("b", mode="survey", modified=False)
        with self.assertRaisesRegex(ValueError, "separately"):
            exporter.load_runs([a, b])

    def test_duplicate_intervention_rejected(self):
        a, b = self.run_fixture("a"), self.run_fixture("b")
        with self.assertRaisesRegex(ValueError, "Duplicate intervention"):
            exporter.load_runs([a, b])

    def test_runner_verification_failure_propagates(self):
        run = self.run_fixture()
        self.verify.side_effect = AssertionError("Frozen question changed")
        with self.assertRaisesRegex(AssertionError, "Frozen question"):
            exporter.export([run], self.root / "out")
        self.assertFalse((self.root / "out").exists())

    def test_technical_controls_not_counted_as_positive_needles(self):
        run = self.run_fixture(mode="preflight")
        old = run / "records/L00-N000123__Q01.json"
        row = json.loads(old.read_text())
        row["condition_id"] = "zero-00"
        old.unlink()
        path = run / "records/zero-00__Q01.json"
        path.write_text(json.dumps(row))
        receipt = json.loads((run / "receipt.json").read_text())
        receipt["expected_record_ids"][1] = path.stem
        receipt["record_hashes"].pop("records/L00-N000123__Q01.json")
        receipt["record_hashes"]["records/" + path.name] = exporter.sha(path)
        (run / "receipt.json").write_text(json.dumps(receipt))
        result = exporter.export([run], self.root / "out")
        self.assertEqual(result["technical_control_answers"], 1)
        self.assertEqual(result["positive_needle_answers"], 0)


if __name__ == "__main__":
    unittest.main()
