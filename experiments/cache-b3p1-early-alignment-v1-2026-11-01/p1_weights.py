"""out_proj weights of the G layers (linear attention), FP64 on CPU, from safetensors.  No module recompute beyond W @ x."""
import json
import os

PREFIX = 'model.language_model.layers.'
HEAD_DIM = 128


def load_out_proj(model_path, layers):
    from safetensors import safe_open
    idx = json.load(open(os.path.join(model_path, 'model.safetensors.index.json')))['weight_map']
    want = {f'{PREFIX}{l}.linear_attn.out_proj.weight': l for l in layers}
    files = {}
    for k in want:
        files.setdefault(idx[k], []).append(k)
    W = {}
    for fname, keys in files.items():
        with safe_open(os.path.join(model_path, fname), framework='pt', device='cpu') as f:
            for k in keys:
                W[want[k]] = f.get_tensor(k).double()
    return W


def block(W, gno_diff, heads):
    """W[:, cols of heads] @ gno_diff[cols of heads]  (exact linear split of out_proj by value-head blocks)."""
    import torch
    if not heads:
        return torch.zeros(W.shape[0], dtype=torch.float64)
    cols = torch.cat([torch.arange(h * HEAD_DIM, (h + 1) * HEAD_DIM) for h in sorted(heads)])
    return W[:, cols] @ gno_diff[cols]
