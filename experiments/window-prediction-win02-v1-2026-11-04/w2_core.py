"""WIN-02 pure pieces (CONTRACT r01; design v2 docs/cache-mechanism-win02-prediction-plan-v1-2026-11-04).  No model here.
Reuses the WIN-01 window/target/replace/bootstrap helpers; adds directional labels, the two-sided relation-M readout,
the per-prediction evidence table and the generalisation node."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'window-recovery-win01-v1-2026-11-04'))
import win_core as W1  # noqa: E402  (frozen WIN-01 helpers)

window_mask, arm_targets, replace, check_replace = W1.window_mask, W1.arm_targets, W1.replace, W1.check_replace
linear_layers, attn_layers, boot_index, describe, scen_mean = W1.linear_layers, W1.attn_layers, W1.boot_index, W1.describe, W1.scen_mean
G14, KV_LAYERS, WINDOWS, ATTR_ARM = W1.G14, W1.KV_LAYERS, W1.WINDOWS, W1.ATTR_ARM
STAGE2_CODE = W1.STAGE2_CODE

NEEDLES = ('N_L02_C5251_D-1', 'N_L03_C7666_D-1', 'N_L05_C2467_D-1', 'R0_L00_D-1')
NEEDLE_LAYER = {'N_L02_C5251_D-1': 2, 'N_L03_C7666_D-1': 3, 'N_L05_C2467_D-1': 5, 'R0_L00_D-1': 0}
NATIVE = {'N_L02_C5251_D-1': 5251, 'N_L03_C7666_D-1': 7666, 'N_L05_C2467_D-1': 2467}
RANDOM = 'R0_L00_D-1'
ARMS = ('T', 'R_all', 'KV_all', 'R+KV_all')
TASKS = ('fact', 'code')

TESTABLE_MIN_ERRORS = 12          # §4: T wrong on at least 12/48 inputs
STOP_LOW, STOP_HIGH = 2, 12       # P1/P2: <= 2 counts as 'no stop', >= 12 as 'stops'
CHANGE_MIN, NULL_BAND = 0.20, 0.10
M_POS_MIN_UNITS = 10              # §4: positive side of M needs >= 10 inputs wrong under T and under R_all
M_BREAK_MIN_UNITS = 10            # break side needs >= 10 inputs correct under R_all
M_BREAK_LO = 0.10                 # break counter-example: interval lower bound >= 0.10
NODE_MIN_TESTABLE, NODE_MIN_SHARE = 4, 0.75


def directional_label(d, expected_sign):
    """§4: d = describe() of a difference; expected_sign +1 or -1."""
    s = d['mean'] * expected_sign
    lo, hi = (d['lo'], d['hi']) if expected_sign > 0 else (-d['hi'], -d['lo'])
    if lo > 0 and s >= CHANGE_MIN:
        return 'holds'
    if hi < 0 and s <= -CHANGE_MIN:
        return 'reverse'
    if d['lo'] >= -NULL_BAND and d['hi'] <= NULL_BAND:
        return 'no_detectable_difference'
    return 'indeterminate'


def testable(y_t):
    return sum(1 for v in y_t.values() if v == 0) >= TESTABLE_MIN_ERRORS


def _desc(vals, units, scen):
    return describe(vals, units, scen, boot_index(units, scen))


def stop_label(n_stop):
    """P1 (W_pre) and P2 (after R_all): expected 'no stop'."""
    if n_stop <= STOP_LOW:
        return 'holds'
    if n_stop >= STOP_HIGH:
        return 'reverse'
    return 'indeterminate'


def p1(stops, task, needle):
    """stops[(task, needle, window, arm)] = count.  No information when neither W_all nor W_post stops >= 12."""
    if all(stops[(task, needle, w, 'T')] < STOP_HIGH for w in ('W_all', 'W_post')):
        return {'label': 'no_information', 'W_pre_T_stops': stops[(task, needle, 'W_pre', 'T')]}
    n = stops[(task, needle, 'W_pre', 'T')]
    return {'label': stop_label(n), 'W_pre_T_stops': n}


def p2(stops, task, needle):
    out = {}
    for w in WINDOWS:
        if stops[(task, needle, w, 'T')] >= STOP_HIGH:
            n = stops[(task, needle, w, 'R_all')]
            out[w] = {'label': stop_label(n), 'T_stops': stops[(task, needle, w, 'T')], 'R_all_stops': n}
    return out or {'label': 'not_applicable', 'reason': 'T never stops >= 12 in any window'}


def relation_m(y_t, y_r, y_rk, units, scen):
    """§4 two-sided M under W_all.
    positive: units with T wrong AND R_all wrong (denominator U+); share rescued by R_all+KV_pre.
    break:    units with R_all correct, whatever T was (denominator U-); share made wrong by R_all+KV_pre.
    Returns both sides, the full-input paired difference, and per-input transitions."""
    if not testable({u: y_t[u] for u in units}):
        return {'label': 'not_applicable', 'reason': 'T has fewer than 12 errors under W_all'}
    up = [u for u in units if y_t[u] == 0 and y_r[u] == 0]
    um = [u for u in units if y_r[u] == 1]
    out = {'U_plus': len(up), 'U_minus': len(um),
           'transitions': [{'unit': u, 'T': y_t[u], 'R_all': y_r[u], 'R_all+KV_pre': y_rk[u]} for u in units],
           'full_input_diff': _desc({u: y_rk[u] - y_r[u] for u in units}, units, scen)}
    if len(up) >= M_POS_MIN_UNITS:
        d = _desc({u: y_rk[u] for u in up}, up, scen)
        out['positive'] = {**d, 'rescued': sum(y_rk[u] for u in up), 'label': directional_label(d, +1)}
    else:
        out['positive'] = {'label': 'ceiling', 'rescued': sum(y_rk[u] for u in up), 'n': len(up)}
    if len(um) >= M_BREAK_MIN_UNITS:
        d = _desc({u: 1 - y_rk[u] for u in um}, um, scen)
        out['break'] = {**d, 'broken': sum(1 - y_rk[u] for u in um), 'counter_example': d['lo'] >= M_BREAK_LO}
    else:
        out['break'] = {'counter_example': False, 'broken': sum(1 - y_rk[u] for u in um), 'n': len(um), 'note': 'fewer than 10 R_all-correct inputs'}
    lab = out['positive']['label']
    out['label'] = 'counter_example' if out['break']['counter_example'] else lab
    return out


def p4(y_t, y_kv, y_r, units, scen):
    """W_pre, same T-wrong inputs: KV_all minus R_all, expected positive."""
    if not testable({u: y_t[u] for u in units}):
        return {'label': 'not_applicable'}
    uw = [u for u in units if y_t[u] == 0]
    d = _desc({u: y_kv[u] - y_r[u] for u in uw}, uw, scen)
    return {**d, 'kv_rescued': sum(y_kv[u] for u in uw), 'r_rescued': sum(y_r[u] for u in uw), 'label': directional_label(d, +1)}


def p5(cells, task, units, scen):
    """R0: full-input paired E(W_post, R_all) - E(W_all, R_all), expected positive; plus the stop pattern."""
    g = lambda w, a: cells[(task, RANDOM, w, a)]   # noqa: E731
    if not (testable(g('W_post', 'T')) and testable(g('W_all', 'T'))):
        return {'label': 'not_applicable'}
    e = {u: (g('W_post', 'R_all')[u] - g('W_post', 'T')[u]) - (g('W_all', 'R_all')[u] - g('W_all', 'T')[u]) for u in units}
    d = _desc(e, units, scen)
    return {**d, 'label': directional_label(d, +1)}


def node(m_cells):
    """§6 generalisation node over the 8 (needle, task) relation-M cells.  A progression rule for this card only."""
    labels = {k: v['label'] for k, v in m_cells.items()}
    pos_testable = [k for k, v in m_cells.items() if v.get('positive', {}).get('label') in ('holds', 'reverse', 'no_detectable_difference', 'indeterminate')]
    holds = [k for k in pos_testable if m_cells[k]['positive']['label'] == 'holds']
    counter = [k for k, v in m_cells.items() if v['label'] == 'counter_example' or v.get('positive', {}).get('label') == 'reverse']
    if counter:
        branch = 'fork'
    elif len(pos_testable) < NODE_MIN_TESTABLE:
        branch = 'mostly_untestable'
    elif len(holds) >= NODE_MIN_SHARE * len(pos_testable):
        branch = 'supported_in_these_conditions'
    elif len(holds) <= 2:
        branch = 'insufficient'
    else:
        branch = 'mixed'
    return {'branch': branch, 'positive_testable': sorted(map(str, pos_testable)), 'holds': sorted(map(str, holds)),
            'counter_examples': sorted(map(str, counter)), 'labels': {str(k): v for k, v in labels.items()}}
