"""FXS-01 frozen reading rules (plan §3).  Pure functions on the selected first-step values of each arm.

m_G = z_G(q0) - z_G(s0);  delta_G = m_G - m_nat.
J_FIX = delta_V - delta_FIX - delta_REST;  J_U = delta_V - delta_U - delta_Ubar.
tau = max(0.5, 0.1 |delta_V|);  |delta_V| < 1 -> 'insufficient';  |J| <= tau 'additive', J > tau 'super', J < -tau 'sub'.
Precision: each raw logit carries half the gap between adjacent representable numbers; the bound on J (or delta_V) is the sum
over its terms.  An input is precision-sensitive if any corner (J +- e_J, delta_V +- e_V) changes its label.
Scenario label: both facts share a label, else 'mixed'.  Direction label: a label held by >= 5/6 scenarios, else 'mixed'.
Worst-case summary: precision-sensitive inputs count as unresolved ('sensitive'), which can never match a label.
"""
RULE = {'tau_abs': 0.5, 'tau_rel': 0.1, 'min_dv': 1.0, 'scen_count': 5}
LABELS = ('additive', 'super', 'sub', 'insufficient')
PARTS = {'FIX': ('T_FIXV', 'T_RESTV'), 'U': ('T_U', 'T_Ubar')}


def label(J, dV):
    if abs(dV) < RULE['min_dv']:
        return 'insufficient'
    tau = max(RULE['tau_abs'], RULE['tau_rel'] * abs(dV))
    if abs(J) <= tau:
        return 'additive'
    return 'super' if J > tau else 'sub'


def m(r):
    return r['q0'] - r['s0']


def half(r):
    return 0.5 * (r['spacing']['q0'] + r['spacing']['s0'])


def input_reading(sc):
    """sc: arm name -> selected values for one input and one direction (T_nat, T_V, T_FIXV, T_RESTV, T_U, T_Ubar)."""
    mn = m(sc['T_nat'])
    delta = {a: m(sc[a]) - mn for a in sc if a != 'T_nat'}
    dV = delta['T_V']
    eV = half(sc['T_V']) + half(sc['T_nat'])
    out = {'m_nat': mn, 'delta': delta}
    for key, (a, b) in PARTS.items():
        J = dV - delta[a] - delta[b]
        eJ = half(sc['T_V']) + half(sc['T_nat']) + half(sc[a]) + half(sc['T_nat']) + half(sc[b]) + half(sc['T_nat'])
        lab = label(J, dV)
        corners = {label(J + sj * eJ, dV + sv * eV) for sj in (-1, 1) for sv in (-1, 1)}
        out[key] = {'J': J, 'err': eJ, 'label': lab, 'sensitive': len(corners | {lab}) > 1,
                    'share': ({a: delta[a] / dV, b: delta[b] / dV} if abs(dV) >= RULE['min_dv'] else None)}
    out['J_FIX_minus_J_U'] = out['FIX']['J'] - out['U']['J']
    out['dV_err'] = eV
    return out


def scenario_pairs(values):
    o = {}
    for iid, v in values.items():
        s, f = iid.rsplit('-', 1)
        o.setdefault(s, {})[f] = v
    return {s: (d['f0'], d['f1']) for s, d in sorted(o.items())}


def scenario_labels(input_labels):
    return {s: (a if a == b else 'mixed') for s, (a, b) in scenario_pairs(input_labels).items()}


def direction_label(scen):
    for lab in LABELS:
        if sum(v == lab for v in scen.values()) >= RULE['scen_count']:
            return lab
    return 'mixed'


def summarise(readings, key):
    """readings: input id -> input_reading(...) for one direction.  Returns original and worst-case labels."""
    orig = {i: r[key]['label'] for i, r in readings.items()}
    worst = {i: ('sensitive' if r[key]['sensitive'] else r[key]['label']) for i, r in readings.items()}
    so, sw = scenario_labels(orig), scenario_labels(worst)
    return {'inputs': orig, 'scenarios': so, 'direction': direction_label(so),
            'worst_inputs': worst, 'worst_scenarios': sw, 'worst_direction': direction_label(sw),
            'n_sensitive': sum(r[key]['sensitive'] for r in readings.values())}


def k_of_4(per_direction):
    return {lab: sum(v == lab for v in per_direction.values()) for lab in LABELS + ('mixed',)}


def threshold_compatible(reading, sc, q0):
    """Plan §3: 'compatible with a first-step threshold reading' only if the FIX/REST split is additive AND the union (T_V)
    selects q0 at step 1 while neither part does.  Otherwise not compatible (never 'caused by a threshold')."""
    return (reading['FIX']['label'] == 'additive' and sc['T_V']['argmax'] == q0
            and sc['T_FIXV']['argmax'] != q0 and sc['T_RESTV']['argmax'] != q0)
