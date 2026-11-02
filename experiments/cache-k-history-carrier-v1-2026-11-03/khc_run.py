"""KHC-01: S x KV carrier test of the k-repair history with the donor's t2 query fixed (plan docs/cache-k-history-carrier-plan-v1-2026-11-03
.zh-CN.md; CONTRACT r01).  Five QKD arms (V, F, Rk, Ak, Ark); ordered pairs r<-d: Rk<-V, V<-Rk, Ak<-F, F<-Ak, Ark<-F, F<-Ark.
Cells sb: S (all G recurrent states) from d if s, KV (all A-layer keys/values) from d if b; t2 Q (14 G layers, kernel-entry query) always the
ORIGINAL donor's on the same t2 input token.  Conv buffers and everything else stay the receiver's.  New cells 00 / 11 equal KRD-01 r02 cells
01 / 11: C route recomputed and checked bit for bit against KRD; N route 00 / 11 trajectories reused from KRD, bridged per input by one t2
forward checked bit for bit against KRD's saved N t2 logits (preflight: full trajectory replay).  New cells 10 / 01 run both routes.
python khc_run.py freeze PATH | run ... | verify WORKER_DIR | launch ..."""
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
KRD_DIR = HERE.parent / 'cache-k-repair-dependence-v1-2026-11-03'
sys.path.insert(0, str(KRD_DIR))
sys.path.insert(0, str(HERE))
import krd_run as KRDR  # noqa: E402  (frozen KRD-01 runner, r02)

QSRR, QKDR = KRDR.QSRR, KRDR.QKDR
QKFR, QCOR, QSTR, QCDR, QCR, NQR, SVQ, NRR = KRDR.QKFR, KRDR.QCOR, KRDR.QSTR, KRDR.QCDR, KRDR.QCR, KRDR.NQR, KRDR.SVQ, KRDR.NRR
FC_DIR, SP_DIR, SVQ_DIR, NQ_DIR, QC_DIR, QCD_DIR, QST_DIR, QCO_DIR, QKF_DIR = KRDR.FC_DIR, KRDR.SP_DIR, KRDR.SVQ_DIR, KRDR.NQ_DIR, KRDR.QC_DIR, KRDR.QCD_DIR, KRDR.QST_DIR, KRDR.QCO_DIR, KRDR.QKF_DIR
QKD_DIR, QKD_FORMAL, QKD_PRE, QSR_DIR, QSR_FORMAL = KRDR.QKD_DIR, KRDR.QKD_FORMAL, KRDR.QKD_PRE, KRDR.QSR_DIR, KRDR.QSR_FORMAL
KRD_FORMAL = KRD_DIR / 'runs/formal-r02'
B3R, V, P, PK, X = KRDR.B3R, KRDR.V, KRDR.P, KRDR.PK, KRDR.X
CF, CFK, LR, B = KRDR.CF, KRDR.CFK, KRDR.LR, KRDR.B
F, L, T1, exp, K = KRDR.F, KRDR.L, KRDR.T1, KRDR.exp, KRDR.K

PLAN_ID = 'KHC-01-K-HISTORY-CARRIER-v1'
PLAN_DOCS = [REPO / 'docs/cache-k-history-carrier-plan-v1-2026-11-03.zh-CN.md', REPO / 'docs/cache-khc-self-check-v1-2026-11-03.zh-CN.md']
DESIGN, QC_INPUTS, QC_TOKENS = KRDR.DESIGN, KRDR.QC_INPUTS, KRDR.QC_TOKENS
QCD_G, QST_FORMAL, QCO_FORMAL, QKF_FORMAL = KRDR.QCD_G, KRDR.QST_FORMAL, KRDR.QCO_FORMAL, KRDR.QKF_FORMAL
QC_FORMAL, NQ_FORMAL, SVQ_FORMAL, SP_FORMAL, NR_FORMAL, B3_FORMAL, XC_FORMAL, SK_FORMAL = KRDR.QC_FORMAL, KRDR.NQ_FORMAL, KRDR.SVQ_FORMAL, KRDR.SP_FORMAL, KRDR.NR_FORMAL, KRDR.B3_FORMAL, KRDR.XC_FORMAL, KRDR.SK_FORMAL
SPLIT, A_LAYERS, MAX_NEW, STOP = KRDR.SPLIT, KRDR.A_LAYERS, KRDR.MAX_NEW, KRDR.STOP
DIRECTIONS, OLD_DIRS, NEW_DIR = KRDR.DIRECTIONS, KRDR.OLD_DIRS, KRDR.NEW_DIR
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
ARMS_ALL, QKF_NAME = KRDR.ARMS, KRDR.QKF_NAME
ARMS = {k: ARMS_ALL[k] for k in ('V', 'F', 'Rk', 'Ak', 'Ark')}
ORDERED = (('Rk', 'V'), ('V', 'Rk'), ('Ak', 'F'), ('F', 'Ak'), ('Ark', 'F'), ('F', 'Ark'))     # (receiver, donor)
CELLS = ('00', '10', '01', '11')
NEW_CELLS = ('10', '01')
KRD_CELL = {'00': '01', '11': '11'}
LIMITS = {'preflight': {'formations': 10, 'prefix_prefills': 2, 'formation_token_forwards': 265, 't1': 40, 'c_t2': 232, 'q_extra': 48,
                        'n_steps': 2976 + 2976, 'n_bridge': 0, 'engineering': 96, 'decode_forwards': 6368, 'trajectories': 96 + 96, 'calibrations': 0},
          'formal': {'formations': 240, 'prefix_prefills': 48, 'formation_token_forwards': 6375, 't1': 960, 'c_t2': 5568, 'q_extra': 1152,
                     'n_steps': 71424, 'n_bridge': 2304, 'engineering': 0, 'decode_forwards': 81408, 'trajectories': 2304, 'calibrations': 0}}
GPU_CAP_S = {'preflight': 0.15 * 3600, 'formal': 1.2 * 3600}
STORAGE_LIMIT = 12 * 2 ** 30
ALLK = KRDR.ALLK
COUNT_KEYS = ('formations', 'prefix_prefills', 'formation_token_forwards', 't1', 'c_t2', 'q_extra', 'n_steps', 'n_bridge', 'engineering',
              'decode_forwards', 'trajectories')
PREFLIGHT_ITEMS = KRDR.PREFLIGHT_ITEMS
comp_sha, comp_sha_range, tensor_bytes_sha = KRDR.comp_sha, KRDR.comp_sha_range, KRDR.tensor_bytes_sha
gdn_module, kernel_identity, load_vectors, qkf_traj, conditions, items = KRDR.gdn_module, KRDR.kernel_identity, KRDR.load_vectors, KRDR.qkf_traj, KRDR.conditions, KRDR.items
qkd_records, QHook, fwd, margins, natural = KRDR.qkd_records, KRDR.QHook, KRDR.fwd, KRDR.margins, KRDR.natural


def plan(stage, worker, n_workers):
    return QKDR.plan(stage, worker, n_workers)


def krd_records():
    out = {}
    for w in sorted(KRD_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        for rel, dg in r['record_hashes'].items():
            assert exp.sha(w / rel) == dg, 'KRD record hash'
            rec = exp.read(w / rel)
            assert exp.sha(w / rec['tensor_file']) == r['tensor_hashes'][rec['tensor_file']], 'KRD tensor hash'
            rec['_tensor_path'] = str(w / rec['tensor_file'])
            out[rec['text']] = rec
    return out


def swap(cr, cd, types, G, s, b):
    """Deep copy of receiver; G recurrent states from donor if s, A-layer keys/values from donor if b; gates as KRD swap_H."""
    import torch
    c = copy.deepcopy(cr)
    if s:
        for l in G:
            assert types[l] == 'linear_attention'
            L._set(c.layers[l], 'recurrent_states', L._get(cd.layers[l], 'recurrent_states').clone())
    for l in A_LAYERS:
        assert types[l] == 'full_attention'
        for f in ('keys', 'values'):
            a, bb = L._get(cr.layers[l], f), L._get(cd.layers[l], f)
            assert a.shape == bb.shape, ('KV shape differs', l, f)
            assert torch.equal(a[..., :-1, :], bb[..., :-1, :]), ('KV prefix differs between receiver and donor', l, f)
            if b:
                L._set(c.layers[l], f, bb.clone())
    Sx = lambda cc: tensor_bytes_sha([L._get(cc.layers[l], 'recurrent_states') for l in G])                           # noqa: E731
    KVx = lambda cc: tensor_bytes_sha([L._get(cc.layers[l], f) for l in A_LAYERS for f in ('keys', 'values')])         # noqa: E731
    rest = lambda cc: tensor_bytes_sha([L._get(cc.layers[i], f) for i, k, f in L.component_tensors(cc, types)           # noqa: E731
                                        if not ((k == 'recurrent' and i in G) or (k == 'kv' and i in A_LAYERS))])
    assert Sx(c) == Sx(cd if s else cr) and KVx(c) == KVx(cd if b else cr) and rest(c) == rest(cr), 'S/KV swap touched the wrong components'
    return c


def run_item(engine, unit, contexts, calib, conds, qctok, output, stage, vecs=None, refs=None):
    import torch
    model, tok = engine.model, engine.tokenizer
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
    assert tuple(G) == (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
    assert tuple(i for i, k in enumerate(types) if k == 'full_attention' and i >= SPLIT) == A_LAYERS
    KRDR.QHOOK_ORIG[0] = gdn_module().torch_recurrent_gated_delta_rule
    a = unit['item_id']
    counts = {k: 0 for k in COUNT_KEYS}
    tensors, gates, out = {}, {}, {}
    C, T, info = QCOR.form_text(engine, a, contexts, calib, conds, qctok, counts)
    hC, hT = comp_sha(C, types, ALLK, 0), {d: comp_sha(T[d], types, ALLK, 0) for d in conds}
    it, code_tok, n = info['item'], info['code_tokens'], info['n']
    comp = it['first_listed'] if it['target'] != it['first_listed'] else it['listed_codes'][1]
    qkd, krd = refs['qkd'][a], refs['krd'][a]
    qkd_t = torch.load(qkd['_tensor_path'], map_location='cpu')
    krd_t = torch.load(krd['_tensor_path'], map_location='cpu')
    dec = lambda ids: tok.decode(ids, skip_special_tokens=False)   # noqa: E731
    for d in conds:
        s = info['scenario']
        kd = krd['directions'][d]
        fF = (refs['qkf'][a][f'F|{d}']['ids'] if d in OLD_DIRS else refs['qco'][a][f'F|{d}']['ids'])[0]
        assert fF not in STOP and fF == kd['fF']
        c1, x, h1, ref = {}, {}, {}, {}
        for arm, (base, u, sign) in ARMS.items():
            qb = T[d] if base == 'T' else C
            vec = None if u is None else QKFR.mask_vec(vecs[u][f'{s}|{d}'].float(), 'k')
            cc, _ = QKFR.edited_arm(T[d], qb, C, G, vec, sign)
            QCOR.check_edit(T[d], qb, C, cc, types, G, vec is not None, f'{arm}|{d}')
            c1[arm], z1 = fwd(engine, cc, info['last'], n - 1, counts, 't1')
            ref[arm] = refs['qkf'][a][f'{QKF_NAME[arm]}|{d}'] if d in OLD_DIRS else qkd['c1343_trajectories'][arm]
            h1[arm] = comp_sha(c1[arm], types, ALLK, 0)
            assert F.th(z1) == ref[arm]['first']['logits_sha256'] and h1[arm] == ref[arm]['first']['cache_sha256'], ('t1 != reference', arm, d)
            x[arm] = int(z1.argmax())
            assert x[arm] == ref[arm]['ids'][0] == kd['x'][arm]
        assert len({comp_sha_range(c1[arm], types, ALLK, 0, SPLIT) for arm in ARMS}) == 1, 'shallow caches differ across arms after t1'
        QC, C00 = {}, {}
        for arm in ARMS:
            hk = QHook(model, G, 'capture')
            _, z = fwd(engine, copy.deepcopy(c1[arm]), fF, n, counts, 'c_t2', hook=hk)
            QC[arm] = hk.got
            M, Mall = margins(z, it, code_tok, comp)
            assert M == qkd['arms'][d][arm]['M'] and M == kd['C00'][arm]['M'], ('C t2 margin != QKD/KRD', arm, d)
            assert torch.equal(z.to(torch.bfloat16).cpu(), qkd_t[f'Ct2|{arm}|{d}']), ('C t2 logits != QKD', arm, d)
            C00[arm] = {'M': M, 'M_all': Mall, 't2_sha': F.th(z)}
            if stage == 'preflight':
                _, z0 = fwd(engine, copy.deepcopy(c1[arm]), fF, n, counts, 'engineering')
                hs = QHook(model, G, 'replace', QC[arm])
                _, zs = fwd(engine, swap(c1[arm], c1[arm], types, G, True, True), fF, n, counts, 'engineering', hook=hs)
                assert torch.equal(z0, z) and torch.equal(zs, z), ('self/no-hook C forward differs', arm, d)
        cells = {}
        for r_, d_ in ORDERED:
            pk = f'{r_}<-{d_}'
            qn = None
            if x[r_] not in STOP:
                hk = QHook(model, G, 'capture')
                fwd(engine, copy.deepcopy(c1[d_]), x[r_], n, counts, 'q_extra', hook=hk)
                qn = hk.got
            for sb in CELLS:
                sS, bKV = sb[0] == '1', sb[1] == '1'
                base = swap(c1[r_], c1[d_], types, G, sS, bKV)
                hk = QHook(model, G, 'replace', QC[d_])
                _, z = fwd(engine, copy.deepcopy(base), fF, n, counts, 'c_t2', hook=hk)
                M, Mall = margins(z, it, code_tok, comp)
                cell = {'C': {'M': M, 'M_all': Mall, 't2_sha': F.th(z)}}
                tensors[f'C|{pk}|{sb}|{d}'] = z.to(torch.bfloat16).cpu()
                if sb in KRD_CELL:
                    kc = f'{pk}|{KRD_CELL[sb]}'
                    assert M == kd['cells'][kc]['C']['M'] and torch.equal(z.to(torch.bfloat16).cpu(), krd_t[f'C|{kc}|{d}']), ('C != KRD', kc, d)
                    old = kd['cells'][kc]['N']
                    if x[r_] in STOP:
                        assert not old['reached_t2']
                        cell['N'] = dict(old, source=f'KRD-r02 {kc}')
                    elif stage == 'preflight':
                        hk = QHook(model, G, 'replace', qn)
                        rn, z2 = natural(engine, base, x[r_], n, counts, hook=hk)
                        assert rn['ids'] == old['ids'] and rn['termination'] == old['termination'], ('N replay != KRD', kc, d)
                        assert torch.equal(z2.to(torch.bfloat16), krd_t[f'N|{kc}|{d}']), ('N t2 logits != KRD', kc, d)
                        cell['N'] = dict(old, source=f'KRD-r02 {kc} (full replay passed)')
                    else:
                        hk = QHook(model, G, 'replace', qn)
                        _, z2 = fwd(engine, base, x[r_], n, counts, 'n_bridge', hook=hk)
                        assert torch.equal(z2.to(torch.bfloat16).cpu(), krd_t[f'N|{kc}|{d}']), ('N bridge t2 logits != KRD', kc, d)
                        assert int(z2.argmax()) == old['ids'][1], ('N bridge token != KRD', kc, d)
                        cell['N'] = dict(old, source=f'KRD-r02 {kc} (t2 bridge passed)')
                else:
                    if x[r_] in STOP:
                        cell['N'] = {'ids': [x[r_]], 'termination': 'stop', 'reached_t2': False, 'text': dec([x[r_]])}
                    else:
                        hk = QHook(model, G, 'replace', qn)
                        rn, z2 = natural(engine, base, x[r_], n, counts, hook=hk)
                        rn['text'] = dec(rn['ids'])
                        cell['N'] = rn
                        tensors[f'N|{pk}|{sb}|{d}'] = z2.to(torch.bfloat16)
                cells[f'{pk}|{sb}'] = cell
                del base
        for arm in ARMS:
            assert comp_sha(c1[arm], types, ALLK, 0) == h1[arm], ('source post-t1 cache modified', arm, d)
        out[d] = {'fF': fF, 'x': x, 'C00_arms': C00, 'cells': cells}
        del c1, QC
        torch.cuda.empty_cache()
    assert hC == comp_sha(C, types, ALLK, 0) and all(comp_sha(T[d], types, ALLK, 0) == hT[d] for d in conds), 'donor modified'
    F.assert_no_hooks(model)
    gates['replay'] = ('t1 logits/cache == QKF/QKD, x == KRD; arm C t2 M/logits == QKD/KRD; cells 00/11 C M and bf16 logits == KRD 01/11; '
                       'N 00/11: ' + ('full trajectory replay == KRD' if stage == 'preflight' else 't2 bf16 logits and next token == KRD (bridge)'))
    gates['swap'] = 'only the named S (G recurrent) / KV (A keys, values) copied from donor; all else == receiver; KV prefix equal'
    gates['q_node'] = 'Q hook fired exactly once per G layer on t2 only; effective kernel query == donor source; wrapper removed after each forward'
    gates['sources'] = 'post-t1 source caches unchanged after all cells; C/T donors unchanged; shallow caches identical across arms after t1'
    if stage == 'preflight':
        gates['self_ops'] = 'C route: no-hook, self-Q replacement with self S+KV swap, and capture forwards identical bit for bit'
    gates['calibration'] = 'NQ-01 saved scenario calibration (source hash in receipt)'
    body = {'text': a, 'scenario': info['scenario'], 'item': it, 'code_tokens': code_tok, 'competitor': comp, 'directions': out,
            'kernel_identity': kernel_identity(), 'calibration': calib, 'counts': counts, 'gates': gates}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', DESIGN, QC_INPUTS, QC_TOKENS, KRD_DIR / 'krd_run.py', KRD_DIR / 'freeze-r02.json', KRD_DIR / 'analysis/krd-readouts-r02.json',
         QSR_DIR / 'qsr_run.py', QKD_DIR / 'qkd_run.py', QKDR.RPOST_C_MANIFEST, QKD_DIR / 'freeze-r02.json', QKF_DIR / 'qkf_run.py',
         QKFR.RPOST_MANIFEST, QCO_DIR / 'qco_run.py', QKFR.QCO_MANIFEST, QST_DIR / 'qst_core.py', SVQ_DIR / 'svq_run.py', FC_DIR / 'fc_core.py'] + PLAN_DOCS
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
    refs = {'qkf': qkf_traj(), 'qco': QKFR.qco_traj(), 'qkd': qkd_records(), 'krd': krd_records()}
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
    lock = open(f'/tmp/acupuncture-khc-worker{worker}.lock', 'w')
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
            assert set(x['cells']) == {f'{r_}<-{d_}|{sb}' for r_, d_ in ORDERED for sb in CELLS} and set(x['C00_arms']) == set(ARMS)
        for g in ('replay', 'swap', 'q_node', 'sources', 'calibration') + (('self_ops',) if r['stage'] == 'preflight' else ()):
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
            cmd = [sys.executable, '-u', str(HERE / 'khc_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
