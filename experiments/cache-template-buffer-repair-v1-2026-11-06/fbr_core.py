"""FBR-01 frozen read-outs (CONTRACT §5).  Each label is tied to the measurement it is computed from; the sentence it licenses is in the contract.

Per direction, from per-input full-answer correctness Y (1 / 0) of each arm.  Rates are family-equal (mean over families of the within-family
mean); meta[input] = (family, cluster).  Bootstrap: resample clusters within each family with replacement, 10000 draws, seed 20261106.
  Stage A (LVK new panel): one family, cluster = scenario (6).   Stage B (new panel): family = structure family (6), cluster = base situation (4).

  g_X = Y(X) - Y(T)                                   repair gain of arm X over the native intervened run
  UP   Y(F_own) >= 0.75                               the upper bound (own clean buffer) exists on this panel
  PA   Y(F_mean) >= 0.90 Y(F_own) and 95% lower bound of g_mean >= 0.50        answer-blind repair
  PB   at most 1 of the 20 norm-matched random buffer changes has g >= 0.5 g_mean
  PC   g_zero < 0.5 g_mean                            zeroing the buffer does not do it
  PD_s / PD_o   Y(F_one, same family / other family) >= 0.90 Y(F_mean)         one reference input is enough
  PE   Y(V_mean + mu_k) >= 0.75 Y(F_own)              the two-vector version
  PF   g_dmean < 0.5 g_mean                           the average DAMAGED buffer of other inputs does not do it
  DMG  Y(T) <= 0.25                                   there is damage to repair on this panel
Unjudgeable: everything if DMG fails; PA, PE if UP fails; PB, PC, PF if g_mean < 0.25; PD if Y(F_mean) < 0.25.
Outcome: no_damage (DMG fails) / no_upper_bound (UP fails) / repair_beyond_random (PA and PB hold)
         / repair_any_change (PA holds, PB fails or unjudgeable) / input_specific (UP holds, PA fails).
"""
import math
import random

TH = {'dmg': 0.25, 'up': 0.75, 'pa_ratio': 0.90, 'pa_gain': 0.50, 'half': 0.5, 'pb_max': 1, 'min_gain': 0.25, 'pd_ratio': 0.90, 'pe_ratio': 0.75}
RAND = tuple(f'R{j}' for j in range(1, 21))
ARMS = ('T', 'F_own', 'F_mean', 'F_one_s', 'F_one_o', 'VmK', 'F_zero', 'F_dmean') + RAND


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


def fam_eq(vals, meta, pick=None):
    by = {}
    for i, v in vals.items():
        f, c = meta[i]
        by.setdefault(f, {}).setdefault(c, []).append(v)
    out = []
    for f, d in sorted(by.items()):
        xs = [v for c in (pick[f] if pick else sorted(d)) for v in d[c]]
        out.append(sum(xs) / len(xs))
    return sum(out) / len(out)


def rates(Y, meta, pick=None):
    return {a: fam_eq(Y[a], meta, pick) for a in ARMS}


def boot_gain(Y, meta, n=10000, seed=20261106):
    rng = random.Random(seed)
    fam = {}
    for f, c in meta.values():
        fam.setdefault(f, set()).add(c)
    fam = {f: sorted(c) for f, c in fam.items()}
    out = {}
    for arm in ('F_own', 'F_mean'):
        v = []
        r2 = random.Random(seed)
        for _ in range(n):
            pick = {f: [r2.choice(c) for _ in c] for f, c in fam.items()}
            v.append(fam_eq(Y[arm], meta, pick) - fam_eq(Y['T'], meta, pick))
        v.sort()
        out[arm] = {'lo': v[int(0.025 * n)], 'hi': v[int(0.975 * n) - 1]}
    return out


def decide(Y, meta, n_boot=10000):
    y = rates(Y, meta)
    g = {a: y[a] - y['T'] for a in ARMS}
    bt = boot_gain(Y, meta, n=n_boot)
    up = y['F_own'] >= TH['up']
    lab = {'UP': 'holds' if up else 'fails'}
    lab['PA'] = 'unjudgeable' if not up else ('holds' if (y['F_mean'] >= TH['pa_ratio'] * y['F_own'] and bt['F_mean']['lo'] >= TH['pa_gain']) else 'fails')
    big = g['F_mean'] >= TH['min_gain']
    cR = sum(1 for r in RAND if g[r] >= TH['half'] * g['F_mean'])
    lab['PB'] = 'unjudgeable' if not big else ('holds' if cR <= TH['pb_max'] else 'fails')
    lab['PC'] = 'unjudgeable' if not big else ('holds' if g['F_zero'] < TH['half'] * g['F_mean'] else 'fails')
    for k, a in (('PD_s', 'F_one_s'), ('PD_o', 'F_one_o')):
        lab[k] = 'unjudgeable' if y['F_mean'] < TH['min_gain'] else ('holds' if y[a] >= TH['pd_ratio'] * y['F_mean'] else 'fails')
    lab['PE'] = 'unjudgeable' if not up else ('holds' if y['VmK'] >= TH['pe_ratio'] * y['F_own'] else 'fails')
    lab['PF'] = 'unjudgeable' if not big else ('holds' if g['F_dmean'] < TH['half'] * g['F_mean'] else 'fails')
    dmg = y['T'] <= TH['dmg']
    lab['DMG'] = 'holds' if dmg else 'fails'
    if not dmg:
        lab.update({k: 'unjudgeable' for k in ('PA', 'PB', 'PC', 'PD_s', 'PD_o', 'PE', 'PF')})
        outcome = 'no_damage'
    elif not up:
        outcome = 'no_upper_bound'
    elif lab['PA'] == 'holds':
        outcome = 'repair_beyond_random' if lab['PB'] == 'holds' else 'repair_any_change'
    else:
        outcome = 'input_specific'
    return {'outcome': outcome, 'labels': lab, 'Y': y, 'gain': g, 'boot': bt, 'rand_half_count': cR, 'rand_half_upper': cp_upper(cR, len(RAND))}
