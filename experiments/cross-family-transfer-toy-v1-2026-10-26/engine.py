"""LLaMA target adapter; retain the frozen transfer hooks and evaluation methods."""
import importlib.util
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT.parent / "transfer-toy-v1-2026-10-26"
_spec = importlib.util.spec_from_file_location("acupuncture_cross_family_legacy_engine", LEGACY / "transfer_engine.py")
_legacy = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_legacy)
LAYERS, SOURCE_NEURONS, SIGNS = _legacy.LAYERS, _legacy.SOURCE_NEURONS, _legacy.SIGNS
encode_text, encode_pair = _legacy.encode_text, _legacy.encode_pair
text_hash, token_hash = _legacy.text_hash, _legacy.token_hash


class LlamaTokenizer:
    """Make raw benchmark BOS explicit while leaving native chat rendering intact."""
    def __init__(self, tokenizer):
        assert tokenizer.bos_token_id is not None
        self.raw = tokenizer

    def __getattr__(self, name):
        return getattr(self.raw, name)

    def __call__(self, *args, **kwargs):
        return self.raw(*args, **kwargs)

    def apply_chat_template(self, *args, **kwargs):
        kwargs.setdefault("date_string", "26 Oct 2026")
        return self.raw.apply_chat_template(*args, **kwargs)

    def encode(self, text, add_special_tokens=True, **kwargs):
        ids = self.raw.encode(text, add_special_tokens=False, **kwargs)
        if add_special_tokens and (not ids or ids[0] != self.bos_token_id):
            ids = [self.bos_token_id, *ids]
        return ids


def stop_tokens(tokenizer, generation_config, model_config):
    """Union official EOS declarations; never introduce Qwen tokens into LLaMA."""
    stops = set()
    for value in (generation_config.eos_token_id, model_config.eos_token_id, tokenizer.eos_token_id):
        if value is not None:
            stops.update([value] if isinstance(value, int) else value)
    assert stops and all(isinstance(i, int) and 0 <= i < model_config.vocab_size for i in stops)
    vocabulary = tokenizer.get_vocab()
    if "<|eot_id|>" in vocabulary:
        assert vocabulary["<|eot_id|>"] in stops, "Official chat terminator missing from EOS config"
    assert tokenizer.bos_token_id not in stops
    pad = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id
    assert isinstance(pad, int) and 0 <= pad < model_config.vocab_size
    return sorted(stops), pad


def load_tokenizer(model_path):
    from transformers import AutoConfig, AutoTokenizer
    config = AutoConfig.from_pretrained(str(model_path), local_files_only=True, trust_remote_code=False)
    tokenizer = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True, trust_remote_code=False, use_fast=True)
    assert tokenizer.is_fast, "Character-boundary alignment requires a fast tokenizer"
    assert config.model_type in ("qwen3_5", "llama"), f"Unsupported model_type: {config.model_type}"
    return LlamaTokenizer(tokenizer) if config.model_type == "llama" else tokenizer


class CrossFamilyEngine(_legacy.TransferEngine):
    def __init__(self, model_path, device="cuda:0", batch_size=1, threads=4, bundle=None):
        from transformers import AutoConfig
        config = AutoConfig.from_pretrained(str(model_path), local_files_only=True, trust_remote_code=False)
        if config.model_type == "qwen3_5":
            super().__init__(model_path, device, batch_size, threads, bundle)
            return
        assert config.model_type == "llama", f"Unsupported model_type: {config.model_type}"
        import torch
        import transformers
        from transformers import AutoModelForCausalLM

        assert batch_size == 1, "Frozen protocol uses actual forward batch one"
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
        torch.set_num_threads(threads)
        torch.manual_seed(0)
        torch.use_deterministic_algorithms(True)
        self.torch, self.device, self.batch_size = torch, device, batch_size
        self.tokenizer = load_tokenizer(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(str(model_path), local_files_only=True,
            trust_remote_code=False, torch_dtype=torch.bfloat16, attn_implementation="eager").to(device).eval()
        self.model.requires_grad_(False)
        self.layers = self.model.model.layers
        assert len(self.layers) > max(LAYERS)
        self.modules = {layer: self.layers[layer].mlp.down_proj for layer in LAYERS}
        assert all(module.bias is None and module.weight.shape == (config.hidden_size, config.intermediate_size)
                   for module in self.modules.values())
        self.column_norms = {str(layer): module.weight.float().norm(dim=0).cpu() for layer, module in self.modules.items()}
        self.stop_ids, self.pad_id = stop_tokens(self.tokenizer, self.model.generation_config, config)
        self.max_length = config.max_position_embeddings
        self.weight_hashes = self._weight_hashes()
        self.conditions = {"T_0": {}, "S_0": {}, "baseline": {}}
        if bundle is not None:
            payload = torch.load(bundle, map_location="cpu", weights_only=True) if isinstance(bundle, (str, Path)) else bundle
            assert payload["hidden_size"] == config.hidden_size
            assert payload["intermediate_size"] == config.intermediate_size
            assert payload["target_weight_sha256"] == self.weight_hashes
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
            "bos_token_id": self.tokenizer.bos_token_id, "pad_token_id": self.pad_id,
            "max_context_tokens": self.max_length, "chat_template_applied": False,
            "tokenization": "Raw benchmark: one explicit BOS, no EOS; native template BOS is not duplicated",
            "chat_template_date_string": "26 Oct 2026",
            "single_immutable_model": True, "fresh_cache_each_call": True,
            "numerical_settings": {"deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
                "float32_matmul_precision": torch.get_float32_matmul_precision(),
                "matmul_allow_tf32": torch.backends.cuda.matmul.allow_tf32,
                "matmul_allow_bf16_reduced_precision_reduction": torch.backends.cuda.matmul.allow_bf16_reduced_precision_reduction,
                "cublas_workspace_config": os.environ.get("CUBLAS_WORKSPACE_CONFIG")}}


Engine = TransferEngine = CrossFamilyEngine
