"""Gate counterexamples, dry-run boundaries and sparse projection semantics."""
import argparse
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import common
import gate
import pipeline
from readiness import verify_assets


class ProtocolTests(unittest.TestCase):
    def metrics(self, damage=0, lower=-2, upper=2, discordant=20):
        return {task: {"damage_pp": damage, "lower_pp": lower, "upper_pp": upper,
            "discordant_pairs": discordant, "nominal_level": .9875} for task in gate.TASKS}

    def test_gate_counterexamples(self):
        values = self.metrics()
        self.assertEqual(gate.decide(values), ("STOP_SMALL_EFFECT", []))
        values["gsm8k"] = self.metrics(6, 1, 11)["gsm8k"]
        self.assertEqual(gate.decide(values), ("PASS", ["gsm8k"]))
        self.assertEqual(gate.decide(self.metrics(6, -1, 12))[0], "INCONCLUSIVE_HOLD")
        self.assertEqual(gate.decide(self.metrics(0, 0, 0, 0))[0], "INCONCLUSIVE_HOLD")
        self.assertEqual(gate.decide(self.metrics(5, 0, 8))[0], "INCONCLUSIVE_HOLD")

    def test_stage2_recomputes_gate_and_binds_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = {"stage1/benchmark/finish-r01/" + name for name in ("scores.jsonl", "summary.json", "receipt.json")} | {"mapping/quality.json"}
            for name in evidence:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}\n")
            quality = {"status": "PASS", "bundle_sha256": "bundle", "freeze_sha256": "freeze"}
            common.write(root / "mapping/quality.json", quality)
            metrics = self.metrics(10, 5, 15)
            record = {"decision": "PASS", "stage": 1, "primary_arm": "true_D_match",
                "bundle_sha256": "bundle", "freeze_sha256": "freeze",
                "metrics": metrics, "qualifying_tasks": list(gate.TASKS),
                "evidence_sha256": {n: common.sha(root / n) for n in evidence}}
            common.write(root / "stage1/gate.json", record)
            with patch.object(gate, "metrics_from_scores", return_value=metrics):
                common.require_stage(2, root)
                # Even an updated evidence hash cannot turn failed or unrelated
                # mapping quality into a valid stage-2 admission.
                for key, wrong in (("status", "MAPPING_QUALITY_HOLD"),
                                   ("bundle_sha256", "other-bundle"), ("freeze_sha256", "other-freeze")):
                    with self.subTest(quality_field=key):
                        common.write(root / "mapping/quality.json", {**quality, key: wrong})
                        record["evidence_sha256"]["mapping/quality.json"] = common.sha(root / "mapping/quality.json")
                        common.write(root / "stage1/gate.json", record)
                        with self.assertRaises(AssertionError):
                            common.require_stage(2, root)
                common.write(root / "mapping/quality.json", quality)
                record["evidence_sha256"]["mapping/quality.json"] = common.sha(root / "mapping/quality.json")
                record["metrics"]["mmlu"]["damage_pp"] = 999
                common.write(root / "stage1/gate.json", record)
                with patch.object(gate, "metrics_from_scores", return_value=self.metrics(10, 5, 15)):
                    with self.assertRaises(AssertionError):
                        common.require_stage(2, root)
            record["decision"] = "INCONCLUSIVE_HOLD"
            common.write(root / "stage1/gate.json", record)
            with self.assertRaises(AssertionError):
                common.require_stage(2, root)

    def test_dry_stage_plan_has_no_implicit_next_stage(self):
        args = argparse.Namespace(run=Path("/tmp/new-run"), target=Path("/tmp/target"), source=Path("/tmp/source"), stage=1)
        with patch.object(pipeline.subprocess, "Popen", side_effect=AssertionError("Must not spawn")):
            first = pipeline.commands(args)
            self.assertEqual([name for name, _ in first], ["collect", "mapping", "preflight", "toy", "benchmark", "score", "export", "gate"])
            self.assertTrue(all("stage2" not in " ".join(command) for _, group in first for _, command in group))
            args.stage = 2
            self.assertEqual(pipeline.commands(args)[0][0], "preflight")
        self.assertEqual(len(common.conditions(1)), 10)
        self.assertEqual(len(common.conditions(2)), 9)
        self.assertFalse(set(common.conditions(1)) & set(common.conditions(2)))

    def test_assets_reject_missing_or_modified_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            content = {"config.json": "{}", "tokenizer.json": "{}", "tokenizer_config.json": "{}",
                "model.safetensors.index.json": '{"weight_map":{"x":"model.safetensors"}}', "model.safetensors": "weights"}
            manifest = {"repo": "test", "revision": "test", "files": []}
            for name, text in content.items():
                (root / name).write_text(text)
                blob = f"blob {len(text)}\0".encode() + text.encode()
                manifest["files"].append({"rfilename": name, "size": len(text), "blobId": hashlib.sha1(blob).hexdigest()})
            self.assertEqual(len(verify_assets(root, manifest)["files_sha256"]), 5)
            (root / "config.json").write_text("[]")
            with self.assertRaises(AssertionError):
                verify_assets(root, manifest)

    def test_projection_keeps_two_different_dose_definitions(self):
        import torch
        from mapping import legacy
        source = torch.tensor([1., 0.])
        matrix = torch.tensor([[.6, 0.], [.8, 1.]])
        columns = torch.tensor([[2., 0.], [0., 3.]])
        specs, audit, mapped = legacy.target_condition(source, matrix, columns)
        self.assertEqual(audit["index"], 1)
        self.assertAlmostEqual(audit["reconstruction_fraction"], .64, places=6)
        self.assertTrue(torch.allclose(mapped, torch.tensor([.6, .8])))
        projected = specs["S_proj"]["coefficient"] * columns[:, 1]
        recipe = specs["S_recipe"]["coefficient"] * columns[:, 1]
        self.assertTrue(torch.allclose(projected, torch.tensor([0., .8])))
        self.assertTrue(torch.allclose(recipe, torch.tensor([0., 1.])))


if __name__ == "__main__":
    unittest.main()
