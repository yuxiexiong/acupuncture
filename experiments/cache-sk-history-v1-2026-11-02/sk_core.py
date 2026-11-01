"""SK-01 pure rules (CONTRACT.zh-CN.md r01 §4–5).  D = max stop logit - max non-stop logit (raw).
Main (entry x_T, conv C): S0 = D10 - D00, S1 = D11 - D01, K0 = D01 - D00, K1 = D11 - D10, H = D11 - D00, J = D11 - D10 - D01 + D00.
Native: N = D(P) - D(C_native); R_S = D(P) - D(P_S0); R_K = D(P) - D(P_K0); R_SK = D(P) - D(P_SK0);
        J_native = D(P) - D(P_S0) - D(P_K0) + D(P_SK0).
"""
RULE = {'N_min': 1.0, 'H_min': 1.0, 'eps_abs': 0.5, 'eps_rel': 0.2, 'r_abs': 0.5, 'r_rel': 0.2, 'r_gap': 0.5,
        'scen_count': 5, 'near': 0.125}


def main_effects(D00, D10, D01, D11):
    return {'S0': D10 - D00, 'S1': D11 - D01, 'K0': D01 - D00, 'K1': D11 - D10, 'H': D11 - D00, 'J': D11 - D10 - D01 + D00}


def native_effects(DC, DP, DS0, DK0, DSK0):
    return {'N': DP - DC, 'R_S': DP - DS0, 'R_K': DP - DK0, 'R_SK': DP - DSK0, 'J_native': DP - DS0 - DK0 + DSK0}


def eps(H):
    return max(RULE['eps_abs'], RULE['eps_rel'] * abs(H))


def r_thr(N):
    return max(RULE['r_abs'], RULE['r_rel'] * N)


def main_category(m, nat):
    """Applicable iff N >= 1 and H >= 1.  Categories (descriptive, frozen order):
    S_concentrated: |S0-H|<=e and |K0|<=e and |K1|<=e;  KV_concentrated: |K0-H|<=e and |S0|<=e and |S1|<=e;
    both -> resolution_insufficient; redundant: |S0-H|<=e and |K0-H|<=e; joint_distributed: S0 < H-e and K0 < H-e and J >= e;
    opposing: |S0|>e and |K0|>e and opposite signs; else other."""
    if not (nat['N'] >= RULE['N_min'] and m['H'] >= RULE['H_min']):
        if nat['N'] <= -RULE['N_min'] or m['H'] <= -RULE['H_min']:
            return 'reverse_effect'
        if nat['N'] >= RULE['N_min']:
            return 'native_strong_mixed_weak'
        return 'not_applicable'
    e = eps(m['H'])
    s = abs(m['S0'] - m['H']) <= e and abs(m['K0']) <= e and abs(m['K1']) <= e
    kv = abs(m['K0'] - m['H']) <= e and abs(m['S0']) <= e and abs(m['S1']) <= e
    if s and kv:
        return 'resolution_insufficient'
    if s:
        return 'S_concentrated'
    if kv:
        return 'KV_concentrated'
    if abs(m['S0'] - m['H']) <= e and abs(m['K0'] - m['H']) <= e:
        return 'redundant'
    if m['S0'] < m['H'] - e and m['K0'] < m['H'] - e and m['J'] >= e:
        return 'joint_distributed'
    if abs(m['S0']) > e and abs(m['K0']) > e and (m['S0'] > 0) != (m['K0'] > 0):
        return 'opposing'
    return 'other'


def p_native(nat):
    """Unconditional (all inputs with N >= 1): R_S >= max(0.5, 0.2N) and R_S - R_K >= 0.5."""
    if nat['N'] < RULE['N_min']:
        return 'not_applicable'
    ok = nat['R_S'] >= r_thr(nat['N']) and nat['R_S'] - nat['R_K'] >= RULE['r_gap']
    return 'support' if ok else 'violate'


def native_pattern(nat):
    """Descriptive with the joint recovery arm (thr = max(0.5, 0.2N))."""
    if nat['N'] < RULE['N_min']:
        return 'not_applicable'
    t = r_thr(nat['N'])
    s, k, sk = nat['R_S'] >= t, nat['R_K'] >= t, nat['R_SK'] >= t
    if not s and not k and sk:
        return 'redundant_or_substitutive'
    if not s and not k and not sk:
        return 'recovery_ops_weak'
    if s and not k:
        return 'S_recovery'
    if k and not s:
        return 'KV_recovery'
    return 'both_recover'


def scenario_pairs(values):
    out = {}
    for iid, v in values.items():
        sc, f = iid.rsplit('-', 1)
        out.setdefault(sc, {})[f] = v
    return {s: (d['f0'], d['f1']) for s, d in sorted(out.items())}


def direction_label(pairs, target=None):
    """>= 5/6 scenarios with the same label in both facts (fixed denominator 6)."""
    counts = {}
    for s, (a, b) in pairs.items():
        if a == b:
            counts[a] = counts.get(a, 0) + 1
    if target is not None:
        return counts.get(target, 0) >= RULE['scen_count'], counts
    best = [k for k, v in counts.items() if v >= RULE['scen_count']]
    return (best[0] if best else None), counts


def near_boundaries(m, nat):
    """Distances to every frozen boundary that is within 0.125 (BF16 step) -> precision-sensitive."""
    e, t = eps(m['H']), r_thr(nat['N'])
    gaps = {'S0-H': e - abs(m['S0'] - m['H']), 'K0': e - abs(m['K0']), 'K1': e - abs(m['K1']), 'K0-H': e - abs(m['K0'] - m['H']),
            'S0': e - abs(m['S0']), 'S1': e - abs(m['S1']), 'R_S': nat['R_S'] - t, 'R_S-R_K': nat['R_S'] - nat['R_K'] - RULE['r_gap'],
            'H_min': m['H'] - RULE['H_min'], 'N_min': nat['N'] - RULE['N_min']}
    return {k: v for k, v in gaps.items() if abs(v) <= RULE['near']}
