"""QKD-01: what computation does the common k offset change?  (plan docs/cache-k-computation-diagnostic-plan-v1-2026-11-03.zh-CN.md;
CONTRACT r01).  Six arms per input x direction (V, F, Rk = T - mu_k, Ak = C + mu_k, Rrk = T - r_post_k, Ark = C + r_post_k) on the
QKF mixed background, four directions (C1343 r_post built here with the QKF formula).  For the first three decoding computations a
read-only wrapper around transformers' torch_recurrent_gated_delta_rule captures (q, k, v, g, beta, S_prev, o) in the 14 G layers;
o is decomposed D = a S^T q, E = -a b (q.k) S^T k, W = b (q.k) v (FP64), and pairwise k-only counterfactuals J / H are computed.
Routes: N (natural greedy, <= 3 steps) and C (t1 shared, then F's first two answer tokens forced).  C1343: full answers generated
with the frozen SVQ generate (no observer).
python qkd_run.py freeze PATH | run ... | verify WORKER_DIR | launch ...
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
QKF_DIR = HERE.parent / 'cache-qk-component-factor-v1-2026-11-02'
sys.path.insert(0, str(QKF_DIR))
sys.path.insert(0, str(HERE))
import qkf_run as QKFR  # noqa: E402  (frozen QKF-01 runner: form_text, edited_arm, mask_vec, check_edit, vectors, QCO chain)

QCOR, QSTR, QCDR, QCR, NQR, SVQ, NRR = QKFR.QCOR, QKFR.QSTR, QKFR.QCDR, QKFR.QCR, QKFR.NQR, QKFR.SVQ, QKFR.NRR
FC_DIR, SP_DIR, SVQ_DIR, NQ_DIR, QC_DIR, QCD_DIR, QST_DIR, QCO_DIR = QKFR.FC_DIR, QKFR.SP_DIR, QKFR.SVQ_DIR, QKFR.NQ_DIR, QKFR.QC_DIR, QKFR.QCD_DIR, QKFR.QST_DIR, QKFR.QCO_DIR
B3R, V, P, PK, X = QKFR.B3R, QKFR.V, QKFR.P, QKFR.PK, QKFR.X
CF, CFK, LR, B = QKFR.CF, QKFR.CFK, QKFR.LR, QKFR.B
F, L, T1, exp, K = QKFR.F, QKFR.L, QKFR.T1, QKFR.exp, QKFR.K

PLAN_ID = 'QKD-01-K-COMPUTATION-DIAGNOSTIC-v1'
PLAN_DOCS = [REPO / 'docs/cache-k-computation-diagnostic-plan-v1-2026-11-03.zh-CN.md', REPO / 'docs/cache-qkd-self-check-v1-2026-11-03.zh-CN.md']
DESIGN = QKFR.DESIGN
QC_INPUTS, QC_TOKENS = QKFR.QC_INPUTS, QKFR.QC_TOKENS
QCD_G, QST_FORMAL, QCO_FORMAL, QKF_FORMAL = QKFR.QCD_G, QKFR.QST_FORMAL, QKFR.QCO_FORMAL, QKF_DIR / 'runs/formal-r01'
RPOST_C = HERE / 'runs/rpost-r01/rpost-c1343.pt'
RPOST_C_MANIFEST = HERE / 'analysis/rpost-c1343-manifest-r01.json'
PREFLIGHT_RECEIPT = HERE / 'runs/preflight-r01/verification.json'
QC_FORMAL, NQ_FORMAL, SVQ_FORMAL, SP_FORMAL, NR_FORMAL, B3_FORMAL, XC_FORMAL, SK_FORMAL = QKFR.QC_FORMAL, QKFR.NQ_FORMAL, QKFR.SVQ_FORMAL, QKFR.SP_FORMAL, QKFR.NR_FORMAL, QKFR.B3_FORMAL, QKFR.XC_FORMAL, QKFR.SK_FORMAL
SPLIT = 13
DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'N_L00_C1343_D-1')
OLD_DIRS = DIRECTIONS[:3]
NEW_DIR = 'N_L00_C1343_D-1'
PREFLIGHT_ITEMS = ('NA-NQ01-ABC-A', 'NA-NQ02-ABC-B')
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
STOP = QKFR.STOP
LIMITS = {'preflight': {'formations': 10, 'trajectories': 12, 'decode_forwards': 768, 'diagnostics': 12, 'calibrations': 0},
          'formal': {'formations': 240, 'trajectories': 288, 'decode_forwards': 14976, 'diagnostics': 288, 'calibrations': 0}}
GPU_CAP_S = {'preflight': 0.15 * 3600, 'formal': 1.2 * 3600}
STORAGE_LIMIT = 20 * 2 ** 30
QK, HALF = QKFR.QK, 2048
ARMS = {'V': ('T', None, 1), 'F': ('C', None, 1), 'Rk': ('T', 'mu', -1), 'Ak': ('C', 'mu', 1), 'Rrk': ('T', 'post', -1), 'Ark': ('C', 'post', 1)}
QKF_NAME = {'V': 'V', 'F': 'F', 'Rk': 'R_mu_k', 'Ak': 'A_mu_k', 'Rrk': 'R_post_k', 'Ark': 'A_post_k'}
PAIRS = (('Rk', 'V'), ('Ak', 'F'), ('Rrk', 'V'), ('Ark', 'F'))
ERR_CAP, ERR_FLOOR, RESOLVE_MULT = 0.02, 1e-5, 5.0
OFF_DIR = 'N_L00_C4146_D-1'
ALLK = ('recurrent', 'kv', 'conv')
COUNT_KEYS = ('formations', 'trajectories', 'decode_forwards', 'diagnostics', 'prefix_prefills', 'formation_token_forwards')
comp_sha = NRR.comp_sha
shared_tokens, generate = QKFR.shared_tokens, QKFR.generate


def conditions():
    c = QCOR.conditions()
    return {d: c[d] for d in DIRECTIONS}


def items():
    return QKFR.items()


plan = QKFR.plan


def gdn_module():
    import transformers.models.qwen3_5.modeling_qwen3_5 as QM
    return QM


def kernel_identity():
    """The decode recurrence and conv update must be the local torch implementations (no FLA / Hub kernel)."""
    import importlib.util
    QM = gdn_module()
    f = QM.torch_recurrent_gated_delta_rule
    return {'fla': importlib.util.find_spec('fla') is not None, 'kernels': importlib.util.find_spec('kernels') is not None,
            'causal_conv1d': importlib.util.find_spec('causal_conv1d') is not None,
            'recurrent_fn_module': getattr(f, '__module__', None), 'recurrent_fn_name': getattr(f, '__name__', None), 'module_file': QM.__file__}


def load_vectors():
    import torch
    v = QKFR.load_vectors()
    rp = exp.read(RPOST_C_MANIFEST)
    assert rp['status'] == 'passed' and exp.sha(RPOST_C) == rp['rpost_sha256'], 'C1343 r_post != manifest'
    v['post'] = dict(v['post'])
    v['post'].update(torch.load(RPOST_C)['r_post'])
    return v


def qkf_traj():
    out = {}
    for w in sorted(QKF_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        for rel, dg in r['record_hashes'].items():
            assert exp.sha(w / rel) == dg, 'QKF record hash'
            rec = exp.read(w / rel)
            out[rec['text']] = rec['trajectories']
    return out


class Capture:
    """Read-only capture of the gated delta rule inputs/outputs per G layer during selected forwards."""

    def __init__(self, model, G):
        self.model, self.G = model, set(G)
        self.QM = gdn_module()
        self.orig = self.QM.torch_recurrent_gated_delta_rule
        self.layer, self.rec, self.handles = None, None, []

    def __enter__(self):
        assert self.QM.torch_recurrent_gated_delta_rule is self.orig
        layers = L.model_layers(self.model)
        for i, lay in enumerate(layers):
            la = getattr(lay, 'linear_attn', None)
            if la is not None:
                def pre(_m, _a, i=i):
                    self.layer = i
                self.handles.append(la.register_forward_pre_hook(pre))
        orig, me = self.orig, self

        def wrapper(query, key, value, g=None, beta=None, initial_state=None, output_final_state=False, use_qk_l2norm_in_kernel=False, **kw):
            S = initial_state.detach().clone() if (me.rec is not None and me.layer in me.G and initial_state is not None) else None
            out = orig(query, key, value, g=g, beta=beta, initial_state=initial_state, output_final_state=output_final_state,
                       use_qk_l2norm_in_kernel=use_qk_l2norm_in_kernel, **kw)
            if S is not None:
                me.rec[me.layer] = {'q': query.detach().clone(), 'k': key.detach().clone(), 'v': value.detach().clone(), 'g': g.detach().clone(),
                                    'beta': beta.detach().clone(), 'S': S, 'o': out[0].detach().clone(), 'l2': use_qk_l2norm_in_kernel}
            return out
        self.QM.torch_recurrent_gated_delta_rule = wrapper
        return self

    def __exit__(self, *exc):
        self.QM.torch_recurrent_gated_delta_rule = self.orig
        for h in self.handles:
            h.remove()
        self.handles = []
        return False


def decompose(c, orig):
    """FP64 D/E/W of one captured call (decode step, seq 1).  Also re-runs the original kernel on clones (wiring check)."""
    import torch
    QM = gdn_module()
    q, k = c['q'].float(), c['k'].float()
    qn = QM.l2norm(q, dim=-1, eps=1e-6) / (q.shape[-1] ** 0.5)
    kn = QM.l2norm(k, dim=-1, eps=1e-6)
    qn, kn = qn[0, 0].double(), kn[0, 0].double()                       # [32, 128]
    v = c['v'].float()[0, 0].double()                                    # [32, 128]
    a = c['g'].float()[0, 0].exp().double()                              # [32]
    b = c['beta'].float()[0, 0].double()                                 # [32]
    S = c['S'].float()[0].double()                                       # [32, 128 (k), 128 (v)]
    o = c['o'].float()[0, 0].double()                                    # [32, 128]
    Sq = torch.einsum('hkv,hk->hv', S, qn)
    p = torch.einsum('hkv,hk->hv', S, kn)
    qk = (qn * kn).sum(-1)
    D = a[:, None] * Sq
    E = -(a * b * qk)[:, None] * p
    W = (b * qk)[:, None] * v
    err = (D + E + W - o).norm(dim=-1) / torch.clamp(D.norm(dim=-1) + E.norm(dim=-1) + W.norm(dim=-1), min=1e-12)
    abs_err = (D + E + W - o).norm(dim=-1)
    re, _ = orig(c['q'].clone(), c['k'].clone(), c['v'].clone(), g=c['g'].clone(), beta=c['beta'].clone(), initial_state=c['S'].clone(),
                 output_final_state=True, use_qk_l2norm_in_kernel=c['l2'])
    wired = bool(torch.equal(re, c['o']))
    return {'qn': qn, 'kn': kn, 'v': v, 'a': a, 'b': b, 'S': S, 'o': o, 'D': D, 'E': E, 'W': W, 'err': err, 'abs_err': abs_err, 'wired': wired}


def pair_stats(r, s):
    """Recipient r, other end s (same layer/step/token): J/H k-only counterfactual with r's q, S, v, a, b; actual differences."""
    import torch
    a0, a1 = (r['qn'] * r['kn']).sum(-1), (r['qn'] * s['kn']).sum(-1)
    p0 = torch.einsum('hkv,hk->hv', r['S'], r['kn'])
    p1 = torch.einsum('hkv,hk->hv', r['S'], s['kn'])
    al, be = r['a'][:, None], r['b'][:, None]
    J = be * (a1 - a0)[:, None] * (r['v'] - al * (p0 + p1) / 2)
    H = -al * be * ((a0 + a1) / 2)[:, None] * (p1 - p0)
    dk = J + H
    dact = s['o'] - r['o']
    res = dact - dk
    nk2 = (dk * dk).sum(-1)
    na2 = (dact * dact).sum(-1)
    resolvable = dact.norm(dim=-1) > RESOLVE_MULT * (r['abs_err'] + s['abs_err'])
    safe = lambda num, den: torch.where(den > 0, num / torch.clamp(den, min=1e-300), torch.full_like(num, float('nan')))   # noqa: E731
    out = {'sJ': safe((J * dk).sum(-1), nk2), 'sH': safe((H * dk).sum(-1), nk2), 'n_dk': dk.norm(dim=-1), 'n_dact': dact.norm(dim=-1),
           'n_res': res.norm(dim=-1), 'n_J': J.norm(dim=-1), 'n_H': H.norm(dim=-1), 'resolvable': resolvable.double()}
    for t in ('D', 'E', 'W'):
        out['s' + t] = safe(((s[t] - r[t]) * dact).sum(-1), na2)
    return torch.stack([out[k] for k in PAIR_FIELDS], -1)              # [32, len(PAIR_FIELDS)]


PAIR_FIELDS = ('sJ', 'sH', 'n_dk', 'n_dact', 'n_res', 'n_J', 'n_H', 'resolvable', 'sD', 'sE', 'sW')


def step(engine, cache, tok, pos, counts):
    import torch
    with torch.inference_mode():
        out = L.forward(engine.model, [tok], pos, cache)
    counts['decode_forwards'] += 1
    z = out.logits[0, -1].float()
    assert torch.isfinite(z).all()
    return out.past_key_values, z


def observe(engine, cache0, last, n, ftoks, types, G, counts, capture=True):
    """N route (natural greedy, <= 3 forwards, stop at a stop token) and C route (t1 shared; t2, t3 forced F tokens)."""
    import torch
    cap = Capture(engine.model, G) if capture else None
    res = {'N_tokens': [], 'N_sha': [], 'N_cache': [], 'caps': {}, 'C_missing': ftoks is None}
    c = copy.deepcopy(cache0)
    tok, pos = last, n - 1
    c1 = None
    for s in (1, 2, 3):
        if capture:
            with cap:
                cap.rec = {}
                c, z = step(engine, c, tok, pos, counts)
                res['caps'][('N', s)] = cap.rec
        else:
            c, z = step(engine, c, tok, pos, counts)
        nxt = int(z.argmax())
        res['N_tokens'].append(nxt)
        res['N_sha'].append(F.th(z))
        res['N_cache'].append(comp_sha(c, types, ALLK, 0))
        if s == 1:
            c1 = copy.deepcopy(c)
        if nxt in STOP:
            break
        tok, pos = nxt, pos + 1
    if capture and ftoks is not None:
        cc = c1
        for s, ft in ((2, ftoks[0]), (3, ftoks[1])):
            with cap:
                cap.rec = {}
                cc, z = step(engine, cc, ft, n - 1 + (s - 1), counts)
                res['caps'][('C', s)] = cap.rec
            if s == 2:
                res['C_t2_logits'] = z.detach().to('cpu').clone()
        res['caps'][('C', 1)] = res['caps'][('N', 1)]
    return res


def run_item(engine, unit, contexts, calib, conds, qctok, output, stage, vecs=None, refs=None):
    import torch
    model, tok = engine.model, engine.tokenizer
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
    assert tuple(G) == (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
    a = unit['item_id']
    counts = {k: 0 for k in COUNT_KEYS}
    tensors, gates, arms_out, pairs_out, c1343 = {}, {}, {}, {}, {}
    C, T, info = QCOR.form_text(engine, a, contexts, calib, conds, qctok, counts)
    hC = comp_sha(C, types, ALLK, 0)
    hT = {d: comp_sha(T[d], types, ALLK, 0) for d in conds}
    it = info['item']
    code_tok = info['code_tokens']
    comp = it['first_listed'] if it['target'] != it['first_listed'] else it['listed_codes'][1]
    orig = gdn_module().torch_recurrent_gated_delta_rule
    err_max, wired_all = 0.0, True
    for d in conds:
        s = info['scenario']
        old = refs['qkf'][a] if d in OLD_DIRS else None
        if d in OLD_DIRS:
            fids = old[f'F|{d}']['ids']
        else:
            fids = refs['qco'][a][f'F|{d}']['ids']
        ftoks = fids[:2] if len(fids) >= 2 and fids[0] not in STOP and fids[1] not in STOP else None
        dec, obs = {}, {}
        for arm, (base, u, sign) in ARMS.items():
            qb = T[d] if base == 'T' else C
            vec = None if u is None else QKFR.mask_vec(vecs[u][f'{s}|{d}'].float(), 'k')
            cc, _ = QKFR.edited_arm(T[d], qb, C, G, vec, sign)
            QCOR.check_edit(T[d], qb, C, cc, types, G, vec is not None, f'{arm}|{d}')
            entry = {}
            if d == NEW_DIR:
                F.assert_no_hooks(model)
                r, lg = generate(engine, cc, info['last'], info['n'], info['q_shared'], info['watch'], types, counts)
                counts['trajectories'] += 1
                r['text'] = tok.decode(r['ids'], skip_special_tokens=False)
                c1343[arm] = r
                tensors[f'gen|{arm}'] = lg
                if arm in ('V', 'F'):
                    o = refs['qco'][a][f'{arm}|{d}']
                    assert r['ids'] == o['ids'] and r['first']['logits_sha256'] == o['first']['logits_sha256'] and r['diag'] == o['diag'], ('C1343 replay != QCO', arm)
                ref_ids, ref_sha, ref_cache = r['ids'], r['first']['logits_sha256'], r['first']['cache_sha256']
            else:
                o = old[f'{QKF_NAME[arm]}|{d}']
                ref_ids, ref_sha, ref_cache = o['ids'], o['first']['logits_sha256'], o['first']['cache_sha256']
            F.assert_no_hooks(model)
            ob = observe(engine, cc, info['last'], info['n'], ftoks, types, G, counts, capture=True)
            F.assert_no_hooks(model)
            assert gdn_module().torch_recurrent_gated_delta_rule is orig, 'capture wrapper left installed'
            assert ob['N_tokens'] == ref_ids[:len(ob['N_tokens'])], ('N route tokens != reference', arm, d)
            assert ob['N_sha'][0] == ref_sha and ob['N_cache'][0] == ref_cache, ('t1 != reference', arm, d)
            if stage == 'preflight':
                off = observe(engine, cc, info['last'], info['n'], None, types, G, counts, capture=False)
                assert off['N_tokens'] == ob['N_tokens'] and off['N_sha'] == ob['N_sha'] and off['N_cache'] == ob['N_cache'], ('observer changed the path', arm, d)
            dd = {}
            for key, rec in ob['caps'].items():
                assert set(rec) == set(G), ('capture missed a layer', arm, d, key)
                dd[key] = {l: decompose(rec[l], orig) for l in G}
                for l in G:
                    err_max = max(err_max, float(dd[key][l]['err'].max()))
                    wired_all &= dd[key][l]['wired']
            dec[arm] = dd
            entry.update({'N_tokens': ob['N_tokens'], 'C_missing': ob['C_missing'],
                          'err_max': max(float(dd[k][l]['err'].max()) for k in dd for l in G)})
            if 'C_t2_logits' in ob:
                z2 = ob['C_t2_logits']
                entry['M'] = float(z2[code_tok[it['target']]] - z2[code_tok[comp]])
                tensors[f'Ct2|{arm}|{d}'] = z2.to(torch.bfloat16)
            obs[arm] = ob['N_tokens']
            arms_out.setdefault(d, {})[arm] = entry
            del cc
        for x, y in PAIRS:
            for recip, other in ((x, y), (y, x)):
                for route, steps in (('C', (1, 2, 3)), ('N', (2, 3))):
                    for st_ in steps:
                        if (route, st_) not in dec[recip] or (route, st_) not in dec[other]:
                            continue
                        if route == 'N' and obs[recip][:st_ - 1] != obs[other][:st_ - 1]:
                            continue
                        tens = torch.stack([pair_stats(dec[recip][(route, st_)][l], dec[other][(route, st_)][l]) for l in G])   # [14, 32, F]
                        key = f'{x}|{y}|r={recip}|{route}{st_}|{d}'
                        tensors[f'pair|{key}'] = tens.float()
                        ok = tens[..., PAIR_FIELDS.index('resolvable')] > 0
                        summ = {'n_resolvable': int(ok.sum()), 'n': int(ok.numel())}
                        for f in ('sJ', 'sH', 'sD', 'sE', 'sW'):
                            vals = tens[..., PAIR_FIELDS.index(f)][ok]
                            vals = vals[torch.isfinite(vals)]
                            summ[f'median_{f}'] = float(vals.median()) if vals.numel() else None
                        for f in ('n_dk', 'n_dact', 'n_res', 'n_J', 'n_H'):
                            summ[f'median_{f}'] = float(tens[..., PAIR_FIELDS.index(f)].median())
                        summ['median_sH_by_layer'] = [float(tens[j, :, PAIR_FIELDS.index('sH')][ok[j]].median()) if bool(ok[j].any()) else None for j in range(len(G))]
                        pairs_out[key] = summ
        del dec
        torch.cuda.empty_cache()
    gates['replay'] = ('old directions: N-route tokens and t1 logits/cache hashes == QKF; C1343: V/F full answers == QCO (ids, first-step hash, '
                       'diagnostic) and N-route == own generation')
    gates['sources'] = 'every arm: V block == C(a), k slot 0 == base, S/KV/shallow == T(a,d); unedited q/k == base; donors unchanged'
    gates['capture'] = 'read-only wrapper; all 14 G layers captured per observed step; wrapper removed and no hooks before every arm'
    gates['wiring'] = 'kernel re-run on captured clones == captured output bit for bit' if wired_all else None
    if stage == 'preflight':
        gates['observer_off'] = 'N route with and without the observer: tokens, logits hashes and cache hashes identical'
    assert wired_all, 'wiring check failed'
    assert comp_sha(C, types, ALLK, 0) == hC and all(comp_sha(T[d], types, ALLK, 0) == hT[d] for d in conds), 'donor modified'
    F.assert_no_hooks(model)
    gates['calibration'] = 'NQ-01 saved scenario calibration (source hash in receipt)'
    body = {'text': a, 'scenario': info['scenario'], 'item': it, 'code_tokens': code_tok, 'competitor': comp, 'arms': arms_out, 'pairs': pairs_out,
            'c1343_trajectories': c1343, 'err_max': err_max, 'kernel_identity': kernel_identity(), 'calibration': calib,
            'counts': counts, 'gates': gates}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', DESIGN, QC_INPUTS, QC_TOKENS, QKF_DIR / 'qkf_run.py', QKF_DIR / 'qkf_rpost.py', QKF_DIR / 'qkf_core.py', QKFR.RPOST_MANIFEST, QCO_DIR / 'qco_run.py', QKFR.QCO_MANIFEST, QST_DIR / 'qst_run.py', QST_DIR / 'qst_core.py', QCD_DIR / 'qcd_run.py', SVQ_DIR / 'svq_run.py', FC_DIR / 'fc_core.py'] + PLAN_DOCS
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
    return own + b3 + xc + sk + nr + sp + svq + nq + qcd + qst + qco + qkf + [p for p in B3R.frozen_paths() if p not in own]


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
    man = exp.read(RPOST_C_MANIFEST)
    assert man['status'] == 'passed' and man['freeze_sha256'] == auth['freeze_sha256'] and exp.sha(RPOST_C) == man['rpost_sha256']
    assert auth['required_evidence'].get('analysis/rpost-c1343-manifest-r01.json') == exp.sha(RPOST_C_MANIFEST)
    ki = kernel_identity()
    assert not ki['fla'] and not ki['kernels'] and not ki['causal_conv1d'], ('non-torch kernel available', ki)
    if stage == 'formal':
        pre = exp.read(HERE / auth['preflight_verification_path'])
        assert pre['status'] == 'passed' and pre['freeze_sha256'] == auth['freeze_sha256'] and pre['stage'] == 'preflight'
    return auth


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
    refs = {'qkf': qkf_traj(), 'qco': QKFR.qco_traj()}
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
    lock = open(f'/tmp/acupuncture-qkd-worker{worker}.lock', 'w')
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
        receipt['summary'] = execute(engine, stage, output, receipt, units, gpu)
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
        assert all(t['diag'] and 'watch' in t['diag'] for t in rec['trajectories'].values()), 'missing diagnostic'
        assert set(rec['arms']) == set(DIRECTIONS) and all(set(v) == set(ARMS) for v in rec['arms'].values())
        assert set(rec['c1343_trajectories']) == set(ARMS)
        for g in ('replay', 'sources', 'capture', 'wiring', 'calibration') + (('observer_off',) if r['stage'] == 'preflight' else ()):
            assert rec['gates'][g], g
        if r['stage'] == 'formal':
            assert rec['err_max'] <= ERR_CAP, ('formal decomposition error above cap', rec['err_max'])
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
            cmd = [sys.executable, '-u', str(HERE / 'qkd_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
