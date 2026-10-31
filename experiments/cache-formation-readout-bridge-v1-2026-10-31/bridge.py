"""CFM-FORM-READ-BRIDGE v1: same-needle deep V crossings, recurrent-state crossings and final-scale records
(CONTRACT.zh-CN.md r01; design docs/cache-formation-readout-bridge-plan-v1-2026-10-31.zh-CN.md r3).

Built on the frozen CFM-FORM-AB v2 code (form_ab.py, A5): same inputs, needle, late window, step route, B and unified
C-shallow scoring. Imports never load a model.

Formations (all from the shared clean chunk 0..b, then one token per position in L):
  C  T  H(=A5 XB)                           pass 1 (lockstep; C's shallow snapshots drive B; natural deep V bands)
  U=T+V_H  W=H+V_T  TC=T+V_C  CT=C+V_T  TR0/TR1=T+(V_T+xi)   pass 2 (V pinned on the 14 deep linear layers)
V = in_proj_qkv value slice before the causal conv. xi: random direction, norm per (layer, position) = ||V_C - V_T||.
Scores (first step on x[n-1], C shallow + own deep, no formation hook; read-only recorder active):
  C, T_native, Y_T, Y_H, Y_U, Y_W, Y_TC, Y_CT, Y_TR0, Y_TR1 and J(T<-S_U), J(U<-S_T), J(W<-S_H), J(H<-S_W).

python bridge.py freeze PATH
python bridge.py run --stage preflight|formal --worker W --authorization AUTH --output DIR   (GPU = W % 2)
python bridge.py verify WORKER_DIR
python bridge.py launch --stage STAGE --authorization AUTH --output RUN_DIR
"""
import argparse
import copy
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
FAB_DIR = HERE.parent / 'cache-formation-mechanism-formation-ab-v2-2026-10-31'
sys.path.insert(0, str(FAB_DIR))
import form_ab as F  # noqa: E402  (frozen A5 code)
E2, S3, T1, L, ST2, S2T, exp = F.E2, F.S3, F.T1, F.L, F.ST2, F.S2T, F.exp

PLAN_ID = 'CFM-FORM-READ-BRIDGE-v1-20261031'
PLAN_DOC = REPO / 'docs/cache-formation-readout-bridge-plan-v1-2026-10-31.zh-CN.md'
FAB_FORMAL = FAB_DIR / 'runs/formal-r01'
TOKENS = HERE / 'data/frozen-tokens-r01.json'
REFERENCE = F.REFERENCE
G_REAL = (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
PASS1 = ('C', 'T', 'H')
PASS2 = ('U', 'W', 'TC', 'CT', 'TR0', 'TR1')
FORMS = PASS1 + PASS2
SPEC = {'C': (False, False, None), 'T': (True, False, None), 'H': (True, True, None),
        'U': (True, False, 'H'), 'W': (True, True, 'T'), 'TC': (True, False, 'C'), 'CT': (False, False, 'T'),
        'TR0': (True, False, 'R0'), 'TR1': (True, False, 'R1')}          # (needle, B, V band)
J_DEF = {'J_T_SU': ('T', 'U'), 'J_U_ST': ('U', 'T'), 'J_W_SH': ('W', 'H'), 'J_H_SW': ('H', 'W')}  # receiver, state donor
SCORES = ('C', 'T_native', 'Y_T', 'Y_H', 'Y_U', 'Y_W', 'Y_TC', 'Y_CT', 'Y_TR0', 'Y_TR1') + tuple(J_DEF)
COMPARISONS = (('Y_T', 'Y_H'), ('Y_T', 'Y_U'), ('Y_W', 'Y_H'), ('Y_T', 'Y_W'), ('Y_U', 'Y_H'),
               ('Y_T', 'J_T_SU'), ('J_U_ST', 'Y_U'), ('J_T_SU', 'Y_U'), ('Y_T', 'J_U_ST'),
               ('Y_W', 'J_W_SH'), ('J_H_SW', 'Y_H'), ('J_W_SH', 'Y_H'), ('Y_W', 'J_H_SW'),
               ('Y_T', 'C'), ('Y_T', 'Y_TC'), ('Y_CT', 'C'), ('Y_T', 'Y_TR0'), ('Y_T', 'Y_TR1'))
SEED = 20261031
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
PREFLIGHT_ITEM = F.PREFLIGHT_ITEM
LIMITS = {'preflight': {'prefixes': 14, 'scores': 22}, 'formal': {'prefixes': 108, 'scores': 168}}
STORAGE_LIMIT = 16 * 2 ** 30
RECON_TOL = {'state_rel': 1e-5, 'core_rel': 5e-3}


def items():
    return F.items()


def g_layers(types, split):
    return tuple(i for i in range(split, len(types)) if types[i] == 'linear_attention')


def full_deep(types, split):
    return tuple(i for i in range(split, len(types)) if types[i] == 'full_attention')


# ---------------------------------------------------------------- formation-time V pinning (the only intervention hook)

class VHook:
    """Forward hook on in_proj_qkv of the G layers (single-token steps). Records the natural V slice; if a band is set,
    replaces the V slice by band[layer][k] and leaves the q/k slices untouched."""

    def __init__(self, model, layers, v0, v1):
        self.model, self.layers, self.v0, self.v1 = model, tuple(layers), v0, v1
        self.band, self.k = None, None
        self.natural, self.applied, self.violations, self.handles = {}, {}, [], []

    def __enter__(self):
        blocks = L.model_layers(self.model)
        for i in self.layers:
            self.handles.append(blocks[i].linear_attn.in_proj_qkv.register_forward_hook(self._hook(i)))
        return self

    def _hook(self, layer):
        def hook(_m, _a, out):
            assert out.shape[1] == 1 and out.shape[-1] == self.v1, out.shape
            self.natural[layer] = out[0, -1, self.v0:self.v1].detach().clone()
            if self.band is None:
                return None
            donor = self.band[layer][self.k]
            new = out.clone()
            new[0, -1, self.v0:self.v1] = donor.to(device=out.device, dtype=out.dtype)
            if not (bool(torch_equal(new[..., :self.v0], out[..., :self.v0]))
                    and bool(torch_equal(new[0, -1, self.v0:self.v1], donor.to(out.device, out.dtype)))):
                self.violations.append((layer, self.k))
            self.applied[layer] = new[0, -1, self.v0:self.v1].detach().clone()
            return new
        return hook

    def __exit__(self, *exc):
        for h in reversed(self.handles):
            h.remove()
        self.handles = []
        return False


def torch_equal(a, b):
    import torch
    return torch.equal(a, b)


# ---------------------------------------------------------------- read-only recorder

class Recorder:
    """Pass-through wrapper of the recurrent delta rule plus read-only forward hooks.
    Formation phase: G-layer kernel drivers, old-state / current-write readout terms, z, core output, state norms.
    Score phase additionally: full-attention q/k/v projections and outputs, deep decoder in/out residuals, final-norm
    input and output. Nothing returned to the model is modified."""

    def __init__(self, model, layers, split, score_extras=True):
        self.model, self.layers, self.split = model, tuple(layers), split
        self.types = L.layer_types(model)
        self.score_extras = score_extras
        self.key, self.current = None, None
        self.rows, self.extra = {}, {}
        self.handles, self.saved = [], None

    def _row(self, layer):
        return self.rows.setdefault(self.key, {}).setdefault(layer, {})

    def _wrap(self, fn):
        import torch
        qm = T1.qwen_module()

        def inner(*args, **kwargs):
            out = fn(*args, **kwargs)
            layer = self.current
            if self.key is None or layer not in self.layers:
                return out
            q, k, v = args[0], args[1], args[2]
            g, beta, s_old = kwargs['g'], kwargs['beta'], kwargs.get('initial_state')
            assert q.shape[1] == 1 and kwargs.get('use_qk_l2norm_in_kernel') is True and s_old is not None
            core, s_new = out
            with torch.no_grad():
                qf, kf = qm.l2norm(q[0, 0].float(), dim=-1, eps=1e-6), qm.l2norm(k[0, 0].float(), dim=-1, eps=1e-6)
                qf = qf / (qf.shape[-1] ** 0.5)
                alpha, b = g[0, 0].float().exp(), beta[0, 0].float()
                kq = (kf * qf).sum(-1)
                w = alpha[:, None] * (qf - b[:, None] * kf * kq[:, None])
                so = s_old[0].float()
                old = torch.einsum('hiv,hi->hv', so, w)
                new = b[:, None] * v[0, 0].float() * kq[:, None]
            r = self._row(layer)
            r.update(q=q[0, 0].detach().clone(), k=k[0, 0].detach().clone(), v=v[0, 0].detach().clone(),
                     g=g[0, 0].detach().clone(), beta=beta[0, 0].detach().clone(), core=core[0, 0].detach().clone(),
                     old=old.detach().clone(), new=new.detach().clone(),
                     s_old_norm=float(so.norm()), s_new_norm=float(s_new[0].float().norm()))
            return out
        inner.__wrapped_original__ = fn
        return inner

    def __enter__(self):
        qm = T1.qwen_module()
        self.saved = qm.torch_recurrent_gated_delta_rule
        qm.torch_recurrent_gated_delta_rule = self._wrap(self.saved)
        blocks = L.model_layers(self.model)
        for i in self.layers:
            attn = blocks[i].linear_attn
            self.handles.append(attn.register_forward_pre_hook(lambda _m, _a, i=i: setattr(self, 'current', i)))
            self.handles.append(attn.register_forward_hook(lambda _m, _a, _o: setattr(self, 'current', None)))
            self.handles.append(attn.in_proj_z.register_forward_hook(
                lambda _m, _a, o, i=i: self._put(i, 'z', o[0, -1])))
        if self.score_extras:
            for i in full_deep(self.types, self.split):
                at = blocks[i].self_attn
                for name in ('q_proj', 'k_proj', 'v_proj'):
                    self.handles.append(getattr(at, name).register_forward_hook(
                        lambda _m, _a, o, i=i, name=name: self._extra(f'{i}:{name}', o[0, -1])))
                self.handles.append(at.register_forward_hook(lambda _m, _a, o, i=i: self._extra(f'{i}:attn_out', o[0][0, -1])))
            for i in range(self.split, len(self.types)):
                self.handles.append(blocks[i].register_forward_pre_hook(lambda _m, a, i=i: self._extra(f'{i}:in', a[0][0, -1])))
                self.handles.append(blocks[i].register_forward_hook(
                    lambda _m, _a, o, i=i: self._extra(f'{i}:out', (o[0] if isinstance(o, tuple) else o)[0, -1])))
            fn = S3.final_norm(self.model)
            self.handles.append(fn.register_forward_pre_hook(lambda _m, a: self._extra('final:h', a[0][0, -1])))
            self.handles.append(fn.register_forward_hook(lambda _m, _a, o: self._extra('final:normed', o[0, -1])))
        return self

    def _put(self, layer, name, t):
        if self.key is not None and layer in self.layers:
            self._row(layer)[name] = t.detach().clone()

    def _extra(self, name, t):
        if self.key is not None and isinstance(self.key, str):
            self.extra.setdefault(self.key, {})[name] = t.detach().clone()

    def __exit__(self, *exc):
        for h in reversed(self.handles):
            h.remove()
        self.handles = []
        T1.qwen_module().torch_recurrent_gated_delta_rule = self.saved
        return False


class _Off:
    """Stand-in when the recorder is disabled (preflight recorder-off replay)."""
    key = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


# ---------------------------------------------------------------- helpers

def to_cpu(x):
    if hasattr(x, 'detach'):
        return x.detach().cpu()
    if isinstance(x, dict):
        return {k: to_cpu(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return type(x)(to_cpu(v) for v in x)
    return x


def item_seed(item_id, draw, base=SEED):
    import zlib
    return base + 1000 * draw + zlib.crc32(item_id.encode())


def random_band(v_t, v_c, seed):
    """V_T + xi, ||xi|| = ||V_C - V_T|| per (layer, position), uniformly random direction (CPU generator, fixed seed)."""
    import torch
    gen = torch.Generator().manual_seed(seed)
    out, norms = {}, {}
    for layer in sorted(v_t):
        a, c = v_t[layer].float().cpu(), v_c[layer].float().cpu()
        mag = (c - a).norm(dim=-1, keepdim=True)
        u = torch.randn(a.shape, generator=gen)
        u = u / u.norm(dim=-1, keepdim=True)
        xi = u * mag
        out[layer] = (a + xi).to(v_t[layer].dtype).to(v_t[layer].device)
        norms[layer] = {'target': mag.squeeze(-1).tolist(), 'xi': xi.norm(dim=-1).tolist()}
    return out, norms


def reconstruct(s_b, rows, keys, layer):
    """CPU float64 rebuild of the recurrent state and core outputs of one layer from the recorded kernel drivers."""
    import torch
    S = s_b.detach().cpu().double().clone()[0]
    worst = 0.0
    for key in keys:
        r = rows[key][layer]
        r = {name: (v.detach().cpu() if hasattr(v, 'detach') else v) for name, v in r.items()}
        q = r['q'].double()
        k = r['k'].double()
        q = q * torch.rsqrt((q * q).sum(-1, keepdim=True) + 1e-6) / (q.shape[-1] ** 0.5)
        k = k * torch.rsqrt((k * k).sum(-1, keepdim=True) + 1e-6)
        v, g, b = r['v'].double(), r['g'].double(), r['beta'].double()
        S = S * g.exp()[:, None, None]
        kv = torch.einsum('hiv,hi->hv', S, k)
        S = S + torch.einsum('hi,hv->hiv', k, (v - kv) * b[:, None])
        o = torch.einsum('hiv,hi->hv', S, q)
        ref = r['core'].double()
        rel = float((o - ref).norm() / max(float(ref.norm()), 1e-8))
        worst = max(worst, rel)
    return S, worst


# ---------------------------------------------------------------- scoring with records

def entropy(logits):
    import torch
    lp = torch.log_softmax(logits.double(), -1)
    return float(-(lp.exp() * lp).sum())


def score(engine, cache, last, n, rec, key, token_set, expected_hooks):
    """First step from an independent deep copy. Only the read-only recorder may be installed."""
    import torch
    model, stop = engine.model, list(engine.stop_ids)
    assert F.hook_counts(model) == expected_hooks, 'a formation hook is still installed during scoring'
    rec.key = key
    try:
        with torch.inference_mode():
            out = L.forward(model, [last], n - 1, copy.deepcopy(cache))
    finally:
        rec.key = None
    logits = out.logits[0, -1].float()
    assert torch.isfinite(logits).all()
    non = logits.clone()
    non[stop] = -float('inf')
    lp = torch.log_softmax(logits, -1)
    top = lp.topk(5)
    res = {'token': int(logits.argmax()), 'stop_advantage': T1.stop_advantage(logits, stop),
           'first_step_eos': int(logits.argmax()) in stop, 'logits_sha256': F.th(logits),
           'top5': [{'token_id': int(t), 'logprob': float(v)} for v, t in zip(top.values, top.indices)],
           'stop_winner': stop[int(logits[stop].argmax())], 'nonstop_winner': int(non.argmax()), 'entropy': entropy(logits)}
    ex = rec.extra.get(key) if isinstance(rec, Recorder) else None
    if ex is not None:
        fn = S3.final_norm(model)
        h = ex['final:h']
        var = h.float().pow(2).mean()
        r = float(torch.sqrt(var + fn.eps))
        recomputed = (h.float() * torch.rsqrt(var + fn.eps) * (1.0 + fn.weight.float())).to(h.dtype)
        res['final_norm'] = {'r': r, 'mean_h2': float(var), 'eps': fn.eps, 'gain': '1+weight',
                             'normed_bitwise': bool(torch.equal(recomputed, ex['final:normed']))}
        head = model.get_output_embeddings()
        assert getattr(head, 'bias', None) is None
        toks = sorted(set(token_set) | {res['stop_winner'], res['nonstop_winner'], res['token']})
        hn = h.double() * torch.rsqrt(h.double().pow(2).mean() + fn.eps) * (1.0 + fn.weight.double())
        z64 = head.weight[toks].double() @ hn
        res['token_logits'] = {str(t): float(logits[t]) for t in toks}
        res['token_logits_fp64'] = {str(t): float(z) for t, z in zip(toks, z64)}
        res['eta'] = max(abs(float(z) - float(logits[t])) for t, z in zip(toks, z64))
    return res, logits.detach().cpu()


def centered_unit(z):
    import torch
    c = z.double() - z.double().mean()
    nrm = float(c.norm())
    return None if nrm < 1e-12 else c / nrm


# ---------------------------------------------------------------- one input

def run_item(engine, reference, prompt, labels, item_id, token_set, a5=None, n=32, split=13, needle=None,
             g=None, preflight_extras=False, keep_tensors=True, seed_base=SEED):
    """Returns (record body, tensors). AssertionError on any engineering gate failure."""
    import torch
    model = engine.model
    F.hook_baseline(model)
    types = L.layer_types(model)
    assert len(types) == n
    G = tuple(g) if g is not None else g_layers(types, split)
    if n == 32:
        assert G == G_REAL, G
    cond = needle if needle is not None else T1.engine_condition(F.A0)
    device = next(model.parameters()).device
    lay = S3.layout(model)
    v0, v1 = 2 * lay['kd'], 2 * lay['kd'] + lay['vd']
    prefix, last, n_prompt = prompt[:-1], prompt[-1], len(prompt)
    b = S2T.boundary_b(labels)
    window = list(range(b + 1, n_prompt - 1))
    shallow, deep = tuple(range(0, split)), tuple(range(split, n))
    bf = F.layer_fields(types, F.b_layers(split))
    counts = {'prefixes': 0, 'scores': 0}
    gates = {}

    with torch.inference_mode():
        base = L.forward(model, list(prefix[:b + 1]), 0, None).past_key_values
    s_b = {i: L._get(base.layers[i], 'recurrent_states').detach().clone() for i in G}

    rec = Recorder(model, G, split)
    with rec:
        expected_hooks = F.hook_counts(model)            # recorder only
    # ---- formation passes
    def formation(names, bands, c_snaps, record=True, spec=SPEC):
        caches = {x: copy.deepcopy(base) for x in names}
        counts['prefixes'] += len(names)
        snaps, snap_hashes, r0, nat, app, viol = [], [], {x: [] for x in names}, {x: {i: [] for i in G} for x in names}, \
            {x: {i: [] for i in G} for x in names}, []
        recorder = Recorder(model, G, split, score_extras=False) if record else _Off()
        with recorder, VHook(model, G, v0, v1) as vh:
            for k, t in enumerate(window):
                if 'C' in names:
                    snap = F.snapshot(caches['C'], bf)
                    snaps.append({key: v.detach().cpu() for key, v in snap.items()})
                    snap_hashes.append(F.snapshot_hashes(snap))
                    donor = snap
                else:
                    donor = None
                for x in names:
                    use_needle, use_b, band = spec[x]
                    if use_b:
                        d = donor if donor is not None else {key: v.to(device) for key, v in c_snaps[k].items()}
                        F.fix_shallow(caches[x], d, types, t)
                    vh.band = bands[band] if band is not None else None
                    vh.k = k
                    if record:
                        recorder.key = (x, t)
                    caches[x], hk = F.forward_tokens(engine, caches[x], [prefix[t]], t, cond if use_needle else None, reference)
                    if record:
                        recorder.key = None
                    if use_b:
                        assert F.b_source_check(caches[x], d, types), ('B source check', x, t)
                    r0[x].append(F.th(hk.r0))
                    for i in G:
                        nat[x][i].append(vh.natural[i])
                        if band is not None:
                            app[x][i].append(vh.applied[i])
                viol += vh.violations
                vh.violations = []
        assert not viol, ('V replacement touched q/k or differs from donor', viol[:3])
        nat = {x: {i: torch.stack(v) for i, v in d.items()} for x, d in nat.items()}
        app = {x: {i: torch.stack(v) for i, v in d.items()} for x, d in app.items() if d[G[0]]}
        rows = recorder.rows if record else {}
        return caches, snaps, snap_hashes, r0, nat, app, rows

    p1 = formation(PASS1, {}, None)
    caches, c_snaps, c_snap_hashes, r0, nat, app, rows = p1
    if a5 is not None:
        assert c_snap_hashes == a5['donor_hashes'], 'B donors (C shallow snapshots) differ from A5'
    bands = {'C': nat['C'], 'T': nat['T'], 'H': nat['H']}
    rb = {}
    for d in (0, 1):
        bands[f'R{d}'], rb[f'R{d}'] = random_band(nat['T'], nat['C'], item_seed(item_id, d, seed_base))
    bands_hash = {k: {str(i): F.th(v) for i, v in d.items()} for k, d in bands.items()}
    p2 = formation(PASS2, bands, c_snaps)
    caches.update(p2[0])
    for x in PASS2:
        r0[x] = p2[3][x]
        nat[x] = p2[4][x]
    app.update(p2[5])
    rows.update(p2[6])
    assert {k: {str(i): F.th(v) for i, v in d.items()} for k, d in bands.items()} == bands_hash, 'donor bands modified'
    for x in PASS2:
        band = SPEC[x][2]
        assert all(torch.equal(app[x][i].to(bands[band][i].device), bands[band][i]) for i in G), ('applied V != band', x)
    # timing / structure gates
    for x in FORMS:
        same = 'T' if SPEC[x][0] else 'C'
        assert r0[x] == r0[same], ('layer-0 output differs', x)
    for x in FORMS:
        assert F.manifest(caches[x], types, (0,)) == F.manifest(caches['C'], types, (0,)), ('layer 0', x)
    shallow_ref = {'U': 'T', 'TC': 'T', 'TR0': 'T', 'TR1': 'T', 'W': 'H', 'CT': 'C'}
    for x, ref in shallow_ref.items():
        assert F.manifest(caches[x], types, shallow) == F.manifest(caches[ref], types, shallow), ('V hook reached shallow', x)
    other = {x: ST2.other_state(caches[x])['sha256'] for x in FORMS}
    assert len(set(other.values())) == 1, other
    gates['formation'] = ('V replaced only in the V slice of the 14 deep linear layers, q/k untouched, applied == donor; '
                          'donor bands unchanged; layer-0 output equals T (needle) or C; shallow layers equal the '
                          'reference formation; management state equal; B source check every step')
    if a5 is not None:
        for x, name in (('C', 'C'), ('T', 'T'), ('H', 'XB')):
            want = {**a5['shallow_manifest'][name], **a5['deep_manifest'][name]}
            assert F.manifest(caches[x], types) == want, ('A5 replay manifest', x)
        gates['a5_replay_formation'] = 'C, T, H full cache manifests bitwise equal A5 C, T, XB; B donors equal A5'

    # ---- CPU reconstruction diagnostic (not a stop gate)
    recon = {}
    for x in FORMS:
        keys = [(x, t) for t in window]
        worst_state, worst_core = 0.0, 0.0
        for i in G:
            S, wc = reconstruct(s_b[i].cpu(), rows, keys, i)
            ref = L._get(caches[x].layers[i], 'recurrent_states')[0].double().cpu()
            worst_state = max(worst_state, float((S - ref).norm() / max(float(ref.norm()), 1e-8)))
            worst_core = max(worst_core, wc)
        recon[x] = {'state_rel_max': worst_state, 'core_rel_max': worst_core,
                    'passed': worst_state <= RECON_TOL['state_rel'] and worst_core <= RECON_TOL['core_rel']}
    old_new = {x: {str(i): [{'t': t, 'old_norm': float(rows[(x, t)][i]['old'].norm()),
                             'new_norm': float(rows[(x, t)][i]['new'].norm()),
                             'core_norm': float(rows[(x, t)][i]['core'].float().norm()),
                             'sum_vs_core_rel': float((rows[(x, t)][i]['old'] + rows[(x, t)][i]['new'] - rows[(x, t)][i]['core'].float()).norm()
                                                      / max(float(rows[(x, t)][i]['core'].float().norm()), 1e-8))}
                            for t in window] for i in G} for x in FORMS}

    # ---- scoring
    hyb = {'C': caches['C'], 'T_native': caches['T']}
    for x in ('T', 'H', 'U', 'W', 'TC', 'CT', 'TR0', 'TR1'):
        hy = E2.transplant(caches[x], caches['C'], shallow, types)
        assert F.manifest(hy, types, shallow) == F.manifest(caches['C'], types, shallow)
        assert F.manifest(hy, types, deep) == F.manifest(caches[x], types, deep)
        hyb[f'Y_{x}'] = hy
    for name, (a, s) in J_DEF.items():
        j = copy.deepcopy(hyb[f'Y_{a}'])
        for i in G:
            L._set(j.layers[i], 'recurrent_states', L._get(caches[s].layers[i], 'recurrent_states').clone())
        mj, ma, ms = F.manifest(j, types), F.manifest(hyb[f'Y_{a}'], types), F.manifest(caches[s], types)
        for key, h in mj.items():
            layer, field = key.split(':')
            want = ms[key] if (int(layer) in G and field == 'recurrent_states') else ma[key]
            assert h == want, ('J field source', name, key)
        assert ST2.other_state(j)['sha256'] == other['C']
        hyb[name] = j
    scores, logits = {}, {}
    with rec:
        for name in SCORES:
            scores[name], logits[name] = score(engine, hyb[name], last, n_prompt, rec, name, token_set, expected_hooks)
            scores[name]['score_state_sha256'] = exp.digest(F.manifest(hyb[name], types))
            counts['scores'] += 1
    for name in SCORES:
        assert scores[name]['final_norm']['normed_bitwise'], ('final norm implementation differs', name)
    r_c = scores['C']['final_norm']['r']
    for name in SCORES:
        ratio = scores[name]['final_norm']['r'] / r_c
        scores[name]['final_norm']['r_over_rC'] = ratio
        scores[name]['entropy_fix_scale'] = entropy(logits[name] * ratio)   # includes BF16 rounding (plan r3 §5.1)
    seen = {}
    for name in SCORES:
        k = scores[name]['score_state_sha256']
        if k in seen:
            assert scores[name]['logits_sha256'] == scores[seen[k]]['logits_sha256'], ('same state, different logits', name)
        seen.setdefault(k, name)
    gates['scoring'] = ('hybrid shallow == C, deep == own formation; J changes only the 14 recurrent_states; only the '
                        'read-only recorder installed; final norm recomputed bitwise; equal states give equal logits')
    if a5 is not None:
        for mine, theirs in (('C', 'C'), ('T_native', 'T_native'), ('Y_T', 'X0'), ('Y_H', 'XB')):
            assert scores[mine]['logits_sha256'] == a5['scores'][theirs]['logits_sha256'], ('A5 replay score', mine)
        gates['a5_replay_scores'] = 'C, T_native, Y_T, Y_H first-step logits bitwise equal A5 C, T_native, X0, XB'
    # centered-direction distances for the fixed comparison list
    cu = {name: centered_unit(logits[name]) for name in SCORES}
    pairs = {}
    for a, bb in COMPARISONS:
        ua, ub = cu[a], cu[bb]
        pairs[f'{a}|{bb}'] = {'u_dist': None if ua is None or ub is None else float((ua - ub).norm())}

    body = {'b': b, 'window': [window[0], window[-1]], 'n_window': len(window), 'G': list(G),
            'scores': scores, 'pairs': pairs, 'token_set': sorted(token_set),
            'reconstruction': recon, 'old_new_terms': old_new, 'random_band_norms': rb,
            'deep_manifest': {x: F.manifest(caches[x], types, deep) for x in FORMS},
            'shallow_manifest': {x: F.manifest(caches[x], types, shallow) for x in FORMS},
            'donor_band_hashes': bands_hash, 'c_snapshot_hashes': c_snap_hashes,
            'counts': counts, 'gates': gates}

    if preflight_extras:
        # (1) recorder-off replay of C, T, H and their four scores, (2) self-V, (3) self-S
        off = formation(PASS1, {}, None, record=False)
        for x in PASS1:
            assert F.manifest(off[0][x], types) == F.manifest(caches[x], types), ('recorder-off manifest', x)
        hy_off = {'C': off[0]['C'], 'T_native': off[0]['T'],
                  'Y_T': E2.transplant(off[0]['T'], off[0]['C'], shallow, types),
                  'Y_H': E2.transplant(off[0]['H'], off[0]['C'], shallow, types)}
        for name, hy in hy_off.items():
            r, _ = F.score(engine, hy, last, n_prompt, keep_logits=False)
            counts['scores'] += 1
            assert r['logits_sha256'] == scores[name]['logits_sha256'], ('recorder-off score', name)
        selfb = {'T': nat['T'], 'H': nat['H']}
        self_spec = {'ST': (True, False, 'T'), 'SH': (True, True, 'H')}
        cs = {}
        for x in ('T', 'H'):
            res = formation(('S' + x,), selfb, c_snaps, record=False, spec=self_spec)
            cs[x] = res[0]['S' + x]
            assert F.manifest(cs[x], types) == F.manifest(caches[x], types), ('self-V replacement not inert', x)
            r, _ = F.score(engine, E2.transplant(cs[x], caches['C'], shallow, types), last, n_prompt, keep_logits=False)
            counts['scores'] += 1
            assert r['logits_sha256'] == scores[f'Y_{x}']['logits_sha256'], ('self-V score', x)
        for x in ('T', 'H'):
            j = copy.deepcopy(hyb[f'Y_{x}'])
            for i in G:
                L._set(j.layers[i], 'recurrent_states', L._get(caches[x].layers[i], 'recurrent_states').clone())
            r, _ = F.score(engine, j, last, n_prompt, keep_logits=False)
            counts['scores'] += 1
            assert r['logits_sha256'] == scores[f'Y_{x}']['logits_sha256'], ('self-S J not inert', x)
        gates['preflight_inert'] = 'recorder-off C/T/H + 4 scores bitwise; self-V T/H bitwise; self-S J T/H bitwise'

    tensors = None
    if keep_tensors:
        tensors = {'positions': window, 's_b': to_cpu(s_b), 'logits': logits,
                   'v_natural': to_cpu(nat), 'v_applied': to_cpu(app), 'bands': to_cpu(bands),
                   'drivers': {f'{x}|{t}': to_cpu(rows[(x, t)]) for x in FORMS for t in window},
                   'score_drivers': {name: to_cpu(rec.rows.get(name, {})) for name in SCORES},
                   'score_extras': {name: to_cpu(rec.extra.get(name, {})) for name in SCORES},
                   'deep': {x: {f'{i}:{f}': L._get(caches[x].layers[i], f).detach().cpu()
                                for i, _, f in L.component_tensors(caches[x], types) if i in set(deep)} for x in FORMS},
                   'c_shallow': {f'{i}:{f}': L._get(caches['C'].layers[i], f).detach().cpu()
                                 for i, _, f in L.component_tensors(caches['C'], types) if i in set(shallow)}}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

def fab_records():
    """A5 (CFM-FORM-AB v2 formal-r01) records by item id."""
    return {p.stem: p for w in sorted(FAB_FORMAL.glob('worker-*')) if w.is_dir() for p in sorted((w / 'records').glob('*.json'))}


def frozen_paths():
    recs = fab_records()
    own = sorted(HERE.glob('*.py')) + [HERE / 'CONTRACT.zh-CN.md', PLAN_DOC, TOKENS, FAB_DIR / 'freeze-r01.json'] \
        + [recs[r['id']] for r in items()]
    return own + [p for p in F.frozen_paths() if p not in own]


def freeze(path):
    value = {'experiment': HERE.name, 'plan_id': PLAN_ID, 'created_at': exp.utc(),
             'files': {str(p.relative_to(REPO)): exp.sha(p) for p in frozen_paths()}}
    exp.write(path, value, immutable=True)
    return {'path': str(path), 'sha256': exp.sha(path), 'files': len(value['files'])}


def check_freeze(path):
    value = exp.read(path)
    actual = {str(p.relative_to(REPO)): exp.sha(p) for p in frozen_paths()}
    assert value['files'] == actual, 'Frozen source changed'
    return exp.sha(path)


def authorize(path, stage):
    auth = exp.read(path)
    assert auth['status'] == 'authorized' and auth['experiment'] == HERE.name and auth['plan_id'] == PLAN_ID
    assert auth['user_instruction'] and stage in auth['allowed_stages'] and auth['maximum_workers'] == MAX_WORKERS[stage]
    assert exp.sha(HERE / auth['freeze_path']) == auth['freeze_sha256']
    check_freeze(HERE / auth['freeze_path'])
    for rel, digest in auth['required_evidence'].items():
        assert exp.sha(HERE / rel) == digest, rel
    cpu = exp.read(HERE / auth['cpu_receipt_path'])
    assert auth['cpu_receipt_path'] in auth['required_evidence']
    assert cpu['status'] == 'passed' and cpu['failures'] == cpu['errors'] == 0 and cpu['tests_run'] > 0
    for name, digest in cpu['source_hashes'].items():
        assert exp.sha(REPO / name) == digest, name
    if stage == 'formal':
        rel = auth['preflight_verification_path']
        assert rel in auth['required_evidence']
        pre = exp.read(HERE / rel)
        assert pre['status'] == 'passed' and pre['freeze_sha256'] == auth['freeze_sha256'] and pre['stage'] == 'preflight'
    return auth


def plan(stage, worker, n_workers):
    return F.plan(stage, worker, n_workers)


def check_limits(counts, stage):
    lim = LIMITS[stage]
    assert counts['prefixes'] <= lim['prefixes'] and counts['scores'] <= lim['scores'], (counts, lim)


def dir_bytes(path):
    return sum(p.stat().st_size for p in Path(path).rglob('*') if p.is_file())


def execute(engine, stage, output, receipt, units):
    from control_engine import encode_text
    ref = exp.read(REFERENCE)
    seg = exp.read(F.SEGMENTS)['items']
    tok = exp.read(TOKENS)
    rows = {r['id']: r for r in items()}
    contexts = exp.contexts_for(engine.tokenizer, list(rows.values()))
    receipt['kernel_identity'] = T1.kernel_identity()
    recs = fab_records()
    calib = {}
    totals = {'prefixes': 0, 'scores': 0}
    count = 0
    for u in units:
        item = rows[u['item_id']]
        rid = item['reference_id']
        if rid not in calib:
            calib[rid] = engine.calibrate([contexts[rid]])[0]
            assert calib[rid] == ref['calibrations'][rid], 'calibration differs from II-B'
            exp.write(output / f'calibrations/{rid}.json', calib[rid], immutable=True)
        prompt = encode_text(engine.tokenizer, contexts[item['id']])
        labels = seg[item['id']]['labels']
        assert exp.digest(prompt) == seg[item['id']]['prompt_token_sha256'] and len(labels) == len(prompt)
        a5 = exp.read(recs[item['id']])
        assert a5['prompt_token_sha256'] == exp.digest(prompt)
        assert tok['items'][item['id']]['a5_record_sha256'] == exp.sha(recs[item['id']])
        token_set = list(tok['stop_ids']) + list(tok['items'][item['id']]['nonstop'])
        started = time.monotonic()
        body, tensors = run_item(engine, calib[rid], prompt, labels, item['id'], token_set, a5=a5,
                                 preflight_extras=(stage == 'preflight'))
        for k in totals:
            totals[k] += body['counts'][k]
        check_limits(totals, stage)
        tpath = output / f'tensors/{u["key"]}.pt'
        receipt['tensor_hashes'][str(tpath.relative_to(output))] = T1.save_tensors(tpath, tensors)
        del tensors
        rec = {'schema': 1, 'experiment': HERE.name, 'plan_id': PLAN_ID, 'stage': stage, 'unit': u, 'item': item,
               'prompt_token_sha256': exp.digest(prompt), 'a5_record': str(recs[item['id']].relative_to(REPO)), **body,
               'seconds': time.monotonic() - started, 'freeze_sha256': receipt['freeze_sha256'], 'created_at': exp.utc()}
        L._store(output, receipt, f'records/{u["key"]}.json', rec)
        assert dir_bytes(output) <= STORAGE_LIMIT // MAX_WORKERS['formal'], 'storage budget exceeded'
        count += 1
    receipt['model_calls'] = totals
    receipt['bytes'] = dir_bytes(output)
    if stage == 'preflight':
        exp.write(output / 'preflight.json', {'status': 'passed', 'units': [u['key'] for u in units], 'model_calls': totals}, immutable=True)
    return {'units': count, 'model_calls': totals}


def run(stage, worker, output, authorization):
    auth = authorize(authorization, stage)
    n_workers, gpu = auth['maximum_workers'], worker % 2
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root'] / f'worker-{worker}').resolve()
    import fcntl
    lock = open(f'/tmp/acupuncture-cfm-bridge-worker{worker}.lock', 'w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    free_mib = int(subprocess.check_output(['nvidia-smi', f'--id={gpu}', '--query-gpu=memory.free', '--format=csv,noheader,nounits'], text=True).strip())
    assert free_mib >= T1.MIN_FREE_MIB, f'Only {free_mib} MiB free on GPU {gpu}'
    output.mkdir(parents=True, exist_ok=False)
    receipt = {'status': 'running', 'stage': stage, 'worker': worker, 'n_workers': n_workers, 'gpu': gpu, 'pid': os.getpid(),
               'started_at': exp.utc(), 'freeze_path': auth['freeze_path'], 'freeze_sha256': auth['freeze_sha256'],
               'authorization_sha256': exp.sha(authorization), 'record_hashes': {}, 'tensor_hashes': {}, 'gpu_free_mib_at_start': free_mib}
    exp.write(output / 'execution.json', dict(receipt), immutable=True)
    exp.write(output / 'authorization.json', auth, immutable=True)
    exp.write(output / 'receipt.json', receipt)
    started = time.monotonic()
    sys.path.insert(0, str(T1.SOURCE))
    from control_engine import ControlEngine
    try:
        source = exp.read(T1.SOURCE / 'contract.json')['source']
        receipt['asset_identity'] = exp.model_assets()
        engine = ControlEngine(source['model_path'], exp.model_spec(), f'cuda:{gpu}')
        exp.metadata_check(engine)
        exp.write(output / 'metadata.json', engine.metadata, immutable=True)
        units = plan(stage, worker, n_workers)
        exp.write(output / 'plan.json', units, immutable=True)
        receipt['summary'] = execute(engine, stage, output, receipt, units)
        receipt['integrity'] = engine.verify_unchanged()
        receipt['status'] = 'completed'
    except BaseException:
        receipt.update(status='failed', error=traceback.format_exc())
        raise
    finally:
        receipt.update(finished_at=exp.utc(), wall_seconds=time.monotonic() - started)
        exp.write(output / 'receipt.json', receipt)
    return receipt


def verify_worker(path):
    path = Path(path)
    r = exp.read(path / 'receipt.json')
    assert r['status'] == 'completed'
    assert r['freeze_sha256'] == exp.sha(HERE / r['freeze_path'])
    check_freeze(HERE / r['freeze_path'])
    assert r['authorization_sha256'] == exp.sha(path / 'authorization.json')
    units = exp.read(path / 'plan.json')
    assert units == plan(r['stage'], r['worker'], r['n_workers'])
    expected = {f'records/{u["key"]}.json' for u in units}
    assert set(r['record_hashes']) == expected
    assert set(r['tensor_hashes']) == {f'tensors/{u["key"]}.pt' for u in units}
    for rel, digest in r['tensor_hashes'].items():
        assert exp.sha(path / rel) == digest, rel
    for rel, digest in r['record_hashes'].items():
        assert exp.sha(path / rel) == digest, rel
        rec = exp.read(path / rel)
        assert set(rec['scores']) == set(SCORES)
        for g in ('formation', 'a5_replay_formation', 'scoring', 'a5_replay_scores'):
            assert rec['gates'][g], g
        if r['stage'] == 'preflight':
            assert rec['gates']['preflight_inert']
    check_limits(r['model_calls'], r['stage'])
    assert r['integrity']['hooks_removed'] is True
    assert r['integrity']['target_weight_sha256_after'] == exp.read(path / 'metadata.json')['target_weight_sha256_before']
    assert exp.read(path / 'exit.json')['returncode'] == 0
    if r['stage'] == 'preflight':
        assert exp.read(path / 'preflight.json')['status'] == 'passed'
    return {'status': 'passed', 'stage': r['stage'], 'units': len(expected), 'freeze_sha256': r['freeze_sha256'],
            'wall_seconds': r['wall_seconds'], 'model_calls': r['model_calls'], 'bytes': r['bytes']}


def launch(stage, authorization, output):
    auth = authorize(authorization, stage)
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root']).resolve()
    output.mkdir(parents=True, exist_ok=False)
    controller = {'status': 'running', 'pid': os.getpid(), 'stage': stage, 'started_at': exp.utc(),
                  'authorization_sha256': exp.sha(authorization), 'freeze_sha256': auth['freeze_sha256'], 'workers': {}}
    exp.write(output / 'execution.json', dict(controller), immutable=True)
    procs, logs, started = {}, [], time.monotonic()
    try:
        for w in range(auth['maximum_workers']):
            log = (output / f'worker-{w}.log').open('x')
            logs.append(log)
            cmd = [sys.executable, '-u', str(HERE / 'bridge.py'), 'run', '--stage', stage, '--worker', str(w),
                   '--authorization', str(Path(authorization).resolve()), '--output', str(output / f'worker-{w}')]
            procs[w] = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
            controller['workers'][str(w)] = {'pid': procs[w].pid, 'command': cmd}
        exp.write(output / 'controller.json', controller)
        pending, failure = dict(procs), False
        while pending:
            for w, p in list(pending.items()):
                code = p.poll()
                if code is None:
                    continue
                (output / f'worker-{w}').mkdir(exist_ok=True)
                exp.write(output / f'worker-{w}/exit.json', {'returncode': code, 'finished_at': exp.utc()}, immutable=True)
                controller['workers'][str(w)]['returncode'] = code
                failure |= code != 0
                del pending[w]
            exp.write(output / 'controller.json', controller)
            if failure:
                for p in pending.values():
                    p.terminate()
            if pending:
                time.sleep(3)
        assert not failure, 'A worker failed; partial evidence preserved'
        results = [verify_worker(output / f'worker-{w}') for w in range(auth['maximum_workers'])]
        units = sum(x['units'] for x in results)
        calls = {k: sum(x['model_calls'][k] for x in results) for k in ('prefixes', 'scores')}
        check_limits(calls, stage)
        if stage == 'formal':
            assert units == 12, units
        exp.write(output / 'verification.json', {'status': 'passed', 'stage': stage, 'freeze_sha256': auth['freeze_sha256'],
                  'workers': results, 'units': units, 'model_calls': calls, 'verified_at': exp.utc()}, immutable=True)
        controller['status'] = 'completed'
    except BaseException as error:
        controller.update(status='failed', error=repr(error))
        for w, p in procs.items():
            if p.poll() is None:
                p.terminate()
                p.wait()
        raise
    finally:
        for log in logs:
            log.close()
        controller.update(finished_at=exp.utc(), wall_seconds=time.monotonic() - started)
        exp.write(output / 'controller.json', controller)
    return controller


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('freeze').add_argument('path')
    sub.add_parser('verify').add_argument('path')
    for name in ('run', 'launch'):
        q = sub.add_parser(name)
        q.add_argument('--stage', required=True, choices=STAGES)
        q.add_argument('--authorization', required=True)
        q.add_argument('--output', required=True)
        if name == 'run':
            q.add_argument('--worker', required=True, type=int, choices=range(2))
    a = p.parse_args()
    sys.path.insert(0, str(T1.SOURCE))
    if a.cmd == 'freeze':
        value = freeze(a.path)
    elif a.cmd == 'verify':
        value = verify_worker(a.path)
    elif a.cmd == 'run':
        value = run(a.stage, a.worker, a.output, a.authorization)
        value = {k: v for k, v in value.items() if k not in ('record_hashes', 'tensor_hashes')}
    else:
        value = launch(a.stage, a.authorization, a.output)
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    main()
