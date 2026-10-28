"""CPU mock checks; no model downloads or GPU allocation."""
import copy
import gzip
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("early_trace_test_engine", ROOT / "trace_engine.py")
trace = importlib.util.module_from_spec(spec)
spec.loader.exec_module(trace)
HAS_TORCH = importlib.util.find_spec("torch") is not None


def fake_transformers():
    module = types.ModuleType("transformers")
    module.StoppingCriteria = type("StoppingCriteria", (), {})
    module.StoppingCriteriaList = list
    module.LogitsProcessor = type("LogitsProcessor", (), {})

    class Processors(list):
        def __call__(self, input_ids, scores):
            for processor in self:
                scores = processor(input_ids, scores)
            return scores
    module.LogitsProcessorList = Processors
    return module


def mock_engine(steered_tokens=(5, 6, 15), clean_tokens=(15,)):
    import torch

    class Tokenizer:
        bos_token_id, eos_token_id = None, 15

        def encode(self, text, **kwargs):
            return [1, 2, 3]

        def decode(self, tokens, skip_special_tokens=False, **kwargs):
            if isinstance(tokens, int):
                tokens = [tokens]
            return " ".join(f"t{int(token)}" for token in tokens if not skip_special_tokens or int(token) != 15)

        def batch_decode(self, rows, **kwargs):
            return [self.decode(row, **kwargs) for row in rows]

    class Attention(torch.nn.Module):
        def forward(self, hidden):
            return hidden * 0.125, None

    class MLP(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.down_proj = torch.nn.Linear(4, 4, bias=False, dtype=torch.bfloat16)
            with torch.no_grad():
                self.down_proj.weight.copy_(torch.eye(4))

        def forward(self, hidden):
            return self.down_proj(hidden)

    class Block(torch.nn.Module):
        def __init__(self, linear):
            super().__init__()
            setattr(self, "linear_attn" if linear else "self_attn", Attention())
            self.mlp = MLP()

        def forward(self, hidden):
            attention = self.linear_attn if hasattr(self, "linear_attn") else self.self_attn
            hidden = hidden + attention(hidden)[0]
            return hidden + self.mlp(hidden)

    class Model(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.layers = torch.nn.ModuleList([Block(True), Block(False)])
            self.generations = []
            self.fail_at_step = None

        def forward(self, input_ids, past_key_values=None, **kwargs):
            if self.fail_at_step == self.step:
                raise RuntimeError("injected test failure")
            self.generations[-1]["forward_inputs"].append(input_ids[0].tolist())
            self.generations[-1]["forward_cache_ids"].append(id(past_key_values))
            hidden = torch.ones((*input_ids.shape, 4), dtype=torch.bfloat16)
            for block in self.layers:
                hidden = block(hidden)
            changed = abs(float(hidden[0, -1, 0]) - 5.0625) > 0.0625
            script = steered_tokens if changed else clean_tokens
            token = script[min(self.step, len(script) - 1)]
            logits = torch.full((1, 1, 16), -4.0, dtype=torch.bfloat16)
            logits[0, 0, token] = 8
            return types.SimpleNamespace(logits=logits)

        def generate(self, input_ids, attention_mask, max_new_tokens, eos_token_id, pad_token_id,
                     stopping_criteria=(), logits_processor=(), **kwargs):
            assert kwargs == {"do_sample": False, "use_cache": True, "logits_to_keep": 1}
            cache = {"fresh": len(self.generations)}
            self.generations.append({"cache": cache, "forward_inputs": [], "forward_cache_ids": [],
                                     "budget": max_new_tokens})
            result = input_ids.clone()
            for self.step in range(max_new_tokens):
                output = self(result if self.step == 0 else result[:, -1:], past_key_values=cache)
                scores = output.logits[:, -1].float()
                for processor in logits_processor:
                    scores = processor(result, scores)
                token = scores.argmax(-1)
                result = torch.cat((result, token[:, None]), dim=-1)
                stop = any(bool(criterion(result, scores).all()) for criterion in stopping_criteria)
                if int(token[0]) in eos_token_id or stop:
                    break
            return result

    engine = trace.TraceEngine.__new__(trace.TraceEngine)
    engine.torch, engine.device, engine.batch_size = torch, "cpu", 1
    engine.tokenizer, engine.model = Tokenizer(), Model().eval()
    engine.layers = engine.model.layers
    engine.modules = {i: block.mlp.down_proj for i, block in enumerate(engine.layers)}
    engine.column_norms = {str(i): module.weight.float().norm(dim=0) for i, module in engine.modules.items()}
    engine.stop_ids, engine.pad_id, engine.max_length = [15], 0, 1024
    engine.weight_hashes = engine._weight_hashes()
    engine.metadata, engine.last_hook = {"model_id": "mock"}, None
    return engine


def source_record(tokens, layer=0, dose=1.0):
    context, prompt = "fixed prompt", [1, 2, 3]
    return {"model_id": "mock", "condition_id": "test", "context": context,
            "layer": layer, "channel": 0 if layer is not None else None, "dose": dose,
            "calibration": {"context_sha256": trace.text_hash(context), "input_token_sha256": trace.token_hash(prompt),
                            "input_token_count": len(prompt), "residual_scales": {"0": 2.0, "1": 2.0}},
            "output": {"token_ids": list(tokens), "max_new_tokens": 128, "input_token_sha256": trace.token_hash(prompt)}}


class SourceTests(unittest.TestCase):
    def test_arm_resolves_frozen_sign(self):
        self.assertEqual(trace.record_arm({"layer": None}), "baseline")
        self.assertEqual(trace.record_arm({"layer": 3, "channel": 9}), (3, 9, 1.0))
        self.assertEqual(trace.record_arm({"layer": 3, "channel": 9, "intervention": {"dose": -0.5}}), (3, 9, -0.5))


@unittest.skipUnless(HAS_TORCH, "CPU torch unavailable; numerical mock validation must run in the server runtime")
class TraceTests(unittest.TestCase):
    def setUp(self):
        # Import the C extension before patch.dict snapshots sys.modules.
        # Otherwise teardown removes torch and the next test tries to reload it.
        import torch
        self.transformers = patch.dict(sys.modules, {"transformers": fake_transformers()})
        self.transformers.start()
        self.addCleanup(self.transformers.stop)

    def test_one_token_eos_zero_and_restored_are_exact(self):
        engine = mock_engine()
        record = source_record([15], layer=None)
        baseline = engine.collect(record)
        zero = engine.collect(record, arm_override=(0, 0, 0.0))
        restored = engine.collect(record)
        for result in (baseline, zero, restored):
            self.assertEqual(result["output"]["token_ids"], [15])
            self.assertTrue(result["source_token_ids_match"])
            self.assertEqual(result["trace"]["observed_position_count"], 3)
            self.assertEqual(result["raw_logit_sha256_per_step"], baseline["raw_logit_sha256_per_step"])
            for site in result["trace"]["sites"]:
                self.assertEqual(site["delta_norm"], [0.0] * 3)
                self.assertTrue(all(abs(value - 1.0) < 1e-6 for value in site["cosine"]))
        self.assertEqual(zero["intervention"]["bf16_offset"], 0.0)
        self.assertTrue(engine.verify_unchanged()["hooks_removed"])

    def test_shadow_uses_identical_prefix_after_clean_would_stop(self):
        engine = mock_engine()
        record = source_record([5, 6, 15])
        original = copy.deepcopy(record)
        result = engine.collect(record)
        data = result["trace"]
        self.assertEqual(record, original)
        self.assertEqual(result["output"]["token_ids"], [5, 6, 15])
        self.assertEqual(result["clean_shadow"]["token_ids"], [5, 6, 15])
        self.assertEqual(data["observed_input_token_ids"], [1, 2, 3, 5, 6])
        self.assertEqual(data["logits"]["first_prediction_divergence"], 0)
        self.assertEqual(len(data["sites"]), 6)
        self.assertEqual(data["sites"][0]["delta_norm"], [0.0] * 5)
        self.assertTrue(any(value > 0 for value in data["sites"][1]["delta_norm"]))
        self.assertTrue(all(step["clean_argmax_is_eos"] for step in data["logits"]["steps"]))
        for i, step in enumerate(data["forward_steps"]):
            self.assertEqual(step["prefix_sha256"], trace.token_hash([1, 2, 3] + [5, 6, 15][:i]))
        for generation in engine.model.generations:
            self.assertEqual(generation["forward_inputs"], [[1, 2, 3], [5], [6]])
            self.assertEqual(len(set(generation["forward_cache_ids"])), 1)
        self.assertIsNot(engine.model.generations[0]["cache"], engine.model.generations[1]["cache"])
        self.assertEqual(result["intervention"]["calls"], 3)
        self.assertEqual(result["intervention"]["positions"], 5)
        self.assertEqual(result["intervention"]["bf16_offset"], 2.0)
        for step in data["logits"]["steps"]:
            candidates = {item["token_id"]: item for item in step["candidates"]}
            self.assertIn(15, candidates)
            self.assertIn(step["generated_token_id"], candidates)
            self.assertNotEqual(step["clean_best_nonstop_token_id"], 15)
            self.assertEqual(step["clean_stop_advantage"], 12.0)
        self.assertTrue(engine.verify_unchanged()["hooks_removed"])

    def test_128_cap_and_component_observer_does_not_change_logits(self):
        engine = mock_engine(steered_tokens=(5,))
        record = source_record([5] * 128)
        plain = engine.collect(record, observe=False)
        observed = engine.collect(record)
        self.assertEqual(plain["output"]["token_ids"], [5] * 128)
        self.assertEqual(observed["output"]["end_reason"], "length_limit")
        self.assertEqual(plain["raw_logit_sha256_per_step"], observed["raw_logit_sha256_per_step"])
        self.assertEqual(observed["trace"]["observed_position_count"], 130)
        self.assertEqual(len(observed["trace"]["forward_steps"]), 128)
        self.assertNotIn("trace", plain)
        self.assertTrue(engine.verify_unchanged()["hooks_removed"])

    def test_frozen_signed_doses_and_gzip(self):
        engine = mock_engine()
        with tempfile.TemporaryDirectory() as directory:
            for dose in (-1.0, -0.0625, 0.0625, 0.5, 1.0):
                path = Path(directory) / "trace.json.gz"
                result = engine.collect(source_record([5, 6, 15], dose=dose), path)
                self.assertEqual(result["intervention"]["requested_offset"], dose * 2)
                self.assertTrue(result["source_token_ids_match"])
                with gzip.open(path, "rt") as stream:
                    saved = json.load(stream)
                self.assertEqual(saved["generated_token_ids"], [5, 6, 15])
                self.assertFalse(path.with_suffix(".gz.tmp").exists())
        self.assertTrue(engine.verify_unchanged()["hooks_removed"])

    def test_failure_removes_all_hooks_and_keeps_weights(self):
        engine = mock_engine()
        engine.model.fail_at_step = 1
        with self.assertRaisesRegex(RuntimeError, "injected test failure"):
            engine.collect(source_record([5, 6, 15]))
        self.assertTrue(engine.verify_unchanged()["hooks_removed"])

    def test_bad_calibration_and_source_mismatch_are_visible(self):
        engine = mock_engine()
        record = source_record([5, 6, 15])
        record["calibration"]["input_token_sha256"] = "wrong"
        with self.assertRaises(AssertionError):
            engine.collect(record)
        self.assertEqual(engine.model.generations, [])
        result = engine.collect(source_record([7, 15]), observe=False)
        self.assertFalse(result["source_token_ids_match"])
        self.assertTrue(engine.verify_unchanged()["hooks_removed"])


if __name__ == "__main__":
    unittest.main()
