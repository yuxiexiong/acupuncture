"""CFM-S2 offline process analysis (CONTRACT.zh-CN.md §4-§8). CPU, float64; never loads a model.

Same update and orientation as CFM-S1 (S_t = A_t S_{t-1} + B_t, A = alpha (I - beta k k^T), B = beta k v^T).
For a pair X (needle side) / Y (reference side) that share positions 0..b:
    H_b = S_b, N_b = 0,  H_t = A_t H_{t-1},  N_t = A_t N_{t-1} + B_t           (per arm; S = H + N)
    u_B = Delta B_t,  u_H = Delta A_t Hbar_{t-1},  u_N = Delta A_t Nbar_{t-1}
    Delta H_t = Abar Delta H_{t-1} + u_H,   Delta N_t = Abar Delta N_{t-1} + u_N + u_B
Everything is offline bookkeeping on the recorded drivers; nothing is fed back into a model.

python formation.py run RUN_DIR --out ANALYSIS_DIR
python formation.py selftest
"""
import argparse
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
S1_DIR = HERE.parent / 'cache-formation-mechanism-s1-native-trace-v1-2026-10-31'
sys.path.insert(0, str(S1_DIR))
import account as A1  # noqa: E402

LAYERS = A1.LAYERS
ANCHORS = ('N_L00_C4146_D-1', 'N_L12_C3621_D-1')
# Contract §5: a-priori numerical bound (float32 unit roundoff, safety factor) and the resolvability multiple.
U32 = 2.0 ** -24
C_ROUND = 16.0
RESOLVE = 10.0
# Contract §6: pairs. same-start pairs share positions 0..b; 10/00 does not.
PAIRS = {'01v00': ('01', '00', True), '11v10': ('11', '10', True), '10v00': ('10', '00', False)}
BACKGROUNDS = ('sym', 'bgX', 'bgY')
# Contract §7 secondary predictions (registered in plan v2, unchanged).
PRED = {'r10_max': 0.5, 'a01_min': 0.5, 'e01_max': 0.5}


def torch():
    import torch as t
    return t


def fro(x):
    return float(x.norm())


def ip(a, b):
    return float((a * b).sum())


def op_matrix(alpha, beta, k):
    """A per head as a (H, dk, dk) matrix."""
    t = torch()
    eye = t.eye(k.shape[-1], dtype=k.dtype).expand(k.shape[0], -1, -1)
    return alpha[:, None, None] * (eye - beta[:, None, None] * k[:, :, None] * k[:, None, :])


def max_head_fro(M):
    return float(M.flatten(1).norm(dim=1).max())


def max_head_norm(q):
    return float(q.norm(dim=-1).max())


# ---------------------------------------------------------------- per-arm states and the a-priori bound

def arm_path(traj, layer):
    """Prepared drivers along main path (prefix + last) and each candidate branch, with exposed kernel states."""
    row = traj['layers'][str(layer)]
    main = A1.prepare(row['main'])
    branches = {b: A1.prepare(d) for b, d in row['branches'].items() if d['q'] is not None}
    return main, branches, row['exposed']


def bound_validity(traj, layer):
    """Contract §5.2: the a-priori bound must cover the measured reconstruction error at every exposed state."""
    t = torch()
    main, branches, exposed = arm_path(traj, layer)
    H, dk, dv = exposed['prefix'].shape
    S, acc = t.zeros(H, dk, dv, dtype=t.float64), 0.0
    n = main['q'].shape[0]
    rows = {}
    for i in range(n):
        B = A1.write_term(main['beta'][i], main['k'][i], main['v'][i])
        S = A1.apply_A(S, main['alpha'][i], main['beta'][i], main['k'][i]) + B
        acc += C_ROUND * U32 * (fro(S) + fro(B))
        if i == n - 2:
            rows['prefix'] = (fro(S - exposed['prefix']), acc)
    rows['last'] = (fro(S - exposed['last']), acc)
    for b, d in branches.items():
        Sb, accb = S.clone(), acc
        for i in range(d['q'].shape[0]):
            B = A1.write_term(d['beta'][i], d['k'][i], d['v'][i])
            Sb = A1.apply_A(Sb, d['alpha'][i], d['beta'][i], d['k'][i]) + B
            accb += C_ROUND * U32 * (fro(Sb) + fro(B))
        rows[b] = (fro(Sb - exposed[b]), accb)
    ok = all(measured <= bound for measured, bound in rows.values())
    return {'points': {k: {'measured_abs': m, 'a_priori_bound': bd} for k, (m, bd) in rows.items()}, 'valid': ok}


# ---------------------------------------------------------------- paired process (plan §4-§5)

class PairState:
    def __init__(self, H, dk, dv):
        t = torch()
        z = lambda: t.zeros(H, dk, dv, dtype=t.float64)
        self.S = {'X': z(), 'Y': z()}
        self.H = {'X': z(), 'Y': z()}
        self.N = {'X': z(), 'Y': z()}
        self.err = {'X': 0.0, 'Y': 0.0}      # a-priori state bound e_S
        self.errH = {'X': 0.0, 'Y': 0.0}     # e_S at b (H inherits it and only contracts)
        self.started = False
        self.dwr = {}                         # (c, background) -> {'D','W','R','eW','eR','eD'}

    def copy(self):
        new = PairState.__new__(PairState)
        new.S = {k: v.clone() for k, v in self.S.items()}
        new.H = {k: v.clone() for k, v in self.H.items()}
        new.N = {k: v.clone() for k, v in self.N.items()}
        new.err, new.errH, new.started = dict(self.err), dict(self.errH), self.started
        new.dwr = {k: {n: (v.clone() if hasattr(v, 'clone') else v) for n, v in d.items()} for k, d in self.dwr.items()}
        return new


def start_dwr(st, c):
    dS = st.S['X'] - st.S['Y']
    e = st.err['X'] + st.err['Y']
    for bg in BACKGROUNDS:
        st.dwr[(c, bg)] = {'D': dS.clone(), 'W': dS * 0, 'R': dS * 0, 'eD': e, 'eW': 0.0, 'eR': 0.0}


def advance(st, pX, pY, i, label, position, path):
    """One position. Returns the per-step row (all scalars aggregated over heads)."""
    t = torch()
    aX = lambda Z: A1.apply_A(Z, pX['alpha'][i], pX['beta'][i], pX['k'][i])
    aY = lambda Z: A1.apply_A(Z, pY['alpha'][i], pY['beta'][i], pY['k'][i])
    abar = lambda Z: (aX(Z) + aY(Z)) / 2
    BX, BY = A1.write_term(pX['beta'][i], pX['k'][i], pX['v'][i]), A1.write_term(pY['beta'][i], pY['k'][i], pY['v'][i])
    AX, AY = op_matrix(pX['alpha'][i], pX['beta'][i], pX['k'][i]), op_matrix(pY['alpha'][i], pY['beta'][i], pY['k'][i])
    dA = AX - AY
    dA_head = max_head_fro(dA)
    Sbar_prev = (st.S['X'] + st.S['Y']) / 2
    eS_prev = (st.err['X'] + st.err['Y']) / 2
    row = {'path': path, 'position': position, 'segment': label}
    u_B = BX - BY
    row['u_B'], row['e_u_B'] = fro(u_B), C_ROUND * U32 * (fro(BX) + fro(BY))
    row['dA_op'] = fro(dA)
    row['e_dA_op'] = C_ROUND * U32 * (fro(AX) + fro(AY))
    proc = aX(Sbar_prev) - aY(Sbar_prev)
    row['dA_Sbar'] = fro(proc)
    row['e_dA_Sbar'] = dA_head * eS_prev + C_ROUND * U32 * dA_head * fro(Sbar_prev)
    row['carry_dS_prev'] = fro(abar(st.S['X'] - st.S['Y']))
    if st.started:
        Hbar, Nbar = (st.H['X'] + st.H['Y']) / 2, (st.N['X'] + st.N['Y']) / 2
        eH = (st.errH['X'] + st.errH['Y']) / 2
        eN = (st.err['X'] + st.errH['X'] + st.err['Y'] + st.errH['Y']) / 2
        dH_prev = st.H['X'] - st.H['Y']
        dN_prev = st.N['X'] - st.N['Y']
        u_H, u_N = aX(Hbar) - aY(Hbar), aX(Nbar) - aY(Nbar)
        row['u_H'], row['e_u_H'] = fro(u_H), dA_head * eH + C_ROUND * U32 * dA_head * fro(Hbar)
        row['u_N'], row['e_u_N'] = fro(u_N), dA_head * eN + C_ROUND * U32 * dA_head * fro(Nbar)
        row['ip_uB_uH'], row['ip_uB_uN'], row['ip_uH_uN'] = ip(u_B, u_H), ip(u_B, u_N), ip(u_H, u_N)
        row['uH_plus_uN_vs_dA_Sbar_rel'] = fro(u_H + u_N - proc) / max(fro(proc), 1e-300)
        st.H = {'X': aX(st.H['X']), 'Y': aY(st.H['Y'])}
        st.N = {'X': aX(st.N['X']) + BX, 'Y': aY(st.N['Y']) + BY}
        dH, dN = st.H['X'] - st.H['Y'], st.N['X'] - st.N['Y']
        row['dH_identity_rel'] = fro(dH - (abar(dH_prev) + u_H)) / max(fro(dH), 1e-300)
        row['dN_identity_rel'] = fro(dN - (abar(dN_prev) + u_N + u_B)) / max(fro(dN), 1e-300)
    newX, newY = aX(st.S['X']) + BX, aY(st.S['Y']) + BY
    for bg_name, move, procbg in (('sym', abar, proc), ('bgX', aX, aX(st.S['Y']) - aY(st.S['Y'])), ('bgY', aY, aX(st.S['X']) - aY(st.S['X']))):
        for c in ('b', 'tau'):
            d = st.dwr.get((c, bg_name))
            if d is None:
                continue
            d['D'], d['W'], d['R'] = move(d['D']), move(d['W']) + u_B, move(d['R']) + procbg
            d['eW'] += row['e_u_B']
            d['eR'] += row['e_dA_Sbar']
    for x, S_new, B in (('X', newX, BX), ('Y', newY, BY)):
        st.err[x] += C_ROUND * U32 * (fro(S_new) + fro(B))
    st.S = {'X': newX, 'Y': newY}
    dS = newX - newY
    row['dS'], row['e_dS'] = fro(dS), st.err['X'] + st.err['Y']
    row['S_X'], row['S_Y'] = fro(newX), fro(newY)
    if st.started:
        dH, dN = st.H['X'] - st.H['Y'], st.N['X'] - st.N['Y']
        row['dH'], row['e_dH'] = fro(dH), st.errH['X'] + st.errH['Y']
        row['dN'], row['e_dN'] = fro(dN), st.err['X'] + st.errH['X'] + st.err['Y'] + st.errH['Y']
        row['ip_dH_dS'], row['ip_dN_dS'] = ip(dH, dS), ip(dN, dS)
        row['HN_sum_rel'] = fro(dH + dN - dS) / max(fro(dS), 1e-300)
    for (c, bg_name), d in st.dwr.items():
        tot = d['D'] + d['W'] + d['R']
        row[f'{c}_{bg_name}'] = {'D': fro(d['D']), 'W': fro(d['W']), 'R': fro(d['R']), 'eD': d['eD'], 'eW': d['eW'], 'eR': d['eR'],
                                 'ip_D_dS': ip(d['D'], dS), 'ip_W_dS': ip(d['W'], dS), 'ip_R_dS': ip(d['R'], dS),
                                 'sum_rel': fro(tot - dS) / max(fro(dS), 1e-300)}
    # Local readout: Delta o = Delta S^T qbar + Sbar^T Delta q, state part split H / N.
    qX, qY = pX['q'][i], pY['q'][i]
    qbar, dq = (qX + qY) / 2, qX - qY
    Sbar = (newX + newY) / 2
    do = A1.readout(newX, qX) - A1.readout(newY, qY)
    do2 = ip(do, do)
    state_part, query_part = A1.readout(dS, qbar), A1.readout(Sbar, dq)
    qn = max(max_head_norm(qX), max_head_norm(qY))
    row.update({'do': math.sqrt(do2), 'do2': do2, 'e_do': (st.err['X'] + st.err['Y']) * qn,
                'ip_state_do': ip(state_part, do), 'ip_query_do': ip(query_part, do),
                'readout_identity_rel': fro(state_part + query_part - do) / max(math.sqrt(do2), 1e-300)})
    if st.started:
        row['ip_dHq_do'] = ip(A1.readout(st.H['X'] - st.H['Y'], qbar), do)
        row['ip_dNq_do'] = ip(A1.readout(st.N['X'] - st.N['Y'], qbar), do)
        row['e_dHq'] = row['e_dH'] * qn
        row['e_dNq'] = row['e_dN'] * qn
        row['ip_uBq_do'] = ip(A1.readout(u_B, qbar), do)
        row['ip_uHq_do'] = ip(A1.readout(u_H, qbar), do)
        row['ip_uNq_do'] = ip(A1.readout(u_N, qbar), do)
    return row


def pair_process(trajX, trajY, labels, layer, b):
    """Full window: positions 0..n-1 on the main path (H/N start after position b, D/W/R from b and from tau),
    then each candidate branch from the post-last state. Returns (rows, start_info)."""
    t = torch()
    pX, bX, eX = arm_path(trajX, layer)
    pY, bY, eY = arm_path(trajY, layer)
    n = pX['q'].shape[0]
    assert len(labels) == n and pY['q'].shape[0] == n
    H, dk, dv = eX['prefix'].shape
    st = PairState(H, dk, dv)
    rows, start = [], None
    for i in range(n):
        r = advance(st, pX, pY, i, labels[i], i, 'main')
        if i > b:
            rows.append(r)
        if i == b:
            dS_b = st.S['X'] - st.S['Y']
            start = {'dS_b': fro(dS_b), 'S_b_X': fro(st.S['X']), 'S_b_Y': fro(st.S['Y']), 'e_S_b': st.err['X'] + st.err['Y']}
            st.H = {'X': st.S['X'].clone(), 'Y': st.S['Y'].clone()}
            st.N = {'X': st.S['X'] * 0, 'Y': st.S['Y'] * 0}
            st.errH = dict(st.err)
            st.started = True
            start_dwr(st, 'b')
        if i == n - 2:
            start_dwr(st, 'tau')
    post = st
    for name in sorted(bX):
        dX, dY = bX[name], bY[name]
        assert dX['q'].shape == dY['q'].shape
        sb = post.copy()
        for i in range(dX['q'].shape[0]):
            rows.append(advance(sb, dX, dY, i, 'cand', n + i, name))
    return rows, start


# ---------------------------------------------------------------- judgments (plan §6, contract §6)

def resolved(row, name, ename=None):
    v, e = row.get(name), row.get(ename or f'e_{name}')
    return v is not None and v > RESOLVE * e


def cell_summary(rows, start, same_start):
    """Per (pair, item, layer): first step b+1, window-level resolvability, and the §6 refutations."""
    main = [r for r in rows if r['path'] == 'main']
    first = main[0]
    quantities = ['u_B', 'dA_op', 'dA_Sbar', 'dS', 'do', 'u_H', 'u_N', 'dH', 'dN']
    window = {}
    for q in quantities:
        hits = [r['position'] for r in rows if resolved(r, q)]
        ratios = [r[q] / r[f'e_{q}'] for r in rows if r.get(f'e_{q}', 0) > 0 and r.get(q) is not None]
        window[q] = {'resolved_positions': len(hits), 'first_resolved': min(hits) if hits else None, 'max_ratio': max(ratios) if ratios else None,
                     'positions': len(rows)}
    tl = next(r for r in main if r['segment'] == 'last')
    tau = main[-2] if len(main) >= 2 else main[-1]
    out = {'same_start': same_start, 'start': start, 'window': window,
           'first_step': {k: first.get(k) for k in ('position', 'segment', 'u_B', 'e_u_B', 'u_H', 'e_u_H', 'dA_op', 'e_dA_op', 'carry_dS_prev', 'dS', 'e_dS', 'ip_uB_uH')},
           'at_tau': {k: tau.get(k) for k in ('position', 'dS', 'e_dS', 'dH', 'e_dH', 'dN', 'e_dN')},
           'at_tL': {k: tl.get(k) for k in ('position', 'dS', 'e_dS', 'dH', 'e_dH', 'dN', 'e_dN', 'do', 'e_do', 'ip_state_do', 'ip_query_do', 'ip_dHq_do', 'ip_dNq_do', 'do2')}}
    f = first
    out['first_step']['uH_resolved'] = resolved(f, 'u_H')
    out['first_step']['uB_resolved'] = resolved(f, 'u_B')
    out['first_step']['dA_op_resolved'] = resolved(f, 'dA_op')
    out['first_step']['operator_changed_action_unresolved'] = resolved(f, 'dA_op') and not resolved(f, 'u_H')
    out['first_step']['start_resolved'] = start['dS_b'] > RESOLVE * start['e_S_b']
    any_B = window['u_B']['resolved_positions'] > 0
    any_H = window['dH']['resolved_positions'] > 0 or window['u_H']['resolved_positions'] > 0
    any_uN = window['u_N']['resolved_positions'] > 0
    any_A = window['dA_op']['resolved_positions'] > 0
    any_action = window['dA_Sbar']['resolved_positions'] > 0
    ref = {}
    if same_start:
        ref['E1_first_step_only_write'] = 'refuted' if out['first_step']['uH_resolved'] else 'not_refuted'
        ref['E2_common_old_source_same_processing'] = 'refuted' if window['dH']['resolved_positions'] > 0 else 'not_refuted'
        out['category'] = {(True, True): 'write_and_old_source_processing', (False, True): 'old_source_processing_only_resolved',
                           (True, False): 'write_only_resolved', (False, False): 'neither_resolved'}[(any_B, any_H)]
        out['new_source_processing_resolved'] = any_uN
    else:
        late = [r for r in rows if r['path'] != 'main' or r['segment'] in ('question', 'instruction', 'tail', 'last', 'cand')]
        ref['E4_late_write_needs_late_needle'] = 'refuted' if any(resolved(r, 'u_B') for r in late) else 'not_refuted'
        out['after_withdrawal'] = {seg: {'positions': sum(1 for r in rows if (r['segment'] == seg)), 'u_B_resolved': sum(1 for r in rows if r['segment'] == seg and resolved(r, 'u_B')),
                                         'dA_Sbar_resolved': sum(1 for r in rows if r['segment'] == seg and resolved(r, 'dA_Sbar'))}
                                   for seg in ('question', 'instruction', 'tail', 'last', 'cand')}
    ref['E3_write_always_same'] = 'refuted' if any_B else 'not_refuted'
    ref['E5_only_transmission_under_same_A_B'] = 'refuted' if (any_A or any_B) else 'not_refuted'
    out['action_source_resolved'] = any_action or any_B
    # E6: end-state small does not mean absence; record cells where the end is unresolved but the path is not.
    e6 = {}
    for q in ('dH', 'dN') if same_start else ():
        e6[q] = {'end_unresolved': not resolved(tl, q), 'path_resolved': window[q]['resolved_positions'] > 0}
    for bg in BACKGROUNDS:
        d = tl.get(f'b_{bg}')
        if d:
            mid_W = any(r.get(f'b_{bg}') and r[f'b_{bg}']['W'] > RESOLVE * r[f'b_{bg}']['eW'] for r in main)
            mid_R = any(r.get(f'b_{bg}') and r[f'b_{bg}']['R'] > RESOLVE * r[f'b_{bg}']['eR'] for r in main)
            e6[f'W_{bg}'] = {'end_unresolved': not d['W'] > RESOLVE * d['eW'], 'path_resolved': mid_W}
            e6[f'R_{bg}'] = {'end_unresolved': not d['R'] > RESOLVE * d['eR'], 'path_resolved': mid_R}
    out['E6_end_small_but_path_resolved'] = {k: v for k, v in e6.items() if v['end_unresolved'] and v['path_resolved']}
    out['refutations'] = ref
    return out


def secondary(last_states, anchor, base):
    """Contract §7: r10, a01, e01 at t_L from the kernel's own post-last states, stacked over facts x layers."""
    t = torch()
    get = lambda arm: t.cat([last_states[(f'{base}-f{f}-required', anchor if arm != '00' else None, arm, layer)].double().flatten()
                             for f in (0, 1) for layer in LAYERS])
    S00, S10, S01, S11 = (get(a) for a in ('00', '10', '01', '11'))
    d10, d01, d11 = S10 - S00, S01 - S00, S11 - S00
    n11 = float(d11.norm())
    out = {'norm_d11': n11, 'norm_d10': float(d10.norm()), 'norm_d01': float(d01.norm()),
           'r10': float(d10.norm()) / n11, 'a01': float((d01 * d11).sum()) / n11 ** 2, 'e01': float((d01 - d11).norm()) / n11}
    out['pred_r10_below_0.5'] = out['r10'] < PRED['r10_max']
    out['near_reproduction_01'] = out['a01'] >= PRED['a01_min'] and out['e01'] <= PRED['e01_max']
    return out


# ---------------------------------------------------------------- run over a verified formal run

def load_run(run):
    import experiment as ex
    run = Path(run)
    v = ex.read(run / 'verification.json')
    assert v['status'] == 'passed' and v['stage'] == 'formal'
    recs = {}
    for w in sorted(run.glob('worker-*')):
        for p in sorted((w / 'records').glob('*.json')):
            rec = ex.read(p)
            rec['_dir'] = str(w)
            recs[rec['spec']['key']] = rec
    assert len(recs) == 84
    return recs


def analyze(run, out):
    t = torch()
    import experiment as ex
    out = Path(out)
    recs = load_run(run)
    traj = {}
    for k, r in recs.items():
        p = Path(r['_dir']) / r['tensor_file']
        assert ex.sha(p) == r['tensor_sha256'], p
        traj[k] = A1.from_capture(t.load(p, map_location='cpu', weights_only=False))
    validity = {f'{k}__{layer}': bound_validity(tr, layer) for k, tr in traj.items() for layer in LAYERS}
    invalid = [k for k, v in validity.items() if not v['valid']]
    result = {'schema': 1, 'status': 'stopped_engineering' if invalid else 'analyzed', 'constants': {'U32': U32, 'C_ROUND': C_ROUND, 'RESOLVE': RESOLVE, 'PRED': PRED},
              'bound_validity_failed': invalid, 'bound_validity': validity}
    if invalid:
        ex.write(out / 'formation-r01.json', result, immutable=True)
        return {'status': result['status'], 'invalid': invalid[:5]}
    items = sorted({r['item']['id'] for r in recs.values()})
    cells, rows_all, checks = {}, [], {'dH_identity_rel_max': 0.0, 'dN_identity_rel_max': 0.0, 'HN_sum_rel_max': 0.0, 'uHN_rel_max': 0.0,
                                       'dwr_sum_rel_max': 0.0, 'readout_identity_rel_max': 0.0}
    for anchor in ANCHORS:
        for iid in items:
            rec00 = recs[f'{iid}__clean__00']
            labels, b = rec00['segments']['labels'], rec00['b']
            for pname, (x, y, same) in PAIRS.items():
                kx = f'{iid}__{anchor}__{x}'
                ky = f'{iid}__clean__00' if y == '00' else f'{iid}__{anchor}__{y}'
                for layer in LAYERS:
                    rows, start = pair_process(traj[kx], traj[ky], labels, layer, b)
                    for r in rows:
                        for key, name, denom in (('dH_identity_rel', 'dH_identity_rel_max', 'dH'), ('dN_identity_rel', 'dN_identity_rel_max', 'dN'),
                                                 ('HN_sum_rel', 'HN_sum_rel_max', 'dS'), ('uH_plus_uN_vs_dA_Sbar_rel', 'uHN_rel_max', 'dA_Sbar')):
                            if r.get(key) is not None and r.get(denom, 0) > 0:
                                checks[name] = max(checks[name], r[key])
                        if r['do'] > 0:
                            checks['readout_identity_rel_max'] = max(checks['readout_identity_rel_max'], r['readout_identity_rel'])
                        for c in ('b', 'tau'):
                            for bg in BACKGROUNDS:
                                d = r.get(f'{c}_{bg}')
                                if d and r['dS'] > 0:
                                    checks['dwr_sum_rel_max'] = max(checks['dwr_sum_rel_max'], d['sum_rel'])
                        rows_all.append({'anchor': anchor, 'item_id': iid, 'base_id': rec00['item']['base_id'], 'pair': pname, 'layer': layer, **r})
                    cells[f'{anchor}__{iid}__{pname}__{layer}'] = cell_summary(rows, start, same)
    checks['passed'] = all(v <= 1e-8 for k, v in checks.items() if k != 'passed')
    result['identity_checks'] = checks
    if not checks['passed']:
        result['status'] = 'stopped_engineering'
        ex.write(out / 'formation-r01.json', result, immutable=True)
        return {'status': result['status'], 'checks': checks}
    result['cells'] = cells
    result['summary'] = summarize(cells)
    last_states = {}
    for k, r in recs.items():
        sp = r['spec']
        for layer in LAYERS:
            last_states[(sp['item_id'], sp['anchor'], sp['arm'], layer)] = traj[k]['layers'][str(layer)]['exposed']['last']
    bases = sorted({r['item']['base_id'] for r in recs.values()})
    sec = {a: {bse: secondary(last_states, a, bse) for bse in bases} for a in ANCHORS}
    sec['L0_r10_above_L12_r10'] = {bse: sec[ANCHORS[0]][bse]['r10'] > sec[ANCHORS[1]][bse]['r10'] for bse in bases}
    result['secondary'] = sec
    result['endpoints'] = endpoints(recs)
    ex.write(out / 'formation-r01.json', result, immutable=True)
    A1.write_jsonl_zst(out / 'steps-r01.jsonl.zst', rows_all)
    return {'status': result['status'], 'identity_checks': checks, 'summary_counts': result['summary']['counts'],
            'secondary': {a: {bse: round(v['r10'], 3) for bse, v in sec[a].items()} for a in ANCHORS}}


def summarize(cells):
    """Counts per (anchor, pair) over the 6 bases x 2 facts x 3 layers = 36 cells; plus per-base listings."""
    counts, per_base = {}, {}
    for key, c in cells.items():
        anchor, iid, pname, layer = key.split('__')
        base = iid.split('-')[0]
        k = f'{anchor}__{pname}'
        d = counts.setdefault(k, {'cells': 0})
        d['cells'] += 1
        for e, v in c['refutations'].items():
            d.setdefault(e, {}).setdefault(v, 0)
            d[e][v] += 1
        if 'category' in c:
            d.setdefault('category', {}).setdefault(c['category'], 0)
            d['category'][c['category']] += 1
            d.setdefault('new_source_processing_resolved', 0)
            d['new_source_processing_resolved'] += bool(c['new_source_processing_resolved'])
            d.setdefault('first_step_operator_changed_action_unresolved', 0)
            d['first_step_operator_changed_action_unresolved'] += bool(c['first_step']['operator_changed_action_unresolved'])
            d.setdefault('start_resolved', 0)
            d['start_resolved'] += bool(c['first_step']['start_resolved'])
        d.setdefault('E6_cells', 0)
        d['E6_cells'] += bool(c['E6_end_small_but_path_resolved'])
        per_base.setdefault(k, {}).setdefault(base, []).append({'item': iid, 'layer': int(layer), **c['refutations'], 'category': c.get('category')})
    return {'counts': counts, 'per_base': per_base}


def endpoints(recs):
    out = {}
    for k, r in recs.items():
        sp = r['spec']
        key = f'{sp["anchor"] or "clean"}__{sp["arm"]}'
        out.setdefault(key, {}).setdefault(r['item']['base_id'], {})[r['item']['target_index']] = r
    res = {}
    for key, bases in out.items():
        res[key] = {}
        for base, facts in sorted(bases.items()):
            ll = {t_: [c['loglikelihood'] for c in facts[t_]['candidates']] for t_ in (0, 1)}
            res[key][base] = {'D': (facts[0]['first_step']['stop_advantage'] + facts[1]['first_step']['stop_advantage']) / 2,
                              'S_fact': (ll[0][0] - ll[0][1]) - (ll[1][0] - ll[1][1]),
                              'first_step_eos': [facts[t_]['first_step_eos'] for t_ in (0, 1)]}
    return res


# ---------------------------------------------------------------- selftest (offline rehearsal, §6.2)

def synthetic_pair(world, seed=0, n=20, H=3, d=8, b=7, branch=3):
    """Two arms sharing positions 0..b. Exposed 'kernel' states are exact recurrences (optionally perturbed)."""
    t = torch()
    g = t.Generator().manual_seed(seed)
    rnd = lambda *s: t.randn(*s, generator=g, dtype=t.float64)
    labels = ['head'] * 2 + ['fact'] * (b - 1) + ['question'] * 5 + ['instruction'] * 3 + ['tail'] * (n - b - 10) + ['last']
    assert len(labels) == n and labels[b] == 'fact' and labels[b + 1] == 'question'

    def drivers(m):
        return {'q': rnd(m, H, d), 'k': rnd(m, H, d), 'v': rnd(m, H, d), 'g': -t.rand(m, H, generator=g, dtype=t.float64) * 0.3,
                'beta': t.rand(m, H, generator=g, dtype=t.float64) * 0.8 + 0.1}
    Y, Yb = drivers(n), drivers(branch)
    X, Xb = {k: v.clone() for k, v in Y.items()}, {k: v.clone() for k, v in Yb.items()}
    after = t.arange(n) > b
    if world == 'write_only':
        X['v'][after] += rnd(int(after.sum()), H, d)
    elif world == 'process_only':
        X['g'][after] -= 0.5
    elif world == 'null':
        pass
    elif world == 'nullspace':      # beta changes at b+1 on a key orthogonal to every earlier key: Delta A != 0, Delta A S_b = 0
        for Z in (X, Y):
            Z['k'][:b + 1, :, d // 2:] = 0.0
            Z['k'][b + 1, :, :d // 2] = 0.0
        X['beta'][b + 1] = Y['beta'][b + 1] * 0.2
    elif world == 'cancel':         # write at b+1 then overwrite the same key with beta=1: path resolved, end difference gone
        X['v'][b + 1] += 2.0 * rnd(H, d)
        for Z in (X, Y):
            Z['k'][b + 2], Z['beta'][b + 2], Z['g'][b + 1], Z['g'][b + 2] = Z['k'][b + 1], 1.0 - 1e-12, 0.0, 0.0
            Z['k'][b + 3:] = 0.0
            Z['v'][b + 3:] = 0.0
            Z['g'][b + 3:] = 0.0
        X['v'][b + 2] = Y['v'][b + 2]
        Xb['k'][:] = 0.0
        Yb['k'][:] = 0.0
    else:
        raise ValueError(world)

    def traj(drv, drv_b):
        S0 = t.zeros(H, d, d, dtype=t.float64)
        S_pre, o1 = A1.run_path(S0, {k: v[:n - 1] for k, v in drv.items()})
        S_last, o2 = A1.run_path(S_pre, {k: v[n - 1:] for k, v in drv.items()})
        S_b, o3 = A1.run_path(S_last, drv_b)
        main = dict(drv, core_out=t.stack(o1 + o2), norm_out=t.stack(o1 + o2), out_proj=t.stack(o1 + o2).flatten(1))
        br = dict(drv_b, core_out=t.stack(o3), norm_out=t.stack(o3), out_proj=t.stack(o3).flatten(1))
        return {'layers': {'0': {'main': main, 'branches': {'cand0': br}, 'exposed': {'prefix': S_pre, 'last': S_last, 'cand0': S_b}}},
                'branches': ['cand0'], 'boundary': {}}
    return traj(X, Xb), traj(Y, Yb), labels, b


def selftest():
    report = {'cases': {}}
    expect = {
        'write_only': {'E1_first_step_only_write': 'not_refuted', 'E2_common_old_source_same_processing': 'not_refuted', 'E3_write_always_same': 'refuted'},
        'process_only': {'E1_first_step_only_write': 'refuted', 'E2_common_old_source_same_processing': 'refuted', 'E3_write_always_same': 'not_refuted'},
        'null': {'E1_first_step_only_write': 'not_refuted', 'E2_common_old_source_same_processing': 'not_refuted', 'E3_write_always_same': 'not_refuted',
                 'E5_only_transmission_under_same_A_B': 'not_refuted'},
        'nullspace': {'E1_first_step_only_write': 'not_refuted'},
    }
    for world, want in expect.items():
        for seed in range(3):
            X, Y, labels, b = synthetic_pair(world, seed)
            rows, start = pair_process(X, Y, labels, 0, b)
            for r in rows:
                if r.get('dH') is not None and r['dS'] > 0:
                    assert r['HN_sum_rel'] < 1e-10 and r['dH_identity_rel'] < 1e-10 and r['dN_identity_rel'] < 1e-10, (world, r)
                for c in ('b', 'tau'):
                    for bg in BACKGROUNDS:
                        dd = r.get(f'{c}_{bg}')
                        if dd and r['dS'] > 0:
                            assert dd['sum_rel'] < 1e-10, (world, c, bg, dd['sum_rel'])
                if r['do'] > 0:
                    assert r['readout_identity_rel'] < 1e-10
            c = cell_summary(rows, start, True)
            got = c['refutations']
            assert all(got[k] == v for k, v in want.items()), (world, seed, got)
            assert start['dS_b'] == 0.0
            if world == 'nullspace':
                assert c['first_step']['operator_changed_action_unresolved'], c['first_step']
            report['cases'][f'{world}:{seed}'] = {'refutations': got, 'category': c['category']}
    # Time cancellation: the write difference is resolved on the path but the end-state Delta N is not.
    X, Y, labels, b = synthetic_pair('cancel', 0)
    rows, start = pair_process(X, Y, labels, 0, b)
    c = cell_summary(rows, start, True)
    assert c['refutations']['E3_write_always_same'] == 'refuted' and 'dN' in c['E6_end_small_but_path_resolved'], c['E6_end_small_but_path_resolved']
    report['cancel'] = 'path-resolved write with unresolved end-state Delta N is flagged (E6)'
    # Different-start pair (10/00): late write difference present -> E4 refuted; absent -> not refuted.
    X, Y, labels, b = synthetic_pair('write_only', 1)
    assert cell_summary(*pair_process(X, Y, labels, 0, b), False)['refutations']['E4_late_write_needs_late_needle'] == 'refuted'
    X, Y, labels, b = synthetic_pair('null', 1)
    assert cell_summary(*pair_process(X, Y, labels, 0, b), False)['refutations']['E4_late_write_needs_late_needle'] == 'not_refuted'
    report['E4'] = 'refuted with late write difference, not refuted without'
    # Bound validity passes on exact states and fails when an exposed state is off by 1e-3 relative.
    X, _, _, _ = synthetic_pair('write_only', 2)
    assert bound_validity(X, 0)['valid']
    X['layers']['0']['exposed']['last'] = X['layers']['0']['exposed']['last'] * (1 + 1e-3)
    assert not bound_validity(X, 0)['valid']
    report['bound_validity'] = 'passes exact, fails 1e-3 perturbation'
    # Secondary predictions on constructed vectors.
    t = torch()
    st = {}
    for f in (0, 1):
        for layer in LAYERS:
            base = t.zeros(4, dtype=t.float64)
            st[(f'Z-f{f}-required', None, '00', layer)] = base
            st[(f'Z-f{f}-required', 'A', '11', layer)] = base + t.tensor([1., 0, 0, 0], dtype=t.float64)
            st[(f'Z-f{f}-required', 'A', '10', layer)] = base + t.tensor([0.3, 0, 0, 0], dtype=t.float64)
            st[(f'Z-f{f}-required', 'A', '01', layer)] = base + t.tensor([0.8, 0.1, 0, 0], dtype=t.float64)
    s = secondary(st, 'A', 'Z')
    assert abs(s['r10'] - 0.3) < 1e-12 and s['pred_r10_below_0.5'] and s['near_reproduction_01']
    for layer in LAYERS:
        st[('Z-f0-required', 'A', '10', layer)] = t.tensor([0.9, 0, 0, 0], dtype=t.float64)
        st[('Z-f1-required', 'A', '10', layer)] = t.tensor([0.9, 0, 0, 0], dtype=t.float64)
        st[('Z-f0-required', 'A', '01', layer)] = t.tensor([0.0, 1.0, 0, 0], dtype=t.float64)
    s = secondary(st, 'A', 'Z')
    assert not s['pred_r10_below_0.5'] and not s['near_reproduction_01']
    report['secondary'] = 'both predictions can hold and fail'
    report['status'] = 'passed'
    return report


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    q = sub.add_parser('run')
    q.add_argument('run')
    q.add_argument('--out', required=True)
    sub.add_parser('selftest')
    a = p.parse_args()
    sys.path.insert(0, str(HERE.parent / 'early-input-control-v1-2026-10-29'))
    value = analyze(a.run, a.out) if a.cmd == 'run' else selftest()
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    main()
