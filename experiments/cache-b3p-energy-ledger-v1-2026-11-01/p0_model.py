"""Single-module FP64 recompute of Qwen3.5 decoder MLP branches (post-attention RMSNorm with (1 + w) gain, SiLU-gated MLP)
from the safetensors weights on CPU.  No model forward, no attention, no cache."""
import json
import os
from pathlib import Path

LAYERS = tuple(range(13, 32))
PREFIX = 'model.language_model.'


class MLPs:
    def __init__(self, model_path, layers=LAYERS):
        import torch
        from safetensors import safe_open
        idx = json.load(open(os.path.join(model_path, 'model.safetensors.index.json')))['weight_map']
        cfg = json.load(open(os.path.join(model_path, 'config.json')))
        tc = cfg.get('text_config', cfg)
        assert tc['hidden_act'] == 'silu'
        self.eps = float(tc['rms_norm_eps'])
        want = {}
        for l in layers:
            for n in ('mlp.gate_proj.weight', 'mlp.up_proj.weight', 'mlp.down_proj.weight', 'post_attention_layernorm.weight'):
                want[f'{PREFIX}layers.{l}.{n}'] = (l, n)
        want[f'{PREFIX}norm.weight'] = ('final', 'norm')
        self.w = {}
        files = {}
        for key in want:
            files.setdefault(idx[key], []).append(key)
        for fname, keys in files.items():
            with safe_open(os.path.join(model_path, fname), framework='pt', device='cpu') as f:
                for key in keys:
                    self.w[want[key]] = f.get_tensor(key).double()
        self.final_gain = 1 + self.w[('final', 'norm')]
        self.torch = torch

    def norm(self, l, x):
        t = self.torch
        x = x.double()
        return x * t.rsqrt(x.pow(2).mean() + self.eps) * (1 + self.w[(l, 'post_attention_layernorm.weight')])

    def mlp(self, l, x):
        """f(x) = down(silu(gate(n)) * up(n)), n = RMSNorm(x) (1 + w); FP64 throughout."""
        t = self.torch
        n = self.norm(l, x)
        g = self.w[(l, 'mlp.gate_proj.weight')] @ n
        u = self.w[(l, 'mlp.up_proj.weight')] @ n
        return self.w[(l, 'mlp.down_proj.weight')] @ (t.nn.functional.silu(g) * u)


def model_path():
    import sys
    c2 = Path(__file__).resolve().parent.parent / 'cache-c2-cross-direction-v1-2026-11-01'
    sys.path.insert(0, str(c2))
    import c2_run as V
    return V.exp.read(V.T1.SOURCE / 'contract.json')['source']['model_path']
