"""Multi-channel steering; reuse the frozen Qwen loader and decoder."""
from collections import defaultdict
from contextlib import contextmanager
import importlib.util
import math
from pathlib import Path
import time

BASE = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("recipe_survey_engine", BASE / "layer-survey-toy-v1-2026-10-27/survey_engine.py")
survey = importlib.util.module_from_spec(spec)
spec.loader.exec_module(survey)


class RecipeEngine(survey.SurveyEngine):
    def prompt_calibration(self, context):
        """A clean forward pass, lower median over prompt positions after the first."""
        assert all(not module._forward_pre_hooks for module in self.modules.values())
        tokens = survey.transfer.encode_text(self.tokenizer, context)
        assert len(tokens) >= 2
        row = {"context_sha256": survey.transfer.text_hash(context),
               "input_token_sha256": survey.transfer.token_hash(tokens), "input_token_count": len(tokens),
               "normalization": "per_prompt_median", "residual_scales": {}}
        started, handles = time.monotonic(), []
        try:
            for layer, block in enumerate(self.layers):
                def capture(_module, _args, output, layer=layer):
                    residual = output[0] if isinstance(output, tuple) else output
                    value = float(residual[0, 1:].float().norm(dim=-1).median())
                    assert math.isfinite(value) and value > 0
                    row["residual_scales"][str(layer)] = value
                handles.append(block.register_forward_hook(capture))
            with self.torch.inference_mode():
                self.model(**self._inputs([tokens]), use_cache=False, logits_to_keep=1)
        finally:
            for handle in handles:
                handle.remove()
        assert set(row["residual_scales"]) == {str(i) for i in range(32)}
        row["calibration_seconds"] = time.monotonic() - started
        return row

    def generate_recipe(self, context, points, calibration, generation):
        """Fresh state and paired seed, with only the source-declared decoder settings."""
        torch = self.torch
        assert calibration["context_sha256"] == survey.transfer.text_hash(context)
        tokens = survey.transfer.encode_text(self.tokenizer, context)
        assert len(tokens) + 128 <= self.max_length
        inputs = self._inputs([tokens])
        torch.manual_seed(generation["seed"])
        kwargs = {"do_sample": generation["do_sample"], "repetition_penalty": generation["repetition_penalty"]}
        if generation["do_sample"]:
            kwargs.update({key: generation[key] for key in ("temperature", "top_p", "top_k", "min_p")})
        torch.cuda.synchronize(self.device)
        started = time.monotonic()
        with torch.inference_mode(), self._intervention(points or "baseline", [calibration], inputs["attention_mask"]):
            output = self.model.generate(**inputs, **kwargs, max_new_tokens=128,
                use_cache=True, logits_to_keep=1, eos_token_id=self.stop_ids, pad_token_id=self.pad_id)
        torch.cuda.synchronize(self.device)
        seconds = time.monotonic() - started
        returned = output[0, inputs["input_ids"].shape[1]:].tolist()
        def decode(ids, skip_special_tokens):
            return self.tokenizer.decode(ids, skip_special_tokens=skip_special_tokens, clean_up_tokenization_spaces=False)
        result = survey.transfer._v2.finish_generation(returned, self.stop_ids, self.pad_id, 128, None, [], decode)
        result.update(input_token_sha256=survey.transfer.token_hash(tokens), batch_seconds=seconds, batch_size=1,
                      effective_generation=generation)
        return result

    @contextmanager
    def _intervention(self, arm, calibrations, input_mask):
        assert all(not module._forward_pre_hooks for module in self.modules.values())
        assert len(calibrations) == input_mask.shape[0] == 1
        self.last_hook = []
        if arm == "baseline":
            yield
            return
        assert isinstance(arm, list) and arm
        groups, seen = defaultdict(list), set()
        for item in arm:
            layer, neuron, dose = item["layer"], item["neuron"], item["dose"]
            assert type(layer) is type(neuron) is int
            assert layer in self.modules and 0 <= neuron < self.modules[layer].weight.shape[1]
            assert (layer, neuron) not in seen and math.isfinite(dose)
            seen.add((layer, neuron))
            norm = float(self.column_norms[str(layer)][neuron])
            scale = calibrations[0]["residual_scales"][str(layer)]
            assert math.isfinite(norm) and norm > 0 and math.isfinite(scale) and scale > 0
            requested = dose * scale / norm
            amount = self.modules[layer].weight.new_tensor(requested)
            row = {"layer": layer, "neuron": neuron, "dose": dose, "column_norm": norm,
                   "reference_residual_scale": scale, "requested_offset": requested,
                   "bf16_offset": float(amount), "calls": 0, "positions": 0}
            groups[layer].append((neuron, amount, row))
            self.last_hook.append(row)
        handles = []
        try:
            for layer, items in groups.items():
                def add(_module, args, items=items):
                    original = args[0]
                    changed = original.clone()
                    width = original.shape[1]
                    assert width == input_mask.shape[1] or width == 1
                    mask = input_mask.to(original.dtype) if width == input_mask.shape[1] else 1.0
                    for neuron, amount, row in items:
                        changed[..., neuron] += amount * mask
                        assert self.torch.isfinite(changed[..., neuron]).all().item()
                        row["calls"] += 1
                        row["positions"] += width
                        if row["calls"] == 1:
                            expected = (original[..., neuron].float() + (amount * mask).float()).to(original.dtype)
                            assert self.torch.equal(changed[..., neuron], expected)
                            row["prefill_target_values_checked"] = True
                            row["prefill_first_original"] = float(original[0, 0, neuron])
                            row["prefill_first_changed"] = float(changed[0, 0, neuron])
                            row["prefill_first_actual_delta"] = row["prefill_first_changed"] - row["prefill_first_original"]
                    return (changed, *args[1:])
                handles.append(self.modules[layer].register_forward_pre_hook(add))
            yield
        finally:
            for handle in handles:
                handle.remove()


def validate_hook(audit, interventions, calibration, generated_count):
    assert len(audit) == len(interventions)
    for row, item in zip(audit, interventions):
        assert all(row[key] == item[key] for key in ("layer", "neuron", "dose"))
        scale = calibration["residual_scales"][str(item["layer"])]
        assert row["reference_residual_scale"] == scale
        assert row["requested_offset"] == item["dose"] * scale / row["column_norm"]
        assert row["calls"] == generated_count
        assert row["positions"] == calibration["input_token_count"] + generated_count - 1
        assert row["prefill_target_values_checked"] is True
    return True
