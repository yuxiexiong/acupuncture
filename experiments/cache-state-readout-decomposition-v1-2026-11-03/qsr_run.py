"""QSR-01: S / q / alpha decomposition of the old-state read-out difference (plan docs/cache-state-readout-decomposition-plan-v1-2026-11-03
.zh-CN.md; CONTRACT r01).  Same six arms and backgrounds as QKD-01; two observed computations per arm: t1 (last prompt token) and t2
(F's first answer token forced).  For pairs (end1 - end0): V-F, Rk-V, Ak-F, Rrk-V, Ark-F, per G layer and value head:
  D_j = a_j S_j^T q_j;  X_S = a_bar dS^T q_bar;  X_q = a_bar S_bar^T dq;  X_a = da S_bar^T q_bar;  X_I = da dS^T dq / 4;  dD = sum (exact).
All arms share the receiver's recurrent state, so at t1 dS == 0 by construction (engineering gate: bitwise equal S at t1).
python qsr_run.py freeze PATH | run ... | verify WORKER_DIR | launch ...
"""
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
QKD_DIR = HERE.parent / 'cache-k-computation-diagnostic-v1-2026-11-03'
sys.path.insert(0, str(QKD_DIR))
sys.path.insert(0, str(HERE))
import qkd_run as QKDR  # noqa: E402  (frozen QKD-01 runner: Capture, step, decompose, arms, vectors, references)

QKFR, QCOR, QSTR, QCDR, QCR, NQR, SVQ, NRR = QKDR.QKFR, QKDR.QCOR, QKDR.QSTR, QKDR.QCDR, QKDR.QCR, QKDR.NQR, QKDR.SVQ, QKDR.NRR
FC_DIR, SP_DIR, SVQ_DIR, NQ_DIR, QC_DIR, QCD_DIR, QST_DIR, QCO_DIR, QKF_DIR = QKDR.FC_DIR, QKDR.SP_DIR, QKDR.SVQ_DIR, QKDR.NQ_DIR, QKDR.QC_DIR, QKDR.QCD_DIR, QKDR.QST_DIR, QKDR.QCO_DIR, QKDR.QKF_DIR
B3R, V, P, PK, X = QKDR.B3R, QKDR.V, QKDR.P, QKDR.PK, QKDR.X
CF, CFK, LR, B = QKDR.CF, QKDR.CFK, QKDR.LR, QKDR.B
F, L, T1, exp, K = QKDR.F, QKDR.L, QKDR.T1, QKDR.exp, QKDR.K

PLAN_ID = 'QSR-01-STATE-READOUT-DECOMPOSITION-v1'
PLAN_DOCS = [REPO / 'docs/cache-state-readout-decomposition-plan-v1-2026-11-03.zh-CN.md', REPO / 'docs/cache-qsr-self-check-v1-2026-11-03.zh-CN.md']
DESIGN = QKDR.DESIGN
QC_INPUTS, QC_TOKENS = QKDR.QC_INPUTS, QKDR.QC_TOKENS
QCD_G, QST_FORMAL, QCO_FORMAL, QKF_FORMAL = QKDR.QCD_G, QKDR.QST_FORMAL, QKDR.QCO_FORMAL, QKDR.QKF_FORMAL
QKD_FORMAL, QKD_PRE = QKD_DIR / 'runs/formal-r02', QKD_DIR / 'runs/preflight-r02'
QC_FORMAL, NQ_FORMAL, SVQ_FORMAL, SP_FORMAL, NR_FORMAL, B3_FORMAL, XC_FORMAL, SK_FORMAL = QKDR.QC_FORMAL, QKDR.NQ_FORMAL, QKDR.SVQ_FORMAL, QKDR.SP_FORMAL, QKDR.NR_FORMAL, QKDR.B3_FORMAL, QKDR.XC_FORMAL, QKDR.SK_FORMAL
SPLIT = 13
DIRECTIONS, OLD_DIRS, NEW_DIR = QKDR.DIRECTIONS, QKDR.OLD_DIRS, QKDR.NEW_DIR
PREFLIGHT_ITEMS = QKDR.PREFLIGHT_ITEMS
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
STOP = QKDR.STOP
LIMITS = {'preflight': {'formations': 10, 'trajectories': 0, 'decode_forwards': 192, 'diagnostics': 0, 'calibrations': 0, 'prefix_prefills': 2,
                        'formation_token_forwards': 265},
          'formal': {'formations': 240, 'trajectories': 0, 'decode_forwards': 2304, 'diagnostics': 0, 'calibrations': 0, 'prefix_prefills': 48,
                     'formation_token_forwards': 6375}}
GPU_CAP_S = {'preflight': 0.10 * 3600, 'formal': 0.70 * 3600}
STORAGE_LIMIT = 20 * 2 ** 30
ARMS, QKF_NAME = QKDR.ARMS, QKDR.QKF_NAME
PAIRS = (('V', 'F'), ('Rk', 'V'), ('Ak', 'F'), ('Rrk', 'V'), ('Ark', 'F'))      # (end1, end0)
SPLIT_FIELDS = ('sS', 'sq', 'sa', 'sI', 'n_dD', 'resolvable', 'id_gap', 'n_XS', 'n_Xq', 'n_Xa', 'n_XI')
ID_REL, ID_ABS = 1e-10, 1e-12
ARM_FIELDS = ('qn', 'D', 'E', 'W', 'o')
RESOLVE_MULT = 5.0
OFF_DIR = 'N_L00_C4146_D-1'
ALLK = ('recurrent', 'kv', 'conv')
COUNT_KEYS = ('formations', 'trajectories', 'decode_forwards', 'diagnostics', 'prefix_prefills', 'formation_token_forwards')
comp_sha = NRR.comp_sha
shared_tokens, Capture, step, decompose, gdn_module = QKDR.shared_tokens, QKDR.Capture, QKDR.step, QKDR.decompose, QKDR.gdn_module
conditions, items, plan, kernel_identity, load_vectors, qkf_traj = QKDR.conditions, QKDR.items, QKDR.plan, QKDR.kernel_identity, QKDR.load_vectors, QKDR.qkf_traj


def qkd_records():
    out = {}
    for w in sorted(QKD_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        for rel, dg in r['record_hashes'].items():
            assert exp.sha(w / rel) == dg, 'QKD record hash'
            rec = exp.read(w / rel)
            assert exp.sha(w / rec['tensor_file']) == r['tensor_hashes'][rec['tensor_file']], 'QKD tensor hash'
            rec['_tensor_path'] = str(w / rec['tensor_file'])
            out[rec['text']] = rec
    return out


def qkd_err_threshold():
    """QKD-r02 frozen formal threshold: min(0.02, max(1e-5, 2 * preflight e_max)), recomputed from the QKD preflight records."""
    e = 0.0
    for w in sorted(QKD_PRE.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        for rel in r['record_hashes']:
            e = max(e, exp.read(w / rel)['err_max'])
    return min(0.02, max(1e-5, 2 * e)), e


def split_terms(d1, d0):
    """Exact midpoint split of dD = D1 - D0 (D = a S^T q) for one layer, FP64.  Returns dict of [32,128] / [32] tensors."""
    import torch
    q1, q0, S1, S0, a1, a0 = d1['qn'], d0['qn'], d1['S'], d0['S'], d1['a'], d0['a']
    A = {(i, j): torch.einsum('hkv,hk->hv', (S0, S1)[i], (q0, q1)[j]) for i in (0, 1) for j in (0, 1)}
    Sb_qb = (A[0, 0] + A[0, 1] + A[1, 0] + A[1, 1]) / 4
    dS_qb = ((A[1, 0] - A[0, 0]) + (A[1, 1] - A[0, 1])) / 2          # differences first: exactly 0 when S1 == S0 bitwise
    Sb_dq = ((A[0, 1] - A[0, 0]) + (A[1, 1] - A[1, 0])) / 2          # exactly 0 when q1 == q0
    dS_dq = (A[1, 1] - A[1, 0]) - (A[0, 1] - A[0, 0])
    ab, da = ((a0 + a1) / 2)[:, None], (a1 - a0)[:, None]
    X = {'S': ab * dS_qb, 'q': ab * Sb_dq, 'a': da * Sb_qb, 'I': da * dS_dq / 4}
    dD = a1[:, None] * A[1, 1] - a0[:, None] * A[0, 0]
    return {'A': A, 'X': X, 'dD': dD}


def split_stats(t, abs1, abs0):
    """Per-head summary [32, len(SPLIT_FIELDS)] of one split_terms output; abs1/abs0 = original-kernel D+E+W reconstruction abs errors."""
    import torch
    X, dD = t['X'], t['dD']
    n2 = (dD * dD).sum(-1)
    sh = lambda Y: torch.where(n2 > 0, (Y * dD).sum(-1) / torch.clamp(n2, min=1e-300), torch.full_like(n2, float('nan')))   # noqa: E731
    gap = (X['S'] + X['q'] + X['a'] + X['I'] - dD).norm(dim=-1)
    nd = dD.norm(dim=-1)
    resolvable = nd > RESOLVE_MULT * (abs1 + abs0)
    cols = {'sS': sh(X['S']), 'sq': sh(X['q']), 'sa': sh(X['a']), 'sI': sh(X['I']), 'n_dD': nd, 'resolvable': resolvable.double(), 'id_gap': gap,
            'n_XS': X['S'].norm(dim=-1), 'n_Xq': X['q'].norm(dim=-1), 'n_Xa': X['a'].norm(dim=-1), 'n_XI': X['I'].norm(dim=-1)}
    return torch.stack([cols[k] for k in SPLIT_FIELDS], -1)


def identity_ok(stats):
    """FP64 identity: |sum - dD| <= 1e-10 |dD| (relative) or <= 1e-12 when dD == 0."""
    nd, gap = stats[..., SPLIT_FIELDS.index('n_dD')], stats[..., SPLIT_FIELDS.index('id_gap')]
    return bool(((gap <= ID_REL * nd) | (gap <= ID_ABS)).all())


def observe2(engine, cache0, last, n, ftok, types, G, counts, capture=True):
    """t1 (last prompt token) and t2 (forced F first answer token).  Returns tokens/hashes, captures, t2 logits."""
    cap = Capture(engine.model, G) if capture else None
    res = {'caps': {}}
    c = copy.deepcopy(cache0)
    for s, (tok, pos) in ((1, (last, n - 1)), (2, (ftok, n))):
        if capture:
            with cap:
                cap.rec = {}
                c, z = step(engine, c, tok, pos, counts)
                res['caps'][s] = cap.rec
        else:
            c, z = step(engine, c, tok, pos, counts)
        res[f't{s}_sha'] = F.th(z)
        res[f't{s}_cache'] = comp_sha(c, types, ALLK, 0)
        if s == 1:
            res['t1_argmax'] = int(z.argmax())
        else:
            res['t2_logits'] = z.detach().to('cpu').clone()
    return res


def run_item(engine, unit, contexts, calib, conds, qctok, output, stage, vecs=None, refs=None, thr=None):
    import torch
    model = engine.model
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
    assert tuple(G) == (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
    a = unit['item_id']
    counts = {k: 0 for k in COUNT_KEYS}
    tensors, fixture, gates, arms_out, pairs_out = {}, {}, {}, {}, {}
    C, T, info = QCOR.form_text(engine, a, contexts, calib, conds, qctok, counts)
    hC = comp_sha(C, types, ALLK, 0)
    hT = {d: comp_sha(T[d], types, ALLK, 0) for d in conds}
    it, code_tok = info['item'], info['code_tokens']
    comp = it['first_listed'] if it['target'] != it['first_listed'] else it['listed_codes'][1]
    orig = gdn_module().torch_recurrent_gated_delta_rule
    qkd = refs['qkd'][a]
    qkd_t = torch.load(qkd['_tensor_path'], map_location='cpu')
    err_max, wired_all, ident_all, t1_zero_all = 0.0, True, True, True
    for d in conds:
        s = info['scenario']
        fids = refs['qkf'][a][f'F|{d}']['ids'] if d in OLD_DIRS else refs['qco'][a][f'F|{d}']['ids']
        assert fids and fids[0] not in STOP, ('F first token missing', d)
        dec, S_t1 = {}, None
        for arm, (base, u, sign) in ARMS.items():
            qb = T[d] if base == 'T' else C
            vec = None if u is None else QKFR.mask_vec(vecs[u][f'{s}|{d}'].float(), 'k')
            cc, _ = QKFR.edited_arm(T[d], qb, C, G, vec, sign)
            QCOR.check_edit(T[d], qb, C, cc, types, G, vec is not None, f'{arm}|{d}')
            F.assert_no_hooks(model)
            ob = observe2(engine, cc, info['last'], info['n'], fids[0], types, G, counts, capture=True)
            F.assert_no_hooks(model)
            assert gdn_module().torch_recurrent_gated_delta_rule is orig, 'capture wrapper left installed'
            if d in OLD_DIRS:
                o = refs['qkf'][a][f'{QKF_NAME[arm]}|{d}']
            else:
                o = qkd['c1343_trajectories'][arm]
            assert ob['t1_sha'] == o['first']['logits_sha256'] and ob['t1_cache'] == o['first']['cache_sha256'], ('t1 != reference', arm, d)
            z2 = ob['t2_logits']
            M = float(z2[code_tok[it['target']]] - z2[code_tok[comp]])
            assert M == qkd['arms'][d][arm]['M'], ('t2 margin != QKD', arm, d, M, qkd['arms'][d][arm]['M'])
            assert torch.equal(z2.to(torch.bfloat16), qkd_t[f'Ct2|{arm}|{d}']), ('t2 logits != QKD saved', arm, d)
            if stage == 'preflight':
                off = observe2(engine, cc, info['last'], info['n'], fids[0], types, G, counts, capture=False)
                for k_ in ('t1_sha', 't1_cache', 't2_sha', 't2_cache', 't1_argmax'):
                    assert off[k_] == ob[k_], ('observer changed the path', arm, d, k_)
                assert torch.equal(off['t2_logits'], ob['t2_logits']), ('observer changed t2 logits', arm, d)
            dd = {}
            for st_, rec in ob['caps'].items():
                assert set(rec) == set(G), ('capture missed a layer', arm, d, st_)
                dd[st_] = {l: decompose(rec[l], orig) for l in G}
                for l in G:
                    err_max = max(err_max, float(dd[st_][l]['err'].max()))
                    wired_all &= dd[st_][l]['wired']
                for f in ARM_FIELDS:
                    tensors[f'arm|{f}|{arm}|t{st_}|{d}'] = torch.stack([dd[st_][l][f] for l in G]).float().cpu()
                tensors[f'arm|a|{arm}|t{st_}|{d}'] = torch.stack([dd[st_][l]['a'] for l in G]).float().cpu()
                tensors[f'arm|b|{arm}|t{st_}|{d}'] = torch.stack([dd[st_][l]['b'] for l in G]).float().cpu()
                tensors[f'arm|err|{arm}|t{st_}|{d}'] = torch.stack([dd[st_][l]['err'] for l in G]).float().cpu()
                tensors[f'arm|abs_err|{arm}|t{st_}|{d}'] = torch.stack([dd[st_][l]['abs_err'] for l in G]).float().cpu()
                if stage == 'preflight':
                    fixture[f'S|{arm}|t{st_}|{d}'] = torch.stack([rec[l]['S'][0] for l in G]).cpu()
            if S_t1 is None:
                S_t1 = {l: ob['caps'][1][l]['S'].clone() for l in G}
            else:
                for l in G:
                    assert torch.equal(ob['caps'][1][l]['S'], S_t1[l]), ('t1 S differs across arms', arm, d, l)
            dec[arm] = dd
            arms_out.setdefault(d, {})[arm] = {'M': M, 't1_argmax': ob['t1_argmax'], 't1_sha': ob['t1_sha'], 't2_sha': ob['t2_sha']}
            tensors[f't2|{arm}|{d}'] = z2.to(torch.bfloat16)
            del cc, ob
        for e1, e0 in PAIRS:
            for st_ in (1, 2):
                layer_stats = []
                for j, l in enumerate(G):
                    t = split_terms(dec[e1][st_][l], dec[e0][st_][l])
                    layer_stats.append(split_stats(t, dec[e1][st_][l]['abs_err'], dec[e0][st_][l]['abs_err']))
                    for (i0, j0), v_ in t['A'].items():
                        tensors.setdefault(f'A{i0}{j0}|{e1}-{e0}|t{st_}|{d}', []).append(v_.float().cpu())
                    for k_, v_ in t['X'].items():
                        tensors.setdefault(f'X{k_}|{e1}-{e0}|t{st_}|{d}', []).append(v_.float().cpu())
                tens = torch.stack(layer_stats)                                    # [14, 32, F] FP64
                key = f'{e1}-{e0}|t{st_}|{d}'
                ident_all &= identity_ok(tens)
                if st_ == 1:
                    z = bool((tens[..., SPLIT_FIELDS.index('n_XS')] == 0).all() and (tens[..., SPLIT_FIELDS.index('n_XI')] == 0).all())
                    t1_zero_all &= z
                tensors[f'split|{key}'] = tens.float().cpu()
                ok = (tens[..., SPLIT_FIELDS.index('resolvable')] > 0)
                summ = {'coverage': float(ok.double().mean())}
                for f in ('sS', 'sq', 'sa', 'sI'):
                    v_ = tens[..., SPLIT_FIELDS.index(f)][ok]
                    v_ = v_[torch.isfinite(v_)]
                    summ[f'median_{f}'] = float(v_.median()) if v_.numel() else None
                    if f == 'sI':
                        summ['median_abs_sI'] = float(v_.abs().median()) if v_.numel() else None
                for f in ('n_dD', 'n_XS', 'n_Xq', 'n_Xa', 'n_XI'):
                    summ[f'median_{f}'] = float(tens[..., SPLIT_FIELDS.index(f)].median())
                pairs_out[key] = summ
        for k_ in [k_ for k_ in tensors if isinstance(tensors[k_], list)]:
            tensors[k_] = torch.stack(tensors[k_])
        del dec, S_t1
        torch.cuda.empty_cache()
    assert wired_all, 'wiring check failed'
    assert ident_all, 'FP64 four-term identity failed'
    assert t1_zero_all, 't1 X_S / X_I not exactly zero'
    assert comp_sha(C, types, ALLK, 0) == hC and all(comp_sha(T[d], types, ALLK, 0) == hT[d] for d in conds), 'donor modified'
    F.assert_no_hooks(model)
    gates['replay'] = 't1 logits/cache hashes == QKF (old directions) / QKD C1343 generations; t2 margin and full bf16 logits == QKD exactly'
    gates['t1_shared_state'] = 'at t1 every arm enters every G layer kernel with a bitwise-identical recurrent state; X_S = X_I = 0 exactly at t1'
    gates['identity'] = f'FP64 X_S+X_q+X_a+X_I == dD within rel {ID_REL} / abs {ID_ABS} on every layer-head'
    gates['sources'] = 'every arm: V block == C(a), k slot 0 == base, S/KV/shallow == T(a,d); donors unchanged'
    gates['capture'] = 'read-only wrapper; 14 G layers per observed step; wrapper removed and no hooks before every arm'
    gates['wiring'] = 'kernel re-run on captured clones == captured output bit for bit'
    if stage == 'preflight':
        gates['observer_off'] = 't1/t2 with and without the observer: argmax, logits (full t2 vector) and cache hashes identical'
    gates['calibration'] = 'NQ-01 saved scenario calibration (source hash in receipt)'
    body = {'text': a, 'scenario': info['scenario'], 'item': it, 'code_tokens': code_tok, 'competitor': comp, 'arms': arms_out, 'pairs': pairs_out,
            'err_max': err_max, 'err_threshold': thr, 'kernel_identity': kernel_identity(), 'calibration': calib, 'counts': counts, 'gates': gates}
    return body, tensors, fixture


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', DESIGN, QC_INPUTS, QC_TOKENS, QKD_DIR / 'qkd_run.py', QKD_DIR / 'qkd_core.py', QKD_DIR / 'qkd_rpost.py', QKDR.RPOST_C_MANIFEST, QKD_DIR / 'freeze-r02.json', QKD_DIR / 'analysis/qkd-readouts-r02.json', QKF_DIR / 'qkf_run.py', QKFR.RPOST_MANIFEST, QCO_DIR / 'qco_run.py', QKFR.QCO_MANIFEST, QST_DIR / 'qst_core.py', SVQ_DIR / 'svq_run.py', FC_DIR / 'fc_core.py'] + PLAN_DOCS
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
    return own + b3 + xc + sk + nr + sp + svq + nq + qcd + qst + qco + qkf + qkd + [p for p in B3R.frozen_paths() if p not in own]


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
    """Conservative formal estimate from the preflight worker: mean per-text seconds (preflight texts also run the observer-off replay and
    save S fixtures) x 48 + per-worker model load x 2; bytes = (preflight bytes - fixture bytes) / 2 x 48."""
    ws = [w for w in sorted(Path(pre_root).glob('worker-*')) if w.is_dir()]
    assert len(ws) == 1
    r = exp.read(ws[0] / 'receipt.json')
    secs = [exp.read(ws[0] / rel)['seconds'] for rel in r['record_hashes']]
    load = r['wall_seconds'] - sum(secs)
    n = len(items())
    fb = sum(r.get('fixture_bytes', {}).values())
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
    thr, _e = qkd_err_threshold()
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
        body, tensors, fixture = run_item(engine, u, contexts, calib[rid], conds, qctok, output, stage, vecs=vecs, refs=refs, thr=thr)
        if fixture:
            rel_f = f'fixtures/{u["key"]}.pt'
            (output / 'fixtures').mkdir(exist_ok=True)
            assert not (output / rel_f).exists()
            torch.save(fixture, output / rel_f)
            receipt.setdefault('fixture_hashes', {})[rel_f] = exp.sha(output / rel_f)
            receipt.setdefault('fixture_bytes', {})[rel_f] = (output / rel_f).stat().st_size
            body['fixture_file'] = rel_f
        del fixture
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
    lock = open(f'/tmp/acupuncture-qsr-worker{worker}.lock', 'w')
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
        assert set(rec['arms']) == set(DIRECTIONS) and all(set(v) == set(ARMS) for v in rec['arms'].values())
        assert set(rec['pairs']) == {f'{e1}-{e0}|t{s_}|{d}' for e1, e0 in PAIRS for s_ in (1, 2) for d in DIRECTIONS}
        for g in ('replay', 't1_shared_state', 'identity', 'sources', 'capture', 'wiring', 'calibration') + (('observer_off',) if r['stage'] == 'preflight' else ()):
            assert rec['gates'][g], g
        assert rec['err_max'] <= rec['err_threshold'], ('decomposition error above the inherited QKD threshold', rec['err_max'], rec['err_threshold'])
        assert rec['gates']['identity']
        if r['stage'] == 'preflight':
            assert exp.sha(path / rec['fixture_file']) == r['fixture_hashes'][rec['fixture_file']]
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
            cmd = [sys.executable, '-u', str(HERE / 'qsr_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
