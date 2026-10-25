"""Immutable Qwen model with scoped, row-specific EVO activation offsets.

Task prompts and scoring belong to the pinned harness; this module only evaluates
their exact strings. Token-pair encoding follows harness d6de81643928d653435c431bae19945d41d32520.
"""
from contextlib import contextmanager
import hashlib
import json
import math
import os
import time


TARGETS = ((14, 8949, 1.0), (13, 7956, -1.0))


def text_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()


def token_hash(tokens):
    return text_hash(json.dumps(tokens, separators=(",", ":")))


def encode_text(tokenizer, text):
    """HFLM default add_bos_token=None: retain tokenizer defaults."""
    prefix_id = tokenizer.bos_token_id if tokenizer.bos_token_id is not None else tokenizer.eos_token_id
    prefix = tokenizer.decode(prefix_id) if prefix_id is not None else None
    kwargs = {"add_special_tokens": False} if prefix and text.startswith(prefix) else {}
    return tokenizer.encode(text, **kwargs)


def encode_pair(tokenizer, context, continuation):
    assert context and continuation, "Benchmark likelihood requests require nonempty strings"
    spaces = len(context) - len(context.rstrip())
    if spaces:
        continuation, context = context[-spaces:] + continuation, context[:-spaces]
    context_ids = encode_text(tokenizer, context)
    whole_ids = encode_text(tokenizer, context + continuation)
    continuation_ids = whole_ids[len(context_ids):]
    assert context_ids and continuation_ids
    return context_ids, continuation_ids


def finish_generation(returned, stop_ids, pad_id, budget, stop_step, stops, decode):
    """Keep actual generated tokens, including the terminator, excluding returned padding."""
    eos_step = next((i + 1 for i, value in enumerate(returned) if value in stop_ids), None)
    endings = [(eos_step, "eos_token")] if eos_step is not None else []
    if stop_step is not None:
        endings.append((stop_step, "task_stop"))
    if endings:
        length, reason = min(endings, key=lambda value: value[0])
        assert all(value == pad_id for value in returned[length:])
    else:
        length, reason = len(returned), "length_limit"
        assert length == budget
    tokens = returned[:length]
    answer = decode(tokens, skip_special_tokens=True)
    boundaries = [answer.index(stop) for stop in stops if stop and stop in answer]
    if boundaries:
        answer = answer[:min(boundaries)]
    return {"token_ids": tokens, "generated_token_count": len(tokens),
            "returned_padding_count": len(returned) - len(tokens), "max_new_tokens": budget,
            "end_reason": reason, "raw_text": decode(tokens, skip_special_tokens=False), "answer_text": answer}


class Engine:
    def __init__(self, model_path, device="cuda:0", batch_size=8, threads=4):
        import torch
        import transformers
        from transformers import AutoTokenizer, Qwen3_5ForConditionalGeneration

        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
        torch.set_num_threads(threads)
        torch.manual_seed(0)
        torch.use_deterministic_algorithms(True)
        self.torch, self.device, self.batch_size = torch, device, batch_size
        assert batch_size > 0
        self.tokenizer = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True, trust_remote_code=False)
        self.model = Qwen3_5ForConditionalGeneration.from_pretrained(
            str(model_path), local_files_only=True, trust_remote_code=False,
            torch_dtype=torch.bfloat16, attn_implementation="eager").to(device).eval()
        self.model.requires_grad_(False)
        self.layers = self.model.model.language_model.layers
        self.modules = {layer: self.layers[layer].mlp.down_proj for layer, _, _ in TARGETS}
        assert all(module.weight.shape == (2560, 9216) and module.bias is None for module in self.modules.values())
        self.column_norms = {str(layer): self.modules[layer].weight[:, neuron].float().norm().item()
                             for layer, neuron, _ in TARGETS}
        assert all(math.isfinite(value) and value > 0 for value in self.column_norms.values())
        configured = self.model.generation_config.eos_token_id
        stops = set([configured] if isinstance(configured, int) else configured or [])
        stops.add(self.tokenizer.eos_token_id)
        im_end = self.tokenizer.convert_tokens_to_ids("<|im_end|>")
        assert self.tokenizer.convert_ids_to_tokens(im_end) == "<|im_end|>"
        assert self.tokenizer.encode("<|im_end|>", add_special_tokens=False) == [im_end]
        stops.add(im_end)
        self.stop_ids = sorted(stops)
        assert self.stop_ids == [248044, 248046]
        self.pad_id = self.tokenizer.pad_token_id
        assert self.pad_id is not None
        config = getattr(self.model.config, "text_config", self.model.config)
        self.max_length = config.max_position_embeddings
        self.weight_hashes = self._weight_hashes()
        self.metadata = {"model_class": type(self.model).__name__, "versions": {
            "torch": torch.__version__, "transformers": transformers.__version__},
            "dtype": "bfloat16", "softmax_dtype": "float32", "attention_backend": "eager",
            "batch_size": batch_size, "targets": TARGETS, "column_norms": self.column_norms,
            "target_weight_sha256_before": self.weight_hashes, "max_context_tokens": self.max_length,
            "effective_stop_tokens": {str(t): self.tokenizer.convert_ids_to_tokens(t) for t in self.stop_ids},
            "pad_token_id": self.pad_id, "chat_template_applied": False,
            "tokenization": "Pinned HFLM default tokenizer special-token behavior; trailing context whitespace moves to continuation",
            "generation_stopping": "Per-row task-string stopping; generated text cut at first task stop, as in harness postprocessing",
            "single_immutable_model": True, "fresh_cache_each_call": True}

    def _weight_hashes(self):
        return {str(layer): hashlib.sha256(module.weight.detach().contiguous().view(self.torch.uint8).cpu().numpy().tobytes()).hexdigest()
                for layer, module in self.modules.items()}

    def verify_unchanged(self):
        assert all(not module._forward_pre_hooks for module in self.modules.values())
        hashes = self._weight_hashes()
        assert hashes == self.weight_hashes
        return {"target_weight_sha256_after": hashes, "hooks_removed": True}

    def _inputs(self, sequences):
        torch = self.torch
        width = max(map(len, sequences))
        assert 0 < width <= self.max_length
        ids = torch.full((len(sequences), width), self.pad_id, dtype=torch.long, device=self.device)
        mask = torch.zeros_like(ids)
        for row, tokens in enumerate(sequences):
            assert tokens
            ids[row, -len(tokens):] = torch.tensor(tokens, dtype=torch.long, device=self.device)
            mask[row, -len(tokens):] = 1
        return {"input_ids": ids, "attention_mask": mask}

    @contextmanager
    def _intervention(self, arm, calibrations, input_mask):
        assert arm in ("baseline", "evo", "zero")
        assert all(not module._forward_pre_hooks for module in self.modules.values())
        handles = []
        try:
            if arm != "baseline":
                for layer, neuron, _ in TARGETS:
                    module = self.modules[layer]
                    offsets = module.weight.new_tensor([0.0 if arm == "zero" else row["activation_offsets"][str(layer)]
                                                        for row in calibrations]).unsqueeze(1)
                    def add(_module, args, n=neuron, amount=offsets):
                        activation = args[0].clone()
                        assert activation.shape[0] == amount.shape[0]
                        if activation.shape[1] == input_mask.shape[1]:
                            activation[..., n] += amount * input_mask.to(activation.dtype)
                        else:
                            assert activation.shape[1] == 1, "Unexpected cached decode width"
                            activation[..., n] += amount
                        return (activation, *args[1:])
                    handles.append(module.register_forward_pre_hook(add))
            yield
        finally:
            for handle in handles:
                handle.remove()

    def calibrate(self, contexts):
        torch, results = self.torch, []
        assert all(not module._forward_pre_hooks for module in self.modules.values())
        with torch.inference_mode():
            for start in range(0, len(contexts), self.batch_size):
                texts = contexts[start:start + self.batch_size]
                sequences = [encode_text(self.tokenizer, text) for text in texts]
                assert all(len(tokens) >= 2 for tokens in sequences)
                inputs = self._inputs(sequences)
                rows = [{"context_sha256": text_hash(text), "input_token_sha256": token_hash(tokens),
                         "input_token_count": len(tokens), "residual_scales": {}, "activation_offsets": {}}
                        for text, tokens in zip(texts, sequences)]
                handles = []
                try:
                    for layer, _, dose in TARGETS:
                        def capture(_module, _args, output, layer=layer, dose=dose):
                            residual = output[0] if isinstance(output, tuple) else output
                            assert residual.shape[:2] == inputs["attention_mask"].shape
                            for index, row in enumerate(rows):
                                valid = residual[index][inputs["attention_mask"][index].bool()][1:]
                                scale = torch.quantile(valid.float().norm(dim=-1), 0.5).item()
                                assert math.isfinite(scale) and scale > 0
                                row["residual_scales"][str(layer)] = scale
                                row["activation_offsets"][str(layer)] = dose * scale / self.column_norms[str(layer)]
                        handles.append(self.layers[layer].register_forward_hook(capture))
                    self.model(**inputs, use_cache=False, logits_to_keep=1)
                finally:
                    for handle in handles:
                        handle.remove()
                results.extend(rows)
        return results


    def score(self, contexts, continuations, arm, calibrations):
        """Summed continuation log-likelihood; reuse identical input forwards (MMLU letters)."""
        torch = self.torch
        assert len(contexts) == len(continuations) == len(calibrations)
        groups, results = {}, [None] * len(contexts)
        for index, (context, continuation, calibration) in enumerate(zip(contexts, continuations, calibrations)):
            assert calibration["context_sha256"] == text_hash(context)
            context_ids, continuation_ids = encode_pair(self.tokenizer, context, continuation)
            tokens = context_ids + continuation_ids[:-1]
            offsets = tuple(calibration["activation_offsets"][str(layer)] for layer, _, _ in TARGETS) if arm == "evo" else ()
            group = groups.setdefault((tuple(tokens), offsets), {"tokens": tokens, "calibration": calibration, "requests": []})
            group["requests"].append((index, continuation_ids, len(context_ids)))
        groups = list(groups.values())
        with torch.inference_mode():
            for start in range(0, len(groups), self.batch_size):
                batch = groups[start:start + self.batch_size]
                inputs = self._inputs([row["tokens"] for row in batch])
                keep = max(len(ids) for row in batch for _, ids, _ in row["requests"])
                with self._intervention(arm, [row["calibration"] for row in batch], inputs["attention_mask"]):
                    logits = self.model(**inputs, use_cache=False, logits_to_keep=keep).logits
                assert torch.isfinite(logits).all().item()
                logprobs = torch.log_softmax(logits, dim=-1, dtype=torch.float32)
                for row, group in enumerate(batch):
                    for index, continuation_ids, context_length in group["requests"]:
                        selected = logprobs[row, -len(continuation_ids):]
                        targets = torch.tensor(continuation_ids, dtype=torch.long, device=self.device)
                        token_probs = selected.gather(-1, targets.unsqueeze(-1)).squeeze(-1)
                        results[index] = {"loglikelihood": token_probs.sum().item(),
                            "is_greedy": bool((selected.argmax(-1) == targets).all().item()),
                            "continuation_token_ids": continuation_ids, "token_logprobs": token_probs.tolist(),
                            "context_token_count": context_length, "input_token_sha256": token_hash(group["tokens"])}
        return results

    def generate(self, contexts, arm, calibrations, max_new_tokens, stops):
        from transformers import StoppingCriteria, StoppingCriteriaList

        torch, tokenizer, results = self.torch, self.tokenizer, []
        assert len(contexts) == len(calibrations) and max_new_tokens > 0
        stops = list(dict.fromkeys(stops))
        assert all(isinstance(stop, str) and stop for stop in stops)
        lookback = max([len(tokenizer.encode(stop, add_special_tokens=False)) + 2 for stop in stops] or [1])

        class TaskStops(StoppingCriteria):
            def __init__(self, width, size):
                self.width, self.steps = width, [None] * size

            def __call__(self, input_ids, scores, **kwargs):
                generated = input_ids[:, self.width:]
                texts = tokenizer.batch_decode(generated[:, -lookback:], skip_special_tokens=False,
                                                clean_up_tokenization_spaces=False)
                for index, text in enumerate(texts):
                    if self.steps[index] is None and any(stop in text for stop in stops):
                        self.steps[index] = generated.shape[1]
                return torch.tensor([step is not None for step in self.steps], dtype=torch.bool, device=input_ids.device)

        with torch.inference_mode():
            for start in range(0, len(contexts), self.batch_size):
                texts, scales = contexts[start:start + self.batch_size], calibrations[start:start + self.batch_size]
                assert all(row["context_sha256"] == text_hash(text) for text, row in zip(texts, scales))
                sequences = [encode_text(tokenizer, text) for text in texts]
                assert max(map(len, sequences)) + max_new_tokens <= self.max_length
                inputs = self._inputs(sequences)
                criterion = TaskStops(inputs["input_ids"].shape[1], len(texts))
                if str(self.device).startswith("cuda"):
                    torch.cuda.synchronize(self.device)
                started = time.monotonic()
                with self._intervention(arm, scales, inputs["attention_mask"]):
                    output = self.model.generate(**inputs, do_sample=False, max_new_tokens=max_new_tokens,
                        use_cache=True, logits_to_keep=1, eos_token_id=self.stop_ids, pad_token_id=self.pad_id,
                        stopping_criteria=StoppingCriteriaList([criterion]))
                if str(self.device).startswith("cuda"):
                    torch.cuda.synchronize(self.device)
                seconds = time.monotonic() - started
                returned = output[:, inputs["input_ids"].shape[1]:].tolist()
                def decode(tokens, skip_special_tokens):
                    return tokenizer.decode(tokens, skip_special_tokens=skip_special_tokens, clean_up_tokenization_spaces=False)
                for index, tokens in enumerate(returned):
                    result = finish_generation(tokens, self.stop_ids, self.pad_id, max_new_tokens,
                                               criterion.steps[index], stops, decode)
                    result.update({"input_token_sha256": token_hash(sequences[index]),
                                   "batch_seconds": seconds, "batch_size": len(texts)})
                    results.append(result)
        return results


def mechanical_checks(engine, batch_size):
    """Bounded non-test controls; does not claim all-task numerical equivalence."""
    assert batch_size >= 1
    prompts = ["Question: What is 2 plus 3?\nAnswer:",
               "A library owns three shelves with ten books on each shelf. Five books are borrowed.\nQuestion: How many books remain?\nAnswer:"]
    choices = [[" 3", " 4", " 5", " 6"],
               [" Twenty-five books remain.", " Thirty books remain.", " Five books remain.", " Thirty-five books remain."]]
    labels = ("baseline", "zero", "evo", "restored")
    result = {"status": "running", "prompts": prompts, "choices": choices,
              "generation_tokens": 16, "batch_size": batch_size, "single": [], "batched": {},
              "calibration_relative_tolerance": 1e-5, "likelihood_absolute_tolerance_nats": 0.02,
              "limits": "Two synthetic contexts repeated to the requested generation batch size; likelihood grouping may use fewer unique rows. Only 16 generated tokens are compared.",
              "failures": []}
    original_batch = engine.batch_size

    def outputs(texts, indices, calibrations):
        collected = {}
        contexts = [text for text in texts for _ in range(4)]
        continuations = [choice for index in indices for choice in choices[index]]
        expanded = [calibration for calibration in calibrations for _ in range(4)]
        for label in labels:
            arm = "baseline" if label == "restored" else label
            scores = engine.score(contexts, continuations, arm, expanded)
            generations = engine.generate(texts, arm, calibrations, 16, ["\n\n"])
            collected[label] = [{"scores": scores[4 * i:4 * i + 4], "generation": generations[i]}
                                for i in range(len(texts))]
        return collected

    def check_equal_control(group, location):
        for label in ("zero", "restored"):
            for index, (base, control) in enumerate(zip(group["baseline"], group[label])):
                if base["generation"]["token_ids"] != control["generation"]["token_ids"] or base["scores"] != control["scores"]:
                    result["failures"].append(f"{location}:{index}:{label}:zero_or_restoration_not_exact")

    try:
        engine.batch_size = 1
        single_calibrations = engine.calibrate(prompts)
        for index, text in enumerate(prompts):
            controls = outputs([text], [index], [single_calibrations[index]])
            check_equal_control(controls, f"single:{index}")
            result["single"].append({"calibration": single_calibrations[index], "outputs": controls})
        engine.batch_size = batch_size
        indices = [index % 2 for index in range(batch_size)]
        batch_prompts = [prompts[index] for index in indices]
        calibrations = engine.calibrate(batch_prompts)
        result["batched_calibrations"] = calibrations
        for index, calibration in enumerate(calibrations):
            reference = single_calibrations[indices[index]]
            for layer, value in calibration["residual_scales"].items():
                if not math.isclose(value, reference["residual_scales"][layer], rel_tol=1e-5, abs_tol=1e-8):
                    result["failures"].append(f"calibration:{index}:layer{layer}:single_batch_mismatch")
        result["batched"] = outputs(batch_prompts, indices, calibrations)
        check_equal_control(result["batched"], "batch")
        max_score_difference = 0.0
        for label in labels:
            for index, batch_row in enumerate(result["batched"][label]):
                single_row = result["single"][indices[index]]["outputs"][label][0]
                if batch_row["generation"]["token_ids"] != single_row["generation"]["token_ids"]:
                    result["failures"].append(f"generation:{label}:{index}:single_batch_token_mismatch")
                before = [row["loglikelihood"] for row in single_row["scores"]]
                after = [row["loglikelihood"] for row in batch_row["scores"]]
                difference = max(abs(a - b) for a, b in zip(before, after))
                max_score_difference = max(max_score_difference, difference)
                if difference > 0.02 or max(range(4), key=before.__getitem__) != max(range(4), key=after.__getitem__):
                    result["failures"].append(f"likelihood:{label}:{index}:single_batch_value_or_rank_mismatch")
        result["max_single_batch_loglikelihood_difference"] = max_score_difference

        # Independently score all logits to catch suffix indexing/logits_to_keep errors.
        engine.batch_size = 1
        context_ids, continuation_ids = encode_pair(engine.tokenizer, prompts[1], choices[1][0])
        inputs = engine._inputs([context_ids + continuation_ids[:-1]])
        result["full_forward_likelihood"] = {}
        torch = engine.torch
        with torch.inference_mode():
            for arm in ("baseline", "evo"):
                with engine._intervention(arm, [single_calibrations[1]], inputs["attention_mask"]):
                    logits = engine.model(**inputs, use_cache=False).logits[0, -len(continuation_ids):]
                full = torch.log_softmax(logits, -1, dtype=torch.float32)
                targets = torch.tensor(continuation_ids, device=engine.device, dtype=torch.long)
                full_tokens = full.gather(-1, targets.unsqueeze(-1)).squeeze(-1).tolist()
                short = result["single"][1]["outputs"][arm][0]["scores"][0]
                difference = max(abs(a - b) for a, b in zip(full_tokens, short["token_logprobs"]))
                result["full_forward_likelihood"][arm] = {"token_logprobs": full_tokens, "max_abs_difference": difference}
                if difference > 0.02:
                    result["failures"].append(f"full_forward:{arm}:suffix_likelihood_mismatch")
        result.update(engine.verify_unchanged())
        result["status"] = "completed" if not result["failures"] else "failed"
        return result
    finally:
        engine.batch_size = original_batch
