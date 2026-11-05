"""NWC-01 frozen read-outs (CONTRACT §5).  Effect-size gates and cluster-bootstrap lower bounds; not a claim of independence beyond the stated unit.

Unit: 24 base situations (4 per structure family), each with 2 code-mapping versions; every input has its target NOT first-listed.
Rates are family-equal: mean over the 6 families of the within-family mean over inputs.
Bootstrap: resample the 4 base situations within each family with replacement (both versions travel together), 10000 draws, seed 20261105,
percentile bounds.

Per direction, from per-input outcomes (Y = full answer correct, E = explicit wrong number) and C-route margins M:
  b = Y(L11) - Y(L00);  l_X = Y(L11) - Y(X);  e_X = E(X) - E(L11);  l_R, e_R = mean over the five natural random arms R1..R5.
  P1/P2 (v8 gates):  point b >= 0.25, l_D >= 0.20, e_D >= 0.15, and the 95% lower bounds of l_D - 0.5 b, l_D - l_E, l_D - l_R, e_D - e_R all > 0.
  P3 (the larger v component is the less effective one):  lower bound of (l_D10 - l_DV) > 0 and |dM(DV)| <= 0.5 |dM(D10)|;
      unjudgeable if the median norm ratio |DV patch| / |D10 patch| < 1, or l_D10 < 0.20, or the receiver is unreachable.
  P4 (efficiency per unit norm):  among K random directions at the D10 patch norm, the fraction whose mean dM <= 0.5 * dM(D10) is <= 0.05;
      unjudgeable if dM(D10) > -0.5.
  P5 (fixed offset):  l_DX >= 0.75 l_D and e_DX >= 0.75 e_D;  unjudgeable if l_D < 0.20, or e_D < 0.15, or the receiver is unreachable.
Labels: 'holds' / 'fails' / 'unjudgeable' for each of P12, P3, P4, P5.  Confirmation of the central sentence = P12 holds in both main directions.
"""
import random

TH = {'b': 0.25, 'l': 0.20, 'e': 0.15, 'unreached': 0.25, 'p3_half': 0.5, 'p4_frac': 0.05, 'p4_half': 0.5, 'p4_min': -0.5, 'p5': 0.75}
RAND = tuple(f'R{j}' for j in range(1, 6))
NAT = ('L00', 'L11', 'D00', 'E00', 'D10', 'DV', 'DX') + RAND


def fam_eq(vals, meta, sits=None):
    """vals: {input: number}; meta: {input: (family, situation)}; sits: optional {family: [situation, ...]} multiset (bootstrap draw)."""
    by = {}
    for i, v in vals.items():
        f, s = meta[i]
        by.setdefault(f, {}).setdefault(s, []).append(v)
    out = []
    for f, d in sorted(by.items()):
        pick = sits[f] if sits else sorted(d)
        xs = [v for s in pick for v in d[s]]
        out.append(sum(xs) / len(xs))
    return sum(out) / len(out)


def quantities(Y, E, meta, sits=None):
    y = {a: fam_eq(Y[a], meta, sits) for a in NAT}
    e = {a: fam_eq(E[a], meta, sits) for a in NAT}
    lR = sum(y['L11'] - y[r] for r in RAND) / len(RAND)
    eR = sum(e[r] - e['L11'] for r in RAND) / len(RAND)
    q = {'b': y['L11'] - y['L00'], 'l_D': y['L11'] - y['D00'], 'l_E': y['L11'] - y['E00'], 'l_R': lR, 'e_D': e['D00'] - e['L11'], 'e_R': eR,
         'l_D10': y['L11'] - y['D10'], 'l_DV': y['L11'] - y['DV'], 'l_DX': y['L11'] - y['DX'], 'e_DX': e['DX'] - e['L11']}
    q.update({'l_D-0.5b': q['l_D'] - 0.5 * q['b'], 'l_D-l_E': q['l_D'] - q['l_E'], 'l_D-l_R': q['l_D'] - q['l_R'], 'e_D-e_R': q['e_D'] - q['e_R'],
              'l_D10-l_DV': q['l_D10'] - q['l_DV']})
    return q


def boot(Y, E, meta, n=10000, seed=20261105):
    rng = random.Random(seed)
    fam = {}
    for f, s in meta.values():
        fam.setdefault(f, set()).add(s)
    fam = {f: sorted(s) for f, s in fam.items()}
    draws = [quantities(Y, E, meta, {f: [rng.choice(s) for _ in s] for f, s in fam.items()}) for _ in range(n)]
    out = {}
    for k in draws[0]:
        v = sorted(d[k] for d in draws)
        out[k] = {'lo': v[int(0.025 * n)], 'hi': v[int(0.975 * n) - 1]}
    return out


def decide(Y, E, meta, dM_D10, dM_DV, dM_rand, norm_ratio_DV, unreached_frac=0.0, n_boot=10000):
    """dM_D10, dM_DV: family-equal mean dM of the D10 / DV arms; dM_rand: K family-equal mean dM of the random directions at the D10 norm."""
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
        p3 = 'holds' if (lo('l_D10-l_DV') > 0 and abs(dM_DV) <= TH['p3_half'] * abs(dM_D10)) else 'fails'
    frac = sum(1 for x in dM_rand if x <= TH['p4_half'] * dM_D10) / len(dM_rand)
    p4 = 'unjudgeable' if dM_D10 > TH['p4_min'] else ('holds' if frac <= TH['p4_frac'] else 'fails')
    p5 = 'unjudgeable' if (q['l_D'] < TH['l'] or q['e_D'] < TH['e'] or unreach) else ('holds' if (q['l_DX'] >= TH['p5'] * q['l_D'] and q['e_DX'] >= TH['p5'] * q['e_D']) else 'fails')
    return {'P12': p12, 'P3': p3, 'P4': p4, 'P5': p5, 'q': q, 'boot': bt, 'p4_fraction': frac, 'dM_D10': dM_D10, 'dM_DV': dM_DV, 'norm_ratio_DV': norm_ratio_DV}
