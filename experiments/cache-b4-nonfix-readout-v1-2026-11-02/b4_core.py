"""B4 pure functions (no model).  CONTRACT.zh-CN.md r01 §4–5 (plan v2 + v3 amendments).

Arms per input x direction (N background): CC, CFIX, K0, K, K_early, K_late, M_nat, M_rand.
X_arm = z(arm) - z(CC);  rho_arm = X_arm / X with X = X_CFIX, formed only when X >= 1.0.
"""
import math

DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'R1_L00_D-1')
G_LAYERS = (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
EARLY = (13, 14, 16, 17, 18)
LATE = (20, 21, 22, 24, 25, 26, 28, 29, 30)
NV, HD = 32, 128
RULE = {
    'X_min': 1.0,                    # denominator rule (logit)
    'strong': 0.5, 'moderate': 0.8, 'reverse': 1.2,
    'd_ref': 0.2,                    # axis B margin in rho units
    'scen_count': 5, 'dir_count': 3,
    'near_zero_rel': 1e-6,           # A_l <= 1e-6 * max(1, ||W g_CC||) -> near-zero layer
    'lambda_lo': 0.1, 'lambda_hi': 10.0,
    'match_rel': 0.05,               # projected norm of the actual BF16 hook diff vs A_l; out_proj audit
    'shadow_tol': 0.25,              # P2
}


def rho(x_arm, x):
    return x_arm / x if x >= RULE['X_min'] else None


def axis_a(r):
    """Descriptive four-bin label (numeric, mutually exclusive)."""
    if r is None:
        return 'denominator_insufficient'
    if r <= RULE['strong']:
        return 'strong_reduction'
    if r <= RULE['moderate']:
        return 'moderate_reduction'
    if r < RULE['reverse']:
        return 'below_change_threshold'
    return 'reverse_enhancement'


def axis_a_main(r):
    """Main axis-A readout (v3 amendment 3): rho_K <= 0.8 or not."""
    if r is None:
        return 'denominator_insufficient'
    return 'reduced' if r <= RULE['moderate'] else 'not_reduced'


def axis_b(r_k, r_nat, r_rand):
    """Both references must be matchable (r not None) to form a label."""
    if r_k is None:
        return 'denominator_insufficient'
    if r_nat is None or r_rand is None:
        return 'comparison_insufficient'
    d1, d2 = r_nat - r_k, r_rand - r_k
    m = RULE['d_ref']
    if d1 >= m and d2 >= m:
        return 'exceeds_both'
    if (d1 >= m) != (d2 >= m):
        return 'exceeds_one'
    if abs(d1) < m and abs(d2) < m:
        return 'close_to_both'
    return 'other'


def scenario_pairs(values):
    out = {}
    for iid, v in values.items():
        s, f = iid.rsplit('-', 1)
        out.setdefault(s, {})[f] = v
    return {s: (d['f0'], d['f1']) for s, d in sorted(out.items())}


def direction_label(pairs):
    """pairs: scenario -> (label_f0, label_f1).  A label holds for a direction if >= 5/6 scenarios have it in both facts.
    Undecidable labels stay in the fixed denominator of 6."""
    counts = {}
    for s, (a, b) in pairs.items():
        if a == b:
            counts[a] = counts.get(a, 0) + 1
    best = [k for k, v in counts.items() if v >= RULE['scen_count']]
    return (best[0] if best else None), counts


def cross_label(per_dir):
    vals = [v for v in per_dir.values() if v is not None]
    for v in set(vals):
        if vals.count(v) >= RULE['dir_count']:
            return v
    return 'condition_dependent'


def joint_scenarios(pairs_a4, pairs_b):
    """Scenarios where BOTH facts are strong_reduction on the four-bin axis A AND exceeds_both on axis B (same scenarios)."""
    return [s for s in pairs_a4 if pairs_a4[s] == ('strong_reduction', 'strong_reduction') and pairs_b[s] == ('exceeds_both', 'exceeds_both')]


def joint_label(per_dir_joint_counts):
    """per_dir: direction -> number of jointly passing scenarios.  Joint conclusion needs >= 5/6 in >= 3/4 directions."""
    return sum(n >= RULE['scen_count'] for n in per_dir_joint_counts.values()) >= RULE['dir_count']


def predictions(rho_k, rho_shadow):
    """rho_k / rho_shadow: direction -> {input_id: value or None}.
    P1: rho_K <= 0.8 in both facts of >= 5/6 scenarios in >= 3/4 directions.
    P2: |rho_K - rho_shadow| <= 0.25, same counting."""
    def count(d, ok):
        pairs = scenario_pairs({i: ok(i) for i in rho_k[d]})
        return sum(a and b for a, b in pairs.values())
    p1 = {d: count(d, lambda i, d=d: rho_k[d][i] is not None and rho_k[d][i] <= RULE['moderate']) for d in rho_k}
    p2 = {d: count(d, lambda i, d=d: rho_k[d][i] is not None and rho_shadow[d][i] is not None
                   and abs(rho_k[d][i] - rho_shadow[d][i]) <= RULE['shadow_tol']) for d in rho_k}
    return {'P1': sum(v >= RULE['scen_count'] for v in p1.values()) >= RULE['dir_count'], 'P1_counts': p1,
            'P2': sum(v >= RULE['scen_count'] for v in p2.values()) >= RULE['dir_count'], 'P2_counts': p2}


# ---------------------------------------------------------------- matching (torch, works on CPU or GPU)

def unit_rows(t):
    """[NV, HD] per-head norms."""
    return t.float().norm(dim=1)


def build_template(direction_rows, target_head_norms, nonfix_mask):
    """direction_rows: [NV, HD] raw template directions; target_head_norms: [NV] (K actual per-head lengths).
    Returns (v [NV, HD] with FIX rows zero, constructible flag).  A head with target > 0 but zero direction is unconstructible."""
    import torch
    d = direction_rows.float()
    n = d.norm(dim=1)
    ok = True
    v = torch.zeros_like(d)
    for h in range(d.shape[0]):
        if not nonfix_mask[h]:
            continue
        if float(target_head_norms[h]) > 0:
            if float(n[h]) == 0:
                ok = False
                continue
            v[h] = d[h] / n[h] * target_head_norms[h]
    return v, ok


def scale_layer(W, v, A, g_cc):
    """Uniform per-layer coefficient lambda = A / ||W v||, with near-zero and out-of-range flags.
    W: [d_model, NV*HD] (FP32 accumulation), v: [NV, HD], A: target projected norm, g_cc: [NV, HD] donor (for the threshold)."""
    thr = RULE['near_zero_rel'] * max(1.0, float((W @ g_cc.float().reshape(-1)).norm()))
    if A <= thr:
        return {'near_zero': True, 'lambda': 0.0, 'ok': True, 'thr': thr}
    pv = float((W @ v.float().reshape(-1)).norm())
    if pv <= thr:
        return {'near_zero': False, 'lambda': None, 'ok': False, 'reason': 'template_projection_near_zero', 'thr': thr}
    lam = A / pv
    ok = RULE['lambda_lo'] <= lam <= RULE['lambda_hi']
    return {'near_zero': False, 'lambda': lam, 'ok': ok, 'reason': None if ok else 'lambda_out_of_range', 'thr': thr}


def seeded_gaussian(key, shape):
    import torch
    import zlib
    g = torch.Generator().manual_seed(zlib.crc32(key.encode()))
    return torch.randn(*shape, generator=g)


def finite(*xs):
    return all(x is not None and math.isfinite(x) for x in xs)
