"""KRD-01 frozen read-outs (plan §6 + CONTRACT §6 additions).  Practical-size screening rules, not significance tests.
Per (direction, ordered pair r<-d, cell c in 10/01/11):
  M (C route, target-not-first subset): g = mean(M_d - M_r); |g| < 0.5 -> 'no_gap' (raw values only).  delta_i = M_c,i - M_r,i.
  'diagnostic transfer': sign(g) * mean(delta) >= max(0.25, 0.25|g|) and >= 4/6 scenario means of delta have the sign of g.
  transfer ratio = mean(delta) / g (unclipped).
  Y (N route, all 48): s = sign(sum(Y_d - Y_r)); s == 0 -> no behaviour gap.  net = s * sum(Y_c - Y_r); 'delivery support' = diagnostic
  transfer and net >= 2.
  Interaction (cells 00/10/01/11): M: |mean(I)| > max(0.25, 0.1|g|); Y: |sum(I)| > 2.
  Specificity (contract addition): common pair vs its random counterpart with the same structure (Rk<-V:Rrk<-V, V<-Rk:V<-Rrk, Ak<-F:Ark<-F,
  F<-Ak:F<-Ark), same cell: 'specific' when the common cell has a diagnostic transfer and sign(g_c) * (mean delta_c - mean delta_rand)
  >= max(0.25, 0.25|g_c|) and >= 4/6 scenarios have sign(g_c) * (scen delta_c - scen delta_rand) > 0; otherwise 'not specific'."""
TH = {'gap': 0.5, 'abs': 0.25, 'rel': 0.25, 'scen': 4, 'y_net': 2, 'int_rel': 0.1, 'y_int': 2, 'p2_ratio': 0.9}
RANDOM_OF = {('Rk', 'V'): ('Rrk', 'V'), ('V', 'Rk'): ('V', 'Rrk'), ('Ak', 'F'): ('Ark', 'F'), ('F', 'Ak'): ('F', 'Ark')}


def sgn(v):
    return (v > 0) - (v < 0)


def smeans(vals, scen):
    out = {}
    for i, v in vals.items():
        out.setdefault(scen[i], []).append(v)
    return {s: sum(x) / len(x) for s, x in out.items()}


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def transfer(Mr, Md, Mc, scen, subset):
    ids = sorted(subset)
    g = mean(Md[i] - Mr[i] for i in ids)
    delta = {i: Mc[i] - Mr[i] for i in ids}
    md = mean(delta.values())
    sm = smeans(delta, scen)
    out = {'g': g, 'mean_delta': md, 'scen_delta': sm, 'n': len(ids)}
    if abs(g) < TH['gap']:
        out.update(label='no_gap', ratio=None, transfer=False)
        return out
    need = max(TH['abs'], TH['rel'] * abs(g))
    n_same = sum(1 for v in sm.values() if sgn(v) == sgn(g))
    ok = sgn(g) * md >= need and n_same >= TH['scen']
    out.update(label='transfer' if ok else 'weak', ratio=md / g, need=need, n_scen_same=n_same, transfer=ok)
    return out


def delivery(Yr, Yd, Yc, tr):
    s = sgn(sum(Yd[i] - Yr[i] for i in Yr))
    if s == 0:
        return {'label': 'no_behaviour_gap', 'net': None, 'support': False, 'gap_count': 0}
    net = s * sum(Yc[i] - Yr[i] for i in Yr)
    toward = sum(1 for i in Yr if s * (Yc[i] - Yr[i]) > 0)
    away = sum(1 for i in Yr if s * (Yc[i] - Yr[i]) < 0)
    gap_count = abs(sum(Yd[i] - Yr[i] for i in Yr))
    sup = bool(tr.get('transfer')) and net >= TH['y_net']
    return {'label': 'support' if sup else 'no_support', 'net': net, 'toward': toward, 'away': away, 'gap_count': gap_count,
            'net_over_gap': net / gap_count if gap_count else None, 'support': sup}


def interaction(y, ids, g=None, binary=False):
    """y[cell][i] for cells 00/10/01/11."""
    I = [y['11'][i] - y['10'][i] - y['01'][i] + y['00'][i] for i in ids]
    if binary:
        tot = sum(I)
        return {'sum': tot, 'practical': abs(tot) > TH['y_int']}
    m = mean(I)
    tol = max(TH['abs'], TH['int_rel'] * abs(g)) if g is not None else TH['abs']
    return {'mean': m, 'tol': tol, 'practical': abs(m) > tol}


def specificity(tr_c, d_c, d_r, scen):
    """tr_c: transfer() of the common cell; d_c / d_r: {input: delta} of the common / random cell (same subset)."""
    if not tr_c.get('transfer'):
        return {'label': 'no_common_transfer', 'specific': False}
    g = tr_c['g']
    ids = sorted(d_c)
    diff = sgn(g) * (mean(d_c[i] for i in ids) - mean(d_r[i] for i in ids))
    sc, sr = smeans(d_c, scen), smeans(d_r, scen)
    n = sum(1 for s in sc if sgn(g) * (sc[s] - sr[s]) > 0)
    need = max(TH['abs'], TH['rel'] * abs(g))
    ok = diff >= need and n >= TH['scen']
    return {'label': 'specific' if ok else 'not_specific', 'diff': diff, 'need': need, 'n_scen': n, 'specific': ok}


def p2(ratio_loss, ratio_gain):
    """Contract P2: both 11-cell transfer ratios < 0.9 (conv residue keeps acting on the loss side, missing on the gain side)."""
    if ratio_loss is None or ratio_gain is None:
        return {'label': 'not_evaluable'}
    ok = ratio_loss < TH['p2_ratio'] and ratio_gain < TH['p2_ratio']
    return {'label': 'holds' if ok else 'fails', 'ratio_loss': ratio_loss, 'ratio_gain': ratio_gain}
