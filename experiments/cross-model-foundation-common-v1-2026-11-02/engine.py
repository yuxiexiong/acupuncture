"""Four-model engine for the cross-model foundation line (PLAN r3 §4–§7).

Invariants enforced here (each is a preflight gate as well):
* A forward with a non-empty cache processes exactly one token.  Hybrid HF
  layers only read restored recurrent/conv state on the single-token path.
* Positions are explicit: position_ids = arange(pos0, pos0 + width).
* Injection is on/off per absolute token position via `self.active`
  (a set of positions); positions outside it are left bit-identical.
* Native needle: add a constant to one down_proj input coordinate.  Direction
  needle: add a vector to the MLP module output.  Both land on the MLP's
  residual write; the requested write norm is |d| * s * sqrt(hidden), with s
  the clean pre-MLP residual RMS median and, for native channels, the
  effective column = down_multiplier * down_proj.weight[:, c].
* Every injected forward records the realized change of the MLP output at
  each active position (recomputed clean output in the same dtype).
"""
import copy
import hashlib
import math
import os
import random
import time
from contextlib import contextmanager

import torch
import torch.nn.functional as F

import models as M
import tokspan as T

SEED = 20261102


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def tensor_sha(t):
    t = t.detach().contiguous().cpu()
    if t.dtype == torch.bfloat16:
        t = t.view(torch.int16)
    return sha256_bytes(t.numpy().tobytes())


def cache_tensors(cache):
    """All tensors reachable from a cache object, in a deterministic order."""
    out = []

    def walk(o, depth=0):
        if depth > 6:
            return
        if torch.is_tensor(o):
            out.append(o)
        elif isinstance(o, (list, tuple)):
            for x in o:
                walk(x, depth + 1)
        elif isinstance(o, dict):
            for k in sorted(o, key=str):
                walk(o[k], depth + 1)
        elif hasattr(o, "__dict__"):
            for k in sorted(vars(o)):
                walk(vars(o)[k], depth + 1)
    walk(cache)
    return out


def cache_fingerprint(cache):
    h = hashlib.sha256()
    n = 0
    for t in cache_tensors(cache):
        h.update(tensor_sha(t).encode())
        n += t.numel() * t.element_size()
    return {"sha256": h.hexdigest(), "bytes": n}


def needle_set(key, layer, intermediate, hidden):
    """PLAN r3 §4: 4 native channels without replacement + 2 Gaussian unit directions."""
    channels = random.Random(f"{SEED}|{key}|{layer}|native").sample(range(intermediate), 4)
    dirs = []
    for j in range(2):
        g = torch.Generator().manual_seed(int(sha256_bytes(f"{SEED}|{key}|{layer}|dir{j}".encode())[:15], 16))
        v = torch.randn(hidden, generator=g, dtype=torch.float64)
        dirs.append(v / v.norm())
    return ([{"kind": "native", "channel": c, "name": f"N{c}"} for c in channels]
            + [{"kind": "direction", "vector": v, "name": f"R{j}",
                "vector_sha256": tensor_sha(v)} for j, v in enumerate(dirs)])


class Engine:
    def __init__(self, key, device="cuda:0"):
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
        torch.use_deterministic_algorithms(True, warn_only=True)
        from transformers import AutoTokenizer
        self.key, self.device = key, device
        spec = M.MODELS[key]
        self.tok = AutoTokenizer.from_pretrained(spec["path"], local_files_only=True)
        t0 = time.monotonic()
        self.model = M.load_model(key, device)
        self.load_seconds = time.monotonic() - t0
        self.tcfg = M.text_config(self.model.config)
        self.layers = M.get_layers(self.model, key)
        self.final_norm = M.get_final_norm(self.model, key)
        self.H = self.tcfg.hidden_size
        self.n_layers = len(self.layers)
        self.picks = M.pick_layers(self.n_layers)
        self.mult = M.down_multiplier(key, self.tcfg)
        self.stop_ids = M.stop_ids(spec["path"], self.tok)
        self.mlp = {l: M.get_mlp(self.layers[l], key) for l in self.picks}
        self.eff_col_norm = {l: (self.mlp[l].down_proj.weight.float().norm(dim=0) * self.mult).cpu()
                             for l in self.picks}
        assert all(self.mlp[l].down_proj.bias is None for l in self.picks)
        self.intermediate = self.mlp[self.picks[0]].down_proj.weight.shape[1]
        self.active = set()
        self._ctx = None
        self.audit = []
        self.recorder = None

    # ---------- identity ----------
    def weight_hash(self):
        h = hashlib.sha256()
        for name, p in sorted(self.model.named_parameters(), key=lambda x: x[0]):
            h.update(name.encode())
            h.update(tensor_sha(p).encode())
        return h.hexdigest()

    def encode(self, item):
        return T.encode_item(self.tok, self.key, item)

    def cont_ids(self, item, text):
        return T.continuation_ids(self.tok, self.key, item, text)

    # ---------- forward ----------
    def step(self, ids, cache, pos0):
        width = len(ids)
        assert width >= 1
        if cache is not None:
            assert width == 1, "multi-token forward on a non-empty cache is forbidden (hybrid seq_len==1 path)"
        else:
            assert pos0 == 0
        dev = self.device
        inp = torch.tensor([ids], device=dev)
        pos = torch.arange(pos0, pos0 + width, device=dev).view(1, -1)
        mask = torch.ones((1, pos0 + width), device=dev, dtype=torch.long)
        self._ctx = (pos0, width)
        with torch.inference_mode():
            out = self.model(input_ids=inp, position_ids=pos, attention_mask=mask,
                             past_key_values=cache, use_cache=True, logits_to_keep=1)
        self._ctx = None
        assert out.past_key_values is not None
        return out.logits[0, -1].float(), out.past_key_values

    def _mask(self, ref):
        pos0, width = self._ctx
        m = torch.tensor([(pos0 + i) in self.active for i in range(width)], device=ref.device)
        return m

    # ---------- injection ----------
    def requested_norm(self, scale, dose):
        return abs(dose) * scale * math.sqrt(self.H)

    @contextmanager
    def needle(self, layer, needle, scale, dose):
        """Install the needle on `layer`.  Active positions come from self.active."""
        mlp = self.mlp[layer]
        target = self.requested_norm(scale, dose)
        sign = 1.0 if dose >= 0 else -1.0
        handles, saved = [], {}
        W = mlp.down_proj.weight
        if needle["kind"] == "native":
            c = needle["channel"]
            col = float(self.eff_col_norm[layer][c])
            amount = W.new_tensor(sign * target / col)

            def pre(_m, args):
                x = args[0]
                saved["x"] = x
                m = self._mask(x)
                if not m.any():
                    return None
                y = x.clone()
                y[0, m, c] = y[0, m, c] + amount
                return (y, *args[1:])
            handles.append(mlp.down_proj.register_forward_pre_hook(pre))

            def post(_m, _a, out):
                m = self._mask(out)
                x = saved.pop("x")
                clean = F.linear(x, W)
                if self.mult != 1.0:
                    clean = clean * self.mult
                self._audit(layer, out, clean, m, target, needle)
                return None
            handles.append(mlp.register_forward_hook(post))
        else:
            vec = (needle["vector"].to(torch.float32) * (sign * target)).to(device=W.device, dtype=W.dtype)

            def post(_m, _a, out):
                m = self._mask(out)
                if not m.any():
                    self._audit(layer, out, out, m, target, needle)
                    return None
                new = out.clone()
                new[0, m] = new[0, m] + vec
                self._audit(layer, new, out, m, target, needle)
                return new
            handles.append(mlp.register_forward_hook(post))
        try:
            yield
        finally:
            for h in handles:
                h.remove()

    def _audit(self, layer, out, clean, m, target, needle):
        delta = (out.float() - clean.float())[0]
        inactive_max = float(delta[~m].abs().max()) if (~m).any() else 0.0
        norms = delta[m].norm(dim=-1).tolist() if m.any() else []
        pos0, width = self._ctx
        self.audit.append({"layer": layer, "needle": needle["name"], "pos0": pos0, "width": width,
                           "active_positions": [pos0 + i for i in range(width) if bool(m[i])],
                           "requested_norm": target, "realized_norms": norms,
                           "inactive_max_abs_change": inactive_max})

    # ---------- residual scale ----------
    def residual_rms(self, ids, layers=None):
        layers = layers or self.picks
        got, handles = {}, []
        for l in layers:
            def pre(_m, args, l=l):
                got[l] = args[0][0].float().pow(2).mean(dim=-1).sqrt().cpu()
            handles.append(M.get_pre_mlp_norm(self.layers[l], self.key).register_forward_pre_hook(pre))
        try:
            self.step(ids, None, 0)
        finally:
            for h in handles:
                h.remove()
        return got

    # ---------- deep recorder ----------
    @contextmanager
    def record(self, positions):
        """Capture residual-level fields at absolute `positions` (set) for all layers."""
        rec = {}
        handles = []

        def put(name, l, x):
            pos0, width = self._ctx
            for i in range(width):
                p = pos0 + i
                if p in positions:
                    rec.setdefault(p, {}).setdefault(name, {})[l] = x[0, i].detach().clone().cpu()

        for l, block in enumerate(self.layers):
            def bpre(_m, args, kwargs, l=l):
                h = args[0] if args else kwargs["hidden_states"]
                put("block_in", l, h)
            handles.append(block.register_forward_pre_hook(bpre, with_kwargs=True))

            def npre(_m, args, l=l):
                put("pre_mlp_residual", l, args[0])
            handles.append(M.get_pre_mlp_norm(block, self.key).register_forward_pre_hook(npre))

            def mpost(_m, _a, out, l=l):
                put("mlp_write", l, out)
            handles.append(M.get_mlp(block, self.key).register_forward_hook(mpost))
            if self.key == "falcon_h1_3b":
                so, ao = block.ssm_out_multiplier, block.attn_out_multiplier

                def mamba_post(_m, _a, out, l=l, so=so):
                    o = out[0] if isinstance(out, tuple) else out
                    put("ssm_write", l, o * so)
                handles.append(block.mamba.register_forward_hook(mamba_post))

                def attn_post(_m, _a, out, l=l, ao=ao):
                    o = out[0] if isinstance(out, tuple) else out
                    put("attn_write", l, o * ao)
                handles.append(block.self_attn.register_forward_hook(attn_post))

        def fpre(_m, args):
            put("final_in", -1, args[0])
        handles.append(self.final_norm.register_forward_pre_hook(fpre))
        try:
            yield rec
        finally:
            for h in handles:
                h.remove()

    # ---------- readouts ----------
    def readout(self, logits, keep_full=True):
        lp = torch.log_softmax(logits, dim=-1)
        stop = torch.tensor(self.stop_ids, device=logits.device)
        top = torch.topk(lp, 32)
        r = {"eos_set_prob": float(lp[stop].exp().sum()),
             "greedy": int(logits.argmax()),
             "greedy_is_eos": int(logits.argmax()) in self.stop_ids,
             "entropy": float(-(lp.exp() * lp).sum()),
             "logsumexp": float(torch.logsumexp(logits, dim=-1)),
             "top32_ids": top.indices.tolist(), "top32_logprobs": top.values.tolist(),
             "logits_sha256": tensor_sha(logits)}
        if keep_full:
            r["_logits"] = logits.detach().to(torch.float16).cpu()
        return r

    def score_candidates(self, logits_q, cache_q, pos_next, cand_ids):
        """Total log-likelihood of each candidate token list; no needle (active must be empty)."""
        assert not self.active
        out = []
        lp0 = torch.log_softmax(logits_q, dim=-1)
        for ids in cand_ids:
            total, per = float(lp0[ids[0]]), [float(lp0[ids[0]])]
            if len(ids) > 1:
                cache = copy.deepcopy(cache_q)
                for i in range(len(ids) - 1):
                    lg, cache = self.step([ids[i]], cache, pos_next + i)
                    v = float(torch.log_softmax(lg, dim=-1)[ids[i + 1]])
                    total += v
                    per.append(v)
                del cache
            out.append({"loglik": total, "token_logprobs": per, "token_ids": ids})
        return out

    def greedy(self, logits, cache, pos, max_new, on_step=None, active_from=None):
        """Greedy continue from `logits` (prediction for position `pos`).

        Returns generated tokens (stop token included if produced) and per-step readouts.
        If active_from is not None, positions >= active_from are injected.
        """
        toks, reads = [], []
        for i in range(max_new):
            r = self.readout(logits, keep_full=False)
            t = r["greedy"]
            r["chosen"] = t
            r["chosen_logprob"] = float(torch.log_softmax(logits, dim=-1)[t])
            toks.append(t)
            reads.append(r)
            if on_step:
                on_step(i, t, cache)
            if t in self.stop_ids or i == max_new - 1:
                break
            if active_from is not None and pos >= active_from:
                self.active.add(pos)
            logits, cache = self.step([t], cache, pos)
            pos += 1
        return toks, reads, logits, cache, pos
