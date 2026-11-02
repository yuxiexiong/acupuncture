"""QKF-01 frozen rules (plan §5-6).  E_s = mean over the 6 scenarios of per-scenario means.
G = E_s[Y_F - Y_V] (applicable iff G > 0 and >= 4 scenarios with a positive gap); D_i = 1[Y_F = 1 and Y_V = 0].
P(u,h) = E_s[Y_R(u,h) - Y_V] / G;  B(u,h) = E_s[D_i * 1(ids_A(u,h) = ids_V)] / E_s[D_i].
Single half (mu): removal ok iff P >= 0.5 and >= 4 scenarios with mean(Y_R - Y_V) > 0; addition ok iff B >= 0.5 and >= 4 scenarios
with at least one exact reproduction.  Advantage over a random tier: P_mu - P_tier >= 0.25 (and B likewise), only if that tier's
edit-matching checks passed for every input.  k-vs-q prediction: P_k - P_q >= 0.25 and B_k - B_q >= 0.25, recovery difference > 0
in >= 4/6 scenarios, reproduction difference > 0 in >= ceil(2/3) of the scenarios that have D (reverse -> q stronger; one side only
-> asymmetric).  Four-cell interactions I_Y^R = E_s[Y_Rqk - Y_Rq - Y_Rk + Y_V], I_Y^A likewise with A and F, I_B = B_qk - B_q - B_k + B_00,
I_M on the fixed-competitor margin; 'visible non-additivity on that metric' iff |I| >= 0.10 and >= 4 scenarios share its sign."""
import math

TH = {'P_min': 0.5, 'B_min': 0.5, 'adv': 0.25, 'scen_min': 4, 'kq': 0.25, 'I_min': 0.10, 'I_scen': 4}


def smeans(vals, scen):
    out = {}
    for i, v in vals.items():
        out.setdefault(scen[i], []).append(v)
    return {s: sum(x) / len(x) for s, x in out.items()}


def eq(vals, scen):
    m = smeans(vals, scen)
    return sum(m.values()) / len(m)


def quantities(Y, match, scen):
    """Y: arm -> {i: 0/1}; match: arm -> {i: bool ids == ids_V}.  Returns G, D, P, B per edited arm and scenario summaries."""
    ids = list(Y['V'])
    gap = smeans({i: Y['F'][i] - Y['V'][i] for i in ids}, scen)
    G = sum(gap.values()) / len(gap)
    D = {i: int(Y['F'][i] == 1 and Y['V'][i] == 0) for i in ids}
    eD = eq(D, scen)
    q = {'G': G, 'n_pos_gap': sum(v > 0 for v in gap.values()), 'applicable': G > 0 and sum(v > 0 for v in gap.values()) >= TH['scen_min'],
         'n_D': sum(D.values()), 'P': {}, 'B': {}, 'scen_R_pos': {}, 'scen_repro': {}, 'D': D}
    for arm in Y:
        if arm.startswith('R_'):
            q['P'][arm] = eq({i: Y[arm][i] - Y['V'][i] for i in ids}, scen) / G if G > 0 else None
            q['scen_R_pos'][arm] = sum(v > 0 for v in smeans({i: Y[arm][i] - Y['V'][i] for i in ids}, scen).values())
        if arm.startswith('A_') or arm == 'F':
            q['B'][arm] = eq({i: D[i] * int(match[arm][i]) for i in ids}, scen) / eD if eD > 0 else None
            q['scen_repro'][arm] = sum(v > 0 for v in smeans({i: D[i] * int(match[arm][i]) for i in ids}, scen).values())
    return q


def single(q, h):
    P, B = q['P'][f'R_mu_{h}'], q['B'][f'A_mu_{h}']
    r_ok = P is not None and P >= TH['P_min'] and q['scen_R_pos'][f'R_mu_{h}'] >= TH['scen_min']
    a_ok = B is not None and B >= TH['B_min'] and q['scen_repro'][f'A_mu_{h}'] >= TH['scen_min']
    return {'R_ok': r_ok, 'A_ok': a_ok, 'P': P, 'B': B}


def advantage(q, h, tier, match_ok):
    """match_ok: {'R': bool, 'A': bool} for this tier/mask across all inputs."""
    out = {}
    pm, pt = q['P'][f'R_mu_{h}'], q['P'][f'R_{tier}_{h}']
    bm, bt = q['B'][f'A_mu_{h}'], q['B'][f'A_{tier}_{h}']
    out['R'] = 'engineering_not_judgeable' if not match_ok['R'] else (None if pm is None else pm - pt >= TH['adv'])
    out['A'] = 'engineering_not_judgeable' if not match_ok['A'] else (None if bm is None else bm - bt >= TH['adv'])
    out['dP'] = None if pm is None else pm - pt
    out['dB'] = None if bm is None else bm - bt
    return out


def k_vs_q(Y, match, q, scen):
    ids = list(Y['V'])
    D = q['D']
    if q['P']['R_mu_k'] is None or q['B']['A_mu_k'] is None:
        return {'verdict': 'not_applicable'}
    dP = q['P']['R_mu_k'] - q['P']['R_mu_q']
    dB = q['B']['A_mu_k'] - q['B']['A_mu_q']
    rec = smeans({i: Y['R_mu_k'][i] - Y['R_mu_q'][i] for i in ids}, scen)
    rep = smeans({i: D[i] * (int(match['A_mu_k'][i]) - int(match['A_mu_q'][i])) for i in ids}, scen)
    withD = [s for s, v in smeans(D, scen).items() if v > 0]
    need = math.ceil(2 * len(withD) / 3)

    def side(sign):
        r = sign * dP >= TH['kq'] and sum(sign * v > 0 for v in rec.values()) >= TH['scen_min']
        b = sign * dB >= TH['kq'] and sum(sign * rep[s] > 0 for s in withD) >= need
        return r, b
    kr, kb = side(1)
    qr, qb = side(-1)
    if kr and kb:
        v = 'k_stronger'
    elif qr and qb:
        v = 'q_stronger'
    elif kr or kb or qr or qb:
        v = 'asymmetric'
    else:
        v = 'no_order'
    return {'verdict': v, 'dP': dP, 'dB': dB, 'k_side': [kr, kb], 'q_side': [qr, qb], 'n_scen_with_D': len(withD)}


def interaction(cells, base, scen):
    """cells: {'q','k','qk'} -> {i: value}; base: {i: value}.  I = E_s[qk - q - k + base]; visible iff |I| >= 0.10, >= 4 same-sign scenarios."""
    ids = list(base)
    per = smeans({i: cells['qk'][i] - cells['q'][i] - cells['k'][i] + base[i] for i in ids}, scen)
    I = sum(per.values()) / len(per)
    same = sum((v > 0) if I > 0 else (v < 0) for v in per.values()) if I != 0 else 0
    return {'I': I, 'by_scenario': per, 'visible': abs(I) >= TH['I_min'] and same >= TH['I_scen']}
