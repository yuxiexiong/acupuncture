"""CFM-S1 offline accounting (CONTRACT.zh-CN.md §5-§8). CPU, float64; never loads a model.

Source update (key x value orientation, transformers 5.20.2 torch_recurrent_gated_delta_rule):
    S_t = A_t S_{t-1} + B_t,   A_t = alpha_t (I - beta_t k_t k_t^T),   B_t = beta_t k_t v_t^T,   o_t = S_t^T q_t
with k, q l2-normalised in the kernel and q scaled by d_k^-1/2. Symmetric account (Delta = T - C, bar = mean):
    Delta S_t = Abar_t Delta S_{t-1} + Delta A_t Sbar_{t-1} + Delta B_t
All means, products and terms live offline; nothing here is fed back into a model.

python account.py run RUN_DIR [RUN_DIR ...] --out ANALYSIS_DIR
python account.py selftest
"""
import argparse
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
LAYERS = (16, 17, 18)
SEGMENTS = ('head', 'fact', 'question', 'instruction', 'tail', 'last', 'cand')
EARLY = ('head', 'fact')
LATE_PLUS = ('question', 'instruction', 'tail', 'last')
ACCOUNTS = ('sym', 'bgT', 'bgC')  # symmetric; T-background A^T dS + dA S^C + dB; C-background A^C dS + dA S^T + dB
# Contract §6.2 engineering tolerances, frozen before any formal output is opened.
TOL = {'state_rel': 1e-3, 'out_rel': 1e-2, 'identity_rel': 1e-9, 'contraction_slack': 1e-9, 'resolve_factor': 10.0}
# Contract §7 pre-registered branch rules (main) and the two sensitivity settings reported beside them.
RULES = {'main': {'w_early_min': 0.5, 'r_max': 0.3, 'r_late_min': 0.3, 'rho_min': 0.5, 'cancel_min': 2.0},
         'strict': {'w_early_min': 0.6, 'r_max': 0.2, 'r_late_min': 0.4, 'rho_min': 0.6, 'cancel_min': 1.5},
         'loose': {'w_early_min': 0.4, 'r_max': 0.4, 'r_late_min': 0.2, 'rho_min': 0.4, 'cancel_min': 2.5}}
SUPPORT_MIN = 4  # of six bases
BRANCHES = ('early_write', 'late_processing', 'coupled', 'readout_disconnect')


def torch():
    import torch as t
    return t


def common_prefix(a, b):
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


# ---------------------------------------------------------------- drivers and reconstruction

def l2n(x):
    t = torch()
    return x * t.rsqrt((x * x).sum(-1, keepdim=True) + 1e-6)


def prepare(drv):
    """Kernel-convention drivers in float64: unit k, unit q scaled by d^-1/2, alpha = exp(g)."""
    q, k = drv['q'].double(), drv['k'].double()
    return {'q': l2n(q) * q.shape[-1] ** -0.5, 'k': l2n(k), 'v': drv['v'].double(),
            'alpha': drv['g'].double().exp(), 'beta': drv['beta'].double()}


def apply_A(Z, alpha, beta, k):
    """A Z = alpha (Z - beta k (k^T Z)), per head; Z (H, dk, dv), alpha/beta (H,), k (H, dk)."""
    t = torch()
    kz = t.einsum('hk,hkv->hv', k, Z)
    return alpha[:, None, None] * (Z - beta[:, None, None] * k[:, :, None] * kz[:, None, :])


def write_term(beta, k, v):
    return beta[:, None, None] * k[:, :, None] * v[:, None, :]


def readout(S, q):
    return torch().einsum('hkv,hk->hv', S, q)


def concat_phase(entries):
    t = torch()
    return t.cat(entries, 0) if entries else None


def from_capture(tensors, layers=LAYERS):
    """Captured recorder tensors -> per-layer drivers along the main path (prefix + last token) and each candidate
    branch, plus the kernel states exposed at the prefix end, after the last token, and at each branch end."""
    t = torch()
    branches = sorted(k for k in tensors if k.startswith('cand') and not k.endswith('_states'))
    out = {'layers': {}, 'branches': branches}
    for layer in layers:
        key = str(layer)
        pre, last = tensors['prefix'][key], tensors['last'][key]
        assert len(pre['q']) == 1 and int(pre['kind'][0]) == 0 and not bool(pre['has_initial'][0]), 'prefix must be one chunk call from zero state'
        assert len(last['q']) == 1 and int(last['kind'][0]) == 1 and bool(last['has_initial'][0])
        assert t.equal(last['initial_state'][0], tensors['prefix_states'][key]['recurrent'].to(last['initial_state'][0].dtype)), 'last-token initial state != prefix cache'
        main = {n: t.cat([pre[n][0], last[n][0]], 0) for n in ('q', 'k', 'v', 'g', 'beta', 'core_out', 'norm_out', 'out_proj')}
        row = {'main': main, 'branches': {}, 'exposed': {'prefix': tensors['prefix_states'][key]['recurrent'].double(),
                                                       'last': tensors['last_states'][key]['recurrent'].double()}}
        for b in branches:
            cap = tensors[b].get(key, {})
            n_calls = len(cap.get('q', []))
            if n_calls:
                assert all(int(x[0]) == 1 for x in cap['kind'])
                assert t.equal(cap['initial_state'][0], tensors['last_states'][key]['recurrent'].to(cap['initial_state'][0].dtype)), 'branch must start from own post-last state'
            row['branches'][b] = {n: concat_phase(cap.get(n, [])) for n in ('q', 'k', 'v', 'g', 'beta', 'core_out', 'norm_out', 'out_proj')}
            row['exposed'][b] = tensors[f'{b}_states'][key]['recurrent'].double()
        out['layers'][key] = row
    out['boundary'] = {ph: {n: concat_phase(v) for n, v in tensors[ph].get('boundary', {}).items()} for ph in ['prefix', 'last'] + branches}
    out['first_logits'] = tensors.get('first_logits')
    return out


def run_path(S, drv, collect_outputs=True):
    """Sequential float64 recurrence from S over every position of drv; returns final S and per-position outputs."""
    p = prepare(drv)
    outs = []
    for i in range(p['q'].shape[0]):
        S = apply_A(S, p['alpha'][i], p['beta'][i], p['k'][i]) + write_term(p['beta'][i], p['k'][i], p['v'][i])
        if collect_outputs:
            outs.append(readout(S, p['q'][i]))
    return S, outs


def rel(a, b):
    return float((a - b).norm() / b.norm().clamp_min(1e-300))


def reconstruction_gate(traj, tol=TOL):
    """§5.5: offline recurrence vs the kernel at every exposed state and every token readout. The absolute state
    errors are kept as the numerical floor of later differences."""
    t = torch()
    out = {'layers': {}, 'tolerance': dict(tol)}
    ok = True
    for key, row in traj['layers'].items():
        H, dk, dv = row['exposed']['prefix'].shape
        S0 = t.zeros(H, dk, dv, dtype=t.float64)
        n = row['main']['q'].shape[0]
        S_pre, outs_pre = run_path(S0, {k: v[:n - 1] for k, v in row['main'].items()})
        S_last, outs_last = run_path(S_pre, {k: v[n - 1:] for k, v in row['main'].items()})
        errs = {'prefix': rel(S_pre, row['exposed']['prefix']), 'last': rel(S_last, row['exposed']['last'])}
        abs_err = {'prefix': float((S_pre - row['exposed']['prefix']).norm()), 'last': float((S_last - row['exposed']['last']).norm())}
        outs = outs_pre + outs_last
        core = row['main']['core_out'].double()
        out_errs = [rel(o, core[i]) for i, o in enumerate(outs)]
        for b, drv in row['branches'].items():
            if drv['q'] is None:
                S_b, ob = S_last, []
            else:
                S_b, ob = run_path(S_last, drv)
                core_b = drv['core_out'].double()
                out_errs += [rel(o, core_b[i]) for i, o in enumerate(ob)]
            errs[b] = rel(S_b, row['exposed'][b])
            abs_err[b] = float((S_b - row['exposed'][b]).norm())
        layer_ok = max(errs.values()) <= tol['state_rel'] and max(out_errs) <= tol['out_rel']
        ok &= layer_ok
        out['layers'][key] = {'state_rel': errs, 'state_abs': abs_err, 'out_rel_max': max(out_errs),
                              'out_rel_median': sorted(out_errs)[len(out_errs) // 2], 'passed': layer_ok}
    out['status'] = 'passed' if ok else 'failed'
    return out


# ---------------------------------------------------------------- paired accounting (§5, §6)

def ip(a, b):
    return float((a * b).sum())


def nrm(a):
    return float(a.norm())


def per_head_ip(a, b):
    return (a * b).flatten(1).sum(1)


class Accounts:
    """All accumulated matrices of one paired path. Copied when the path branches into candidates."""

    def __init__(self, H, dk, dv):
        t = torch()
        z = lambda: t.zeros(H, dk, dv, dtype=t.float64)
        self.S = {'T': z(), 'C': z()}
        self.Z = {(a, kind, s): z() for a in ACCOUNTS for kind in ('W', 'R') for s in SEGMENTS}
        self.P = {(x, s): z() for x in ('T', 'C') for s in SEGMENTS}

    def copy(self):
        new = Accounts.__new__(Accounts)
        new.S = {k: v.clone() for k, v in self.S.items()}
        new.Z = {k: v.clone() for k, v in self.Z.items()}
        new.P = {k: v.clone() for k, v in self.P.items()}
        return new

    def total(self, a, kind):
        return sum(self.Z[(a, kind, s)] for s in SEGMENTS)


def step(acc, pT, pC, i, seg):
    """Advance one position; returns the per-step terms (before acc is overwritten)."""
    ST, SC = acc.S['T'], acc.S['C']
    dS_prev, Sbar = ST - SC, (ST + SC) / 2
    aT = lambda Z: apply_A(Z, pT['alpha'][i], pT['beta'][i], pT['k'][i])
    aC = lambda Z: apply_A(Z, pC['alpha'][i], pC['beta'][i], pC['k'][i])
    abar = lambda Z: (aT(Z) + aC(Z)) / 2
    BT, BC = write_term(pT['beta'][i], pT['k'][i], pT['v'][i]), write_term(pC['beta'][i], pC['k'][i], pC['v'][i])
    carry = abar(dS_prev)
    proc = aT(Sbar) - aC(Sbar)
    decay = (pT['alpha'][i] - pC['alpha'][i])[:, None, None] * Sbar
    write = BT - BC
    newT, newC = aT(ST) + BT, aC(SC) + BC
    dS = newT - newC
    proc_bg = {'sym': proc, 'bgT': aT(SC) - aC(SC), 'bgC': aT(ST) - aC(ST)}
    move = {'sym': abar, 'bgT': aT, 'bgC': aC}
    for a in ACCOUNTS:
        for s in SEGMENTS:
            acc.Z[(a, 'W', s)] = move[a](acc.Z[(a, 'W', s)]) + (write if s == seg else 0)
            acc.Z[(a, 'R', s)] = move[a](acc.Z[(a, 'R', s)]) + (proc_bg[a] if s == seg else 0)
    for x, ax, B in (('T', aT, BT), ('C', aC, BC)):
        for s in SEGMENTS:
            acc.P[(x, s)] = ax(acc.P[(x, s)]) + (B if s == seg else 0)
    acc.S = {'T': newT, 'C': newC}
    prev = dS_prev.flatten(1).norm(dim=1)
    ratio = carry.flatten(1).norm(dim=1) / prev.clamp_min(1e-300)
    return {'dS': dS, 'carry': carry, 'proc': proc, 'decay': decay, 'corr': proc - decay, 'write': write,
            'contraction_max': float(ratio[prev > 0].max()) if bool((prev > 0).any()) else 0.0}


def summarize_step(acc, terms, pT, pC, i, seg, actual):
    """Per-position scalars (aggregated over heads) and a few per-head arrays."""
    t = torch()
    dS = terms['dS']
    dS2 = ip(dS, dS)
    resid = dS - (terms['carry'] + terms['proc'] + terms['write'])
    row = {'segment': seg, 'dS': math.sqrt(dS2), 'dS2': dS2,
           'S_T': nrm(acc.S['T']), 'S_C': nrm(acc.S['C']),
           'identity_rel': nrm(resid) / max(math.sqrt(dS2), 1e-300) if dS2 > 0 else nrm(resid),
           'contraction_max': terms['contraction_max']}
    for n in ('carry', 'proc', 'decay', 'corr', 'write'):
        row[n] = nrm(terms[n])
        row[f'ip_{n}_dS'] = ip(terms[n], dS)
    row['ip_carry_proc'] = ip(terms['carry'], terms['proc'])
    row['ip_carry_write'] = ip(terms['carry'], terms['write'])
    row['ip_proc_write'] = ip(terms['proc'], terms['write'])
    for a in ACCOUNTS:
        ZW, ZR = acc.total(a, 'W'), acc.total(a, 'R')
        row[f'{a}_ZW'], row[f'{a}_ZR'] = nrm(ZW), nrm(ZR)
        row[f'{a}_ip_ZW_dS'], row[f'{a}_ip_ZR_dS'] = ip(ZW, dS), ip(ZR, dS)
        row[f'{a}_ZW_plus_ZR_rel_err'] = nrm(ZW + ZR - dS) / max(math.sqrt(dS2), 1e-300) if dS2 > 0 else nrm(ZW + ZR - dS)
        for kind in ('W', 'R'):
            row[f'{a}_ip_Z{kind}_seg_dS'] = {s: ip(acc.Z[(a, kind, s)], dS) for s in SEGMENTS}
    # Own-trajectory segment sources: P^{X,s} propagated with X's own A; sum over s is S^X.
    for x in ('T', 'C'):
        SX = acc.S[x]
        row[f'P{x}_seg_share'] = {s: ip(acc.P[(x, s)], SX) / max(ip(SX, SX), 1e-300) for s in SEGMENTS}
        row[f'P{x}_seg_norm'] = {s: nrm(acc.P[(x, s)]) for s in SEGMENTS}
    row['Pdiff_seg_norm'] = {s: nrm(acc.P[('T', s)] - acc.P[('C', s)]) for s in SEGMENTS}
    row['Pdiff_seg_ip_dS'] = {s: ip(acc.P[('T', s)] - acc.P[('C', s)], dS) for s in SEGMENTS}
    # Local readout (§6): Delta o = Delta S^T qbar + Sbar^T Delta q, with Delta S split by the symmetric W/R accounts.
    qT, qC = pT['q'][i], pC['q'][i]
    qbar, dq = (qT + qC) / 2, qT - qC
    Sbar = (acc.S['T'] + acc.S['C']) / 2
    oT, oC = readout(acc.S['T'], qT), readout(acc.S['C'], qC)
    do = oT - oC
    state_part, query_part = readout(dS, qbar), readout(Sbar, dq)
    row.update({'o_T': nrm(oT), 'o_C': nrm(oC), 'do': nrm(do), 'do2': ip(do, do),
                'ip_state_do': ip(state_part, do), 'ip_query_do': ip(query_part, do),
                'state_part': nrm(state_part), 'query_part': nrm(query_part),
                'readout_identity_rel': nrm(state_part + query_part - do) / max(nrm(do), 1e-300)})
    for a in ACCOUNTS:
        for kind in ('W', 'R'):
            row[f'{a}_ip_Z{kind}q_do'] = ip(readout(acc.total(a, kind), qbar), do)
    row['sym_ip_Zq_seg_do'] = {f'{kind}:{s}': ip(readout(acc.Z[('sym', kind, s)], qbar), do) for kind in ('W', 'R') for s in SEGMENTS}
    if actual is not None:
        aT, aC = actual
        for n in ('core_out', 'norm_out', 'out_proj'):
            dT, dC = aT[n][i].double(), aC[n][i].double()
            row[f'actual_{n}_diff'] = nrm(dT - dC)
            row[f'actual_{n}_C'] = nrm(dC)
        row['actual_vs_recon_do_rel'] = nrm((aT['core_out'][i].double() - aC['core_out'][i].double()) - do) / max(nrm(do), 1e-300)
    heads = {'dS': dS.flatten(1).norm(dim=1), 'write': terms['write'].flatten(1).norm(dim=1),
             'proc': terms['proc'].flatten(1).norm(dim=1), 'carry': terms['carry'].flatten(1).norm(dim=1),
             'ip_symZW_dS': per_head_ip(acc.total('sym', 'W'), dS), 'do': do.norm(dim=1), 'ip_state_do': per_head_ip(state_part, do)}
    return row, {k: v.float() for k, v in heads.items()}


def account_pair(trajT, trajC, labels, layer):
    """Main path (prefix + last) then each candidate branch from the post-last accounts."""
    t = torch()
    rT, rC = trajT['layers'][str(layer)], trajC['layers'][str(layer)]
    pT, pC = prepare(rT['main']), prepare(rC['main'])
    n = pT['q'].shape[0]
    assert len(labels) == n, (len(labels), n)
    H, dk, dv = rT['exposed']['prefix'].shape
    acc = Accounts(H, dk, dv)
    rows, heads = [], []
    for i in range(n):
        terms = step(acc, pT, pC, i, labels[i])
        r, h = summarize_step(acc, terms, pT, pC, i, labels[i], (rT['main'], rC['main']))
        r.update(path='main', position=i)
        rows.append(r)
        heads.append(h)
    post = acc
    for b in trajT['branches']:
        dT, dC = rT['branches'][b], rC['branches'][b]
        if dT['q'] is None:
            continue
        bT, bC = prepare(dT), prepare(dC)
        acc_b = post.copy()
        for i in range(bT['q'].shape[0]):
            terms = step(acc_b, bT, bC, i, 'cand')
            r, h = summarize_step(acc_b, terms, bT, bC, i, 'cand', (dT, dC))
            r.update(path=b, position=n + i)
            rows.append(r)
            heads.append(h)
    return rows, heads


def boundary_summary(trajT, trajC):
    out = {}
    for ph, vecs in trajT['boundary'].items():
        out[ph] = {}
        for name, vT in vecs.items():
            vC = trajC['boundary'][ph][name]
            if vT is None:
                continue
            d = (vT.double() - vC.double()).norm(dim=-1)
            out[ph][name] = {'last_position_diff': float(d[-1]), 'last_position_C_norm': float(vC[-1].double().norm()),
                             'diff_per_position': [float(x) for x in d]}
    return out


# ---------------------------------------------------------------- §7 branch rules

def pooled(cells):
    """cells: summaries at t_L (last prompt token) for one (anchor, base): both facts x three layers."""
    dS2 = sum(c['dS2'] for c in cells)
    do2 = sum(c['do2'] for c in cells)
    out = {'dS2': dS2, 'do2': do2}
    for a in ACCOUNTS:
        out[f'{a}_W'] = sum(c[f'{a}_ip_ZW_dS'] for c in cells) / dS2
        out[f'{a}_R'] = sum(c[f'{a}_ip_ZR_dS'] for c in cells) / dS2
        out[f'{a}_W_early'] = sum(c[f'{a}_ip_ZW_seg_dS'][s] for c in cells for s in EARLY) / dS2
        out[f'{a}_R_late'] = sum(c[f'{a}_ip_ZR_seg_dS'][s] for c in cells for s in LATE_PLUS) / dS2
        out[f'{a}_R_early'] = sum(c[f'{a}_ip_ZR_seg_dS'][s] for c in cells for s in EARLY) / dS2
        out[f'{a}_W_late'] = sum(c[f'{a}_ip_ZW_seg_dS'][s] for c in cells for s in LATE_PLUS) / dS2
    out['rho_state'] = sum(c['ip_state_do'] for c in cells) / do2 if do2 > 0 else float('nan')
    out['rho_query'] = sum(c['ip_query_do'] for c in cells) / do2 if do2 > 0 else float('nan')
    out['cancel'] = sum(c['sym_ZW'] + c['sym_ZR'] for c in cells) / sum(c['dS'] for c in cells)
    return out


def classify(cells, floors, rules):
    """One (anchor, base). floors: matching numerical floor (abs state error, T + C) per cell."""
    if any(c['dS'] <= TOL['resolve_factor'] * f for c, f in zip(cells, floors)):
        return {'branch': 'unresolved', 'flags': []}
    p = pooled(cells)
    flags = []
    if not p['rho_state'] >= rules['rho_min']:
        flags.append('readout_disconnect')
    order = {a: p[f'{a}_W'] > p[f'{a}_R'] for a in ACCOUNTS}
    if p['cancel'] >= rules['cancel_min'] or len(set(order.values())) > 1:
        flags.append('coupled')
    if not flags:
        if min(p[f'{a}_W_early'] for a in ACCOUNTS) >= rules['w_early_min'] and max(p[f'{a}_R'] for a in ACCOUNTS) <= rules['r_max']:
            flags.append('early_write')
        if min(p[f'{a}_R_late'] for a in ACCOUNTS) >= rules['r_late_min']:
            flags.append('late_processing')
    return {'branch': '+'.join(flags) if flags else 'unclassified', 'flags': flags, 'pooled': p}


def anchor_verdict(by_base):
    """§7: a branch is supported for an anchor when at least SUPPORT_MIN of six bases carry it; none -> unstable."""
    counts = {b: sum(b in v['flags'] for v in by_base.values()) for b in BRANCHES}
    counts['unresolved'] = sum(v['branch'] == 'unresolved' for v in by_base.values())
    counts['unclassified'] = sum(v['branch'] == 'unclassified' for v in by_base.values())
    supported = [b for b in BRANCHES if counts[b] >= SUPPORT_MIN]
    return {'counts': counts, 'supported': supported, 'verdict': '+'.join(supported) if supported else 'unstable_or_insufficient'}


# ---------------------------------------------------------------- endpoints (old readouts)

def endpoints(records):
    """Per base: first-step stop advantage D (facts weighted equally), S_fact = [ll(A)-ll(B)]|fact A - [...]|fact B."""
    by = {}
    for r in records:
        it = r['item']
        by.setdefault((r['spec']['condition_id'], it['base_id']), {})[it['target_index']] = r
    out = {}
    for (cid, base), facts in sorted(by.items()):
        assert set(facts) == {0, 1}
        ll = {t: [c['loglikelihood'] for c in facts[t]['candidates']] for t in (0, 1)}
        out.setdefault(cid, {})[base] = {
            'D': (facts[0]['first_step']['stop_advantage'] + facts[1]['first_step']['stop_advantage']) / 2,
            'S_fact': (ll[0][0] - ll[0][1]) - (ll[1][0] - ll[1][1]),
            'first_step_eos': [facts[t]['first_step_eos'] for t in (0, 1)]}
    return out


# ---------------------------------------------------------------- run over a verified formal run

def load_records(runs):
    import experiment as ex
    recs = []
    for run in runs:
        run = Path(run)
        v = ex.read(run / 'verification.json')
        assert v['status'] == 'passed' and v['stage'] == 'formal'
        for w in sorted(run.glob('worker-*')):
            for p in sorted((w / 'records').glob('*.json')):
                rec = ex.read(p)
                rec['_dir'] = str(w)
                recs.append(rec)
    return recs


def analyze(runs, out):
    t = torch()
    import experiment as ex
    out = Path(out)
    recs = load_records(runs)
    index = {(r['item']['id'], r['spec']['condition_id']): r for r in recs}
    assert len(index) == 36
    items = sorted({r['item']['id'] for r in recs})
    traj, gates = {}, {}
    for (iid, cid), r in sorted(index.items()):
        p = Path(r['_dir']) / r['tensor_file']
        assert ex.sha(p) == r['tensor_sha256'], p
        cap = t.load(p, map_location='cpu', weights_only=False)
        traj[(iid, cid)] = from_capture(cap)
        gates[f'{iid}__{cid}'] = reconstruction_gate(traj[(iid, cid)])
    failed = [k for k, g in gates.items() if g['status'] != 'passed']
    result = {'schema': 1, 'status': 'stopped_engineering' if failed else 'analyzed', 'tolerances': TOL, 'rules': RULES,
              'reconstruction': gates, 'reconstruction_failed': failed}
    if failed:
        ex.write(out / 'accounts-r01.json', result, immutable=True)
        return result
    token_rows, head_rows, tl_cells, floors = [], {}, {}, {}
    checks = {'identity_rel_max': 0.0, 'readout_identity_rel_max': 0.0, 'contraction_max': 0.0, 'zsum_rel_max': 0.0}
    for anchor in ('N_L00_C4146_D-1', 'N_L12_C3621_D-1'):
        for iid in items:
            rec = index[(iid, anchor)]
            labels = rec['segments']['labels']
            for layer in LAYERS:
                rows, heads = account_pair(traj[(iid, anchor)], traj[(iid, 'clean')], labels, layer)
                ge = gates[f'{iid}__{anchor}']['layers'][str(layer)]['state_abs']
                gc = gates[f'{iid}__clean']['layers'][str(layer)]['state_abs']
                for r in rows:
                    if r['dS2'] > 0:
                        checks['identity_rel_max'] = max(checks['identity_rel_max'], r['identity_rel'])
                        checks['zsum_rel_max'] = max(checks['zsum_rel_max'], *(r[f'{a}_ZW_plus_ZR_rel_err'] for a in ACCOUNTS))
                    if r['do'] > 0:
                        checks['readout_identity_rel_max'] = max(checks['readout_identity_rel_max'], r['readout_identity_rel'])
                    checks['contraction_max'] = max(checks['contraction_max'], r['contraction_max'])
                    token_rows.append({'anchor': anchor, 'item_id': iid, 'base_id': rec['item']['base_id'], 'layer': layer, **r})
                head_rows[f'{anchor}__{iid}__{layer}'] = {k: t.stack([h[k] for h in heads]) for k in heads[0]}
                tL = next(r for r in rows if r['path'] == 'main' and r['segment'] == 'last')
                tl_cells.setdefault(anchor, {}).setdefault(rec['item']['base_id'], []).append(tL)
                floors.setdefault(anchor, {}).setdefault(rec['item']['base_id'], []).append(ge['last'] + gc['last'])
    # §5.5 / derivation-tier checks: exact identities and the contraction bound must hold up to rounding.
    checks['passed'] = (checks['identity_rel_max'] <= TOL['identity_rel'] and checks['zsum_rel_max'] <= TOL['identity_rel']
                        and checks['readout_identity_rel_max'] <= TOL['identity_rel'] and checks['contraction_max'] <= 1 + TOL['contraction_slack'])
    result['identity_checks'] = checks
    if not checks['passed']:
        result['status'] = 'stopped_engineering'
        ex.write(out / 'accounts-r01.json', result, immutable=True)
        return result
    verdicts = {}
    for setting, rules in RULES.items():
        verdicts[setting] = {}
        for anchor, bases in tl_cells.items():
            by_base = {b: classify(cells, floors[anchor][b], rules) for b, cells in sorted(bases.items())}
            verdicts[setting][anchor] = {'by_base': by_base, **anchor_verdict(by_base)}
    result['verdicts'] = verdicts
    result['threshold_sensitive'] = {a: len({verdicts[s][a]['verdict'] for s in RULES}) > 1 for a in tl_cells}
    result['endpoints'] = endpoints(recs)
    result['boundary'] = {f'{iid}__{a}': boundary_summary(traj[(iid, a)], traj[(iid, 'clean')]) for a in ('N_L00_C4146_D-1', 'N_L12_C3621_D-1') for iid in items}
    result['segment_summary'] = segment_summary(token_rows)
    ex.write(out / 'accounts-r01.json', result, immutable=True)
    write_jsonl_zst(out / 'tokens-r01.jsonl.zst', token_rows)
    out.mkdir(parents=True, exist_ok=True)
    t.save(head_rows, out / 'heads-r01.pt')
    return {k: v for k, v in result.items() if k in ('status', 'identity_checks', 'threshold_sensitive')} | {
        'verdicts_main': {a: v['verdict'] for a, v in verdicts['main'].items()}}


def segment_summary(token_rows):
    """§5.3: per (anchor, base, layer, segment) new difference created inside the segment (sum of |write|, |proc|),
    and the shares of Delta S at the segment's final position. Main path only."""
    out = {}
    for r in token_rows:
        if r['path'] != 'main':
            continue
        key = f'{r["anchor"]}__{r["item_id"]}__{r["layer"]}'
        seg = out.setdefault(key, {}).setdefault(r['segment'], {'tokens': 0, 'write_sum': 0.0, 'proc_sum': 0.0, 'carry_sum': 0.0})
        seg['tokens'] += 1
        seg['write_sum'] += r['write']
        seg['proc_sum'] += r['proc']
        seg['carry_sum'] += r['carry']
        if r['dS2'] > 0:
            seg['end'] = {'position': r['position'], 'dS': r['dS'],
                          'sym_W': r['sym_ip_ZW_dS'] / r['dS2'], 'sym_R': r['sym_ip_ZR_dS'] / r['dS2'],
                          'rho_state': r['ip_state_do'] / r['do2'] if r['do2'] > 0 else None}
    return out


def write_jsonl_zst(path, rows):
    import subprocess
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    data = ''.join(json.dumps(r, ensure_ascii=False, allow_nan=False) + '\n' for r in rows).encode()
    with open(path, 'xb') as f:
        f.write(subprocess.run(['zstd', '-q', '-19', '-c'], input=data, stdout=subprocess.PIPE, check=True).stdout)


# ---------------------------------------------------------------- selftest (§6.2 offline rehearsal)

def synthetic(world, seed=0, n=24, H=4, d=8, fact=(2, 10), branch=3):
    """Synthetic C/T driver pairs in captured format. The kernel 'exposed' states are exact recurrences (plus an
    optional perturbation) so both the gates and the branch rules can be exercised in either direction."""
    t = torch()
    g = t.Generator().manual_seed(seed)
    rnd = lambda *s: t.randn(*s, generator=g, dtype=t.float64)
    labels = ['head'] * fact[0] + ['fact'] * (fact[1] - fact[0]) + ['question'] * 6 + ['instruction'] * 3 + ['tail'] * (n - fact[1] - 10) + ['last']
    assert len(labels) == n

    def drivers(m):
        return {'q': rnd(m, H, d), 'k': rnd(m, H, d), 'v': rnd(m, H, d), 'g': -t.rand(m, H, generator=g, dtype=t.float64) * 0.3,
                'beta': t.rand(m, H, generator=g, dtype=t.float64) * 0.8 + 0.1}
    C = drivers(n)
    Cb = drivers(branch)
    T = {k: v.clone() for k, v in C.items()}
    Tb = {k: v.clone() for k, v in Cb.items()}
    in_fact = t.tensor([lab == 'fact' for lab in labels])
    late = t.tensor([lab in LATE_PLUS for lab in labels])
    if world == 'early_write':          # value changes in the fact segment only: Delta A = 0, Delta B != 0 there
        T['v'][in_fact] += 1.5 * rnd(int(in_fact.sum()), H, d)
    elif world == 'late_processing':    # history processing changes after the fact only, small value change early
        T['v'][in_fact] += 0.2 * rnd(int(in_fact.sum()), H, d)
        T['g'][late] -= 0.6
    elif world == 'coupled':            # re-writing an association the state already holds, with a different beta:
        rep = slice(fact[0] + 1, fact[1])  # Delta B and Delta A Sbar ~ -Delta B cancel step by step (delta-rule redundancy)
        for X in (C, T):
            X['k'][rep], X['v'][rep], X['g'][rep] = X['k'][fact[0]], X['v'][fact[0]], 0.0
        C['beta'][rep], T['beta'][rep] = 0.3, 0.95
    elif world == 'readout_disconnect':  # tiny state difference, large query change at the read positions
        T['v'][in_fact] += 0.01 * rnd(int(in_fact.sum()), H, d)
        T['q'][-1] += 5.0 * rnd(H, d)
    elif world == 'null':
        pass
    else:
        raise ValueError(world)

    def traj(drv, drv_b, perturb=0.0):
        S0 = t.zeros(H, d, d, dtype=t.float64)
        S_pre, o1 = run_path(S0, {k: v[:n - 1] for k, v in drv.items()})
        S_last, o2 = run_path(S_pre, {k: v[n - 1:] for k, v in drv.items()})
        S_b, o3 = run_path(S_last, drv_b)
        main = dict(drv, core_out=t.stack(o1 + o2), norm_out=t.stack(o1 + o2), out_proj=t.stack(o1 + o2).flatten(1))
        br = dict(drv_b, core_out=t.stack(o3), norm_out=t.stack(o3), out_proj=t.stack(o3).flatten(1))
        return {'layers': {'0': {'main': main, 'branches': {'cand0': br},
                                 'exposed': {'prefix': S_pre * (1 + perturb), 'last': S_last, 'cand0': S_b}}},
                'branches': ['cand0'], 'boundary': {}}
    return traj(T, Tb), traj(C, Cb), labels


def selftest():
    import copy
    t = torch()
    report = {'cases': {}}

    def classify_world(world, seed):
        tT, tC, labels = synthetic(world, seed)
        rows, _ = account_pair(tT, tC, labels, 0)
        tL = next(r for r in rows if r['path'] == 'main' and r['segment'] == 'last')
        floor = sum(reconstruction_gate(x)['layers']['0']['state_abs']['last'] for x in (tT, tC))
        return classify([tL], [floor], RULES['main']), rows
    expect = {'early_write': 'early_write', 'late_processing': 'late_processing', 'coupled': 'coupled',
              'readout_disconnect': 'readout_disconnect', 'null': 'unresolved'}
    for world, want in expect.items():
        got = []
        for seed in range(5):
            res, rows = classify_world(world, seed)
            got.append(res['branch'])
            for r in rows:
                if r['dS2'] > 0:
                    assert r['identity_rel'] < 1e-10 and r['readout_identity_rel'] < 1e-10, (world, r['identity_rel'])
                    for a in ACCOUNTS:
                        assert r[f'{a}_ZW_plus_ZR_rel_err'] < 1e-10
                assert r['contraction_max'] <= 1 + 1e-12
        hits = sum(want in g.split('+') for g in got)
        report['cases'][world] = {'expected': want, 'got': got, 'hits': hits}
        assert hits >= 4, (world, got)
    # Each world classifies into its own branch and not into the others' exclusive ones.
    assert all(not any(o in g.split('+') for g in report['cases']['early_write']['got']) for o in ('coupled', 'readout_disconnect'))
    # Reconstruction gate passes on exact kernel states and fails on a 1e-2 relative perturbation of one state.
    tT, tC, _ = synthetic('early_write', 0)
    assert reconstruction_gate(tT)['status'] == 'passed'
    bad, _, _ = synthetic('early_write', 0)
    bad['layers']['0']['exposed']['prefix'] = bad['layers']['0']['exposed']['prefix'] * (1 + 1e-2)
    assert reconstruction_gate(bad)['status'] == 'failed'
    bad2 = copy.deepcopy(tT)
    bad2['layers']['0']['main']['core_out'] = bad2['layers']['0']['main']['core_out'] * 1.05
    assert reconstruction_gate(bad2)['status'] == 'failed'
    report['reconstruction_gate'] = 'passes exact, fails 1e-2 state and 5% output perturbation'
    # Anchor-level rule: 4/6 supports, 3/6 does not.
    mk = lambda flags: {'branch': '+'.join(flags) or 'unclassified', 'flags': flags}
    v = anchor_verdict({f'b{i}': mk(['early_write'] if i < 4 else []) for i in range(6)})
    assert v['verdict'] == 'early_write'
    v = anchor_verdict({f'b{i}': mk(['early_write'] if i < 3 else ['late_processing'] if i < 5 else []) for i in range(6)})
    assert v['verdict'] == 'unstable_or_insufficient'
    report['anchor_rule'] = '4/6 supported, 3/6 + 2/6 unstable'
    # Contraction check: a non-contractive A (alpha > 1) is detected.
    tT, tC, labels = synthetic('early_write', 1)
    for tr in (tT, tC):
        tr['layers']['0']['main']['g'] = tr['layers']['0']['main']['g'].abs() + 0.2
    rows, _ = account_pair(tT, tC, labels, 0)
    assert max(r['contraction_max'] for r in rows) > 1 + 1e-6
    report['contraction_check'] = 'detects alpha > 1'
    report['status'] = 'passed'
    return report


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    q = sub.add_parser('run')
    q.add_argument('runs', nargs='+')
    q.add_argument('--out', required=True)
    sub.add_parser('selftest')
    a = p.parse_args()
    sys.path.insert(0, str(HERE.parent / 'early-input-control-v1-2026-10-29'))
    value = analyze(a.runs, a.out) if a.cmd == 'run' else selftest()
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    main()
