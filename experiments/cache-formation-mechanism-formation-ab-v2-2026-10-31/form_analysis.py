"""CFM-FORM-AB v2 readouts and pre-registered descriptions (CONTRACT.zh-CN.md sections 5-6). Pure Python.

python form_analysis.py run RUN_DIR --out ANALYSIS_DIR
python form_analysis.py selftest
"""
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
STRONG, WEAK, ENHANCE, JOINT_MORE = 0.7, 0.3, -0.3, 0.3
CELLS = ('C', 'T_native', 'X0', 'XA', 'XB', 'XAB')
DIFFS = {'A|B0': ('X0', 'XA'), 'A|B1': ('XB', 'XAB'), 'B|A0': ('X0', 'XB'), 'B|A1': ('XA', 'XAB'), 'AB': ('X0', 'XAB')}
EFFECTIVE = ('partial', 'strong', 'reversal')


def band(r):
    """Contract section 5 descriptive scale (not significance): R relative to Delta = D_X0 - D_C."""
    if r is None:
        return None
    if r > 1:
        return 'reversal'
    if r >= STRONG:
        return 'strong'
    if r > WEAK:
        return 'partial'
    if r >= ENHANCE:
        return 'weak'
    return 'enhance'


def contrasts(v, key='D'):
    """v: {cell: {'D':..., 'm':...}} -> paired differences, interaction, Delta, R and bands."""
    x = {c: v[c][key] for c in CELLS}
    diffs = {k: x[a] - x[b] for k, (a, b) in DIFFS.items()}
    inter = x['XAB'] - x['XA'] - x['XB'] + x['X0']
    delta = x['X0'] - x['C']
    ok = delta > 0
    R = {k: (d / delta if ok else None) for k, d in diffs.items()}
    return {'values': x, 'delta': delta, 'applicable': ok, 'diffs': diffs, 'interaction': inter,
            'interaction_over_delta': inter / delta if ok else None, 'R': R, 'bands': {k: band(r) for k, r in R.items()}}


def patterns(c):
    """Contract section 6 rows; several may hold at once. Returns {row: bool} or None when not applicable."""
    if not c['applicable']:
        return None
    b, R = c['bands'], c['R']
    single_max = max(R['A|B0'], R['B|A0'])
    eff = lambda k: b[k] in EFFECTIVE
    return {
        'B_strong_both__A_weak_both': b['B|A0'] == 'strong' and b['B|A1'] == 'strong' and b['A|B0'] == 'weak' and b['A|B1'] == 'weak',
        'A_strong_both__B_weak_both': b['A|B0'] == 'strong' and b['A|B1'] == 'strong' and b['B|A0'] == 'weak' and b['B|A1'] == 'weak',
        'both_partial__joint_more': b['A|B0'] == 'partial' and b['B|A0'] == 'partial' and R['AB'] - single_max > JOINT_MORE,
        'both_strong__joint_not_more': b['A|B0'] == 'strong' and b['B|A0'] == 'strong' and R['AB'] - single_max <= JOINT_MORE,
        'conditional_dependence': (b['A|B0'] == 'weak' and b['B|A0'] == 'weak' and b['AB'] in ('strong', 'reversal'))
                                  or (b['A|B0'] == 'weak' and eff('A|B1')) or (b['A|B1'] == 'weak' and eff('A|B0'))
                                  or (b['B|A0'] == 'weak' and eff('B|A1')) or (b['B|A1'] == 'weak' and eff('B|A0')),
        'enhancement_or_reversal': any(v in ('enhance', 'reversal') for v in b.values()),
        'all_weak': b['A|B0'] == 'weak' and b['B|A0'] == 'weak' and b['AB'] == 'weak',
    }


def cell_values(rec):
    s = rec['scores']
    return {c: {'D': s[c]['stop_advantage'], 'm': s[c]['m_fixed'], 'EOS': bool(s[c]['first_step_eos']),
                'stop_winner': s[c]['stop_winner'], 'nonstop_winner': s[c]['nonstop_winner']} for c in CELLS}


def scenario(facts):
    """facts: {0: cell_values, 1: cell_values} for one base."""
    assert set(facts) == {0, 1}
    mean = {c: {'D': (facts[0][c]['D'] + facts[1][c]['D']) / 2, 'm': (facts[0][c]['m'] + facts[1][c]['m']) / 2} for c in CELLS}
    main = contrasts(mean, 'D')
    fixed = contrasts(mean, 'm')
    per_fact = {t: contrasts(facts[t], 'D') for t in (0, 1)}
    disagree = (not per_fact[0]['applicable'] or not per_fact[1]['applicable']
                or any(per_fact[0]['bands'][k] != per_fact[1]['bands'][k] for k in DIFFS)
                or any((per_fact[0]['diffs'][k] > 0) != (per_fact[1]['diffs'][k] > 0) for k in DIFFS))
    switch = {t: sorted({(facts[t][c]['stop_winner'], facts[t][c]['nonstop_winner']) for c in ('X0', 'XA', 'XB', 'XAB')}) for t in (0, 1)}
    pat = patterns(main)
    if pat is not None:
        pat['fact_versions_disagree'] = disagree
    return {'D': {c: mean[c]['D'] for c in CELLS}, 'D_raw': {t: {c: facts[t][c]['D'] for c in CELLS} for t in (0, 1)},
            'EOS': {c: sum(facts[t][c]['EOS'] for t in (0, 1)) for c in CELLS},
            'main': main, 'fixed_token': fixed, 'per_fact': per_fact,
            'winner_switch': any(len(v) > 1 for v in switch.values()), 'winners': {str(t): switch[t] for t in (0, 1)},
            'interaction_D_vs_fixed_differ_in_band': (main['applicable'] and fixed['applicable']
                                                      and band(main['interaction_over_delta']) != band(fixed['interaction_over_delta'])),
            'patterns': pat}


def summarize(table):
    rows = {b: scenario(f) for b, f in sorted(table.items())}
    counts = {}
    for r in rows.values():
        for k, v in (r['patterns'] or {'not_applicable': True}).items():
            counts[k] = counts.get(k, 0) + int(bool(v))
    app = [r for r in rows.values() if r['main']['applicable']]
    signs = {k: sorted({(r['main']['diffs'][k] > 0) for r in app}) for k in DIFFS}
    return {'rows': rows, 'pattern_counts': counts, 'applicable': len(app),
            'scenarios_disagree_in_sign': {k: len(v) > 1 for k, v in signs.items()}}


def route_floor(records):
    """Numeric reference only: step route vs E2 chunk route |dD| / Delta_E2 per input (contract gate R)."""
    out = {}
    for rec in records:
        g = rec['route_gate']
        out[rec['item']['id']] = {k: g['rows'][k]['abs_diff'] / g['delta_e2'] for k in g['rows']}
    vals = [v for d in out.values() for v in d.values()]
    return {'per_input': out, 'max_over_delta_e2': max(vals) if vals else None}


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
    table = {}
    for rec in recs:
        table.setdefault(rec['item']['base_id'], {})[rec['item']['target_index']] = cell_values(rec)
    result = summarize(table)
    result['route_floor'] = route_floor(recs)
    Path(out).mkdir(parents=True, exist_ok=True)
    ex.write(Path(out) / 'form-ab-readouts-r01.json', result, immutable=True)
    return {'applicable': result['applicable'], 'pattern_counts': result['pattern_counts'],
            'route_floor_max': result['route_floor']['max_over_delta_e2']}


# ---------------------------------------------------------------- selftest (each description can and cannot occur)

def _facts(dc=-20.0, dx0=-3.0, ra=0.1, rb=0.1, rab=None, rb1=None, ra1=None, dc1=None):
    """Synthetic cell values with Delta = dx0 - dc and chosen R's (both facts identical unless dc1 differs)."""
    delta = dx0 - dc
    rab = (ra + rb) if rab is None else rab
    xa, xb, xab = dx0 - ra * delta, dx0 - rb * delta, dx0 - rab * delta
    if rb1 is not None:      # B|A1 = (XA - XAB)/delta
        xab = xa - rb1 * delta
    if ra1 is not None:      # A|B1 = (XB - XAB)/delta
        xab = xb - ra1 * delta
    def one(c0):
        vals = {'C': c0, 'T_native': dx0 + 2.0, 'X0': dx0, 'XA': xa, 'XB': xb, 'XAB': xab}
        return {c: {'D': v, 'm': v, 'EOS': v > 0, 'stop_winner': 1, 'nonstop_winner': 2} for c, v in vals.items()}
    return {0: one(dc), 1: one(dc if dc1 is None else dc1)}


def selftest():
    # band boundaries
    assert [band(x) for x in (1.2, 1.0, 0.7, 0.5, 0.3, 0.0, -0.3, -0.5)] == \
        ['reversal', 'strong', 'strong', 'partial', 'weak', 'weak', 'weak', 'enhance']
    cases = {
        'B_strong_both__A_weak_both': dict(ra=0.1, rb=0.9, rab=1.0),
        'A_strong_both__B_weak_both': dict(ra=0.9, rb=0.1, rab=1.0),
        'both_partial__joint_more': dict(ra=0.4, rb=0.45, rab=0.9),
        'both_strong__joint_not_more': dict(ra=0.8, rb=0.8, rab=0.85),
        'conditional_dependence': dict(ra=0.1, rb=0.1, rab=0.8),
        'enhancement_or_reversal': dict(ra=0.1, rb=-0.6, rab=-0.5),
        'all_weak': dict(ra=0.1, rb=0.05, rab=0.12),
    }
    for want, kw in cases.items():
        r = scenario(_facts(**kw))
        assert r['patterns'][want] is True, (want, r['main']['R'], r['patterns'])
        assert r['patterns']['fact_versions_disagree'] is False
        # every other row false for at least one case (rows can fail)
    for row in cases:
        assert any(scenario(_facts(**kw))['patterns'][row] is False for kw in cases.values()), row
    # interaction value and conditional via background: A weak alone but effective with B on
    r = scenario(_facts(ra=0.1, rb=0.2, ra1=0.6))
    assert r['patterns']['conditional_dependence'] and abs(r['main']['R']['A|B1'] - 0.6) < 1e-9
    assert abs(r['main']['interaction'] - (r['main']['values']['XAB'] - r['main']['values']['XA'] - r['main']['values']['XB'] + r['main']['values']['X0'])) < 1e-12
    # reversal beyond the clean baseline
    r = scenario(_facts(ra=0.1, rb=1.3, rab=1.3))
    assert r['main']['bands']['B|A0'] == 'reversal' and r['patterns']['enhancement_or_reversal']
    # Delta <= 0 -> not applicable, no labels
    r = scenario(_facts(dc=-3.0, dx0=-3.0))
    assert r['patterns'] is None and r['main']['R']['AB'] is None
    s = summarize({'X': _facts(dc=-3.0, dx0=-5.0), 'Y': _facts(ra=0.9, rb=0.1, rab=1.0)})
    assert s['applicable'] == 1 and s['pattern_counts']['not_applicable'] == 1
    # fact versions disagree when one fact has a different Delta
    r = scenario(_facts(ra=0.5, rb=0.1, dc1=-6.0))
    assert r['patterns']['fact_versions_disagree'] is True
    # scenario sign disagreement detection
    s = summarize({'X': _facts(ra=0.5, rb=0.1), 'Y': _facts(ra=-0.5, rb=0.1)})
    assert s['scenarios_disagree_in_sign']['A|B0'] is True and s['scenarios_disagree_in_sign']['B|A0'] is False
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
