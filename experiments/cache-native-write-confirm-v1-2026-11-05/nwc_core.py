"""NWC-01 r03 frozen read-outs (CONTRACT §5).  Each label is tied to the measurement it is computed from; the sentence a label licenses is in
the contract, not here.

Unit: 24 base situations (4 per structure family).  Stratum N: versions a, b (target second / third listed) -> 48 inputs, all gates except P6.
Stratum F: version c (target first-listed) -> 24 inputs, P6 only.  Rates are family-equal (mean over the 6 families of the within-family mean).
Bootstrap: resample the 4 base situations within each family with replacement (all versions travel together), 10000 draws, seed 20261105.

  b = Y(L11) - Y(L00);  l_X = Y(L11) - Y(X);  e_X = E(X) - E(L11);  l_R, e_R = mean over the ten natural random arms R1..R10 (D00 patch norm,
  directions drawn fresh for this panel; the five NWR-01 directions are not used in any gate).
  P12  point b >= 0.25, l_D >= 0.20, e_D >= 0.15, and 95% lower bounds of l_D - 0.5 b, l_D - l_E, l_D - l_R, e_D - e_R all > 0.
  P3   lower bound of (l_D10 - l_DV) > 0 and |dM(DV)| <= 0.5 |dM(D10)|.   (DV = endpoint state difference L00 - L10 read through D.)
  P4M  count of the 40 random directions at the D10 patch norm whose family-equal mean dM <= 0.5 dM(D10) is <= 2.
  P4Y  count of the 20 natural random directions at the D10 patch norm whose l >= 0.5 l_D10 is <= 1.
  P5   rho = dM(DX) / dM(D00) in [0.75, 1.25] and |l_DXh - l_D00h| <= 0.15 (half amplitude).
  P6   stratum F: Y_F(L11) - Y_F(D00) <= 0.10.
Unjudgeable: see decide().  Every count is reported with a two-sided 95% Clopper-Pearson upper bound for the population fraction.
"""
import math
import random

TH = {'b': 0.25, 'l': 0.20, 'e': 0.15, 'unreached': 0.25, 'half': 0.5, 'p4m_max': 2, 'p4y_max': 1, 'dM_min': -0.5,
      'rho_lo': 0.75, 'rho_hi': 1.25, 'p5_y': 0.15, 'p6': 0.10, 'p6_base': 0.75}
RAND = tuple(f'R{j}' for j in range(1, 11))
QNAT = tuple(f'Q{j}' for j in range(1, 21))
NAT_N = ('L00', 'L11', 'D00', 'E00', 'D10', 'DV', 'DX', 'D00h', 'DXh') + RAND + QNAT
NAT_F = ('L11', 'D00')


def cp_upper(k, n, alpha=0.05):
    """Two-sided (1 - alpha) Clopper-Pearson upper bound for a binomial proportion."""
    if k >= n:
        return 1.0
    cdf = lambda p: sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))   # noqa: E731
    lo, hi = k / n, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if cdf(mid) > alpha / 2 else (lo, mid)
    return hi


def fam_eq(vals, meta, stratum, sits=None):
    """vals: {input: number}; meta: {input: (family, situation, stratum)}; sits: optional {family: [situation, ...]} (bootstrap multiset)."""
    by = {}
    for i, v in vals.items():
        f, s, st = meta[i]
        if st == stratum:
            by.setdefault(f, {}).setdefault(s, []).append(v)
    out = []
    for f, d in sorted(by.items()):
        xs = [v for s in (sits[f] if sits else sorted(d)) for v in d[s]]
        out.append(sum(xs) / len(xs))
    return sum(out) / len(out)


def quantities(Y, E, meta, sits=None):
    y = {a: fam_eq(Y[a], meta, 'N', sits) for a in NAT_N}
    e = {a: fam_eq(E[a], meta, 'N', sits) for a in ('L11', 'D00') + RAND}
    lR = sum(y['L11'] - y[r] for r in RAND) / len(RAND)
    eR = sum(e[r] - e['L11'] for r in RAND) / len(RAND)
    q = {'b': y['L11'] - y['L00'], 'l_D': y['L11'] - y['D00'], 'l_E': y['L11'] - y['E00'], 'l_R': lR, 'e_D': e['D00'] - e['L11'], 'e_R': eR,
         'l_D10': y['L11'] - y['D10'], 'l_DV': y['L11'] - y['DV'], 'l_DX': y['L11'] - y['DX'], 'l_D00h': y['L11'] - y['D00h'], 'l_DXh': y['L11'] - y['DXh'],
         'l_Q': [y['L11'] - y[a] for a in QNAT], 'l_Rj': [y['L11'] - y[r] for r in RAND],
         'YF_L11': fam_eq(Y['L11'], meta, 'F', sits), 'YF_D00': fam_eq(Y['D00'], meta, 'F', sits)}
    q.update({'l_D-0.5b': q['l_D'] - 0.5 * q['b'], 'l_D-l_E': q['l_D'] - q['l_E'], 'l_D-l_R': q['l_D'] - q['l_R'], 'e_D-e_R': q['e_D'] - q['e_R'],
              'l_D10-l_DV': q['l_D10'] - q['l_DV'], 'lF_D': q['YF_L11'] - q['YF_D00']})
    return q


BOOT_KEYS = ('b', 'l_D', 'e_D', 'l_D-0.5b', 'l_D-l_E', 'l_D-l_R', 'e_D-e_R', 'l_D10-l_DV', 'lF_D')


def boot(Y, E, meta, n=10000, seed=20261105):
    rng = random.Random(seed)
    fam = {}
    for f, s, _ in meta.values():
        fam.setdefault(f, set()).add(s)
    fam = {f: sorted(s) for f, s in fam.items()}
    draws = [quantities(Y, E, meta, {f: [rng.choice(s) for _ in s] for f, s in fam.items()}) for _ in range(n)]
    out = {}
    for k in BOOT_KEYS:
        v = sorted(d[k] for d in draws)
        out[k] = {'lo': v[int(0.025 * n)], 'hi': v[int(0.975 * n) - 1]}
    return out


def decide(Y, E, meta, dM, dM_rand, norm_ratio_DV, unreached_frac=0.0, n_boot=10000):
    """dM: family-equal mean dM (stratum N) of arms D00, D10, DV, DX; dM_rand: the 40 family-equal mean dM at the D10 patch norm."""
    q, bt = quantities(Y, E, meta), boot(Y, E, meta, n=n_boot)
    lo = lambda k: bt[k]['lo']   # noqa: E731
    unreach = unreached_frac >= TH['unreached']
    if q['b'] < TH['b'] or unreach:
        p12 = 'unjudgeable'
    else:
        p12 = 'holds' if (q['l_D'] >= TH['l'] and q['e_D'] >= TH['e'] and all(lo(k) > 0 for k in ('l_D-0.5b', 'l_D-l_E', 'l_D-l_R', 'e_D-e_R'))) else 'fails'
    if norm_ratio_DV < 1 or q['l_D10'] < TH['l'] or unreach:
        p3 = 'unjudgeable'
    else:
        p3 = 'holds' if (lo('l_D10-l_DV') > 0 and abs(dM['DV']) <= TH['half'] * abs(dM['D10'])) else 'fails'
    cM = sum(1 for x in dM_rand if x <= TH['half'] * dM['D10'])
    p4m = 'unjudgeable' if dM['D10'] > TH['dM_min'] else ('holds' if cM <= TH['p4m_max'] else 'fails')
    cY = sum(1 for x in q['l_Q'] if x >= TH['half'] * q['l_D10'])
    p4y = 'unjudgeable' if (q['l_D10'] < TH['l'] or unreach) else ('holds' if cY <= TH['p4y_max'] else 'fails')
    if dM['D00'] > TH['dM_min'] or unreach:
        p5, rho = 'unjudgeable', None
    else:
        rho = dM['DX'] / dM['D00']
        p5 = 'holds' if (TH['rho_lo'] <= rho <= TH['rho_hi'] and abs(q['l_DXh'] - q['l_D00h']) <= TH['p5_y']) else 'fails'
    p6 = 'unjudgeable' if (q['YF_L11'] < TH['p6_base'] or unreach) else ('holds' if q['lF_D'] <= TH['p6'] else 'fails')
    cR = sum(1 for x in q['l_Rj'] if x >= TH['half'] * q['l_D'])                 # descriptive: fresh random arms reaching half of the main loss
    return {'P12': p12, 'P3': p3, 'P4M': p4m, 'P4Y': p4y, 'P5': p5, 'P6': p6, 'q': q, 'boot': bt, 'dM': dM, 'rho': rho,
            'r_half_count': cR, 'r_half_upper': cp_upper(cR, len(q['l_Rj'])),
            'p4m_count': cM, 'p4m_upper': cp_upper(cM, len(dM_rand)), 'p4y_count': cY, 'p4y_upper': cp_upper(cY, len(q['l_Q'])),
            'norm_ratio_DV': norm_ratio_DV}
