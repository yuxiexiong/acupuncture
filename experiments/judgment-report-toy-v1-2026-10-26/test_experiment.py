"""Authorization, calibration identity and real CPU hook checks; no Qwen loading."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import experiment as e


class Tokenizer:
    bos_token_id = None
    eos_token_id = 31

    def decode(self, _token):
        return "<eos>"

    def encode(self, text, **_kwargs):
        if len(text) >= 2 and text[-2] == " " and text[-1] in "ABCD":
            return self.encode(text[:-2]) + [ord(text[-1]) - ord("A") + 1]
        return [ord(c) % 30 + 1 for c in text]


def mini_item(context="Compare:", base="b", rotation=0):
    order = [(i + rotation) % 4 for i in range(4)]
    return {"id": f"{base}-r{rotation}", "base_id": base, "pair_id": base,
        "panel": "comparison", "benchmark": "functional_comparison", "demand": "required",
        "rotation": rotation, "order": order, "target_index": order.index(0), "target_content_index": 0,
        "choices": ["p", "q", "r", "s"], "continuations": [" A", " B", " C", " D"],
        "context": context, "context_sha256": e.text_hash(context),
        "reference_context": "Compare:", "reference_context_sha256": e.text_hash("Compare:")}


class Guards(unittest.TestCase):
    def test_prepare_and_old_permission_never_load_model(self):
        calls = []
        factory = lambda *a, **k: calls.append((a, k))
        with self.assertRaisesRegex(ValueError, "Stopped before model loading"):
            e.run("C05", "unused", engine_factory=factory)
        with self.assertRaisesRegex(ValueError, "old launch permissions"):
            e.run("C05", "unused", e.HERE / "authorization.prepare.json", True,
                  engine_factory=factory)
        self.assertEqual(calls, [])

    def test_calibration_reference_is_not_current_input(self):
        item = mini_item("Different labels:", rotation=1)
        reference = {"context_sha256": e.text_hash("Compare:"), "input_token_sha256": "reference-tokens",
            "input_token_count": 8, "residual_scales": {"13": 2.0, "14": 3.0}}
        saved = deepcopy(reference)
        bound = e.bind_calibration(item, reference, Tokenizer())
        self.assertEqual(bound["residual_scales"], reference["residual_scales"])
        self.assertEqual(bound["context_sha256"], e.text_hash(item["context"]))
        self.assertEqual(bound["reference_calibration_sha256"], e.digest(reference))
        self.assertNotIn("input_token_sha256", bound)
        self.assertNotEqual(bound["binding_input_token_sha256"], reference["input_token_sha256"])
        self.assertEqual(reference, saved)
        with self.assertRaises(ValueError):
            e.bind_calibration(item, {**reference, "context_sha256": "wrong"}, Tokenizer())
        self.assertTrue(e.tokenizer_check(Tokenizer(), [mini_item(), item])["single_token_labels"])

    def test_wrong_freeze_authorization_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            e.write(root / "contract.json", e.read(e.HERE / "contract.json"))
            e.write(root / "freeze.json", {"fixture": True})
            auth = {"status": "authorized", "experiment": root.name,
                "freeze_sha256": "wrong", "candidate_ids": ["C05", "C01"],
                "maximum_model_workers": 2, "user_instruction": "synthetic test only", "granted_at": "fixture"}
            e.write(root / "auth.json", auth)
            with patch.object(e, "HERE", root), self.assertRaises(ValueError):
                e.check_authorization(root / "auth.json", "C05", True)

    def test_failed_load_receipt_retained_and_output_cannot_be_reused(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            contract = e.read(e.HERE / "contract.json")
            items = e.task_data.read_rows(e.HERE / "data/items.jsonl")
            e.write(root / "contract.json", contract)
            e.write(root / "freeze.json", {"fixture": True})
            e.write(root / "auth.json", {"status": "authorized", "experiment": contract["experiment"],
                "freeze_sha256": e.sha(root / "freeze.json"), "candidate_ids": ["C05", "C01"],
                "maximum_model_workers": 2, "user_instruction": "synthetic unit test, no model permission",
                "granted_at": "fixture"})
            def fail(*_args, **_kwargs):
                raise RuntimeError("synthetic load failure")
            with patch.object(e, "HERE", root), patch.object(e, "verify", return_value={}), \
                    patch.object(e.task_data, "read_rows", return_value=items):
                output = root / "runs/test"
                with self.assertRaisesRegex(RuntimeError, "synthetic load failure"):
                    e.run("C05", output, root / "auth.json", True, engine_factory=fail)
                receipt = e.read(output / "receipt.json")
                self.assertEqual(receipt["status"], "failed")
                self.assertFalse(receipt["model_loaded"])
                self.assertTrue((output / "failure.log").exists())
                with self.assertRaises(FileExistsError):
                    e.run("C05", output, root / "auth.json", True, engine_factory=fail)


@unittest.skipUnless(importlib.util.find_spec("torch"), "CPU PyTorch needed for synthetic hook check")
class CPUHooks(unittest.TestCase):
    def test_collect_reuses_reference_preserves_needles_and_cleans_up(self):
        from test_root_engine import tiny_engine
        engine = tiny_engine()
        engine.tokenizer = Tokenizer()
        items = [mini_item(), mini_item("Changed options:", rotation=1)]
        candidate = {"id": "C05", "component": "L19.attention", "positions": "prompt_last", "control_seed": 20261031}
        with tempfile.TemporaryDirectory() as folder:
            rows = e.collect(engine, items, candidate, Path(folder))
            self.assertEqual(len(list(Path(folder).glob("item-*.json"))), 2)
            self.assertEqual(engine.counts["calibration_forward"], 1)
            self.assertEqual(engine.counts["forward"], 80)
            self.assertEqual(rows[0]["reference_calibration"], rows[1]["reference_calibration"])
            self.assertEqual(rows[0]["calibration"]["residual_scales"], rows[1]["calibration"]["residual_scales"])
            for row in rows:
                audit = row["conditions"]["repair"]["patch_audit"][0][0]
                self.assertEqual(set(audit["actual_source_writes"]), {"13", "14"})
                self.assertEqual(audit["positions"], [row["calibration"]["binding_input_token_count"] - 1])
                self.assertTrue(audit["untouched_positions_identical"])
            references = {}
            for item, row in zip(items, rows):
                e.verify_row(item, row, candidate, references)
            bad = deepcopy(rows[1])
            bad["reference_calibration"]["input_token_count"] += 1
            bad["calibration"]["reference_calibration_sha256"] = e.digest(bad["reference_calibration"])
            with self.assertRaisesRegex(ValueError, "share the exact reference"):
                e.verify_row(items[1], bad, candidate, references)
            bad = deepcopy(rows[0])
            bad["conditions"]["repair"]["patch_audit"][0][0]["component"] = "L23.attention"
            with self.assertRaisesRegex(ValueError, "Patch component"):
                e.verify_row(items[0], bad, candidate, {})
            self.assertTrue(engine.verify_unchanged()["hooks_removed"])

    def test_failure_preserves_completed_item_and_removes_hooks(self):
        from test_root_engine import tiny_engine
        engine = tiny_engine()
        engine.tokenizer = Tokenizer()
        original = engine._forward
        def fail_during_second_item(*args, **kwargs):
            if engine.counts["forward"] == 45:
                raise RuntimeError("synthetic mid-patch failure")
            return original(*args, **kwargs)
        engine._forward = fail_during_second_item
        candidate = {"id": "C05", "component": "L19.attention", "positions": "prompt_last", "control_seed": 20261031}
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(RuntimeError, "synthetic mid-patch failure"):
                e.collect(engine, [mini_item(), mini_item("Changed:", rotation=1)], candidate, Path(folder))
            self.assertTrue((Path(folder) / "item-000.json").is_file())
            self.assertFalse((Path(folder) / "item-001.json").exists())
            self.assertTrue(engine.verify_unchanged()["hooks_removed"])


if __name__ == "__main__":
    unittest.main()
