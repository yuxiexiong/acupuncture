"""Scoped 4B contribution experiments. Importing this file never loads a model.

Only attention/MLP contributions downstream of the source writes are patchable;
decoder residual outputs and the two injected MLPs are deliberately unavailable.
"""
from contextlib import contextmanager
import importlib.util
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "acupuncture_transfer_engine", HERE.parent / "transfer-toy-v1-2026-10-26/transfer_engine.py")
_transfer = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_transfer)
encode_pair, text_hash, token_hash = _transfer.encode_pair, _transfer.text_hash, _transfer.token_hash


def position_indices(scope, context_length, input_length):
    """Input position context_length-1 predicts the first continuation token."""
    if scope == "prompt_last":
        result = [context_length - 1]
    elif scope == "answer_tail":
        result = list(range(context_length, input_length))
    elif scope == "score_positions":
        result = list(range(context_length - 1, input_length))
    else:
        assert isinstance(scope, list) and all(type(p) is int for p in scope)
        result = scope
    assert len(result) == len(set(result)) and all(0 <= p < input_length for p in result)
    return result


def score_divisors(item):
    return [len(x) if item["benchmark"] == "arc_challenge" else 1
            for x in item["choices"]]


def summarize_scores(values, target):
    assert len(values) >= 2 and all(math.isfinite(x) for x in values)
    prediction = max(range(len(values)), key=values.__getitem__)
    wrong = max((i for i in range(len(values)) if i != target), key=values.__getitem__)
    return {"scores": values, "margin": values[target] - values[wrong],
            "prediction": prediction, "correct": prediction == target, "strongest_wrong": wrong}


def tensor_output(output):
    return output[0] if isinstance(output, tuple) else output


def replace_tensor_output(output, tensor):
    return (tensor, *output[1:]) if isinstance(output, tuple) else tensor


def scoped_replacement(torch, current, donor, positions, donor_positions, mode, seed):
    """The unrelated direction has the exact donor delta norm at each position."""
    assert current.ndim == donor.ndim == 3 and current.shape[0] == donor.shape[0] == 1
    assert current.shape[-1] == donor.shape[-1] and len(positions) == len(donor_positions)
    assert mode in ("donor", "matched")
    if not positions:
        return current, {"positions": [], "donor_positions": [], "mode": mode,
            "applicable": False, "reason": "empty_position_mask", "requested_delta_norm": [],
            "actual_delta_norm": [], "untouched_positions_identical": True}
    source = donor[:, donor_positions].to(device=current.device, dtype=current.dtype)
    old = current[:, positions]
    delta = source.float() - old.float()
    changed = current.clone()
    if mode == "donor":
        changed[:, positions] = source
    else:
        assert mode == "matched"
        generator = torch.Generator(device="cpu").manual_seed(seed)
        noise = torch.randn(delta.shape, generator=generator, dtype=torch.float32).to(current.device)
        noise = noise / noise.norm(dim=-1, keepdim=True).clamp_min(1e-30)
        changed[:, positions] = old + (noise * delta.norm(dim=-1, keepdim=True)).to(old.dtype)
    actual = changed[:, positions].float() - old.float()
    return changed, {"positions": positions, "donor_positions": donor_positions, "mode": mode, "applicable": True,
        "requested_delta_norm": delta.norm(dim=-1).flatten().tolist(),
        "actual_delta_norm": actual.norm(dim=-1).flatten().tolist(),
        "untouched_positions_identical": bool(torch.equal(
            changed[:, [p for p in range(current.shape[1]) if p not in positions]],
            current[:, [p for p in range(current.shape[1]) if p not in positions]]))}


class RootEngine(_transfer.TransferEngine):
    def __init__(self, model_path, device="cuda:0", threads=4):
        super().__init__(model_path, device=device, batch_size=1, threads=threads)
        assert self.metadata["hidden_size"] == 2560 and self.metadata["intermediate_size"] == 9216
        assert len(self.layers) == 32
        self.contributions = {}
        for layer in range(14, 32):
            block = self.layers[layer]
            attention = block.linear_attn if block.block_type == "linear_attention" else block.self_attn
            self.contributions[f"L{layer}.attention"] = attention
            if layer >= 15:
                self.contributions[f"L{layer}.mlp"] = block.mlp
        self.counts = {"forward": 0, "backward": 0, "calibration_forward": 0}
        self.make_condition("clean")
        self.make_condition("AB")

    def candidates(self):
        return list(self.contributions)

    def make_condition(self, name, dose=1.0, random_pair=None):
        assert dose in (0.5, 1.0)
        arm = f"{name}@{dose:g}"
        if random_pair is None:
            assert name in ("clean", "A", "B", "AB")
            layers = {"clean": (), "A": (14,), "B": (13,), "AB": (13, 14)}[name]
            pair = _transfer.SOURCE_NEURONS
        else:
            layers = (13, 14)
            pair = {int(k): int(v) for k, v in random_pair.items()}
            assert set(pair) == {13, 14}
            assert all(pair[l] != _transfer.SOURCE_NEURONS[l] for l in layers)
        specs = {}
        for layer in layers:
            index = pair[layer]
            assert 0 <= index < len(self.column_norms[str(layer)])
            norm = float(self.column_norms[str(layer)][index])
            assert math.isfinite(norm) and norm > 0
            specs[str(layer)] = {"kind": "channel", "index": index, "scale": "target",
                                 "coefficient": dose * _transfer.SIGNS[layer] / norm}
        if arm in self.conditions:
            assert self.conditions[arm] == specs, "Condition name reused with a different recipe"
        self.conditions[arm] = specs
        return arm

    def calibrate(self, contexts):
        rows = super().calibrate(contexts)
        self.counts["calibration_forward"] += len(contexts)
        return rows

    @contextmanager
    def _intervention(self, arm, calibrations, input_mask):
        self.last_source_audit = {}
        with super()._intervention(arm, calibrations, input_mask):
            handles, before = [], {}
            try:
                for key, spec in self.conditions[arm].items():
                    module, index = self.modules[int(key)], spec["index"]
                    def record_before(_module, args, key=key, index=index):
                        before[key] = args[0][..., index].detach().clone()
                    def record_after(_module, args, key=key, index=index):
                        difference = args[0][..., index].detach().float() - before[key].float()
                        valid = difference[input_mask.bool()]
                        self.last_source_audit[key] = {"channel": index, "positions": valid.numel(),
                            "offset_min": valid.min().item(), "offset_max": valid.max().item(),
                            "offset_mean": valid.mean().item(), "nonzero_positions": int((valid != 0).sum())}
                    handles.append(module.register_forward_pre_hook(record_before, prepend=True))
                    handles.append(module.register_forward_pre_hook(record_after))
                yield
                assert set(self.last_source_audit) == set(self.conditions[arm]), "Needle hook did not execute"
            finally:
                for handle in handles:
                    handle.remove()

    def _forward(self, tokens, arm, calibration, keep, gradient=False):
        inputs = self._inputs([tokens])
        with self._intervention(arm, [calibration], inputs["attention_mask"]):
            self.counts["forward"] += 1
            logits = self.model(**inputs, use_cache=False, logits_to_keep=keep).logits
        assert self.torch.isfinite(logits).all()
        return logits

    @contextmanager
    def _record(self, names, gradient=False):
        saved, handles = {}, []
        try:
            if gradient:
                # Sources have already been written at L13; all candidates are later.
                def start_graph(_module, _args, output):
                    return replace_tensor_output(output, tensor_output(output).detach().requires_grad_(True))
                handles.append(self.layers[13].register_forward_hook(start_graph))
            for name in names:
                assert name in self.contributions
                def capture(_module, _args, output, name=name):
                    value = tensor_output(output)
                    assert value.ndim == 3 and value.shape[0] == 1
                    saved[name] = value if gradient else value.detach().clone()
                handles.append(self.contributions[name].register_forward_hook(capture))
            yield saved
        finally:
            for handle in handles:
                handle.remove()

    def _choice(self, context, continuation, arm, calibration, patch=None, capture=None):
        torch = self.torch
        assert calibration["context_sha256"] == text_hash(context)
        context_ids, continuation_ids = encode_pair(self.tokenizer, context, continuation)
        tokens = context_ids + continuation_ids[:-1]
        capture = capture or []
        names = list(dict.fromkeys(row["component"] for row in capture))
        assert len(names) == len(capture), "Use one frozen position scope per independent reader"
        donor, patch_audit, handles = None, [], []
        if patch:
            assert patch["component"] in self.contributions
            def order(name):
                layer, kind = name.split(".")
                return int(layer[1:]), 0 if kind == "attention" else 1
            assert all(order(spec["component"]) > order(patch["component"]) for spec in capture), \
                "The independent reader must be downstream and unpatched"
            donor_context = patch.get("donor_context", context)
            donor_ids, donor_continuation = encode_pair(self.tokenizer, donor_context, continuation)
            donor_tokens = donor_ids + donor_continuation[:-1]
            if donor_context != context:
                assert len(donor_ids) == len(context_ids) and donor_continuation == continuation_ids, \
                    "Natural-function donor must have an exact token-position alignment"
                assert patch.get("donor_positions", patch["positions"]) == patch["positions"], \
                    "Natural-function donor uses the frozen same-position map"
            # Natural-function donors keep recipient scales; no adaptive recalibration.
            with torch.no_grad(), self._record([patch["component"]]) as stored:
                self._forward(donor_tokens, patch["donor_arm"], calibration, len(donor_continuation))
            donor = stored[patch["component"]]
            positions = position_indices(patch["positions"], len(context_ids), len(tokens))
            donor_positions = position_indices(patch.get("donor_positions", patch["positions"]),
                                               len(donor_ids), len(donor_tokens))
            def apply(_module, _args, output):
                changed, audit = scoped_replacement(torch, tensor_output(output), donor, positions,
                    donor_positions, patch.get("mode", "donor"), patch.get("seed", 0))
                audit.update(component=patch["component"], recipient_arm=arm, donor_arm=patch["donor_arm"],
                    source_needle_layers=list(self.conditions[arm]),
                    recipient_input_sha256=token_hash(tokens), donor_input_sha256=token_hash(donor_tokens))
                patch_audit.append(audit)
                return replace_tensor_output(output, changed)
            handles.append(self.contributions[patch["component"]].register_forward_hook(apply))
        try:
            with torch.no_grad(), self._record(names) as stored:
                logits = self._forward(tokens, arm, calibration, len(continuation_ids))
            for audit in patch_audit:
                audit["actual_source_writes"] = dict(self.last_source_audit)
            selected = torch.log_softmax(logits[0, -len(continuation_ids):], -1, dtype=torch.float32)
            targets = torch.tensor(continuation_ids, device=self.device, dtype=torch.long)
            token_scores = selected.gather(-1, targets[:, None]).flatten()
            observations = {}
            for spec in capture:
                positions = position_indices(spec["positions"], len(context_ids), len(tokens))
                values = stored[spec["component"]][0, positions].float()
                if "projection" in spec:
                    direction = torch.tensor(spec["projection"], device=values.device, dtype=torch.float32)
                    assert direction.shape == (values.shape[-1],) and torch.isfinite(direction).all()
                    values = values @ direction
                observations[spec["component"]] = {"positions": positions, "values": values.cpu().tolist()}
            detail = {"loglikelihood": token_scores.sum().item(), "token_logprobs": token_scores.tolist(),
                "continuation_token_ids": continuation_ids, "context_token_count": len(context_ids),
                "input_token_sha256": token_hash(tokens), "source_write_audit": dict(self.last_source_audit)}
            return detail, observations, patch_audit
        finally:
            for handle in handles:
                handle.remove()

    def score_item(self, item, arm, calibration, patch=None, capture=None):
        assert len(item["choices"]) == len(item["continuations"])
        details, observations, audits = [], [], []
        for continuation in item["continuations"]:
            detail, observed, audit = self._choice(item["context"], continuation, arm, calibration, patch, capture)
            details.append(detail)
            observations.append(observed)
            audits.append(audit)
        scores = [row["loglikelihood"] / divisor for row, divisor in zip(details, score_divisors(item))]
        return {**summarize_scores(scores, item["target_index"]), "choice_details": details,
                "observations": observations, "patch_audit": audits}

    def rank_item(self, item, calibration):
        """First-order repair of AB margin; highest wrong option is fixed at AB."""
        torch = self.torch
        clean, ab = self.make_condition("clean"), self.make_condition("AB")
        observed = self.score_item(item, ab, calibration)
        target, wrong = item["target_index"], observed["strongest_wrong"]
        divisors, names, totals = score_divisors(item), self.candidates(), {}
        for choice_index, sign in ((target, 1.0), (wrong, -1.0)):
            context_ids, continuation_ids = encode_pair(self.tokenizer, item["context"], item["continuations"][choice_index])
            tokens = context_ids + continuation_ids[:-1]
            with torch.no_grad(), self._record(names) as donor:
                self._forward(tokens, clean, calibration, len(continuation_ids))
            # Move only donor tensors to CPU between forwards; preserve no graph.
            donor = {name: value.cpu() for name, value in donor.items()}
            with torch.enable_grad(), self._record(names, gradient=True) as recipient:
                logits = self._forward(tokens, ab, calibration, len(continuation_ids), gradient=True)
                logprobs = torch.log_softmax(logits[0, -len(continuation_ids):], -1, dtype=torch.float32)
                targets = torch.tensor(continuation_ids, device=self.device, dtype=torch.long)
                scalar = sign * logprobs.gather(-1, targets[:, None]).sum() / divisors[choice_index]
                gradients = torch.autograd.grad(scalar, [recipient[name] for name in names])
                self.counts["backward"] += 1
            for name, gradient in zip(names, gradients):
                delta = donor[name].to(gradient.device).float() - recipient[name].detach().float()
                for scope in ("prompt_last", "answer_tail"):
                    positions = position_indices(scope, len(context_ids), len(tokens))
                    if not positions:
                        continue
                    key = (name, scope)
                    row = totals.setdefault(key, {"component": name, "positions": scope,
                        "predicted_repair": 0.0, "active_position_count": 0})
                    row["predicted_repair"] += (gradient[:, positions].float() * delta[:, positions]).sum().item()
                    row["active_position_count"] += len(positions)
            del gradients, recipient, logits, scalar, donor
        assert all(math.isfinite(row["predicted_repair"]) for row in totals.values())
        return list(totals.values())

    def verify_unchanged(self):
        result = super().verify_unchanged()
        assert all(not module._forward_hooks for module in self.contributions.values())
        assert all(parameter.grad is None for parameter in self.model.parameters())
        return {**result, "parameter_gradients_absent": True, "counts": dict(self.counts)}
