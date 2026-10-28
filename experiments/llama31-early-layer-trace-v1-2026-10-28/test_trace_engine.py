"""Llama adapter checks and inherited CPU numerical trace acceptance."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


trace = load("llama_trace_test_adapter", ROOT / "trace_engine.py")
base = load("llama_trace_inherited_tests", ROOT.parent / "early-layer-mechanism-v1-2026-10-28/test_trace_engine.py")
original_mock = base.mock_engine


def llama_mock(*args, **kwargs):
    engine = original_mock(*args, **kwargs)
    for block in engine.layers:
        if hasattr(block, "linear_attn"):
            block.self_attn = block.linear_attn
            del block.linear_attn
    return engine


class AdapterTests(unittest.TestCase):
    def test_loader_generation_calibration_and_intervention_remain_llama(self):
        for name in ("__init__", "generate", "calibrate", "_intervention"):
            self.assertIs(getattr(trace.TraceEngine, name), getattr(trace.llama.Engine, name))
        for name in ("collect", "_sites", "_observe", "_forced_clean", "_component_summaries", "_logit_summaries"):
            self.assertIs(getattr(trace.TraceEngine, name), getattr(trace.shared.TraceEngine, name))

    def test_native_bos_is_not_duplicated_and_stops_remain_llama(self):
        class RawTokenizer:
            bos_token_id, eos_token_id, pad_token_id = 1, 2, None

            def encode(self, text, add_special_tokens=False):
                self.assert_no_special = not add_special_tokens
                return [1, 7] if text.startswith("<|begin_of_text|>") else [7]

            def decode(self, token):
                return "<|begin_of_text|>" if token == 1 else "<|end_of_text|>"

            def get_vocab(self):
                return {"<|eot_id|>": 3}

        raw = RawTokenizer()
        tokenizer = trace.llama.cross.LlamaTokenizer(raw)
        # Both shared trace replay and frozen Llama generation call this encoder.
        self.assertEqual(trace.shared.encode_text(tokenizer, "<|begin_of_text|>native chat"), [1, 7])
        self.assertEqual(trace.shared.encode_text(tokenizer, "plain"), [1, 7])
        self.assertTrue(raw.assert_no_special)
        stops, pad = trace.llama.cross.stop_tokens(tokenizer,
            SimpleNamespace(eos_token_id=[2, 3]), SimpleNamespace(eos_token_id=2, vocab_size=16))
        self.assertEqual((stops, pad), ([2, 3], 2))
        self.assertNotIn(tokenizer.bos_token_id, stops)


class LlamaTraceTests(base.TraceTests):
    def setUp(self):
        super().setUp()
        for target, value in (("trace", trace), ("mock_engine", llama_mock)):
            patched = patch.object(base, target, value)
            patched.start()
            self.addCleanup(patched.stop)

    def test_all_attention_sites_are_llama_and_return_tuples(self):
        engine = base.mock_engine()
        self.assertEqual([meta["module_type"] for meta, _ in engine._sites()
                          if meta["component"] == "attention"], ["self_attn", "self_attn"])
        result = engine.collect(base.source_record([5, 6, 15]))
        self.assertEqual(len(result["trace"]["sites"]), 6)
        self.assertTrue(result["clean_shadow"]["fresh_cache"])
        self.assertTrue(engine.verify_unchanged()["hooks_removed"])


if __name__ == "__main__":
    unittest.main()
