"""QC-01 frozen rules (plan §4).  Per-condition applicability, scenario/direction categories and statuses are the frozen NQ-01
rules (nq_core).  Added here: the pre-registered coverage prediction and the paired contrasts.

T_V status per condition and direction: nq_core.status(panel_ok, transferred, label(T_V), 'follow_query').
P_cov for a specification s in {N, L}: the tail condition reaches >= 3/4 'support' AND the broad condition (same text) does not
reach 3/4 even if every not-applicable direction had supported (n_support + n_not_applicable < 3).  If the broad condition already
reaches 3/4 -> 'no_room' (no visible repair space).  Otherwise 'unsupported' / 'indeterminate' (tail short only through
not-applicable directions).  P_cov overall holds iff both specifications are 'support'.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'cache-name-query-order-v1-2026-11-02'))
import nq_core as NK  # noqa: E402

RULE = dict(NK.RULE)
CONTRASTS = {'specification': [('NB', 'LB'), ('NA', 'LA'), ('NA-tail', 'LA-tail')],
             'coverage': [('NA', 'NA-tail'), ('LA', 'LA-tail')],
             'layout': [('NB', 'NA-tail'), ('LB', 'LA-tail')]}


def tv_statuses(cond_result):
    """cond_result: nq_analysis.analyse(...) output for one condition."""
    ok = cond_result['C']['applicability']['panel_ok']
    return {d: NK.status(ok, x['damage']['transferred'], x['labels']['T_V'], 'follow_query') for d, x in cond_result['directions'].items()}


def p_cov_spec(broad_statuses, tail_statuses):
    t, b = NK.overall(tail_statuses), NK.overall(broad_statuses)
    if b['met']:
        return {'status': 'no_room', 'tail': t, 'broad': b}
    if t['met'] and b['n_support'] + b['n_not_applicable'] < RULE['dir_count']:
        return {'status': 'support', 'tail': t, 'broad': b}
    if t['met']:
        return {'status': 'indeterminate', 'tail': t, 'broad': b}            # broad could still reach 3/4 via n/a directions
    if t['n_support'] + t['n_not_applicable'] >= RULE['dir_count']:
        return {'status': 'indeterminate', 'tail': t, 'broad': b}            # tail short only through n/a directions
    return {'status': 'unsupported', 'tail': t, 'broad': b}


def p_cov(by_condition_statuses):
    n = p_cov_spec(by_condition_statuses['NA'], by_condition_statuses['NA-tail'])
    l = p_cov_spec(by_condition_statuses['LA'], by_condition_statuses['LA-tail'])
    return {'N': n, 'L': l, 'met': n['status'] == 'support' and l['status'] == 'support'}


def paired(a_ok, b_ok):
    """a_ok / b_ok: nq_id -> delivered (one arm, one direction) for two conditions."""
    assert set(a_ok) == set(b_ok)
    out = {'a_only': 0, 'b_only': 0, 'both': 0, 'neither': 0}
    for k in a_ok:
        x, y = a_ok[k], b_ok[k]
        out['both' if x and y else 'a_only' if x else 'b_only' if y else 'neither'] += 1
    return out
