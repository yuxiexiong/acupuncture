"""B3 pure functions (no model): 2x2 decomposition of the fixed-list V effect, random-split null band for the
interaction, final-norm scale decomposition, layerwise first-detectable position.  CONTRACT.zh-CN.md r01 §4.

Cells (all in the N background of one input x direction):  CC (no T V history), FIX (FIX heads T), REST (other heads
T), CT (all T); random splits U_k / U_k^c (FIX's frozen layer-matched random 45-head subset k and its complement).
    X = z(FIX) - z(CC)     F = z(CT) - z(CC)     D = F - X     R = z(REST) - z(CC)
    I = z(CT) - z(FIX) - z(REST) + z(CC)          so  D = R + I  exactly.
"""
import math

DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'R1_L00_D-1')
ANCHOR = DIRECTIONS[0]
WEAKENED = DIRECTIONS[1:]          # C2: X/F > 1 in all six scenarios
SPLITS = ('U1', 'U2')
RULE = {
    'D_min': 0.5,          # |mean D| below this (logit) -> D too small to decompose (descriptive only)
    'major': 0.75,         # share >= major -> that part dominates
    'minor': 0.25,         # min share below -minor -> flag 'opposing'
    'band_count': 9,       # >= 9 of 12 inputs beyond the pooled random-split band, same side -> FIX-specific
    'scale_share': 0.5,    # |interaction carried by r| >= 0.5 |I| -> final-norm scale involved
    'recon_tol': 0.15,     # |z recomputed from final h (fp64) - z from logits| (logit), analysis numerics check
}
SIDES = {'stop': 'cz_s46', 'answer': 'cz_a'}


def contrasts(z):
    """z: dict cell -> value with keys CC, FIX, REST, CT."""
    X = z['FIX'] - z['CC']
    F = z['CT'] - z['CC']
    R = z['REST'] - z['CC']
    I = z['CT'] - z['FIX'] - z['REST'] + z['CC']
    return {'X': X, 'F': F, 'D': F - X, 'R': R, 'I': I}


def split_interaction(z_ct, z_cc, z_u, z_uc):
    return z_ct - z_u - z_uc + z_cc


def mean(xs):
    return sum(xs) / len(xs)


def composition(R, I, D):
    """Per-direction composition of the weakening D over inputs (means are linear, so mean R + mean I = mean D)."""
    mR, mI, mD = mean(R), mean(I), mean(D)
    out = {'mean_R': mR, 'mean_I': mI, 'mean_D': mD}
    if abs(mD) < RULE['D_min']:
        out.update(category='D_small', share_R=None, share_I=None, opposing=None)
        return out
    sR, sI = mR / mD, mI / mD
    if sR >= RULE['major']:
        cat = 'self'
    elif sI >= RULE['major']:
        cat = 'interaction'
    else:
        cat = 'both'
    per_input = []
    for r, i, d in zip(R, I, D):
        if abs(d) < RULE['D_min']:
            per_input.append('D_small')
        else:
            per_input.append('self' if r / d >= RULE['major'] else 'interaction' if i / d >= RULE['major'] else 'both')
    out.update(category=cat, share_R=sR, share_I=sI, opposing=min(sR, sI) < -RULE['minor'],
               per_input=per_input, per_input_counts={k: per_input.count(k) for k in ('self', 'interaction', 'both', 'D_small')})
    return out


def band(values, nulls):
    """values: per-input statistic for FIX/REST; nulls: per-input list of the same statistic for random splits.
    Pooled band = [min, max] of all null values of the direction.  Under exchangeability a single input lands beyond
    one given side with probability <= 1/(m+1) (m pooled nulls); >= 9/12 on one side is the FIX-specific label."""
    pooled = [v for row in nulls for v in row]
    lo, hi = min(pooled), max(pooled)
    above = sum(v > hi for v in values)
    below = sum(v < lo for v in values)
    side = 'above' if above >= below else 'below'
    count = max(above, below)
    return {'lo': lo, 'hi': hi, 'above': above, 'below': below, 'side': side, 'count': count, 'n_null': len(pooled),
            'label': 'specific' if count >= RULE['band_count'] else 'within'}


def scale_terms(p0, r0, p1, r1):
    """Symmetric exact split of p1/r1 - p0/r0 into numerator and denominator terms (plan §5 item 2)."""
    num = (p1 - p0) * (1 / r1 + 1 / r0) / 2
    den = (p1 + p0) * (1 / r1 - 1 / r0) / 2
    return {'num': num, 'den': den, 'total': p1 / r1 - p0 / r0}


def scale_interaction(p, r):
    """p, r: dict cell -> value for CC, FIX, REST, CT.  I_z = sum c z; the part carried by the numerator at a common
    scale r_bar (mean r of the four cells) is sum c p / r_bar; the rest is carried by r varying across cells."""
    c = {'CT': 1, 'FIX': -1, 'REST': -1, 'CC': 1}
    rbar = mean([r[k] for k in c])
    iz = sum(c[k] * p[k] / r[k] for k in c)
    ip = sum(c[k] * p[k] for k in c) / rbar
    return {'I_z': iz, 'I_num_common_r': ip, 'I_scale': iz - ip, 'r_bar': rbar}


def scale_label(I_z, I_scale):
    mz, ms = mean(I_z), mean(I_scale)
    if abs(mz) == 0:
        return {'mean_I_z': mz, 'mean_I_scale': ms, 'label': 'zero'}
    return {'mean_I_z': mz, 'mean_I_scale': ms, 'share_scale': ms / mz,
            'label': 'scale_involved' if abs(ms) >= RULE['scale_share'] * abs(mz) else 'numerator_dominant'}


def first_detectable(layers, per_layer_values, per_layer_nulls):
    """First layer (in order) whose interaction on the stop readout is beyond the pooled random-split band on one side
    in >= band_count inputs.  Called 'first detectable position of this readout', not an origin."""
    rows = {}
    first = None
    for l in layers:
        b = band(per_layer_values[l], per_layer_nulls[l])
        rows[l] = b
        if first is None and b['label'] == 'specific':
            first = {'layer': l, 'side': b['side'], 'count': b['count']}
    return {'first': first, 'rows': rows}


def prediction(comp, spec):
    """Registered (speculative tier) before any B3 data: P1 interaction dominates the weakening in >= 2 of the three
    weakened directions; P2 FIX/REST interaction is beyond the random-split band in >= 2 of the three."""
    p1 = sum(comp[d]['category'] == 'interaction' for d in WEAKENED) >= 2
    p2 = sum(spec[d]['label'] == 'specific' for d in WEAKENED) >= 2
    return {'P1_interaction_dominates': p1, 'P2_fix_specific_interaction': p2}


def finite(x):
    return x is not None and not (isinstance(x, float) and (math.isnan(x) or math.isinf(x)))
