"""EH-XC pure rules (CONTRACT.zh-CN.md r01 §3–4).  D = max stop logit - max non-stop logit (raw).
N = D(P) - D00;  E = D11 - D00;  H0 = D01 - D00;  H1 = D11 - D10;  X0 = D10 - D00;  X1 = D11 - D01;  I = D11 - D10 - D01 + D00.
Applicable (same input): N >= 1 and E >= 1 (logit, directional; not absolute values).
P_H: H0 >= 0.5 E and H0 > X0.   P_I: I >= max(0.5, 0.1 E).
"""
import math

RULE = {'N_min': 1.0, 'E_min': 1.0, 'H_share': 0.5, 'I_abs': 0.5, 'I_rel': 0.1,
        'scen_count': 5, 'xc_count': 6, 'r_count': 3}


def effects(D00, D10, D01, D11, DP):
    return {'N': DP - D00, 'E': D11 - D00, 'H0': D01 - D00, 'H1': D11 - D10, 'X0': D10 - D00, 'X1': D11 - D01,
            'I': D11 - D10 - D01 + D00}


def applicability(e):
    N, E = e['N'], e['E']
    if N >= RULE['N_min'] and E >= RULE['E_min']:
        return 'applicable'
    if N <= -RULE['N_min'] or E <= -RULE['E_min']:
        return 'reverse_effect'
    if N >= RULE['N_min'] and E < RULE['E_min']:
        return 'native_strong_mixed_weak'
    return 'native_insufficient'


def p_h(e):
    return e['H0'] >= RULE['H_share'] * e['E'] and e['H0'] > e['X0']


def i_threshold(E):
    return max(RULE['I_abs'], RULE['I_rel'] * E)


def p_i(e):
    return e['I'] >= i_threshold(e['E'])


def fact_status(e):
    """Per-fact status for the three relations: 'support' / 'violate' / applicability category."""
    app = applicability(e)
    if app != 'applicable':
        return {'hist': app, 'inter': app, 'joint': app, 'applicability': app}
    h, i = p_h(e), p_i(e)
    return {'hist': 'support' if h else 'violate', 'inter': 'support' if i else 'violate',
            'joint': 'support' if (h and i) else 'violate', 'applicability': app}


def scenario_support(st0, st1, rel):
    """Both facts applicable and both satisfy -> support; else the reason."""
    a, b = st0[rel], st1[rel]
    if a == 'support' and b == 'support':
        return 'support'
    if 'support' in (a, b) and a != b:
        return 'fact_disagreement' if {a, b} <= {'support', 'violate'} else 'partly_not_applicable'
    if a == b:
        return a
    return 'mixed'


def scenario_pairs(values):
    out = {}
    for iid, v in values.items():
        s, f = iid.rsplit('-', 1)
        out.setdefault(s, {})[f] = v
    return {s: (d['f0'], d['f1']) for s, d in sorted(out.items())}


def needle_label(per_input_status, rel):
    """per_input_status: input -> fact_status.  Label 'replicated' iff >= 5/6 scenarios support (fixed denominator 6)."""
    pairs = scenario_pairs(per_input_status)
    sc = {s: scenario_support(a, b, rel) for s, (a, b) in pairs.items()}
    n = sum(v == 'support' for v in sc.values())
    return {'replicated': n >= RULE['scen_count'], 'n_support': n, 'scenarios': sc}


def panel(labels_joint, members, need):
    hits = [d for d in members if labels_joint[d]['replicated']]
    return {'met': len(hits) >= need, 'n': len(hits), 'of': len(members), 'members_met': hits}


def bf16_spacing(v):
    """Local BF16 spacing at |v| (8 significant bits)."""
    if v == 0 or not math.isfinite(v):
        return None
    return 2.0 ** (math.floor(math.log2(abs(v))) - 7)
