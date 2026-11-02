"""Model registry and architecture adapters for the cross-model foundation line.

Everything architecture-specific lives here.  The rest of the code only uses:
layers, the MLP module (its output is the residual write), the effective
write column of a native channel (down_proj column times any output
multiplier), the pre-MLP residual (input of the pre-MLP norm), and the final
norm.  Identities follow docs/f0-receipts-cross-model-2026-11-01.
"""
import json
import math
import os

MODELS = {
    "qwen35_4b": {
        "path": "/data/models/Qwen3.5-4B-851bf6e",
        "hf_repo": "Qwen/Qwen3.5-4B",
        "revision": "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a",
        "identity": "hf_revision",
    },
    "qwen3_4b": {
        "path": "/workspace/models/Qwen3-4B-1cfa9a72",
        "hf_repo": "Qwen/Qwen3-4B",
        "revision": "1cfa9a7208912126459214e8b04321603b3df60c",
        "identity": "hf_revision",
    },
    "llama32_3b": {
        "path": "/workspace/deployed_regime/models/Llama-3.2-3B-Instruct",
        "hf_repo": "meta-llama/Llama-3.2-3B-Instruct",
        "revision": "modelscope:LLM-Research/Llama-3.2-3B-Instruct@master",
        "identity": "modelscope_mirror_hash_only",
    },
    "falcon_h1_3b": {
        "path": "/workspace/models/Falcon-H1-3B-Instruct-01087ec4",
        "hf_repo": "tiiuae/Falcon-H1-3B-Instruct",
        "revision": "01087ec4c132d7f186908716b3530ea187f062a1",
        "identity": "hf_revision",
    },
}

# Llama 3.2's template inserts "Today Date" from the wall clock unless given.
LLAMA_DATE_STRING = "26 Jul 2024"


def pick_layers(n_layers):
    """PLAN r3 §4: floor(0.1(L-1)), floor(0.5(L-1)), floor(0.85(L-1))."""
    return [math.floor(f * (n_layers - 1)) for f in (0.1, 0.5, 0.85)]


def text_config(cfg):
    return getattr(cfg, "text_config", None) or cfg


def model_class(key):
    if key == "qwen35_4b":
        from transformers import Qwen3_5ForConditionalGeneration
        return Qwen3_5ForConditionalGeneration
    from transformers import AutoModelForCausalLM
    return AutoModelForCausalLM


def build_from_config(key, cfg):
    cls = model_class(key)
    return cls._from_config(cfg) if key == "qwen35_4b" else cls.from_config(cfg)


def load_model(key, device, dtype=None):
    import torch
    spec = MODELS[key]
    return model_class(key).from_pretrained(
        spec["path"], local_files_only=True, trust_remote_code=False,
        dtype=dtype or torch.bfloat16, attn_implementation="eager").to(device).eval()


def get_layers(model, key):
    if key == "qwen35_4b":
        return model.model.language_model.layers
    return model.model.layers


def get_text_model(model, key):
    return model.model.language_model if key == "qwen35_4b" else model.model


def get_final_norm(model, key):
    tm = get_text_model(model, key)
    for name in ("norm", "final_layernorm"):
        if hasattr(tm, name):
            return getattr(tm, name)
    raise AttributeError(f"no final norm on {key}")


def get_mlp(block, key):
    return block.feed_forward if key == "falcon_h1_3b" else block.mlp


def get_pre_mlp_norm(block, key):
    """Its input is the residual stream right before the MLP write is added."""
    return block.pre_ff_layernorm if key == "falcon_h1_3b" else block.post_attention_layernorm


def down_multiplier(key, tcfg):
    """Scalar applied to down_proj output inside the MLP module (1.0 if none)."""
    if key == "falcon_h1_3b":
        return float(tcfg.mlp_multipliers[1])
    return 1.0


def layer_types(key, tcfg):
    n = tcfg.num_hidden_layers
    if key == "qwen35_4b":
        return list(tcfg.layer_types)
    if key == "falcon_h1_3b":
        return ["parallel_attention_mamba2"] * n
    return ["full_attention"] * n


def template_kwargs(key):
    if key in ("qwen35_4b", "qwen3_4b"):
        return {"enable_thinking": False}
    if key == "llama32_3b":
        return {"date_string": LLAMA_DATE_STRING}
    return {}


def render(tok, key, user_text):
    return tok.apply_chat_template([{"role": "user", "content": user_text}], tokenize=False,
                                   add_generation_prompt=True, **template_kwargs(key))


def template_ids(tok, key, user_text):
    out = tok.apply_chat_template([{"role": "user", "content": user_text}], tokenize=True,
                                  add_generation_prompt=True, **template_kwargs(key))
    if isinstance(out, dict) or hasattr(out, "keys"):
        out = out["input_ids"]
    return list(out)


def stop_ids(path, tok):
    ids = set()
    gc = os.path.join(path, "generation_config.json")
    if os.path.exists(gc):
        e = json.load(open(gc)).get("eos_token_id")
    else:
        cfg = json.load(open(os.path.join(path, "config.json")))
        e = cfg.get("eos_token_id", (cfg.get("text_config") or {}).get("eos_token_id"))
    if isinstance(e, int):
        ids.add(e)
    elif e:
        ids.update(e)
    if tok.eos_token_id is not None:
        ids.add(tok.eos_token_id)
    return sorted(ids)
