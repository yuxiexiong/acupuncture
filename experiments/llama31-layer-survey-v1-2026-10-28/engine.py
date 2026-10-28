"""Llama loader plus the frozen survey calibration and generation methods."""
from contextlib import contextmanager
import importlib.util
import math
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("llama_dose_survey_engine", BASE / "layer-survey-toy-v1-2026-10-27/survey_engine.py")
survey = importlib.util.module_from_spec(spec)
spec.loader.exec_module(survey)
spec = importlib.util.spec_from_file_location("llama_dose_cross_family_engine", BASE / "cross-family-transfer-toy-v1-2026-10-26/engine.py")
cross = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cross)
DOSES = (-1.0, -0.5, -0.25, -0.125, -0.0625, 0.0, 0.0625, 0.125, 0.25, 0.5, 1.0)


def effective_generation(model, stop_ids, pad_id):
    original = model.generation_config.to_dict()
    config, kwargs = model._prepare_generation_config(None, do_sample=False, max_new_tokens=128,
        use_cache=True, logits_to_keep=1, eos_token_id=stop_ids, pad_token_id=pad_id)
    assert model.generation_config.to_dict() == original, "Generation audit changed model defaults"
    neutral = {"num_beams": 1, "num_beam_groups": 1, "repetition_penalty": 1.0,
        "encoder_repetition_penalty": 1.0, "no_repeat_ngram_size": 0,
        "min_length": 0, "min_new_tokens": None, "forced_bos_token_id": None,
        "forced_eos_token_id": None, "suppress_tokens": None,
        "begin_suppress_tokens": None}
    current = {key: getattr(config, key, default) for key, default in neutral.items()}
    assert current == neutral, f"Unexpected generation policy: {current}"
    current["renormalize_logits"] = getattr(config, "renormalize_logits", None)
    assert current["renormalize_logits"] in (None, False)
    assert config.do_sample is False and config.max_new_tokens == 128 and config.use_cache is True
    assert config.eos_token_id == stop_ids and config.pad_token_id == pad_id
    assert kwargs["logits_to_keep"] == 1
    return {**current, "do_sample": False, "max_new_tokens": 128, "use_cache": True,
            "logits_to_keep": 1, "task_stop_strings": [],
            "resolved_by": "model._prepare_generation_config(None, explicit frozen generate arguments)",
            "temperature_top_p": "inactive because generate explicitly passes do_sample=False"}


class Engine(survey.SurveyEngine):
    def __init__(self, model_path, model_spec, device):
        cross.CrossFamilyEngine.__init__(self, model_path, device=device, batch_size=1, threads=4)
        assert self.model.config.model_type == "llama"
        assert len(self.layers) == model_spec["layers"] == 32
        assert self.metadata["hidden_size"] == model_spec["hidden_size"]
        assert self.metadata["intermediate_size"] == model_spec["intermediate_size"]
        self.modules = {i: block.mlp.down_proj for i, block in enumerate(self.layers)}
        shape = (model_spec["hidden_size"], model_spec["intermediate_size"])
        assert all(module.bias is None and tuple(module.weight.shape) == shape for module in self.modules.values())
        self.column_norms = {str(i): module.weight.float().norm(dim=0).cpu() for i, module in self.modules.items()}
        self.weight_hashes = self._weight_hashes()
        self.metadata.update(layers=list(self.modules), target_weight_sha256_before=self.weight_hashes,
            model_id=model_spec["id"], revision=model_spec["revision"], chat_template_applied=True,
            enable_thinking=None, thinking_control="not applicable to Llama native template",
            tokenization="Native Llama chat template; its BOS is not duplicated; official native EOS IDs",
            calibration="Original clean prompt block-output token L2 median, excluding the first token",
            intervention="One gated MLP channel before down_proj, prompt and every generated position")
        self.metadata["effective_generation"] = effective_generation(self.model, self.stop_ids, self.pad_id)
        self.metadata["sampling_defaults_inactive"] = {
            key: getattr(self.model.generation_config, key, None) for key in ("do_sample", "temperature", "top_p")}
        self.last_hook = None

    @contextmanager
    def _intervention(self, arm, calibrations, input_mask):
        assert all(not module._forward_pre_hooks for module in self.modules.values())
        self.last_hook = None
        if arm == "baseline":
            yield
            return
        layer, channel, dose = arm
        assert len(calibrations) == 1 and input_mask.shape[0] == 1
        assert layer in self.modules and 0 <= channel < self.modules[layer].weight.shape[1]
        assert dose in DOSES
        module = self.modules[layer]
        norm = float(self.column_norms[str(layer)][channel])
        scale = calibrations[0]["residual_scales"][str(layer)]
        assert math.isfinite(norm) and norm > 0 and math.isfinite(scale) and scale > 0
        # Every signed dose uses the original double ratio before its own BF16 cast.
        requested = dose * scale / norm
        amount = module.weight.new_tensor(requested)
        audit = {"layer": layer, "channel": channel, "dose": dose, "column_norm": norm,
                 "clean_residual_scale": scale, "requested_offset": requested,
                 "bf16_offset": float(amount), "calls": 0, "positions": 0}
        self.last_hook = audit

        def add_one(_module, args):
            original = args[0]
            changed = original.clone()
            width = original.shape[1]
            assert width == input_mask.shape[1] or width == 1
            mask = input_mask.to(original.dtype) if width == input_mask.shape[1] else 1.0
            changed[..., channel] += amount * mask
            assert self.torch.isfinite(changed[..., channel]).all().item(), "Nonfinite target activation"
            audit["calls"] += 1
            audit["positions"] += width
            if audit["calls"] == 1:
                expected = (original[..., channel].float() + (amount * mask).float()).to(original.dtype)
                assert self.torch.equal(changed[..., channel], expected)
                audit["prefill_target_values_checked"] = True
                audit["prefill_first_original"] = float(original[0, 0, channel])
                audit["prefill_first_changed"] = float(changed[0, 0, channel])
                audit["prefill_first_actual_delta"] = audit["prefill_first_changed"] - audit["prefill_first_original"]
            return (changed, *args[1:])

        handle = module.register_forward_pre_hook(add_one)
        try:
            yield
        finally:
            handle.remove()
