"""Versioned controls on the frozen SurveyEngine; imports never load a model."""
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import time
from types import MethodType

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("control_frozen_survey",
    HERE.parent / "layer-survey-toy-v1-2026-10-27/survey_engine.py")
survey = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(survey)
encode_text = survey.transfer.encode_text
text_hash, token_hash = survey.transfer.text_hash, survey.transfer.token_hash
MODES = ("full", "prefill", "decode", "prompt_last", "prompt_except_last")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        allow_nan=False, separators=(",", ":")).encode()).hexdigest()


def selection_mask(mode, prediction_step, width, prompt_length, active=True):
    assert mode in MODES and prediction_step >= 0 and prompt_length >= 1
    assert width == (prompt_length if prediction_step == 0 else 1)
    if not active:
        return [False] * width
    if mode == "full":
        return [True] * width
    if mode == "decode":
        return [prediction_step > 0] * width
    if prediction_step > 0:
        return [False] * width
    if mode == "prefill":
        return [True] * width
    if mode == "prompt_last":
        return [i == width - 1 for i in range(width)]
    return [i != width - 1 for i in range(width)]


def exact_pair(tokenizer, context, continuation):
    assert context and continuation
    prompt = encode_text(tokenizer, context)
    whole = encode_text(tokenizer, context + continuation)
    assert prompt and whole[:len(prompt)] == prompt, "Candidate changed the complete prompt"
    suffix = whole[len(prompt):]
    assert suffix
    return prompt, suffix


def tensor_hash(tensor):
    raw = tensor.detach().contiguous().cpu().reshape(-1).view(dtype=__import__("torch").uint8)
    return hashlib.sha256(raw.numpy().tobytes()).hexdigest()


def state_fingerprint(value):
    """Record cache tensors and structural/scalar state, without object addresses."""
    seen = {}

    def visit(item, path):
        if item is None or isinstance(item, (str, bool, int)):
            return item
        if isinstance(item, float):
            return item if math.isfinite(item) else str(item)
        if hasattr(item, "detach") and hasattr(item, "shape"):
            return {"dtype": str(item.dtype), "shape": list(item.shape), "sha256": tensor_hash(item)}
        if id(item) in seen:
            return {"alias": seen[id(item)]}
        seen[id(item)] = path
        if isinstance(item, dict):
            return {str(k): visit(v, f"{path}.{k}") for k, v in sorted(item.items(), key=lambda p: str(p[0]))}
        if isinstance(item, (tuple, list)):
            return [visit(v, f"{path}.{i}") for i, v in enumerate(item)]
        if hasattr(item, "__dict__"):
            return {"class": type(item).__qualname__, "fields": visit(vars(item), path + ".fields")}
        return {"class": type(item).__qualname__}

    payload = visit(value, "cache")
    return {"sha256": digest(payload), "state": payload}


def bind_reference(context, reference, tokenizer):
    scales = reference["residual_scales"]
    assert scales and all(math.isfinite(v) and v > 0 for v in scales.values())
    tokens = encode_text(tokenizer, context)
    return {"context_sha256": text_hash(context), "input_token_sha256": token_hash(tokens),
        "input_token_count": len(tokens), "residual_scales": dict(scales),
        "reference_context_sha256": reference["context_sha256"],
        "reference_input_token_sha256": reference["input_token_sha256"],
        "reference_calibration_sha256": digest(reference)}


class ControlEngine(survey.SurveyEngine):
    def _component(self, layer, component):
        block = self.layers[layer]
        if component == "mlp":
            return block.mlp
        assert component == "attention"
        return block.linear_attn if hasattr(block, "linear_attn") else block.self_attn

    def _validate_condition(self, condition, reference):
        assert condition["kind"] in ("clean", "native", "direction")
        if condition["kind"] == "clean":
            assert condition.get("dose", 0) == 0
            return
        layer, dose = condition["layer"], condition["dose"]
        assert type(layer) is int and layer in self.modules and math.isfinite(dose)
        assert str(layer) in reference["residual_scales"]
        if condition["kind"] == "native":
            channel = condition["channel"]
            assert type(channel) is int and 0 <= channel < self.modules[layer].weight.shape[1]
        else:
            vector = condition["vector"]
            assert len(vector) == self.modules[layer].weight.shape[0]
            assert all(math.isfinite(x) for x in vector)
            assert math.isclose(math.sqrt(sum(x*x for x in vector)), 1., rel_tol=1e-5, abs_tol=1e-6)

    @contextmanager
    def _control_hooks(self, condition, reference, mode, prompt_length, state,
                       fork_step, branch_kind, capture_steps, patch, capture):
        torch, handles = self.torch, []
        self._validate_condition(condition, reference)
        assert mode in MODES
        for spec in (patch, capture):
            if spec is not None:
                assert type(spec["layer"]) is int and 0 <= spec["layer"] < len(self.layers)
                assert type(spec["prediction_step"]) is int and 0 <= spec["prediction_step"] < 128
                self._component(spec["layer"], spec["component"])
        if patch is not None:
            donor = patch["donor"]
            assert all(donor[key] == patch[key] for key in ("layer", "component", "prediction_step")), "Patch donor identity mismatch"
            assert tensor_hash(donor["vector"]) == donor["vector_sha256"]
            assert donor["reference_calibration_sha256"] == digest(reference), "Patch calibration mismatch"

        def start_call(_module, args, kwargs):
            state["step"] += 1
            step = state["step"]
            if step in capture_steps:
                state["cache_fingerprints"][str(step)] = state_fingerprint(kwargs.get("past_key_values"))

        def raw_logits(_module, _args, output):
            state["logits"] = output.logits[0, -1].detach()

        handles.append(self.model.register_forward_pre_hook(start_call, with_kwargs=True))
        handles.append(self.model.register_forward_hook(raw_logits))

        def enabled_mask(width, device):
            active = branch_kind != "rebuild" and not (
                branch_kind == "withdraw" and state["step"] >= fork_step)
            return torch.tensor(selection_mask(mode, state["step"], width, prompt_length, active),
                                dtype=torch.bool, device=device).reshape(1, -1)

        if condition["kind"] != "clean":
            layer = condition["layer"]
            weight = self.modules[layer].weight
            scale, dose = reference["residual_scales"][str(layer)], condition["dose"]
            if condition["kind"] == "native":
                channel = condition["channel"]
                column_norm = float(self.column_norms[str(layer)][channel])
                assert math.isfinite(column_norm) and column_norm > 0
                requested = dose * scale / column_norm
                amount = weight.new_tensor(requested)

                def add_channel(_module, args):
                    original = args[0]
                    mask = enabled_mask(original.shape[1], original.device)
                    changed = original.clone()
                    changed[..., channel] += amount * mask.to(original.dtype)
                    expected = original[..., channel] + amount * mask.to(original.dtype)
                    delta = changed[..., channel].float() - original[..., channel].float()
                    assert torch.isfinite(changed[..., channel]).all()
                    untouched = torch.equal(original[..., :channel], changed[..., :channel]) and torch.equal(
                        original[..., channel+1:], changed[..., channel+1:])
                    masked = torch.equal(original[~mask], changed[~mask])
                    assert untouched and masked and torch.equal(changed[..., channel], expected)
                    selected = delta[mask]
                    state["write_audit"].append({"prediction_step": state["step"], "layer": layer,
                        "kind": "native", "channel": channel, "width": original.shape[1],
                        "mask": mask[0].tolist(), "positions": int(mask.sum()),
                        "clean_residual_scale": scale, "dose": dose, "column_norm": column_norm,
                        "requested_offset": requested, "bf16_offset": float(amount),
                        "requested_vector_norm": abs(dose) * scale,
                        "actual_offset_min": float(selected.min()) if selected.numel() else 0.,
                        "actual_offset_max": float(selected.max()) if selected.numel() else 0.,
                        "actual_projected_delta_norm_max": float(selected.abs().max()) * column_norm if selected.numel() else 0.,
                        "nonzero_positions": int((selected != 0).sum()),
                        "target_values_match": True, "non_target_values_unchanged": untouched,
                        "masked_positions_unchanged": masked})
                    return (changed, *args[1:])

                handles.append(self.modules[layer].register_forward_pre_hook(add_channel))
            else:
                vector = torch.tensor(condition["vector"], device=self.device, dtype=torch.float32)
                addition = (vector * (dose * scale)).to(weight.dtype)

                def add_direction(_module, _args, output):
                    original = output[0] if isinstance(output, tuple) else output
                    mask = enabled_mask(original.shape[1], original.device)
                    changed = original + mask[..., None].to(original.dtype) * addition
                    expected = original + mask[..., None].to(original.dtype) * addition
                    assert torch.isfinite(changed).all() and torch.equal(changed, expected)
                    masked = torch.equal(original[~mask], changed[~mask])
                    assert masked
                    norms = (changed.float() - original.float()).norm(dim=-1)[mask]
                    state["write_audit"].append({"prediction_step": state["step"], "layer": layer,
                        "kind": "direction", "width": original.shape[1], "mask": mask[0].tolist(),
                        "positions": int(mask.sum()), "clean_residual_scale": scale, "dose": dose,
                        "direction_sha256": digest(condition["vector"]),
                        "requested_vector_norm": abs(dose) * scale,
                        "bf16_addition_norm": float(addition.float().norm()),
                        "actual_delta_norm_min": float(norms.min()) if norms.numel() else 0.,
                        "actual_delta_norm_max": float(norms.max()) if norms.numel() else 0.,
                        "target_values_match": True, "masked_positions_unchanged": masked})
                    return (changed, *output[1:]) if isinstance(output, tuple) else changed

                handles.append(self.layers[layer].mlp.register_forward_hook(add_direction))

        # Capture precedes replacement and follows any intervention on that component.
        if capture is not None:
            def save_component(_module, _args, output):
                if state["step"] == capture["prediction_step"]:
                    value = output[0] if isinstance(output, tuple) else output
                    state["captured"] = value[0, -1].detach().clone().cpu()
            handles.append(self._component(capture["layer"], capture["component"]).register_forward_hook(save_component))

        if patch is not None:
            def replace_component(_module, _args, output):
                if state["step"] != patch["prediction_step"]:
                    return output
                original = output[0] if isinstance(output, tuple) else output
                donor = patch["donor"]
                assert donor["prefix_token_sha256"] == token_hash(state["history"]), "Patch generated history mismatch"
                vector = donor["vector"].to(device=original.device, dtype=original.dtype)
                assert vector.shape == original[0, -1].shape and torch.isfinite(vector).all()
                assert tensor_hash(donor["vector"]) == donor["vector_sha256"]
                changed = original.clone()
                changed[0, -1] = vector
                before, after = original[0, -1].float(), changed[0, -1].float()
                assert torch.equal(original[:, :-1], changed[:, :-1])
                state["patch_audit"].append({"layer": patch["layer"], "component": patch["component"],
                    "prediction_step": state["step"], "position": original.shape[1] - 1,
                    "donor_id": patch.get("donor_id", donor["id"]),
                    "donor_metadata": {k: v for k, v in donor.items() if k != "vector"},
                    "before_sha256": tensor_hash(original[0, -1]), "after_sha256": tensor_hash(changed[0, -1]),
                    "before_norm": float(before.norm()), "after_norm": float(after.norm()),
                    "delta_norm": float((after-before).norm()), "delta_max_abs": float((after-before).abs().max()),
                    "other_positions_unchanged": True})
                return (changed, *output[1:]) if isinstance(output, tuple) else changed
            handles.append(self._component(patch["layer"], patch["component"]).register_forward_hook(replace_component))
        try:
            yield
        finally:
            for handle in reversed(handles):
                handle.remove()

    def _run(self, context, reference, condition, mode, max_new_tokens, capture_steps,
             target_token_ids, patch, capture, forced_prefix=(), branch_kind="continue",
             require_prefix_greedy=False, score_targets=(), retain_fork_logits=False):
        from transformers import LogitsProcessor, LogitsProcessorList
        torch, tokenizer = self.torch, self.tokenizer
        prompt = encode_text(tokenizer, context)
        assert prompt and 1 <= max_new_tokens <= 128 and len(prompt) + max_new_tokens <= self.max_length
        assert len(forced_prefix) <= max_new_tokens
        assert not any(t in self.stop_ids for t in forced_prefix[:-1])
        state = {"step": -1, "write_audit": [], "patch_audit": [], "cache_fingerprints": {},
                 "readouts": [], "captured": None, "forced_prefix_matches_greedy": True, "history": []}
        fork_step = len(forced_prefix)
        if branch_kind != "continue":
            capture_steps = tuple(set(capture_steps) | {fork_step})
        engine = self

        class ReadAndForce(LogitsProcessor):
            def __call__(self, input_ids, scores):
                step = input_ids.shape[1] - len(prompt)
                assert step == state["step"]
                assert input_ids[0, :len(prompt)].tolist() == prompt
                assert input_ids[0, len(prompt):len(prompt)+min(step, fork_step)].tolist() == list(forced_prefix[:step])
                greedy = int(scores[0].argmax())
                actual = int(forced_prefix[step]) if step < fork_step else greedy
                if step < fork_step and actual != greedy:
                    state["forced_prefix_matches_greedy"] = False
                    assert not require_prefix_greedy, "Source prefix does not replay under the specified intervention"
                logits = state.pop("logits").float()
                assert torch.isfinite(logits).all()
                if retain_fork_logits and step == fork_step:
                    state["_fork_logits"] = logits.detach().cpu().clone()
                top = logits.topk(min(32, logits.numel()))
                requested = set(map(int, target_token_ids)) | set(engine.stop_ids) | {actual, greedy}
                if step < len(score_targets):
                    requested.add(int(score_targets[step]))
                assert all(0 <= t < logits.numel() for t in requested)
                log_probs = torch.log_softmax(logits, dim=-1)
                non_stop = logits.clone()
                non_stop[engine.stop_ids] = -float("inf")
                top_ids, requested_ids = top.indices.cpu().tolist(), sorted(requested)
                selected_ids = top_ids + requested_ids
                selected = torch.stack((logits[selected_ids], log_probs[selected_ids]), dim=-1).cpu().tolist()
                top_rows = [{"token_id": t, "logit": values[0], "logprob": values[1]}
                            for t, values in zip(top_ids, selected[:len(top_ids)])]
                requested_rows = {str(t): {"logit": values[0], "logprob": values[1]}
                                  for t, values in zip(requested_ids, selected[len(top_ids):])}
                state["readouts"].append({"prediction_step": step,
                    "prefix_token_sha256": token_hash(input_ids[0].tolist()),
                    "actual_token_id": actual, "greedy_token_id": greedy,
                    "actual_logit": requested_rows[str(actual)]["logit"],
                    "actual_logprob": requested_rows[str(actual)]["logprob"],
                    "top32": top_rows, "requested": requested_rows,
                    "stop_advantage": float(logits[engine.stop_ids].max() - non_stop.max()),
                    "logits_sha256": tensor_hash(logits) if step in capture_steps else None})
                state["history"].append(actual)
                if step < fork_step:
                    selected = torch.full_like(scores, -float("inf"))
                    selected[0, actual] = 0.
                    return selected
                return scores

        inputs = self._inputs([prompt])
        if str(self.device).startswith("cuda"):
            torch.cuda.synchronize(self.device)
        started = time.monotonic()
        with torch.inference_mode(), self._control_hooks(condition, reference, mode, len(prompt), state,
                fork_step, branch_kind, set(capture_steps), patch, capture):
            output = self.model.generate(**inputs, do_sample=False, max_new_tokens=max_new_tokens,
                use_cache=True, logits_to_keep=1, eos_token_id=self.stop_ids, pad_token_id=self.pad_id,
                logits_processor=LogitsProcessorList([ReadAndForce()]))
        if str(self.device).startswith("cuda"):
            torch.cuda.synchronize(self.device)
        seconds = time.monotonic() - started
        tokens = output[0, len(prompt):].tolist()
        assert tokens[:fork_step] == list(forced_prefix)
        assert len(tokens) == len(state["readouts"])
        assert tokens == [r["actual_token_id"] for r in state["readouts"]]
        assert tokens and not any(t in self.stop_ids for t in tokens[:-1])
        assert tokens[-1] in self.stop_ids or len(tokens) == max_new_tokens
        bound = bind_reference(context, reference, tokenizer)
        result = {"status": "completed", "token_ids": tokens, "generated_token_count": len(tokens),
            "raw_text": tokenizer.decode(tokens, skip_special_tokens=False, clean_up_tokenization_spaces=False),
            "answer_text": tokenizer.decode(tokens, skip_special_tokens=True, clean_up_tokenization_spaces=False),
            "returned_padding_count": 0, "max_new_tokens": max_new_tokens,
            "end_reason": "eos_token" if tokens[-1] in self.stop_ids else "length_limit",
            "input_token_sha256": token_hash(prompt), "token_sha256": token_hash(tokens),
            "context_token_count": len(prompt), "calibration": bound,
            "condition": condition, "mode": mode, "branch_kind": branch_kind,
            "forced_prefix_tokens": list(forced_prefix), "fork_step": fork_step,
            "forced_prefix_matches_greedy": state["forced_prefix_matches_greedy"],
            "step_readouts": state["readouts"], "write_audit": state["write_audit"],
            "patch_audit": state["patch_audit"], "cache_fingerprints": state["cache_fingerprints"],
            "batch_seconds": seconds, "seconds": seconds, "fresh_cache": True,
            "logits_hash_scope": "full_vocabulary_at_capture_steps_only"}
        if capture is not None:
            assert state["captured"] is not None, "Capture position was not reached"
            result["captured"] = state["captured"]
        if retain_fork_logits:
            result["_fork_logits"] = state["_fork_logits"]
        return result

    def generate_one(self, context, reference, condition, mode="full", max_new_tokens=128,
                     capture_steps=(0, 4, 16), target_token_ids=(), patch=None, capture=None):
        return self._run(context, reference, condition, mode, max_new_tokens, capture_steps,
                         target_token_ids, patch, capture)

    def branch(self, context, reference, condition, prefix_tokens, kind="continue", max_new_tokens=128,
               mode="full", capture_steps=(0, 4, 16), target_token_ids=(), patch=None,
               retain_fork_logits=False):
        assert kind in ("continue", "withdraw", "rebuild")
        assert all(type(t) is int and t >= 0 for t in prefix_tokens)
        if any(t in self.stop_ids for t in prefix_tokens) or len(prefix_tokens) >= max_new_tokens:
            return {"status": "not_applicable", "reason": "source_ended_before_fork_or_budget_exhausted",
                    "fork_step": len(prefix_tokens), "prefix_tokens": list(prefix_tokens)}
        return self._run(context, reference, condition, mode, max_new_tokens,
            tuple(set(capture_steps) | {len(prefix_tokens)}), target_token_ids, patch, None,
            forced_prefix=prefix_tokens, branch_kind=kind, require_prefix_greedy=(kind != "rebuild"),
            retain_fork_logits=retain_fork_logits)

    def score_one(self, context, continuation, reference, condition, mode="full", verify_logits=False):
        prompt, suffix = exact_pair(self.tokenizer, context, continuation)
        assert len(suffix) <= 128 and not any(t in self.stop_ids for t in suffix[:-1])
        capture_steps = tuple(range(len(suffix))) if verify_logits else ()
        result = self._run(context, reference, condition, mode, len(suffix), capture_steps, (), None, None,
                           forced_prefix=suffix, score_targets=suffix)
        scores = [r["requested"][str(t)]["logprob"] for r, t in zip(result["step_readouts"], suffix)]
        result.update(continuation_token_ids=suffix, token_logprobs=scores, loglikelihood=sum(scores),
                      is_greedy=result["forced_prefix_matches_greedy"], context_token_count=len(prompt))
        return result

    def manual_score_one(self, context, continuation, reference, condition, mode="full"):
        """Independent incremental forwards: no generate, forced processor, or combined suffix prefill."""
        torch = self.torch
        prompt, suffix = exact_pair(self.tokenizer, context, continuation)
        assert len(prompt) + len(suffix) <= self.max_length and len(suffix) <= 128
        assert not any(t in self.stop_ids for t in suffix[:-1])
        state = {"step": -1, "write_audit": [], "patch_audit": [], "cache_fingerprints": {}, "history": []}
        scores, hashes, widths, cache = [], [], [], None
        if str(self.device).startswith("cuda"):
            torch.cuda.synchronize(self.device)
        started = time.monotonic()
        with torch.inference_mode(), self._control_hooks(condition, reference, mode, len(prompt), state,
                0, "continue", set(), None, None):
            for step, target in enumerate(suffix):
                current = prompt if step == 0 else [suffix[step - 1]]
                inputs = self._inputs([current])
                inputs["attention_mask"] = torch.ones((1, len(prompt) + step), device=self.device, dtype=torch.long)
                # Explicit text positions, as generate passes them; never infer from stale model.rope_deltas.
                start = len(prompt) + step - len(current)
                inputs["position_ids"] = torch.arange(start, start + len(current), device=self.device).view(1, -1)
                output = self.model(**inputs, past_key_values=cache, use_cache=True, logits_to_keep=1)
                assert state["step"] == step and output.logits.shape[:2] == (1, 1)
                cache = output.past_key_values
                assert cache is not None, "Incremental reference did not return a cache"
                logits = output.logits[0, -1].detach().float()
                assert torch.isfinite(logits).all()
                scores.append(float(torch.log_softmax(logits, dim=-1)[target]))
                hashes.append(tensor_hash(logits))
                widths.append(len(current))
                state["history"].append(target)
                state.pop("logits")
        if str(self.device).startswith("cuda"):
            torch.cuda.synchronize(self.device)
        return {"status": "completed", "algorithm": "explicit_incremental_forward_without_generate",
            "continuation_token_ids": suffix, "token_logprobs": scores, "loglikelihood": sum(scores),
            "logits_sha256": hashes, "forward_input_widths": widths,
            "input_token_sha256": token_hash(prompt), "context_token_count": len(prompt),
            "calibration": bind_reference(context, reference, self.tokenizer),
            "write_audit": state["write_audit"], "fresh_cache": True,
            "seconds": time.monotonic() - started}

    def prepare_donor(self, context, reference, condition, *, layer, component, prediction_step,
                      prefix_tokens=(), mode="full", donor_id=None):
        assert len(prefix_tokens) == prediction_step and 0 <= prediction_step < 128
        assert not any(t in self.stop_ids for t in prefix_tokens)
        capture = {"layer": layer, "component": component, "prediction_step": prediction_step}
        output = self._run(context, reference, condition, mode, prediction_step + 1,
            (prediction_step,), (), None, capture, forced_prefix=prefix_tokens)
        vector = output.pop("captured")
        metadata = {"context_sha256": text_hash(context), "input_token_sha256": output["input_token_sha256"],
            "prefix_token_sha256": token_hash(list(prefix_tokens)), "condition_sha256": digest(condition),
            "reference_calibration_sha256": digest(reference), "layer": layer, "component": component,
            "prediction_step": prediction_step, "mode": mode, "vector_sha256": tensor_hash(vector),
            "source_readout": output["step_readouts"][-1], "source_seconds": output["seconds"]}
        return {"id": donor_id or digest(metadata), **metadata, "vector": vector}

    def legacy_generate(self, context, reference, condition, max_new_tokens=128):
        """Use the frozen negative/positive-one implementation for bounded replay checks."""
        spec = importlib.util.spec_from_file_location("control_legacy_negative",
            HERE.parent / "layer-negative-dose-survey-toy-v1-2026-10-27/dose_engine.py")
        negative = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(negative)
        arm = "baseline" if condition["kind"] == "clean" else (
            condition["layer"], condition["channel"], condition["dose"])
        assert condition["kind"] in ("clean", "native")
        bound = bind_reference(context, reference, self.tokenizer)
        previous = self._intervention
        try:
            self._intervention = MethodType(negative.DoseEngine._intervention, self)
            return super().generate([context], arm, [bound], max_new_tokens, [])[0]
        finally:
            self._intervention = previous

    def verify_unchanged(self):
        assert not self.model._forward_hooks and not self.model._forward_pre_hooks
        for layer in range(len(self.layers)):
            for name in ("attention", "mlp"):
                assert not self._component(layer, name)._forward_hooks
        return super().verify_unchanged()
