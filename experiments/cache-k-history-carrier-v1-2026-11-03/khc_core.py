"""KHC-01 frozen read-outs (plan §5-6; CONTRACT §5).  Practical-size screening rules, not significance tests.
Per (direction, ordered pair), donor Q fixed in every cell; cells 00 (S=r, KV=r), 10 (S=d), 01 (KV=d), 11 (S=d, KV=d).
M on the 32 target-not-first inputs: h = mean(M11 - M00); |h| < 0.5 -> 'small_h' (raw effects only).  pS = mean(M10 - M00) / h,
pKV = mean(M01 - M00) / h (unclipped).  Diagnostic effect of cell c (toward 11): sign(h) * mean(Mc - M00) >= max(0.25, 0.25|h|) and >= 4/6
scenario means with the sign of h.  Y on all 48: direction s = sign(sum(Y11 - Y00)); support of c: s != 0 and s * sum(Yc - Y00) >= 2.
Class (first match): small_h; overshoot_or_sign (any of pS, pKV > 1.25 or < -0.25); S (pS >= 0.75, |pKV| <= 0.25, S diag + Y support);
KV (symmetric); both (pS, pKV >= 0.75, each diag + Y support); joint_only (neither single diag, joint diag + Y support); else mixed.
If the Y end-point gap (Y11 vs Y00) is zero, Y support is replaced by the diagnostic rule and the class gets the suffix '_diag_only'.
Interaction I = z11 - z10 - z01 + z00: M practical if |mean I| > max(0.25, 0.1|h|); Y practical if |sum I| > 2.
P1: per gap direction, at least 3 of the 4 common pairs (Rk<-V, V<-Rk, Ak<-F, F<-Ak) are class 'S'; fewer than 3 judgeable (not small_h)
-> not_evaluable.  Hand-over: an unordered pair whose two directions share class S or KV records that preferred carrier."""
TH = {'h': 0.5, 'abs': 0.25, 'rel': 0.25, 'scen': 4, 'y_net': 2, 'int_rel': 0.1, 'y_int': 2, 'single': 0.75, 'other': 0.25,
      'over_hi': 1.25, 'over_lo': -0.25, 'p1': 3}
COMMON = ('Rk<-V', 'V<-Rk', 'Ak<-F', 'F<-Ak')


def sgn(v):
    return (v > 0) - (v < 0)


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def smeans(vals, scen):
    out = {}
    for i, v in vals.items():
        out.setdefault(scen[i], []).append(v)
    return {s: sum(x) / len(x) for s, x in out.items()}


def effect(M00, Mc, h, scen, ids):
    delta = {i: Mc[i] - M00[i] for i in ids}
    md = mean(delta.values())
    sm = smeans(delta, scen)
    need = max(TH['abs'], TH['rel'] * abs(h))
    n_same = sum(1 for v in sm.values() if sgn(v) == sgn(h) and sgn(h) != 0)
    return {'mean': md, 'scen': sm, 'need': need, 'n_scen_same': n_same, 'ok': sgn(h) * md >= need and n_same >= TH['scen']}


def yeffect(Y00, Y11, Yc):
    s = sgn(sum(Y11[i] - Y00[i] for i in Y00))
    if s == 0:
        return {'gap0': True, 'net': None, 'support': False, 'toward': None, 'away': None}
    net = s * sum(Yc[i] - Y00[i] for i in Y00)
    return {'gap0': False, 'net': net, 'support': net >= TH['y_net'], 'gap': abs(sum(Y11[i] - Y00[i] for i in Y00)),
            'toward': sum(1 for i in Y00 if s * (Yc[i] - Y00[i]) > 0), 'away': sum(1 for i in Y00 if s * (Yc[i] - Y00[i]) < 0)}


def classify(M, Y, scen, tnf):
    """M[cell][i], Y[cell][i] for cells 00/10/01/11 (M over all inputs; tnf = target-not-first subset)."""
    ids = sorted(tnf)
    h = mean(M['11'][i] - M['00'][i] for i in ids)
    res = {'h': h}
    I_M = mean(M['11'][i] - M['10'][i] - M['01'][i] + M['00'][i] for i in ids)
    I_Y = sum(Y['11'][i] - Y['10'][i] - Y['01'][i] + Y['00'][i] for i in Y['00'])
    res['interaction'] = {'M_mean': I_M, 'M_tol': max(TH['abs'], TH['int_rel'] * abs(h)), 'M_practical': abs(I_M) > max(TH['abs'], TH['int_rel'] * abs(h)),
                          'Y_sum': I_Y, 'Y_practical': abs(I_Y) > TH['y_int']}
    e = {c: effect(M['00'], M[c], h, scen, ids) for c in ('10', '01', '11')}
    y = {c: yeffect(Y['00'], Y['11'], Y[c]) for c in ('10', '01', '11')}
    res.update(effects=e, y=y)
    if abs(h) < TH['h']:
        res.update(label='small_h', pS=None, pKV=None)
        return res
    pS, pKV = e['10']['mean'] / h, e['01']['mean'] / h
    res.update(pS=pS, pKV=pKV)
    gap0 = y['11']['gap0']
    sup = (lambda c: e[c]['ok']) if gap0 else (lambda c: e[c]['ok'] and y[c]['support'])
    if any(p > TH['over_hi'] or p < TH['over_lo'] for p in (pS, pKV)):
        lab = 'overshoot_or_sign'
    elif pS >= TH['single'] and abs(pKV) <= TH['other'] and sup('10'):
        lab = 'S'
    elif pKV >= TH['single'] and abs(pS) <= TH['other'] and sup('01'):
        lab = 'KV'
    elif pS >= TH['single'] and pKV >= TH['single'] and sup('10') and sup('01'):
        lab = 'both'
    elif not e['10']['ok'] and not e['01']['ok'] and sup('11'):
        lab = 'joint_only'
    else:
        lab = 'mixed'
    if gap0 and lab in ('S', 'KV', 'both', 'joint_only'):
        lab += '_diag_only'
    res['label'] = lab
    return res


def p1(labels):
    """labels: {pair: class} for the 4 common pairs of one gap direction."""
    judge = [p for p in COMMON if labels[p] != 'small_h']
    nS = sum(1 for p in COMMON if labels[p] == 'S')
    if len(judge) < TH['p1']:
        return {'label': 'not_evaluable', 'n_S': nS, 'n_judgeable': len(judge)}
    return {'label': 'holds' if nS >= TH['p1'] else 'fails', 'n_S': nS, 'n_judgeable': len(judge)}


def handover(labels):
    out = {}
    for a, b in (('Rk<-V', 'V<-Rk'), ('Ak<-F', 'F<-Ak'), ('Ark<-F', 'F<-Ark')):
        la, lb = labels[a], labels[b]
        out[f'{a}|{b}'] = la if (la == lb and la in ('S', 'KV')) else 'joint_or_asymmetric'
    return out
