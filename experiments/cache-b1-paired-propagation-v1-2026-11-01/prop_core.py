"""B1 paired propagation analysis: pure pieces (plan docs/cache-b1-paired-propagation-analysis-plan-v1-2026-11-01 r2).

Frozen candidate screening (§4.1) and the descriptive unit response (§3.4).
"""
import statistics

RULE = {'min_scen': 5, 'margin': 0.1, 'display_rel_min': 1e-4, 'closure_rel': 1e-10}
LAYERS_SCREENED = tuple(range(14, 32))
PARTS = ('mix', 'rest')


def modules():
    return [f'{l}:{p}' for l in LAYERS_SCREENED for p in PARTS]


def closure_ok(parts, total):
    """Telescoping closure in FP64: |sum(parts) - total| <= 1e-10 * max(1, sum |terms|)."""
    s = sum(parts)
    scale = max(1.0, sum(abs(x) for x in parts) + abs(total))
    return abs(s - total) <= RULE['closure_rel'] * scale, abs(s - total)


def screen(c, scen_of):
    """c: input -> {'DEL': value, 'RAND0': value, 'RAND1': value} for ONE module, ONE background, ONE direction.
    Returns per-scenario pass and the module decision (plan §4.1)."""
    by = {}
    for i, v in c.items():
        by.setdefault(scen_of[i], []).append(v)
    st = {}
    for s, vs in sorted(by.items()):
        assert len(vs) == 2, (s, len(vs))
        d = [v['DEL'] for v in vs]
        same = (d[0] > 0 and d[1] > 0) or (d[0] < 0 and d[1] < 0)
        m = statistics.mean(d)
        ref = max(statistics.mean(abs(v[f'RAND{j}']) for v in vs) for j in (0, 1))
        st[s] = {'mean_DEL': m, 'random_ref': ref, 'pass': bool(same and abs(m) > ref + RULE['margin']),
                 'sign': (1 if m > 0 else -1 if m < 0 else 0)}
    passed = [v for v in st.values() if v['pass']]
    signs = {v['sign'] for v in passed}
    selected = len(passed) >= RULE['min_scen'] and len(signs) == 1
    return {'scenarios': st, 'n_pass': len(passed), 'selected': selected,
            'mean_abs_DEL': statistics.mean(abs(v['mean_DEL']) for v in st.values())}


def decide(screens_n, screens_m):
    """screens_*: module -> screen() result for the primary direction. Plan §4.1 decision."""
    sel_n = [m for m, r in screens_n.items() if r['selected']]
    sel_m = [m for m, r in screens_m.items() if r['selected']]
    if sel_n:
        best = max(sel_n, key=lambda m: screens_n[m]['mean_abs_DEL'])
        return {'decision': 'candidate', 'priority': best, 'alternates': [m for m in sel_n if m != best], 'mixed_only_leads': sel_m}
    if sel_m:
        return {'decision': 'end_branch_mixed_lead_only', 'priority': None, 'alternates': [], 'mixed_only_leads': sel_m}
    return {'decision': 'end_branch_no_candidate', 'priority': None, 'alternates': [], 'mixed_only_leads': []}


def unit_response(num, den, ref_norm):
    """gamma = num / den, displayed only if den / ref_norm >= 1e-4."""
    show = den > 0 and ref_norm > 0 and den / ref_norm >= RULE['display_rel_min']
    return {'num': num, 'den': den, 'rel_den': den / ref_norm if ref_norm > 0 else None, 'gamma': num / den if show else None}


def scenario_unit_response(rows, scen_of, ref):
    """rows: input -> {'num', 'den'}; ref: input -> R norm. Means of numerator and denominator per scenario, then ratio."""
    by = {}
    for i, r in rows.items():
        by.setdefault(scen_of[i], []).append((r['num'], r['den'], ref[i]))
    return {s: unit_response(statistics.mean(x[0] for x in v), statistics.mean(x[1] for x in v), statistics.mean(x[2] for x in v))
            for s, v in sorted(by.items())}
