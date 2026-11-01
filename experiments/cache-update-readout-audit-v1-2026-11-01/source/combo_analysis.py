"""CFM-CACHE-COMBINATION v1 readouts (CONTRACT.zh-CN.md sections 5-6). Pure Python; descriptive only.

python combo_analysis.py run RUN_DIR --out ANALYSIS_DIR
python combo_analysis.py selftest
"""
import argparse
from itertools import combinations
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
GROUPS = ('S', 'F', 'K')
PAIRS = ('C|CT', 'TC|T', 'C|T')
STOP = (248044, 248046)
SHOW_MIN = 1.0          # ratios are shown only if |Delta| >= 1 logit and |Delta| > numeric bound (display rule only)


def mn(m):
    return ''.join(g for g in GROUPS if g in m) or '0'


SUBSETS = [frozenset(c) for r in range(4) for c in combinations(GROUPS, r)]
FULL = frozenset(GROUPS)


def decompose(d):
    """d: {subset-name: value} for one base. Returns main effects, pair interactions, triple interaction, identity."""
    v = lambda *g: d[mn(frozenset(g))]
    m = {i: v(i) - v() for i in GROUPS}
    I2 = {i + j: v(i, j) - v(i) - v(j) + v() for i, j in combinations(GROUPS, 2)}
    I3 = v(*GROUPS) - sum(v(i, j) for i, j in combinations(GROUPS, 2)) + sum(v(i) for i in GROUPS) - v()
    delta = v(*GROUPS) - v()
    total = sum(m.values()) + sum(I2.values()) + I3
    return {'main': m, 'pair': I2, 'triple': I3, 'delta': delta, 'identity_residual': total - delta}


def conditional(d):
    """Effect of adding group i on every background N (N without i)."""
    out = {}
    for i in GROUPS:
        for N in SUBSETS:
            if i in N:
                continue
            out[f'+{i}|{mn(N)}'] = d[mn(N | {i})] - d[mn(N)]
    return out


def metric_values(cell, nonstop, stop=STOP):
    tl = cell['token_logits']
    out = {'D': cell['stop_advantage'], 'D_fix': cell['stop_advantage'] * cell['final_norm']['r_over_rC']}
    for s in stop:
        for c in nonstop:
            if str(c) in tl:
                out[f'{s}-{c}'] = tl[str(s)] - tl[str(c)]
    out[f'{stop[1]}-{stop[0]}'] = tl[str(stop[1])] - tl[str(stop[0])]
    return out


def pair_readout(scores, pmap, nonstop, stop=STOP):
    """pmap: {M-name: cell name} for base a (M from b). Both bases are reported (base b: d_b(M) = d_a(complement M))."""
    vals = {k: metric_values(scores[c], nonstop, stop) for k, c in pmap.items()}
    eta = {k: scores[c]['eta'] for k, c in pmap.items()}
    metrics = list(vals['0'])
    out = {}
    for met in metrics:
        da = {k: vals[k][met] for k in vals}
        db = {mn(m): da[mn(FULL - m)] for m in SUBSETS}
        dec_a, dec_b = decompose(da), decompose(db)
        delta = dec_a['delta']
        bound = 2 * (eta['0'] + eta['SFK'])
        show = abs(delta) >= SHOW_MIN and abs(delta) > bound
        A = {k: da[k] - da['0'] for k in da}
        R = {mn(m): da['SFK'] - da[mn(FULL - m)] for m in SUBSETS}
        out[met] = {'d': da, 'delta': delta, 'endpoint_bound': bound, 'ratios_shown': show,
                    'A': A, 'R': R, 'A_over_delta': {k: v / delta for k, v in A.items()} if show else None,
                    'R_over_delta': {k: v / delta for k, v in R.items()} if show else None,
                    'decomp_base_a': dec_a, 'decomp_base_b': dec_b, 'conditional': conditional(da)}
    # numeric bounds of each decomposition term (sum over the cells it uses, 2 eta each)
    out['term_bounds'] = {'main': 2 * (eta['0'] + max(eta[g] for g in GROUPS)),
                          'pair': 2 * sum(eta[k] for k in eta if len(k) <= 2 or k == '0'),
                          'triple': 2 * sum(eta.values())}
    out['winners'] = {k: [scores[c]['stop_winner'], scores[c]['nonstop_winner']] for k, c in pmap.items()}
    out['EOS'] = {k: bool(scores[c]['first_step_eos']) for k, c in pmap.items()}
    return out


def profile_compare(pa, pb, met='D'):
    """Normalised cell values (d(M)-d(0))/Delta for two pairs sharing base C."""
    def norm(p):
        d, delta = p[met]['d'], p[met]['delta']
        return None if abs(delta) < SHOW_MIN else {k: (v - d['0']) / delta for k, v in d.items()}
    na, nb = norm(pa), norm(pb)
    if na is None or nb is None:
        return {'status': 'delta_too_small'}
    diff = {k: na[k] - nb[k] for k in na}
    nontriv = [k for k in na if k not in ('0', 'SFK')]
    order = lambda n: sorted(nontriv, key=lambda k: n[k])
    return {'a': na, 'b': nb, 'diff': diff, 'max_abs_diff': max(abs(v) for v in diff.values()),
            'order_a': order(na), 'order_b': order(nb), 'same_order': order(na) == order(nb)}


def stage_b(scores, pmap_cct, nonstop, u, stop=STOP):
    c = scores['B:C']
    ct = scores[pmap_cct['SFK']]
    mc, mct = metric_values(c, nonstop, stop), metric_values(ct, nonstop, stop)
    out = {'E_CT': {k: mct[k] - mc[k] for k in mc}}
    for k in ('CR0', 'CR1'):
        mk = metric_values(scores[f'B:{k}'], nonstop, stop)
        out[f'E_{k}'] = {x: mk[x] - mc[x] for x in mc}
        out[f'{k}_over_CT_D'] = out[f'E_{k}']['D'] / out['E_CT']['D'] if abs(out['E_CT']['D']) >= SHOW_MIN else None
        out[f'{k}_winners'] = [scores[f'B:{k}']['stop_winner'], scores[f'B:{k}']['nonstop_winner']]
    out['CT_winners'] = [ct['stop_winner'], ct['nonstop_winner']]
    out['u_dist'] = u
    return out


def fact_readout(rec, nonstop, stop=STOP):
    s = rec['scores']
    pairs = {p: pair_readout(s, rec['pairs'][p], nonstop, stop) for p in PAIRS}
    return {'pairs': pairs, 'profile_CT_vs_T': {met: profile_compare(pairs['C|CT'], pairs['C|T'], met) for met in ('D', 'D_fix')},
            'stage_B': stage_b(s, rec['pairs']['C|CT'], nonstop, rec['u_dist']['B'], stop)}


def mean_d(f0, f1, pair, met='D'):
    return {k: (f0['pairs'][pair][met]['d'][k] + f1['pairs'][pair][met]['d'][k]) / 2 for k in f0['pairs'][pair][met]['d']}


def scenario(facts):
    out = {'per_fact': facts, 'mean': {}}
    for pair in PAIRS:
        out['mean'][pair] = {}
        for met in ('D', 'D_fix'):
            d = mean_d(facts['0'], facts['1'], pair, met)
            dec = decompose(d)
            show = abs(dec['delta']) >= SHOW_MIN
            out['mean'][pair][met] = {'d': d, 'decomp_base_a': dec,
                                      'decomp_base_b': decompose({mn(m): d[mn(FULL - m)] for m in SUBSETS}),
                                      'A_over_delta': {k: (v - d['0']) / dec['delta'] for k, v in d.items()} if show else None}
    for met in ('D', 'D_fix'):
        pa = {met: {'d': out['mean']['C|CT'][met]['d'], 'delta': out['mean']['C|CT'][met]['decomp_base_a']['delta']}}
        pb = {met: {'d': out['mean']['C|T'][met]['d'], 'delta': out['mean']['C|T'][met]['decomp_base_a']['delta']}}
        out['mean'].setdefault('profile_CT_vs_T', {})[met] = profile_compare(pa, pb, met)
    b0, b1 = facts['0']['stage_B'], facts['1']['stage_B']
    out['mean']['stage_B_D'] = {k: (b0[k]['D'] + b1[k]['D']) / 2 for k in ('E_CT', 'E_CR0', 'E_CR1')}
    return out


def summarize(records, tokens):
    by = {}
    for rec in records:
        b, t = rec['item']['base_id'], str(rec['item']['target_index'])
        by.setdefault(b, {})[t] = fact_readout(rec, tokens['items'][rec['item']['id']]['nonstop'])
    rows = {b: scenario(f) for b, f in sorted(by.items())}
    worst_identity = max(abs(dd['identity_residual']) for r in rows.values() for p in PAIRS for met in ('D', 'D_fix')
                         for dd in (r['mean'][p][met]['decomp_base_a'], r['mean'][p][met]['decomp_base_b']))
    return {'rows': rows, 'max_identity_residual': worst_identity}


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
    tokens = ex.read(HERE.parent / 'cache-formation-readout-bridge-v1-2026-10-31/data/frozen-tokens-r01.json')
    result = summarize(recs, tokens)
    Path(out).mkdir(parents=True, exist_ok=True)
    ex.write(Path(out) / 'combo-readouts-r01.json', result, immutable=True)
    return {'max_identity_residual': result['max_identity_residual'], 'scenarios': len(result['rows'])}


# ---------------------------------------------------------------- selftest

def _cell(D, r=1.0, eta=0.01):
    return {'stop_advantage': D, 'final_norm': {'r_over_rC': r}, 'eta': eta, 'stop_winner': 248044, 'nonstop_winner': 7,
            'first_step_eos': D > 0, 'token_logits': {'248044': D, '248046': D - 1.0, '7': 0.0}}


def _scores(da, db_extra=None):
    """Pair C|CT with values da[M-name]; C|T reuses C endpoint and its own values; TC|T arbitrary."""
    s, pm = {}, {}
    for k, v in da.items():
        s[f'a{k}'] = _cell(v)
        pm[k] = f'a{k}'
    return s, pm


def selftest():
    # identity on arbitrary non-additive values
    d = {'0': -20.0, 'S': -18.0, 'F': -10.0, 'K': -19.0, 'SF': -5.0, 'SK': -17.5, 'FK': -9.0, 'SFK': -2.0}
    dec = decompose(d)
    assert abs(dec['identity_residual']) < 1e-12 and abs(dec['delta'] - 18.0) < 1e-12
    assert abs(dec['main']['F'] - 10.0) < 1e-12 and abs(dec['pair']['SF'] - (-5 + 18 + 10 - 20)) < 1e-12
    # additive case: no interactions
    add = {mn(m): -20.0 + sum({'S': 2.0, 'F': 10.0, 'K': 6.0}[g] for g in m) for m in SUBSETS}
    da = decompose(add)
    assert all(abs(v) < 1e-12 for v in da['pair'].values()) and abs(da['triple']) < 1e-12
    # pure triple interaction: all partial swaps zero, full swap = Delta
    tri = {mn(m): (-20.0 if m != FULL else -2.0) for m in SUBSETS}
    dt = decompose(tri)
    assert all(abs(v) < 1e-12 for v in dt['main'].values()) and abs(dt['triple'] - 18.0) < 1e-12
    # base b equals reverse direction
    db = decompose({mn(m): d[mn(FULL - m)] for m in SUBSETS})
    assert abs(db['delta'] + 18.0) < 1e-12 and abs(db['identity_residual']) < 1e-12
    # pair readout: ratio display rule both ways, conditional effects
    s, pm = _scores(d)
    pr = pair_readout(s, pm, [7])
    assert pr['D']['ratios_shown'] and abs(pr['D']['A_over_delta']['F'] - 10 / 18) < 1e-12
    assert abs(pr['D']['conditional']['+S|F'] - (-5.0 + 10.0)) < 1e-12
    small = {k: v * 0.01 for k, v in d.items()}
    s2, pm2 = _scores(small)
    assert pair_readout(s2, pm2, [7])['D']['ratios_shown'] is False
    s3, pm3 = _scores(d)
    for c in s3.values():
        c['eta'] = 10.0
    assert pair_readout(s3, pm3, [7])['D']['ratios_shown'] is False
    # profile comparison: identical vs different
    p1 = pair_readout(s, pm, [7])
    same = profile_compare(p1, p1)
    assert same['max_abs_diff'] == 0 and same['same_order']
    s4, pm4 = _scores(add)
    diff = profile_compare(p1, pair_readout(s4, pm4, [7]))
    assert diff['max_abs_diff'] > 0.1
    assert profile_compare(pair_readout(s2, pm2, [7]), p1)['status'] == 'delta_too_small'
    # stage B
    sc = {'B:C': _cell(-20.0), 'B:CR0': _cell(-19.5), 'B:CR1': _cell(-20.2), 'ct': _cell(-2.0)}
    b = stage_b(sc, {'SFK': 'ct'}, [7], {})
    assert abs(b['E_CT']['D'] - 18.0) < 1e-12 and abs(b['CR0_over_CT_D'] - 0.5 / 18) < 1e-12
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
