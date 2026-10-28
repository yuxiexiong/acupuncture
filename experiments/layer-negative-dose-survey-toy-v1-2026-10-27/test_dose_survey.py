"""CPU design, provenance, generation-boundary and complete-export acceptance."""
import copy
import importlib.util
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

import dose_survey as survey
import export_dose_survey as exporter

OLD = survey.HERE.parent / "layer-survey-toy-v1-2026-10-27"


class DesignChecks(unittest.TestCase):
    def test_selection_reproduces_original_ten_without_reroll(self):
        contract, questions, selection = survey.load_design()
        samples = survey.io.read(OLD / "samples.json")
        points = selection["selected_channels"]
        self.assertEqual(len(points), 88)
        self.assertEqual(len({(p["model_id"], p["layer"]) for p in points}), 88)
        self.assertEqual(survey.io.sha(survey.HERE / "questions.json"), survey.io.sha(OLD / "questions.json"))
        self.assertEqual(contract["instruction"], survey.io.read(OLD / "contract.json")["instruction"])
        self.assertEqual(contract["generation"]["max_new_tokens"], 128)
        self.assertFalse(contract["generation"]["do_sample"])
        self.assertFalse(contract["generation"]["enable_thinking"])
        self.assertEqual([q["id"] for q in questions], [f"Q{i:02}" for i in range(1, 9)])
        self.assertEqual(tuple(contract["nonzero_doses"]), (-1 / 16, -1 / 8, -1 / 4, -1 / 2, -1.))
        self.assertEqual(survey.io.sha(survey.HERE / "selection.json"), survey.io.sha(survey.POSITIVE / "selection.json"))
        self.assertEqual(tuple(-d for d in survey.NEW_DOSES), tuple(selection["nonzero_doses"]))
        self.assertEqual(contract["comparison_doses"], list(exporter.DOSES))
        self.assertNotIn(-.75, survey.NEW_DOSES)
        for model in contract["models"]:
            chosen = [p for p in points if p["model_id"] == model["id"]]
            self.assertEqual([p["layer"] for p in chosen], list(range(model["layers"])))
            for point in chosen:
                candidates = sorted(c["channel"] for c in samples[model["id"]] if c["layer"] == point["layer"])
                self.assertEqual(len(candidates), 10)
                seed = f'acupuncture-layer-dose-v1:{model["id"]}:{point["layer"]}'
                self.assertEqual(point["candidate_channels"], candidates)
                self.assertEqual(point["seed"], seed)
                self.assertEqual(point["channel"], random.Random(seed).choice(candidates))
                self.assertEqual(point["proposed_worker"], point["layer"] % 2)

    def test_disjoint_formal_schedule_and_bounded_preflight(self):
        contract, questions, selection = survey.load_design()
        formal, preflight = [], []
        for model in contract["models"]:
            for shard in range(2):
                jobs = survey.schedule("survey", model, questions, selection, shard, 2)
                self.assertEqual(len(jobs), model["layers"] // 2 * 8 * 5)
                self.assertEqual({d for _, _, _, d in jobs}, set(survey.NEW_DOSES))
                self.assertTrue(all(p["layer"] % 2 == shard for _, p, _, _ in jobs))
                for point in {p["condition_id"] for _, p, _, _ in jobs}:
                    for dose in survey.NEW_DOSES:
                        self.assertEqual({q["id"] for _, p, q, d in jobs if p["condition_id"] == point and d == dose},
                                         {f"Q{i:02}" for i in range(1, 9)})
                formal.extend((model["id"], name, q["id"]) for name, _, q, _ in jobs)
                checks = survey.schedule("preflight", model, questions, selection, shard, 2)
                self.assertEqual(len(checks), 23)
                self.assertEqual(sum(name == "baseline" for name, _, _, _ in checks), 8)
                for prefix in ("replay-", "zero-", "restored-"):
                    self.assertEqual(sum(name.startswith(prefix) and not name.startswith("restored-negative-") for name, _, _, _ in checks), 3)
                owned = list(range(shard, model["layers"], 2))
                expected = list(zip((owned[0], owned[len(owned)//2], owned[-1]), ("Q01", "Q04", "Q08")))
                self.assertEqual([(p["layer"], q["id"]) for name, p, q, _ in checks if name.startswith("replay-")], expected)
                smoke = [(p["layer"], q["id"], d) for _, p, q, d in checks if d in survey.NEW_DOSES]
                self.assertEqual(smoke, [(owned[len(owned)//2], "Q04", d) for d in survey.NEW_DOSES])
                name, point, question, dose = checks[-1]
                self.assertEqual(name, f'restored-negative-{point["condition_id"]}')
                self.assertEqual((point["layer"], question["id"], dose), (owned[len(owned)//2], "Q04", None))
                preflight.extend((model["id"], shard, name, q["id"]) for name, _, q, _ in checks)
        self.assertEqual(len(formal), 3520)
        self.assertEqual(len(formal), len(set(formal)))
        self.assertEqual(len(preflight), 138)
        self.assertEqual(len(preflight), len(set(preflight)))

    def test_preflight_permission_cannot_authorize_formal(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "auth.json"
            survey.io.write(path, dict(experiment=survey.HERE.name, freeze_sha256="frozen", status="authorized",
                purpose="preflight", models=["2b"], gpus=[0], user_instruction="bounded test", recorded_utc="test",
                maximum_generations=138, maximum_workers=2, maximum_new_tokens_per_record=128,
                maximum_generated_tokens=138 * 128, formal_launch_confirmed=False))
            with patch.object(survey, "check_freeze", return_value="frozen"):
                survey.check_authorization(path, "preflight", "2b", 0, True)
                for mode, model, gpu, execute in (("survey", "2b", 0, True), ("preflight", "2b", 0, False),
                                                  ("preflight", "9b", 0, True), ("preflight", "2b", 1, True)):
                    with self.subTest(mode=mode, model=model, gpu=gpu, execute=execute), self.assertRaises(AssertionError):
                        survey.check_authorization(path, mode, model, gpu, execute)

    def test_freeze_detects_changed_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "input").write_text("fixed")
            survey.io.write(root / "freeze.json", {"experiment": root.name, "files": {"input": survey.io.sha(root / "input")}})
            with patch.object(survey, "HERE", root), patch.object(survey, "REPO", root):
                survey.check_freeze()
                (root / "input").write_text("changed")
                with self.assertRaises(AssertionError):
                    survey.check_freeze()

    def test_all_old_reused_sources_are_verified(self):
        contract, questions, selection = survey.load_design()
        sources = set()
        for model in contract["models"]:
            for q in questions:
                row, source = survey.source_record(model["id"], None, q["id"])
                sources.add(source["record"])
                self.assertEqual(row["output"]["token_sha256"], survey.token_hash(row["output"]["token_ids"]))
        for point in selection["selected_channels"]:
            for q in questions:
                row, source = survey.source_record(point["model_id"], point, q["id"])
                sources.add(source["record"])
                self.assertEqual(row["intervention"]["dose"], 1.)
                self.assertEqual(survey.io.sha(survey.REPO / source["record"]), source["record_sha256"])
        self.assertEqual(len(sources), 728)
        for relative, digest in selection["source_files_sha256"].items():
            self.assertEqual(survey.io.sha(survey.REPO / relative), digest)

    def test_full_positive_reference_keeps_original_hashes_and_is_all_reused(self):
        _, questions, selection = survey.load_design()
        reference, provenance = exporter.positive_reference(questions, selection)
        sources = {row["export_source"]["record"]: row for group in reference.values() for row in group.values()}
        self.assertEqual((len(reference), len(sources)), (704, 3544))
        self.assertEqual(provenance["unique_sources_verified"], 3544)
        self.assertTrue(all(r["export_source"]["origin"] == "reused" for r in sources.values()))
        self.assertEqual(sum(r["export_source"]["positive_export_origin"] == "new" for r in sources.values()), 2816)
        original_sha = survey.io.sha
        with patch.object(survey.io, "sha", side_effect=lambda p: "tampered" if Path(p).name == "all.records.jsonl" else original_sha(p)):
            with self.assertRaisesRegex(AssertionError, "Positive export hash mismatch"):
                exporter.positive_reference(questions, selection)

    def test_post_negative_restoration_requires_exact_historical_tokens_and_raw(self):
        contract, questions, selection = survey.load_design()
        model, question, point = contract["models"][0], questions[3], selection["selected_channels"][0]
        original, source = survey.source_record(model["id"], point, question["id"])
        baseline, _ = survey.source_record(model["id"], None, question["id"])
        condition = f'restored-negative-{point["condition_id"]}'
        row = copy.deepcopy(original)
        row.update(condition_id=condition, kind="restored", point_id=point["condition_id"], dose=0.,
                   source=source, intervention=None, output=copy.deepcopy(baseline["output"]))
        calibrations = {question["id"]: original["calibration"]}
        survey.check_record(row, model, condition, point, question, None, calibrations)
        row["output"]["raw_text"] += "changed"
        with self.assertRaisesRegex(AssertionError, "raw-text mismatch"):
            survey.check_record(row, model, condition, point, question, None, calibrations)
        row["output"] = copy.deepcopy(baseline["output"])
        row["output"]["token_ids"][0] += 1
        row["output"]["token_sha256"] = survey.token_hash(row["output"]["token_ids"])
        with self.assertRaisesRegex(AssertionError, "Zero/restoration mismatch"):
            survey.check_record(row, model, condition, point, question, None, calibrations)

    def test_decoder_keeps_eos_and_full_128_without_padding_or_rewriting(self):
        spec = importlib.util.spec_from_file_location("frozen_generation_test", survey.HERE.parent / "capability-damage-v2-2026-10-26/model_engine.py")
        engine = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(engine)
        decode = lambda tokens, skip_special_tokens: repr(tokens)
        for stop in (248044, 248046):
            result = engine.finish_generation([7, stop, 248044, 248044], [248044, 248046], 248044, 128, None, [], decode)
            self.assertEqual(result["token_ids"], [7, stop])
            self.assertEqual(result["generated_token_count"], 2)
            self.assertEqual(result["end_reason"], "eos_token")
        cap = list(range(128))
        result = engine.finish_generation(cap, [248044, 248046], 248044, 128, None, [], decode)
        self.assertEqual(result["token_ids"], cap)
        self.assertEqual(result["end_reason"], "length_limit")
        with self.assertRaises(AssertionError):
            engine.finish_generation(cap + [128], [248044, 248046], 248044, 128, None, [], decode)


class ExportChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.contract, self.questions, self.selection = survey.load_design()

    def tearDown(self):
        self.temp.cleanup()

    def row(self, model="2b", point=None, qid="Q04", dose=0., shard=0, origin="new", kind="dose"):
        prompt = next(q["prompt"] for q in self.questions if q["id"] == qid)
        point_id = point["condition_id"] if point else "baseline"
        condition = "D" + str(float(dose)).replace(".", "p") if point and dose else "baseline"
        tokens = [7] * 127 + [248046]
        return {"status": "completed", "model_id": model, "condition_id": f"{point_id}-{condition}" if point else condition,
                "point_id": point_id if point else None, "layer": point["layer"] if point else None,
                "channel": point["channel"] if point else None, "question_id": qid, "dose": dose, "kind": kind,
                "prompt": prompt, "context": prompt, "calibration": {},
                "intervention": {"dose": dose, "column_norm": 2., "requested_offset": dose / 2, "bf16_offset": dose / 2} if point else None,
                "output": {"token_ids": tokens, "token_sha256": survey.token_hash(tokens), "generated_token_count": 128,
                           "max_new_tokens": 128, "input_token_sha256": "input-fixed", "end_reason": "eos_token",
                           "raw_text": '<img src=x onerror="alert(1)">\n完整末尾 END <|im_end|>', "answer_text": "完整末尾 END"},
                "export_source": {"origin": origin, "record": f"{origin}/{model}/{shard}/{point_id}/{qid}/{dose}.json",
                                  "record_sha256": "a" * 64, "worker_shard": shard}}

    def positive_reference(self, questions, selection):
        lookup = {}
        for point in selection["selected_channels"]:
            for q in questions:
                lookup[(point["model_id"], point["condition_id"], q["id"])] = {
                    d: self.row(point["model_id"], point if d else None, q["id"], d, None, "reused")
                    for d in (0., *exporter.POSITIVE_DOSES)}
        return lookup, {"synthetic_reference": True}

    def receipt(self, model, shard, mode):
        return {"receipt": {"model_id": model, "shard": shard, "shards": 2, "mode": mode, "freeze_sha256": "frozen"}}

    def test_full_formal_export_has_7064_unique_sources_and_704_eleven_columns(self):
        records, receipts = [], []
        for model in self.contract["models"]:
            for shard in range(2):
                receipts.append(self.receipt(model["id"], shard, "survey"))
                records.extend(self.row(model["id"], point, q["id"], dose, shard)
                               for _, point, q, dose in survey.schedule("survey", model, self.questions, self.selection, shard, 2))
        with patch.object(exporter, "load_runs", return_value=(records, receipts)), patch.object(exporter, "positive_reference", side_effect=self.positive_reference):
            result = exporter.export(["synthetic"], self.root / "formal")
            self.assertEqual(result["counts"], {"new_records": 3520, "reused_sources": 3544, "unique_records": 7064,
                                               "comparison_groups": 704, "scientific_records": 7064})
            self.assertTrue(result["whole_survey_complete"])
            with self.assertRaises(FileExistsError):
                exporter.export(["synthetic"], self.root / "formal")
        index = survey.io.read(self.root / "formal/comparison_index.json")
        self.assertTrue(all([d["dose"] for d in group["doses"]] == [-1., -.5, -.25, -.125, -.0625, 0., .0625, .125, .25, .5, 1.] for group in index))
        rows = [json.loads(line) for line in (self.root / "formal/all.records.jsonl").read_text().splitlines()]
        self.assertEqual(len(rows), 7064)
        self.assertEqual(sum(r["export_source"]["origin"] == "new" for r in rows), 3520)
        self.assertTrue(all(len(row["output"]["token_ids"]) == 128 for row in rows))
        page = (self.root / "formal/paired_raw.html").read_text()
        self.assertEqual(page.count('class="eleven"'), 704)
        self.assertNotIn('<img src=x', page)
        self.assertIn('&lt;img src=x', page)
        self.assertIn('完整末尾 END', page)
        self.assertNotIn('text-overflow', page)

    def test_partial_formal_run_cannot_be_labeled_complete(self):
        with self.assertRaisesRegex(AssertionError, "six complete"):
            exporter.groups_for([], [self.receipt("2b", 0, "survey")], self.questions, self.selection, "survey")

    def test_138_preflight_rows_are_separate_from_six_sample_groups(self):
        records, receipts = [], []
        for model in self.contract["models"]:
            for shard in range(2):
                receipts.append(self.receipt(model["id"], shard, "preflight"))
                for condition, point, q, dose in survey.schedule("preflight", model, self.questions, self.selection, shard, 2):
                    row = self.row(model["id"], point, q["id"], dose or 0., shard,
                                   kind="dose" if dose in survey.NEW_DOSES else condition.split("-")[0])
                    row["condition_id"] = condition
                    row["export_source"]["record"] = f'new/{model["id"]}/{shard}/{condition}__{q["id"]}.json'
                    records.append(row)
        with patch.object(exporter, "load_runs", return_value=(records, receipts)), patch.object(exporter, "positive_reference", side_effect=self.positive_reference):
            result = exporter.export(["synthetic"], self.root / "preflight")
        self.assertTrue(result["whole_preflight_complete"])
        self.assertFalse(result["whole_survey_complete"])
        self.assertEqual(result["counts"]["scientific_records"], 0)
        self.assertEqual(result["counts"]["unique_records"], 138)
        self.assertEqual(result["counts"]["comparison_groups"], 6)
        self.assertEqual(result["counts"]["reused_sources"], 33)
        self.assertEqual(len((self.root / "preflight/all.records.jsonl").read_text().splitlines()), 138)
        page = (self.root / "preflight/paired_raw.html").read_text()
        self.assertIn("非正式调查结果", page)
        self.assertIn("全部工程验收记录", page)
        self.assertEqual(page.count('class="eleven"'), 6)

    def test_record_file_token_hash_and_128_budget_reject_tampering(self):
        path = self.root / "record.json"
        row = self.row()
        survey.io.write(path, row)
        original_hash = survey.io.sha(path)
        self.assertEqual(exporter.checked_row(path, original_hash, "new")["output"]["token_ids"], row["output"]["token_ids"])
        path.write_text(path.read_text() + " ")
        with self.assertRaisesRegex(AssertionError, "Source record hash"):
            exporter.checked_row(path, original_hash, "new")
        for tokens, digest in (([8], row["output"]["token_sha256"]), ([7] * 129, survey.token_hash([7] * 129))):
            changed = copy.deepcopy(row)
            changed["output"].update(token_ids=tokens, generated_token_count=len(tokens), token_sha256=digest)
            survey.io.write(path, changed)
            with self.assertRaises(AssertionError):
                exporter.checked_row(path, survey.io.sha(path), "new")
        short = copy.deepcopy(row)
        short["output"].update(token_ids=[7, 248046], generated_token_count=2, token_sha256=survey.token_hash([7, 248046]))
        survey.io.write(path, short)
        self.assertEqual(exporter.checked_row(path, survey.io.sha(path), "new")["output"]["token_ids"], [7, 248046])


if __name__ == "__main__":
    unittest.main()
