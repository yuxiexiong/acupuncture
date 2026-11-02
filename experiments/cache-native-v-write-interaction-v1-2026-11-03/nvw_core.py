"""NVW-01 frozen read-outs (plan §5-6 with the review amendments; CONTRACT §5).  Operational labels, not significance tests.
Effects per family f, background b, operation op in {W, K}: e = Z(op) - Z(0) per input, scenario-equal mean.  Interaction
I_op(Z) = e(V restored) - e(V not restored) per input.  Expected sign: R +1, A -1, Z -1.
Stable directional: sign * eq >= 0.25 and >= 4/6 scenario means with sign * value > 0 (G on all 48, M on the 32 target-not-first).
Primary readouts: within-background first-step effect -> G; cross-background interaction -> I_W(M).  I(G) descriptive.
Delivery: net = sign * sum(Y(op) - Y(0)) >= 2 and >= 2 scenarios with at least one move in the expected direction -> 'multi-scenario'.
W boundary: K stable directional but W not, per endpoint and background.
Ratios (descriptive, |denominator| >= 0.5): W/K; 'effect relative to whole q/k restoration reference': R on T: e / (Z(Q) - Z(T)); R on V:
e / (Z(F) - Z(V)); A, Z on Q: e / (Z(T) - Z(Q)); on F: e / (Z(V) - Z(F)).  Numerator, denominator and sign always reported.
Multi-direction: >= 2 of the 3 gap directions with the same label."""
TH = {'abs': 0.25, 'scen': 4, 'y_net': 2, 'y_scen': 2, 'den': 0.5}
EXPECT = {'R': 1, 'A': -1, 'Z': -1}
REF = {('R', 0): ('Q', 'T'), ('R', 1): ('F', 'V'), ('A', 0): ('T', 'Q'), ('A', 1): ('V', 'F'), ('Z', 0): ('T', 'Q'), ('Z', 1): ('V', 'F')}


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def smeans(vals, scen):
    out = {}
    for i, v in vals.items():
        out.setdefault(scen[i], []).append(v)
    return {s: sum(x) / len(x) for s, x in out.items()}


def stable(vals, scen, sign):
    """vals: {input: difference}.  Directional label relative to sign."""
    sm = smeans(vals, scen)
    eq = mean(sm.values())
    npos = sum(1 for v in sm.values() if sign * v > 0)
    nneg = sum(1 for v in sm.values() if sign * v < 0)
    lab = 'expected' if (sign * eq >= TH['abs'] and npos >= TH['scen']) else ('opposite' if (-sign * eq >= TH['abs'] and nneg >= TH['scen']) else 'not_stable')
    return {'eq': eq, 'scen': sm, 'label': lab, 'n_scen_expected': npos, 'n_scen_opposite': nneg}


def delivery(Y0, Y1, scen, sign):
    net = sign * sum(Y1[i] - Y0[i] for i in Y0)
    moved = {}
    for i in Y0:
        if sign * (Y1[i] - Y0[i]) > 0:
            moved[scen[i]] = moved.get(scen[i], 0) + 1
    fixed = sum(1 for i in Y0 if Y0[i] == 0 and Y1[i] == 1)
    broken = sum(1 for i in Y0 if Y0[i] == 1 and Y1[i] == 0)
    lab = 'multi_scenario' if (net >= TH['y_net'] and len(moved) >= TH['y_scen']) else 'none'
    return {'net': net, 'fixed': fixed, 'broken': broken, 'n_scen_moved': len(moved), 'label': lab}


def ratio(num, den):
    return num / den if (num is not None and den is not None and abs(den) >= TH['den']) else None


def family(Z, scen, fam, tnf, allids):
    """Z[readout][arm][input]; arms: background names 'T','V','Q','F' and f'{fam}{bg}{op}'.  readouts: 'G', 'M', 'Y'."""
    from_bg = {'R': ('T', 'V'), 'A': ('Q', 'F'), 'Z': ('Q', 'F')}[fam]
    sign = EXPECT[fam]
    ids = {'G': sorted(allids), 'M': sorted(tnf)}
    res = {'backgrounds': from_bg, 'effects': {}, 'interaction': {}, 'delivery': {}, 'ratios': {}, 'W_boundary': {}}
    for v, bg in enumerate(from_bg):
        for op in ('W', 'K'):
            arm = f'{fam}{bg}{op}'
            for r in ('G', 'M'):
                res['effects'][f'{r}|{bg}|{op}'] = stable({i: Z[r][arm][i] - Z[r][bg][i] for i in ids[r]}, scen, sign)
            res['delivery'][f'{bg}|{op}'] = delivery(Z['Y'][bg], Z['Y'][arm], scen, sign)
        for r in ('G', 'M'):
            eW, eK = res['effects'][f'{r}|{bg}|W'], res['effects'][f'{r}|{bg}|K']
            num_bg, den_bg = REF[(fam, v)]
            ref = mean(smeans({i: Z[r][num_bg][i] - Z[r][den_bg][i] for i in ids[r]}, scen).values())
            res['ratios'][f'{r}|{bg}'] = {'W_over_K': ratio(eW['eq'], eK['eq']), 'W': eW['eq'], 'K': eK['eq'], 'ref': ref, 'ref_pair': f'{num_bg}-{den_bg}',
                                         'W_over_ref': ratio(eW['eq'], ref), 'K_over_ref': ratio(eK['eq'], ref)}
            res['W_boundary'][f'{r}|{bg}'] = eK['label'] == 'expected' and eW['label'] != 'expected'
    b0, b1 = from_bg
    for op in ('W', 'K'):
        for r in ('G', 'M'):
            vals = {i: (Z[r][f'{fam}{b1}{op}'][i] - Z[r][b1][i]) - (Z[r][f'{fam}{b0}{op}'][i] - Z[r][b0][i]) for i in ids[r]}
            res['interaction'][f'{r}|{op}'] = stable(vals, scen, sign)
        res['interaction'][f'Y|{op}'] = sign * sum((Z['Y'][f'{fam}{b1}{op}'][i] - Z['Y'][b1][i]) - (Z['Y'][f'{fam}{b0}{op}'][i] - Z['Y'][b0][i]) for i in allids)
    res['labels'] = {'native_first_step_W': res['effects'][f'G|{b0}|W']['label'], 'target_competition_W_unrestored': res['effects'][f'M|{b0}|W']['label'],
                     'target_competition_W_restored': res['effects'][f'M|{b1}|W']['label'], 'interaction_M_W': res['interaction']['M|W']['label'],
                     'delivery_W_unrestored': res['delivery'][f'{b0}|W']['label'], 'delivery_W_restored': res['delivery'][f'{b1}|W']['label']}
    return res


def multi_direction(labels_by_dir, key, value):
    n = sum(1 for lab in labels_by_dir.values() if lab[key] == value)
    return {'n': n, 'multi': n >= 2}
