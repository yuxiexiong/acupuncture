"""CPU-only tests: small constructed tensors/models, never pretrained assets."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

from root_engine import (RootEngine, position_indices, scoped_replacement, score_divisors,
                         summarize_scores, text_hash)

HAS_TORCH = importlib.util.find_spec("torch") is not None


class PureTests(unittest.TestCase):
    def test_predictive_positions(self):
        self.assertEqual(position_indices("prompt_last", 5, 5), [4])
        self.assertEqual(position_indices("answer_tail", 5, 5), [])
        self.assertEqual(position_indices("score_positions", 5, 7), [4, 5, 6])
        with self.assertRaises(AssertionError):
            position_indices([0, 0], 5, 7)

    def test_score_contract(self):
        self.assertEqual(score_divisors({"benchmark": "arc_challenge", "choices": ["cat", "dogs"]}), [3, 4])
        result = summarize_scores([2.0, 2.0, 0.0], 1)
        self.assertFalse(result["correct"])
        self.assertEqual(result["prediction"], 0)
        self.assertEqual(result["margin"], 0)


def tiny_engine():
    import torch
    torch.manual_seed(174)

    class MLP(torch.nn.Module):
        def __init__(self, width):
            super().__init__()
            self.up = torch.nn.Linear(4, width, bias=False)
            self.down_proj = torch.nn.Linear(width, 4, bias=False)
        def forward(self, value):
            return self.down_proj(self.up(value))

    class Block(torch.nn.Module):
        def __init__(self, index):
            super().__init__()
            self.linear_attn = torch.nn.Linear(4, 4, bias=False)
            self.mlp = MLP(9000 if index in (13, 14) else 4)
        def forward(self, value):
            value = value + self.linear_attn(value)
            return value + self.mlp(value)

    class Model(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.embedding = torch.nn.Embedding(32, 4)
            self.layers = torch.nn.ModuleList(Block(i) for i in range(32))
            self.readout = torch.nn.Linear(4, 32, bias=False)
            with torch.no_grad():
                for parameter in self.parameters():
                    parameter.mul_(0.03)
            self.calls = []
        def forward(self, input_ids, attention_mask, use_cache, logits_to_keep):
            assert use_cache is False
            self.calls.append((input_ids.detach().clone(), use_cache))
            value = self.embedding(input_ids)
            for layer in self.layers:
                value = layer(value)
            return SimpleNamespace(logits=self.readout(value[:, -logits_to_keep:]))

    class Tokenizer:
        bos_token_id = None
        eos_token_id = 31
        def decode(self, _token):
            return "<eos>"
        def encode(self, text, **_kwargs):
            return [ord(c) % 30 + 1 for c in text]

    engine = RootEngine.__new__(RootEngine)
    engine.torch, engine.device, engine.batch_size = torch, "cpu", 1
    engine.model = Model().eval().requires_grad_(False)
    engine.layers, engine.tokenizer = engine.model.layers, Tokenizer()
    engine.pad_id, engine.max_length = 0, 1000
    engine.modules = {i: engine.layers[i].mlp.down_proj for i in (13, 14)}
    engine.column_norms = {str(i): module.weight.norm(dim=0) for i, module in engine.modules.items()}
    engine.conditions = {}
    engine.contributions = {}
    for i in range(14, 32):
        engine.contributions[f"L{i}.attention"] = engine.layers[i].linear_attn
        if i >= 15:
            engine.contributions[f"L{i}.mlp"] = engine.layers[i].mlp
    engine.counts = {"forward": 0, "backward": 0, "calibration_forward": 0}
    engine.weight_hashes = engine._weight_hashes()
    engine.make_condition("clean")
    engine.make_condition("AB")
    return engine


@unittest.skipUnless(HAS_TORCH, "torch required; run this file on the existing CPU runtime")
class TensorTests(unittest.TestCase):
    def test_locality_and_matching(self):
        import torch
        current = torch.arange(24, dtype=torch.float32).reshape(1, 3, 8)
        donor = current + 1.5
        changed, audit = scoped_replacement(torch, current, donor, [1], [2], "donor", 7)
        self.assertTrue(torch.equal(changed[:, 1], donor[:, 2]))
        self.assertTrue(audit["untouched_positions_identical"])
        random, matched = scoped_replacement(torch, current, donor, [1], [2], "matched", 7)
        repeat, _ = scoped_replacement(torch, current, donor, [1], [2], "matched", 7)
        self.assertTrue(torch.equal(random, repeat))
        self.assertAlmostEqual(matched["requested_delta_norm"][0], matched["actual_delta_norm"][0], places=5)
        self.assertFalse(torch.equal(random[:, 1], donor[:, 2]))

    def test_bfloat_rounding_is_recorded(self):
        import torch
        current = torch.ones(1, 3, 8, dtype=torch.bfloat16) * 23
        donor = current + 1
        changed, audit = scoped_replacement(torch, current, donor, [1], [1], "matched", 14)
        actual = (changed[:, 1].float() - current[:, 1].float()).norm().item()
        self.assertEqual(audit["actual_delta_norm"], [actual])
        self.assertTrue(audit["untouched_positions_identical"])

    def test_actual_hooks_scoring_gradients_and_cleanup(self):
        engine = tiny_engine()
        item = {"context": "Question:", "choices": ["A", "B", "C", "D"],
                "continuations": ["A", "B", "C", "D"], "target_index": 0, "benchmark": "mmlu"}
        calibration = {"context_sha256": text_hash(item["context"]),
                       "residual_scales": {"13": 1.0, "14": 1.0}}
        clean, ab = engine.make_condition("clean"), engine.make_condition("AB")
        engine.make_condition("R1", 0.5, {13: 2, 14: 3})
        base = engine.score_item(item, ab, calibration)
        ranked = engine.rank_item(item, calibration)
        self.assertEqual(len(ranked), 35)
        self.assertTrue(all(row["positions"] == "prompt_last" for row in ranked))
        candidate = next(row for row in ranked if row["component"] == "L15.mlp")
        patch = {"component": "L15.mlp", "positions": "prompt_last", "donor_arm": clean, "mode": "donor"}
        repaired = engine.score_item(item, ab, calibration, patch=patch,
            capture=[{"component": "L16.mlp", "positions": "prompt_last"}])
        # On this linear constructed network and a fixed wrong option, attribution
        # equals the finite replacement effect on the log-probability difference.
        wrong = base["strongest_wrong"]
        effect = repaired["scores"][0] - repaired["scores"][wrong] - base["margin"]
        self.assertAlmostEqual(candidate["predicted_repair"], effect, places=5)
        self.assertEqual(repaired["patch_audit"][0][0]["source_needle_layers"], ["13", "14"])
        self.assertLess(repaired["patch_audit"][0][0]["actual_source_writes"]["13"]["offset_mean"], 0)
        self.assertGreater(repaired["patch_audit"][0][0]["actual_source_writes"]["14"]["offset_mean"], 0)
        self.assertTrue(repaired["patch_audit"][0][0]["untouched_positions_identical"])
        self.assertEqual(len(repaired["observations"][0]["L16.mlp"]["values"][0]), 4)
        self.assertTrue(engine.verify_unchanged()["parameter_gradients_absent"])

    def test_forbidden_site_and_empty_scope_leave_no_hooks(self):
        engine = tiny_engine()
        item = {"context": "q:", "choices": ["A", "B"], "continuations": ["A", "B"],
                "target_index": 0, "benchmark": "mmlu"}
        calibration = {"context_sha256": text_hash(item["context"]), "residual_scales": {"13": 1., "14": 1.}}
        with self.assertRaises(AssertionError):
            engine.score_item(item, "AB@1", calibration, patch={"component": "L14.mlp",
                "positions": "prompt_last", "donor_arm": "clean@1"})
        result = engine.score_item(item, "AB@1", calibration, patch={"component": "L15.mlp",
                "positions": "answer_tail", "donor_arm": "clean@1"})
        self.assertFalse(result["patch_audit"][0][0]["applicable"])
        self.assertTrue(engine.verify_unchanged()["hooks_removed"])

    def test_natural_donor_alignment_and_independent_reader(self):
        engine = tiny_engine()
        item = {"context": "value 3:", "choices": ["A", "B"], "continuations": ["A", "B"],
                "target_index": 0, "benchmark": "mmlu"}
        calibration = {"context_sha256": text_hash(item["context"]), "residual_scales": {"13": 1., "14": 1.}}
        patch = {"component": "L15.mlp", "positions": "prompt_last", "donor_arm": "clean@1",
                 "donor_context": "value 7:"}
        result = engine.score_item(item, "clean@1", calibration, patch=patch)
        audit = result["patch_audit"][0][0]
        self.assertNotEqual(audit["recipient_input_sha256"], audit["donor_input_sha256"])
        self.assertEqual(audit["actual_source_writes"], {})
        with self.assertRaises(AssertionError):
            engine.score_item(item, "clean@1", calibration, patch={**patch, "donor_context": "value 10:"})
        with self.assertRaises(AssertionError):
            engine.score_item(item, "clean@1", calibration, patch=patch,
                capture=[{"component": "L15.mlp", "positions": "prompt_last"}])
        self.assertTrue(engine.verify_unchanged()["hooks_removed"])


if __name__ == "__main__":
    unittest.main()
