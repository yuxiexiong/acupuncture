"""NWC-01 r03 (CONTRACT r03): out-of-development confirmation of the NWR-01 relation on 72 new inputs (stratum N: target not first-listed, 48;
stratum F: target first-listed, 24), three directions, receiver L11, patches only at t2 in the 14 G layers.
All patches are built from float32 state differences dS and the receiver's own q / k / alpha / beta:
  use 'D': scale * alpha dS^T q            use 'E': -scale * alpha beta (k^T q) dS^T k            unit u: u * |alpha dS^T q| (norm source dS)
  D00 / E00: dS = S1[L00] - S1[L11]     D10: S1[L10] - S1[L11]     DV: S1[L00] - S1[L10]     DX: partner's S1[L00] - S1[L11]
  halves: scale 0.5;  R1..R10: unit at the D00 norm, FRESH seeds on the new panel (the five NWR-01 seeds are used only on the two bridge
  inputs);  Q1..Q40: unit at the D10 norm (@k) and at the D00 norm (@n).
New inputs have no earlier records: gates are internal (hook identities, FP64 patch arithmetic, patch identities, t1 structure).
The preflight additionally runs two NWR-01 inputs through this runner and requires bit-for-bit agreement with the NWR-01 records.
python nwc_run.py freeze PATH | run ... | verify WORKER_DIR | launch ..."""
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
NWR_DIR = HERE.parent / 'cache-native-write-readout-v1-2026-11-05'
sys.path.insert(0, str(NWR_DIR))
sys.path.insert(0, str(HERE))
import nwr_run as N  # noqa: E402  (frozen NWR-01 runner; brings the frozen SRU-01 / LVK-01 runners)
from nwr_run import *  # noqa: E402,F401,F403

HERE = Path(__file__).resolve().parent
S, LVKR = N.S, N.LVKR
NWR_FORMAL = NWR_DIR / 'runs/formal-r01'
INPUTS, NWC_LEDGER = HERE / 'data/nwc-inputs-r01.json', HERE / 'data/nwc-tokens-r01.json'
PLAN_ID = 'NWC-01-NATIVE-WRITE-CONFIRM-r03'
DIRS3 = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1')
MAIN_DIRS = DIRS3[:2]
BRIDGE_DIR = N.DIR
SEEDS_R = tuple(202611061 + j for j in range(10))                    # fresh: not the NWR-01 seeds
RAND = tuple(f'R{j}' for j in range(1, 11))
OLD_SEEDS_R, OLD_RAND = N.SEEDS, N.RAND                              # bridge inputs only
SEEDS_Q = tuple(202611101 + j for j in range(40))
N_QNAT = 20
QN = tuple(f'Q{j}' for j in range(1, N_QNAT + 1))
BASE_T2 = ('D00', 'E00', 'D10') + RAND
EXTRA_T2 = ('DV', 'DX', 'D00h', 'DXh', 'D10h') + QN                 # stratum N only
ARMS_F = ('C', 'L00', 'L10', 'L11') + BASE_T2
ARMS_N = ARMS_F + EXTRA_T2
BRIDGE_ITEMS = ('LVK-H-NA-NQ01-ABC-A', 'LVK-H-NA-NQ02-ABC-B')
PREFLIGHT_NEW = ('NWC-NQ01-S1-a', 'NWC-NQ01-S1-c')
PREFLIGHT_ITEMS = BRIDGE_ITEMS + PREFLIGHT_NEW
N_FORMAL = 72
TOL = 1e-5
IDENT_TOL = 1e-4                                                   # float32 sum of two patches vs the third
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
ND = len(DIRS3)
# per-unit upper bounds (window <= 28 tokens per formation; natural trajectories <= 31 further forwards)
_U = {'N': {'formations': 2 * (1 + ND), 'prefix_prefills': 2, 't1': 1 + 5 * ND, 'refs': 3 * ND, 'c_t2': 99 * ND, 'trajectories': 1 + 41 * ND, 'shadow': 84 * ND},
      'F': {'formations': 1 + ND, 'prefix_prefills': 1, 't1': 1 + 3 * ND, 'refs': 3 * ND, 'c_t2': 14 * ND, 'trajectories': 1 + 16 * ND, 'shadow': 56 * ND},
      'old': {'formations': 2, 'prefix_prefills': 1, 't1': 4, 'refs': 3, 'c_t2': 9, 'trajectories': 12, 'shadow': 56},
      'self': {'formations': 1 + ND, 'prefix_prefills': 1, 't1': 2 * ND, 'refs': 0, 'c_t2': 0, 'trajectories': 0, 'shadow': 28 * ND}}


def _lim(mix):
    out = {k: sum(_U[u][k] * n for u, n in mix.items()) for k in _U['N']}
    out['formation_token_forwards'] = 28 * out['formations']
    out['n_steps'] = 31 * out['trajectories']
    out['decode_forwards'] = out['t1'] + out['refs'] + out['c_t2'] + out['n_steps'] + sum(n for u, n in mix.items() if u in ('N', 'F', 'old')) * ND
    out['calibrations'] = 0
    return out


LIMITS = {'preflight': _lim({'old': 2, 'N': 1, 'F': 1, 'self': 1}), 'formal': _lim({'N': 48, 'F': 24})}
GPU_CAP_S = {'preflight': 0.3 * 3600, 'formal': 2.2 * 3600}
STORAGE_LIMIT = 16 * 2 ** 30


def conditions():
    c = LVKR.conditions()
    return {d: c[d] for d in DIRS3}


def nwc_ledger():
    led = exp.read(NWC_LEDGER)
    assert led['status'] == 'passed' and led['inputs_sha256'] == exp.sha(INPUTS) and led['n'] == N_FORMAL
    return led['items']


def nwr_records():
    out = {}
    for w in sorted(NWR_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        for rel, dg in r['record_hashes'].items():
            assert exp.sha(w / rel) == dg, 'NWR record hash'
            rec = exp.read(w / rel)
            out[rec['text']] = rec
    return out


def all_units():
    led = nwc_ledger()
    return [{'item_id': k, 'base_id': v['plan']['base_id'], 'key': k, 'panel': 'new', 'stratum': v['plan']['stratum']} for k, v in led.items()]


def plan(stage, worker, n_workers):
    rows = all_units()
    if stage == 'preflight':
        old = LVKR.ledger()
        br = [{'item_id': k, 'base_id': old[k]['plan']['base_id'], 'key': k, 'panel': 'old', 'stratum': 'old'} for k in BRIDGE_ITEMS]
        new = [r for r in rows if r['item_id'] in PREFLIGHT_NEW]
        assert len(new) == 2 and {r['stratum'] for r in new} == {'N', 'F'}
        return br + new
    fams = sorted({r['base_id'] for r in rows})
    mine = {f for k, f in enumerate(fams) if k % n_workers == worker}
    return [r for r in rows if r['base_id'] in mine]


def read_gen(query, key, value, g, beta, S_r, l2norm, dS, use='D', scale=1.0, unit=None):
    """Replicated kernel order (as S.read_use) with one output patch built from the float32 state difference dS.
    Returns (out cast, native S2, stats [H, 3] = |alpha dS^T q|, |patch|, cos, FP64 / norm error, Dc [H, dv] float32 cpu)."""
    import torch
    initial_dtype = query.dtype
    q, k, v, bt, dc = [x.transpose(1, 2).to(torch.float32, memory_format=torch.contiguous_format) for x in (query, key, value, beta, g)]
    q = l2norm(q, dim=-1, eps=1e-6)
    k = l2norm(k, dim=-1, eps=1e-6)
    q = q / (q.shape[-1] ** 0.5)
    S_ = S_r.to(v)
    out = torch.zeros_like(v)
    q_t, k_t, v_t = q[:, :, 0], k[:, :, 0], v[:, :, 0]
    decay_t = dc[:, :, 0].exp()[..., None, None]
    S_ = S_ * decay_t
    beta_t = bt[:, :, 0].unsqueeze(-1)
    kv_mem = (S_ * k_t.unsqueeze(-1)).sum(dim=-2)
    delta = (v_t - kv_mem) * beta_t
    S_ = S_ + k_t.unsqueeze(-1) * delta.unsqueeze(-2)
    o_t = (S_ * q_t.unsqueeze(-1)).sum(dim=-2)
    al = decay_t[..., 0, 0].unsqueeze(-1)
    Dc = al * (dS * q_t.unsqueeze(-1)).sum(dim=-2)
    nD = Dc.norm(dim=-1, keepdim=True)
    if unit is not None:
        P = unit.to(Dc) * nD
        nz = nD[..., 0] > 0
        err = float(((P.norm(dim=-1) - nD[..., 0]).abs()[nz] / nD[..., 0][nz]).max()) if bool(nz.any()) else 0.0
        add = bool(nz.any())
    else:
        if use == 'D':
            P = Dc
        else:
            kq = (k_t * q_t).sum(-1, keepdim=True)
            P = -al * beta_t * kq * (dS * k_t.unsqueeze(-1)).sum(dim=-2)
        dd, ad, qd, kd, bd = dS.double(), al.double(), q_t.double(), k_t.double(), beta_t.double()
        if use == 'D':
            Pd = ad * (dd * qd.unsqueeze(-1)).sum(-2)
        else:
            Pd = -ad * bd * (kd * qd).sum(-1, keepdim=True) * (dd * kd.unsqueeze(-1)).sum(-2)
        if scale != 1.0:
            P = P * scale
        oo = o_t.double() + scale * Pd
        err = float(((o_t + P).double() - oo).abs().max() / max(1.0, float(oo.abs().max())))
        add = True
    if add:
        o_t = o_t + P
    nP = P.norm(dim=-1)
    cos = (Dc * P).sum(-1) / torch.clamp(nD[..., 0] * nP, min=1e-30)
    stats = torch.stack([nD[0, :, 0], nP[0], cos[0]], -1).float().cpu()
    out[:, :, 0] = o_t
    out = out.transpose(1, 2).contiguous().to(initial_dtype)
    return out, S_, stats, err, Dc[0].float().cpu()


class GHook:
    """One t2 forward in the 14 G layers with a read_gen patch.  dS: {layer: float32 state difference}; recv: {layer: receiver S1} (asserted
    bit-equal to the kernel's initial state); seed: unit direction of (seed, layer) at the norm of alpha dS^T q."""

    def __init__(self, model, G, dS, recv, use='D', scale=1.0, seed=None, keep=False):
        self.model, self.G, self.dS, self.recv, self.use, self.scale, self.seed, self.keep = model, tuple(G), dS, recv, use, scale, seed, keep
        self.QM = gdn_module()
        self.orig = self.QM.torch_recurrent_gated_delta_rule
        self.layer, self.handles, self.calls, self.stats, self.err, self.Dc = None, [], [], {}, {}, {}

    def __enter__(self):
        import torch
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
            assert torch.equal(initial_state, me.recv[me.layer]), ('receiver state != S1[L11]', me.layer)
            u = None if me.seed is None else unit_dir(me.seed, me.layer, (value.shape[0], value.shape[2], value.shape[3]))
            out, S2, st, err, Dc = read_gen(query, key, value, g, beta, initial_state, me.QM.l2norm, me.dS[me.layer], me.use, me.scale, u)
            me.stats[me.layer], me.err[me.layer] = st, err
            if me.keep:
                me.Dc[me.layer] = Dc
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
        assert set(self.err) == set(self.G) and max(self.err.values()) <= TOL, ('patch arithmetic / norm', max(self.err.values()))


def endpoint_delta(engine, led, contexts, calib, conds, counts, vecs, G):
    """S1[L00] - S1[L11] (float32, per layer) for another input: its own formation, its own t1 endpoints.  Used for the cross-input arm."""
    import torch
    model = engine.model
    types = L.layer_types(model)
    C, T, info = form_new(engine, led, contexts, calib, conds, counts)
    cconv = {l: L._get(C.layers[l], 'conv_states').clone() for l in G}
    _, u, sign = ARMS_ALL['Rk']
    out = {}
    for d in conds:
        vec = QKFR.mask_vec(vecs[u][f"{info['scenario']}|{d}"].float(), 'k')
        bT, _ = QKFR.edited_arm(T[d], T[d], T[d], G, None, 1)
        check_bg(bT, T[d], C, types, G, 'T', 'T')
        c00, _ = t1(engine, copy.deepcopy(bT), info['last'], info['n'], counts, 't1')
        hk = LHook(model, G, 'cell', a=1, b=1, vec=vec, sign=sign, cconv=cconv)
        c11, _ = t1L(engine, copy.deepcopy(bT), info['last'], info['n'], counts, 't1', hk)
        rs = lambda c, l: L._get(c.layers[l], 'recurrent_states').to(torch.float32)   # noqa: E731
        out[d] = {l: (rs(c00, l) - rs(c11, l)).clone() for l in G}
        del c00, c11, bT
    del C, T
    torch.cuda.empty_cache()
    return out


def run_item(engine, unit, contexts, calib, conds, qctok, output, stage, vecs=None, refs=None):
    import torch
    model, tok = engine.model, engine.tokenizer
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
    assert tuple(G) == (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30) and G[0] == LAYER0
    assert tuple(STOP) == tuple(CFK.STOP) == tuple(engine.stop_ids)
    QM = gdn_module()
    KRDR.QHOOK_ORIG[0] = QM.torch_recurrent_gated_delta_rule
    a_id, panel = unit['item_id'], unit['panel']
    old = panel == 'old'
    led = refs['old_ledger'][a_id] if old else refs['ledger'][a_id]
    stratum = 'old' if old else led['plan']['stratum']
    cuse = {BRIDGE_DIR: conds[BRIDGE_DIR]} if old else dict(conds)
    full = stratum == 'N'
    counts = {k: 0 for k in COUNT_KEYS}
    tensors, gates, dirs_out = {}, {}, {}
    nz_total, err_max, ident_max, half_max = 0, 0.0, 0.0, 0.0
    C, T, info = form_new(engine, led, contexts, calib, cuse, counts)
    hC, hT = comp_sha(C, types, ALLK, 0), {d: comp_sha(T[d], types, ALLK, 0) for d in cuse}
    it, code_tok, n = info['item'], info['code_tokens'], info['n']
    comp = it['first_listed'] if it['target'] != it['first_listed'] else it['listed_codes'][1]
    cconv = {l: L._get(C.layers[l], 'conv_states').clone() for l in G}
    dec = lambda ids: tok.decode(ids, skip_special_tokens=False)   # noqa: E731
    fF = led['tokens']['q_shared']
    rs = lambda c, l: L._get(c.layers[l], 'recurrent_states')      # noqa: E731

    def nat(c1_, z1_, hook=None):
        x_ = int(z1_.argmax())
        r, z2_ = natural(engine, copy.deepcopy(c1_), x_, n, counts, hook=hook)
        r['text'] = dec(r['ids'])
        return x_, r, z2_

    cC, zC = t1(engine, copy.deepcopy(C), info['last'], n, counts, 't1')
    xC, rC, _ = nat(cC, zC)
    clean = {'x': xC, 'N': rC}
    del cC
    partner = None
    if full:
        pled = refs['ledger'][led['plan']['partner_id']]
        assert pled['plan']['base_id'] == led['plan']['base_id'] and pled['plan']['version'] == led['plan']['version'] and pled['plan']['situation'] != led['plan']['situation']
        partner = endpoint_delta(engine, pled, contexts, calib, cuse, counts, vecs, G)
    selfd = endpoint_delta(engine, led, contexts, calib, cuse, counts, vecs, G) if (full and stage == 'preflight') else None
    _, u, sign = ARMS_ALL['Rk']
    for d in cuse:
        arms = {'C': clean}
        vec = QKFR.mask_vec(vecs[u][f"{info['scenario']}|{d}"].float(), 'k')
        bT, _ = QKFR.edited_arm(T[d], T[d], T[d], G, None, 1)
        check_bg(bT, T[d], C, types, G, 'T', 'T')
        hbT = comp_sha(bT, types, ALLK, 0)
        c1, z1, x, S1, z2n = {}, {}, {}, {}, {}
        cap0 = CapHook(model, G)
        c1['L00'], z1['L00'] = t1(engine, copy.deepcopy(bT), info['last'], n, counts, 't1', hook=cap0)
        for name, (aa, bb) in (('L10', (1, 0)), ('L11', (1, 1))):
            hk = LHook(model, G, 'cell', a=aa, b=bb, vec=vec, sign=sign, cconv=cconv)
            c1[name], z1[name] = t1L(engine, copy.deepcopy(bT), info['last'], n, counts, 't1', hk)
        for name in ('L00', 'L10', 'L11'):
            S1[name] = {l: rs(c1[name], l).clone() for l in G}
            x[name], r_, z2n[name] = nat(c1[name], z1[name])
            arms[name] = {'x': x[name], 'N': r_}
            tensors[f't1|{name}|{d}'] = z1[name].to(torch.bfloat16).cpu()
        h1 = {name: comp_sha(c1[name], types, ALLK, 0) for name in c1}
        # t1 structure: L00 vs "original kernel fed the shadow v" (== L10 bit for bit)
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
        okz, z0 = bit_equal(o_.logits[0, -1].float(), z1['L10'])
        assert okz, 'structure reference != L10'
        nz_total += z0
        struct = struct_compare(cap0.args, cap1.args, G)
        assert struct_ok(struct, G), ('t1 structure', struct[str(G[0])])
        del cap0, cap1, o_
        f32 = lambda nm, l: S1[nm][l].to(torch.float32)   # noqa: E731
        dS = {'D00': {l: f32('L00', l) - f32('L11', l) for l in G}, 'D10': {l: f32('L10', l) - f32('L11', l) for l in G}}
        if full:
            dS['DV'] = {l: f32('L00', l) - f32('L10', l) for l in G}
            dS['DX'] = partner[d]
            if selfd is not None:
                assert all(torch.equal(selfd[d][l], dS['D00'][l]) for l in G), 'endpoint_delta(self) != S1[L00] - S1[L11]'
        xr, cr, recv = x['L11'], c1['L11'], S1['L11']
        reached = xr not in STOP
        Dcs, pn = {}, {}

        def m_only(hook):
            _, zc = fwd(engine, copy.deepcopy(cr), fF, n, counts, 'c_t2', hook=hook)
            return zc

        def t2_arm(name, mk, keep=False, natural_too=True):
            nonlocal err_max
            hk_c = mk(keep)
            zc = m_only(hk_c)
            M, Mall = margins(zc, it, code_tok, comp)
            st = torch.stack([hk_c.stats[l] for l in G])
            pn[name] = float((st[..., 1] ** 2).sum().sqrt())
            if keep:
                Dcs[name] = torch.stack([hk_c.Dc[l] for l in G])
            rec = {'C': {'M': M, 'M_all': Mall, 't2_sha': F.th(zc)}}
            err_max = max(err_max, max(hk_c.err.values()))
            if not name.startswith('Q'):
                tensors[f'C|{name}|{d}'] = zc.to(torch.bfloat16).cpu()
                tensors[f'stats|C|{name}|{d}'] = st
            if natural_too:
                if reached:
                    hk_n = mk(False)
                    nr, _ = natural(engine, copy.deepcopy(cr), xr, n, counts, hook=hk_n)
                    nr['text'] = dec(nr['ids'])
                    nr['t2_token'] = nr['ids'][1]
                    err_max = max(err_max, max(hk_n.err.values()))
                else:
                    nr = {'ids': [xr], 'termination': 'stop', 'reached_t2': False, 'text': dec([xr])}
                rec['N'] = nr
            arms[name] = rec
            return M

        zc00 = m_only(None)
        M00, Mall00 = margins(zc00, it, code_tok, comp)
        arms['L11']['C'] = {'M': M00, 'M_all': Mall00, 't2_sha': F.th(zc00)}
        tensors[f'C|L11|{d}'] = zc00.to(torch.bfloat16).cpu()
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
        mk = lambda key, **kw: (lambda keep: GHook(model, G, dS[key], recv, keep=keep, **kw))   # noqa: E731
        t2_arm('D00', mk('D00'), keep=True)
        t2_arm('E00', mk('D00', use='E'))
        t2_arm('D10', mk('D10'), keep=True)
        for name, seed in (zip(OLD_RAND, OLD_SEEDS_R) if old else zip(RAND, SEEDS_R)):
            t2_arm(name, mk('D00', seed=seed))
        qk, qn = None, None
        if full:
            t2_arm('DV', mk('DV'), keep=True)
            t2_arm('DX', mk('DX'), keep=True)
            t2_arm('D00h', mk('D00', scale=0.5))
            t2_arm('DXh', mk('DX', scale=0.5))
            t2_arm('D10h', mk('D10', scale=0.5))
            qk = [t2_arm(f'Q{j + 1}', mk('D10', seed=SEEDS_Q[j])) for j in range(N_QNAT)]
            for j in range(N_QNAT, len(SEEDS_Q)):
                hk = GHook(model, G, dS['D10'], recv, seed=SEEDS_Q[j])
                qk.append(margins(m_only(hk), it, code_tok, comp)[0])
                err_max = max(err_max, max(hk.err.values()))
            qn = []
            for j in range(len(SEEDS_Q)):
                hk = GHook(model, G, dS['D00'], recv, seed=SEEDS_Q[j])
                qn.append(margins(m_only(hk), it, code_tok, comp)[0])
                err_max = max(err_max, max(hk.err.values()))
            ident = float((Dcs['DV'] + Dcs['D10'] - Dcs['D00']).abs().max() / max(1e-30, float(Dcs['D00'].abs().max())))
            assert ident <= IDENT_TOL, ('DV + D10 != D00 patch', ident)
            ident_max = max(ident_max, ident)
            for full_, half_ in (('D00', 'D00h'), ('DX', 'DXh'), ('D10', 'D10h')):
                hrel = abs(pn[half_] - 0.5 * pn[full_]) / max(1e-30, 0.5 * pn[full_])
                assert hrel <= TOL, ('half-amplitude patch', half_, hrel)
                half_max = max(half_max, hrel)
        tensors[f'patch|D00|{d}'] = Dcs['D00'].to(torch.float16)
        tensors[f'struct|v_rel_diff|{d}'] = torch.tensor([struct[str(l)]['v_rel_diff'] for l in G])
        for name in c1:
            assert comp_sha(c1[name], types, ALLK, 0) == h1[name], ('post-t1 source cache modified', name)
        assert comp_sha(bT, types, ALLK, 0) == hbT
        if old:                                                     # bit-for-bit bridge to the NWR-01 record of this input
            nw = refs['nwr'][a_id]
            assert nw['direction'] == d and info['hashes'] and x == nw['x']
            for name in N.ARMS:
                a_, b_ = arms[name], nw['arms'][name]
                assert a_['N']['ids'] == b_['N']['ids'] and a_['N']['termination'] == b_['N']['termination'], ('natural != NWR', name)
                if 'C' in b_:
                    assert a_['C']['t2_sha'] == b_['C']['t2_sha'] and a_['C']['M'] == b_['C']['M'], ('C route t2 != NWR', name)
        assert set(arms) == set(ARMS_N if full else (N.ARMS if old else ARMS_F))
        dirs_out[d] = {'x': x, 'reached_t2': reached, 'arms': arms, 'structure_t1': struct, 'patch_norm': pn, 'M_Qk': qk, 'M_Qn': qn}
        del c1, S1, bT, dS
        torch.cuda.empty_cache()
    assert hC == comp_sha(C, types, ALLK, 0) and all(comp_sha(T[d], types, ALLK, 0) == hT[d] for d in cuse), 'donor modified'
    F.assert_no_hooks(model)
    gates['panel'] = 'tokens == frozen ledger (old inputs: LVK ledger); formation hashes recorded'
    gates['hooks'] = 'replicated-order hook with a=b=0 == native t2 (C, N); t2 hook fires once per G layer; receiver state == S1[L11]; t3 onward no hook'
    gates['arithmetic'] = f'patch arithmetic vs FP64 / random-patch norm, max relative error {err_max:.3g} <= {TOL}'
    gates['identities'] = ('not applicable (stratum without constructed donors)' if not full else
                           f'DV + D10 == D00 patch, max relative error {ident_max:.3g}; half-amplitude norms, max relative error {half_max:.3g} <= {TOL}; identity tolerance {IDENT_TOL}'
                           + ('; endpoint_delta(self) == S1[L00] - S1[L11] bit for bit' if selfd is not None else ''))
    gates['structure'] = 't1 kernel inputs L00 vs L10: first G layer q/k/g/beta/S0 bit-equal and v different; S0 bit-equal in every G layer'
    gates['bridge'] = 'NWR-01 record reproduced bit for bit (natural tokens, C-route t2 hash and M, 12 arms)' if old else 'not applicable (new input)'
    gates['calibration'] = 'NQ-01 saved scenario calibration (source hash in receipt)'
    body = {'text': a_id, 'panel': panel, 'stratum': stratum, 'scenario': info['scenario'], 'situation': None if old else led['plan']['situation'],
            'version': None if old else led['plan']['version'], 'partner_id': None if old else led['plan']['partner_id'],
            'item': it, 'code_tokens': code_tok, 'competitor': comp, 'fF': fF, 'directions': dirs_out, 'formation_hashes': info['hashes'],
            'target_second_token': code_tok[it['target']], 'signed_zero_exceptions': nz_total, 'err_max': err_max, 'ident_max': ident_max,
            'half_max': half_max, 'seeds_R': list(OLD_SEEDS_R if old else SEEDS_R), 'seeds_Q': list(SEEDS_Q), 'kernel_identity': kernel_identity(), 'calibration': calib,
            'counts': counts, 'gates': gates}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + [HERE / 'CONTRACT.zh-CN.md', INPUTS, NWC_LEDGER]
    nwr = [NWR_DIR / 'nwr_run.py', NWR_DIR / 'nwr_core.py', NWR_DIR / 'freeze-r01.json', NWR_FORMAL / 'verification.json']
    nwr += [w / 'receipt.json' for w in sorted(NWR_FORMAL.glob('worker-*')) if w.is_dir()]
    return own + nwr


def extrapolate(pre_root):
    """Formal estimate from the preflight worker: seconds of the stratum-N unit x 48 + of the stratum-F unit x 24 + model load x 2; bytes likewise."""
    ws = [w for w in sorted(Path(pre_root).glob('worker-*')) if w.is_dir()]
    assert len(ws) == 1
    r = exp.read(ws[0] / 'receipt.json')
    recs = [exp.read(ws[0] / rel) for rel in r['record_hashes']]
    load = r['wall_seconds'] - sum(x['seconds'] for x in recs)
    by = {x['stratum']: x for x in recs if x['panel'] == 'new'}
    sz = lambda x: (ws[0] / x['tensor_file']).stat().st_size   # noqa: E731
    return {'N_seconds': by['N']['seconds'], 'F_seconds': by['F']['seconds'], 'load_seconds': load,
            'device_seconds': 48 * by['N']['seconds'] + 24 * by['F']['seconds'] + 2 * load, 'bytes': 48 * sz(by['N']) + 24 * sz(by['F']), 'texts': N_FORMAL}


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
    S.check_freeze(N.SRU_DIR / 'freeze-r01.json')          # the whole frozen SRU / LVK source tree is unchanged
    N.check_freeze(NWR_DIR / 'freeze-r01.json')            # the frozen NWR-01 sources are unchanged
    ki = kernel_identity()
    assert not ki['fla'] and not ki['kernels'] and not ki['causal_conv1d'], ('non-torch kernel available', ki)
    if stage == 'formal':
        pre = exp.read(HERE / auth['preflight_verification_path'])
        assert pre['status'] == 'passed' and pre['freeze_sha256'] == auth['freeze_sha256'] and pre['stage'] == 'preflight'
        ex = extrapolate(HERE / Path(auth['preflight_verification_path']).parent)
        assert ex['device_seconds'] <= GPU_CAP_S['formal'] and ex['bytes'] <= STORAGE_LIMIT, ('preflight extrapolation exceeds the formal cap', ex)
    return auth


def check_limits(counts, stage):
    lim = LIMITS[stage]
    assert all(counts[k] <= lim[k] for k in lim), (counts, lim)


def execute(engine, stage, output, receipt, units, gpu):
    qi = QCDR.qc_items()
    contexts = exp.contexts_for(engine.tokenizer, [qi[t['plan']['qc_broad_id']] for t in items()])
    contexts.update(exp.contexts_for(engine.tokenizer, [v['item'] for v in ledger().values()]))
    contexts.update(exp.contexts_for(engine.tokenizer, [v['item'] for v in nwc_ledger().values()]))
    conds = conditions()
    receipt['kernel_identity'] = T1.kernel_identity()
    assert list(engine.stop_ids) == list(CFK.STOP)
    F.hook_baseline(engine.model)
    import torch
    totals = {k: 0 for k in COUNT_KEYS + ('calibrations',)}
    calib = {}
    qctok = exp.read(QC_TOKENS)
    vecs = load_vectors()
    refs = {'ledger': nwc_ledger(), 'old_ledger': LVKR.ledger(), 'nwr': nwr_records()}
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
    lock = open(f'/tmp/acupuncture-nwc-worker{worker}.lock', 'w')
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
        want = [BRIDGE_DIR] if rec['panel'] == 'old' else list(DIRS3)
        assert list(rec['directions']) == want and rec['seeds_R'] == list(OLD_SEEDS_R if rec['panel'] == 'old' else SEEDS_R) and rec['seeds_Q'] == list(SEEDS_Q)
        for d in want:
            x = rec['directions'][d]
            assert set(x['arms']) == set(ARMS_N if rec['stratum'] == 'N' else (N.ARMS if rec['panel'] == 'old' else ARMS_F))
            assert struct_ok(x['structure_t1'], [int(k) for k in x['structure_t1']])
            assert (x['M_Qk'] is None) == (rec['stratum'] != 'N') and (x['M_Qk'] is None or (len(x['M_Qk']) == len(x['M_Qn']) == len(SEEDS_Q)))
        assert rec['err_max'] <= TOL and rec['ident_max'] <= IDENT_TOL and rec['half_max'] <= TOL
        for g in ('panel', 'hooks', 'arithmetic', 'identities', 'structure', 'bridge', 'calibration'):
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
            cmd = [sys.executable, '-u', str(HERE / 'nwc_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
        assert units == (len(PREFLIGHT_ITEMS) if stage == 'preflight' else N_FORMAL), units
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
