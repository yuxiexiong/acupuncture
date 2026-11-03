"""NCC-01 core (CPU-testable): cache-group replacement at tau, first-step read-outs, first-token category and aggregation
(plan docs/cache-native-carrier-comparison-v1-2026-11-03/PLAN.zh-CN.md; CONTRACT r01).

Groups (deep layers only; shallow 0-12 and everything else from the receiver T):
  V : conv_states V channels [V_LO:] of the 14 G layers (all stored slots = the finite conv window)
  S : recurrent_states of the 14 G layers
  K : keys / values of the deep full-attention layers (15, 19, 23, 27, 31)
  J : all deep caches = full conv_states (q/k/V) + S of the G layers + K   (contract §0: TJ includes deep conv q/k history)
Read-outs at the first answer token: B = z[f] - max_{j != f} z[j] (full vocabulary), z[f], best stop logit, best non-stop competitor
(j != f, j not a stop id), winner, first == f, first-step stop.  Category: code (first == f), stop, preamble (non-stop, != f, the natural
output later contains a listed code), other.  Aggregation: per input, six scenarios equally weighted; one shared set of bootstrap index
lists (2000, seed 20261103) for every arm and needle."""
import random

GROUPS = ('V', 'S', 'K', 'J')
BOOT_N = 2000
SEED = 20261103


def targets(group, G, KL, v_lo):
    """[(layer, field, channel_slice or None)] replaced by the group."""
    if group == 'V':
        return [(l, 'conv_states', ('from', v_lo)) for l in G]
    if group == 'S':
        return [(l, 'recurrent_states', None) for l in G]
    if group == 'K':
        return [(l, f, None) for l in KL for f in ('keys', 'values')]
    if group == 'J':
        return [(l, 'conv_states', None) for l in G] + [(l, 'recurrent_states', None) for l in G] + [(l, f, None) for l in KL for f in ('keys', 'values')]
    raise ValueError(group)


def replace(receiver, donor, tg, get, set_, deepcopy):
    """Deep copy of receiver with the targets taken from donor (clones; donor and receiver untouched)."""
    X = deepcopy(receiver)
    for l, f, sl in tg:
        a, b = get(X.layers[l], f), get(donor.layers[l], f)
        assert a.shape == b.shape and a.dtype == b.dtype, ('shape/dtype', l, f, tuple(a.shape), tuple(b.shape))
        if sl is None:
            set_(X.layers[l], f, b.clone())
        else:
            new = a.clone()
            new[:, sl[1]:] = b[:, sl[1]:]
            set_(X.layers[l], f, new)
    return X


def first_step(z, f, stop_ids):
    """First-step read-outs from float logits z (1-D tensor)."""
    import torch
    zf = float(z[f])
    others = z.clone()
    others[f] = -float('inf')
    best_other = float(others.max())
    stop = torch.tensor(sorted(stop_ids), device=z.device)
    best_stop = float(z[stop].max())
    ns = others.clone()
    ns[stop] = -float('inf')
    win = int(z.argmax())
    return {'B': zf - best_other, 'z_f': zf, 'best_stop': best_stop, 'best_nonstop_comp': float(ns.max()), 'winner': win,
            'first_is_f': win == f, 'first_stop': win in stop_ids}


def category(first_is_f, first_stop, text, codes):
    if first_stop:
        return 'stop'
    if first_is_f:
        return 'code'
    return 'preamble' if any(c in text for c in codes) else 'other'


# ---------------------------------------------------------------- aggregation

def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def seq(vals, scen, ids):
    by = {}
    for i in ids:
        by.setdefault(scen[i], []).append(vals[i])
    return mean(mean(v) for _s, v in sorted(by.items()))


def boot_draws(ids, scen, n=BOOT_N, seed=SEED):
    by = {}
    for i in sorted(ids):
        by.setdefault(scen[i], []).append(i)
    rng = random.Random(seed)
    return [[rng.choice(v) for _s, v in sorted(by.items()) for _ in v] for _ in range(n)]


def describe(vals, scen, ids, draws):
    xs = sorted(seq(vals, scen, dr) for dr in draws)
    n = len(xs)
    sm = {}
    for i in ids:
        sm.setdefault(scen[i], []).append(vals[i])
    sm = {s: mean(v) for s, v in sorted(sm.items())}
    return {'eq': seq(vals, scen, ids), 'interval': [xs[int(0.025 * n)], xs[int(0.975 * n) - 1]], 'scen': sm,
            'scen_pos': sum(v > 0 for v in sm.values()), 'scen_neg': sum(v < 0 for v in sm.values())}


def y_changes(Yx, Yt, ids, scen):
    d = {i: Yx[i] - Yt[i] for i in ids}
    return {'net': sum(d.values()), 'toward': sum(v > 0 for v in d.values()), 'away': sum(v < 0 for v in d.values()),
            'n_scen_toward': len({scen[i] for i, v in d.items() if v > 0})}


def needle_block(R, needle, arms, ids, scen, draws):
    """R[(needle, arm)][i] = {'Y': 0/1, 'B': float, 'cat': str, ...}; R[('C', 'C')][i] shared."""
    Y = {a: {i: R[(needle, a)][i]['Y'] for i in ids} for a in arms}
    Bv = {a: {i: R[(needle, a)][i]['B'] for i in ids} for a in arms}
    YC = {i: R[('C', 'C')][i]['Y'] for i in ids}
    BC = {i: R[('C', 'C')][i]['B'] for i in ids}
    out = {'Y_counts': {a: sum(Y[a].values()) for a in arms}, 'Y_C': sum(YC.values()),
           'Y_scen_eq': {a: seq({i: float(Y[a][i]) for i in ids}, scen, ids) for a in arms},
           'changes_vs_T': {a: y_changes(Y[a], Y['T'], ids, scen) for a in arms if a != 'T'},
           'gap_to_C': {a: sum(YC.values()) - sum(Y[a].values()) for a in arms},
           'dB_vs_T': {a: describe({i: Bv[a][i] - Bv['T'][i] for i in ids}, scen, ids, draws) for a in arms if a != 'T'},
           'B_gap_to_C': {a: describe({i: BC[i] - Bv[a][i] for i in ids}, scen, ids, draws) for a in arms},
           'categories': {a: {c: sum(1 for i in ids if R[(needle, a)][i]['cat'] == c) for c in ('code', 'preamble', 'stop', 'other')} for a in arms},
           'first_stop': {a: sum(1 for i in ids if R[(needle, a)][i]['first_stop']) for a in arms},
           'components': {a: {k: seq({i: R[(needle, a)][i][k] for i in ids}, scen, ids) for k in ('z_f', 'best_stop', 'best_nonstop_comp')} for a in arms}}
    out['_dY'] = {a: {i: Y[a][i] - Y['T'][i] for i in ids} for a in arms if a != 'T'}
    out['_dB'] = {a: {i: Bv[a][i] - Bv['T'][i] for i in ids} for a in arms if a != 'T'}
    return out


def cross_needle(b0, b1, arms, ids, scen, draws):
    """Same-input paired differences of the arm effects between the two needles (L0 minus L12)."""
    out = {}
    for a in arms:
        if a == 'T':
            continue
        out[a] = {'dY_L0_minus_L12': describe({i: float(b0['_dY'][a][i] - b1['_dY'][a][i]) for i in ids}, scen, ids, draws),
                  'dB_L0_minus_L12': describe({i: b0['_dB'][a][i] - b1['_dB'][a][i] for i in ids}, scen, ids, draws)}
    return out
