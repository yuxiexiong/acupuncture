"""Joint measurement hooks; imports do not load torch, transformers or a model."""
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("joint_frozen_transfer_engine",
    HERE.parent / "transfer-toy-v1-2026-10-26/transfer_engine.py")
_transfer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_transfer)
TransferEngine = _transfer.TransferEngine
encode_text = _transfer.encode_text
text_hash, token_hash = _transfer.text_hash, _transfer.token_hash
DOSES = (0.0, 0.0625, 0.125, 0.25, 0.5, 1.0)


def encode_pair(tokenizer, context, continuation):
    """Score only answer tokens after the exact generation prompt, including whitespace."""
    assert context and continuation
    prefix = encode_text(tokenizer, context)
    whole = encode_text(tokenizer, context + continuation)
    assert prefix and whole[:len(prefix)] == prefix, "Candidate changed prompt token boundary"
    suffix = whole[len(prefix):]
    assert suffix, "Candidate has no continuation tokens"
    return prefix, suffix


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        allow_nan=False).encode()).hexdigest()


def bf16_round(value):
    bits = struct.unpack("I", struct.pack("f", value))[0]
    bits = (bits + 0x7fff + ((bits >> 16) & 1)) & 0xffff0000
    return struct.unpack("f", struct.pack("I", bits))[0]


def bind_calibration(context, reference, tokenizer):
    """Keep the clean reference identity separate from this actual input."""
    scales = reference["residual_scales"]
    assert set(scales) == {"13", "14"}
    assert all(math.isfinite(v) and v > 0 for v in scales.values())
    tokens = encode_text(tokenizer, context)
    return {"context_sha256": text_hash(context), "input_token_sha256": token_hash(tokens),
        "input_token_count": len(tokens), "residual_scales": deepcopy(scales),
        "activation_offsets": {}, "reference_context_sha256": reference["context_sha256"],
        "reference_input_token_sha256": reference["input_token_sha256"],
        "reference_calibration_sha256": digest(reference)}


class JointEngine(_transfer.TransferEngine):
    def score(self, contexts, continuations, arm, calibrations):
        """One candidate, fresh state, and summed likelihood of answer tokens only."""
        assert len(contexts) == len(continuations) == len(calibrations) == 1
        context, continuation, calibration = contexts[0], continuations[0], calibrations[0]
        assert calibration["context_sha256"] == text_hash(context)
        prefix, suffix = encode_pair(self.tokenizer, context, continuation)
        tokens = prefix + suffix[:-1]
        inputs, torch = self._inputs([tokens]), self.torch
        with torch.inference_mode():
            with self._intervention(arm, calibrations, inputs["attention_mask"]):
                logits = self.model(**inputs, use_cache=False, logits_to_keep=len(suffix)).logits
            assert torch.isfinite(logits).all()
            selected = torch.log_softmax(logits[0, -len(suffix):], -1, dtype=torch.float32)
            targets = torch.tensor(suffix, dtype=torch.long, device=self.device)
            token_scores = selected.gather(-1, targets[:, None]).flatten()
            return [{"loglikelihood": token_scores.sum().item(),
                "is_greedy": bool((selected.argmax(-1) == targets).all()),
                "continuation_token_ids": suffix, "token_logprobs": token_scores.tolist(),
                "context_token_count": len(prefix), "input_token_sha256": token_hash(tokens)}]

    def configure(self, conditions):
        """Register only frozen native-channel pairs, plus a zero-write check."""
        self.conditions = {"baseline": {}, "zero": {str(l): {"kind": "channel",
            "index": _transfer.SOURCE_NEURONS[l], "scale": "target", "coefficient": 0.0}
            for l in (13, 14)}}
        self.condition_definitions = {}
        for condition in conditions:
            name, dose = condition["id"], condition["dose"]
            channels = condition["channels"]
            assert dose in DOSES and name != "zero"
            assert name not in self.condition_definitions, "Duplicate condition ID"
            assert (dose == 0 and not channels) or (dose > 0 and set(channels) == {"13", "14"})
            specs = {}
            for layer, index in channels.items():
                assert type(index) is int and 0 <= index < len(self.column_norms[layer])
                norm = float(self.column_norms[layer][index])
                assert math.isfinite(norm) and norm > 0
                specs[layer] = {"kind": "channel", "index": index, "scale": "target",
                    "coefficient": dose * _transfer.SIGNS[int(layer)] / norm}
            assert name != "baseline" or not specs
            self.conditions[name] = specs
            self.condition_definitions[name] = deepcopy(condition)
        self.last_audit = {}

    @contextmanager
    def _intervention(self, arm, calibrations, input_mask):
        """Audit the unchanged parent hook on prefill and every cached step."""
        assert len(calibrations) == input_mask.shape[0] == 1
        self.last_audit = {}
        stats, before, handles = {}, {}, []
        torch = self.torch
        with super()._intervention(arm, calibrations, input_mask):
            try:
                for layer, spec in self.conditions[arm].items():
                    assert spec["kind"] == "channel" and spec["scale"] == "target"
                    module, index = self.modules[int(layer)], spec["index"]
                    norm = float(self.column_norms[layer][index])
                    scale = calibrations[0]["residual_scales"][layer]
                    requested = scale * spec["coefficient"]
                    amount = module.weight.new_tensor(requested)
                    row = {"channel": index, "column_norm": norm,
                        "clean_residual_scale": scale, "requested_offset": requested,
                        "bf16_offset": float(amount), "requested_vector_norm": abs(requested) * norm,
                        "bf16_offset_vector_norm": abs(float(amount)) * norm,
                        "calls": 0, "positions": 0, "widths": [],
                        "nonzero": torch.zeros((), device=self.device, dtype=torch.long),
                        "total": torch.zeros((), device=self.device, dtype=torch.float64),
                        "minimum": torch.tensor(float("inf"), device=self.device),
                        "maximum": torch.tensor(float("-inf"), device=self.device),
                        "target_ok": torch.tensor(True, device=self.device),
                        "untouched_ok": torch.tensor(True, device=self.device),
                        "padding_ok": torch.tensor(True, device=self.device)}
                    stats[layer] = row

                    def capture(_module, args, layer=layer):
                        # Parent clones before editing, so this reference remains pristine.
                        before[layer] = args[0].detach()

                    def audit(_module, args, layer=layer, index=index, amount=amount):
                        old, changed, row = before[layer], args[0], stats[layer]
                        assert old.shape == changed.shape and old.ndim == 3 and old.shape[0] == 1
                        width = changed.shape[1]
                        assert width == input_mask.shape[1] or width == 1
                        mask = input_mask.bool() if width == input_mask.shape[1] else torch.ones(
                            changed.shape[:2], dtype=torch.bool, device=changed.device)
                        expected = old[..., index] + amount * mask.to(old.dtype)
                        row["target_ok"] &= (changed[..., index] == expected).all()
                        row["untouched_ok"] &= (old[..., :index] == changed[..., :index]).all()
                        row["untouched_ok"] &= (old[..., index + 1:] == changed[..., index + 1:]).all()
                        row["padding_ok"] &= (old[~mask] == changed[~mask]).all()
                        difference = (changed[..., index].float() - old[..., index].float())[mask]
                        row["calls"] += 1
                        row["positions"] += difference.numel()
                        row["widths"].append(width)
                        row["nonzero"] += (difference != 0).sum()
                        row["total"] += difference.sum(dtype=torch.float64)
                        row["minimum"] = torch.minimum(row["minimum"], difference.min())
                        row["maximum"] = torch.maximum(row["maximum"], difference.max())
                        if row["calls"] == 1:
                            assert width == input_mask.shape[1]
                            row["first"] = torch.stack((old[..., index][mask][0],
                                changed[..., index][mask][0], expected[mask][0])).float()

                    handles.append(module.register_forward_pre_hook(capture, prepend=True))
                    handles.append(module.register_forward_pre_hook(audit))
                yield
            finally:
                for handle in handles:
                    handle.remove()
                for layer, row in stats.items():
                    if not row["calls"]:
                        self.last_audit[layer] = {"channel": row["channel"], "calls": 0}
                        continue
                    scalar_keys = ("channel", "column_norm", "clean_residual_scale", "requested_offset",
                        "bf16_offset", "requested_vector_norm", "bf16_offset_vector_norm",
                        "calls", "positions", "widths")
                    first = row["first"].tolist()
                    self.last_audit[layer] = {**{key: row[key] for key in scalar_keys},
                        "nonzero_positions": int(row["nonzero"]),
                        "actual_offset_min": float(row["minimum"]),
                        "actual_offset_max": float(row["maximum"]),
                        "actual_offset_mean": float(row["total"] / row["positions"]),
                        "prefill_first_original": first[0], "prefill_first_changed": first[1],
                        "prefill_first_expected": first[2],
                        "all_target_values_match_bf16_addition": bool(row["target_ok"]),
                        "non_target_values_unchanged": bool(row["untouched_ok"]),
                        "padded_positions_unchanged": bool(row["padding_ok"])}


def validate_audit(audit, condition, calibration, prompt_length,
                   generated_count=None, input_length=None):
    """Verify actual writes; weak-dose rounding to zero remains valid evidence."""
    assert (generated_count is None) != (input_length is None)
    channels, dose = condition["channels"], condition["dose"]
    assert set(audit) == set(channels)
    calls = generated_count if generated_count is not None else 1
    positions = prompt_length + generated_count - 1 if generated_count is not None else input_length
    widths = [prompt_length] + [1] * (calls - 1) if generated_count is not None else [input_length]
    for layer, row in audit.items():
        norm, scale = row["column_norm"], calibration["residual_scales"][layer]
        assert math.isfinite(norm) and norm > 0
        requested = scale * (dose * _transfer.SIGNS[int(layer)] / norm)
        assert row["channel"] == channels[layer] and row["clean_residual_scale"] == scale
        assert row["requested_offset"] == requested and row["bf16_offset"] == bf16_round(requested)
        assert row["requested_vector_norm"] == abs(requested) * norm
        assert row["bf16_offset_vector_norm"] == abs(row["bf16_offset"]) * norm
        assert row["calls"] == calls and row["positions"] == positions and row["widths"] == widths
        assert 0 <= row["nonzero_positions"] <= positions
        assert all(row[key] is True for key in ("all_target_values_match_bf16_addition",
            "non_target_values_unchanged", "padded_positions_unchanged"))
        assert row["prefill_first_changed"] == row["prefill_first_expected"]
        assert row["prefill_first_expected"] == bf16_round(
            row["prefill_first_original"] + row["bf16_offset"])
        values = [row[key] for key in ("actual_offset_min", "actual_offset_max", "actual_offset_mean")]
        assert all(math.isfinite(v) for v in values)
        assert values[0] <= values[2] <= values[1]
        if dose == 0:
            assert values == [0.0, 0.0, 0.0] and row["nonzero_positions"] == 0
        else:
            assert all(_transfer.SIGNS[int(layer)] * value >= 0 for value in values)
    return True
