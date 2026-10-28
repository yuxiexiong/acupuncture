"""Mirror the frozen single-channel hook; +1 is reserved for preflight replay."""
from contextlib import contextmanager
import importlib.util
import math
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("dose_frozen_survey_engine", BASE / "layer-survey-toy-v1-2026-10-27/survey_engine.py")
survey = importlib.util.module_from_spec(spec)
spec.loader.exec_module(survey)
DOSES = (-0.0625, -0.125, -0.25, -0.5, -1.0, 0.0, 1.0)


class DoseEngine(survey.SurveyEngine):
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
        # Calculate every dose from the original double precision ratio, before BF16.
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
