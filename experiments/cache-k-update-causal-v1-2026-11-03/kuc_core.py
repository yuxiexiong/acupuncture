"""KUC-01 frozen read-outs (plan §5; CONTRACT §5).  Practical-size screening rules, not significance tests.
Per (direction, family F in R/A/Z): cells 00 (background arm: V for R, F for A/Z), 10 (erase term), 01 (write term), 11 (both).
Expected sign: R +1 (raise target margin / delivery), A and Z -1.
M: C-route margin on the 32 target-not-first inputs, scenario-equal mean of per-input differences.
  Directional M support of cell c: sign * eq(Mc - M00) >= 0.25 and >= 4/6 scenario means with sign * value > 0.
  Opposite: -sign * eq >= 0.25 and >= 4/6 scenarios opposite.
Y (all 48, Y_full): net = sign * sum(Yc - Y00); support net >= 2; opposite net <= -2.
Joint support = M support and Y support; M support alone = diagnostic.
g1 = eq(M11 - M00); g_old = eq(M_orig - M00) (orig = Rk / Ak / Ark); per-cell ratios (Mc - M00)/g1 when |g1| >= 0.5; g1/g_old when
|g_old| >= 0.5 (descriptive; the contract only records the non-gating expectation 0 < g1/g_old < 1 in most directions).
Interaction I = z11 - z10 - z01 + z00: M practical when |eq I| > max(0.25, 0.1|g1|); Y practical when |sum I| > 2.
P2 class: sign_inconsistent (any cell opposite on M) > both_single > single_E > single_W > joint_only > diag_only > none.
P1 (gap directions): R11 and A11 both have joint support in every one of the three directions.
Derived (reported only): residue = M_orig_C - M11_C per input (conditional total effect of the retained conv k edit on the t2 output)."""
TH = {'abs': 0.25, 'scen': 4, 'y_net': 2, 'g': 0.5, 'int_rel': 0.1, 'y_int': 2}
EXPECT = {'R': 1, 'A': -1, 'Z': -1}


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def smeans(vals, scen):
    out = {}
    for i, v in vals.items():
        out.setdefault(scen[i], []).append(v)
    return {s: sum(x) / len(x) for s, x in out.items()}


def eqm(vals, scen):
    sm = smeans(vals, scen)
    return mean(sm.values()), sm


def m_effect(Ma, Mb, scen, ids, sign):
    """Effect of b relative to a (Mb - Ma) on ids."""
    eq, sm = eqm({i: Mb[i] - Ma[i] for i in ids}, scen)
    npos = sum(1 for v in sm.values() if sign * v > 0)
    nneg = sum(1 for v in sm.values() if sign * v < 0)
    return {'eq': eq, 'scen': sm, 'support': sign * eq >= TH['abs'] and npos >= TH['scen'],
            'opposite': -sign * eq >= TH['abs'] and nneg >= TH['scen'], 'n_scen_expected': npos}


def y_effect(Ya, Yb, sign):
    net = sign * sum(Yb[i] - Ya[i] for i in Ya)
    fix = sum(1 for i in Ya if Ya[i] == 0 and Yb[i] == 1)
    brk = sum(1 for i in Ya if Ya[i] == 1 and Yb[i] == 0)
    return {'net': net, 'fixed': fix, 'broken': brk, 'support': net >= TH['y_net'], 'opposite': net <= -TH['y_net']}


def family(M, Y, scen, tnf, sign):
    """M[cell][i], Y[cell][i] for cells 00/10/01/11/orig."""
    ids = sorted(tnf)
    eff = {c: m_effect(M['00'], M[c], scen, ids, sign) for c in ('10', '01', '11', 'orig')}
    yef = {c: y_effect(Y['00'], Y[c], sign) for c in ('10', '01', '11', 'orig')}
    cond = {'E_given_W1': m_effect(M['01'], M['11'], scen, ids, sign), 'W_given_E1': m_effect(M['10'], M['11'], scen, ids, sign),
            'E_given_W1_Y': y_effect(Y['01'], Y['11'], sign), 'W_given_E1_Y': y_effect(Y['10'], Y['11'], sign)}
    g1, g_old = eff['11']['eq'], eff['orig']['eq']
    ratios = {c: (eff[c]['eq'] / g1 if abs(g1) >= TH['g'] else None) for c in ('10', '01')}
    I_M, _ = eqm({i: M['11'][i] - M['10'][i] - M['01'][i] + M['00'][i] for i in ids}, scen)
    I_Y = sum(Y['11'][i] - Y['10'][i] - Y['01'][i] + Y['00'][i] for i in Y['00'])
    tol = max(TH['abs'], TH['int_rel'] * abs(g1))
    joint = {c: eff[c]['support'] and yef[c]['support'] for c in ('10', '01', '11')}
    if any(eff[c]['opposite'] for c in ('10', '01', '11')):
        lab = 'sign_inconsistent'
    elif joint['10'] and joint['01']:
        lab = 'both_single'
    elif joint['10']:
        lab = 'single_E'
    elif joint['01']:
        lab = 'single_W'
    elif joint['11']:
        lab = 'joint_only'
    elif eff['11']['support']:
        lab = 'diag_only'
    else:
        lab = 'none'
    res_all = {i: M['orig'][i] - M['11'][i] for i in M['00']}
    res_eq, res_sm = eqm({i: res_all[i] for i in ids}, scen)
    return {'effects': eff, 'y': yef, 'conditional': cond, 'g1': g1, 'g_old': g_old, 'g1_over_g_old': (g1 / g_old if abs(g_old) >= TH['g'] else None),
            'cell_ratios': ratios, 'interaction': {'M': I_M, 'M_tol': tol, 'M_practical': abs(I_M) > tol, 'Y': I_Y, 'Y_practical': abs(I_Y) > TH['y_int']},
            'joint': joint, 'label': lab,
            'residue': {'M_tnf_eq': res_eq, 'M_tnf_scen': res_sm, 'M_all48_mean': mean(res_all.values()),
                        'Y_orig_minus_11': sum(Y['orig'][i] - Y['11'][i] for i in Y['00'])}}


def p1(fams):
    """fams[direction][family] = family() output for the three gap directions."""
    per = {d: bool(f['R']['joint']['11'] and f['A']['joint']['11']) for d, f in fams.items()}
    return {'per_direction': per, 'label': 'holds' if all(per.values()) else ('partial' if any(per.values()) else 'fails'), 'n': sum(per.values())}
