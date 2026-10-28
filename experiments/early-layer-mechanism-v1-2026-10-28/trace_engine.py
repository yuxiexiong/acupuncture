"""Read-only traces of frozen free generation and a clean, same-prefix shadow."""
from contextlib import contextmanager
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parent


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


negative = _load("trace_negative_dose", ROOT.parent / "layer-negative-dose-survey-toy-v1-2026-10-27/dose_engine.py")
positive = _load("trace_positive_dose", ROOT.parent / "layer-dose-survey-toy-v1-2026-10-27/dose_engine.py")
frozen = negative.survey.transfer._v2
token_hash, text_hash, encode_text = frozen.token_hash, frozen.text_hash, frozen.encode_text


def record_arm(record):
    if record.get("layer") is None:
        return "baseline"
    dose = record.get("dose", (record.get("intervention") or {}).get("dose", 1.0))
    return int(record["layer"]), int(record["channel"]), float(dose)


class TraceEngine(negative.DoseEngine):
    def _intervention(self, arm, calibrations, input_mask):
        # Reuse both frozen implementations; neither their allowed doses nor code changes.
        engine = positive.DoseEngine if arm != "baseline" and arm[2] > 0 else negative.DoseEngine
        return engine._intervention(self, arm, calibrations, input_mask)

    def _sites(self):
        sites = []
        for layer, block in enumerate(self.layers):
            attention = "linear_attn" if hasattr(block, "linear_attn") else "self_attn"
            for component, module in (("attention", getattr(block, attention)), ("mlp", block.mlp), ("residual", block)):
                sites.append(({"name": f"L{layer}.{component}", "layer": layer, "component": component,
                               "module_type": attention if component == "attention" else component}, module))
        return sites

    @contextmanager
    def _observe(self, components=True):
        sites = self._sites() if components else []
        captures = {meta["name"]: [] for meta, _ in sites}
        captures["logits"] = []
        handles = []
        try:
            for meta, module in sites:
                def capture(_module, _args, output, name=meta["name"]):
                    value = output[0] if isinstance(output, tuple) else output
                    assert value.ndim == 3 and value.shape[0] == 1
                    # No CPU transfer, scalar read, mutation, or precision change in observers.
                    captures[name].append(value[0].detach().clone())
                handles.append(module.register_forward_hook(capture))

            def capture_logits(_module, _args, output):
                captures["logits"].append(output.logits[0, -1].detach().clone())
            handles.append(self.model.register_forward_hook(capture_logits))
            yield captures
        finally:
            for handle in handles:
                handle.remove()

    def _logit_hashes(self, captures):
        rows = self.torch.stack(captures["logits"]).contiguous().view(self.torch.uint8).cpu().numpy()
        return [hashlib.sha256(row.tobytes()).hexdigest() for row in rows]

    def verify_unchanged(self):
        result = super().verify_unchanged()
        assert not self.model._forward_hooks
        assert all(not module._forward_hooks for _, module in self._sites())
        return result

    def _forced_clean(self, context, calibration, target):
        from transformers import LogitsProcessor, LogitsProcessorList

        engine = self
        prompt = encode_text(self.tokenizer, context)
        expected_ids = self.torch.tensor([prompt + target], device=self.device)
        prefix_checks = []

        class ForceHistory(LogitsProcessor):
            def __call__(self, input_ids, scores):
                step = input_ids.shape[1] - len(prompt)
                assert 0 <= step < len(target), "Forced branch exceeded the source continuation"
                # Accumulate on GPU and check once after generation, not a sync per token.
                prefix_checks.append((input_ids == expected_ids[:, :input_ids.shape[1]]).all())
                forced = engine.torch.full_like(scores, -float("inf"))
                forced[:, target[step]] = 0
                return forced

        inputs = self._inputs([prompt])
        with self.torch.inference_mode(), self._intervention("baseline", [calibration], inputs["attention_mask"]):
            # An independent generate invocation constructs a fresh hybrid/attention cache.
            # The observer sees raw logits before ForceHistory runs.
            output = self.model.generate(**inputs, do_sample=False, max_new_tokens=128,
                use_cache=True, logits_to_keep=1, eos_token_id=self.stop_ids, pad_token_id=self.pad_id,
                logits_processor=LogitsProcessorList([ForceHistory()]))
        returned = output[0, len(prompt):].tolist()
        assert returned == target, "Clean shadow did not consume the intervention history exactly"
        assert len(prefix_checks) == len(target) and self.torch.stack(prefix_checks).all().item()
        return {"token_ids": returned, "generated_token_count": len(returned),
                "end_reason": "eos_token" if returned[-1] in self.stop_ids else "length_limit",
                "forced_history": True, "prefixes_verified": len(prefix_checks), "fresh_cache": True}

    def _component_summaries(self, clean, steer, prompt_length, generated_count):
        torch = self.torch
        summaries, metadata, checks = [], [], []
        expected_widths = [prompt_length] + [1] * (generated_count - 1)
        for meta, _ in self._sites():
            name = meta["name"]
            assert [row.shape[0] for row in clean[name]] == expected_widths
            assert [row.shape[0] for row in steer[name]] == expected_widths
            a, b = torch.cat(clean[name]).float(), torch.cat(steer[name]).float()
            assert a.shape == b.shape
            checks.extend((torch.isfinite(a).all(), torch.isfinite(b).all()))
            an, bn, dn = a.norm(dim=-1), b.norm(dim=-1), (b - a).norm(dim=-1)
            relative = torch.where(an > 0, dn / an, float("nan"))
            cosine = torch.where((an * bn) > 0, (a * b).sum(-1) / (an * bn), float("nan"))
            summaries.append(torch.stack((an, bn, dn, relative, cosine.clamp(-1, 1)), dim=-1))
            metadata.append(meta)
        assert torch.stack(checks).all().item(), "Nonfinite captured component"
        values = torch.stack(summaries).cpu().tolist()
        fields = ("clean_norm", "steer_norm", "delta_norm", "relative_delta", "cosine")
        return [{**meta, **{field: [row[i] if math.isfinite(row[i]) else None for row in rows]
                           for i, field in enumerate(fields)}} for meta, rows in zip(metadata, values)]

    def _logit_summaries(self, clean, steer, target):
        torch = self.torch
        a, b = torch.stack(clean["logits"]).float(), torch.stack(steer["logits"]).float()
        assert a.shape == b.shape and a.shape[0] == len(target)
        assert torch.isfinite(a).all().item() and torch.isfinite(b).all().item(), "Nonfinite logits"
        k = min(10, a.shape[-1])
        a_top, b_top = a.topk(k, dim=-1), b.topk(k, dim=-1)
        a_nonstop, b_nonstop = a.clone(), b.clone()
        a_nonstop[:, self.stop_ids], b_nonstop[:, self.stop_ids] = -float("inf"), -float("inf")
        a_best, b_best = a_nonstop.max(-1), b_nonstop.max(-1)
        del a_nonstop, b_nonstop
        fixed = torch.tensor([self.stop_ids + [token] for token in target], device=a.device)
        candidates = torch.cat((a_top.indices, b_top.indices, a_best.indices[:, None], b_best.indices[:, None], fixed), dim=-1)
        ap, bp = a.log_softmax(-1), b.log_softmax(-1)
        scores = torch.stack((a.gather(-1, candidates), b.gather(-1, candidates),
                              ap.gather(-1, candidates), bp.gather(-1, candidates)), dim=-1)
        stats = torch.stack((-(ap.exp() * ap).sum(-1), -(bp.exp() * bp).sum(-1),
                             (bp.exp() * (bp - ap)).sum(-1),
                             a_top.values[:, 0] - a_top.values[:, 1],
                             b_top.values[:, 0] - b_top.values[:, 1],
                             a[:, self.stop_ids].max(-1).values - a_best.values,
                             b[:, self.stop_ids].max(-1).values - b_best.values,
                             a_best.values, b_best.values), dim=-1)
        ids, values, statistics = candidates.cpu().tolist(), scores.cpu().tolist(), stats.cpu().tolist()
        rows = []
        for step, (tokens, cross_scores, stat) in enumerate(zip(ids, values, statistics)):
            seen, union = set(), []
            for token, score in zip(tokens, cross_scores):
                if token in seen:
                    continue
                seen.add(token)
                union.append({"token_id": token,
                    "token_text": self.tokenizer.decode([token], skip_special_tokens=False, clean_up_tokenization_spaces=False),
                    "clean_logit": score[0], "steer_logit": score[1],
                    "clean_logprob": score[2], "steer_logprob": score[3], "is_eos": token in self.stop_ids})
            rows.append({"step": step, "generated_token_id": target[step],
                         "clean_top_token_ids": tokens[:k], "steer_top_token_ids": tokens[k:2 * k],
                         "clean_argmax_is_eos": tokens[0] in self.stop_ids,
                         "clean_entropy": stat[0], "steer_entropy": stat[1], "kl_steer_to_clean": stat[2],
                         "clean_top_margin": stat[3], "steer_top_margin": stat[4],
                         "clean_stop_advantage": stat[5], "steer_stop_advantage": stat[6],
                         "clean_best_nonstop_token_id": tokens[2 * k], "steer_best_nonstop_token_id": tokens[2 * k + 1],
                         "clean_best_nonstop_logit": stat[7], "steer_best_nonstop_logit": stat[8], "candidates": union})
        first_divergence = next((row["step"] for row in rows if row["clean_top_token_ids"][0] != row["steer_top_token_ids"][0]), None)
        return {"top_k": k, "first_prediction_divergence": first_divergence,
                "score_semantics": "Raw pre-processor logits and full-vocabulary float32 log-softmax; candidate union of both top-k, best non-stop tokens over the full vocabulary, all EOS IDs, and actual generated token. Stop advantage is max EOS logit minus max non-stop logit.", "steps": rows}

    def collect(self, record, trace_path=None, *, observe=True, arm_override=None):
        """Replay one source row; observe=False records logits but no components.

        Result always contains output/intervention/source_token_ids_match. With observers,
        trace is returned in memory, or written as JSON when trace_path is supplied.
        The caller must fail preflight on source_token_ids_match=False.
        """
        context, calibration = record["context"], record["calibration"]
        prompt = encode_text(self.tokenizer, context)
        assert calibration["context_sha256"] == text_hash(context)
        assert calibration["input_token_sha256"] == token_hash(prompt)
        assert calibration["input_token_count"] == len(prompt)
        assert len(prompt) + 128 <= self.max_length
        expected = record["output"]["token_ids"]
        assert 0 < len(expected) <= 128
        assert record["output"].get("max_new_tokens", 128) == 128
        assert record["output"].get("input_token_sha256", token_hash(prompt)) == token_hash(prompt)
        if record.get("model_id") and self.metadata.get("model_id"):
            assert record["model_id"] == self.metadata["model_id"]
        arm = record_arm(record) if arm_override is None else arm_override
        started = time.monotonic()
        with self._observe(components=observe) as steer:
            output = self.generate([context], arm, [calibration], 128, [])[0]
        audit = dict(self.last_hook) if self.last_hook is not None else None
        target = output["token_ids"]
        result = {"output": output, "intervention": audit, "arm": arm,
                  "source_token_ids_match": target == expected,
                  "source_generated_token_sha256": token_hash(expected),
                  "generated_token_sha256": token_hash(target), "observed": observe,
                  "observer_mode": "components_and_logits" if observe else "logits_only",
                  "raw_logit_sha256_per_step": self._logit_hashes(steer)}
        assert len(result["raw_logit_sha256_per_step"]) == len(target)
        if observe:
            with self._observe() as clean:
                shadow = self._forced_clean(context, calibration, target)
            # The final sampled token is not fed back after EOS or the length limit.
            consumed = prompt + target[:-1]
            steps = [{"step": i, "prefix_length": len(prompt) + i,
                      "prefix_sha256": token_hash(prompt + target[:i]),
                      "observed_start": 0 if i == 0 else len(prompt) + i - 1,
                      "observed_count": len(prompt) if i == 0 else 1}
                     for i in range(len(target))]
            trace = {"schema": "early-layer-trace-v1", "model_id": record.get("model_id"),
                     "condition_id": record.get("condition_id"), "arm": arm,
                     "context_sha256": text_hash(context), "calibration": calibration,
                     "intervention": audit, "source_token_ids_match": result["source_token_ids_match"],
                     "input_token_ids": prompt, "input_token_sha256": token_hash(prompt),
                     "generated_token_ids": target, "generated_token_sha256": token_hash(target),
                     "raw_logit_sha256_per_step": result["raw_logit_sha256_per_step"],
                     "observed_input_token_ids": consumed, "prompt_token_count": len(prompt),
                     "observed_position_count": len(consumed), "forward_steps": steps,
                     "output": output, "clean_shadow": shadow,
                     "interpretation": "Clean shadow is a forced-prefix reference, not a natural clean answer. Differences describe propagation conditional on the intervention history; they do not prove a mediator is causal.",
                     "sites": self._component_summaries(clean, steer, len(prompt), len(target)),
                     "logits": self._logit_summaries(clean, steer, target)}
            result["clean_shadow"] = shadow
            if trace_path is None:
                result["trace"] = trace
            else:
                path = Path(trace_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                temporary = path.with_suffix(path.suffix + ".tmp")
                opener = gzip.open if path.suffix == ".gz" else open
                with opener(temporary, "wt", encoding="utf-8") as stream:
                    json.dump(trace, stream, ensure_ascii=False, allow_nan=False)
                    stream.write("\n")
                temporary.replace(path)
                result["trace_path"] = str(path)
        assert not self.model._forward_hooks
        assert all(not module._forward_hooks for _, module in self._sites())
        assert all(not module._forward_pre_hooks for module in self.modules.values())
        result["hooks_removed"] = True
        result["total_seconds"] = time.monotonic() - started
        return result
