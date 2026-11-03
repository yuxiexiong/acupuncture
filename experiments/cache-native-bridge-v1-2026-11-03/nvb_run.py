"""NVB-01: from the native intervened state T, split the t1 local-v restoration of LVK into its output use and its stored-state use
(plan docs/cache-native-bridge-plan-v2-2026-11-03.zh-CN.md; CONTRACT r01).  LVK new panel (48 held-out texts), 4 directions.
At t1, in the 14 G layers only, cell B(c, a, b) computes the LVK update twice on the same local inputs and returns
    o1 = S_hat(v_c, k_b)^T q   and   S_return = S_hat(v_a, k_b),   S_hat(v, k_b) = alpha S0 - alpha beta k0 (k0^T S0) + beta k_b v^T
(custom_update order, erase key always k0).  c, a in {0: native v0, 1: shadow v1}; b in {0: k0, 1: shadow k1}.  Matched random arm (c = 0):
a = r_j stores v0 + rho_j, rho_j a per-head random direction with norm ||v1 - v0|| of that head and layer (deterministic seed, same for b = 0/1).
Diagonal cells replay LVK L00 / L01 / L10 / L11.  t2 onward: no hook (except a read-only q/k capture on three C-route cells).
python nvb_run.py freeze PATH | run ... | verify WORKER_DIR | launch ..."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
LVK_DIR = HERE.parent / 'cache-local-v-k-v1-2026-11-03'
SRU_DIR = HERE.parent / 'cache-state-read-use-v1-2026-11-03'
sys.path.insert(0, str(LVK_DIR))
sys.path.insert(0, str(SRU_DIR))
sys.path.insert(0, str(HERE))
import lvk_run as LVKR  # noqa: E402  (frozen LVK-01 runner)
import sru_run as SRUR  # noqa: E402  (frozen SRU-01 runner: LVK record loader, read-only t2 capture hook)
import nvb_core as NC  # noqa: E402

KRDR, KUCR, QKFR, QCOR, QCDR, QCR, QKDR = LVKR.KRDR, LVKR.KUCR, LVKR.QKFR, LVKR.QCOR, LVKR.QCDR, LVKR.QCR, LVKR.QKDR
B, CFK, F, L, T1, exp = LVKR.B, LVKR.CFK, LVKR.F, LVKR.L, LVKR.T1, LVKR.exp
LVK_FORMAL, SRU_FORMAL = LVK_DIR / 'runs/formal-r01', SRU_DIR / 'runs/formal-r01'

PLAN_ID = 'NVB-01-NATIVE-V-USE-BRIDGE-v1'
PLAN_DOCS = [REPO / 'docs/cache-native-bridge-plan-v1-2026-11-03.zh-CN.md', REPO / 'docs/cache-native-bridge-plan-v2-2026-11-03.zh-CN.md']
SPLIT, MAX_NEW, STOP, DIRECTIONS, LAYER0 = LVKR.SPLIT, LVKR.MAX_NEW, LVKR.STOP, LVKR.DIRECTIONS, LVKR.LAYER0
QK, K_LO, K_HI, V_LO = LVKR.QK, LVKR.K_LO, LVKR.K_HI, LVKR.V_LO
ARMS_ALL = LVKR.ARMS_ALL
G14 = (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
MAIN = NC.MAIN
K_DRAWS = NC.K_DRAWS
DIAG = {'000': 'L00', '001': 'L01', '110': 'L10', '111': 'L11'}     # NVB cell (c a b) -> LVK cell (a b) with c == a
CAPTURE = ('000', '100', '010')
ORACLE_TOL = 1e-5
PREFLIGHT_ITEMS = LVKR.NEW_PRE
COUNT_KEYS = LVKR.COUNT_KEYS + ('r_t1', 'r_c_t2')
ALLK = LVKR.ALLK


def _limits(n_in):
    per = {'t1': 8 * 4, 'refs': 4 * 4, 'r_t1': K_DRAWS * 2 * 4, 'c_t2': 8 * 4, 'r_c_t2': K_DRAWS * 2 * 4, 'trajectories': 8 * 4}
    lim = {k: v * n_in for k, v in per.items()}
    lim['n_steps'] = lim['trajectories'] * (MAX_NEW - 1)
    lim['decode_forwards'] = lim['t1'] + lim['refs'] + lim['r_t1'] + lim['c_t2'] + lim['r_c_t2'] + lim['n_steps']
    # shadow convolutions per direction: main v 6 + k 4; LVK refs L01 k, L10 v, L11 v+k = 4; random per draw v (b0) + v+k (b1) = 3
    lim['shadow'] = (10 + 4 + 3 * K_DRAWS) * len(G14) * 4 * n_in
    lim.update({'formations': 5 * n_in, 'prefix_prefills': n_in, 'calibrations': 0})
    return lim


LIMITS = {'preflight': {**_limits(2), 'formation_token_forwards': 270}, 'formal': {**_limits(48), 'formation_token_forwards': 6390}}
GPU_CAP_S = {'preflight': 0.15 * 3600, 'formal': 1.2 * 3600}
STORAGE_LIMIT = 12 * 2 ** 30
comp_sha = LVKR.comp_sha
gdn_module, kernel_identity, load_vectors, conditions, items = LVKR.gdn_module, LVKR.kernel_identity, LVKR.load_vectors, LVKR.conditions, LVKR.items
margins, natural, fwd, t1, t1L, LHook, form_new, ledger = LVKR.margins, LVKR.natural, LVKR.fwd, LVKR.t1, LVKR.t1L, LVKR.LHook, LVKR.form_new, LVKR.ledger
bit_equal, cache_equal, check_bg, first_step, custom_update, to_key = LVKR.bit_equal, LVKR.cache_equal, LVKR.check_bg, LVKR.first_step, LVKR.custom_update, LVKR.to_key


def plan(stage, worker, n_workers):
    rows = [r for r in LVKR.all_units() if r['panel'] == 'new']
    if stage == 'preflight':
        rows = [r for r in rows if r['item_id'] in PREFLIGHT_ITEMS]
        assert len(rows) == 2
        return rows
    bases = list(dict.fromkeys(r['base_id'] for r in rows))
    mine = {b for k, b in enumerate(bases) if k % n_workers == worker}
    return [r for r in rows if r['base_id'] in mine]


# ---------------------------------------------------------------- local computation

def rho_seed(rkey, layer):
    item, d, j = rkey
    return int.from_bytes(hashlib.sha256(f'NVB-RHO|{item}|{d}|{j}|{layer}'.encode()).digest()[:8], 'little') & (2 ** 63 - 1)


def make_rho(rkey, layer, v0, v1):
    """Per-head random direction (float32), norm == ||v1 - v0|| of that head (float32).  v0 / v1: [B, 1, H, dv]."""
    import torch
    dv = v1.to(torch.float32) - v0.to(torch.float32)
    nrm = dv.norm(dim=-1, keepdim=True)
    gen = torch.Generator(device='cpu').manual_seed(rho_seed(rkey, layer))
    z = torch.randn(tuple(dv.shape), generator=gen, dtype=torch.float32)
    z = z / z.norm(dim=-1, keepdim=True).clamp_min(1e-30)
    return z.to(dv.device) * nrm, nrm


def ds_error(Sa, Sc, kb, va, vc, beta, l2norm):
    """|S_a - S_c - beta k_b,norm (v_a - v_c)^T| / max(1, |expected|) in FP64 (real-arithmetic identity of the custom update)."""
    import torch
    w = l2norm(kb.transpose(1, 2).to(torch.float32), dim=-1, eps=1e-6)[:, :, 0].double()          # [B, H, dk]
    vd = (va.to(torch.float32).transpose(1, 2)[:, :, 0] - vc.to(torch.float32).transpose(1, 2)[:, :, 0]).double()   # [B, H, dv]
    bt = beta.transpose(1, 2).to(torch.float32)[:, :, 0].double()                                   # [B, H]
    exp_ = bt[..., None, None] * w.unsqueeze(-1) * vd.unsqueeze(-2)
    act = Sa.double() - Sc.double()
    return float((act - exp_).abs().max() / max(1.0, float(exp_.abs().max())))


def split_update(query, key, kb, vc, va, g, beta, initial_state, l2norm):
    """Output from the v_c candidate, returned state from the v_a candidate (same q / k0 / k_b / alpha / beta / S0).  Diagonal (va is vc): one
    call.  Returns (out, S_return, oracle_err, ds_err or None)."""
    oc, Sc, ec = custom_update(query, key, kb, vc, g, beta, initial_state, True, True, l2norm, oracle=True)
    if va is vc:
        return oc, Sc, ec, None
    _, Sa, ea = custom_update(query, key, kb, va, g, beta, initial_state, True, True, l2norm, oracle=True)
    return oc, Sa, max(ec, ea), ds_error(Sa, Sc, kb, va, vc, beta, l2norm)


class NHook:
    """One t1 forward, cell (c, a, b); a == 'r' with rkey = (item, direction, draw).  Shadows as LVK LHook: v1 from the pre-update conv buffer
    clone with the V channels replaced by C's conv history (same current input), k1 by the frozen k edit of the old k slots; never written back."""

    def __init__(self, model, G, c, a, b, vec=None, sign=None, cconv=None, rkey=None):
        assert c in (0, 1) and a in (0, 1, 'r') and b in (0, 1)
        assert (a == 'r') == (rkey is not None) and (a != 'r' or c == 0)
        self.model, self.G, self.c, self.a, self.b, self.vec, self.sign, self.cconv, self.rkey = model, tuple(G), c, a, b, vec, sign, cconv, rkey
        self.need_v = c == 1 or a in (1, 'r')
        self.need_k = b == 1
        self.QM = gdn_module()
        self.orig_k, self.orig_c = self.QM.torch_recurrent_gated_delta_rule, self.QM.causal_conv1d_update
        self.layer, self.mod, self.handles = None, None, []
        self.conv_calls, self.kern_calls, self.sv, self.sk = [], [], {}, {}
        self.oracle, self.dserr, self.rhoerr, self.vdiff = {}, {}, {}, {}
        self.rho_h = hashlib.sha256()
        self.n_shadow = 0

    def __enter__(self):
        assert self.QM.torch_recurrent_gated_delta_rule is self.orig_k and self.QM.causal_conv1d_update is self.orig_c
        for i, lay in enumerate(L.model_layers(self.model)):
            la = getattr(lay, 'linear_attn', None)
            if la is not None:
                def pre(m, _a, i=i):
                    self.layer, self.mod = i, m
                self.handles.append(la.register_forward_pre_hook(pre))
        me = self

        def conv(hidden_states, conv_state, weight, bias=None, activation=None):
            if me.layer not in me.G:
                return me.orig_c(hidden_states, conv_state, weight, bias, activation)
            import torch
            Bc = conv_state.clone()
            out = me.orig_c(hidden_states, conv_state, weight, bias, activation)
            m = me.mod
            me.conv_calls.append(me.layer)
            if me.need_v:
                B2 = torch.cat([Bc[:, :V_LO], me.cconv[me.layer][:, V_LO:]], dim=1).contiguous()
                o2 = me.orig_c(hidden_states, B2, weight, bias, activation)
                assert torch.equal(o2[:, :V_LO], out[:, :V_LO]), 'shadow v changed q/k channels'
                mixed = o2.transpose(1, 2)
                _, _, v1 = torch.split(mixed, [m.key_dim, m.key_dim, m.value_dim], dim=-1)
                me.sv[me.layer] = v1.reshape(mixed.shape[0], mixed.shape[1], -1, m.head_v_dim)
                me.n_shadow += 1
            if me.need_k:
                j = me.G.index(me.layer)
                blk, _ = QCOR.edit_block(Bc[:, :QK].clone(), me.vec[j], me.sign)
                B3 = torch.cat([blk, Bc[:, QK:]], dim=1).contiguous()
                o3 = me.orig_c(hidden_states, B3, weight, bias, activation)
                assert torch.equal(o3[:, :K_LO], out[:, :K_LO]) and torch.equal(o3[:, K_HI:], out[:, K_HI:]), 'shadow k changed q/v channels'
                me.sk[me.layer] = to_key(o3, m)
                me.n_shadow += 1
            return out

        def kern(query, key, value, g=None, beta=None, initial_state=None, output_final_state=False, use_qk_l2norm_in_kernel=False, **kw):
            if me.layer not in me.G:
                return me.orig_k(query, key, value, g=g, beta=beta, initial_state=initial_state, output_final_state=output_final_state,
                                 use_qk_l2norm_in_kernel=use_qk_l2norm_in_kernel, **kw)
            import torch
            assert query.shape[1] == 1 and output_final_state and use_qk_l2norm_in_kernel
            me.kern_calls.append(me.layer)
            v0 = value
            v1 = me.sv[me.layer] if me.need_v else None
            if v1 is not None:
                assert v1.shape == v0.shape and v1.dtype == v0.dtype
                me.vdiff[me.layer] = (v1.to(torch.float32) - v0.to(torch.float32))[0, 0].norm(dim=-1).cpu()
            kb = me.sk[me.layer] if me.b else key
            assert kb.shape == key.shape and kb.dtype == key.dtype
            vc = v1 if me.c else v0
            if me.a == 'r':
                rho, nrm = make_rho(me.rkey, me.layer, v0, v1)
                va = v0.to(torch.float32) + rho
                got = (va - v0.to(torch.float32)).norm(dim=-1, keepdim=True)
                me.rhoerr[me.layer] = float((got - nrm).abs().max() / max(1e-6, float(nrm.max())))
                me.rho_h.update(rho.detach().cpu().contiguous().numpy().tobytes())
            else:
                va = v1 if me.a else v0
            o, S, err, dse = split_update(query, key, kb, vc, va, g, beta, initial_state, me.QM.l2norm)
            me.oracle[me.layer] = err
            if dse is not None:
                me.dserr[me.layer] = dse
            return o, S
        self.QM.causal_conv1d_update = conv
        self.QM.torch_recurrent_gated_delta_rule = kern
        return self

    def __exit__(self, *exc):
        self.QM.causal_conv1d_update = self.orig_c
        self.QM.torch_recurrent_gated_delta_rule = self.orig_k
        for h in self.handles:
            h.remove()
        self.handles = []
        return False

    def check(self):
        assert sorted(self.kern_calls) == sorted(self.G) and sorted(self.conv_calls) == sorted(self.G), ('hook calls', self.kern_calls, self.conv_calls)
        assert set(self.oracle) == set(self.G) and max(self.oracle.values()) <= ORACLE_TOL, ('FP64 oracle', max(self.oracle.values()))
        if self.c != self.a:
            assert set(self.dserr) == set(self.G) and max(self.dserr.values()) <= ORACLE_TOL, ('state-difference identity', max(self.dserr.values()))
        else:
            assert not self.dserr
        if self.a == 'r':
            assert set(self.rhoerr) == set(self.G) and max(self.rhoerr.values()) <= ORACLE_TOL, ('rho norm', max(self.rhoerr.values()))

    @property
    def rho_sha(self):
        return self.rho_h.hexdigest()


def s_only_equal(ca, cb, types, G):
    """Every cache tensor bit-equal except the G-layer recurrent states.  Returns (ok, n_signed_zero, G layers whose S differs, first failure)."""
    import torch
    nz, diff = 0, []
    for i, kind, f in L.component_tensors(ca, types):
        a, b = L._get(ca.layers[i], f), L._get(cb.layers[i], f)
        if f == 'recurrent_states' and i in G:
            if not torch.equal(a, b):
                diff.append(i)
            continue
        ok, z = bit_equal(a, b)
        if not ok:
            return False, nz, diff, (i, f)
        nz += z
    return True, nz, diff, None


# ---------------------------------------------------------------- one input

def run_item(engine, unit, contexts, calib, conds, qctok, output, stage, vecs=None, refs=None):
    import torch
    model, tok = engine.model, engine.tokenizer
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
    assert tuple(G) == G14 and G[0] == LAYER0
    assert tuple(STOP) == tuple(CFK.STOP) == tuple(engine.stop_ids), 'stop ids != parser stop set'
    KRDR.QHOOK_ORIG[0] = gdn_module().torch_recurrent_gated_delta_rule
    a_id = unit['item_id']
    assert unit['panel'] == 'new'
    counts = {k: 0 for k in COUNT_KEYS}
    tensors, gates, out = {}, {}, {}
    acc = {'nz': 0, 'oracle': 0.0, 'dserr': 0.0, 'rhoerr': 0.0, 'min_s_layers': len(G14), 'min_s_layers_random': len(G14)}
    led = refs['ledger'][a_id]
    lv = refs['lvk'][a_id]
    lv_t = torch.load(lv['_tensor_path'], map_location='cpu')
    C, T, info = form_new(engine, led, contexts, calib, conds, counts)
    assert info['hashes'] == lv['formation_hashes'], 'formation hashes != LVK'
    hC, hT = comp_sha(C, types, ALLK, 0), {d: comp_sha(T[d], types, ALLK, 0) for d in conds}
    it, code_tok, n = info['item'], info['code_tokens'], info['n']
    comp = it['first_listed'] if it['target'] != it['first_listed'] else it['listed_codes'][1]
    cconv = {l: L._get(C.layers[l], 'conv_states').clone() for l in G}
    dec = lambda ids: tok.decode(ids, skip_special_tokens=False)   # noqa: E731

    def note(hk):
        acc['oracle'] = max(acc['oracle'], max(hk.oracle.values()))
        if hk.dserr:
            acc['dserr'] = max(acc['dserr'], max(hk.dserr.values()))
        if hk.rhoerr:
            acc['rhoerr'] = max(acc['rhoerr'], max(hk.rhoerr.values()))

    for d in conds:
        s = info['scenario']
        fF = led['tokens']['q_shared']
        assert fF not in STOP
        _, u, sign = ARMS_ALL['Rk']
        vec = QKFR.mask_vec(vecs[u][f'{s}|{d}'].float(), 'k')
        bT, _ = QKFR.edited_arm(T[d], T[d], T[d], G, None, 1)
        check_bg(bT, T[d], C, types, G, 'T', 'T')
        hbT = comp_sha(bT, types, ALLK, 0)
        lvd = lv['directions'][d]['arms']
        c1, z1, cells, qcap = {}, {}, {}, {}
        # ---- 8 main cells at t1
        for cell in MAIN:
            hk = NHook(model, G, int(cell[0]), int(cell[1]), int(cell[2]), vec=vec, sign=sign, cconv=cconv)
            c1[cell], z1[cell] = t1L(engine, copy.deepcopy(bT), info['last'], n, counts, 't1', hk)
            note(hk)
            tensors[f't1|{cell}|{d}'] = z1[cell].to(torch.bfloat16).cpu()
            if hk.vdiff:
                tensors[f'vdiff|{cell}|{d}'] = torch.stack([hk.vdiff[l] for l in G])
        # ---- diagonal replay: t1 bf16 == LVK; full cache == reference implementation (native t1 for 000, LVK LHook otherwise)
        for cell, lk in DIAG.items():
            assert bit_equal(z1[cell].to(torch.bfloat16).cpu(), lv_t[f't1|{lk}|{d}'])[0], ('diagonal t1 != LVK', cell, d)
            if cell == '000':
                cr, zr = t1(engine, copy.deepcopy(bT), info['last'], n, counts, 'refs')
            else:
                hk = LHook(model, G, 'cell', a=int(lk[1]), b=int(lk[2]), vec=vec, sign=sign, cconv=cconv)
                cr, zr = t1L(engine, copy.deepcopy(bT), info['last'], n, counts, 'refs', hk)
            okz, z0 = bit_equal(zr, z1[cell])
            okc, zc0, _, fail = cache_equal(cr, c1[cell], types, G)
            assert okz and okc, ('diagonal != reference implementation', cell, d, fail)
            acc['nz'] += z0 + zc0
            del cr
        # ---- storage-only bridges: fixed (c, b), a 0 -> 1: logits and every non-S cache tensor identical; only G-layer S may differ
        sdiff = {}
        for c_ in '01':
            for b_ in '01':
                x0, x1 = f'{c_}0{b_}', f'{c_}1{b_}'
                okz, z0 = bit_equal(z1[x0], z1[x1])
                ok, zc0, dl, fail = s_only_equal(c1[x0], c1[x1], types, G)
                assert okz and ok and dl, ('storage-only bridge', x0, x1, d, fail, dl)
                acc['nz'] += z0 + zc0
                acc['min_s_layers'] = min(acc['min_s_layers'], len(dl))
                sdiff[f'{x0}-{x1}'] = dl
        # ---- C route (forced shared first token) and N route (own t1 token, greedy, no hook)
        for cell in MAIN:
            hk = SRUR.RHook(model, G, 'capture') if cell in CAPTURE else None
            _, zc = fwd(engine, copy.deepcopy(c1[cell]), fF, n, counts, 'c_t2', hook=hk)
            if hk is not None:
                qcap[cell] = hk.qk
            M, Mall = margins(zc, it, code_tok, comp)
            tensors[f'C|{cell}|{d}'] = zc.to(torch.bfloat16).cpu()
            x_ = int(z1[cell].argmax())
            r, z2 = natural(engine, copy.deepcopy(c1[cell]), x_, n, counts)
            r['text'] = dec(r['ids'])
            if z2 is not None:
                tensors[f'N|{cell}|{d}'] = z2.to(torch.bfloat16)
            cells[cell] = {'x': x_, 'first': first_step(z1[cell], fF), 'C': {'M': M, 'M_all': Mall, 't2_sha': F.th(zc)}, 'N': r}
            if cell in DIAG:
                la = lvd[DIAG[cell]]
                assert bit_equal(tensors[f'C|{cell}|{d}'], lv_t[f'C|{DIAG[cell]}|{d}'])[0] and M == la['C']['M'], ('diagonal C t2 != LVK', cell, d)
                assert r['ids'] == la['N']['ids'] and r['termination'] == la['N']['termination'] and x_ == la['x'], ('diagonal natural != LVK', cell, d)
        # ---- matched random storage arm (c = 0), C route only
        rnd = {}
        for j in range(K_DRAWS):
            rnd[str(j)] = {}
            for b_ in '01':
                hk = NHook(model, G, 0, 'r', int(b_), vec=vec, sign=sign, cconv=cconv, rkey=(a_id, d, j))
                cr, zr = t1L(engine, copy.deepcopy(bT), info['last'], n, counts, 'r_t1', hk)
                note(hk)
                base = f'00{b_}'
                okz, z0 = bit_equal(zr, z1[base])
                ok, zc0, dl, fail = s_only_equal(c1[base], cr, types, G)
                assert okz and ok and dl, ('random storage-only bridge', j, b_, d, fail)
                acc['nz'] += z0 + zc0
                acc['min_s_layers_random'] = min(acc['min_s_layers_random'], len(dl))
                _, zc = fwd(engine, cr, fF, n, counts, 'r_c_t2')
                M, Mall = margins(zc, it, code_tok, comp)
                rnd[str(j)][b_] = {'M': M, 'M_all': Mall, 't2_sha': F.th(zc), 'rho_sha': hk.rho_sha}
            assert rnd[str(j)]['0']['rho_sha'] == rnd[str(j)]['1']['rho_sha'], ('rho differs between b = 0 and b = 1', j, d)
        # ---- t2 q / k agreement (C route, same input token): output-branch change (000 vs 100) and storage change (000 vs 010)

        def cosm(u_, w_):
            uu, ww = u_.float().reshape(-1, u_.shape[-1]), w_.float().reshape(-1, w_.shape[-1])
            return float(torch.nn.functional.cosine_similarity(uu, ww, dim=-1).median())
        qk_cos = {str(l): {f'{p}|{x}': cosm(qcap['000'][l][k_], qcap[x][l][k_]) for x in ('100', '010') for k_, p in ((0, 'q'), (1, 'k'))} for l in G}
        assert comp_sha(bT, types, ALLK, 0) == hbT, ('pre-t1 background cache modified', d)
        out[d] = {'fF': fF, 'cells': cells, 'random': rnd, 'storage_diff_layers': sdiff, 'qk_cos_t2': qk_cos,
                  'target_second_token': code_tok[it['target']]}
        del c1, bT
        torch.cuda.empty_cache()
    assert hC == comp_sha(C, types, ALLK, 0) and all(comp_sha(T[d], types, ALLK, 0) == hT[d] for d in conds), 'donor modified'
    F.assert_no_hooks(model)
    gates['sources'] = 'formation hashes == LVK; T background check; pre-t1 caches and C / T unchanged'
    gates['diagonal'] = 'B000/B001/B110/B111 == LVK L00/L01/L10/L11 (t1 bf16, C t2 bf16, M, natural tokens); full cache == native t1 / LVK LHook'
    gates['storage_only'] = f'fixed (c, b): t1 logits and all non-S cache bit-equal, only G-layer S differs (min layers {acc["min_s_layers"]}); random arm vs B00b likewise (min {acc["min_s_layers_random"]})'
    gates['oracle'] = f'custom update FP64 max relative error {acc["oracle"]:.3g} <= {ORACLE_TOL}'
    gates['state_identity'] = f'S_a - S_c == beta k_b (v_a - v_c)^T, FP64 max {acc["dserr"]:.3g} <= {ORACLE_TOL}'
    gates['rho'] = f'per-head ||rho|| == ||v1 - v0||, max {acc["rhoerr"]:.3g} <= {ORACLE_TOL}; same rho for b = 0 / 1'
    gates['hooks'] = 't1 hooks once per G layer; t2 only read-only capture on 000/100/010 C route; t3 onward none; module functions restored'
    gates['calibration'] = 'NQ-01 saved scenario calibration (source hash in receipt)'
    body = {'text': a_id, 'panel': 'new', 'scenario': info['scenario'], 'item': it, 'code_tokens': code_tok, 'competitor': comp, 'directions': out,
            'signed_zero_exceptions': acc['nz'], 'oracle_max': acc['oracle'], 'dserr_max': acc['dserr'], 'rhoerr_max': acc['rhoerr'],
            'k_draws': K_DRAWS, 'kernel_identity': kernel_identity(), 'calibration': calib, 'counts': counts, 'gates': gates}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md'] + PLAN_DOCS
    sru = [SRU_DIR / 'freeze-r01.json', SRU_DIR / 'analysis/sru-readouts-r01.json', SRU_FORMAL / 'verification.json']
    sru += [w / 'receipt.json' for w in sorted(SRU_FORMAL.glob('worker-*')) if w.is_dir()]
    return own + sru + [p for p in SRUR.frozen_paths() if p not in own and p not in sru]


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
    man = exp.read(QKDR.RPOST_C_MANIFEST)
    assert man['status'] == 'passed' and exp.sha(QKDR.RPOST_C) == man['rpost_sha256'], 'QKD C1343 r_post != manifest'
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
    import threading
    import torch
    totals = {k: 0 for k in COUNT_KEYS + ('calibrations',)}
    calib = {}
    qctok = exp.read(LVKR.QC_TOKENS)
    vecs = load_vectors()
    refs = {'lvk': SRUR.lvk_records(), 'ledger': ledger()}
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
            rec = {'schema': 1, 'experiment': HERE.name, 'plan_id': PLAN_ID, 'stage': stage, 'unit': u, 'item': {'id': u['item_id']}, **body,
                   'seconds': time.monotonic() - started, 'freeze_sha256': receipt['freeze_sha256'], 'created_at': exp.utc()}
            L._store(output, receipt, f'records/{u["key"]}.json', rec)
            exp.write(output / 'receipt.json', receipt)
            assert B.dir_bytes(output) <= STORAGE_LIMIT // MAX_WORKERS['formal'], 'storage budget exceeded'
            hb['totals'], hb['units_done'] = dict(totals), hb['units_done'] + 1
            elapsed = time.monotonic() - gpu['t0']
            assert elapsed <= GPU_CAP_S[stage] / gpu['n_workers'], ('device-second cap reached; scheduling stopped', elapsed)
    finally:
        hb['stop'] = True
        th.join()
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
    lock = open(f'/tmp/acupuncture-nvb-worker{worker}.lock', 'w')
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
        assert set(rec['directions']) == set(DIRECTIONS) and rec['k_draws'] == K_DRAWS
        for d in DIRECTIONS:
            dd = rec['directions'][d]
            assert set(dd['cells']) == set(MAIN) and set(dd['random']) == {str(j) for j in range(K_DRAWS)}
            assert all(set(v) == {'0', '1'} for v in dd['random'].values())
        for g in ('sources', 'diagonal', 'storage_only', 'oracle', 'state_identity', 'rho', 'hooks', 'calibration'):
            assert rec['gates'][g], g
        assert rec['oracle_max'] <= ORACLE_TOL and rec['dserr_max'] <= ORACLE_TOL and rec['rhoerr_max'] <= ORACLE_TOL
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
            cmd = [sys.executable, '-u', str(HERE / 'nvb_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
