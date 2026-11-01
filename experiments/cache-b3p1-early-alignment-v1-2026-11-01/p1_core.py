"""B3-P1 pure math (FP64 torch, no model).  CONTRACT.zh-CN.md r01.

Per unit (input x direction x split), steps s = 0..37 = (layer 13 mixer, layer 13 MLP, ..., layer 31 MLP).
alpha_s = delta10_s - delta00_s, beta_s = delta01_s - delta00_s (actual residual increments).  a, b = cumulative sums.
C = 2<a,b>;  dC_s = 2<alpha_s,beta_s> + 2<a_before,beta_s> + 2<alpha_s,b_before>  (same-step, newB-on-oldA, newA-on-oldB)
M_ij = 2<alpha_i,beta_j>,  sum_ij M_ij over a window starting at the entry = C at the window end.
"""
import math

RULE = {
    'major': 0.75, 'minor': 0.25,        # share labels
    'dir_count': 3, 'scen_count': 5,      # >= 3/4 directions, >= 5/6 scenarios (both facts)
    'tau_vec': 1e-6, 'tau_E': 1e-9,       # NA thresholds (relative to |c_end|, |c_end|^2)
    'identity_rel': 1e-9,
}
WINDOW = list(range(12))                  # layers 13-18: 6 layers x (mixer, MLP)
FULL = list(range(38))
STEP_NAMES = [f'{l}:{k}' for l in range(13, 32) for k in ('mix', 'mlp')]


def stack(vs):
    import torch
    return torch.stack([v.double() for v in vs])


def project(X, e):
    """Rows of X projected off unit vector e (fixed axis)."""
    return X - (X @ e)[:, None] * e[None, :]


def steps(alpha, beta, idx, tau_v):
    """alpha, beta: [S, d] FP64.  idx: step indices of the window (must start at step 0).  Returns per-step rows, M, sums."""
    assert idx[0] == 0 and idx == list(range(idx[0], idx[-1] + 1))
    al, be = alpha[idx], beta[idx]
    M = 2 * al @ be.T
    a = al.new_zeros(al.shape[1])
    b = be.new_zeros(be.shape[1])
    rows = []
    for j in range(len(idx)):
        x, y = al[j], be[j]
        same = 2 * float(x @ y)
        nb_oa = 2 * float(a @ y)
        na_ob = 2 * float(x @ b)
        a, b = a + x, b + y
        na, nb_, nx, ny = float(a.norm()), float(b.norm()), float(x.norm()), float(y.norm())
        rows.append({'step': STEP_NAMES[idx[j]], 'dC': same + nb_oa + na_ob, 'same': same, 'newB_oldA': nb_oa, 'newA_oldB': na_ob,
                     'C': 2 * float(a @ b), 'norm_a': na, 'norm_b': nb_,
                     'cos_ab': float(a @ b) / (na * nb_) if na > tau_v and nb_ > tau_v else None,
                     'norm_alpha': nx, 'norm_beta': ny,
                     'cos_alpha_beta': float(x @ y) / (nx * ny) if nx > tau_v and ny > tau_v else None})
    C_end = rows[-1]['C']
    scale = max(1.0, sum(abs(r['same']) + abs(r['newB_oldA']) + abs(r['newA_oldB']) for r in rows))
    err_steps = abs(sum(r['dC'] for r in rows) - C_end) / scale
    err_M = abs(float(M.sum()) - C_end) / max(1.0, float(M.abs().sum()))
    return rows, M, {'C_end': C_end, 'err_steps': err_steps, 'err_M': err_M}


def shares(rows, M, tau_E):
    """MLP share of positive growth; same-step absolute share of the window's M (no pre-summing of signs)."""
    pos = [max(r['dC'], 0.0) for r in rows]
    G = sum(pos)
    neg = sum(min(r['dC'], 0.0) for r in rows)
    mlp = sum(p for p, r in zip(pos, rows) if r['step'].endswith(':mlp'))
    D_abs = float(M.diagonal().abs().sum())
    O_abs = float(M.abs().sum()) - D_abs
    signed_same = float(M.diagonal().sum())
    signed_cross = float(M.sum()) - signed_same
    return {'G': G, 'negative_total': neg, 'net': sum(r['dC'] for r in rows),
            'S_MLP': mlp / G if G > tau_E else None,
            'same_abs_share': D_abs / (D_abs + O_abs) if D_abs + O_abs > tau_E else None,
            'signed_same': signed_same, 'signed_cross': signed_cross,
            'cancellation': (-neg) / G if G > tau_E else None}


def label_mlp(s):
    if s is None:
        return 'not_resolvable'
    return 'mlp_dominant' if s >= RULE['major'] else 'mixer_dominant' if s <= RULE['minor'] else 'distributed'


def label_same(s):
    if s is None:
        return 'not_resolvable'
    return 'same_step_concentrated' if s >= RULE['major'] else 'cross_step_concentrated' if s <= RULE['minor'] else 'mixed'


def label_block(s):
    if s is None:
        return 'not_resolvable'
    return 'own_block_dominant' if s >= RULE['major'] else 'other_block_dominant' if s <= RULE['minor'] else 'mixed'


def across(per_dir_scen):
    """per_dir_scen: direction -> {scenario: (label_f0, label_f1)}.  A label holds in a direction if >= 5/6 scenarios have it
    in both facts; cross-direction label if it holds in >= 3/4 directions, else 'condition_dependent'."""
    held = {}
    for d, scen in per_dir_scen.items():
        counts = {}
        for s, (x, y) in scen.items():
            if x == y:
                counts[x] = counts.get(x, 0) + 1
        best = [k for k, v in counts.items() if v >= RULE['scen_count']]
        held[d] = best[0] if best else None
    vals = [v for v in held.values() if v is not None]
    for v in set(vals):
        if vals.count(v) >= RULE['dir_count']:
            return v, held
    return 'condition_dependent', held


def joint(orig, proj):
    return orig if orig == proj else 'projection_sensitive'


def block_terms(aA, aB, aR, bA, bB, bR, a_before, b_before):
    """One G-mixer step with alpha = aA + aB + aR, beta = bA + bB + bR (A-head block, B-head block, rounding remainder).
    own parts: aA (A's history through A heads), bB.  other parts: aB (A's history expressed through B heads), bA.
    Returns dC split into own-only, involving-other, involving-remainder (exact sum)."""
    def d(x, y):
        return float((x * y).sum())
    own = 2 * d(aA, bB) + 2 * d(a_before, bB) + 2 * d(aA, b_before)
    rem = 2 * (d(aR, bA + bB + bR) + d(aA + aB, bR)) + 2 * d(a_before, bR) + 2 * d(aR, b_before)
    total = 2 * d(aA + aB + aR, bA + bB + bR) + 2 * d(a_before, bA + bB + bR) + 2 * d(aA + aB + aR, b_before)
    other = total - own - rem
    return {'own': own, 'other': other, 'rem': rem, 'total': total,
            'norm_aA': float(aA.norm()), 'norm_aB': float(aB.norm()), 'norm_bA': float(bA.norm()), 'norm_bB': float(bB.norm()),
            'norm_aR': float(aR.norm()), 'norm_bR': float(bR.norm())}


def block_share(rows, tau_E):
    own = sum(abs(r['own']) for r in rows)
    other = sum(abs(r['other']) for r in rows)
    return own / (own + other) if own + other > tau_E else None


def radial(a, b, c):
    """Share of 2<a,b> carried along the common background axis c, and the perpendicular cosine."""
    e = c / c.norm()
    ae, be = float(a @ e), float(b @ e)
    al = 2 * float(a @ b)
    ap, bp = a - ae * e, b - be * e
    return {'aligned': al, 'along_c': 2 * ae * be, 'share_along_c': 2 * ae * be / al if al != 0 else None,
            'a_dot_e': ae, 'b_dot_e': be, 'cos_perp': float(ap @ bp) / float(ap.norm() * bp.norm())}


def registered(fix_window_same, fix_full_same, fix_window_block):
    """Speculative tier, frozen before the run.
    P1: FIX same-step label is 'cross_step_concentrated' in the 13-18 window AND over all 38 steps (joint orig/P labels).
    P2: FIX cross-direction head-block label over the G-mixer steps of the 13-18 window is 'other_block_dominant' or 'mixed'
        (i.e. a stable label that is not own-block dominant; 'condition_dependent' does not count)."""
    return {'P1_cross_step': fix_window_same == 'cross_step_concentrated' and fix_full_same == 'cross_step_concentrated',
            'P2_not_own_block': fix_window_block in ('other_block_dominant', 'mixed')}


def scenario_pairs(values):
    """values: dict input_id (Pxx-f0 / Pxx-f1) -> value.  Returns scenario -> (v_f0, v_f1)."""
    out = {}
    for iid, v in values.items():
        sc, f = iid.rsplit('-', 1)
        out.setdefault(sc, {})[f] = v
    return {sc: (x['f0'], x['f1']) for sc, x in sorted(out.items())}
