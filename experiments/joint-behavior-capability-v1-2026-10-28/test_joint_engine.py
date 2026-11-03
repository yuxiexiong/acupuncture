"""CPU-only synthetic checks; torch is required, never silently skipped."""
from copy import deepcopy
from types import SimpleNamespace
import unittest

from joint_engine import JointEngine, bind_calibration, bf16_round, encode_pair, text_hash, token_hash, validate_audit


class Tokenizer:
    bos_token_id = None
    eos_token_id = None

    def encode(self, text, **kwargs):
        return list(text.encode())


class BindingTests(unittest.TestCase):
    def test_complete_prompt_whitespace_stays_in_prefix(self):
        context, continuation = "prompt\n\n", "correct answer"
        prefix, suffix = encode_pair(Tokenizer(), context, continuation)
        self.assertEqual(prefix, list(context.encode()))
        self.assertEqual(suffix, list(continuation.encode()))

    def test_rejects_context_boundary_retokenization(self):
        class MergingTokenizer(Tokenizer):
            def encode(self, text, **kwargs):
                return [9] if text == "promptanswer" else [1]
        with self.assertRaisesRegex(AssertionError, "prompt token boundary"):
            encode_pair(MergingTokenizer(), "prompt", "answer")

    def test_reference_is_not_replaced_by_variant(self):
        reference = {"context_sha256": "reference-text", "input_token_sha256": "reference-tokens",
            "residual_scales": {"13": 2.0, "14": 3.0}}
        bound = bind_calibration("new prompt", reference, Tokenizer())
        self.assertNotEqual(bound["context_sha256"], reference["context_sha256"])
        self.assertEqual(bound["reference_context_sha256"], reference["context_sha256"])
        self.assertEqual(bound["reference_input_token_sha256"], reference["input_token_sha256"])
        bound["residual_scales"]["13"] = 9
        self.assertEqual(reference["residual_scales"]["13"], 2)

    def test_rounding_ties_even(self):
        self.assertEqual(bf16_round(1.00390625), 1.0)
        self.assertEqual(bf16_round(1.01171875), 1.015625)
        self.assertEqual(bf16_round(-1.00390625), -1.0)


class HookTests(unittest.TestCase):
    def setUp(self):
        import torch
        self.torch = torch
        engine = JointEngine.__new__(JointEngine)
        engine.torch, engine.device = torch, "cpu"
        engine.modules = {l: torch.nn.Linear(9216, 2, bias=False).to(torch.bfloat16) for l in (13, 14)}
        for l, module in engine.modules.items():
            with torch.no_grad():
                module.weight.fill_(0.5 if l == 13 else 1.0)
                module.weight[:, 3].fill_(2.0)
        engine.column_norms = {str(l): m.weight.float().norm(dim=0) for l, m in engine.modules.items()}
        self.clean = {"id": "clean", "recipe": "clean", "dose": 0.0, "channels": {}}
        self.ab = {"id": "AB", "recipe": "AB", "dose": 0.5,
            "channels": {"13": 7956, "14": 8949}}
        self.random = {"id": "R01", "recipe": "R01", "dose": 0.5,
            "channels": {"13": 3, "14": 7}}
        engine.configure([self.clean, self.ab, self.random])
        self.engine = engine
        self.calibration = {"residual_scales": {"13": 4.0, "14": 8.0}}

    def execute(self, arm, widths, mask=None, value=1.0):
        torch, engine = self.torch, self.engine
        mask = torch.ones((1, widths[0]), dtype=torch.long) if mask is None else mask
        captured, originals, hooks = {}, {}, []
        # A normal forward hook sees the input after all pre-hooks.
        for layer, module in engine.modules.items():
            hooks.append(module.register_forward_hook(
                lambda _m, args, _out, l=layer: captured.setdefault(l, []).append(args[0].clone())))
        try:
            with torch.inference_mode(), engine._intervention(arm, [self.calibration], mask):
                for step, width in enumerate(widths):
                    for layer, module in engine.modules.items():
                        activation = torch.full((1, width, 9216), value + step, dtype=torch.bfloat16)
                        originals[layer, step] = activation.clone()
                        module(activation)
                        self.assertTrue(torch.equal(activation, originals[layer, step]))
        finally:
            for hook in hooks:
                hook.remove()
        return deepcopy(engine.last_audit), captured, originals

    def test_prefill_decode_sign_and_only_selected_channel(self):
        audit, changed, originals = self.execute("AB", [3, 1, 1])
        self.assertTrue(validate_audit(audit, self.ab, self.calibration, 3, generated_count=3))
        for layer, arrays in changed.items():
            index = self.ab["channels"][str(layer)]
            self.assertEqual(audit[str(layer)]["nonzero_positions"], 5)
            for step, array in enumerate(arrays):
                delta = array.float() - originals[layer, step].float()
                self.assertEqual(int((delta != 0).sum()), array.shape[1])
                self.assertTrue(bool((delta[..., index] < 0).all()) if layer == 13
                    else bool((delta[..., index] > 0).all()))
        self.assertTrue(all(not m._forward_pre_hooks for m in self.engine.modules.values()))

    def test_zero_restoration_and_cleanup_after_exception(self):
        before, outputs, _ = self.execute("clean", [3])
        zero, zero_outputs, _ = self.execute("zero", [3])
        zero_condition = {"channels": {"13": 7956, "14": 8949}, "dose": 0.0}
        self.assertTrue(validate_audit(zero, zero_condition, self.calibration, 3, input_length=3))
        self.execute("AB", [3])
        restored, restored_outputs, _ = self.execute("clean", [3])
        self.assertEqual(before, restored)
        for layer in outputs:
            self.assertTrue(self.torch.equal(outputs[layer][0], zero_outputs[layer][0]))
            self.assertTrue(self.torch.equal(outputs[layer][0], restored_outputs[layer][0]))
        with self.assertRaisesRegex(RuntimeError, "injected failure"):
            with self.engine._intervention("AB", [self.calibration], self.torch.ones((1, 3))):
                raise RuntimeError("injected failure")
        self.assertTrue(all(not m._forward_pre_hooks for m in self.engine.modules.values()))

    def test_matching_norms_and_rounding_to_zero_is_retained(self):
        original, _, _ = self.execute("AB", [3])
        random, _, _ = self.execute("R01", [3])
        for layer in ("13", "14"):
            self.assertAlmostEqual(original[layer]["requested_vector_norm"],
                random[layer]["requested_vector_norm"])
        rounded, _, _ = self.execute("AB", [3], value=1000000.0)
        self.assertTrue(validate_audit(rounded, self.ab, self.calibration, 3, input_length=3))
        self.assertTrue(all(row["nonzero_positions"] == 0 for row in rounded.values()))

    def test_mask_and_audit_tamper_detection(self):
        mask = self.torch.tensor([[0, 1, 1]])
        audit, changed, originals = self.execute("AB", [3], mask=mask)
        for layer in (13, 14):
            self.assertEqual(audit[str(layer)]["positions"], 2)
            self.assertTrue(self.torch.equal(changed[layer][0][:, 0], originals[layer, 0][:, 0]))
        valid, _, _ = self.execute("AB", [3])
        valid["13"]["channel"] = 0
        with self.assertRaises(AssertionError):
            validate_audit(valid, self.ab, self.calibration, 3, input_length=3)

    def test_rejects_wrong_dose_and_duplicate_condition(self):
        condition = deepcopy(self.ab)
        condition["dose"] = 0.75
        with self.assertRaises(AssertionError):
            self.engine.configure([condition])
        with self.assertRaises(AssertionError):
            self.engine.configure([self.ab, self.ab])

    def test_multitoken_score_uses_exact_suffix_logits(self):
        class SmallTokenizer(Tokenizer):
            def encode(self, text, **kwargs):
                return ["abcd".index(c) + 1 for c in text]
        engine, torch, calls = self.engine, self.torch, []
        engine.tokenizer = SmallTokenizer()
        engine.max_length, engine.pad_id = 128, 0
        logits = torch.tensor([[[9.0, 0, 0, 0, 0], [0.0, 0, 0, 3, 0], [0.0, 0, 0, 0, 4]]])
        def model(**kwargs):
            calls.append(kwargs)
            return SimpleNamespace(logits=logits[:, -kwargs["logits_to_keep"]:])
        engine.model = model
        calibration = {**self.calibration, "context_sha256": text_hash("ab")}
        result = engine.score(["ab"], ["cd"], "clean", [calibration])[0]
        expected = torch.log_softmax(logits[0, 1:], -1)[[0, 1], [3, 4]].tolist()
        self.assertEqual(result["token_logprobs"], expected)
        self.assertEqual(result["continuation_token_ids"], [3, 4])
        self.assertEqual(result["context_token_count"], 2)
        self.assertEqual(result["input_token_sha256"], token_hash([1, 2, 3]))
        self.assertTrue(result["is_greedy"])
        self.assertEqual(len(calls), 1)
        self.assertFalse(calls[0]["use_cache"])
        self.assertEqual(calls[0]["input_ids"].tolist(), [[1, 2, 3]])
        self.assertEqual(engine.last_audit, {})


if __name__ == "__main__":
    unittest.main()
