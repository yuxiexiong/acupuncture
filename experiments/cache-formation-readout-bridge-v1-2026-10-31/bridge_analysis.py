"""CFM-FORM-READ-BRIDGE v1 readouts (CONTRACT.zh-CN.md sections 5-6). Pure Python. All cuts are descriptive only.

python bridge_analysis.py run RUN_DIR --out ANALYSIS_DIR
python bridge_analysis.py selftest
"""
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
WEAK, PARTIAL, NEAR_HI, RESID, STATE_MIN, CONTRA = 0.3, 0.7, 1.3, 0.3, 0.3, 0.5
STOP = (248044, 248046)


def band(x):
    if x is None:
        return None
    if x < 0:
        return 'reverse'
    if x <= WEAK:
        return 'weak'
    if x < PARTIAL:
        return 'partial'
    if x <= NEAR_HI:
        return 'near'
    return 'overshoot'


def pair_label(r0, r1, res0, res1):
    """Descriptive label of a two-direction transfer (ratios to the reference difference; residuals likewise)."""
    if r0 is None or r1 is None:
        return None
    b0, b1 = band(r0), band(r1)
    if 'reverse' in (b0, b1):
        return 'reverse'
    if 'overshoot' in (b0, b1):
        return 'overshoot'
    if b0 == b1 == 'near' and abs(res0) <= RESID and abs(res1) <= RESID:
        return 'near_transfer'
    if b0 == b1 == 'weak':
        return 'weak'
    if 'weak' in (b0, b1):
        return 'background_dependent'
    return 'partial'


def diffs(Y):
    """Y: {score: value}. All paired quantities of contract section 5 for one readout."""
    q = {'dB': Y['Y_T'] - Y['Y_H'], 'EV0': Y['Y_T'] - Y['Y_U'], 'EV1': Y['Y_W'] - Y['Y_H'],
         'res_T_W': Y['Y_T'] - Y['Y_W'], 'res_U_H': Y['Y_U'] - Y['Y_H'],
         'dfull': Y['Y_T'] - Y['C'], 'EVC0': Y['Y_T'] - Y['Y_TC'], 'EVC1': Y['Y_CT'] - Y['C'],
         'res_TC_C': Y['Y_TC'] - Y['C'], 'res_T_CT': Y['Y_T'] - Y['Y_CT'],
         'Enull0': Y['Y_T'] - Y['Y_TR0'], 'Enull1': Y['Y_T'] - Y['Y_TR1'],
         'TU_delta': Y['Y_T'] - Y['Y_U'], 'TU_Qa': Y['Y_T'] - Y['J_T_SU'], 'TU_Qb': Y['J_U_ST'] - Y['Y_U'],
         'TU_res_a': Y['J_T_SU'] - Y['Y_U'], 'TU_res_b': Y['Y_T'] - Y['J_U_ST'],
         'WH_delta': Y['Y_W'] - Y['Y_H'], 'WH_Qa': Y['Y_W'] - Y['J_W_SH'], 'WH_Qb': Y['J_H_SW'] - Y['Y_H'],
         'WH_res_a': Y['J_W_SH'] - Y['Y_H'], 'WH_res_b': Y['Y_W'] - Y['J_H_SW']}
    q['I_BxV'] = Y['Y_T'] - Y['Y_U'] - Y['Y_W'] + Y['Y_H']   # B x V-source interaction (summary only)
    return q


def describe(q):
    """Labels from the D quantities of one fact or one scenario mean."""
    out = {}
    dB, df = q['dB'], q['dfull']
    if dB > 0:
        r0, r1 = q['EV0'] / dB, q['EV1'] / dB
        out['B_transfer'] = {'r_EV0': r0, 'r_EV1': r1, 'r_res_T_W': q['res_T_W'] / dB, 'r_res_U_H': q['res_U_H'] / dB,
                             'bands': [band(r0), band(r1)],
                             'label': pair_label(r0, r1, q['res_T_W'] / dB, q['res_U_H'] / dB)}
        for pre in ('TU', 'WH'):
            d = q[f'{pre}_delta']
            if abs(d) >= STATE_MIN * abs(dB):
                ra, rb = q[f'{pre}_Qa'] / d, q[f'{pre}_Qb'] / d
                out[f'state_{pre}'] = {'r_Qa': ra, 'r_Qb': rb, 'bands': [band(ra), band(rb)],
                                       'label': pair_label(ra, rb, q[f'{pre}_res_a'] / d, q[f'{pre}_res_b'] / d)}
            else:
                out[f'state_{pre}'] = {'label': 'upstream_V_weak_ratio_unstable', 'Qa': q[f'{pre}_Qa'], 'Qb': q[f'{pre}_Qb']}
    else:
        out['B_transfer'] = {'label': 'not_applicable_dB_le_0'}
    if df > 0:
        r0, r1 = q['EVC0'] / df, q['EVC1'] / df
        n0, n1 = q['Enull0'] / df, q['Enull1'] / df
        out['TC_transfer'] = {'r_EVC0': r0, 'r_EVC1': r1, 'r_null': [n0, n1], 'bands': [band(r0), band(r1)],
                              'null_bands': [band(n0), band(n1)],
                              'label': pair_label(r0, r1, q['res_TC_C'] / df, q['res_T_CT'] / df),
                              'EVC0_exceeds_both_null_draws': q['EVC0'] > max(q['Enull0'], q['Enull1']),
                              'EVC0_minus_max_null_over_dfull': (q['EVC0'] - max(q['Enull0'], q['Enull1'])) / df}
    else:
        out['TC_transfer'] = {'label': 'not_applicable_dfull_le_0'}
    return out


EFFECTS = {'dB': ('Y_T', 'Y_H'), 'EV0': ('Y_T', 'Y_U'), 'EV1': ('Y_W', 'Y_H'), 'dfull': ('Y_T', 'C'),
           'EVC0': ('Y_T', 'Y_TC'), 'EVC1': ('Y_CT', 'C'), 'Enull0': ('Y_T', 'Y_TR0'), 'Enull1': ('Y_T', 'Y_TR1'),
           'TU_Qa': ('Y_T', 'J_T_SU'), 'TU_Qb': ('J_U_ST', 'Y_U'), 'WH_Qa': ('Y_W', 'J_W_SH'), 'WH_Qb': ('J_H_SW', 'Y_H')}


def frozen_diffs(cell, nonstop):
    tl = cell['tl']
    out = {f'{s}-{c}': tl[str(s)] - tl[str(c)] for s in STOP for c in nonstop if str(c) in tl}
    out['248046-248044'] = tl['248046'] - tl['248044']
    return out


def fact_readouts(cells, nonstop):
    """cells: {score: {'D','r','tl','H','H_fix','eta','stop_winner','nonstop_winner','u_pairs'}} for one input."""
    rc = cells['C']['r']
    Y = {k: v['D'] for k, v in cells.items()}
    Yfix = {k: v['D'] * v['r'] / rc for k, v in cells.items()}
    fd = {k: frozen_diffs(v, nonstop) for k, v in cells.items()}
    eff = {}
    for name, (a, b) in EFFECTS.items():
        e_tot, e_fix = Y[a] - Y[b], Yfix[a] - Yfix[b]
        bound = 2 * (cells[a]['eta'] + cells[b]['eta'])
        fdt = {k: fd[a][k] - fd[b][k] for k in fd[a]}
        fdf = {k: fd[a][k] * cells[a]['r'] / rc - fd[b][k] * cells[b]['r'] / rc for k in fd[a]}
        contra = [k for k, v in fdt.items() if e_tot != 0 and (v > 0) != (e_tot > 0) and abs(v) >= CONTRA * abs(e_tot)
                  and k != '248046-248044']
        eff[name] = {'pair': [a, b], 'D_total': e_tot, 'D_fix': e_fix, 'D_scale': e_tot - e_fix,
                     'numeric_bound': bound, 'within_numeric_bound': abs(e_tot) <= bound,
                     'H_total': cells[a]['H'] - cells[b]['H'], 'H_fix': cells[a]['H_fix'] - cells[b]['H_fix'],
                     'frozen_total': fdt, 'frozen_fix': fdf, 'frozen_contradicting_D': contra,
                     'winners': {a: [cells[a]['stop_winner'], cells[a]['nonstop_winner']],
                                 b: [cells[b]['stop_winner'], cells[b]['nonstop_winner']]},
                     'u_dist': cells[a].get('u_pairs', {}).get(f'{a}|{b}')}
    q = diffs(Y)
    return {'D': Y, 'q': q, 'describe': describe(q), 'effects': eff,
            'EOS': {k: v['EOS'] for k, v in cells.items()}}


def scenario(facts):
    """facts: {0: fact_readouts, 1: fact_readouts}."""
    Y = {k: (facts[0]['D'][k] + facts[1]['D'][k]) / 2 for k in facts[0]['D']}
    q = diffs(Y)
    desc = describe(q)
    key = lambda d, sect: (d.get(sect) or {}).get('label')
    disagree = {s: key(facts[0]['describe'], s) != key(facts[1]['describe'], s)
                for s in ('B_transfer', 'state_TU', 'state_WH', 'TC_transfer')}
    return {'D_mean': Y, 'q_mean': q, 'describe_mean': desc, 'fact_labels_disagree': disagree,
            'per_fact': {str(t): facts[t] for t in (0, 1)},
            'EOS': {k: facts[0]['EOS'][k] + facts[1]['EOS'][k] for k in facts[0]['EOS']}}


def cells_from_record(rec):
    out = {}
    for k, s in rec['scores'].items():
        out[k] = {'D': s['stop_advantage'], 'r': s['final_norm']['r'], 'tl': s['token_logits'], 'H': s['entropy'],
                  'H_fix': s['entropy_fix_scale'], 'eta': s['eta'], 'EOS': int(bool(s['first_step_eos'])),
                  'stop_winner': s['stop_winner'], 'nonstop_winner': s['nonstop_winner'],
                  'u_pairs': {p: v['u_dist'] for p, v in rec['pairs'].items()}}
    return out


def summarize(table, nonstop):
    rows = {}
    for b, facts in sorted(table.items()):
        fr = {t: fact_readouts(facts[t], nonstop[b][t]) for t in (0, 1)}
        rows[b] = scenario(fr)
    counts = {}
    for r in rows.values():
        for sect, d in r['describe_mean'].items():
            lab = d.get('label')
            counts.setdefault(sect, {}).setdefault(lab, 0)
            counts[sect][lab] += 1
    return {'rows': rows, 'label_counts': counts}


def run(run_dir, out):
    sys.path.insert(0, str(HERE.parent / 'early-input-control-v1-2026-10-29'))
    import experiment as ex
    run_dir = Path(run_dir)
    v = ex.read(run_dir / 'verification.json')
    assert v['status'] == 'passed' and v['stage'] == 'formal'
    recs = []
    for w in sorted(p for p in run_dir.glob('worker-*') if p.is_dir()):
        rcp = ex.read(w / 'receipt.json')
        for p in sorted((w / 'records').glob('*.json')):
            assert ex.sha(p) == rcp['record_hashes'][str(p.relative_to(w))]
            recs.append(ex.read(p))
    assert len(recs) == 12
    tok = ex.read(HERE / 'data/frozen-tokens-r01.json')
    table, nonstop = {}, {}
    for rec in recs:
        b, t = rec['item']['base_id'], rec['item']['target_index']
        table.setdefault(b, {})[t] = cells_from_record(rec)
        nonstop.setdefault(b, {})[t] = tok['items'][rec['item']['id']]['nonstop']
    result = summarize(table, nonstop)
    result['reconstruction'] = {rec['item']['id']: rec['reconstruction'] for rec in recs}
    Path(out).mkdir(parents=True, exist_ok=True)
    ex.write(Path(out) / 'bridge-readouts-r01.json', result, immutable=True)
    return {'label_counts': result['label_counts'],
            'reconstruction_all_passed': all(v['passed'] for d in result['reconstruction'].values() for v in d.values())}


# ---------------------------------------------------------------- selftest

def _cells(Y, r=None, eta=0.01):
    r = r or {}
    out = {}
    for k, d in Y.items():
        out[k] = {'D': d, 'r': r.get(k, 1.0), 'tl': {'248044': d, '248046': d - 1.0, '7': 0.0}, 'H': 1.0, 'H_fix': 1.0,
                  'eta': eta, 'EOS': int(d > 0), 'stop_winner': 248044, 'nonstop_winner': 7, 'u_pairs': {}}
    return out


def _Y(dB=6.0, ev0=0.9, ev1=0.9, dfull=17.0, evc0=0.9, evc1=0.9, null=(0.1, 0.1), q_tu=(0.9, 0.9), q_wh=(0.9, 0.9)):
    """Score values with chosen ratios: EV0=ev0*dB, EV1=ev1*dB, residuals consistent with near transfer."""
    C = -20.0
    T = C + dfull
    H = T - dB
    U = T - ev0 * dB
    W = H + ev1 * dB
    TC = T - evc0 * dfull
    CT = C + evc1 * dfull
    Y = {'C': C, 'T_native': T + 2, 'Y_T': T, 'Y_H': H, 'Y_U': U, 'Y_W': W, 'Y_TC': TC, 'Y_CT': CT,
         'Y_TR0': T - null[0] * dfull, 'Y_TR1': T - null[1] * dfull}
    dtu, dwh = T - U, W - H
    Y['J_T_SU'] = T - q_tu[0] * dtu
    Y['J_U_ST'] = U + q_tu[1] * dtu
    Y['J_W_SH'] = W - q_wh[0] * dwh
    Y['J_H_SW'] = H + q_wh[1] * dwh
    return Y


def selftest():
    assert [band(x) for x in (-0.1, 0.0, 0.3, 0.5, 0.7, 1.3, 1.4)] == ['reverse', 'weak', 'weak', 'partial', 'near', 'near', 'overshoot']
    want = {'near_transfer': {}, 'weak': dict(ev0=0.1, ev1=0.2), 'reverse': dict(ev0=-0.4),
            'overshoot': dict(ev1=1.6), 'background_dependent': dict(ev0=0.1, ev1=0.8), 'partial': dict(ev0=0.5, ev1=0.5)}
    for lab, kw in want.items():
        d = describe(diffs(_Y(**kw)))
        assert d['B_transfer']['label'] == lab, (lab, d['B_transfer'])
    # (residual <= 0.3 is implied by both ratios in the near band: four-cell arithmetic identity, not tested separately)
    # state crossover: near vs unstable when upstream V weak
    assert describe(diffs(_Y()))['state_TU']['label'] == 'near_transfer'
    assert describe(diffs(_Y(q_tu=(0.1, 0.0))))['state_TU']['label'] == 'weak'
    assert describe(diffs(_Y(ev0=0.1, ev1=0.1)))['state_TU']['label'] == 'upstream_V_weak_ratio_unstable'
    # T<->C and the null draws
    d = describe(diffs(_Y(evc0=0.8, evc1=0.8, null=(0.1, 0.2))))['TC_transfer']
    assert d['label'] == 'near_transfer' and d['EVC0_exceeds_both_null_draws'] is True
    d = describe(diffs(_Y(evc0=0.8, null=(0.85, 0.1))))['TC_transfer']
    assert d['EVC0_exceeds_both_null_draws'] is False
    assert describe(diffs(_Y(dfull=-1.0)))['TC_transfer']['label'] == 'not_applicable_dfull_le_0'
    assert describe(diffs(_Y(dB=-1.0)))['B_transfer']['label'] == 'not_applicable_dB_le_0'
    # scale decomposition: identical r -> no scale part; different r -> scale part = D_a(1 - r_a/r_C) - ...
    fr = fact_readouts(_cells(_Y()), [7])
    assert abs(fr['effects']['dB']['D_scale']) < 1e-12
    fr = fact_readouts(_cells(_Y(), r={'Y_T': 2.0}), [7])
    e = fr['effects']['dB']
    assert abs(e['D_fix'] - (_Y()['Y_T'] * 2.0 - _Y()['Y_H'])) < 1e-9 and abs(e['D_scale']) > 0
    # numeric bound flag both ways
    assert fact_readouts(_cells(_Y(), eta=10.0), [7])['effects']['dB']['within_numeric_bound'] is True
    assert fact_readouts(_cells(_Y(), eta=0.001), [7])['effects']['dB']['within_numeric_bound'] is False
    # frozen-token contradiction both ways
    c = _cells(_Y())
    assert fact_readouts(c, [7])['effects']['EV0']['frozen_contradicting_D'] == []
    c['Y_U']['tl']['7'] = -100.0      # stop-7 rises in U although D falls -> contradicts D direction of EV0
    assert fact_readouts(c, [7])['effects']['EV0']['frozen_contradicting_D']
    # scenario + fact disagreement
    s = scenario({0: fact_readouts(_cells(_Y()), [7]), 1: fact_readouts(_cells(_Y(ev0=0.1, ev1=0.1)), [7])})
    assert s['fact_labels_disagree']['B_transfer'] is True
    s = summarize({'X': {0: _cells(_Y()), 1: _cells(_Y())}}, {'X': {0: [7], 1: [7]}})
    assert s['label_counts']['B_transfer'] == {'near_transfer': 1}
    return {'status': 'passed'}


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    q = sub.add_parser('run')
    q.add_argument('run')
    q.add_argument('--out', required=True)
    sub.add_parser('selftest')
    a = p.parse_args()
    print(json.dumps(run(a.run, a.out) if a.cmd == 'run' else selftest(), ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
