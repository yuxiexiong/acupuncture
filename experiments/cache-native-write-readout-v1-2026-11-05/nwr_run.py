"""NWR-01 r02 (CONTRACT-r02; Proposal v8 §4 main comparison A): does the recurrent state written by the NATIVE t1 write, S1(L00), used through the t2
direct read D in the already-open receiver L11, re-create substantive errors -- beyond the other use (E), beyond output-norm-matched random
patches, and as explicit wrong numbers rather than stops?   Direction N4146 only; LVK new panel (48 seen development inputs).
Arms (12 natural trajectories per input): C, L00, L10, L11 (references, bridged to LVK); receiver L11 at t2 in the 14 G layers only:
  D00: o2 += alpha (S1[L00] - S_r)^T q          E00: o2 += -alpha beta (k^T q) (S1[L00] - S_r)^T k          D10: the SRU withdraw cell (bridged)
  R1..R5: o2 += u_j * |alpha (S1[L00] - S_r)^T q|   per layer and head, u_j a fixed unit direction (seed, layer); nothing injected where the norm is 0.
q/k/v/alpha/beta are the receiver's own; the stored S2 is the receiver's native update; t3 onward no hook.
Also records, at t1, the kernel inputs of every G layer for L00 and for 'original kernel fed the shadow v' (== L10 bit for bit): first G layer must
agree in q, k, g, beta, S0 and differ only in v; S0 must agree in every G layer.
python nwr_run.py freeze PATH | run ... | verify WORKER_DIR | launch ..."""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
SRU_DIR = HERE.parent / 'cache-state-read-use-v1-2026-11-03'
sys.path.insert(0, str(SRU_DIR))
sys.path.insert(0, str(HERE))
import sru_run as S  # noqa: E402  (frozen SRU-01 runner; brings the frozen LVK-01 runner)
from sru_run import *  # noqa: E402,F401,F403

HERE = Path(__file__).resolve().parent
LVKR = S.LVKR
SRU_FORMAL = SRU_DIR / 'runs/formal-r01'
PLAN_ID = 'NWR-01-NATIVE-WRITE-READOUT-r02'
DIR = 'N_L00_C4146_D-1'
SEEDS = (202611051, 202611052, 202611053, 202611054, 202611055)
RAND = tuple(f'R{j}' for j in range(1, 6))
ARMS = ('C', 'L00', 'L10', 'L11', 'D00', 'E00', 'D10') + RAND
T2_ARMS = {'D00': ('cell', 1, 0, 'L00'), 'E00': ('cell', 0, 1, 'L00'), 'D10': ('cell', 1, 0, 'L10')}
SFIELDS = ('q', 'k', 'g', 'beta', 'S0', 'v')
NORM_TOL = 1e-5
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
PREFLIGHT_ITEMS = LVKR.NEW_PRE
_PER = {'t1': 4, 'refs': 3, 'c_t2': 9, 'trajectories': 12, 'shadow': 56}


def _lim(n, formation_tokens):
    return {'formations': 2 * n, 'prefix_prefills': n, 'formation_token_forwards': formation_tokens, 't1': _PER['t1'] * n, 'refs': _PER['refs'] * n,
            'n_steps': _PER['trajectories'] * 31 * n, 'c_t2': _PER['c_t2'] * n,
            'decode_forwards': (_PER['t1'] + _PER['refs'] + _PER['c_t2'] + _PER['trajectories'] * 31) * n,
            'trajectories': _PER['trajectories'] * n, 'shadow': _PER['shadow'] * n, 'calibrations': 0}


LIMITS = {'preflight': _lim(2, 108), 'formal': _lim(48, 2556)}
GPU_CAP_S = {'preflight': 0.15 * 3600, 'formal': 1.2 * 3600}
STORAGE_LIMIT = 8 * 2 ** 30


def conditions():
    c = LVKR.conditions()
    return {DIR: c[DIR]}


def sru_records():
    out = {}
    for w in sorted(SRU_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        for rel, dg in r['record_hashes'].items():
            assert exp.sha(w / rel) == dg, 'SRU record hash'
            rec = exp.read(w / rel)
            assert exp.sha(w / rec['tensor_file']) == r['tensor_hashes'][rec['tensor_file']], 'SRU tensor hash'
            rec['_tensor_path'] = str(w / rec['tensor_file'])
            out[rec['text']] = rec
    return out


def unit_dir(seed, layer, shape):
    """Fixed unit direction per (seed, layer): rows of unit L2 norm, float32, CPU generator."""
    import torch
    g = torch.Generator().manual_seed(seed * 100 + layer)
    u = torch.randn(*shape, generator=g, dtype=torch.float64)
    return (u / u.norm(dim=-1, keepdim=True)).float()


def read_use_rand(query, key, value, g, beta, S_r, S_d, unit, l2norm):
    """S.read_use order with, at the output only, a vector along `unit` whose per-head L2 norm equals that of the direct-read patch
    Dc = alpha (S_d - S_r)^T q, added in FP32 before the cast.  Returns (out cast, native S2, pre-cast out, stats [H, 3] = |Dc|, |R|, cos, norm error)."""
    import torch
    initial_dtype = query.dtype
    q, k, v, bt, dc = [x.transpose(1, 2).to(torch.float32, memory_format=torch.contiguous_format) for x in (query, key, value, beta, g)]
    q = l2norm(q, dim=-1, eps=1e-6)
    k = l2norm(k, dim=-1, eps=1e-6)
    q = q / (q.shape[-1] ** 0.5)
    S = S_r.to(v)
    out = torch.zeros_like(v)
    q_t, k_t, v_t = q[:, :, 0], k[:, :, 0], v[:, :, 0]
    decay_t = dc[:, :, 0].exp()[..., None, None]
    S = S * decay_t
    beta_t = bt[:, :, 0].unsqueeze(-1)
    kv_mem = (S * k_t.unsqueeze(-1)).sum(dim=-2)
    delta = (v_t - kv_mem) * beta_t
    S = S + k_t.unsqueeze(-1) * delta.unsqueeze(-2)
    o_t = (S * q_t.unsqueeze(-1)).sum(dim=-2)
    dS = S_d.to(v) - S_r.to(v)
    al = decay_t[..., 0, 0].unsqueeze(-1)
    Dc = al * (dS * q_t.unsqueeze(-1)).sum(dim=-2)
    nD = Dc.norm(dim=-1, keepdim=True)
    R = unit.to(Dc) * nD
    nR = R.norm(dim=-1, keepdim=True)
    nz = nD[..., 0] > 0
    err = float(((nR - nD).abs()[..., 0][nz] / nD[..., 0][nz]).max()) if bool(nz.any()) else 0.0
    if bool(nz.any()):
        o_t = o_t + R
    cos = (Dc * R).sum(-1) / torch.clamp(nD[..., 0] * nR[..., 0], min=1e-30)
    stats = torch.stack([nD[0, :, 0], nR[0, :, 0], cos[0]], -1).float().cpu()
    out[:, :, 0] = o_t
    pre = out.clone()
    out = out.transpose(1, 2).contiguous().to(initial_dtype)
    return out, S, pre, stats, err


class XHook:
    """One t2 forward in the 14 G layers.  kind 'cell' (a, b, donor S1) delegates to the frozen S.read_use; kind 'rand' (donor S1, seed) uses
    read_use_rand with the fixed unit direction of (seed, layer)."""

    def __init__(self, model, G, kind, Sd, a=0, b=0, seed=None):
        assert kind in ('cell', 'rand') and (kind == 'cell' or seed is not None)
        self.model, self.G, self.kind, self.a, self.b, self.Sd, self.seed = model, tuple(G), kind, a, b, Sd, seed
        self.QM = gdn_module()
        self.orig = self.QM.torch_recurrent_gated_delta_rule
        self.layer, self.handles, self.calls, self.oracle, self.stats, self.nerr = None, [], [], {}, {}, {}

    def __enter__(self):
        assert self.QM.torch_recurrent_gated_delta_rule is self.orig
        for i, lay in enumerate(L.model_layers(self.model)):
            la = getattr(lay, 'linear_attn', None)
            if la is not None:
                def pre(_m, _a, i=i):
                    self.layer = i
                self.handles.append(la.register_forward_pre_hook(pre))
        me = self

        def kern(query, key, value, g=None, beta=None, initial_state=None, output_final_state=False, use_qk_l2norm_in_kernel=False, **kw):
            if me.layer not in me.G:
                return me.orig(query, key, value, g=g, beta=beta, initial_state=initial_state, output_final_state=output_final_state,
                               use_qk_l2norm_in_kernel=use_qk_l2norm_in_kernel, **kw)
            assert query.shape[1] == 1 and use_qk_l2norm_in_kernel and output_final_state
            me.calls.append(me.layer)
            Sd = me.Sd[me.layer]
            assert Sd.shape == initial_state.shape and Sd.dtype == initial_state.dtype
            if me.kind == 'cell':
                out, S2, _, st, err = S.read_use(query, key, value, g, beta, initial_state, Sd, me.a, me.b, me.QM.l2norm, oracle=bool(me.a or me.b))
                if st is not None:
                    me.stats[me.layer], me.oracle[me.layer] = st, err
            else:
                u = unit_dir(me.seed, me.layer, (value.shape[0], value.shape[2], value.shape[3]))
                out, S2, _, st, err = read_use_rand(query, key, value, g, beta, initial_state, Sd, u, me.QM.l2norm)
                me.stats[me.layer], me.nerr[me.layer] = st, err
            return out, S2
        self.QM.torch_recurrent_gated_delta_rule = kern
        return self

    def __exit__(self, *exc):
        self.QM.torch_recurrent_gated_delta_rule = self.orig
        for h in self.handles:
            h.remove()
        self.handles = []
        return False

    def check(self):
        assert sorted(self.calls) == sorted(self.G), ('t2 hook calls', self.calls)
        if self.kind == 'cell' and (self.a or self.b):
            assert set(self.oracle) == set(self.G) and max(self.oracle.values()) <= S.ORACLE_TOL, ('FP64 oracle', max(self.oracle.values()))
        if self.kind == 'rand':
            assert set(self.nerr) == set(self.G) and max(self.nerr.values()) <= NORM_TOL, ('random patch norm', max(self.nerr.values()))


class CapHook:
    """Records (CPU clones) the kernel inputs of every G layer in one forward and passes through to the function installed at construction."""
    mode = 'noop'

    def __init__(self, model, G):
        self.model, self.G = model, tuple(G)
        self.QM = gdn_module()
        self.orig = self.QM.torch_recurrent_gated_delta_rule
        self.layer, self.handles, self.calls, self.args, self.conv_calls = None, [], [], {}, []

    def __enter__(self):
        assert self.QM.torch_recurrent_gated_delta_rule is self.orig
        for i, lay in enumerate(L.model_layers(self.model)):
            la = getattr(lay, 'linear_attn', None)
            if la is not None:
                def pre(_m, _a, i=i):
                    self.layer = i
                self.handles.append(la.register_forward_pre_hook(pre))
        me = self

        def kern(query, key, value, g=None, beta=None, initial_state=None, output_final_state=False, use_qk_l2norm_in_kernel=False, **kw):
            if me.layer in me.G:
                me.calls.append(me.layer)
                me.args[me.layer] = {nm: x.detach().to('cpu').clone() for nm, x in zip(SFIELDS, (query, key, g, beta, initial_state, value))}
            return me.orig(query, key, value, g=g, beta=beta, initial_state=initial_state, output_final_state=output_final_state,
                           use_qk_l2norm_in_kernel=use_qk_l2norm_in_kernel, **kw)
        self.QM.torch_recurrent_gated_delta_rule = kern
        return self

    def __exit__(self, *exc):
        self.QM.torch_recurrent_gated_delta_rule = self.orig
        for h in self.handles:
            h.remove()
        self.handles = []
        return False

    def check(self):
        assert sorted(self.calls) == sorted(self.G), ('capture calls', self.calls)


def struct_compare(a, b, G):
    """Per G layer: bitwise equality of each kernel input between two captures, plus the relative size of the v difference."""
    import torch
    out = {}
    for l in G:
        row = {nm: bool(torch.equal(a[l][nm], b[l][nm])) for nm in SFIELDS}
        va, vb = a[l]['v'].float(), b[l]['v'].float()
        row['v_rel_diff'] = float((vb - va).norm() / max(float(va.norm()), 1e-30))
        out[str(l)] = row
    return out


def struct_ok(s, G):
    f = s[str(G[0])]
    return bool(f['q'] and f['k'] and f['g'] and f['beta'] and f['S0'] and not f['v'] and all(s[str(l)]['S0'] for l in G))


def run_item(engine, unit, contexts, calib, conds, qctok, output, stage, vecs=None, refs=None):
    import torch
    model, tok = engine.model, engine.tokenizer
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
    assert tuple(G) == (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30) and G[0] == LAYER0
    assert tuple(STOP) == tuple(CFK.STOP) == tuple(engine.stop_ids)
    assert list(conds) == [DIR]
    QM = gdn_module()
    KRDR.QHOOK_ORIG[0] = QM.torch_recurrent_gated_delta_rule
    a_id, d = unit['item_id'], DIR
    assert unit['panel'] == 'new'
    counts = {k: 0 for k in COUNT_KEYS}
    tensors, gates, arms = {}, {}, {}
    nz_total, oracle_max, nerr_max = 0, 0.0, 0.0
    led, lv, sr = refs['ledger'][a_id], refs['lvk'][a_id], refs['sru'][a_id]
    lv_t = torch.load(lv['_tensor_path'], map_location='cpu')
    sr_t = torch.load(sr['_tensor_path'], map_location='cpu')
    C, T, info = form_new(engine, led, contexts, calib, conds, counts)
    for hk_, hv in info['hashes'].items():
        assert lv['formation_hashes'][hk_] == hv, ('formation hash != LVK', hk_)
    hC, hT = comp_sha(C, types, ALLK, 0), comp_sha(T[d], types, ALLK, 0)
    it, code_tok, n = info['item'], info['code_tokens'], info['n']
    comp = it['first_listed'] if it['target'] != it['first_listed'] else it['listed_codes'][1]
    cconv = {l: L._get(C.layers[l], 'conv_states').clone() for l in G}
    dec = lambda ids: tok.decode(ids, skip_special_tokens=False)   # noqa: E731
    fF = led['tokens']['q_shared']
    lvd = lv['directions'][d]['arms']
    z2n = {}

    def ref_arm(name, c1_, z1_, lva):
        """Reference endpoint: natural trajectory from its own first token, bridged to LVK."""
        x_ = int(z1_.argmax())
        r, z2_ = natural(engine, copy.deepcopy(c1_), x_, n, counts)
        r['text'] = dec(r['ids'])
        assert x_ == lva['x'] and r['ids'] == lva['N']['ids'] and r['termination'] == lva['N']['termination'], ('natural != LVK', name)
        arms[name] = {'x': x_, 'N': r}
        z2n[name] = z2_
        return x_

    # ---- clean C
    cC, zC = t1(engine, copy.deepcopy(C), info['last'], n, counts, 't1')
    assert bit_equal(zC.to(torch.bfloat16).cpu(), lv_t['t1|C|all'])[0], 't1 C != LVK'
    ref_arm('C', cC, zC, lv['directions']['C_clean'])
    del cC
    # ---- endpoints on the native background T
    _, u, sign = ARMS_ALL['Rk']
    vec = QKFR.mask_vec(vecs[u][f"{info['scenario']}|{d}"].float(), 'k')
    bT, _ = QKFR.edited_arm(T[d], T[d], T[d], G, None, 1)
    check_bg(bT, T[d], C, types, G, 'T', 'T')
    hbT = comp_sha(bT, types, ALLK, 0)
    c1, z1, x, S1 = {}, {}, {}, {}
    cap0 = CapHook(model, G)
    c1['L00'], z1['L00'] = t1(engine, copy.deepcopy(bT), info['last'], n, counts, 't1', hook=cap0)
    for name, (aa, bb) in (('L10', (1, 0)), ('L11', (1, 1))):
        hk = LHook(model, G, 'cell', a=aa, b=bb, vec=vec, sign=sign, cconv=cconv)
        c1[name], z1[name] = t1L(engine, copy.deepcopy(bT), info['last'], n, counts, 't1', hk)
    for name in ('L00', 'L10', 'L11'):
        assert bit_equal(z1[name].to(torch.bfloat16).cpu(), lv_t[f't1|{name}|{d}'])[0], ('t1 != LVK', name)
        S1[name] = {l: L._get(c1[name].layers[l], 'recurrent_states').clone() for l in G}
        x[name] = ref_arm(name, c1[name], z1[name], lvd[name])
    h1 = {name: comp_sha(c1[name], types, ALLK, 0) for name in c1}
    # ---- t1 structure: L00 vs "original kernel fed the shadow v" (== L10 bit for bit)
    cap1 = CapHook(model, G)
    with cap1:
        hk = LHook(model, G, 'ref_v', cconv=cconv)
        with hk:
            with torch.inference_mode():
                o_ = L.forward(model, [info['last']], n - 1, copy.deepcopy(bT))
        hk.check()
    cap1.check()
    assert QM.torch_recurrent_gated_delta_rule is KRDR.QHOOK_ORIG[0], 'kernel wrapper left installed'
    F.assert_no_hooks(model)
    counts['decode_forwards'] += 1
    counts['refs'] += 1
    counts['shadow'] += hk.n_shadow
    zr = o_.logits[0, -1].float()
    okz, z0 = bit_equal(zr, z1['L10'])
    assert okz, 'structure reference != L10'
    nz_total += z0
    struct = struct_compare(cap0.args, cap1.args, G)
    assert struct_ok(struct, G), ('t1 structure', struct[str(G[0])])
    tensors['struct|v_rel_diff'] = torch.tensor([struct[str(l)]['v_rel_diff'] for l in G])
    del cap0, cap1, o_
    # ---- receiver L11 at t2
    xr, cr = x['L11'], c1['L11']
    reached = xr not in STOP

    def t2_arm(name, mk):
        nonlocal oracle_max, nerr_max
        hk_c = mk()
        _, zc = fwd(engine, copy.deepcopy(cr), fF, n, counts, 'c_t2', hook=hk_c)
        M, Mall = margins(zc, it, code_tok, comp)
        tensors[f'C|{name}'] = zc.to(torch.bfloat16).cpu()
        tensors[f'stats|C|{name}'] = torch.stack([hk_c.stats[l] for l in G])
        rec = {'C': {'M': M, 'M_all': Mall, 't2_sha': F.th(zc)}}
        hooks = [hk_c]
        if reached:
            hk_n = mk()
            nr, z2 = natural(engine, copy.deepcopy(cr), xr, n, counts, hook=hk_n)
            nr['text'] = dec(nr['ids'])
            nr['t2_token'] = nr['ids'][1]
            tensors[f'N|{name}'] = z2.to(torch.bfloat16)
            tensors[f'stats|N|{name}'] = torch.stack([hk_n.stats[l] for l in G])
            hooks.append(hk_n)
        else:
            nr = {'ids': [xr], 'termination': 'stop', 'reached_t2': False, 'text': dec([xr])}
        for h in hooks:
            if h.oracle:
                oracle_max = max(oracle_max, max(h.oracle.values()))
            if h.nerr:
                nerr_max = max(nerr_max, max(h.nerr.values()))
        rec['N'] = nr
        arms[name] = rec
        return zc

    # 00: native t2 (C route bridged to LVK) and the replicated-order hook with a = b = 0
    _, zc00 = fwd(engine, copy.deepcopy(cr), fF, n, counts, 'c_t2')
    assert bit_equal(zc00.to(torch.bfloat16).cpu(), lv_t[f'C|L11|{d}'])[0], '00 C t2 != LVK'
    M00, Mall00 = margins(zc00, it, code_tok, comp)
    arms['L11']['C'] = {'M': M00, 'M_all': Mall00, 't2_sha': F.th(zc00)}
    tensors['C|L11'] = zc00.to(torch.bfloat16).cpu()
    hr = XHook(model, G, 'cell', S1['L00'], a=0, b=0)
    _, zr = fwd(engine, copy.deepcopy(cr), fF, n, counts, 'refs', hook=hr)
    okz, z0 = bit_equal(zr, zc00)
    assert okz, 'replicated-order 00 hook != native t2 (C)'
    nz_total += z0
    if reached:
        hr = XHook(model, G, 'cell', S1['L00'], a=0, b=0)
        _, zr = fwd(engine, copy.deepcopy(cr), xr, n, counts, 'refs', hook=hr)
        okz, z0 = bit_equal(zr.detach().cpu(), z2n['L11'])
        assert okz, 'replicated-order 00 hook != native t2 (N)'
        nz_total += z0
    for name, (kind, aa, bb, donor) in T2_ARMS.items():
        zc = t2_arm(name, lambda aa=aa, bb=bb, donor=donor: XHook(model, G, 'cell', S1[donor], a=aa, b=bb))
        if name == 'D10':                        # bridge to the SRU withdraw cell 10
            sc = sr['directions'][d]['pairs']['withdraw']['10']
            assert bit_equal(zc.to(torch.bfloat16).cpu(), sr_t[f'C|withdraw|10|{d}'])[0], 'D10 C t2 != SRU'
            assert arms[name]['N']['ids'] == sc['N']['ids'] and arms[name]['N']['termination'] == sc['N']['termination'], 'D10 natural != SRU'
    for name, seed in zip(RAND, SEEDS):
        t2_arm(name, lambda seed=seed: XHook(model, G, 'rand', S1['L00'], seed=seed))
    for name in c1:
        assert comp_sha(c1[name], types, ALLK, 0) == h1[name], ('post-t1 source cache modified', name)
    assert comp_sha(bT, types, ALLK, 0) == hbT
    assert hC == comp_sha(C, types, ALLK, 0) and comp_sha(T[d], types, ALLK, 0) == hT, 'donor modified'
    F.assert_no_hooks(model)
    assert set(arms) == set(ARMS)
    gates['sources'] = 'formation hashes == LVK; C/L00/L10/L11 t1 bf16 logits, first token and natural tokens == LVK; post-t1 sources unchanged'
    gates['replay'] = 'L11 C t2 bf16 logits == LVK; replicated-order hook with a=b=0 == native t2 (C, N); D10 == SRU withdraw cell 10 (C t2 bf16, natural tokens)'
    gates['oracle'] = f'cells D00/E00/D10 local output vs FP64 formula, max relative error {oracle_max:.3g} <= {S.ORACLE_TOL}'
    gates['random'] = f'random patch L2 norm == |D patch| per layer and head, max relative error {nerr_max:.3g} <= {NORM_TOL}; nothing injected at zero norm'
    gates['structure'] = 't1 kernel inputs L00 vs L10: first G layer q/k/g/beta/S0 bit-equal and v different; S0 bit-equal in every G layer'
    gates['hooks'] = 't1 only LVK shadow / capture hooks; t2 hook fires once per G layer; t3 onward no hook; module functions restored'
    gates['calibration'] = 'NQ-01 saved scenario calibration (source hash in receipt)'
    body = {'text': a_id, 'panel': 'new', 'scenario': info['scenario'], 'item': it, 'code_tokens': code_tok, 'competitor': comp, 'direction': d,
            'fF': fF, 'x': x, 'reached_t2': reached, 'arms': arms, 'structure_t1': struct, 'target_second_token': code_tok[it['target']],
            'signed_zero_exceptions': nz_total, 'oracle_max': oracle_max, 'rand_norm_err_max': nerr_max, 'seeds': list(SEEDS),
            'kernel_identity': kernel_identity(), 'calibration': calib, 'counts': counts, 'gates': gates}
    del c1, S1, bT
    torch.cuda.empty_cache()
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + [HERE / 'CONTRACT-r02.zh-CN.md']
    sru = [SRU_DIR / 'sru_run.py', SRU_DIR / 'sru_core.py', SRU_DIR / 'freeze-r01.json', SRU_FORMAL / 'verification.json']
    sru += [w / 'receipt.json' for w in sorted(SRU_FORMAL.glob('worker-*')) if w.is_dir()]
    lvk = [LVK_DIR / 'lvk_run.py', LVK_DIR / 'freeze-r01.json', LVK_FORMAL / 'verification.json', HELDOUT, LEDGER]
    lvk += [w / 'receipt.json' for w in sorted(LVK_FORMAL.glob('worker-*')) if w.is_dir()]
    fc = [HERE.parent / 'cache-first-token-continuation-v1-2026-11-02/fc_core.py']
    return own + sru + lvk + fc


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
    assert cpu['status'] == 'passed' and cpu['failures'] == cpu['errors'] == 0 and cpu['tests_run'] > 0
    for name, digest in cpu['source_hashes'].items():
        assert exp.sha(REPO / name) == digest, name
    S.check_freeze(SRU_DIR / 'freeze-r01.json')            # the whole frozen SRU / LVK source tree is unchanged
    ki = kernel_identity()
    assert not ki['fla'] and not ki['kernels'] and not ki['causal_conv1d'], ('non-torch kernel available', ki)
    if stage == 'formal':
        pre = exp.read(HERE / auth['preflight_verification_path'])
        assert pre['status'] == 'passed' and pre['freeze_sha256'] == auth['freeze_sha256'] and pre['stage'] == 'preflight'
        ex = extrapolate(HERE / Path(auth['preflight_verification_path']).parent)
        assert ex['device_seconds'] <= GPU_CAP_S['formal'] and ex['bytes'] <= STORAGE_LIMIT, ('preflight extrapolation exceeds the formal cap', ex)
    return auth


def extrapolate(pre_root):
    """Formal estimate from the preflight worker: mean per-text seconds x 48 + per-worker model load x 2; bytes likewise."""
    ws = [w for w in sorted(Path(pre_root).glob('worker-*')) if w.is_dir()]
    assert len(ws) == 1
    r = exp.read(ws[0] / 'receipt.json')
    recs = [exp.read(ws[0] / rel) for rel in r['record_hashes']]
    load = r['wall_seconds'] - sum(x['seconds'] for x in recs)
    sec = sum(x['seconds'] for x in recs) / len(recs)
    by = sum((ws[0] / x['tensor_file']).stat().st_size for x in recs) / len(recs)
    return {'per_text_seconds': sec, 'load_seconds': load, 'device_seconds': 48 * sec + 2 * load, 'bytes': 48 * by, 'texts': 48}


def check_limits(counts, stage):
    lim = LIMITS[stage]
    assert all(counts[k] <= lim[k] for k in lim), (counts, lim)


def execute(engine, stage, output, receipt, units, gpu):
    qi = QCDR.qc_items()
    contexts = exp.contexts_for(engine.tokenizer, [qi[t['plan']['qc_broad_id']] for t in items()])
    contexts.update(exp.contexts_for(engine.tokenizer, [v['item'] for v in ledger().values()]))
    conds = conditions()
    receipt['kernel_identity'] = T1.kernel_identity()
    assert list(engine.stop_ids) == list(CFK.STOP)
    F.hook_baseline(engine.model)
    import torch
    totals = {k: 0 for k in COUNT_KEYS + ('calibrations',)}
    calib = {}
    qctok = exp.read(QC_TOKENS)
    vecs = load_vectors()
    refs = {'lvk': lvk_records(), 'sru': sru_records(), 'ledger': ledger()}
    thr = None
    import threading
    hb = {'totals': dict(totals), 'units_done': 0, 'stop': False}
    def beat():
        while not hb['stop']:
            try:
                exp.write(output / 'heartbeat.json', {'at': exp.utc(), 'pid': os.getpid(), 'units_done': hb['units_done'], 'units': len(units),
                                                     'model_calls': hb['totals'], 'device_seconds': time.monotonic() - gpu['t0'], 'bytes': B.dir_bytes(output)})
            except OSError:
                pass
            for _ in range(60):
                if hb['stop']:
                    break
                time.sleep(1)
    th = threading.Thread(target=beat, daemon=True)
    th.start()
    try:
        out = _execute_units(engine, stage, output, receipt, units, gpu, contexts, conds, totals, calib, qctok, vecs, refs, thr, hb, torch)
    finally:
        hb['stop'] = True
        th.join()
    return out


def _execute_units(engine, stage, output, receipt, units, gpu, contexts, conds, totals, calib, qctok, vecs, refs, thr, hb, torch):
    for u in units:
        started = time.monotonic()
        rid = f"{u['base_id']}-ABC-A"
        if rid not in calib:
            calib[rid], csha = QCR.nq_calibration(rid)
            receipt.setdefault('calibration_sources', {})[rid] = csha
        body, tensors = run_item(engine, u, contexts, calib[rid], conds, qctok, output, stage, vecs=vecs, refs=refs)
        for k in COUNT_KEYS:
            totals[k] += body['counts'][k]
        check_limits(totals, stage)
        rel_t = f'tensors/{u["key"]}.pt'
        (output / 'tensors').mkdir(exist_ok=True)
        assert not (output / rel_t).exists()
        torch.save(tensors, output / rel_t)
        receipt['tensor_hashes'][rel_t] = exp.sha(output / rel_t)
        body['tensor_file'] = rel_t
        item = {'id': u['item_id']}
        rec = {'schema': 1, 'experiment': HERE.name, 'plan_id': PLAN_ID, 'stage': stage, 'unit': u, 'item': item, **body,
               'seconds': time.monotonic() - started, 'freeze_sha256': receipt['freeze_sha256'], 'created_at': exp.utc()}
        L._store(output, receipt, f'records/{u["key"]}.json', rec)
        exp.write(output / 'receipt.json', receipt)
        assert B.dir_bytes(output) <= STORAGE_LIMIT // MAX_WORKERS['formal'], 'storage budget exceeded'
        hb['totals'], hb['units_done'] = dict(totals), hb['units_done'] + 1
        elapsed = time.monotonic() - gpu['t0']
        assert elapsed <= GPU_CAP_S[stage] / gpu['n_workers'], ('device-second cap reached; scheduling stopped', elapsed)
    receipt['model_calls'] = totals
    receipt['bytes'] = B.dir_bytes(output)
    if stage == 'preflight':
        exp.write(output / 'preflight.json', {'status': 'passed', 'units': [u['key'] for u in units], 'model_calls': totals,
                                               'bytes': receipt['bytes']}, immutable=True)
    return {'units': len(units), 'model_calls': totals}


def run(stage, worker, output, authorization):
    auth = authorize(authorization, stage)
    n_workers, gpu = auth['maximum_workers'], worker % 2
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root'] / f'worker-{worker}').resolve()
    import fcntl
    lock = open(f'/tmp/acupuncture-nwr-worker{worker}.lock', 'w')
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
    import torch
    try:
        source = exp.read(T1.SOURCE / 'contract.json')['source']
        receipt['asset_identity'] = exp.model_assets()
        engine = ControlEngine(source['model_path'], exp.model_spec(), f'cuda:{gpu}')
        exp.metadata_check(engine)
        exp.write(output / 'metadata.json', engine.metadata, immutable=True)
        units = plan(stage, worker, n_workers)
        exp.write(output / 'plan.json', units, immutable=True)
        receipt['summary'] = execute(engine, stage, output, receipt, units, {'id': gpu, 't0': started, 'n_workers': n_workers})
        receipt['integrity'] = engine.verify_unchanged()
        receipt['peak_memory_bytes'] = int(torch.cuda.max_memory_allocated(gpu))
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
    assert set(r['record_hashes']) == {f'records/{u["key"]}.json' for u in units}
    assert set(r['tensor_hashes']) == {f'tensors/{u["key"]}.pt' for u in units}
    for rel, digest in r['record_hashes'].items():
        assert exp.sha(path / rel) == digest, rel
    for rel in r['record_hashes']:
        rec = exp.read(path / rel)
        rel_t = rec['tensor_file']
        assert exp.sha(path / rel_t) == r['tensor_hashes'][rel_t], rel_t
        assert rec['direction'] == DIR and set(rec['arms']) == set(ARMS) and rec['seeds'] == list(SEEDS)
        assert struct_ok(rec['structure_t1'], [int(k) for k in rec['structure_t1']])
        assert rec['oracle_max'] <= S.ORACLE_TOL and rec['rand_norm_err_max'] <= NORM_TOL
        for g in ('sources', 'replay', 'oracle', 'random', 'structure', 'hooks', 'calibration'):
            assert rec['gates'][g], g
    check_limits(r['model_calls'], r['stage'])
    assert r['integrity']['hooks_removed'] is True
    assert r['integrity']['target_weight_sha256_after'] == exp.read(path / 'metadata.json')['target_weight_sha256_before']
    assert exp.read(path / 'exit.json')['returncode'] == 0
    if r['stage'] == 'preflight':
        assert exp.read(path / 'preflight.json')['status'] == 'passed'
    return {'status': 'passed', 'stage': r['stage'], 'units': len(units), 'freeze_sha256': r['freeze_sha256'],
            'wall_seconds': r['wall_seconds'], 'model_calls': r['model_calls'], 'bytes': r['bytes'], 'peak_memory_bytes': r.get('peak_memory_bytes')}


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
            cmd = [sys.executable, '-u', str(HERE / 'nwr_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
        calls = {k: sum(x['model_calls'][k] for x in results) for k in results[0]['model_calls']}
        check_limits(calls, stage)
        assert units == (len(PREFLIGHT_ITEMS) if stage == 'preflight' else 48), units
        gpu_s = sum(x['wall_seconds'] for x in results)
        assert gpu_s <= GPU_CAP_S[stage], ('device-time cap exceeded', gpu_s)
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
