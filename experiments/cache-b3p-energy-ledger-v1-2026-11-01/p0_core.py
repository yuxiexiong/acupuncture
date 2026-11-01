"""B3-P0 pure math (FP64 torch, no model).  CONTRACT.zh-CN.md r01.

Four cells of one split (A = 45-head set, B = the rest): 00 = N:CC, 10 = A gets T V history, 01 = B gets it, 11 = N:CT.
For any vector y:  c = y00, a = y10 - y00, b = y01 - y00, k = K(y) = y11 - y10 - y01 + y00.
Exact identity:  K(||y||^2) = 2<a,b> + 2<y11 - k, k> + ||k||^2
                 ("aligned main effects"      "vector interaction")
Branch attribution of the final h (h = entry + sum_j increments_j, entry identical in the four cells):
    aligned_j = <a_j, b> + <a, b_j>                  sum_j = 2<a,b>
    inter_j   = 2<h11 - k, k_j> + <k, k_j>           sum_j = 2<h11 - k, k> + ||k||^2
"""
import math

RULE = {
    'class_major': 0.75,     # aligned share >= 0.75 -> 'aligned_main'; <= 0.25 -> 'vector_interaction'; else 'mixed'
    'class_minor': 0.25,
    'dir_count': 3,          # >= 3 of 4 directions
    'scen_count': 5,         # >= 5 of 6 scenarios
    'cand_share': 0.25,      # branch inter_j scenario mean >= 0.25 x K(E_final) scenario mean
    'tiny': 1e-6,            # K(E_final) must exceed tiny x max(E_final of the four cells) to form shares
    'pred_r_drop': 0.25,     # additive-donor counterfactual: scenario-mean K(r) reduced by >= 25%
    'pred_p_logit': 0.1,     # |delta p_11| / r_11 <= 0.1 logit, both facts
    'identity_rel': 1e-9,    # FP64 identity tolerance relative to sum of |terms|
    'recompute_rel': None,   # filled from readiness (C_native calibration), see CONTRACT §3
    'k_recompute_rel': 0.2,  # |K(f64) - K(f_rec)| <= 0.2 ||K(f_rec)|| for an MLP layer's generated/inherited split to be usable
}
CELLS = ('00', '10', '01', '11')


def dot(x, y):
    return float((x * y).sum())


def parts(y):
    """y: dict cell -> FP64 vector."""
    c = y['00']
    a = y['10'] - c
    b = y['01'] - c
    k = y['11'] - y['10'] - y['01'] + c
    return c, a, b, k


def energy(y, e=None):
    c, a, b, k = parts(y)
    KE = sum(s * dot(y[x], y[x]) for x, s in zip(CELLS, (1, -1, -1, 1)))
    aligned = 2 * dot(a, b)
    base = y['11'] - k
    inter = 2 * dot(base, k) + dot(k, k)
    scale = abs(2 * dot(a, b)) + abs(2 * dot(base, k)) + dot(k, k) + sum(dot(y[x], y[x]) for x in CELLS)
    out = {'KE': KE, 'aligned': aligned, 'inter': inter, 'identity_err': KE - aligned - inter, 'identity_scale': scale,
           'cos_ab': aligned / 2 / math.sqrt(dot(a, a) * dot(b, b)) if dot(a, a) > 0 and dot(b, b) > 0 else None,
           'norm_a': math.sqrt(dot(a, a)), 'norm_b': math.sqrt(dot(b, b)), 'norm_k': math.sqrt(dot(k, k))}
    if e is not None:
        ae, be = dot(a, e), dot(b, e)
        out['aligned_stop_dir'] = 2 * ae * be
        out['aligned_orth'] = aligned - 2 * ae * be
    return out


def attribution(incs, y):
    """incs: list of (name, dict cell -> increment vector); y: dict cell -> final h.  Returns per-branch aligned/inter."""
    c, a, b, k = parts(y)
    base = y['11'] - k
    rows = {}
    for name, d in incs:
        _, aj, bj, kj = parts(d)
        rows[name] = {'aligned': dot(aj, b) + dot(a, bj), 'inter': 2 * dot(base, kj) + dot(k, kj), 'k_vec': kj}
    return rows


def inter_of(kj, y):
    _, _, _, k = parts(y)
    return 2 * dot(y['11'] - k, kj) + dot(k, kj)


def rms(h, eps):
    return math.sqrt(dot(h, h) / h.numel() + eps)


def readout(y, u, eps):
    """K of r, p = u.h, z = p/r over the four cells."""
    r = {x: rms(y[x], eps) for x in CELLS}
    p = {x: dot(u, y[x]) for x in CELLS}
    sgn = dict(zip(CELLS, (1, -1, -1, 1)))
    return {'r': r, 'p': p, 'Kr': sum(sgn[x] * r[x] for x in CELLS), 'Kp': sum(sgn[x] * p[x] for x in CELLS),
            'Kz': sum(sgn[x] * p[x] / r[x] for x in CELLS)}


def classify(shares):
    """shares: per-direction aligned share (scenario-mean aligned / scenario-mean KE); None if not formable."""
    lab = []
    for s in shares:
        if s is None:
            lab.append('not_formable')
        elif s >= RULE['class_major']:
            lab.append('aligned_main')
        elif s <= RULE['class_minor']:
            lab.append('vector_interaction')
        else:
            lab.append('mixed')
    for name in ('aligned_main', 'vector_interaction'):
        if lab.count(name) >= RULE['dir_count']:
            return name, lab
    return ('mixed' if lab.count('not_formable') < 2 else 'not_formable'), lab


def scenario_pairs(values):
    """values: dict input_id -> value; inputs named Pxx-f0 / Pxx-f1.  Returns dict scenario -> (v_f0, v_f1)."""
    out = {}
    for iid, v in values.items():
        s, f = iid.rsplit('-', 1)
        out.setdefault(s, {})[f] = v
    return {s: (d['f0'], d['f1']) for s, d in sorted(out.items())}


def branch_qualifies(per_dir):
    """per_dir: direction -> {scenario: (inter_f0, inter_f1, KE_f0, KE_f1, formable_f0, formable_f1)}.
    Scenario passes: both facts formable, both inter > 0, mean inter >= cand_share x mean KE.  Direction passes: >= 5/6."""
    dirs_ok = 0
    detail = {}
    for d, scen in per_dir.items():
        ok = 0
        for s, (i0, i1, e0, e1, f0, f1) in scen.items():
            if f0 and f1 and i0 > 0 and i1 > 0 and (i0 + i1) / 2 >= RULE['cand_share'] * (e0 + e1) / 2:
                ok += 1
        detail[d] = ok
        dirs_ok += ok >= RULE['scen_count']
    return dirs_ok >= RULE['dir_count'], detail


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def prediction_card(per_dir):
    """per_dir: direction -> {scenario: ((Kr0_f0, Kr1_f0, dp_f0), (Kr0_f1, Kr1_f1, dp_f1))} with Kr0 baseline, Kr1 after the
    additive-donor operation, dp = |delta p_11| / r_11 (logit).  Scenario passes: both facts Kr1 < Kr0 and dp <= 0.1, and
    scenario-mean drop >= 25% of scenario-mean Kr0 (Kr0 mean must be > 0).  Direction: >= 5/6; card: >= 3/4."""
    dirs_ok, detail = 0, {}
    for d, scen in per_dir.items():
        ok = 0
        for s, (x0, x1) in scen.items():
            k0 = (x0[0] + x1[0]) / 2
            k1 = (x0[1] + x1[1]) / 2
            if (x0[1] < x0[0] and x1[1] < x1[0] and x0[2] <= RULE['pred_p_logit'] and x1[2] <= RULE['pred_p_logit']
                    and k0 > 0 and (k0 - k1) >= RULE['pred_r_drop'] * k0):
                ok += 1
        detail[d] = ok
        dirs_ok += ok >= RULE['scen_count']
    return dirs_ok >= RULE['dir_count'], detail


def registered_predictions(fix_class_shares, cos_fix, cos_u1, cos_u2):
    """Speculative tier, frozen before the run.
    P1: FIX aligned share >= 0.5 in >= 3/4 directions (each main effect shrinks |h| along -c, so a and b share a -c part).
    P2: FIX scenario-mean cos(a,b) of the final h exceeds both random splits' in >= 3/4 directions."""
    p1 = sum(s is not None and s >= 0.5 for s in fix_class_shares) >= RULE['dir_count']
    p2 = sum(f is not None and f > max(x for x in (g, h) if x is not None)
             for f, g, h in zip(cos_fix, cos_u1, cos_u2)) >= RULE['dir_count']
    return {'P1_aligned_share_ge_half': p1, 'P2_fix_cos_exceeds_random': p2}
