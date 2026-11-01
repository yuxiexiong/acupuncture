"""NR-01 pure rules (CONTRACT.zh-CN.md r01).  R(A) = D(P) - D(restore A to C), P = full native T.  N = D(P) - D(C_native).
Factors X (shallow/entry), F (deep conv), H (deep S + KV).  r_i = R(i); i_ij = R(ij) - R(i) - R(j);
i_XFH = R(XFH) - R(XF) - R(XH) - R(FH) + R(X) + R(F) + R(H);  N = sum r + sum i_ij + i_XFH  (R(XFH) == N by the 111 gate).
Keep-only-i retention L(i) = N - R(other two).
"""
CODES = {'X': '100', 'F': '010', 'H': '001', 'XF': '110', 'XH': '101', 'FH': '011', 'XFH': '111'}
RULE = {'N_min': 1.0, 'half': 0.5, 'tau_abs': 0.5, 'tau_rel': 0.1, 'scen_count': 5, 'near': 0.125}


def recoveries(D_P, D_cells):
    """D_cells: code -> D.  Returns R for every subset name."""
    return {name: D_P - D_cells[code] for name, code in CODES.items()}


def decompose(R, N):
    i_XF = R['XF'] - R['X'] - R['F']
    i_XH = R['XH'] - R['X'] - R['H']
    i_FH = R['FH'] - R['F'] - R['H']
    i_XFH = R['XFH'] - R['XF'] - R['XH'] - R['FH'] + R['X'] + R['F'] + R['H']
    out = {'r_X': R['X'], 'r_F': R['F'], 'r_H': R['H'], 'i_XF': i_XF, 'i_XH': i_XH, 'i_FH': i_FH, 'i_XFH': i_XFH,
           'cond_XF_given_H': i_XF + i_XFH, 'cond_XH_given_F': i_XH + i_XFH, 'cond_FH_given_X': i_FH + i_XFH,
           'L_X': N - R['FH'], 'L_F': N - R['XH'], 'L_H': N - R['XF'],
           'E_XFH': N - (R['X'] + R['F'] + R['H'])}
    out['identity_err'] = N - (R['X'] + R['F'] + R['H'] + i_XF + i_XH + i_FH + i_XFH)
    return out


def tau(N):
    return max(RULE['tau_abs'], RULE['tau_rel'] * N)


def sign_label(v, t):
    return 'positive' if v >= t else 'negative' if v <= -t else 'small'


def fact_predictions(dec, N):
    """Registered (speculative), on unseen quantities only.  P_X: R(X) < 0.5N.  P_XH: i_XH >= tau(N)."""
    if N < RULE['N_min']:
        return {'P_X': 'not_applicable', 'P_XH': 'not_applicable'}
    return {'P_X': 'support' if dec['r_X'] < RULE['half'] * N else 'violate',
            'P_XH': 'support' if dec['i_XH'] >= tau(N) else 'violate'}


def descriptive(dec, N):
    if N < RULE['N_min']:
        return {'applicable': False}
    t = tau(N)
    lab = {'applicable': True, 'tau': t,
           'strong_single_recovery': [f for f in 'XFH' if dec[f'r_{f}'] >= RULE['half'] * N],
           'single_retention_majority': [f for f in 'XFH' if dec[f'L_{f}'] >= RULE['half'] * N],
           'interaction_signs': {k: sign_label(dec[k], t) for k in ('i_XF', 'i_XH', 'i_FH', 'i_XFH')}}
    lab['additive_compatible'] = all(abs(dec[k]) < t for k in ('i_XF', 'i_XH', 'i_FH')) and abs(dec['E_XFH']) < t
    lab['reverse_or_over'] = [k for k in ('r_X', 'r_F', 'r_H') if dec[k] < 0 or dec[k] > N]
    return lab


def near_boundaries(dec, N):
    t = tau(N)
    gaps = {'P_X': RULE['half'] * N - dec['r_X'], 'P_XH': dec['i_XH'] - t}
    for k in ('i_XF', 'i_FH', 'i_XFH'):
        gaps[k + '_pos'] = dec[k] - t
        gaps[k + '_neg'] = -t - dec[k]
    return {k: v for k, v in gaps.items() if abs(v) <= RULE['near']}


def scenario_pairs(values):
    out = {}
    for iid, v in values.items():
        s, f = iid.rsplit('-', 1)
        out.setdefault(s, {})[f] = v
    return {s: (d['f0'], d['f1']) for s, d in sorted(out.items())}


def direction_status(pairs):
    """support if >= 5/6 scenarios support in both facts; unsupported if >= 5 scenarios applicable in both facts but support < 5;
    else insufficient."""
    sup = sum(a == 'support' and b == 'support' for a, b in pairs.values())
    app = sum(a != 'not_applicable' and b != 'not_applicable' for a, b in pairs.values())
    if sup >= RULE['scen_count']:
        return 'support', sup
    return ('unsupported' if app >= RULE['scen_count'] else 'insufficient'), sup
