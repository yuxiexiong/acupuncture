"""CPU-only contract/gate and fake-run checks; these do not validate a real model."""
import argparse
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import run_root as runner
import freeze as freezer


CONTRACT = {
    "experiment": "test", "random_seed": 20261026, "random_pairs": 5,
    "diagnostic_doses": [1.0, .5], "torch_threads": 4,
    "source": {"intermediate_size": 9216, "dtype": "bfloat16", "torch_version": "test",
               "transformers_version": "test", "target_weight_sha256": {"13": "a", "14": "b"}},
    "candidate_budget": {"ranked": 8, "audit": 2, "total": 10},
    "dev_counts": {"mmlu": 1, "arc_challenge": 1},
}


class FakeEngine:
    loads = 0

    def __init__(self, *args, **kwargs):
        type(self).loads += 1
        self.metadata = {"dtype": "bfloat16", "versions": {"torch": "test", "transformers": "test"}}
        self.weight_hashes = {"13": "a", "14": "b"}
        self.counts = {"forward": 0, "calibration_forward": 0}

    def make_condition(self, name, dose=1.0, random_pair=None):
        return f"{name}@{dose:g}"

    def calibrate(self, contexts):
        self.counts["calibration_forward"] += len(contexts)
        return [{"context_sha256": runner.hashlib.sha256(context.encode()).hexdigest(),
                 "residual_scales": {"13": 1.0, "14": 1.0}} for context in contexts]

    def score_item(self, item, arm, calibration, **kwargs):
        self.counts["forward"] += 1
        return {"scores": [1, 0], "correct": 1, "margin": 1, "prediction": 0}

    def verify_unchanged(self):
        return {"hooks_removed": True, "parameter_gradients_absent": True}


class FunctionalFakeEngine(FakeEngine):
    """Exercise stage plumbing with known synthetic repair/replay behavior."""
    def score_item(self, item, arm, calibration, patch=None, capture=None):
        self.counts["forward"] += 1
        correct = arm.startswith("clean")
        content_sign = runner.SIGN_BY_CONTENT_SLOT[item.get("content_slot", 0)]
        observed_sign = content_sign if correct else -content_sign
        if patch and patch["mode"] == "donor":
            if "donor_context" in patch:
                if item["demand"] == "required":
                    correct = False
                    observed_sign = runner.SIGN_BY_CONTENT_SLOT[item["donor_content_slot"]]
            else:
                correct = patch["donor_arm"].startswith("clean")
                observed_sign = content_sign if correct else -content_sign
        target = item["target_index"]
        prediction = target if correct else item.get("donor_target_index", (target + 1) % len(item["choices"]))
        if not correct and prediction == target:
            prediction = (target + 1) % len(item["choices"])
        scores = [0.0] * len(item["choices"])
        scores[prediction] = 2.0
        observations = []
        for _ in item["choices"]:
            values = {}
            for reader in capture or []:
                vector = [2.0 * observed_sign] + [0.0] * 2559
                if "projection" in reader:
                    value = sum(a * b for a, b in zip(vector, reader["projection"]))
                else:
                    value = vector
                values[reader["component"]] = {"positions": [0], "values": [value]}
            observations.append(values)
        audits = []
        if patch:
            writes = {str(layer): {"nonzero_positions": 1} for layer in (13, 14)} if arm.startswith("AB") else {}
            audits = [[{"actual_source_writes": writes, "untouched_positions_identical": True,
                        "requested_delta_norm": [1.0], "actual_delta_norm": [1.0]}] for _ in item["choices"]]
        return {"scores": scores, "correct": int(prediction == target), "prediction": prediction,
                "margin": scores[target] - max(value for i, value in enumerate(scores) if i != target),
                "observations": observations, "patch_audit": audits}


class RunnerTests(unittest.TestCase):
    def test_exact_17_conditions_and_fixed_random_controls(self):
        engine = FakeEngine()
        arms = runner.conditions(engine, CONTRACT)
        self.assertEqual(len(arms), 17)
        self.assertEqual(set(arms), {"clean"} | {f"{name}_d{dose:g}" for dose in (1, .5)
            for name in ("A", "B", "AB", "R01", "R02", "R03", "R04", "R05")})
        self.assertEqual(runner.random_pairs(CONTRACT), runner.random_pairs(CONTRACT))
        self.assertTrue(all(p[13] != 7956 and p[14] != 8949 for p in runner.random_pairs(CONTRACT)))

    def test_rank_budget_and_audit_not_top_candidates(self):
        records = [{"id": task, "benchmark": task, "ranking": [{"component": f"L{15+i}.mlp", "positions": "prompt_last",
                    "predicted_repair": 20-i if task == "mmlu" else i, "active_position_count": 1}
                    for i in range(16)]} for task in ("mmlu", "arc_challenge")]
        selected = runner.select_candidates(records, CONTRACT)
        self.assertEqual(len(selected), 10)
        self.assertEqual(sum(row["selection"] == "ranked" for row in selected), 8)
        self.assertEqual(sum(row["selection"] == "audit" for row in selected), 2)
        self.assertEqual(len({row["component"] for row in selected}), 10)
        self.assertEqual(selected, runner.select_candidates(records, CONTRACT))

    def test_missing_scope_is_zero_with_fixed_task_denominator(self):
        rows = []
        for task in ("mmlu", "arc_challenge"):
            for i in range(2):
                rows.append({"id": f"{task}-{i}", "benchmark": task, "ranking": [
                    {"component": "L15.mlp", "positions": "prompt_last", "predicted_repair": 3,
                     "active_position_count": 1}] + ([{"component": "L16.mlp", "positions": "answer_tail",
                     "predicted_repair": 4, "active_position_count": 1}] if i == 0 else [])})
        selected = runner.select_candidates(rows, CONTRACT)
        tail = next(row for row in selected if row["positions"] == "answer_tail")
        self.assertEqual(tail["mean_predicted_repair"], {"mmlu": 2, "arc_challenge": 2})
        self.assertEqual(tail["question_denominator"], {"mmlu": 2, "arc_challenge": 2})

    def test_reader_gate_rejects_circularity_and_empty_scope(self):
        candidate = {"id": "C01", "component": "L15.mlp", "positions": "prompt_last"}
        value = {"family": "reading", "explanations": [{"candidate_id": "C01",
            "candidate_sha256": runner.digest(candidate), "hypothesis": "test", "task_relation": "test",
            "expected_direction": "test", "falsifier": "test", "reader": {"component": "L16.attention", "positions": "prompt_last"}}]}
        runner.validate_explanations(value, [candidate])
        value["explanations"][0]["reader"]["component"] = "L15.mlp"
        with self.assertRaises(ValueError):
            runner.validate_explanations(value, [candidate])
        candidate["positions"] = "answer_tail"
        with self.assertRaises(ValueError):
            runner.validate_explanations(value, [candidate])

    def test_receipt_hash_gate_rejects_modified_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "item.json").write_text("{}")
            runner.write(root / "receipt.json", {"status": "completed", "stage": "rank", "freeze_sha256": "f",
                "files": {"item.json": runner.sha(root / "item.json")}})
            runner.completed_receipt(root / "receipt.json", "rank", "f")
            (root / "item.json").write_text('{"changed":true}')
            with self.assertRaises(ValueError):
                runner.completed_receipt(root / "receipt.json", "rank", "f")

    def test_freeze_cannot_omit_the_contract_or_code(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "freeze.json"
            runner.write(path, {"schema_version": 1, "status": "prepared_not_model_validated",
                "model_execution_authorized": False, "files": {}})
            with self.assertRaises(ValueError):
                freezer.verify(path)

    def test_launch_gate_requires_actual_instruction(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "authorization.json"
            runner.write(path, {"status": "authorized", "experiment": "test"})
            with self.assertRaises(ValueError):
                runner.check_launch(path, CONTRACT)

    def test_nonmatched_control_is_a_technical_failure(self):
        item = {"id": "q", "continuations": [" A"]}
        output = {"patch_audit": [[{"actual_source_writes": {}, "untouched_positions_identical": True,
            "requested_delta_norm": [1.0], "actual_delta_norm": [1.05]}]]}
        with self.assertRaises(ValueError) as result:
            runner.check_patch_output(output, set(), item, "control_replay")
        self.assertEqual(result.exception.evidence["output"], output)

    def test_prepared_noexecute_never_constructs_engine(self):
        FakeEngine.loads = 0
        with tempfile.TemporaryDirectory() as temporary:
            freeze = Path(temporary) / "freeze.json"
            freeze.write_text("{}")
            args = argparse.Namespace(freeze=freeze, execute=False)
            with patch.object(runner, "read", return_value=CONTRACT), patch.object(runner, "verify"):
                with self.assertRaises(ValueError):
                    runner.run(args, engine_factory=FakeEngine)
        self.assertEqual(FakeEngine.loads, 0)

    def test_fake_decompose_records_all_conditions_and_exclusive_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            freeze = root / "freeze.json"
            freeze.write_text("{}")
            auth = root / "auth.json"
            runner.write(auth, {"status": "authorized", "experiment": "test", "user_instruction": "synthetic test only", "granted_at": "test"})
            prior = root / "preflight.json"
            runner.write(prior, {"stage": "preflight", "status": "completed", "freeze_sha256": runner.sha(freeze), "files": {}})
            items = [{"id": task, "benchmark": task, "context": task,
                      "context_sha256": runner.hashlib.sha256(task.encode()).hexdigest(),
                      "continuations": [" a", " b"], "target_index": 0} for task in ("mmlu", "arc_challenge")]
            real_read = runner.read
            def read_config(path):
                return CONTRACT if Path(path).name == "contract.json" else real_read(path)
            args = argparse.Namespace(freeze=freeze, execute=True, launch_authorization=auth, prior=[prior],
                stage="decompose", explanations=None, output=root / "result", model="unused", device="cpu")
            with patch.object(runner, "read", side_effect=read_config), patch.object(runner, "verify"), \
                 patch.object(runner, "read_rows", return_value=items), patch.object(runner, "summarize", return_value={}):
                receipt = runner.run(args, engine_factory=FakeEngine)
                self.assertEqual(receipt["status"], "completed")
                self.assertEqual(receipt["counts"]["forward"], 34)
                self.assertEqual(receipt["counts"]["calibration_forward"], 2)
                record = real_read(args.output / "item-000.json")
                self.assertEqual(len(record["conditions"]), 17)
                with self.assertRaises(FileExistsError):
                    runner.run(args, engine_factory=FakeEngine)

    def test_projection_fits_content_not_letter_and_freezes_normalization(self):
        records = []
        for slot in range(4):
            for label in (0, 1):
                sign = runner.SIGN_BY_CONTENT_SLOT[slot]
                records.append({"demand": "required", "content_slot": slot,
                    "label_variant": label, "conditions": {"clean": {"observations": [{"L16.mlp":
                        {"values": [[sign * 2, label * 9]], "positions": [0]}}]}}})
        direction = runner.fit_reader(records, {"component": "L16.mlp"})
        self.assertEqual(direction, [1.0, 0.0])

    def test_fake_validation_functional_freeze_and_confirmation_pipeline(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            freeze = root / "freeze.json"
            freeze.write_text("{}")
            auth = root / "auth.json"
            runner.write(auth, {"status": "authorized", "experiment": "test",
                "user_instruction": "synthetic test only", "granted_at": "test"})
            preflight = root / "preflight"
            preflight.mkdir()
            runner.write(preflight / "receipt.json", {"status": "completed", "stage": "preflight",
                "freeze_sha256": runner.sha(freeze), "files": {}})
            ranked = root / "rank"
            ranked.mkdir()
            candidate = {"id": "C01", "component": "L15.mlp", "positions": "prompt_last", "control_seed": 7}
            runner.write(ranked / "candidates.json", [candidate])
            runner.write(ranked / "receipt.json", {"status": "completed", "stage": "rank",
                "freeze_sha256": runner.sha(freeze), "files": {"candidates.json": runner.sha(ranked / "candidates.json")}})
            items = [{"id": task, "benchmark": task, "context": task,
                "context_sha256": runner.hashlib.sha256(task.encode()).hexdigest(),
                "continuations": [" a", " b"], "choices": ["a", "b"], "target_index": 0}
                for task in ("mmlu", "arc_challenge")]
            # Four balanced base pairs per split exercise the exact variant layout,
            # with reduced statistical size only inside this model-free fixture.
            all_functions = runner.functional_rows("reading")
            function_items = [row for row in all_functions if int(row["pair_id"].split("-")[-1]) in
                              (1, 2, 3, 4, 17, 18, 19, 20)]
            real_read = runner.read
            def read_config(path):
                return CONTRACT if Path(path).name == "contract.json" else real_read(path)
            base = dict(freeze=freeze, execute=True, launch_authorization=auth, model="unused", device="cpu")
            with patch.object(runner, "read", side_effect=read_config), patch.object(runner, "verify"), \
                 patch.object(runner, "read_rows", return_value=items), \
                 patch.object(runner, "functional_rows", return_value=function_items), \
                 patch.object(runner, "summarize", return_value={}), \
                 patch.object(runner, "paired_effect", return_value={}), \
                 patch.object(freezer, "verify"), patch.object(freezer, "HERE", root):
                validation = root / "validation"
                args = argparse.Namespace(**base, stage="validate", output=validation,
                    prior=[preflight / "receipt.json", ranked / "receipt.json"], explanations=None)
                runner.run(args, engine_factory=FunctionalFakeEngine)
                record = real_read(validation / "C01/ability-000.json")
                self.assertEqual(set(record["conditions"]), {"clean", "AB_d1", "repair", "replay", "control_repair", "control_replay"})
                proposal = root / "proposal.json"
                runner.write(proposal, {"family": "reading", "validation_receipt_sha256": runner.sha(validation / "receipt.json"),
                    "explanations": [{"candidate_id": "C01", "candidate_sha256": runner.digest(candidate),
                        "hypothesis": "synthetic content reading", "task_relation": "signed content contrast",
                        "expected_direction": "repair increases original relation", "falsifier": "counterpart controls match",
                        "reader": {"component": "L16.mlp", "positions": "prompt_last"}}]})
                function_dev = root / "function-dev"
                args = argparse.Namespace(**base, stage="function-dev", output=function_dev,
                    prior=[preflight / "receipt.json", validation / "receipt.json"], explanations=proposal)
                runner.run(args, engine_factory=FunctionalFakeEngine)
                record = real_read(function_dev / "C01/functional-000.json")
                self.assertEqual(len(record["conditions"]), 8)
                self.assertIn("natural_swap", record["conditions"])
                self.assertTrue((function_dev / "C01/label-0-summary.json").exists())
                self.assertTrue((function_dev / "C01/label-1-summary.json").exists())
                sealed = root / "sealed.json"
                freezer.seal(function_dev, sealed)
                frozen = real_read(sealed)
                self.assertEqual(len(frozen["explanations"][0]["reader"]["projection"]), 2560)
                self.assertEqual(frozen["function_dev_receipt_sha256"], runner.sha(function_dev / "receipt.json"))
                confirmation = root / "confirm"
                args = argparse.Namespace(**base, stage="confirm", output=confirmation,
                    prior=[preflight / "receipt.json", validation / "receipt.json", function_dev / "receipt.json"],
                    explanations=sealed)
                receipt = runner.run(args, engine_factory=FunctionalFakeEngine)
                self.assertEqual(receipt["status"], "completed")
                observed = real_read(confirmation / "C01/functional-000.json")["conditions"]["clean"]["observations"]
                self.assertIsInstance(observed[0]["L16.mlp"]["values"][0], float)
                # Altering the frozen explanation is rejected before model loading.
                frozen["explanations"][0]["hypothesis"] = "changed after development"
                altered = root / "altered.json"
                runner.write(altered, frozen)
                args.explanations = altered
                args.output = root / "must-not-run"
                loads = FunctionalFakeEngine.loads
                with self.assertRaises(ValueError):
                    runner.run(args, engine_factory=FunctionalFakeEngine)
                self.assertEqual(FunctionalFakeEngine.loads, loads)
                self.assertFalse(args.output.exists())


if __name__ == "__main__":
    unittest.main()
