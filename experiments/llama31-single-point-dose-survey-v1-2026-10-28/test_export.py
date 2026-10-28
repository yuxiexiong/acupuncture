import copy
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

import export_survey as exporter
import survey


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.point = {"id": "L00-N000123", "layer": 0, "channel": 123}
        self.rows = []
        for dose in exporter.DOSES:
            output = {"token_ids": [42, 128009], "token_sha256": exporter.token_hash([42, 128009]),
                      "input_token_sha256": "same-input", "generated_token_count": 2, "max_new_tokens": 128,
                      "raw_text": '<img src=x onerror="alert(1)"> & ' + "完整" * 2048 + "<|eot_id|>",
                      "answer_text": "正文", "end_reason": "eos_token"}
            self.rows.append({"status": "completed", "model_id": exporter.MODEL,
                "condition_id": "baseline" if dose == 0 else f'L00-N000123-D{dose}',
                "kind": "baseline" if dose == 0 else "dose", "point_id": None if dose == 0 else self.point["id"],
                "layer": None if dose == 0 else 0, "channel": None if dose == 0 else 123, "dose": dose,
                "question_id": "Q01", "prompt": "问题 <script>", "context": "固定模板", "calibration": {"m": 2},
                "intervention": None if dose == 0 else {"dose": dose, "column_norm": 2,
                    "clean_residual_scale": 2, "requested_offset": dose, "bf16_offset": dose},
                "output": output, "export_source": {"origin": "new", "record": "records/<test>.json", "record_sha256": "a" * 64}})

    def tearDown(self):
        self.temp.cleanup()

    def test_pair_order_and_full_html_escaping(self):
        rows = exporter.paired_rows(list(reversed(self.rows)), self.point, "Q01")
        self.assertEqual([r["dose"] for r in rows], list(exporter.DOSES))
        group = {"model_id": exporter.MODEL, "layer": 0, "channel": 123, "question_id": "Q01", "rows": rows}
        page = exporter.render([group])
        self.assertIn("完整" * 2048, page)
        self.assertIn("&lt;img src=x", page)
        self.assertNotIn("<img src=x", page)
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;|eot_id|&gt;", page)
        self.assertEqual(page.count("<section>"), 11)

    def test_missing_duplicate_or_nonmirror_dose_rejected(self):
        for rows in (self.rows[:-1], [*self.rows[:-1], self.rows[0]]):
            with self.assertRaises(AssertionError):
                exporter.paired_rows(rows, self.point, "Q01")
        bad = copy.deepcopy(self.rows)
        bad[0]["intervention"]["requested_offset"] = 1.0
        with self.assertRaisesRegex(AssertionError, "Requested dose"):
            exporter.paired_rows(bad, self.point, "Q01")

    def test_mismatched_context_or_calibration_rejected(self):
        for field, value in (("context", "另一个题面"), ("calibration", {"m": 3})):
            bad = copy.deepcopy(self.rows)
            bad[0][field] = value
            with self.assertRaises(AssertionError):
                exporter.paired_rows(bad, self.point, "Q01")

    def test_record_and_token_hash_checks(self):
        path = self.root / "record.json"
        path.write_text(json.dumps(self.rows[0]))
        digest = exporter.sha(path)
        self.assertEqual(exporter.checked_row(path, digest)["output"]["raw_text"], self.rows[0]["output"]["raw_text"])
        path.write_text(path.read_text() + " ")
        with self.assertRaisesRegex(AssertionError, "Record hash"):
            exporter.checked_row(path, digest)
        bad = copy.deepcopy(self.rows[0])
        bad["output"]["token_ids"] = [11, 128009]
        path.write_text(json.dumps(bad))
        with self.assertRaisesRegex(AssertionError, "Token hash"):
            exporter.checked_row(path, exporter.sha(path))

    def test_partial_preflight_or_verify_failure_never_exports(self):
        run = self.root / "run"
        (run / "records").mkdir(parents=True)
        receipt = {"status": "completed", "checks_passed": True, "mode": "survey", "model_id": exporter.MODEL,
                   "shard": 0, "shards": 2, "record_hashes": {}, "expected_record_ids": []}
        stub = types.SimpleNamespace(verify=lambda _run: receipt, load_design=survey.load_design)
        with patch.dict("sys.modules", {"survey": stub}):
            with self.assertRaisesRegex(AssertionError, "Incomplete formal worker"):
                exporter.export([run], self.root / "output")
            self.assertFalse((self.root / "output").exists())
            receipt["mode"] = "preflight"
            with self.assertRaisesRegex(AssertionError, "Only complete formal"):
                exporter.load_runs([run])
            with self.assertRaisesRegex(AssertionError, "both complete workers"):
                exporter.load_runs([])
            def failed(_run):
                raise AssertionError("Frozen identity failed")
            stub.verify = failed
            with self.assertRaisesRegex(AssertionError, "Frozen identity failed"):
                exporter.export([run], self.root / "output")

    def test_real_runner_specs_match_point_shards_on_every_layer(self):
        _contract, _questions, samples = survey.load_design()
        points = samples[exporter.MODEL]
        point_shards = {point["id"]: point["layer"] % 2 for point in points}
        seen = []
        for shard in (0, 1):
            jobs = survey.make_specs("survey", exporter.MODEL, shard)
            self.assertEqual(len(jobs), 1152)
            shard_points = {}
            for condition, point, _question, _dose in jobs:
                row = {"model_id": exporter.MODEL, "condition_id": condition,
                       "kind": "dose" if point else "baseline", "point_id": point["id"] if point else None}
                exporter.check_worker_row(row, shard, point_shards)
                if point and point["id"] not in shard_points:
                    shard_points[point["id"]] = point
                    with self.assertRaisesRegex(AssertionError, "Wrong point worker shard"):
                        exporter.check_worker_row(row, 1 - shard, point_shards)
            self.assertEqual(len(shard_points), 16)
            for layer in range(32):
                self.assertEqual(sum(p["layer"] == layer for p in shard_points.values()), 1 if layer%2==shard else 0)
            seen.append(set(shard_points))
        self.assertFalse(seen[0] & seen[1])
        self.assertEqual(seen[0] | seen[1], {p["id"] for p in points})

    def test_complete_one_point_per_layer_export_and_missing_source(self):
        _contract, questions, samples = survey.load_design()
        records=[]
        for question in questions:
            row=copy.deepcopy(self.rows[5]);row.update(question_id=question['id'],prompt=question['prompt'])
            records.append(row)
        for point in samples[exporter.MODEL]:
            for question in questions:
                for template in self.rows:
                    if template['dose']==0:continue
                    row=copy.deepcopy(template)
                    row.update(point_id=point['id'],layer=point['layer'],channel=point['channel'],question_id=question['id'],prompt=question['prompt'])
                    records.append(row)
        groups=exporter.groups_for(records,questions,samples)
        self.assertEqual(len(groups),256)
        self.assertTrue(all(len(g['rows'])==11 for g in groups))
        self.assertEqual(sum(len(g['rows']) for g in groups),2816)
        with self.assertRaisesRegex(AssertionError,'Incomplete formal source'):
            exporter.groups_for(records[:-1],questions,samples)


if __name__ == "__main__":
    unittest.main()
