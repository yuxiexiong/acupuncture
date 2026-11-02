"""NVW-01: conditional dependence of the t1 write-term k operation on V restoration (plan docs/cache-native-v-write-interaction-plan-v1-
2026-11-03.zh-CN.md; CONTRACT r01).  Backgrounds from the same C/T formation: T (all T), V (G conv V from C), Q (G conv q/k from C),
F (G conv q/k and V from C); everything else T.  Families: R (T / V, shadow k = old k slots - mu), A (Q / F, + mu), Z (Q / F, + r_post);
per family x background: 0 (background itself), W (write term uses the shadow k), K (full t1 k-node replacement).  16 natural trajectories
per (input, direction).  Readouts: t1 first-step margin G = z[fF] - max(z[stop]); C route t2 M; natural Y_full.
python nvw_run.py freeze PATH | run ... | verify WORKER_DIR | launch ..."""
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
KUC_DIR = HERE.parent / 'cache-k-update-causal-v1-2026-11-03'
sys.path.insert(0, str(KUC_DIR))
sys.path.insert(0, str(HERE))
import kuc_run as KUCR  # noqa: E402  (frozen KUC-01 runner)

KRDR, QSRR, QKDR = KUCR.KRDR, KUCR.QSRR, KUCR.QKDR
QKFR, QCOR, QSTR, QCDR, QCR, NQR, SVQ, NRR = KUCR.QKFR, KUCR.QCOR, KUCR.QSTR, KUCR.QCDR, KUCR.QCR, KUCR.NQR, KUCR.SVQ, KUCR.NRR
FC_DIR, SP_DIR, SVQ_DIR, NQ_DIR, QC_DIR, QCD_DIR, QST_DIR, QCO_DIR, QKF_DIR = KUCR.FC_DIR, KUCR.SP_DIR, KUCR.SVQ_DIR, KUCR.NQ_DIR, KUCR.QC_DIR, KUCR.QCD_DIR, KUCR.QST_DIR, KUCR.QCO_DIR, KUCR.QKF_DIR
QKD_DIR, QKD_FORMAL, QKD_PRE, QSR_DIR, QSR_FORMAL = KUCR.QKD_DIR, KUCR.QKD_FORMAL, KUCR.QKD_PRE, KUCR.QSR_DIR, KUCR.QSR_FORMAL
KRD_DIR, KHC_DIR, KRD_FORMAL = KUCR.KRD_DIR, KUCR.KHC_DIR, KUCR.KRD_FORMAL
KUC_FORMAL = KUC_DIR / 'runs/formal-r01'
B3R, V, P, PK, X = KUCR.B3R, KUCR.V, KUCR.P, KUCR.PK, KUCR.X
CF, CFK, LR, B = KUCR.CF, KUCR.CFK, KUCR.LR, KUCR.B
F, L, T1, exp, K = KUCR.F, KUCR.L, KUCR.T1, KUCR.exp, KUCR.K

PLAN_ID = 'NVW-01-NATIVE-V-WRITE-INTERACTION-v1'
PLAN_DOCS = [REPO / 'docs/cache-native-v-write-interaction-plan-v1-2026-11-03.zh-CN.md', REPO / 'docs/cache-native-v-write-interaction-self-check-v1-2026-11-03.zh-CN.md']
DESIGN, QC_INPUTS, QC_TOKENS = KUCR.DESIGN, KUCR.QC_INPUTS, KUCR.QC_TOKENS
QCD_G, QST_FORMAL, QCO_FORMAL, QKF_FORMAL = KUCR.QCD_G, KUCR.QST_FORMAL, KUCR.QCO_FORMAL, KUCR.QKF_FORMAL
QC_FORMAL, NQ_FORMAL, SVQ_FORMAL, SP_FORMAL, NR_FORMAL, B3_FORMAL, XC_FORMAL, SK_FORMAL = KUCR.QC_FORMAL, KUCR.NQ_FORMAL, KUCR.SVQ_FORMAL, KUCR.SP_FORMAL, KUCR.NR_FORMAL, KUCR.B3_FORMAL, KUCR.XC_FORMAL, KUCR.SK_FORMAL
SPLIT, A_LAYERS, MAX_NEW, STOP = KUCR.SPLIT, KUCR.A_LAYERS, KUCR.MAX_NEW, KUCR.STOP
DIRECTIONS, OLD_DIRS, NEW_DIR = KUCR.DIRECTIONS, KUCR.OLD_DIRS, KUCR.NEW_DIR
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
ARMS_ALL, QKF_NAME = KUCR.ARMS_ALL, KUCR.QKF_NAME
QK, K_LO, K_HI = KUCR.QK, KUCR.K_LO, KUCR.K_HI
BACKGROUNDS = {'T': ('T', 'T'), 'V': ('T', 'C'), 'Q': ('C', 'T'), 'F': ('C', 'C')}     # name: (G conv q/k source, G conv V source)
FAMILIES = {'R': (('T', 'V'), 'Rk'), 'A': (('Q', 'F'), 'Ak'), 'Z': (('Q', 'F'), 'Ark')}  # family: ((V not restored, V restored), arm with the k edit)
OPS = {'W': '01', 'K': '11'}
KUC_KEY = {('R', 'W'): 'R01', ('R', 'K'): 'R11', ('A', 'W'): 'A01', ('A', 'K'): 'A11', ('Z', 'W'): 'Z01', ('Z', 'K'): 'Z11'}
LAYER0 = 13
LIMITS = {'preflight': {'formations': 10, 'prefix_prefills': 2, 'formation_token_forwards': 265, 't1': 128, 'refs': 80, 'n_steps': 3968,
                        'c_t2': 128, 'decode_forwards': 4304, 'trajectories': 128, 'shadow': 2016, 'calibrations': 0},
          'formal': {'formations': 240, 'prefix_prefills': 48, 'formation_token_forwards': 6375, 't1': 3072, 'refs': 1920, 'n_steps': 95232,
                     'c_t2': 3072, 'decode_forwards': 103296, 'trajectories': 3072, 'shadow': 48384, 'calibrations': 0}}
GPU_CAP_S = {'preflight': 0.2 * 3600, 'formal': 2.0 * 3600}
STORAGE_LIMIT = 12 * 2 ** 30
ALLK = KUCR.ALLK
COUNT_KEYS = KUCR.COUNT_KEYS
PREFLIGHT_ITEMS = KUCR.PREFLIGHT_ITEMS
comp_sha, comp_sha_range, tensor_bytes_sha = KUCR.comp_sha, KUCR.comp_sha_range, KUCR.tensor_bytes_sha
gdn_module, kernel_identity, load_vectors, qkf_traj, conditions, items = KUCR.gdn_module, KUCR.kernel_identity, KUCR.load_vectors, KUCR.qkf_traj, KUCR.conditions, KUCR.items
qkd_records, margins, natural, fwd, t1 = KUCR.qkd_records, KUCR.margins, KUCR.natural, KUCR.fwd, KUCR.t1
bit_equal, cache_equal, UHook, custom_update = KUCR.bit_equal, KUCR.cache_equal, KUCR.UHook, KUCR.custom_update


def plan(stage, worker, n_workers):
    return QKDR.plan(stage, worker, n_workers)


def kuc_records():
    out = {}
    for w in sorted(KUC_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        for rel, dg in r['record_hashes'].items():
            assert exp.sha(w / rel) == dg, 'KUC record hash'
            rec = exp.read(w / rel)
            assert exp.sha(w / rec['tensor_file']) == r['tensor_hashes'][rec['tensor_file']], 'KUC tensor hash'
            rec['_tensor_path'] = str(w / rec['tensor_file'])
            out[rec['text']] = rec
    return out


def to_key(out, m):
    """Conv output [b, ch, seq] -> kernel-entry key exactly as Qwen3_5GatedDeltaNet does."""
    import torch
    mixed = out.transpose(1, 2)
    _, key, _ = torch.split(mixed, [m.key_dim, m.key_dim, m.value_dim], dim=-1)
    key = key.reshape(mixed.shape[0], mixed.shape[1], -1, m.head_k_dim)
    if m.num_v_heads // m.num_k_heads > 1:
        key = key.repeat_interleave(m.num_v_heads // m.num_k_heads, dim=2)
    return key


def term_stats(key0, key1, value, g, beta, S0, l2norm):
    """Per head (FP64, from the kernel's FP32 conventions): raw |k0|, |k1|, cos(k0n, k1n), |k0n^T D|, |k1n^T D|, |v|, beta, |dE|, |dW|,
    cos(dE, dW) with dE = -beta (k1n (k1n^T D) - k0n (k0n^T D)), dW = beta (k1n - k0n) v^T, D = alpha S0 (key x value)."""
    import torch
    f = lambda x: x.transpose(1, 2).to(torch.float32)[0, :, 0]   # noqa: E731  [heads, dim]
    k0, k1, v = f(key0), f(key1), f(value)
    b = beta.to(torch.float32)[0, 0].double()                     # [heads]
    a = g.to(torch.float32)[0, 0].exp().double()
    k0n, k1n = l2norm(k0, dim=-1, eps=1e-6).double(), l2norm(k1, dim=-1, eps=1e-6).double()
    D = S0.to(torch.float32)[0].double() * a[:, None, None]       # [heads, k, v]
    p0 = torch.einsum('hkv,hk->hv', D, k0n)
    p1 = torch.einsum('hkv,hk->hv', D, k1n)
    vd = v.double()
    dE = -b[:, None, None] * (k1n[:, :, None] * p1[:, None, :] - k0n[:, :, None] * p0[:, None, :])
    dW = b[:, None, None] * (k1n - k0n)[:, :, None] * vd[:, None, :]
    nE, nW = dE.flatten(1).norm(dim=-1), dW.flatten(1).norm(dim=-1)
    cosEW = (dE.flatten(1) * dW.flatten(1)).sum(-1) / torch.clamp(nE * nW, min=1e-300)
    cosk = (k0n * k1n).sum(-1)
    return torch.stack([k0.double().norm(dim=-1), k1.double().norm(dim=-1), cosk, p0.norm(dim=-1), p1.norm(dim=-1), vd.norm(dim=-1), b, nE, nW, cosEW], -1)


STAT_FIELDS = ('k0_raw', 'k1_raw', 'cos_k0k1', 'p0', 'p1', 'v', 'beta', 'dE', 'dW', 'cos_dEdW')


class NHook(UHook):
    """UHook plus: native and shadow key at layer 13 (cross-background wiring gate) and per-layer term statistics (record only)."""

    def __enter__(self):
        super().__enter__()
        inner_c, inner_k, me = self.QM.causal_conv1d_update, self.QM.torch_recurrent_gated_delta_rule, self
        self.k0_l0, self.stats = None, {}

        def conv2(hidden_states, conv_state, weight, bias=None, activation=None):
            out = inner_c(hidden_states, conv_state, weight, bias, activation)
            if me.layer == LAYER0:
                me.k0_l0 = to_key(out, me.mod).clone()
            return out

        def kern2(query, key, value, g=None, beta=None, initial_state=None, output_final_state=False, use_qk_l2norm_in_kernel=False, **kw):
            if me.layer in me.G and me.mode == 'cell':
                me.stats[me.layer] = term_stats(key, me.shadow[me.layer], value, g, beta, initial_state, me.QM.l2norm).float().cpu()
            return inner_k(query, key, value, g=g, beta=beta, initial_state=initial_state, output_final_state=output_final_state,
                           use_qk_l2norm_in_kernel=use_qk_l2norm_in_kernel, **kw)
        self.QM.causal_conv1d_update = conv2
        self.QM.torch_recurrent_gated_delta_rule = kern2
        return self


def check_bg(c, T_, C_, types, G, qk_src, v_src):
    """Background source check: G conv q/k channels from qk_src, V channels from v_src, every other tensor == T (byte equality)."""
    import torch
    src = {'T': T_, 'C': C_}
    for i, kind, f in L.component_tensors(c, types):
        a = L._get(c.layers[i], f)
        if kind == 'conv' and i in G:
            assert torch.equal(a[:, :QK], L._get(src[qk_src].layers[i], f)[:, :QK]), ('bg q/k source', i)
            assert torch.equal(a[:, QK:], L._get(src[v_src].layers[i], f)[:, QK:]), ('bg V source', i)
        else:
            assert bit_equal(a, L._get(T_.layers[i], f))[0], ('bg other source', i, f)


def first_step(z, fF):
    import torch
    stops = [float(z[s]) for s in STOP]
    top = int(z.argmax())
    zz = z.clone()
    zz[fF] = -float('inf')
    return {'G': float(z[fF]) - max(stops), 'z_fF': float(z[fF]), 'z_stop': stops, 'argmax': top, 'other_max_token': int(zz.argmax()),
            'other_max': float(zz.max())}


def run_item(engine, unit, contexts, calib, conds, qctok, output, stage, vecs=None, refs=None):
    import torch
    model, tok = engine.model, engine.tokenizer
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
    assert tuple(G) == (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30) and G[0] == LAYER0
    assert tuple(STOP) == tuple(CFK.STOP) == tuple(engine.stop_ids), 'stop ids != parser stop set'
    KRDR.QHOOK_ORIG[0] = gdn_module().torch_recurrent_gated_delta_rule
    a = unit['item_id']
    counts = {k: 0 for k in COUNT_KEYS}
    tensors, gates, out = {}, {}, {}
    nz_total, oracle_max = 0, 0.0
    C, T, info = QCOR.form_text(engine, a, contexts, calib, conds, qctok, counts)
    hC, hT = comp_sha(C, types, ALLK, 0), {d: comp_sha(T[d], types, ALLK, 0) for d in conds}
    it, code_tok, n = info['item'], info['code_tokens'], info['n']
    comp = it['first_listed'] if it['target'] != it['first_listed'] else it['listed_codes'][1]
    kuc = refs['kuc'][a]
    kuc_t = torch.load(kuc['_tensor_path'], map_location='cpu')
    dec = lambda ids: tok.decode(ids, skip_special_tokens=False)   # noqa: E731
    for d in conds:
        s = info['scenario']
        kd = kuc['directions'][d]
        fF = kd['fF']
        assert fF not in STOP and fF == (refs['qkf'][a][f'F|{d}']['ids'] if d in OLD_DIRS else refs['qco'][a][f'F|{d}']['ids'])[0]

        def finish(c1, z1, key):
            _, zc = fwd(engine, copy.deepcopy(c1), fF, n, counts, 'c_t2')
            M, Mall = margins(zc, it, code_tok, comp)
            tensors[f'C|{key}|{d}'] = zc.to(torch.bfloat16).cpu()
            tensors[f't1|{key}|{d}'] = z1.to(torch.bfloat16).cpu()
            x_ = int(z1.argmax())
            r, _ = natural(engine, copy.deepcopy(c1), x_, n, counts)
            r['text'] = dec(r['ids'])
            return {'x': x_, 'first': first_step(z1, fF), 'C': {'M': M, 'M_all': Mall, 't2_sha': F.th(zc)}, 'N': r}, zc

        base, hbase, c1, z1s, res = {}, {}, {}, {}, {}
        for bg, (qs, vs) in BACKGROUNDS.items():
            src = {'T': T[d], 'C': C}
            cc, _ = QKFR.edited_arm(T[d], src[qs], src[vs], G, None, 1)
            check_bg(cc, T[d], C, types, G, qs, vs)
            base[bg], hbase[bg] = cc, comp_sha(cc, types, ALLK, 0)
            c1[bg], z1 = t1(engine, copy.deepcopy(cc), info['last'], n, counts, 't1')
            z1s[bg] = z1
            res[bg], zc = finish(c1[bg], z1, bg)
            cn, zn = t1(engine, copy.deepcopy(cc), info['last'], n, counts, 'refs', hook=UHook(model, G, 'noop'))
            okz, z0 = bit_equal(zn, z1)
            okc, zc0, _, fail = cache_equal(cn, c1[bg], types, G)
            assert okz and okc, ('no-op custom update != native', bg, d, fail)
            nz_total += z0 + zc0
            if bg in ('V', 'F'):
                assert bit_equal(z1.to(torch.bfloat16).cpu(), kuc_t[f't1|{bg}|{d}'])[0] and bit_equal(zc.to(torch.bfloat16).cpu(), kuc_t[f'C|{bg}|{d}'])[0], ('V/F != KUC', bg, d)
                assert res[bg]['N']['ids'] == kd['orig'][bg]['N']['ids'] and res[bg]['C']['M'] == kd['orig'][bg]['C']['M'], ('V/F trajectory != KUC', bg, d)
        l0 = {}
        for fam, ((b0, b1), src_arm) in FAMILIES.items():
            _, u, sign = ARMS_ALL[src_arm]
            vec = QKFR.mask_vec(vecs[u][f'{s}|{d}'].float(), 'k')
            for bg in (b0, b1):
                cr, zr = t1(engine, copy.deepcopy(base[bg]), info['last'], n, counts, 'refs', hook=UHook(model, G, 'ref_full', vec=vec, sign=sign))
                for op, code in OPS.items():
                    hk = NHook(model, G, 'cell', code=code, vec=vec, sign=sign)
                    cn, zn = t1(engine, copy.deepcopy(base[bg]), info['last'], n, counts, 't1', hook=hk)
                    if hk.oracle:
                        oracle_max = max(oracle_max, max(hk.oracle.values()))
                    l0[(fam, bg, op)] = (hk.k0_l0, hk.shadow[LAYER0])
                    tensors[f'stats|{fam}{bg}{op}|{d}'] = torch.stack([hk.stats[l] for l in G])
                    if op == 'K':
                        okz, z0 = bit_equal(zn, zr)
                        okc, zc0, _, fail = cache_equal(cn, cr, types, G)
                        assert okz and okc, ('K != original kernel fed the shadow k', fam, bg, d, fail)
                        nz_total += z0 + zc0
                    key = f'{fam}{bg}{op}'
                    r_, zc = finish(cn, zn, key)
                    res[key] = r_
                    if bg == b1:
                        kk = KUC_KEY[(fam, op)]
                        assert bit_equal(zn.to(torch.bfloat16).cpu(), kuc_t[f't1|{kk}|{d}'])[0] and bit_equal(zc.to(torch.bfloat16).cpu(), kuc_t[f'C|{kk}|{d}'])[0], ('high-V arm != KUC', key, kk, d)
                        assert r_['N']['ids'] == kd['new'][kk]['N']['ids'] and r_['C']['M'] == kd['new'][kk]['C']['M'], ('high-V trajectory != KUC', key, kk, d)
                    del cn
                del cr
            for op in OPS:
                (a0, s0), (a1, s1) = l0[(fam, b0, op)], l0[(fam, b1, op)]
                assert bit_equal(a0, a1)[0] and bit_equal(s0, s1)[0], ('layer-13 k0/k1 differ across backgrounds', fam, op, d)
        for bg in BACKGROUNDS:
            assert comp_sha(base[bg], types, ALLK, 0) == hbase[bg], ('pre-t1 background cache modified', bg, d)
        out[d] = {'fF': fF, 'arms': res}
        del base, c1
        torch.cuda.empty_cache()
    assert hC == comp_sha(C, types, ALLK, 0) and all(comp_sha(T[d], types, ALLK, 0) == hT[d] for d in conds), 'donor modified'
    F.assert_no_hooks(model)
    gates['backgrounds'] = 'T/V/Q/F: only the listed G conv slices from C, every other tensor == T; sources unchanged'
    gates['noop'] = 'custom update with kE = kW = native k == native t1 (logits and every cache tensor) on all four backgrounds'
    gates['full_node'] = 'K == original kernel fed the shadow k (t1 logits and every cache tensor), six family x background arms'
    gates['kuc_bridge'] = 'V, F and the six high-V W/K arms == KUC V, F, R01, R11, A01, A11, Z01, Z11: t1 and C t2 bf16 logits, natural tokens, M'
    gates['layer13'] = 'native and shadow k at layer 13 identical across the two backgrounds of each family (W and K arms)'
    gates['oracle'] = f'W arms: FP32 S and o vs FP64 three-term formula, max relative error {oracle_max:.3g} <= {KUCR.ORACLE_TOL}'
    gates['hooks'] = 'conv/kernel hooks once per G layer at t1 only; module functions restored; shadow never written back; stop ids == parser'
    gates['calibration'] = 'NQ-01 saved scenario calibration (source hash in receipt)'
    body = {'text': a, 'scenario': info['scenario'], 'item': it, 'code_tokens': code_tok, 'competitor': comp, 'directions': out,
            'signed_zero_exceptions': nz_total, 'oracle_max': oracle_max, 'stat_fields': list(STAT_FIELDS), 'kernel_identity': kernel_identity(),
            'calibration': calib, 'counts': counts, 'gates': gates}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', DESIGN, QC_INPUTS, QC_TOKENS, KUC_DIR / 'kuc_run.py', KUC_DIR / 'freeze-r01.json',
         KUC_DIR / 'analysis/kuc-readouts-r01.json', KRD_DIR / 'krd_run.py', KRD_DIR / 'freeze-r02.json', QSR_DIR / 'qsr_run.py', QKD_DIR / 'qkd_run.py',
         QKDR.RPOST_C_MANIFEST, QKD_DIR / 'freeze-r02.json', QKF_DIR / 'qkf_run.py', QKFR.RPOST_MANIFEST, QCO_DIR / 'qco_run.py', QKFR.QCO_MANIFEST,
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
    refs = {'qkf': qkf_traj(), 'qco': QKFR.qco_traj(), 'qkd': qkd_records(), 'kuc': kuc_records()}
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
    lock = open(f'/tmp/acupuncture-nvw-worker{worker}.lock', 'w')
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
            assert set(x['arms']) == set(BACKGROUNDS) | {f'{fam}{bg}{op}' for fam, (bgs, _) in FAMILIES.items() for bg in bgs for op in OPS}
        for g in ('backgrounds', 'noop', 'full_node', 'kuc_bridge', 'layer13', 'oracle', 'hooks', 'calibration'):
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
            cmd = [sys.executable, '-u', str(HERE / 'nvw_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
