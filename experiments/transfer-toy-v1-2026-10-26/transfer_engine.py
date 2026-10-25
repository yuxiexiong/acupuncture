"""Versioned transfer hooks; reuse the frozen v2 likelihood/generation implementation."""
from contextlib import contextmanager
import importlib.util
import json
import math
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("acupuncture_frozen_v2_engine", ROOT.parent / "capability-damage-v2-2026-10-26/model_engine.py")
_v2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_v2)
encode_text, encode_pair = _v2.encode_text, _v2.encode_pair
text_hash, token_hash = _v2.text_hash, _v2.token_hash
LAYERS = (13, 14)
SOURCE_NEURONS = {13: 7956, 14: 8949}
SIGNS = {13: -1.0, 14: 1.0}


class TransferEngine(_v2.Engine):
    def __init__(self, model_path, device="cuda:0", batch_size=1, threads=4, bundle=None):
        import torch
        import transformers
        from transformers import AutoTokenizer, Qwen3_5ForConditionalGeneration

        assert batch_size == 1, "Frozen transfer protocol uses actual forward batch one"
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
        torch.set_num_threads(threads)
        torch.manual_seed(0)
        torch.use_deterministic_algorithms(True)
        self.torch, self.device, self.batch_size = torch, device, batch_size
        self.tokenizer = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True, trust_remote_code=False)
        self.model = Qwen3_5ForConditionalGeneration.from_pretrained(str(model_path),
            local_files_only=True, trust_remote_code=False, torch_dtype=torch.bfloat16,
            attn_implementation="eager").to(device).eval()
        self.model.requires_grad_(False)
        self.layers = self.model.model.language_model.layers
        self.modules = {layer: self.layers[layer].mlp.down_proj for layer in LAYERS}
        config = getattr(self.model.config, "text_config", self.model.config)
        assert len(self.layers) > max(LAYERS)
        assert all(module.bias is None and module.weight.shape == (config.hidden_size, config.intermediate_size)
                   for module in self.modules.values())
        self.column_norms = {str(layer): module.weight.float().norm(dim=0).cpu() for layer, module in self.modules.items()}
        configured = self.model.generation_config.eos_token_id
        stops = set([configured] if isinstance(configured, int) else configured or [])
        stops.add(self.tokenizer.eos_token_id)
        im_end = self.tokenizer.convert_tokens_to_ids("<|im_end|>")
        assert self.tokenizer.encode("<|im_end|>", add_special_tokens=False) == [im_end]
        stops.add(im_end)
        self.stop_ids = sorted(stops)
        assert self.stop_ids == [248044, 248046]
        self.pad_id = self.tokenizer.pad_token_id
        assert self.pad_id is not None
        self.max_length = config.max_position_embeddings
        self.weight_hashes = self._weight_hashes()
        self.conditions = {"T_0": {}, "S_0": {}, "baseline": {}}
        if bundle is not None:
            payload = torch.load(bundle, map_location="cpu", weights_only=True) if isinstance(bundle, (str, Path)) else bundle
            assert payload["hidden_size"] == config.hidden_size
            assert payload["intermediate_size"] == config.intermediate_size
            assert payload["target_weight_sha256"] == self.weight_hashes, "Bundle belongs to different model weights"
            self.conditions.update(payload["conditions"])
        self.conditions["zero_channel"] = {str(l): {"kind": "channel", "index": 0, "scale": "target", "coefficient": 0.0} for l in LAYERS}
        self.conditions["zero_vector"] = {str(l): {"kind": "vector", "vector": torch.zeros(config.hidden_size), "scale": "target", "coefficient": 0.0} for l in LAYERS}
        self.metadata = {"model_class": type(self.model).__name__, "model_path": str(model_path),
            "versions": {"torch": str(torch.__version__), "transformers": str(transformers.__version__),
                         "cuda_runtime": torch.version.cuda, "cudnn": torch.backends.cudnn.version()},
            "device": str(device), "dtype": "bfloat16", "softmax_dtype": "float32",
            "attention_backend": "eager", "batch_size": batch_size,
            "hidden_size": config.hidden_size, "intermediate_size": config.intermediate_size,
            "layers": list(LAYERS), "target_weight_sha256_before": self.weight_hashes,
            "effective_stop_tokens": {str(t): self.tokenizer.convert_ids_to_tokens(t) for t in self.stop_ids},
            "pad_token_id": self.pad_id, "max_context_tokens": self.max_length,
            "chat_template_applied": False, "single_immutable_model": True, "fresh_cache_each_call": True,
            "numerical_settings": {"deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
                "float32_matmul_precision": torch.get_float32_matmul_precision(),
                "matmul_allow_tf32": torch.backends.cuda.matmul.allow_tf32,
                "matmul_allow_bf16_reduced_precision_reduction": torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction,
                "cublas_workspace_config": os.environ.get("CUBLAS_WORKSPACE_CONFIG")}}

    def verify_unchanged(self):
        assert all(not module._forward_pre_hooks for module in self.modules.values())
        assert all(not self.layers[layer]._forward_hooks for layer in LAYERS)
        hashes = self._weight_hashes()
        assert hashes == self.weight_hashes
        return {"target_weight_sha256_after": hashes, "hooks_removed": True}

    def source_bundle(self):
        assert self.metadata["hidden_size"] == 2560 and self.metadata["intermediate_size"] == 9216
        channel, vector = {}, {}
        for layer in LAYERS:
            index = SOURCE_NEURONS[layer]
            norm = float(self.column_norms[str(layer)][index])
            column = self.modules[layer].weight[:, index].float().detach().cpu()
            channel[str(layer)] = {"kind": "channel", "index": index, "scale": "target", "coefficient": SIGNS[layer] / norm}
            vector[str(layer)] = {"kind": "vector", "vector": SIGNS[layer] * column / norm, "scale": "target", "coefficient": 1.0}
        return {"hidden_size": 2560, "intermediate_size": 9216, "target_weight_sha256": self.weight_hashes,
                "conditions": {"S_0": {}, "S_channel": channel, "S_vector": vector}}

    @contextmanager
    def _intervention(self, arm, calibrations, input_mask):
        torch = self.torch
        arm = "true_S_recipe" if arm == "evo" else arm
        assert arm in self.conditions, f"Unknown frozen condition {arm}"
        assert all(not module._forward_pre_hooks for module in self.modules.values())
        handles = []
        try:
            for layer_string, spec in self.conditions[arm].items():
                layer = int(layer_string)
                assert layer in LAYERS
                scale_key = "source_residual_scales" if spec["scale"] == "source" else "residual_scales"
                scales = [row[scale_key][str(layer)] * spec.get("coefficient", 1.0) for row in calibrations]
                assert all(math.isfinite(x) for x in scales)
                reference = self.modules[layer].weight
                amount = reference.new_tensor(scales).reshape(-1, 1)
                def mask_for(width):
                    if width == input_mask.shape[1]:
                        return input_mask.to(reference.dtype)
                    assert width == 1, "Unexpected cached decode width"
                    return 1.0
                if spec["kind"] == "channel":
                    index = spec["index"]
                    assert 0 <= index < reference.shape[1]
                    def add_channel(_module, args, index=index, amount=amount, mask_for=mask_for):
                        activation = args[0].clone()
                        activation[..., index] += amount * mask_for(activation.shape[1])
                        return (activation, *args[1:])
                    handles.append(self.modules[layer].register_forward_pre_hook(add_channel))
                else:
                    assert spec["kind"] == "vector"
                    vector = spec["vector"].to(device=self.device, dtype=torch.float32)
                    assert vector.shape == (reference.shape[0],) and self.torch.isfinite(vector).all()
                    float_amount = torch.tensor(scales, device=self.device, dtype=torch.float32).reshape(-1, 1)
                    def add_vector(_module, _args, output, vector=vector, amount=float_amount, mask_for=mask_for):
                        residual = output[0] if isinstance(output, tuple) else output
                        addition = (amount * mask_for(residual.shape[1])).unsqueeze(-1) * vector
                        changed = residual + addition.to(residual.dtype)
                        return (changed, *output[1:]) if isinstance(output, tuple) else changed
                    handles.append(self.layers[layer].register_forward_hook(add_vector))
            yield
        finally:
            for handle in handles:
                handle.remove()

    def score(self, contexts, continuations, arm, calibrations):
        arm = "true_S_recipe" if arm == "evo" else arm
        return super().score(contexts, continuations, arm, calibrations)

    def calibrate(self, contexts):
        torch, results = self.torch, []
        assert all(not module._forward_pre_hooks for module in self.modules.values())
        assert all(not self.layers[layer]._forward_hooks for layer in LAYERS)
        with torch.inference_mode():
            for text in contexts:
                tokens = encode_text(self.tokenizer, text)
                assert len(tokens) >= 2
                inputs = self._inputs([tokens])
                row = {"context_sha256": text_hash(text), "input_token_sha256": token_hash(tokens),
                       "input_token_count": len(tokens), "residual_scales": {}, "activation_offsets": {}}
                handles = []
                try:
                    for layer in LAYERS:
                        def capture(_module, _args, output, layer=layer):
                            residual = output[0] if isinstance(output, tuple) else output
                            scale = torch.quantile(residual[0, 1:].float().norm(dim=-1), 0.5).item()
                            assert math.isfinite(scale) and scale > 0
                            row["residual_scales"][str(layer)] = scale
                        handles.append(self.layers[layer].register_forward_hook(capture))
                    self.model(**inputs, use_cache=False, logits_to_keep=1)
                finally:
                    for handle in handles:
                        handle.remove()
                results.append(row)
        return results


Engine = TransferEngine


def source_bundle(engine):
    return engine.source_bundle()
