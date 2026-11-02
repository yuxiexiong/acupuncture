"""KRD-01: conditional dependence of the k repair on the post-t1 history pack H (G recurrent S + A attention KV) and the t2 G-layer
query node Q (plan docs/cache-k-repair-dependence-plan-v1-2026-11-03.zh-CN.md; CONTRACT r01).
Six QKD arms per (input, direction); t1 per arm; ordered pairs r<-d over (Rk,V) (Ak,F) (Rrk,V) (Ark,F) in both receiving directions;
cells hq in {00, 10, 01, 11}: H from d if h, else r; Q at t2 (all 14 G layers, kernel-entry `query`) from the ORIGINAL endpoint d if q,
else r.  Convolution buffers, current k/v/gates and everything else stay the receiver's and respond normally.
C route: t2 input = old F first token (QKD/QSR diagnostic), full t2 logits.  N route: t2 input = the receiver's own natural first token
x_r; donor Q captured on d's post-t1 cache with x_r; natural greedy continuation to stop or 32 new tokens (incl. x_r); Q clamped at t2 only.
python krd_run.py freeze PATH | run ... | verify WORKER_DIR | launch ..."""
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
QSR_DIR = HERE.parent / 'cache-state-readout-decomposition-v1-2026-11-03'
sys.path.insert(0, str(QSR_DIR))
sys.path.insert(0, str(HERE))
import qsr_run as QSRR  # noqa: E402  (frozen QSR-01 runner; itself imports the frozen QKD-01 runner)

QKDR = QSRR.QKDR
QKFR, QCOR, QSTR, QCDR, QCR, NQR, SVQ, NRR = QSRR.QKFR, QSRR.QCOR, QSRR.QSTR, QSRR.QCDR, QSRR.QCR, QSRR.NQR, QSRR.SVQ, QSRR.NRR
FC_DIR, SP_DIR, SVQ_DIR, NQ_DIR, QC_DIR, QCD_DIR, QST_DIR, QCO_DIR, QKF_DIR = QSRR.FC_DIR, QSRR.SP_DIR, QSRR.SVQ_DIR, QSRR.NQ_DIR, QSRR.QC_DIR, QSRR.QCD_DIR, QSRR.QST_DIR, QSRR.QCO_DIR, QSRR.QKF_DIR
QKD_DIR, QKD_FORMAL, QKD_PRE = QSRR.QKD_DIR, QSRR.QKD_FORMAL, QSRR.QKD_PRE
QSR_FORMAL = QSR_DIR / 'runs/formal-r01'
B3R, V, P, PK, X = QSRR.B3R, QSRR.V, QSRR.P, QSRR.PK, QSRR.X
CF, CFK, LR, B = QSRR.CF, QSRR.CFK, QSRR.LR, QSRR.B
F, L, T1, exp, K = QSRR.F, QSRR.L, QSRR.T1, QSRR.exp, QSRR.K

PLAN_ID = 'KRD-01-K-REPAIR-DEPENDENCE-v1'
PLAN_DOCS = [REPO / 'docs/cache-k-repair-dependence-plan-v1-2026-11-03.zh-CN.md', REPO / 'docs/cache-krd-self-check-v1-2026-11-03.zh-CN.md']
DESIGN, QC_INPUTS, QC_TOKENS = QSRR.DESIGN, QSRR.QC_INPUTS, QSRR.QC_TOKENS
QCD_G, QST_FORMAL, QCO_FORMAL, QKF_FORMAL = QSRR.QCD_G, QSRR.QST_FORMAL, QSRR.QCO_FORMAL, QSRR.QKF_FORMAL
QC_FORMAL, NQ_FORMAL, SVQ_FORMAL, SP_FORMAL, NR_FORMAL, B3_FORMAL, XC_FORMAL, SK_FORMAL = QSRR.QC_FORMAL, QSRR.NQ_FORMAL, QSRR.SVQ_FORMAL, QSRR.SP_FORMAL, QSRR.NR_FORMAL, QSRR.B3_FORMAL, QSRR.XC_FORMAL, QSRR.SK_FORMAL
SPLIT = 13
DIRECTIONS, OLD_DIRS, NEW_DIR = QSRR.DIRECTIONS, QSRR.OLD_DIRS, QSRR.NEW_DIR
STOP = QSRR.STOP
MAX_NEW = 32
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
ARMS, QKF_NAME = QSRR.ARMS, QSRR.QKF_NAME
A_LAYERS = (15, 19, 23, 27, 31)
UNORDERED = (('Rk', 'V'), ('Ak', 'F'), ('Rrk', 'V'), ('Ark', 'F'))
ORDERED = tuple(x for a, b in UNORDERED for x in ((a, b), (b, a)))          # (receiver, donor)
CELLS = ('10', '01', '11')
N_ENG = 2 * 4 * 6 * 2                                                          # preflight engineering forwards per text
LIMITS = {'preflight': {'formations': 10, 'prefix_prefills': 2, 'formation_token_forwards': 265, 't1': 48, 'c_t2': 240, 'n_steps': 7440,
                        'q_extra': 64, 'engineering': 96, 'decode_forwards': 7888, 'trajectories': 240, 'calibrations': 0},
          'formal': {'formations': 240, 'prefix_prefills': 48, 'formation_token_forwards': 6375, 't1': 1152, 'c_t2': 5760, 'n_steps': 178560,
                     'q_extra': 1536, 'engineering': 0, 'decode_forwards': 187008, 'trajectories': 5760, 'calibrations': 0}}
GPU_CAP_S = {'preflight': 0.25 * 3600, 'formal': 2.5 * 3600}
STORAGE_LIMIT = 20 * 2 ** 30
ALLK = ('recurrent', 'kv', 'conv')
COUNT_KEYS = ('formations', 'prefix_prefills', 'formation_token_forwards', 't1', 'c_t2', 'n_steps', 'q_extra', 'engineering',
              'decode_forwards', 'trajectories')
PREFLIGHT_ITEMS = QSRR.PREFLIGHT_ITEMS
comp_sha, comp_sha_range, tensor_bytes_sha = NRR.comp_sha, NRR.comp_sha_range, NRR.tensor_bytes_sha
gdn_module, kernel_identity, load_vectors, qkf_traj, conditions, items = QKDR.gdn_module, QKDR.kernel_identity, QKDR.load_vectors, QKDR.qkf_traj, QKDR.conditions, QKDR.items
qkd_records = QSRR.qkd_records


def plan(stage, worker, n_workers):
    return QKDR.plan(stage, worker, n_workers)


class QHook:
    """At one forward: capture (mode 'capture') or replace (mode 'replace', src {layer: tensor}) the `query` argument of the gated delta rule
    kernel in the G layers.  Records every G call; anything else passes through untouched."""

    def __init__(self, model, G, mode, src=None):
        assert mode in ('capture', 'replace')
        self.model, self.G, self.mode, self.src = model, tuple(G), mode, src
        self.QM = gdn_module()
        self.orig = self.QM.torch_recurrent_gated_delta_rule
        self.layer, self.handles, self.got, self.calls = None, [], {}, []

    def __enter__(self):
        assert self.QM.torch_recurrent_gated_delta_rule is self.orig
        for i, lay in enumerate(L.model_layers(self.model)):
            la = getattr(lay, 'linear_attn', None)
            if la is not None:
                def pre(_m, _a, i=i):
                    self.layer = i
                self.handles.append(la.register_forward_pre_hook(pre))
        orig, me = self.orig, self

        def wrapper(query, key, value, *a, **kw):
            if me.layer in me.G:
                assert query.shape[1] == 1, 'decode step expected'
                me.calls.append(me.layer)
                if me.mode == 'capture':
                    me.got[me.layer] = query.detach().clone()
                else:
                    s = me.src[me.layer]
                    assert s.shape == query.shape and s.dtype == query.dtype and s.device == query.device, ('Q source mismatch', me.layer)
                    query = s.clone()
                    me.got[me.layer] = query
            return orig(query, key, value, *a, **kw)
        self.QM.torch_recurrent_gated_delta_rule = wrapper
        return self

    def __exit__(self, *exc):
        self.QM.torch_recurrent_gated_delta_rule = self.orig
        for h in self.handles:
            h.remove()
        self.handles = []
        return False

    def check(self, src=None):
        assert sorted(self.calls) == sorted(self.G) and len(self.calls) == len(self.G), ('Q hook calls', self.calls)
        if self.mode == 'replace':
            assert all(QM_equal(self.got[l], self.src[l]) for l in self.G), 'effective Q != source'


def QM_equal(a, b):
    import torch
    return bool(torch.equal(a, b))


def fwd(engine, cache, tok, pos, counts, kind, hook=None):
    """One decode forward on `cache` (consumed).  Returns (cache, float logits)."""
    import torch
    F.assert_no_hooks(engine.model) if hook is None else None
    if hook is not None:
        with hook:
            with torch.inference_mode():
                out = L.forward(engine.model, [tok], pos, cache)
        hook.check()
    else:
        with torch.inference_mode():
            out = L.forward(engine.model, [tok], pos, cache)
    assert gdn_module().torch_recurrent_gated_delta_rule is QHOOK_ORIG[0], 'kernel wrapper left installed'
    F.assert_no_hooks(engine.model)
    counts['decode_forwards'] += 1
    counts[kind] += 1
    z = out.logits[0, -1].float()
    assert torch.isfinite(z).all()
    return out.past_key_values, z


QHOOK_ORIG = [None]


def swap_H(cr, cd, types, G):
    """Deep copy of receiver cache with G recurrent states and A-layer KV cloned from the donor cache; gates on prefixes and untouched parts."""
    import torch
    c = copy.deepcopy(cr)
    for l in G:
        assert types[l] == 'linear_attention'
        L._set(c.layers[l], 'recurrent_states', L._get(cd.layers[l], 'recurrent_states').clone())
    for l in A_LAYERS:
        assert types[l] == 'full_attention'
        for f in ('keys', 'values'):
            a, b = L._get(cr.layers[l], f), L._get(cd.layers[l], f)
            assert a.shape == b.shape, ('KV shape differs', l, f)
            assert torch.equal(a[..., :-1, :], b[..., :-1, :]), ('KV prefix differs between receiver and donor', l, f)
            L._set(c.layers[l], f, b.clone())
    hist = lambda cc: tensor_bytes_sha([L._get(cc.layers[l], 'recurrent_states') for l in G] +                    # noqa: E731
                                       [L._get(cc.layers[l], f) for l in A_LAYERS for f in ('keys', 'values')])
    rest = lambda cc: tensor_bytes_sha([L._get(cc.layers[i], f) for i, k, f in L.component_tensors(cc, types)       # noqa: E731
                                        if not ((k == 'recurrent' and i in G) or (k == 'kv' and i in A_LAYERS))])
    assert hist(c) == hist(cd) and rest(c) == rest(cr), 'H swap touched the wrong components'
    for l in G:
        assert L._get(c.layers[l], 'recurrent_states').data_ptr() != L._get(cd.layers[l], 'recurrent_states').data_ptr()
    return c


def margins(z, it, code_tok, comp):
    t = code_tok[it['target']]
    others = [code_tok[c] for c in it['listed_codes'] if c != it['target']]
    return float(z[t] - z[code_tok[comp]]), float(z[t] - max(float(z[o]) for o in others))


def natural(engine, cache, x, n, counts, hook=None, want_logits=True):
    """Greedy continuation after t1: ids starts with x (t1 output); at most MAX_NEW - 1 further forwards; hook only at t2."""
    import torch
    ids, z2, c = [x], None, cache
    if x in STOP:
        return {'ids': ids, 'termination': 'stop', 'reached_t2': False}, None
    for k in range(1, MAX_NEW):
        c, z = fwd(engine, c, ids[-1], n - 1 + k, counts, 'n_steps', hook=hook if k == 1 else None)
        if k == 1:
            z2 = z.detach().to('cpu').clone()
        t = int(z.argmax())
        ids.append(t)
        if t in STOP:
            break
    counts['trajectories'] += 1
    return {'ids': ids, 'termination': 'stop' if ids[-1] in STOP else 'budget', 'reached_t2': True, 't2_sha': F.th(z2)}, z2


def run_item(engine, unit, contexts, calib, conds, qctok, output, stage, vecs=None, refs=None):
    import torch
    model, tok = engine.model, engine.tokenizer
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
    assert tuple(G) == (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
    assert tuple(i for i, k in enumerate(types) if k == 'full_attention' and i >= SPLIT) == A_LAYERS
    QHOOK_ORIG[0] = gdn_module().torch_recurrent_gated_delta_rule
    a = unit['item_id']
    counts = {k: 0 for k in COUNT_KEYS}
    tensors, gates, out = {}, {}, {}
    C, T, info = QCOR.form_text(engine, a, contexts, calib, conds, qctok, counts)
    hC, hT = comp_sha(C, types, ALLK, 0), {d: comp_sha(T[d], types, ALLK, 0) for d in conds}
    it, code_tok, n = info['item'], info['code_tokens'], info['n']
    comp = it['first_listed'] if it['target'] != it['first_listed'] else it['listed_codes'][1]
    qkd = refs['qkd'][a]
    qkd_t = torch.load(qkd['_tensor_path'], map_location='cpu')
    dec = lambda ids: tok.decode(ids, skip_special_tokens=False)   # noqa: E731
    for d in conds:
        s = info['scenario']
        fF = (refs['qkf'][a][f'F|{d}']['ids'] if d in OLD_DIRS else refs['qco'][a][f'F|{d}']['ids'])[0]
        assert fF not in STOP
        c1, x, h1, ref, slots = {}, {}, {}, {}, {}
        for arm, (base, u, sign) in ARMS.items():
            qb = T[d] if base == 'T' else C
            vec = None if u is None else QKFR.mask_vec(vecs[u][f'{s}|{d}'].float(), 'k')
            cc, _ = QKFR.edited_arm(T[d], qb, C, G, vec, sign)
            QCOR.check_edit(T[d], qb, C, cc, types, G, vec is not None, f'{arm}|{d}')
            assert comp_sha_range(cc, types, ('recurrent', 'kv'), 0, 10 ** 9) == comp_sha_range(T[d], types, ('recurrent', 'kv'), 0, 10 ** 9)
            c1[arm], z1 = fwd(engine, cc, info['last'], n - 1, counts, 't1')
            ref[arm] = refs['qkf'][a][f'{QKF_NAME[arm]}|{d}'] if d in OLD_DIRS else qkd['c1343_trajectories'][arm]
            h1[arm] = comp_sha(c1[arm], types, ALLK, 0)
            assert F.th(z1) == ref[arm]['first']['logits_sha256'] and h1[arm] == ref[arm]['first']['cache_sha256'], ('t1 != reference', arm, d)
            x[arm] = int(z1.argmax())
            assert x[arm] == ref[arm]['ids'][0]
        shallow = {arm: comp_sha_range(c1[arm], types, ALLK, 0, SPLIT) for arm in ARMS}
        assert len(set(shallow.values())) == 1, 'shallow caches differ across arms after t1'
        for r_, d_ in (('Rk', 'V'), ('Ak', 'F')):          # descriptive: which conv slots carry a k difference after t1 (edit residue rolling)
            slots[f'{r_}-{d_}'] = [[int(j) for j in range(4) if not torch.equal(L._get(c1[r_].layers[l], 'conv_states')[0, 2048:4096, j],
                                                                               L._get(c1[d_].layers[l], 'conv_states')[0, 2048:4096, j])] for l in G]
        # ---- C route: 00 (capture own Q), replay vs QKD
        QC, M00 = {}, {}
        for arm in ARMS:
            hk = QHook(model, G, 'capture')
            _, z = fwd(engine, copy.deepcopy(c1[arm]), fF, n, counts, 'c_t2', hook=hk)
            QC[arm] = hk.got
            M, Mall = margins(z, it, code_tok, comp)
            assert M == qkd['arms'][d][arm]['M'], ('C t2 margin != QKD', arm, d)
            assert torch.equal(z.to(torch.bfloat16).cpu(), qkd_t[f'Ct2|{arm}|{d}']), ('C t2 logits != QKD', arm, d)
            M00[arm] = {'M': M, 'M_all': Mall, 't2_sha': F.th(z)}
            tensors[f'C|{arm}<-{arm}|00|{d}'] = z.to(torch.bfloat16).cpu()
            if stage == 'preflight':      # engineering: no-hook and self-replacement (+ self H) reproduce the capture forward bit for bit
                _, z0 = fwd(engine, copy.deepcopy(c1[arm]), fF, n, counts, 'engineering')
                hs = QHook(model, G, 'replace', QC[arm])
                _, zs = fwd(engine, swap_H(c1[arm], c1[arm], types, G), fF, n, counts, 'engineering', hook=hs)
                assert torch.equal(z0, z) and torch.equal(zs, z), ('self/no-hook C forward differs', arm, d)
        # ---- N route: 00 natural (capture own Q at t2 on own x), replay vs reference
        QN, N00 = {}, {}
        for arm in ARMS:
            hk = QHook(model, G, 'capture')
            r0, z2 = natural(engine, copy.deepcopy(c1[arm]), x[arm], n, counts, hook=hk)
            assert r0['ids'] == ref[arm]['ids'] and r0['termination'] == ref[arm]['termination'], ('N 00 != reference trajectory', arm, d)
            r0['text'] = dec(r0['ids'])
            if r0['reached_t2']:
                QN[(arm, x[arm])] = hk.got
                tensors[f'N|{arm}<-{arm}|00|{d}'] = z2.to(torch.bfloat16)
            N00[arm] = r0
        cells = {}
        for r_, d_ in ORDERED:
            # donor Q for the N route on the receiver's x
            if x[r_] not in STOP and (d_, x[r_]) not in QN:
                hk = QHook(model, G, 'capture')
                fwd(engine, copy.deepcopy(c1[d_]), x[r_], n, counts, 'q_extra', hook=hk)
                QN[(d_, x[r_])] = hk.got
            for hq in CELLS:
                h, q = hq[0] == '1', hq[1] == '1'
                base = swap_H(c1[r_], c1[d_], types, G) if h else copy.deepcopy(c1[r_])
                hk = QHook(model, G, 'replace', QC[d_ if q else r_])
                _, z = fwd(engine, copy.deepcopy(base), fF, n, counts, 'c_t2', hook=hk)
                M, Mall = margins(z, it, code_tok, comp)
                key = f'{r_}<-{d_}|{hq}'
                cell = {'C': {'M': M, 'M_all': Mall, 't2_sha': F.th(z)}}
                tensors[f'C|{key}|{d}'] = z.to(torch.bfloat16).cpu()
                if x[r_] in STOP:
                    cell['N'] = {'ids': [x[r_]], 'termination': 'stop', 'reached_t2': False, 'text': dec([x[r_]])}
                else:
                    hk = QHook(model, G, 'replace', QN[(d_ if q else r_, x[r_])])
                    rn, z2 = natural(engine, base, x[r_], n, counts, hook=hk)
                    rn['text'] = dec(rn['ids'])
                    cell['N'] = rn
                    tensors[f'N|{key}|{d}'] = z2.to(torch.bfloat16)
                cells[key] = cell
                del base
        for arm in ARMS:
            assert comp_sha(c1[arm], types, ALLK, 0) == h1[arm], ('source post-t1 cache modified', arm, d)
        out[d] = {'fF': fF, 'x': x, 'C00': M00, 'N00': N00, 'cells': cells, 'k_slot_diff_after_t1': slots,
                  'q_n_sources': sorted(f'{k[0]}|{k[1]}' for k in QN)}
        del c1, QC, QN
        torch.cuda.empty_cache()
    assert hC == comp_sha(C, types, ALLK, 0) and all(comp_sha(T[d], types, ALLK, 0) == hT[d] for d in conds), 'donor modified'
    F.assert_no_hooks(model)
    gates['replay'] = 't1 logits/cache == QKF/QKD; C 00 t2 margin and bf16 logits == QKD; N 00 trajectories == QKF/QKD ids and termination'
    gates['h_swap'] = 'G recurrent + A KV == donor, every other component == receiver, KV prefix equal, no shared storage'
    gates['q_node'] = 'Q hook fired exactly once per G layer on t2 only; effective kernel query == source; wrapper removed after each forward'
    gates['sources'] = 'post-t1 source caches unchanged after all cells; C/T donors unchanged; shallow caches identical across arms after t1'
    if stage == 'preflight':
        gates['self_ops'] = 'C route: no-hook, self-Q replacement with self-H swap, and capture forwards identical bit for bit'
    gates['calibration'] = 'NQ-01 saved scenario calibration (source hash in receipt)'
    body = {'text': a, 'scenario': info['scenario'], 'item': it, 'code_tokens': code_tok, 'competitor': comp, 'directions': out,
            'kernel_identity': kernel_identity(), 'calibration': calib, 'counts': counts, 'gates': gates}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', DESIGN, QC_INPUTS, QC_TOKENS, QSR_DIR / 'qsr_run.py', QSR_DIR / 'freeze-r01.json',
         QKD_DIR / 'qkd_run.py', QKDR.RPOST_C_MANIFEST, QKD_DIR / 'freeze-r02.json', QKF_DIR / 'qkf_run.py', QKFR.RPOST_MANIFEST,
         QCO_DIR / 'qco_run.py', QKFR.QCO_MANIFEST, QST_DIR / 'qst_core.py', SVQ_DIR / 'svq_run.py', FC_DIR / 'fc_core.py'] + PLAN_DOCS
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
    return own + b3 + xc + sk + nr + sp + svq + nq + qcd + qst + qco + qkf + qkd + qsr + [p for p in B3R.frozen_paths() if p not in own]


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
    """Conservative formal estimate from the preflight worker: mean per-text seconds (preflight texts also run the engineering
    forwards) x 48 + per-worker model load x 2; bytes = preflight bytes / 2 x 48."""
    ws = [w for w in sorted(Path(pre_root).glob('worker-*')) if w.is_dir()]
    assert len(ws) == 1
    r = exp.read(ws[0] / 'receipt.json')
    secs = [exp.read(ws[0] / rel)['seconds'] for rel in r['record_hashes']]
    load = r['wall_seconds'] - sum(secs)
    n = len(items())
    fb = 0
    return {'per_text_seconds': sum(secs) / len(secs), 'load_seconds': load, 'device_seconds': sum(secs) / len(secs) * n + 2 * load,
            'bytes': (r['bytes'] - fb) / len(secs) * n, 'texts': n}


def check_limits(counts, stage):
    lim = LIMITS[stage]
    assert all(counts[k] <= lim[k] for k in lim), (counts, lim)


def execute(engine, stage, output, receipt, units, gpu):
    qi = QCDR.qc_items()
    contexts = exp.contexts_for(engine.tokenizer, [qi[t['plan']['qc_broad_id']] for t in items()])
    conds = conditions()
    receipt['kernel_identity'] = T1.kernel_identity()
    assert list(engine.stop_ids) == list(CFK.STOP)
    F.hook_baseline(engine.model)
    import torch
    totals = {k: 0 for k in COUNT_KEYS + ('calibrations',)}
    calib = {}
    qctok = exp.read(QC_TOKENS)
    vecs = load_vectors()
    refs = {'qkf': qkf_traj(), 'qco': QKFR.qco_traj(), 'qkd': qkd_records()}
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
    lock = open(f'/tmp/acupuncture-krd-worker{worker}.lock', 'w')
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
        for d, x in rec['directions'].items():
            assert set(x['cells']) == {f'{r_}<-{d_}|{hq}' for r_, d_ in ORDERED for hq in CELLS} and set(x['N00']) == set(ARMS)
        for g in ('replay', 'h_swap', 'q_node', 'sources', 'calibration') + (('self_ops',) if r['stage'] == 'preflight' else ()):
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
            cmd = [sys.executable, '-u', str(HERE / 'krd_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
