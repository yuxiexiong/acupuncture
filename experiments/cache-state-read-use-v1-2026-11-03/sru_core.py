"""SRU-01 frozen read-outs (plan §5 with review additions; CONTRACT §5).  Operational labels, not significance tests.
Per direction and ordered pair (gain: receiver L10, donor L11, expected sign +; withdraw: receiver L11, donor L10, expected sign -):
  dM_c = M_c - M_00 (target-not-first 32, scenario-equal), c in 10 (direct read), 01 (correction), 11 (both).
  M directional support: sign * eq >= 0.25 and >= 4/6 scenario means with the expected sign; 'opposite' symmetric.
  Y support (all 48): net = sign * sum(Y_c - Y_00) >= 2 and >= 2 scenarios with an expected-direction change.
  joint(c) = M support and Y support.  Interaction I = z11 - z10 - z01 + z00 (M scenario-equal; Y count).
Labels (first match): opposite (any cell M opposite); direct_dominant (joint 11 and joint 10, |dM11| >= 0.5, dM10/dM11 >= 0.75,
|dM01/dM11| <= 0.25); correction_dominant (symmetric); both_single (joint 10 and joint 01); joint_only (joint 11 only); diag_only (M 11 support,
no Y support); weak.
Bidirectional direct reading: both pairs direct_dominant in a direction; multi-direction: >= 2 of 3 gap directions.
Descriptive: background gap g = M(donor 00) - M(receiver 00); dM11 / g; t2-selection-correct counts (natural t2 token == target's second token)."""
TH = {'abs': 0.25, 'scen': 4, 'y_net': 2, 'y_scen': 2, 'den': 0.5, 'dom': 0.75, 'other': 0.25}
SIGN = {'gain': 1, 'withdraw': -1}
CELLS = ('10', '01', '11')


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def smeans(vals, scen):
    out = {}
    for i, v in vals.items():
        out.setdefault(scen[i], []).append(v)
    return {s: sum(x) / len(x) for s, x in out.items()}


def stable(vals, scen, sign):
    sm = smeans(vals, scen)
    eq = mean(sm.values())
    npos = sum(1 for v in sm.values() if sign * v > 0)
    nneg = sum(1 for v in sm.values() if sign * v < 0)
    lab = 'expected' if (sign * eq >= TH['abs'] and npos >= TH['scen']) else ('opposite' if (-sign * eq >= TH['abs'] and nneg >= TH['scen']) else 'not_stable')
    return {'eq': eq, 'scen': sm, 'label': lab, 'n_expected': npos}


def ysupport(Y0, Y1, scen, sign):
    net = sign * sum(Y1[i] - Y0[i] for i in Y0)
    moved = {scen[i] for i in Y0 if sign * (Y1[i] - Y0[i]) > 0}
    toward = sum(1 for i in Y0 if sign * (Y1[i] - Y0[i]) > 0)
    away = sum(1 for i in Y0 if sign * (Y1[i] - Y0[i]) < 0)
    return {'net': net, 'toward': toward, 'away': away, 'n_scen': len(moved), 'support': net >= TH['y_net'] and len(moved) >= TH['y_scen']}


def pair(M, Y, scen, tnf, pname, Mdonor00=None):
    """M[cell][i], Y[cell][i] for cells 00/10/01/11 of one ordered pair."""
    sign = SIGN[pname]
    ids = sorted(tnf)
    eff = {c: stable({i: M[c][i] - M['00'][i] for i in ids}, scen, sign) for c in CELLS}
    ys = {c: ysupport(Y['00'], Y[c], scen, sign) for c in CELLS}
    joint = {c: eff[c]['label'] == 'expected' and ys[c]['support'] for c in CELLS}
    d11, d10, d01 = eff['11']['eq'], eff['10']['eq'], eff['01']['eq']
    r10 = d10 / d11 if abs(d11) >= TH['den'] else None
    r01 = d01 / d11 if abs(d11) >= TH['den'] else None
    if any(eff[c]['label'] == 'opposite' for c in CELLS):
        lab = 'opposite'
    elif joint['11'] and joint['10'] and r10 is not None and r10 >= TH['dom'] and abs(r01) <= TH['other']:
        lab = 'direct_dominant'
    elif joint['11'] and joint['01'] and r01 is not None and r01 >= TH['dom'] and abs(r10) <= TH['other']:
        lab = 'correction_dominant'
    elif joint['10'] and joint['01']:
        lab = 'both_single'
    elif joint['11']:
        lab = 'joint_only'
    elif eff['11']['label'] == 'expected':
        lab = 'diag_only'
    else:
        lab = 'weak'
    I_M = mean(smeans({i: M['11'][i] - M['10'][i] - M['01'][i] + M['00'][i] for i in ids}, scen).values())
    I_Y = sum(Y['11'][i] - Y['10'][i] - Y['01'][i] + Y['00'][i] for i in Y['00'])
    g = mean(smeans({i: Mdonor00[i] - M['00'][i] for i in ids}, scen).values()) if Mdonor00 is not None else None
    return {'effects': eff, 'y': ys, 'joint': joint, 'r10': r10, 'r01': r01, 'label': lab, 'I_M': I_M, 'I_Y': I_Y, 'g': g,
            'd11_over_g': (d11 / g if g is not None and abs(g) >= TH['den'] else None)}


def direction(pairs):
    return {'bidirectional_direct': pairs['gain']['label'] == 'direct_dominant' and pairs['withdraw']['label'] == 'direct_dominant'}
