"""WIN-01 pure pieces (CONTRACT r01).  No model is loaded here.

- windows: position masks for W_all / W_pre / W_post over the prefix 0..n-2
- arm targets: [(layer, field, slice)] with slice None (whole tensor) or ('pos', b) (KV positions 0..b along the sequence axis)
- replace / check_replace: deep copy of the receiver with targets from the donor; everything else bit-equal
- criteria (§8): testability, arm effect, window contrast with scenario-stratified bootstrap, B-block transfer
"""
import random

NEEDLES = ('N_L00_C4146_D-1', 'N_L01_C2765_D-1')
NEEDLE_LAYER = {'N_L00_C4146_D-1': 0, 'N_L01_C2765_D-1': 1}
WINDOWS = ('W_all', 'W_pre', 'W_post')
ARMS = ('T', 'R_all', 'S_deep', 'KV_all', 'R+KV_all')
ATTR_ARM = 'R_all+KV_pre'                    # only under W_all (DECISIONS D4)
B_ARMS = ('Bx_R', 'Bx_S', 'Bx_KV', 'Bx_all')
B_ALIGNED_ONLY = ('Bx_KV', 'Bx_all')
G14 = (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
KV_LAYERS = (3, 7, 11, 15, 19, 23, 27, 31)
STAGE2_CODE = {'T': 'TTT', 'R_all': 'TCT', 'KV_all': 'CTT', 'R+KV_all': 'CCT'}   # W_all bridge cells (code order KV, R, conv)
BOOT_N, SEED = 2000, 20261103
TESTABLE_MIN_ERRORS = 12
CHANGE_MIN, NULL_BAND = 0.20, 0.10
B_TRANSFER_MIN, B_NULL_BAND = 0.20, 0.10


# ---------------------------------------------------------------- windows

def window_mask(window, n, b):
    """Boolean mask over prefix positions 0..n-2 (length n-1)."""
    assert 0 <= b < n - 2, (n, b)
    pos = range(n - 1)
    if window == 'W_all':
        return [True for _ in pos]
    if window == 'W_pre':
        return [p <= b for p in pos]
    if window == 'W_post':
        return [p > b for p in pos]
    raise ValueError(window)


# ---------------------------------------------------------------- targets

def linear_layers(types):
    return tuple(i for i, k in enumerate(types) if k == 'linear_attention')


def attn_layers(types):
    return tuple(i for i, k in enumerate(types) if k == 'full_attention')


def arm_targets(arm, types, b=None):
    rec_all = [(l, 'recurrent_states', None) for l in linear_layers(types)]
    rec_g = [(l, 'recurrent_states', None) for l in G14]
    kv_all = [(l, f, None) for l in attn_layers(types) for f in ('keys', 'values')]
    if arm == 'T':
        return []
    if arm in ('R_all', 'Bx_R'):
        return rec_all
    if arm in ('S_deep', 'Bx_S'):
        return rec_g
    if arm in ('KV_all', 'Bx_KV'):
        return kv_all
    if arm == 'R+KV_all':
        return rec_all + kv_all
    if arm == ATTR_ARM:
        assert b is not None
        return rec_all + [(l, f, ('pos', b)) for l in attn_layers(types) for f in ('keys', 'values')]
    if arm == 'Bx_all':
        return rec_all + [(l, 'conv_states', None) for l in linear_layers(types)] + kv_all
    raise ValueError(arm)


def _slice_pos(t, b):
    """KV tensors are [batch, heads, seq, dim]; positions 0..b along axis 2."""
    assert t.dim() == 4, tuple(t.shape)
    return (slice(None), slice(None), slice(0, b + 1), slice(None))


def replace(receiver, donor, tg, get, set_, deepcopy):
    X = deepcopy(receiver)
    for l, f, sl in tg:
        a, d = get(X.layers[l], f), get(donor.layers[l], f)
        if sl is None:
            assert a.shape == d.shape and a.dtype == d.dtype, ('shape/dtype', l, f, tuple(a.shape), tuple(d.shape))
            set_(X.layers[l], f, d.clone())
        else:
            assert sl[0] == 'pos'
            idx = _slice_pos(a, sl[1])
            assert a[idx].shape == d[idx].shape and a.dtype == d.dtype, ('slice shape', l, f)
            new = a.clone()
            new[idx] = d[idx]
            set_(X.layers[l], f, new)
    return X


def check_replace(X, receiver, donor, tg, fields, get, equal):
    """Targets equal the donor (slice: positions 0..b donor, rest receiver); all other tensors bit-equal to the receiver."""
    tset = {(l, f) for l, f, _ in tg}
    for l, f, sl in tg:
        a, d, r = get(X.layers[l], f), get(donor.layers[l], f), get(receiver.layers[l], f)
        if sl is None:
            assert equal(a, d), ('target != donor', l, f)
        else:
            idx = _slice_pos(a, sl[1])
            b = sl[1]
            assert equal(a[idx], d[idx]), ('slice != donor', l, f)
            assert equal(a[:, :, b + 1:], r[:, :, b + 1:]), ('outside slice changed', l, f)
    for l, f in fields:
        if (l, f) not in tset:
            assert equal(get(X.layers[l], f), get(receiver.layers[l], f)), ('non-target changed', l, f)


# ---------------------------------------------------------------- criteria (§8)

def boot_index(units, scen, n=BOOT_N, seed=SEED):
    """Scenario-stratified bootstrap.  Each draw is a list of groups: scenarios resampled with replacement (a scenario
    drawn twice appears as two groups), units resampled with replacement within each drawn scenario."""
    rng = random.Random(seed)
    by = {}
    for u in units:
        by.setdefault(scen[u], []).append(u)
    keys = sorted(by)
    draws = []
    for _ in range(n):
        groups = []
        for _k in keys:
            members = by[keys[rng.randrange(len(keys))]]
            groups.append([members[rng.randrange(len(members))] for _ in members])
        draws.append(groups)
    return draws


def scen_mean(vals, units, scen):
    by = {}
    for u in units:
        by.setdefault(scen[u], []).append(vals[u])
    return sum(sum(v) / len(v) for v in by.values()) / len(by)


def _draw_mean(vals, groups):
    return sum(sum(vals[u] for u in g) / len(g) for g in groups) / len(groups)


def describe(vals, units, scen, draws):
    """Scenario-equal-weight mean with 95% percentile interval over the shared draws (draws built on these units)."""
    est = scen_mean(vals, units, scen)
    bs = sorted(_draw_mean(vals, g) for g in draws)
    return {'mean': est, 'lo': bs[int(0.025 * len(bs))], 'hi': bs[int(0.975 * len(bs)) - 1], 'n': len(units)}


def testable(y_t):
    """§8.1: at least 12 of the inputs wrong under T."""
    return sum(1 for v in y_t.values() if v == 0) >= TESTABLE_MIN_ERRORS


def effect(y_arm, y_t):
    return {u: y_arm[u] - y_t[u] for u in y_t}


def contrast_label(d):
    """§8.3 on a describe() dict of the paired difference."""
    if (d['lo'] > 0 or d['hi'] < 0) and abs(d['mean']) >= CHANGE_MIN:
        return 'changes'
    if d['lo'] >= -NULL_BAND and d['hi'] <= NULL_BAND:
        return 'no_detectable_difference'
    return 'indeterminate'


def window_contrast(y1_arm, y1_t, y2_arm, y2_t, units, scen, draws):
    """Delta = E(w1, A) - E(w2, A), paired per input; label only when both windows are testable."""
    if not (testable({u: y1_t[u] for u in units}) and testable({u: y2_t[u] for u in units})):
        return {'label': 'not_applicable', 'reason': 'T has fewer than 12 errors in a window'}
    e1, e2 = effect(y1_arm, y1_t), effect(y2_arm, y2_t)
    d = describe({u: e1[u] - e2[u] for u in units}, units, scen, draws)
    return {**d, 'label': contrast_label(d)}


def same_window_contrast(ya, yb, y_t, units, scen, draws):
    """M5: [A] - [B] within one window (both relative to the same T), paired."""
    if not testable({u: y_t[u] for u in units}):
        return {'label': 'not_applicable', 'reason': 'T has fewer than 12 errors'}
    d = describe({u: ya[u] - yb[u] for u in units}, units, scen, draws)
    lab = contrast_label(d)
    return {**d, 'label': {'changes': 'has_effect'}.get(lab, lab)}


def transfer_label(donor_rate, base_rate):
    """§8.5: donor_rate = describe() of donor-fact indicator; base_rate = scalar D0 on the same receivers' C."""
    if donor_rate['lo'] >= base_rate + B_TRANSFER_MIN:
        return 'transferred'
    if donor_rate['hi'] <= base_rate + B_NULL_BAND:
        return 'not_transferred'
    return 'indeterminate'
