"""CPU-only acceptance of the adapter; no model weights or CUDA are loaded."""
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import torch

from engine import DOSES, Engine, cross, effective_generation, survey


class Config(SimpleNamespace):
    def to_dict(self):
        return vars(self).copy()


def generation_model(**changed):
    raw = Config(do_sample=True, temperature=.6, top_p=.9, num_beams=None,
                 repetition_penalty=None, min_length=None, renormalize_logits=None)
    def prepare(config, **kwargs):
        assert config is None
        logits = kwargs.pop("logits_to_keep")
        resolved = {"num_beams": 1, "num_beam_groups": 1, "repetition_penalty": 1.0,
            "encoder_repetition_penalty": 1.0, "no_repeat_ngram_size": 0,
            "min_length": 0, "min_new_tokens": None, "forced_bos_token_id": None,
            "forced_eos_token_id": None, "suppress_tokens": None,
            "begin_suppress_tokens": None, "renormalize_logits": None}
        return Config(**{**resolved, **changed, **kwargs}), {"logits_to_keep": logits}
    return SimpleNamespace(generation_config=raw, _prepare_generation_config=prepare)


class EngineChecks(unittest.TestCase):
    def setUp(self):
        self.engine = Engine.__new__(Engine)
        self.engine.torch = torch
        self.engine.modules = {i: torch.nn.Linear(4, 3, bias=False, dtype=torch.bfloat16) for i in range(2)}
        self.engine.column_norms = {str(i): torch.tensor([1., 2., 3., 4.]) for i in range(2)}
        self.calibrations = [{"residual_scales": {"0": 7.03125, "1": 10.01953125}}]
        self.mask = torch.tensor([[0, 1, 1]])
        self.x = torch.tensor([[[1., 2., 3., 4.], [2., 3., 4., 5.], [3., 4., 5., 6.]]], dtype=torch.bfloat16)

    def captured(self, arm, tensors):
        observed = []
        with self.engine._intervention(arm, self.calibrations, self.mask):
            self.assertFalse(self.engine.modules[0]._forward_pre_hooks)
            handle = self.engine.modules[1].register_forward_pre_hook(lambda _m, args: observed.append(args[0].clone()))
            try:
                for value in tensors:
                    self.engine.modules[1](value)
            finally:
                handle.remove()
        return observed

    def test_all_signed_doses_original_ratio_one_channel_prompt_and_decode(self):
        weights = {i: module.weight.clone() for i, module in self.engine.modules.items()}
        original = self.x.clone()
        for dose in DOSES:
            with self.subTest(dose=dose):
                observed = self.captured((1, 2, dose), [self.x, self.x[:, :1]])
                requested = dose * self.calibrations[0]["residual_scales"]["1"] / 3.
                amount = torch.tensor(requested, dtype=torch.bfloat16)
                self.assertEqual(self.engine.last_hook["requested_offset"], requested)
                self.assertEqual(self.engine.last_hook["bf16_offset"], float(amount))
                self.assertEqual(float(amount), -float(torch.tensor(-requested, dtype=torch.bfloat16)))
                if dose:
                    rounded_unit = float(torch.tensor(self.calibrations[0]["residual_scales"]["1"] / 3., dtype=torch.bfloat16))
                    self.assertNotEqual(requested, dose * rounded_unit)
                expected = self.x.clone()
                expected[0, 1:, 2] += amount
                self.assertTrue(torch.equal(observed[0], expected))
                decode = self.x[:, :1].clone()
                decode[..., 2] += amount
                self.assertTrue(torch.equal(observed[1], decode))
                self.assertTrue(torch.equal(self.x, original))
                self.assertEqual(self.engine.last_hook["calls"], 2)
                self.assertEqual(self.engine.last_hook["positions"], 4)
                self.assertTrue(self.engine.last_hook["prefill_target_values_checked"])
                self.assertTrue(all(not module._forward_pre_hooks for module in self.engine.modules.values()))
        self.assertTrue(all(torch.equal(weights[i], module.weight) for i, module in self.engine.modules.items()))

    def test_zero_and_removed_signed_hooks_restore_exactly(self):
        module = self.engine.modules[1]
        baseline = module(self.x).detach().clone()
        with self.engine._intervention((1, 2, 0.), self.calibrations, self.mask):
            self.assertTrue(torch.equal(module(self.x), baseline))
        for dose in DOSES:
            with self.engine._intervention((1, 2, dose), self.calibrations, self.mask):
                module(self.x)
            with self.engine._intervention("baseline", self.calibrations, self.mask):
                self.assertIsNone(self.engine.last_hook)
                self.assertTrue(torch.equal(module(self.x), baseline))

    def test_hook_removed_on_forward_failure(self):
        with self.assertRaisesRegex(RuntimeError, "intentional"):
            with self.engine._intervention((1, 2, -.5), self.calibrations, self.mask):
                self.engine.modules[1](self.x)
                raise RuntimeError("intentional")
        self.assertTrue(all(not module._forward_pre_hooks for module in self.engine.modules.values()))

    def test_invalid_doses_coordinates_and_width_never_leave_hooks(self):
        for arm in ((1, 2, -.75), (1, 2, .75), (1, 2, .3), (1, 2, 2.), (1, 2, float("nan")), (2, 2, -.5), (1, 4, -.5)):
            with self.subTest(arm=arm), self.assertRaises((AssertionError, ValueError)):
                with self.engine._intervention(arm, self.calibrations, self.mask):
                    self.fail("Invalid condition entered")
            self.assertTrue(all(not module._forward_pre_hooks for module in self.engine.modules.values()))
        with self.assertRaises(AssertionError):
            self.captured((1, 2, -.5), [self.x[:, :2]])
        self.assertTrue(all(not module._forward_pre_hooks for module in self.engine.modules.values()))

    def test_original_generation_calibration_and_cleanup_are_inherited(self):
        self.assertIs(Engine.generate, survey.transfer._v2.Engine.generate)
        self.assertIs(Engine.calibrate, survey.SurveyEngine.calibrate)
        self.assertIs(Engine.verify_unchanged, survey.SurveyEngine.verify_unchanged)

    def test_constructor_covers_all_32_layers_and_metadata(self):
        def tiny_init(instance, model_path, device, batch_size, threads):
            self.assertEqual((batch_size, threads), (1, 4))
            instance.torch = torch
            instance.model = generation_model()
            instance.model.config = SimpleNamespace(model_type="llama")
            instance.stop_ids, instance.pad_id = [128001, 128008, 128009], 128009
            instance.layers = [SimpleNamespace(mlp=SimpleNamespace(down_proj=torch.nn.Linear(4, 3, bias=False, dtype=torch.bfloat16)), _forward_hooks={}) for _ in range(32)]
            instance.metadata = {"hidden_size": 3, "intermediate_size": 4, "chat_template_date_string": "26 Oct 2026"}
        model_spec = {"layers": 32, "hidden_size": 3, "intermediate_size": 4, "id": "cpu_fixture", "revision": "fixture"}
        with patch.object(cross.CrossFamilyEngine, "__init__", tiny_init):
            engine = Engine("unused", model_spec, "cpu")
        self.assertEqual(list(engine.modules), list(range(32)))
        self.assertEqual(len(engine.column_norms), 32)
        self.assertEqual(len(engine.weight_hashes), 32)
        self.assertEqual(engine.metadata["layers"], list(range(32)))
        self.assertIsNone(engine.metadata["enable_thinking"])
        self.assertEqual(engine.metadata["chat_template_date_string"], "26 Oct 2026")
        self.assertFalse(engine.metadata["effective_generation"]["do_sample"])
        self.assertTrue(engine.metadata["sampling_defaults_inactive"]["do_sample"])
        self.assertTrue(engine.verify_unchanged()["hooks_removed"])

    def test_generation_policy_rejects_non_neutral_defaults(self):
        for changed in ({"num_beams": 2}, {"repetition_penalty": 1.1}, {"min_new_tokens": 10}, {"forced_eos_token_id": 128009}, {"suppress_tokens": [42]}):
            with self.subTest(changed=changed), self.assertRaises(AssertionError):
                effective_generation(generation_model(**changed), [128001, 128008, 128009], 128009)

    def test_unresolved_none_defaults_are_audited_after_resolution_without_mutation(self):
        model = generation_model()
        before = model.generation_config.to_dict()
        settings = effective_generation(model, [128001, 128008, 128009], 128009)
        self.assertFalse(settings["do_sample"])
        self.assertEqual(settings["num_beams"], 1)
        self.assertIsNone(settings["renormalize_logits"])
        self.assertEqual(model.generation_config.to_dict(), before)
        self.assertIsNone(model.generation_config.num_beams)

    def test_native_stop_ids_and_no_duplicate_bos(self):
        class Tokenizer:
            bos_token_id, eos_token_id, pad_token_id = 128000, 128009, None
            def get_vocab(self):
                return {"<|eot_id|>": 128009}
            def encode(self, text, add_special_tokens=False, **kwargs):
                return [128000, 42] if text == "native chat" else [42]
            def apply_chat_template(self, *args, **kwargs):
                return kwargs["date_string"]
        tokenizer = cross.LlamaTokenizer(Tokenizer())
        stops, pad = cross.stop_tokens(tokenizer, SimpleNamespace(eos_token_id=[128001, 128008, 128009]), SimpleNamespace(eos_token_id=128001, vocab_size=128256))
        self.assertEqual(stops, [128001, 128008, 128009])
        self.assertEqual(pad, 128009)
        self.assertEqual(tokenizer.encode("native chat"), [128000, 42])
        self.assertEqual(tokenizer.encode("plain"), [128000, 42])
        self.assertEqual(tokenizer.apply_chat_template([]), "26 Oct 2026")


if __name__ == "__main__":
    unittest.main()
