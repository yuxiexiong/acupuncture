"""SRU-01: how the t1 state difference between the LVK write endpoints L10 (local v1) and L11 (local v1 + write-term k1) becomes a target
advantage at t2 (plan docs/cache-state-read-use-plan-v1-2026-11-03.zh-CN.md; CONTRACT r01).  New panel (48 held-out texts), 4 directions.
Ordered pairs: gain (receiver L10, donor L11) and withdraw (receiver L11, donor L10).  Cells ab at t2 in the 14 G layers only:
o2_ab = o2 + a * alpha (Sd - Sr)^T q - b * alpha beta (k^T q) (Sd - Sr)^T k, added in FP32 before the cast; returned S2 is the receiver's native
update.  q/k/v/alpha/beta are the current branch's own.  Sr / Sd are the post-t1 recurrent states of the original endpoints.
python sru_run.py freeze PATH | run ... | verify WORKER_DIR | launch ..."""
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
LVK_DIR = HERE.parent / 'cache-local-v-k-v1-2026-11-03'
sys.path.insert(0, str(LVK_DIR))
sys.path.insert(0, str(HERE))
import lvk_run as LVKR  # noqa: E402  (frozen LVK-01 runner)

NVR, KUCR, KRDR, QSRR, QKDR = LVKR.NVR, LVKR.KUCR, LVKR.KRDR, LVKR.QSRR, LVKR.QKDR
QKFR, QCOR, QSTR, QCDR, QCR, NQR, SVQ, NRR = LVKR.QKFR, LVKR.QCOR, LVKR.QSTR, LVKR.QCDR, LVKR.QCR, LVKR.NQR, LVKR.SVQ, LVKR.NRR
FC_DIR, SP_DIR, SVQ_DIR, NQ_DIR, QC_DIR, QCD_DIR, QST_DIR, QCO_DIR, QKF_DIR = LVKR.FC_DIR, LVKR.SP_DIR, LVKR.SVQ_DIR, LVKR.NQ_DIR, LVKR.QC_DIR, LVKR.QCD_DIR, LVKR.QST_DIR, LVKR.QCO_DIR, LVKR.QKF_DIR
QKD_DIR, QKD_FORMAL, QKD_PRE, QSR_DIR, QSR_FORMAL = LVKR.QKD_DIR, LVKR.QKD_FORMAL, LVKR.QKD_PRE, LVKR.QSR_DIR, LVKR.QSR_FORMAL
KRD_DIR, KHC_DIR, KRD_FORMAL, KUC_DIR, KUC_FORMAL, NVW_DIR, NVW_FORMAL = LVKR.KRD_DIR, LVKR.KHC_DIR, LVKR.KRD_FORMAL, LVKR.KUC_DIR, LVKR.KUC_FORMAL, LVKR.NVW_DIR, LVKR.NVW_FORMAL
LVK_FORMAL = LVK_DIR / 'runs/formal-r01'
B3R, V, P, PK, X = LVKR.B3R, LVKR.V, LVKR.P, LVKR.PK, LVKR.X
CF, CFK, LR, B = LVKR.CF, LVKR.CFK, LVKR.LR, LVKR.B
F, L, T1, exp, K = LVKR.F, LVKR.L, LVKR.T1, LVKR.exp, LVKR.K

PLAN_ID = 'SRU-01-STATE-READ-USE-v1'
PLAN_DOCS = [REPO / 'docs/cache-state-read-use-plan-v1-2026-11-03.zh-CN.md', REPO / 'docs/cache-state-read-use-self-check-v1-2026-11-03.zh-CN.md']
DESIGN, QC_INPUTS, QC_TOKENS, HELDOUT, LEDGER = LVKR.DESIGN, LVKR.QC_INPUTS, LVKR.QC_TOKENS, LVKR.HELDOUT, LVKR.LEDGER
QCD_G, QST_FORMAL, QCO_FORMAL, QKF_FORMAL = LVKR.QCD_G, LVKR.QST_FORMAL, LVKR.QCO_FORMAL, LVKR.QKF_FORMAL
QC_FORMAL, NQ_FORMAL, SVQ_FORMAL, SP_FORMAL, NR_FORMAL, B3_FORMAL, XC_FORMAL, SK_FORMAL = LVKR.QC_FORMAL, LVKR.NQ_FORMAL, LVKR.SVQ_FORMAL, LVKR.SP_FORMAL, LVKR.NR_FORMAL, LVKR.B3_FORMAL, LVKR.XC_FORMAL, LVKR.SK_FORMAL
SPLIT, A_LAYERS, MAX_NEW, STOP = LVKR.SPLIT, LVKR.A_LAYERS, LVKR.MAX_NEW, LVKR.STOP
DIRECTIONS, OLD_DIRS, NEW_DIR = LVKR.DIRECTIONS, LVKR.OLD_DIRS, LVKR.NEW_DIR
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
ARMS_ALL = LVKR.ARMS_ALL
LAYER0 = LVKR.LAYER0
PAIRS = {'gain': ('L10', 'L11'), 'withdraw': ('L11', 'L10')}     # name: (receiver, donor)
CELLS = ('00', '10', '01', '11')
ORACLE_TOL = 1e-5
PREFLIGHT_ITEMS = LVKR.NEW_PRE
LIMITS = {'preflight': {'formations': 10, 'prefix_prefills': 2, 'formation_token_forwards': 270, 't1': 16, 'refs': 64, 'n_steps': 64 * 31,
                        'c_t2': 64, 'decode_forwards': 16 + 64 + 64 * 31 + 64, 'trajectories': 64, 'shadow': 2 * 4 * 42, 'calibrations': 0},
          'formal': {'formations': 240, 'prefix_prefills': 48, 'formation_token_forwards': 6390, 't1': 384, 'refs': 1536, 'n_steps': 1536 * 31,
                     'c_t2': 1536, 'decode_forwards': 384 + 1536 + 1536 * 31 + 1536, 'trajectories': 1536, 'shadow': 48 * 4 * 42, 'calibrations': 0}}
GPU_CAP_S = {'preflight': 0.15 * 3600, 'formal': 1.2 * 3600}
STORAGE_LIMIT = 12 * 2 ** 30
ALLK = LVKR.ALLK
COUNT_KEYS = LVKR.COUNT_KEYS
comp_sha, tensor_bytes_sha = LVKR.comp_sha, LVKR.tensor_bytes_sha
gdn_module, kernel_identity, load_vectors, conditions, items = LVKR.gdn_module, LVKR.kernel_identity, LVKR.load_vectors, LVKR.conditions, LVKR.items
margins, natural, fwd, t1, t1L, LHook, form_new, ledger = LVKR.margins, LVKR.natural, LVKR.fwd, LVKR.t1, LVKR.t1L, LVKR.LHook, LVKR.form_new, LVKR.ledger
bit_equal, cache_equal, check_bg, first_step = LVKR.bit_equal, LVKR.cache_equal, LVKR.check_bg, LVKR.first_step


def plan(stage, worker, n_workers):
    rows = [r for r in LVKR.all_units() if r['panel'] == 'new']
    if stage == 'preflight':
        rows = [r for r in rows if r['item_id'] in PREFLIGHT_ITEMS]
        assert len(rows) == 2
        return rows
    bases = list(dict.fromkeys(r['base_id'] for r in rows))
    mine = {b for k, b in enumerate(bases) if k % n_workers == worker}
    return [r for r in rows if r['base_id'] in mine]


def lvk_records():
    out = {}
    for w in sorted(LVK_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        for rel, dg in r['record_hashes'].items():
            assert exp.sha(w / rel) == dg, 'LVK record hash'
            rec = exp.read(w / rel)
            if rec['panel'] != 'new':
                continue
            assert exp.sha(w / rec['tensor_file']) == r['tensor_hashes'][rec['tensor_file']], 'LVK tensor hash'
            rec['_tensor_path'] = str(w / rec['tensor_file'])
            out[rec['text']] = rec
    return out


def read_use(query, key, value, g, beta, S_r, S_d, a, b, l2norm, oracle=False):
    """Original torch_recurrent_gated_delta_rule order (decay, kv_mem, delta, update, read) with, at the output only, the receiver's old state
    replaced by the donor's in the direct-read term (a) and/or the correction term (b), added in FP32 before the cast.  Returns
    (out cast, native S2, pre-cast out FP32, stats, oracle error)."""
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
    stats, err = None, None
    if a or b:
        dS = S_d.to(v) - S_r.to(v)
        al = decay_t[..., 0, 0].unsqueeze(-1)                     # [B, H, 1]
        Dc = al * (dS * q_t.unsqueeze(-1)).sum(dim=-2)
        kq = (k_t * q_t).sum(-1, keepdim=True)
        Ec = -al * beta_t * kq * (dS * k_t.unsqueeze(-1)).sum(dim=-2)
        if a:
            o_t = o_t + Dc
        if b:
            o_t = o_t + Ec
        stats = torch.stack([Dc.norm(dim=-1)[0], Ec.norm(dim=-1)[0], (Dc * Ec).sum(-1)[0] / torch.clamp(Dc.norm(dim=-1)[0] * Ec.norm(dim=-1)[0], min=1e-30)], -1).float().cpu()
        if oracle:
            Sr, Sd = S_r.to(v).double(), S_d.to(v).double()
            ad, bd, qd, kd, vd = al.double(), beta_t.double(), q_t.double(), k_t.double(), v_t.double()
            kqd = (kd * qd).sum(-1, keepdim=True)
            Sa, Sb = (Sd if a else Sr), (Sd if b else Sr)
            oo = ad * (Sa * qd.unsqueeze(-1)).sum(-2) - ad * bd * kqd * (Sb * kd.unsqueeze(-1)).sum(-2) + bd * kqd * vd
            err = float((o_t.double() - oo).abs().max() / max(1.0, float(oo.abs().max())))
    out[:, :, 0] = o_t
    pre = out.clone()
    out = out.transpose(1, 2).contiguous().to(initial_dtype)
    return out, S, pre, stats, err


class RHook:
    """One t2 forward.  mode 'cell' (a, b, donor states Sd {layer: S1}) or 'capture' (record raw q / k per G layer).  For cell 11 additionally
    checks the local pre-cast output against the same replicated original order fed Sd (relative error <= 1e-5)."""

    def __init__(self, model, G, mode, a=0, b=0, Sd=None):
        assert mode in ('cell', 'capture')
        self.model, self.G, self.mode, self.a, self.b, self.Sd = model, tuple(G), mode, a, b, Sd
        self.QM = gdn_module()
        self.orig = self.QM.torch_recurrent_gated_delta_rule
        self.layer, self.handles, self.calls, self.oracle, self.ref11, self.stats, self.qk = None, [], [], {}, {}, {}, {}

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
            if me.mode == 'capture':
                me.qk[me.layer] = (query.detach().clone(), key.detach().clone())
                return me.orig(query, key, value, g=g, beta=beta, initial_state=initial_state, output_final_state=output_final_state,
                               use_qk_l2norm_in_kernel=use_qk_l2norm_in_kernel, **kw)
            Sd = me.Sd[me.layer]
            assert Sd.shape == initial_state.shape and Sd.dtype == initial_state.dtype
            out, S2, pre, st, err = read_use(query, key, value, g, beta, initial_state, Sd, me.a, me.b, me.QM.l2norm, oracle=bool(me.a or me.b))
            if st is not None:
                me.stats[me.layer] = st
                me.oracle[me.layer] = err
            if me.a and me.b:
                _, _, pre_ref, _, _ = read_use(query, key, value, g, beta, Sd, Sd, 0, 0, me.QM.l2norm)
                me.ref11[me.layer] = float((pre.double() - pre_ref.double()).abs().max() / max(1.0, float(pre_ref.double().abs().max())))
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
        if self.mode == 'cell' and (self.a or self.b):
            assert set(self.oracle) == set(self.G) and max(self.oracle.values()) <= ORACLE_TOL, ('FP64 oracle', max(self.oracle.values()))
        if self.mode == 'cell' and self.a and self.b:
            assert max(self.ref11.values()) <= ORACLE_TOL, ('11 vs replicated original fed Sd', max(self.ref11.values()))


def run_item(engine, unit, contexts, calib, conds, qctok, output, stage, vecs=None, refs=None):
    import torch
    model, tok = engine.model, engine.tokenizer
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
    assert tuple(G) == (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30) and G[0] == LAYER0
    assert tuple(STOP) == tuple(CFK.STOP) == tuple(engine.stop_ids)
    KRDR.QHOOK_ORIG[0] = gdn_module().torch_recurrent_gated_delta_rule
    a_id = unit['item_id']
    assert unit['panel'] == 'new'
    counts = {k: 0 for k in COUNT_KEYS}
    tensors, gates, out = {}, {}, {}
    nz_total, oracle_max, ref11_max = 0, 0.0, 0.0
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
    for d in conds:
        s = info['scenario']
        fF = led['tokens']['q_shared']
        _, u, sign = ARMS_ALL['Rk']
        vec = QKFR.mask_vec(vecs[u][f'{s}|{d}'].float(), 'k')
        bT, _ = QKFR.edited_arm(T[d], T[d], T[d], G, None, 1)
        check_bg(bT, T[d], C, types, G, 'T', 'T')
        hbT = comp_sha(bT, types, ALLK, 0)
        c1, z1, x, S1, h1 = {}, {}, {}, {}, {}
        for name, (aa, bb) in (('L10', (1, 0)), ('L11', (1, 1))):
            hk = LHook(model, G, 'cell', a=aa, b=bb, vec=vec, sign=sign, cconv=cconv)
            c1[name], z1[name] = t1L(engine, copy.deepcopy(bT), info['last'], n, counts, 't1', hk)
            lva = lv['directions'][d]['arms'][name]
            assert bit_equal(z1[name].to(torch.bfloat16).cpu(), lv_t[f't1|{name}|{d}'])[0], ('t1 != LVK', name, d)
            x[name] = int(z1[name].argmax())
            assert x[name] == lva['x'] == lva['N']['ids'][0]
            S1[name] = {l: L._get(c1[name].layers[l], 'recurrent_states').clone() for l in G}
            h1[name] = comp_sha(c1[name], types, ALLK, 0)
        qk = {}
        res = {}
        for pname, (r_, d_) in PAIRS.items():
            cells = {}
            for cell in CELLS:
                aa, bb = int(cell[0]), int(cell[1])
                # ---- C route
                if cell == '00':
                    hk = RHook(model, G, 'capture')
                    _, zc = fwd(engine, copy.deepcopy(c1[r_]), fF, n, counts, 'c_t2', hook=hk)
                    if pname == 'gain' or r_ not in qk:
                        qk[r_] = hk.qk
                    lva = lv['directions'][d]['arms'][r_]
                    assert bit_equal(zc.to(torch.bfloat16).cpu(), lv_t[f'C|{r_}|{d}'])[0], ('00 C t2 != LVK', r_, d)
                    hr = RHook(model, G, 'cell', a=0, b=0, Sd=S1[d_])
                    _, zr = fwd(engine, copy.deepcopy(c1[r_]), fF, n, counts, 'refs', hook=hr)
                    okz, z0 = bit_equal(zr, zc)
                    assert okz, ('replicated-order 00 hook != native t2 (C)', r_, d)
                    nz_total += z0
                else:
                    hk = RHook(model, G, 'cell', a=aa, b=bb, Sd=S1[d_])
                    _, zc = fwd(engine, copy.deepcopy(c1[r_]), fF, n, counts, 'c_t2', hook=hk)
                    oracle_max = max(oracle_max, max(hk.oracle.values()))
                    if hk.ref11:
                        ref11_max = max(ref11_max, max(hk.ref11.values()))
                    tensors[f'stats|{pname}|{cell}|{d}'] = torch.stack([hk.stats[l] for l in G])
                M, Mall = margins(zc, it, code_tok, comp)
                tensors[f'C|{pname}|{cell}|{d}'] = zc.to(torch.bfloat16).cpu()
                cr = {'M': M, 'M_all': Mall, 't2_sha': F.th(zc)}
                # ---- N route (receiver's own first token)
                xr = x[r_]
                if xr in STOP:
                    nr = {'ids': [xr], 'termination': 'stop', 'reached_t2': False, 'text': dec([xr])}
                else:
                    hook = None if cell == '00' else RHook(model, G, 'cell', a=aa, b=bb, Sd=S1[d_])
                    nr, z2 = natural(engine, copy.deepcopy(c1[r_]), xr, n, counts, hook=hook)
                    nr['text'] = dec(nr['ids'])
                    tensors[f'N|{pname}|{cell}|{d}'] = z2.to(torch.bfloat16)
                    if cell == '00':
                        lva = lv['directions'][d]['arms'][r_]
                        assert nr['ids'] == lva['N']['ids'] and nr['termination'] == lva['N']['termination'], ('00 natural != LVK', r_, d)
                        hr = RHook(model, G, 'cell', a=0, b=0, Sd=S1[d_])
                        _, zr = fwd(engine, copy.deepcopy(c1[r_]), xr, n, counts, 'refs', hook=hr)
                        okz, z0 = bit_equal(zr.detach().cpu(), z2)
                        assert okz, ('replicated-order 00 hook != native t2 (N)', r_, d)
                    elif hook.ref11:
                        ref11_max = max(ref11_max, max(hook.ref11.values()))
                    if cell != '00':
                        oracle_max = max(oracle_max, max(hook.oracle.values()))
                    nr['t2_token'] = nr['ids'][1]
                cells[cell] = {'C': cr, 'N': nr}
            res[pname] = cells
        # q/k agreement at t2 (C route, same input token) between the two endpoints, per layer: median over heads of cos
        def cosm(u_, w_):
            uu, ww = u_.float().reshape(-1, u_.shape[-1]), w_.float().reshape(-1, w_.shape[-1])
            return float(torch.nn.functional.cosine_similarity(uu, ww, dim=-1).median())
        qk_cos = {str(l): {'q': cosm(qk['L10'][l][0], qk['L11'][l][0]), 'k': cosm(qk['L10'][l][1], qk['L11'][l][1])} for l in G}
        for nme in ('L10', 'L11'):
            assert comp_sha(c1[nme], types, ALLK, 0) == h1[nme], ('post-t1 source cache modified', nme, d)
        assert comp_sha(bT, types, ALLK, 0) == hbT
        out[d] = {'fF': fF, 'x': x, 'pairs': res, 'qk_cos_t2': qk_cos,
                  'target_second_token': code_tok[it['target']]}
        del c1, S1, bT
        torch.cuda.empty_cache()
    assert hC == comp_sha(C, types, ALLK, 0) and all(comp_sha(T[d], types, ALLK, 0) == hT[d] for d in conds), 'donor modified'
    F.assert_no_hooks(model)
    gates['sources'] = 'formation hashes == LVK; L10/L11 t1 bf16 logits and first token == LVK; post-t1 sources unchanged'
    gates['replay'] = '00 cells: C t2 bf16 logits == LVK, natural tokens == LVK; replicated-order hook with a=b=0 == native t2 (C, N)'
    gates['oracle'] = f'cells 10/01/11 local output vs FP64 formula, max relative error {oracle_max:.3g} <= {ORACLE_TOL}'
    gates['ref11'] = f'cell 11 local pre-cast output vs replicated original order fed Sd, max relative error {ref11_max:.3g} <= {ORACLE_TOL}'
    gates['hooks'] = 't1 only LVK shadow hooks; t2 read hook fires once per G layer; t3 onward no hook; module functions restored'
    gates['calibration'] = 'NQ-01 saved scenario calibration (source hash in receipt)'
    body = {'text': a_id, 'panel': 'new', 'scenario': info['scenario'], 'item': it, 'code_tokens': code_tok, 'competitor': comp, 'directions': out,
            'signed_zero_exceptions': nz_total, 'oracle_max': oracle_max, 'ref11_max': ref11_max, 'kernel_identity': kernel_identity(),
            'calibration': calib, 'counts': counts, 'gates': gates}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', DESIGN, QC_INPUTS, QC_TOKENS, HELDOUT, LEDGER,
         HERE.parent / 'cache-state-read-use-design-v1-2026-11-03/cpu-design-audit-r01.json', LVK_DIR / 'lvk_run.py', LVK_DIR / 'freeze-r01.json',
         LVK_DIR / 'analysis/lvk-readouts-r01.json', NVW_DIR / 'nvw_run.py', KUC_DIR / 'kuc_run.py', KRD_DIR / 'krd_run.py', QSR_DIR / 'qsr_run.py',
         QKD_DIR / 'qkd_run.py', QKDR.RPOST_C_MANIFEST, QKF_DIR / 'qkf_run.py', QKFR.RPOST_MANIFEST, QCO_DIR / 'qco_run.py', QKFR.QCO_MANIFEST,
         QST_DIR / 'qst_core.py', SVQ_DIR / 'svq_run.py', FC_DIR / 'fc_core.py'] + PLAN_DOCS
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
    refs = {'lvk': lvk_records(), 'ledger': ledger()}
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
    lock = open(f'/tmp/acupuncture-sru-worker{worker}.lock', 'w')
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
        assert set(rec['directions']) == set(DIRECTIONS)
        for d in DIRECTIONS:
            assert set(rec['directions'][d]['pairs']) == set(PAIRS) and all(set(v) == set(CELLS) for v in rec['directions'][d]['pairs'].values())
        for g in ('sources', 'replay', 'oracle', 'ref11', 'hooks', 'calibration'):
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
            cmd = [sys.executable, '-u', str(HERE / 'sru_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
