"""CGV-01 (V2 + review): boundary exploration of the write -> read relation (plan data/source/cache-chain-generalization-plan-v2-2026-11-03.zh-CN.md,
branch commit 6234dde1; CONTRACT r01).  Stages: prep (L12 needle q/k collection on the 48 old development texts; 3 new-scenario calibrations),
preflight, formal.  Groups: G1 L12/C3621/-1 needle on the 48 held-out texts (LVK endpoints C, L00..L11 + SRU D/E reads); G2 three new task
structures (27 inputs) x N4146 / N1210 with frozen mu_all (+ same-angle random write chain on GS01 x N4146); G3-C clean background challenge
(write-term k + mu vs same-angle random rotation) x N4146 / N1210 on the 48 held-out texts, with D/E reads both ways.
python cgv_run.py freeze PATH | run ... | verify WORKER_DIR | launch ..."""
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
import sru_run as SRUR  # noqa: E402  (frozen SRU-01 runner)

LVKR, NVR, KUCR, KRDR, QSRR, QKDR = SRUR.LVKR, SRUR.NVR, SRUR.KUCR, SRUR.KRDR, SRUR.QSRR, SRUR.QKDR
QKFR, QCOR, QSTR, QCDR, QCR, NQR, SVQ, NRR = SRUR.QKFR, SRUR.QCOR, SRUR.QSTR, SRUR.QCDR, SRUR.QCR, SRUR.NQR, SRUR.SVQ, SRUR.NRR
FC_DIR, SP_DIR, SVQ_DIR, NQ_DIR, QC_DIR, QCD_DIR, QST_DIR, QCO_DIR, QKF_DIR = SRUR.FC_DIR, SRUR.SP_DIR, SRUR.SVQ_DIR, SRUR.NQ_DIR, SRUR.QC_DIR, SRUR.QCD_DIR, SRUR.QST_DIR, SRUR.QCO_DIR, SRUR.QKF_DIR
QKD_DIR, QKD_FORMAL, QKD_PRE, QSR_DIR, QSR_FORMAL = SRUR.QKD_DIR, SRUR.QKD_FORMAL, SRUR.QKD_PRE, SRUR.QSR_DIR, SRUR.QSR_FORMAL
KRD_DIR, KHC_DIR, KRD_FORMAL, KUC_DIR, KUC_FORMAL, NVW_DIR, NVW_FORMAL = SRUR.KRD_DIR, SRUR.KHC_DIR, SRUR.KRD_FORMAL, SRUR.KUC_DIR, SRUR.KUC_FORMAL, SRUR.NVW_DIR, SRUR.NVW_FORMAL
LVK_DIR, LVK_FORMAL = SRUR.LVK_DIR, SRUR.LVK_FORMAL
SRU_FORMAL = SRU_DIR / 'runs/formal-r01'
B3R, V, P, PK, X = SRUR.B3R, SRUR.V, SRUR.P, SRUR.PK, SRUR.X
CF, CFK, LR, B = SRUR.CF, SRUR.CFK, SRUR.LR, SRUR.B
F, L, T1, exp, K = SRUR.F, SRUR.L, SRUR.T1, SRUR.exp, SRUR.K

PLAN_ID = 'CGV-01-CHAIN-BOUNDARY-v2'
SRC = HERE / 'data/source'
PLAN_DOCS = [SRC / 'cache-chain-generalization-plan-v2-2026-11-03.zh-CN.md', SRC / 'cache-chain-generalization-self-check-v2-2026-11-03.zh-CN.md',
             SRC / 'new-scenarios-r01.json', SRC / 'cpu-design-audit-r01.json', SRC / 'SOURCES.txt']
DESIGN, QC_INPUTS, QC_TOKENS, HELDOUT, LEDGER = SRUR.DESIGN, SRUR.QC_INPUTS, SRUR.QC_TOKENS, SRUR.HELDOUT, SRUR.LEDGER
QCD_G, QST_FORMAL, QCO_FORMAL, QKF_FORMAL = SRUR.QCD_G, SRUR.QST_FORMAL, SRUR.QCO_FORMAL, SRUR.QKF_FORMAL
QC_FORMAL, NQ_FORMAL, SVQ_FORMAL, SP_FORMAL, NR_FORMAL, B3_FORMAL, XC_FORMAL, SK_FORMAL = SRUR.QC_FORMAL, SRUR.NQ_FORMAL, SRUR.SVQ_FORMAL, SRUR.SP_FORMAL, SRUR.NR_FORMAL, SRUR.B3_FORMAL, SRUR.XC_FORMAL, SRUR.SK_FORMAL
G2_LEDGER, G2_MU, RAND_U, ASSETS = HERE / 'data/g2-ledger-r01.json', HERE / 'data/g2-mu-all-r01.pt', HERE / 'data/random-u-r01.pt', HERE / 'data/assets-manifest-r01.json'
PREP_MAN, L12_MU, GEN_CALIB = HERE / 'data/prep-manifest-r01.json', HERE / 'data/l12-mu-r01.pt', HERE / 'data/gen-calibrations-r01.json'
SPLIT, A_LAYERS, MAX_NEW, STOP = SRUR.SPLIT, SRUR.A_LAYERS, SRUR.MAX_NEW, SRUR.STOP
DIRECTIONS, OLD_DIRS, NEW_DIR = SRUR.DIRECTIONS, SRUR.OLD_DIRS, SRUR.NEW_DIR
STAGES = ('prep', 'preflight', 'formal')
MAX_WORKERS = {'prep': 2, 'preflight': 1, 'formal': 2}
ARMS_ALL = SRUR.ARMS_ALL
LAYER0 = SRUR.LAYER0
QK, K_LO, K_HI = LVKR.QK, LVKR.K_LO, LVKR.K_HI
L12 = 'N_L12_C3621_D-1'
L12_COND = {'id': L12, 'kind': 'native', 'layer': 12, 'channel': 3621, 'dose': -1.0}
L0_DIRS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1')
G1_PRE = ('LVK-H-NA-NQ01-ABC-A', 'LVK-H-NA-NQ02-ABC-B')
G2_PRE = ('GEN-GS01-ABC-A', 'GEN-GS02-ABC-A', 'GEN-GS03-ABC-A')
BRIDGE_ITEM = 'LVK-H-NA-NQ01-ABC-A'
CELLS = ('10', '01', '11')
GUARD_S = 24 * 3600            # runaway guard per worker only (no fixed experimental GPU budget, per the user's decision)
GPU_CAP_S = {s: GUARD_S * 2 for s in STAGES}
STORAGE_LIMIT = 12 * 2 ** 30
ALLK = SRUR.ALLK
COUNT_KEYS = SRUR.COUNT_KEYS
ROT_TOL = 1e-5
comp_sha, tensor_bytes_sha = SRUR.comp_sha, SRUR.tensor_bytes_sha
gdn_module, kernel_identity, conditions, items = SRUR.gdn_module, SRUR.kernel_identity, SRUR.conditions, SRUR.items
margins, natural, fwd, t1, t1L, LHook, form_new, ledger = SRUR.margins, SRUR.natural, SRUR.fwd, SRUR.t1, SRUR.t1L, SRUR.LHook, SRUR.form_new, SRUR.ledger
bit_equal, cache_equal, check_bg, first_step, RHook, UHook = SRUR.bit_equal, SRUR.cache_equal, SRUR.check_bg, SRUR.first_step, SRUR.RHook, LVKR.UHook
cache_equal_vmask, custom_update, to_key = LVKR.cache_equal_vmask, KUCR.custom_update, LVKR.to_key
PREFLIGHT_ITEMS = G1_PRE


def g2_ledger():
    led = exp.read(G2_LEDGER)
    assert led['status'] == 'passed' and led['new_scenarios_sha256'] == exp.sha(SRC / 'new-scenarios-r01.json')
    return led['items']


def assets():
    man = exp.read(ASSETS)
    for f, k in ((G2_LEDGER, 'g2_ledger_sha256'), (G2_MU, 'g2_mu_all_sha256'), (RAND_U, 'random_u_sha256')):
        assert exp.sha(f) == man[k], ('asset hash', f)
    assert exp.sha(QKFR.QCO_OFFSETS_PT) == man['qco_offsets_sha256']
    return man


def prep_assets():
    import torch
    man = exp.read(PREP_MAN)
    assert man['status'] == 'passed' and exp.sha(L12_MU) == man['l12_mu_sha256'] and exp.sha(GEN_CALIB) == man['gen_calibrations_sha256']
    return torch.load(L12_MU, map_location='cpu')['mu'], exp.read(GEN_CALIB)['calibrations']


def units_for(stage):
    rows = []
    if stage == 'prep':
        for t in items():
            rows.append({'kind': 'collect', 'item_id': t['id'], 'base_id': t['plan']['base_id'], 'key': f"collect|{t['id']}"})
        for s in ('GS01', 'GS02', 'GS03'):
            rows.append({'kind': 'calib', 'item_id': f'GEN-{s}-ABC-A', 'base_id': s, 'key': f'calib|{s}'})
        return rows
    newp = ledger()
    g2 = g2_ledger()
    g1_ids = G1_PRE if stage == 'preflight' else tuple(newp)
    g2_ids = G2_PRE if stage == 'preflight' else tuple(g2)
    for a in g1_ids:
        rows.append({'kind': 'g1', 'item_id': a, 'base_id': newp[a]['plan']['base_id'], 'key': f'g1|{a}'})
    for a in g2_ids:
        rows.append({'kind': 'g2', 'item_id': a, 'base_id': g2[a]['plan']['base_id'], 'key': f'g2|{a}'})
    for a in g1_ids:
        rows.append({'kind': 'g3c', 'item_id': a, 'base_id': newp[a]['plan']['base_id'], 'key': f'g3c|{a}'})
    if stage == 'preflight':
        rows.append({'kind': 'bridge', 'item_id': BRIDGE_ITEM, 'base_id': newp[BRIDGE_ITEM]['plan']['base_id'], 'key': f'bridge|{BRIDGE_ITEM}'})
    return rows


def plan(stage, worker, n_workers):
    rows = units_for(stage)
    if n_workers == 1:
        return rows
    bases = list(dict.fromkeys(r['base_id'] for r in rows))
    mine = {b for k, b in enumerate(bases) if k % n_workers == worker}
    return [r for r in rows if r['base_id'] in mine]


def unit_budget(u):
    """Maximal model calls of one unit (natural trajectories counted with up to 31 forwards after t1)."""
    b = {k: 0 for k in COUNT_KEYS + ('calibrations',)}
    kind = u['kind']
    if kind == 'collect':
        L_ = {t['id']: t for t in items()}[u['item_id']]['plan']['L']
        b.update(formations=2, prefix_prefills=1, formation_token_forwards=2 * L_)
    elif kind == 'calib':
        b.update(calibrations=1)
    else:
        L_ = (g2_ledger() if kind == 'g2' else ledger())[u['item_id']]['plan']['L']
        if kind == 'g1':
            b.update(formations=2, prefix_prefills=1, formation_token_forwards=2 * L_, t1=5, refs=8, trajectories=11, shadow=84)
        elif kind == 'g2':
            rnd = u['base_id'] == 'GS01'
            b.update(formations=3, prefix_prefills=1, formation_token_forwards=3 * L_, t1=1 + 2 * 4 + (2 if rnd else 0), refs=2 * 8 + (2 if rnd else 0),
                     trajectories=1 + 2 * 10 + (8 if rnd else 0), shadow=2 * 84 + (42 if rnd else 0))
        elif kind == 'g3c':
            b.update(formations=1, prefix_prefills=1, formation_token_forwards=L_, t1=5, refs=1 + 2 + 2 * 4, trajectories=1 + 2 * 14, shadow=2 * 28)
        elif kind == 'bridge':
            b.update(formations=2, prefix_prefills=1, formation_token_forwards=2 * L_, t1=2, refs=4, trajectories=8, shadow=42)
        b['c_t2'] = b['trajectories']
        b['n_steps'] = 31 * b['trajectories']
    b['decode_forwards'] = b['t1'] + b['refs'] + b['c_t2'] + b['n_steps']
    return b


def stage_limits(stage):
    tot = {k: 0 for k in COUNT_KEYS + ('calibrations',)}
    for u in units_for(stage):
        for k, v in unit_budget(u).items():
            tot[k] += v
    return tot


LIMITS = None      # computed lazily (needs data files)


def limits(stage):
    return stage_limits(stage)


# ---------------------------------------------------------------- same-angle random rotation

def rotate(k0_raw, km_raw, u_rep, l2norm):
    """Per head: unit kR at the same angle to normalised k0 as normalised k_mu, rotated toward the component of u orthogonal to k0; returned in
    raw scale ||k0_raw|| (FP32) so the kernel's L2 normalisation treats it exactly like k0.  Returns (kR_raw FP32, stats)."""
    import torch
    f = lambda x: x.transpose(1, 2).to(torch.float32)[0, :, 0]    # noqa: E731  [heads, dim]
    k0, km = f(k0_raw), f(km_raw)
    k0n, kmn = l2norm(k0, dim=-1, eps=1e-6).double(), l2norm(km, dim=-1, eps=1e-6).double()
    k0h = k0n / k0n.norm(dim=-1, keepdim=True)
    c = ((k0n * kmn).sum(-1) / (k0n.norm(dim=-1) * kmn.norm(dim=-1))).clamp(-1, 1)
    uu = u_rep.to(k0h)
    w = uu - (uu * k0h).sum(-1, keepdim=True) * k0h
    w = w / w.norm(dim=-1, keepdim=True)
    kh = c[:, None] * k0h + torch.sqrt(torch.clamp(1 - c * c, min=0))[:, None] * w
    kr = (kh * k0.double().norm(dim=-1, keepdim=True)).float()
    krn = l2norm(kr, dim=-1, eps=1e-6).double()
    c_real = (krn * k0n).sum(-1) / (krn.norm(dim=-1) * k0n.norm(dim=-1))
    st = {'cos_target_median': float(c.median()), 'cos_err_max': float((c_real - c).abs().max()),
          'norm_err_max': float((krn.norm(dim=-1) - k0n.norm(dim=-1)).abs().max()), 'u_dot_k0_abs_median': float((uu * k0h).sum(-1).abs().median())}
    return kr.reshape(1, 1, *kr.shape).contiguous(), st


class RotHook(LHook):
    """LHook variant: the write-term k is the same-angle random rotation of k0 (angle taken from this branch's own mu shadow); v as LHook (a)."""

    def __init__(self, model, G, a, vec, sign, cconv, u):
        super().__init__(model, G, 'cell', a=a, b=1, vec=vec, sign=sign, cconv=cconv)
        self.u, self.rot = u, {}

    def __enter__(self):
        super().__enter__()
        inner_c, me = self.QM.causal_conv1d_update, self
        orig_k = self.orig_k

        def conv2(hidden_states, conv_state, weight, bias=None, activation=None):
            out = inner_c(hidden_states, conv_state, weight, bias, activation)
            if me.layer in me.G:
                m = me.mod
                k0 = to_key(out, m)
                ur = me.u[me.G.index(me.layer)].repeat_interleave(m.num_v_heads // m.num_k_heads, dim=0)
                kr, st = rotate(k0, me.sk[me.layer], ur, me.QM.l2norm)
                assert st['cos_err_max'] <= ROT_TOL and st['norm_err_max'] <= ROT_TOL, ('rotation match', me.layer, st)
                me.sk[me.layer] = kr.to(k0.device)
                me.rot[me.layer] = st
            return out

        def kern2(query, key, value, g=None, beta=None, initial_state=None, output_final_state=False, use_qk_l2norm_in_kernel=False, **kw):
            if me.layer not in me.G:
                return orig_k(query, key, value, g=g, beta=beta, initial_state=initial_state, output_final_state=output_final_state,
                              use_qk_l2norm_in_kernel=use_qk_l2norm_in_kernel, **kw)
            me.kern_calls.append(me.layer)
            va = me.sv[me.layer] if me.a else value
            kb = me.sk[me.layer]
            assert kb.shape == key.shape and va.shape == value.shape
            o, S, err = custom_update(query, key, kb, va, g, beta, initial_state, output_final_state, use_qk_l2norm_in_kernel, me.QM.l2norm, oracle=True)
            me.oracle[me.layer] = err
            return o, S
        self.QM.causal_conv1d_update = conv2
        self.QM.torch_recurrent_gated_delta_rule = kern2
        return self


# ---------------------------------------------------------------- formation

def form_old_l12(engine, a, contexts, calib, counts):
    """Old development text: base and C (hashes == QCD G) and T for the L12 needle (write audit)."""
    import torch
    from control_engine import encode_text
    model, tok = engine.model, engine.tokenizer
    types = L.layer_types(model)
    t = {x['id']: x for x in items()}[a]
    pl = t['plan']
    item = QCDR.qc_items()[pl['qc_broad_id']]
    seg = PK.label_tokens(tok, contexts[a], item['boundary_text'], encode_text)
    assert not seg['straddling_tokens'] and (seg['b'], seg['n']) == (pl['b_b'], pl['n'])
    prompt = seg['ids']
    prefix = prompt[:-1]
    Bw = list(range(pl['p'], pl['e'] + 1))
    with torch.inference_mode():
        base = L.forward(model, list(prefix[:seg['b'] + 1]), 0, None).past_key_values
    counts['prefix_prefills'] += 1
    g = QSTR._g_record(a)
    assert comp_sha(base, types, ALLK, 0) == g['hashes']['base_b']
    C = P.form(engine, base, prefix, Bw, None, calib)
    counts['formations'] += 1
    counts['formation_token_forwards'] += len(Bw)
    assert comp_sha(C, types, ALLK, 0) == g['hashes']['C_b']
    au = X.write_audit(engine, L12_COND, calib)
    au['rel_err'] = abs(au['nominal_write_norm'] - au['target_write_norm']) / au['target_write_norm']
    assert au['rel_err'] <= V.K.RULE['write_rel'], ('L12 write audit', au)
    T = P.form(engine, base, prefix, Bw, L12_COND, calib)
    counts['formations'] += 1
    counts['formation_token_forwards'] += len(Bw)
    return C, T, au


# ---------------------------------------------------------------- shared pieces for the main groups

class Ctx:
    def __init__(self, engine, G, info, fF, counts, tensors, acc):
        self.engine, self.model, self.G, self.info, self.fF, self.counts, self.tensors, self.acc = engine, engine.model, G, info, fF, counts, tensors, acc
        it = info['item']
        self.it, self.code_tok, self.n = it, info['code_tokens'], info['n']
        self.comp = it['first_listed'] if it['target'] != it['first_listed'] else it['listed_codes'][1]
        self.dec = lambda ids: engine.tokenizer.decode(ids, skip_special_tokens=False)


def arm(cx, base, hook=None, kind='t1'):
    if hook is None:
        return t1(cx.engine, copy.deepcopy(base), cx.info['last'], cx.n, cx.counts, kind)
    if isinstance(hook, UHook):
        return t1(cx.engine, copy.deepcopy(base), cx.info['last'], cx.n, cx.counts, kind, hook=hook)
    c, z = t1L(cx.engine, copy.deepcopy(base), cx.info['last'], cx.n, cx.counts, kind, hook)
    if getattr(hook, 'oracle', None):
        cx.acc['oracle'] = max(cx.acc['oracle'], max(hook.oracle.values()))
    return c, z


def finish(cx, c1, z1, key):
    import torch
    _, zc = fwd(cx.engine, copy.deepcopy(c1), cx.fF, cx.n, cx.counts, 'c_t2')
    M, Mall = margins(zc, cx.it, cx.code_tok, cx.comp)
    cx.tensors[f'C|{key}'] = zc.to(torch.bfloat16).cpu()
    cx.tensors[f't1|{key}'] = z1.to(torch.bfloat16).cpu()
    x_ = int(z1.argmax())
    r, z2 = natural(cx.engine, copy.deepcopy(c1), x_, cx.n, cx.counts)
    r['text'] = cx.dec(r['ids'])
    if r['reached_t2']:
        r['t2_token'] = r['ids'][1]
    return {'x': x_, 'first': first_step(z1, cx.fF), 'C': {'M': M, 'M_all': Mall, 't2_sha': F.th(zc)}, 'N': r}, zc, z2


def refs00(cx, c1_r, x_r, zc, z2, Sd):
    """Replicated-order t2 hook with a = b = 0 == native t2 (C route; N route when reached)."""
    hk = RHook(cx.model, cx.G, 'cell', a=0, b=0, Sd=Sd)
    _, z = fwd(cx.engine, copy.deepcopy(c1_r), cx.fF, cx.n, cx.counts, 'refs', hook=hk)
    assert bit_equal(z, zc)[0], 'a=b=0 hook != native (C)'
    if x_r not in STOP:
        hk = RHook(cx.model, cx.G, 'cell', a=0, b=0, Sd=Sd)
        _, z = fwd(cx.engine, copy.deepcopy(c1_r), x_r, cx.n, cx.counts, 'refs', hook=hk)
        assert bit_equal(z.detach().cpu(), z2)[0], 'a=b=0 hook != native (N)'


def reads(cx, c1, S1, x, pairs, tag):
    import torch
    out = {}
    for pname, (r_, d_) in pairs.items():
        cells = {}
        for cell in CELLS:
            a, b = int(cell[0]), int(cell[1])
            hk = RHook(cx.model, cx.G, 'cell', a=a, b=b, Sd=S1[d_])
            _, zc = fwd(cx.engine, copy.deepcopy(c1[r_]), cx.fF, cx.n, cx.counts, 'c_t2', hook=hk)
            cx.acc['oracle'] = max(cx.acc['oracle'], max(hk.oracle.values()))
            if hk.ref11:
                cx.acc['ref11'] = max(cx.acc['ref11'], max(hk.ref11.values()))
            M, Mall = margins(zc, cx.it, cx.code_tok, cx.comp)
            cx.tensors[f'C|{tag}|{pname}|{cell}'] = zc.to(torch.bfloat16).cpu()
            if x[r_] in STOP:
                nr = {'ids': [x[r_]], 'termination': 'stop', 'reached_t2': False, 'text': cx.dec([x[r_]])}
            else:
                hk2 = RHook(cx.model, cx.G, 'cell', a=a, b=b, Sd=S1[d_])
                nr, _ = natural(cx.engine, copy.deepcopy(c1[r_]), x[r_], cx.n, cx.counts, hook=hk2)
                cx.acc['oracle'] = max(cx.acc['oracle'], max(hk2.oracle.values()))
                if hk2.ref11:
                    cx.acc['ref11'] = max(cx.acc['ref11'], max(hk2.ref11.values()))
                nr['text'] = cx.dec(nr['ids'])
                nr['t2_token'] = nr['ids'][1]
            cells[cell] = {'C': {'M': M, 'M_all': Mall, 't2_sha': F.th(zc)}, 'N': nr}
        out[pname] = cells
    return out


def S1_of(c1, G):
    return {l: L._get(c1.layers[l], 'recurrent_states').clone() for l in G}


def l_chain(cx, bT, bV, cconv, vec, sign, tag, need_refs=True):
    """LVK endpoints L00..L11 on bT (+ engineering refs and the full-layer t1 bridge to V / VW) and the SRU D/E reads L10 <-> L11."""
    G, types = cx.G, L.layer_types(cx.model)
    res, c1, z1, zc, z2 = {}, {}, {}, {}, {}
    c1['L00'], z1['L00'] = arm(cx, bT)
    for code in ('01', '10', '11'):
        hk = LHook(cx.model, G, 'cell', a=int(code[0]), b=int(code[1]), vec=vec, sign=sign, cconv=cconv)
        c1[f'L{code}'], z1[f'L{code}'] = arm(cx, bT, hk)
    for nm in ('L00', 'L01', 'L10', 'L11'):
        res[nm], zc[nm], z2[nm] = finish(cx, c1[nm], z1[nm], f'{tag}|{nm}')
    if need_refs:
        cn, zn = arm(cx, bT, UHook(cx.model, G, 'noop'), kind='refs')
        assert bit_equal(zn, z1['L00'])[0] and cache_equal(cn, c1['L00'], types, G)[0], 'no-op custom != native (T)'
        cn, zn = arm(cx, bT, LHook(cx.model, G, 'ref_v', cconv=cconv), kind='refs')
        assert bit_equal(zn, z1['L10'])[0] and cache_equal(cn, c1['L10'], types, G)[0], 'L10 != original kernel fed v1'
        cV, zV = arm(cx, bV, kind='refs')
        hk = UHook(cx.model, G, 'cell', code='01', vec=vec, sign=sign)
        cVW, zVW = arm(cx, bV, hk, kind='refs')
        cx.acc['oracle'] = max(cx.acc['oracle'], max(hk.oracle.values()))
        for nm, (cc, zz) in (('L10', (cV, zV)), ('L11', (cVW, zVW))):
            ok1, _ = bit_equal(z1[nm], zz)
            ok2, _, nm_, fail = cache_equal_vmask(c1[nm], cc, types, G)
            assert ok1 and ok2, ('t1 bridge to V background failed', nm, fail)
            cx.acc['vmask'] += nm_
    S1 = {nm: S1_of(c1[nm], G) for nm in ('L10', 'L11')}
    x = {nm: res[nm]['x'] for nm in res}
    refs00(cx, c1['L10'], x['L10'], zc['L10'], z2['L10'], S1['L11'])
    refs00(cx, c1['L11'], x['L11'], zc['L11'], z2['L11'], S1['L10'])
    rd = reads(cx, c1, S1, x, {'gain': ('L10', 'L11'), 'withdraw': ('L11', 'L10')}, f'{tag}|mu')
    return res, rd, c1, z1, zc, z2, S1


def run_item(engine, unit, contexts, calib, conds, qctok, output, stage, vecs=None, refs=None):
    import torch
    model = engine.model
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
    assert tuple(G) == (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30) and G[0] == LAYER0
    assert tuple(STOP) == tuple(CFK.STOP) == tuple(engine.stop_ids)
    KRDR.QHOOK_ORIG[0] = gdn_module().torch_recurrent_gated_delta_rule
    kind, a = unit['kind'], unit['item_id']
    counts = {k: 0 for k in COUNT_KEYS + ('calibrations',)}
    tensors, gates, out = {}, {}, {}
    acc = {'oracle': 0.0, 'ref11': 0.0, 'vmask': 0, 'rot_cos_err': 0.0, 'rot_norm_err': 0.0}
    if kind == 'collect':
        C, T, au = form_old_l12(engine, a, contexts, calib, counts)
        tensors['qk'] = {'C': QCOR.qk_tensor(C, G), f'T|{L12}': QCOR.qk_tensor(T, G)}
        gates['collect'] = 'base and C hashes == QCD G; L12 write audit passed; q/k conv slots of the 14 G layers saved'
        body = {'kind': kind, 'text': a, 'scenario': unit['base_id'], 'write_audit': au, 'qk_sha': {k: L.tensor_hash(v) for k, v in tensors['qk'].items()},
                'counts': counts, 'gates': gates, 'calibration': calib}
        return body, tensors
    if kind == 'calib':
        F.assert_no_hooks(model)
        cal = engine.calibrate([contexts[a]])[0]
        counts['calibrations'] += 1
        gates['calib'] = 'engine.calibrate on the scenario self-reference context (same algorithm as NQ-01)'
        return {'kind': kind, 'text': a, 'scenario': unit['base_id'], 'calibration_result': cal, 'counts': counts, 'gates': gates}, tensors
    u_rand = refs['u']
    if kind in ('g1', 'g3c', 'bridge'):
        led = refs['ledger'][a]
    else:
        led = refs['g2'][a]
    if kind == 'g1':
        cds = {L12: L12_COND}
    elif kind == 'g2':
        cds = {d: conds[d] for d in L0_DIRS}
    elif kind == 'bridge':
        cds = {'N_L00_C4146_D-1': conds['N_L00_C4146_D-1']}
    else:
        cds = {}
    C, T, info = form_new(engine, led, contexts, calib, cds, counts)
    hC, hT = comp_sha(C, types, ALLK, 0), {d: comp_sha(T[d], types, ALLK, 0) for d in cds}
    fF = led['tokens']['q_shared']
    assert fF not in STOP
    cx = Ctx(engine, G, info, fF, counts, tensors, acc)
    s = info['scenario']
    cconv = {l: L._get(C.layers[l], 'conv_states').clone() for l in G}
    if kind in ('g1', 'g2', 'bridge'):
        if kind == 'g1':
            res, zcC, _ = finish(cx, *arm(cx, C), 'C')
            out['C'] = res
        if kind == 'g2':
            res, _, _ = finish(cx, *arm(cx, C), 'C')
            out['C'] = res
        for d in cds:
            if kind == 'g1':
                vec = QKFR.mask_vec(refs['l12_mu'][f'{s}|{L12}'].float(), 'k')
            elif kind == 'g2':
                vec = QKFR.mask_vec(refs['g2_mu'][d].float(), 'k')
            else:
                vec = QKFR.mask_vec(vecs['mu'][f'{s}|{d}'].float(), 'k')
            sign = ARMS_ALL['Rk'][2]
            bT, _ = QKFR.edited_arm(T[d], T[d], T[d], G, None, 1)
            check_bg(bT, T[d], C, types, G, 'T', 'T')
            bV, _ = QKFR.edited_arm(T[d], T[d], C, G, None, 1)
            hb = comp_sha(bT, types, ALLK, 0)
            res, rd, c1, z1, zc, z2, S1 = l_chain(cx, bT, bV, cconv, vec, sign, d, need_refs=(kind != 'bridge'))
            dres = {'endpoints': res, 'reads': {'mu': rd}}
            if kind == 'g2' and s == 'GS01' and d == 'N_L00_C4146_D-1':
                for code, aa in (('R01', 0), ('R11', 1)):
                    hk = RotHook(model, G, aa, vec, sign, cconv, u_rand)
                    c1[code], z1[code] = arm(cx, bT, hk)
                    acc['rot_cos_err'] = max(acc['rot_cos_err'], max(v['cos_err_max'] for v in hk.rot.values()))
                    acc['rot_norm_err'] = max(acc['rot_norm_err'], max(v['norm_err_max'] for v in hk.rot.values()))
                    dres.setdefault('rotation', {})[code] = {str(l): v for l, v in hk.rot.items()}
                    res[code], zc[code], z2[code] = finish(cx, c1[code], z1[code], f'{d}|{code}')
                S1['R11'] = S1_of(c1['R11'], G)
                x = {nm: res[nm]['x'] for nm in res}
                refs00(cx, c1['R11'], x['R11'], zc['R11'], z2['R11'], S1['L10'])
                dres['reads']['rand'] = reads(cx, c1, S1, x, {'gain': ('L10', 'R11'), 'withdraw': ('R11', 'L10')}, f'{d}|rand')
            if kind == 'bridge':
                sr = refs['sru'][a]['directions'][d]
                for nm in ('L10', 'L11'):
                    assert res[nm]['x'] == sr['x'][nm]
                for pname in ('gain', 'withdraw'):
                    for cell in CELLS:
                        mine, old = rd[pname][cell], sr['pairs'][pname][cell]
                        assert mine['C']['M'] == old['C']['M'] and mine['N']['ids'] == old['N']['ids'], ('bridge != SRU', pname, cell)
                    r00 = 'L10' if pname == 'gain' else 'L11'
                    assert res[r00]['C']['M'] == sr['pairs'][pname]['00']['C']['M'] and res[r00]['N']['ids'] == sr['pairs'][pname]['00']['N']['ids']
                gates['sru_bridge'] = 'L10/L11 endpoints and gain/withdraw cells 10/01/11 (C margin and natural tokens) == SRU-01 formal record'
            assert comp_sha(bT, types, ALLK, 0) == hb
            out[d] = dres
            del c1, S1, bT, bV
            torch.cuda.empty_cache()
    else:   # g3c: clean background challenge
        c0, z0 = arm(cx, C)
        res0, zc0, z20 = finish(cx, c0, z0, 'A0')
        cn, zn = arm(cx, C, UHook(model, G, 'noop'), kind='refs')
        assert bit_equal(zn, z0)[0] and cache_equal(cn, c0, types, G)[0], 'no-op custom != native (C)'
        S0 = S1_of(c0, G)
        refs00(cx, c0, res0['x'], zc0, z20, S0)
        out['A0'] = res0
        for d in L0_DIRS:
            vec = QKFR.mask_vec(vecs['mu'][f'{s}|{d}'].float(), 'k')
            sign = ARMS_ALL['Ak'][2]
            c1, z1, zc, z2, res = {'A0': c0}, {'A0': z0}, {'A0': zc0}, {'A0': z20}, {'A0': res0}
            hk = LHook(model, G, 'cell', a=0, b=1, vec=vec, sign=sign, cconv=cconv)
            c1['Amu'], z1['Amu'] = arm(cx, C, hk)
            hk = RotHook(model, G, 0, vec, sign, cconv, u_rand)
            c1['AR'], z1['AR'] = arm(cx, C, hk)
            acc['rot_cos_err'] = max(acc['rot_cos_err'], max(v['cos_err_max'] for v in hk.rot.values()))
            acc['rot_norm_err'] = max(acc['rot_norm_err'], max(v['norm_err_max'] for v in hk.rot.values()))
            for nm in ('Amu', 'AR'):
                res[nm], zc[nm], z2[nm] = finish(cx, c1[nm], z1[nm], f'{d}|{nm}')
            S1 = {nm: S1_of(c1[nm], G) for nm in ('Amu', 'AR')}
            S1['A0'] = S0
            x = {nm: res[nm]['x'] for nm in res}
            for nm in ('Amu', 'AR'):
                refs00(cx, c1[nm], x[nm], zc[nm], z2[nm], S0)
            rd = {'mu': reads(cx, c1, S1, x, {'apply': ('A0', 'Amu'), 'undo': ('Amu', 'A0')}, f'{d}|mu'),
                  'rand': reads(cx, c1, S1, x, {'apply': ('A0', 'AR'), 'undo': ('AR', 'A0')}, f'{d}|rand')}
            out[d] = {'endpoints': {k: v for k, v in res.items() if k != 'A0'}, 'reads': rd, 'rotation': {str(l): v for l, v in hk.rot.items()}}
            del c1, S1
            torch.cuda.empty_cache()
    assert hC == comp_sha(C, types, ALLK, 0) and all(comp_sha(T[d], types, ALLK, 0) == hT[d] for d in cds), 'donor modified'
    F.assert_no_hooks(model)
    if acc['oracle']:
        assert acc['oracle'] <= KUCR.ORACLE_TOL
    assert acc['ref11'] <= KUCR.ORACLE_TOL
    gates['sources'] = 'held-out / new-scenario tokens == frozen ledgers; formation recorded; C/T donors unchanged'
    gates['hooks'] = 't1 write hooks and t2 read hooks fire once per G layer; module functions restored; no hook from t3'
    gates['oracle'] = f'selective write and read updates vs FP64 formula, max relative error {acc["oracle"]:.3g}; cell 11 vs original fed Sd {acc["ref11"]:.3g}'
    gates['refs'] = 'no-op custom == native at t1; a=b=0 read hook == native at t2 (C and N routes)'
    if kind in ('g1', 'g2'):
        gates['bridge_t1'] = 'L10 == V and L11 == VW at t1 except G conv V old slots (full-layer)'
    if acc['rot_cos_err'] or kind == 'g3c' or (kind == 'g2' and s == 'GS01'):
        gates['rotation'] = f'same-angle random rotation: max |cos realised - target| {acc["rot_cos_err"]:.3g}, max norm error {acc["rot_norm_err"]:.3g} <= {ROT_TOL}'
    gates['calibration'] = 'NQ-01 scenario calibration (old scenarios) / prep self-reference calibration (new scenarios)'
    body = {'kind': kind, 'text': a, 'scenario': s, 'item': info['item'], 'code_tokens': info['code_tokens'], 'fF': fF, 'directions': out,
            'formation_hashes': info.get('hashes'), 'acc': acc, 'kernel_identity': kernel_identity(), 'calibration': calib, 'counts': counts, 'gates': gates}
    return body, tensors




def SRUR_records():
    out = {}
    for w in sorted(SRU_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        for rel, dg in r['record_hashes'].items():
            assert exp.sha(w / rel) == dg, 'SRU record hash'
            rec = exp.read(w / rel)
            out[rec['text']] = rec
    return out


def load_vectors():
    return SRUR.load_vectors()


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', DESIGN, QC_INPUTS, QC_TOKENS, HELDOUT, LEDGER, G2_LEDGER, G2_MU, RAND_U, ASSETS,
         SRU_DIR / 'sru_run.py', SRU_DIR / 'freeze-r01.json', SRU_DIR / 'analysis/sru-readouts-r01.json', LVK_DIR / 'lvk_run.py', LVK_DIR / 'freeze-r01.json',
         NVW_DIR / 'nvw_run.py', KUC_DIR / 'kuc_run.py', KRD_DIR / 'krd_run.py', QSR_DIR / 'qsr_run.py', QKD_DIR / 'qkd_run.py', QKDR.RPOST_C_MANIFEST,
         QKF_DIR / 'qkf_run.py', QKFR.RPOST_MANIFEST, QCO_DIR / 'qco_run.py', QCO_DIR / 'qco_offsets.py', QKFR.QCO_MANIFEST, QST_DIR / 'qst_core.py',
         SVQ_DIR / 'svq_run.py', FC_DIR / 'fc_core.py'] + PLAN_DOCS
    b3 = [w / 'receipt.json' for w in sorted(B3_FORMAL.glob('worker-*')) if w.is_dir()] + [B3_FORMAL / 'verification.json']
    xc = [w / 'receipt.json' for w in sorted(XC_FORMAL.glob('worker-*')) if w.is_dir()] + [XC_FORMAL / 'verification.json']
    sk = [w / 'receipt.json' for w in sorted(SK_FORMAL.glob('worker-*')) if w.is_dir()] + [SK_FORMAL / 'verification.json']
    nr = [w / 'receipt.json' for w in sorted(NR_FORMAL.glob('worker-*')) if w.is_dir()] + [NR_FORMAL / 'verification.json']
    sp = [w / 'receipt.json' for w in sorted(SP_FORMAL.glob('worker-*')) if w.is_dir()] + [SP_FORMAL / 'verification.json']
    sp += [w / f'calibrations/{c.name}' for w in sorted(SP_FORMAL.glob('worker-*')) if w.is_dir() for c in sorted((w / 'calibrations').glob('*.json'))]
    svq = [w / 'receipt.json' for w in sorted(SVQ_FORMAL.glob('worker-*')) if w.is_dir()] + [SVQ_FORMAL / 'verification.json']
    nq = [w / 'receipt.json' for w in sorted(NQ_FORMAL.glob('worker-*')) if w.is_dir()] + [NQ_FORMAL / 'verification.json']
    nq += [w / f'calibrations/{c.name}' for w in sorted(NQ_FORMAL.glob('worker-*')) if w.is_dir() for c in sorted((w / 'calibrations').glob('*.json'))]
    qcd = [w / 'receipt.json' for w in sorted(QCD_G.glob('worker-*')) if w.is_dir()] + [QCD_G / 'verification.json']
    qst = [w / 'receipt.json' for w in sorted(QST_FORMAL.glob('worker-*')) if w.is_dir()] + [QST_FORMAL / 'verification.json']
    qco = [w / 'receipt.json' for w in sorted(QCO_FORMAL.glob('worker-*')) if w.is_dir()] + [QCO_FORMAL / 'verification.json']
    qkf = [w / 'receipt.json' for w in sorted(QKF_FORMAL.glob('worker-*')) if w.is_dir()] + [QKF_FORMAL / 'verification.json']
    qkd = [w / 'receipt.json' for w in sorted(QKD_FORMAL.glob('worker-*')) if w.is_dir()] + [QKD_FORMAL / 'verification.json'] + [w / 'receipt.json' for w in sorted(QKD_PRE.glob('worker-*')) if w.is_dir()]
    qsr = [w / 'receipt.json' for w in sorted(QSR_FORMAL.glob('worker-*')) if w.is_dir()] + [QSR_FORMAL / 'verification.json']
    krd = [w / 'receipt.json' for w in sorted(KRD_FORMAL.glob('worker-*')) if w.is_dir()] + [KRD_FORMAL / 'verification.json']
    krd += [w / 'receipt.json' for w in sorted(KUC_FORMAL.glob('worker-*')) if w.is_dir()] + [KUC_FORMAL / 'verification.json']
    krd += [w / 'receipt.json' for w in sorted(NVW_FORMAL.glob('worker-*')) if w.is_dir()] + [NVW_FORMAL / 'verification.json']
    krd += [w / 'receipt.json' for w in sorted(LVK_FORMAL.glob('worker-*')) if w.is_dir()] + [LVK_FORMAL / 'verification.json']
    krd += [w / 'receipt.json' for w in sorted(SRU_FORMAL.glob('worker-*')) if w.is_dir()] + [SRU_FORMAL / 'verification.json']
    return own + b3 + xc + sk + nr + sp + svq + nq + qcd + qst + qco + qkf + qkd + qsr + krd + [p for p in B3R.frozen_paths() if p not in own]


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
    assets()
    if stage in ('preflight', 'formal'):
        prep_assets()
        assert auth['required_evidence'].get('data/prep-manifest-r01.json') == exp.sha(PREP_MAN), 'prep manifest not in evidence'
    if stage == 'formal':
        pre = exp.read(HERE / auth['preflight_verification_path'])
        assert pre['status'] == 'passed' and pre['freeze_sha256'] == auth['freeze_sha256'] and pre['stage'] == 'preflight'
        ex = extrapolate(HERE / Path(auth['preflight_verification_path']).parent)
        assert ex['device_seconds'] <= GPU_CAP_S['formal'] and ex['bytes'] <= STORAGE_LIMIT, ('preflight extrapolation exceeds the formal cap', ex)
    return auth


def extrapolate(pre_root):
    """Formal estimate (reported, not a budget gate): mean preflight seconds per unit kind x formal unit counts + 2 model loads; bytes likewise."""
    ws = [w for w in sorted(Path(pre_root).glob('worker-*')) if w.is_dir()]
    assert len(ws) == 1
    r = exp.read(ws[0] / 'receipt.json')
    recs = [exp.read(ws[0] / rel) for rel in r['record_hashes']]
    load = r['wall_seconds'] - sum(x['seconds'] for x in recs)
    per, by = {}, {}
    for x in recs:
        per.setdefault(x['kind'], []).append(x['seconds'])
        by.setdefault(x['kind'], []).append((ws[0] / x['tensor_file']).stat().st_size)
    n = {}
    for u in units_for('formal'):
        n[u['kind']] = n.get(u['kind'], 0) + 1
    dev = sum(sum(per[k]) / len(per[k]) * c for k, c in n.items()) + 2 * load
    byt = sum(sum(by[k]) / len(by[k]) * c for k, c in n.items())
    return {'per_kind_seconds': {k: sum(v) / len(v) for k, v in per.items()}, 'formal_units': n, 'load_seconds': load, 'device_seconds': dev, 'bytes': byt}


def check_limits(counts, stage):
    lim = limits(stage)
    assert all(counts[k] <= lim[k] for k in lim), (counts, lim)


def execute(engine, stage, output, receipt, units, gpu):
    qi = QCDR.qc_items()
    contexts = exp.contexts_for(engine.tokenizer, [qi[t['plan']['qc_broad_id']] for t in items()])
    contexts.update(exp.contexts_for(engine.tokenizer, [v['item'] for v in ledger().values()]))
    contexts.update(exp.contexts_for(engine.tokenizer, [v['item'] for v in g2_ledger().values()]))
    conds = conditions()
    receipt['kernel_identity'] = T1.kernel_identity()
    assert list(engine.stop_ids) == list(CFK.STOP)
    F.hook_baseline(engine.model)
    import torch
    totals = {k: 0 for k in COUNT_KEYS + ('calibrations',)}
    calib = {}
    qctok = exp.read(QC_TOKENS)
    vecs = load_vectors()
    refs = {'ledger': ledger(), 'g2': g2_ledger()}
    assets()
    refs['u'] = torch.load(RAND_U, map_location='cpu')['u']
    refs['g2_mu'] = torch.load(G2_MU, map_location='cpu')['mu_all']
    if stage in ('preflight', 'formal'):
        refs['l12_mu'], refs['gen_calib'] = prep_assets()
    if stage == 'preflight':
        refs['sru'] = SRUR_records()
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
        if u['kind'] == 'calib':
            cu = None
        elif u['kind'] == 'g2':
            cu = refs['gen_calib'][f"GEN-{u['base_id']}-ABC-A"]
            receipt.setdefault('calibration_sources', {})[u['base_id']] = 'prep:' + exp.sha(GEN_CALIB)
        else:
            rid = f"{u['base_id']}-ABC-A"
            if rid not in calib:
                calib[rid], csha = QCR.nq_calibration(rid)
                receipt.setdefault('calibration_sources', {})[rid] = csha
            cu = calib[rid]
        body, tensors = run_item(engine, u, contexts, cu, conds, qctok, output, stage, vecs=vecs, refs=refs)
        for k in COUNT_KEYS + ('calibrations',):
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
    lock = open(f'/tmp/acupuncture-cgv-worker{worker}.lock', 'w')
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
        assert rec['kind'] == rec['unit']['kind']
        for g in ('collect',) if rec['kind'] == 'collect' else ('calib',) if rec['kind'] == 'calib' else ('sources', 'hooks', 'oracle', 'refs', 'calibration'):
            assert rec['gates'][g], g
        if rec['kind'] in ('g1', 'g2'):
            assert rec['gates']['bridge_t1']
        if rec['kind'] == 'g3c' or (rec['kind'] == 'g2' and rec['scenario'] == 'GS01'):
            assert rec['gates']['rotation']
        if rec['kind'] == 'bridge':
            assert rec['gates']['sru_bridge']
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
            cmd = [sys.executable, '-u', str(HERE / 'cgv_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
        assert units == len(units_for(stage)), units
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
