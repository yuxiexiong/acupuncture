"""CGV-01 frozen read-outs (V2 plan §7 with the review amendments).  Continuous values, directions, paired fixes/breaks and coverage; no
'mechanism holds/fails' labels.  Shared scale across groups: scenario-equal means of per-input differences (M on target-not-first inputs; G, Y
on all inputs); descriptive 'stable' = |eq| >= 0.25 with all-but-two-scenario sign agreement replaced by the group rule (G1/G3: >= 4/6
scenarios; G2: 3/3 scenarios).  Old SRU labels (direct_dominant, ...) are reported as an additional descriptor only.  Triage flag (resource
rule; reads were run for every group, flag reported): endpoints to be swapped differ in natural Y for >= 1 input or any scenario |mean M diff|
>= 0.25.  Ratios D/DE and DE/g only when |denominator| >= 0.5, numerator/denominator/sign reported, not shares or ceilings."""
TH = {'abs': 0.25, 'den': 0.5, 'y_net': 2, 'y_scen': 2}


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def smeans(vals, scen):
    out = {}
    for i, v in vals.items():
        out.setdefault(scen[i], []).append(v)
    return {s: sum(x) / len(x) for s, x in out.items()}


def scen_rule(scen):
    n = len(set(scen.values()))
    return n if n <= 3 else 4


def desc(vals, scen, sign=1):
    sm = smeans(vals, scen)
    eq = mean(sm.values())
    need = scen_rule({i: scen[i] for i in vals})
    npos = sum(1 for v in sm.values() if sign * v > 0)
    nneg = sum(1 for v in sm.values() if sign * v < 0)
    lab = 'stable_expected' if (sign * eq >= TH['abs'] and npos >= need) else ('stable_opposite' if (-sign * eq >= TH['abs'] and nneg >= need) else 'not_stable')
    return {'eq': eq, 'scen': sm, 'n_scen_expected_sign': npos, 'n_scen': len(sm), 'descriptor': lab}


def ydiff(Ya, Yb, scen, sign=1):
    net = sign * sum(Yb[i] - Ya[i] for i in Ya)
    moved = {scen[i] for i in Ya if sign * (Yb[i] - Ya[i]) > 0}
    return {'net': net, 'fixed': sum(1 for i in Ya if Ya[i] == 0 and Yb[i] == 1), 'broken': sum(1 for i in Ya if Ya[i] == 1 and Yb[i] == 0),
            'n_scen_moved': len(moved), 'descriptor': 'multi_scenario' if (net >= TH['y_net'] and len(moved) >= TH['y_scen']) else 'none'}


def ratio(a, b):
    return a / b if (a is not None and b is not None and abs(b) >= TH['den']) else None


def contrast(Z, a, b, scen, ids, sign=1):
    return desc({i: Z[b][i] - Z[a][i] for i in ids}, scen, sign)


def triage(M, Y, a, b, scen, ids):
    sm = smeans({i: M[b][i] - M[a][i] for i in ids}, scen)
    return {'y_differs': any(Y[a][i] != Y[b][i] for i in Y[a]), 'max_scen_abs_dM': max(abs(v) for v in sm.values()),
            'continue': any(Y[a][i] != Y[b][i] for i in Y[a]) or max(abs(v) for v in sm.values()) >= TH['abs']}


def read_pair(Mc, Yc, M00, Y00, Mdonor, scen, tnf, sign):
    """Mc/Yc: {cell: {i: v}} for cells 10/01/11; 00 = receiver endpoint; Mdonor = donor endpoint M."""
    ids = sorted(tnf)
    eff = {c: desc({i: Mc[c][i] - M00[i] for i in ids}, scen, sign) for c in ('10', '01', '11')}
    ys = {c: ydiff(Y00, Yc[c], scen, sign) for c in ('10', '01', '11')}
    g = mean(smeans({i: Mdonor[i] - M00[i] for i in ids}, scen).values())
    d10, d01, d11 = eff['10']['eq'], eff['01']['eq'], eff['11']['eq']
    I_M = mean(smeans({i: Mc['11'][i] - Mc['10'][i] - Mc['01'][i] + M00[i] for i in ids}, scen).values())
    joint = {c: eff[c]['descriptor'] == 'stable_expected' and ys[c]['descriptor'] == 'multi_scenario' for c in ('10', '01', '11')}
    r10, r01 = ratio(d10, d11), ratio(d01, d11)
    if any(eff[c]['descriptor'] == 'stable_opposite' for c in ('10', '01', '11')):
        old = 'opposite'
    elif joint['11'] and joint['10'] and r10 is not None and r10 >= 0.75 and abs(r01) <= 0.25:
        old = 'direct_dominant'
    elif joint['11'] and joint['01'] and r01 is not None and r01 >= 0.75 and abs(r10) <= 0.25:
        old = 'correction_dominant'
    elif joint['10'] and joint['01']:
        old = 'both_single'
    elif joint['11']:
        old = 'joint_only'
    elif eff['11']['descriptor'] == 'stable_expected':
        old = 'diag_only'
    else:
        old = 'weak'
    return {'effects': eff, 'y': ys, 'g': g, 'D_over_DE': r10, 'E_over_DE': r01, 'DE_over_g': ratio(d11, g), 'I_M': I_M, 'old_label_descriptor': old}
