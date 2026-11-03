"""NMT-01 core (CPU-testable): increment scaling, random-content increments, I_S descriptors, read-outs and the frozen readings
(plan docs/cache-increment-norm-match-v2-2026-11-03/PLAN.zh-CN.md; CONTRACT r01 §3–§5).

State blocks are [1, H, dk, dv] (one G layer).  dS(s, b) = S(s,1,b) - S(s,0,b); n_s(l,h,b) = ||dS(s,b)[l,h]||_F.
  UP  : X = dS(0,b) * n_1/n_0          (native direction, restored magnitude distribution)
  DN  : X = dS(1,b) * n_0/n_1          (restored direction, native magnitude distribution)
  UPG : X = dS(0,b) * N_1(b)/N_0(b)    (one global factor; N_s(b) = norm of all 14 layers x heads concatenated)
  RND : X = n_1 * k_hat_b rho_hat^T    (native unit write key of that layer/head/b; random unit right factor shared by b = 0/1)
Zero rules (per block): src = tgt = 0 -> 0; src > 0, tgt = 0 -> 0; src = 0, tgt > 0 -> Unmatchable (engineering stop).
Layer 13 (identical blocks for both sources) is copied directly by the runner for UP / DN.
Read-out: H(r, X) = [F(r,X,1) - Z(r,1)] - [F(r,X,0) - Z(r,0)]; D_src(r) = H(r,'1') - H(r,'0');
  Phi_up = (H_UP - H_0) / D_src, Phi_dn = (H_1 - H_DN) / D_src; residuals R_up = H_UP - H_1, R_dn = H_DN - H_0.
Aggregation: per input, six scenarios equally weighted for numerator and denominator, then divide (never average per-input ratios);
ratio only when the scenario-equal D_src >= 0.5.  Bootstrap: scenario-stratified, 2000 draws, seed 20261103, ONE set of resampled index
lists shared by every arm, receiver, b and direction; a draw with denominator <= 0 makes the ratio interval unavailable."""
import random

D_MIN = 0.5
BOOT_N = 2000
SEED = 20261103
NEAR_LO, NEAR_HI, LOW, BG = 0.75, 1.25, 0.5, 0.3
IS_BAND = (0.8, 1.25)


class Unmatchable(Exception):
    """Source block is zero while the target block is not: a direction cannot be scaled to a non-zero norm."""


def head_norms(T):
    """[1, H, dk, dv] -> [H] FP64 Frobenius norms."""
    return T.double().flatten(-2).norm(dim=-1)[0]


def scale_blocks(src, n_src, n_tgt):
    """src [1,H,dk,dv]; n_src, n_tgt [H] FP64.  Returns (X FP64, coefficient [H] FP64 with 0 where X = 0)."""
    import torch
    zs, zt = n_src == 0, n_tgt == 0
    if bool((zs & ~zt).any()):
        raise Unmatchable(f'{int((zs & ~zt).sum())} head block(s): source zero, target non-zero')
    coef = torch.where(zs | zt, torch.zeros_like(n_src), n_tgt / torch.where(zs, torch.ones_like(n_src), n_src))
    return src.double() * coef[None, :, None, None], coef


def rnd_block(n_tgt, k_hat, rho):
    """n_tgt [H]; k_hat [1,H,dk] (unit); rho [H,dv] (any norm) -> [1,H,dk,dv] FP64 = n_tgt * k_hat rho_hat^T."""
    k = k_hat.double()[0]
    k = k / k.norm(dim=-1, keepdim=True).clamp_min(1e-300)     # kernel key carries eps inside rsqrt: re-unitise, same direction
    r = rho.double().to(k.device)
    r = r / r.norm(dim=-1, keepdim=True).clamp_min(1e-300)
    return (n_tgt.double()[:, None, None] * k[:, :, None] * r[:, None, :])[None]


def rank1_residual(dS, k_hat):
    """|| dS - k k^T dS || / || dS || per head (max over heads): checks that k_hat is the write axis of dS."""
    k = k_hat.double()[0]                      # [H, dk]
    k = k / k.norm(dim=-1, keepdim=True).clamp_min(1e-300)
    D = dS.double()[0]                         # [H, dk, dv]
    proj = k[:, :, None] * (k[:, :, None] * D).sum(1, keepdim=True)
    num = (D - proj).flatten(-2).norm(dim=-1)
    den = D.flatten(-2).norm(dim=-1)
    ok = den > 0
    return float((num[ok] / den[ok]).max()) if bool(ok.any()) else 0.0


def is_descriptor(X0, X1, T0, T1):
    """Per layer: ||I(X)|| / ||I(T)|| and cos(I(X), I(T)), with I(.) = (.)_b1 - (.)_b0.  X*, T*: {layer: [1,H,dk,dv]}.
    Also the concatenated (all layers) ratio and cosine."""
    import torch
    rows, ax, at = {}, [], []
    for l in X0:
        ix = (X1[l].double() - X0[l].double()).flatten()
        it = (T1[l].double() - T0[l].double()).flatten()
        nx, nt = float(ix.norm()), float(it.norm())
        rows[str(l)] = {'ratio': nx / nt if nt > 0 else None, 'cos': float(torch.dot(ix, it)) / (nx * nt) if nx * nt > 0 else None}
        ax.append(ix)
        at.append(it)
    ix, it = torch.cat(ax), torch.cat(at)
    nx, nt = float(ix.norm()), float(it.norm())
    return {'layers': rows, 'ratio_all': nx / nt if nt > 0 else None, 'cos_all': float(torch.dot(ix, it)) / (nx * nt) if nx * nt > 0 else None}


# ---------------------------------------------------------------- aggregation

def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def seq(vals, scen, ids=None):
    """Scenario-equal mean of vals over ids (list, may repeat)."""
    ids = list(vals) if ids is None else ids
    by = {}
    for i in ids:
        by.setdefault(scen[i], []).append(vals[i])
    return mean(mean(v) for _s, v in sorted(by.items()))


def boot_draws(ids, scen, n=BOOT_N, seed=SEED):
    """Shared resampled index lists (within scenario, with replacement)."""
    by = {}
    for i in sorted(ids):
        by.setdefault(scen[i], []).append(i)
    rng = random.Random(seed)
    return [[rng.choice(v) for _s, v in sorted(by.items()) for _ in v] for _ in range(n)]


def interval(xs):
    xs = sorted(xs)
    n = len(xs)
    return [xs[int(0.025 * n)], xs[int(0.975 * n) - 1]]


def H_of(M, r, arm, ids):
    """Per-input H(r, arm); M[(r, arm, b)][i], arm 'Z' = receiver base B(r,0,b)."""
    return {i: (M[(r, arm, '1')][i] - M[(r, 'Z', '1')][i]) - (M[(r, arm, '0')][i] - M[(r, 'Z', '0')][i]) for i in ids}


def ratio_stat(num, den, scen, ids, draws):
    """Point ratio of scenario-equal means and its bootstrap interval (None if the point denominator < D_MIN or any draw <= 0)."""
    n0, d0 = seq(num, scen, ids), seq(den, scen, ids)
    out = {'num': n0, 'den': d0, 'phi': None, 'interval': None, 'interval_available': False}
    if d0 is None or d0 < D_MIN:
        return out
    out['phi'] = n0 / d0
    rs, bad = [], 0
    for dr in draws:
        dd = seq(den, scen, dr)
        if dd <= 0:
            bad += 1
            continue
        rs.append(seq(num, scen, dr) / dd)
    if bad == 0:
        out['interval'], out['interval_available'] = interval(rs), True
    out['bad_draws'] = bad
    return out


def diff_interval(vals, scen, ids, draws):
    return {'eq': seq(vals, scen, ids), 'interval': interval([seq(vals, scen, dr) for dr in draws])}


def receiver_block(M, r, scen, ids, draws, extra_arms=()):
    """All read-outs for one receiver: H per arm, D_src, Phi_up / Phi_dn (+ extra arms like UP), residuals, per-b paired differences."""
    arms = ('0', '1', 'UP', 'DN') + tuple(extra_arms)
    H = {a: H_of(M, r, a, ids) for a in arms}
    D = {i: H['1'][i] - H['0'][i] for i in ids}
    out = {'H': {a: diff_interval(H[a], scen, ids, draws) for a in arms}, 'D_src': diff_interval(D, scen, ids, draws)}
    out['phi_up'] = ratio_stat({i: H['UP'][i] - H['0'][i] for i in ids}, D, scen, ids, draws)
    out['phi_dn'] = ratio_stat({i: H['1'][i] - H['DN'][i] for i in ids}, D, scen, ids, draws)
    for a in extra_arms:
        out[f'phi_{a}'] = ratio_stat({i: H[a][i] - H['0'][i] for i in ids}, D, scen, ids, draws)
        out[f'diff_{a}_minus_UP'] = diff_interval({i: H[a][i] - H['UP'][i] for i in ids}, scen, ids, draws)
    out['R_up'] = diff_interval({i: H['UP'][i] - H['1'][i] for i in ids}, scen, ids, draws)
    out['R_dn'] = diff_interval({i: H['DN'][i] - H['0'][i] for i in ids}, scen, ids, draws)
    out['paired_cells'] = {f'UP-1|b{b}': diff_interval({i: M[(r, 'UP', b)][i] - M[(r, '1', b)][i] for i in ids}, scen, ids, draws)
                           for b in '01'}
    out['paired_cells'].update({f'DN-0|b{b}': diff_interval({i: M[(r, 'DN', b)][i] - M[(r, '0', b)][i] for i in ids}, scen, ids, draws)
                                for b in '01'})
    out['cells'] = {f'{a}|b{b}': seq(M[(r, a, b)], scen, ids) for a in ('Z',) + arms for b in '01'}
    out['_H'] = H
    out['_D'] = D
    return out


def background(rb0, rb1, scen, ids, draws, which):
    """Phi(r=0) - Phi(r=1) with a paired bootstrap on the same draws; label when |diff| >= BG and the interval excludes 0."""
    a, b = rb0[which], rb1[which]
    if a['phi'] is None or b['phi'] is None:
        return {'available': False}
    num0 = {i: (rb0['_H']['UP'][i] - rb0['_H']['0'][i]) if which == 'phi_up' else (rb0['_H']['1'][i] - rb0['_H']['DN'][i]) for i in ids}
    num1 = {i: (rb1['_H']['UP'][i] - rb1['_H']['0'][i]) if which == 'phi_up' else (rb1['_H']['1'][i] - rb1['_H']['DN'][i]) for i in ids}
    ds = []
    for dr in draws:
        d0, d1 = seq(rb0['_D'], scen, dr), seq(rb1['_D'], scen, dr)
        if d0 <= 0 or d1 <= 0:
            return {'available': True, 'diff': a['phi'] - b['phi'], 'interval': None, 'label': False, 'note': 'denominator <= 0 in a draw'}
        ds.append(seq(num0, scen, dr) / d0 - seq(num1, scen, dr) / d1)
    iv = interval(ds)
    diff = a['phi'] - b['phi']
    return {'available': True, 'diff': diff, 'interval': iv, 'label': abs(diff) >= BG and (iv[0] > 0 or iv[1] < 0)}


def reading(up, dn, is_up=None, is_dn=None):
    """Frozen reading (CONTRACT §5) for one direction x receiver.  up / dn: ratio_stat dicts.  is_*: concatenated I_S ratio (median over
    inputs) of the arm, annotated when outside IS_BAND for an arm whose Phi is low."""
    if up['phi'] is None or dn['phi'] is None:
        return {'label': 'unscaled', 'flags': []}
    pu, pd = up['phi'], dn['phi']
    flags = []
    if pu > NEAR_HI or pd > NEAR_HI:
        flags.append('overcompensation')
    if pu < 0 or pd < 0:
        flags.append('reversed')
    lo = lambda s: s['interval'][0] if s['interval_available'] else None   # noqa: E731
    hi = lambda s: s['interval'][1] if s['interval_available'] else None   # noqa: E731
    if (pu >= NEAR_LO and pd <= LOW) or (pd >= NEAR_LO and pu <= LOW):
        label = 'one_sided'
    elif NEAR_LO <= pu <= NEAR_HI and NEAR_LO <= pd <= NEAR_HI and lo(up) is not None and lo(dn) is not None and lo(up) >= LOW and lo(dn) >= LOW:
        label = 'near_reference'
    elif any(s['phi'] <= LOW and hi(s) is not None and hi(s) < NEAR_LO for s in (up, dn)):
        label = 'insufficient'
    elif 'overcompensation' in flags:
        label = 'overcompensation'
    else:
        label = 'partial'
    for name, s, isr in (('UP', up, is_up), ('DN', dn, is_dn)):
        if s['phi'] <= LOW and isr is not None and not (IS_BAND[0] <= isr <= IS_BAND[1]):
            flags.append(f'IS_unmatched_{name}')
    return {'label': label, 'flags': flags, 'phi_up': pu, 'phi_dn': pd}


def y_block(Y, r, ids, scen, stopped):
    """Y[(r, arm, b)][i] in {0,1}.  Totals, per-b changes vs Z, fixed-b count differences (UP vs '1', DN vs '0'), H_Y, live subset."""
    arms = ('Z', '0', '1', 'UP', 'DN')
    tot = {f'{a}|b{b}': sum(Y[(r, a, b)][i] for i in ids) for a in arms for b in '01'}
    ch = {}
    for a in ('0', '1', 'UP', 'DN'):
        for b in '01':
            d = {i: Y[(r, a, b)][i] - Y[(r, 'Z', b)][i] for i in ids}
            ch[f'{a}|b{b}'] = {'net': sum(d.values()), 'toward': sum(v > 0 for v in d.values()), 'away': sum(v < 0 for v in d.values())}
    fixed = {}
    for a, t in (('UP', '1'), ('DN', '0')):
        for b in '01':
            d = {i: Y[(r, a, b)][i] - Y[(r, t, b)][i] for i in ids}
            fixed[f'{a}-{t}|b{b}'] = {'net': sum(d.values()), 'plus': sum(v > 0 for v in d.values()), 'minus': sum(v < 0 for v in d.values())}
    hy = {a: sum((Y[(r, a, '1')][i] - Y[(r, 'Z', '1')][i]) - (Y[(r, a, '0')][i] - Y[(r, 'Z', '0')][i]) for i in ids) for a in ('0', '1', 'UP', 'DN')}
    keep = [i for i in ids if i not in stopped[(r, '0')] and i not in stopped[(r, '1')]]
    return {'totals': tot, 'changes_vs_Z': ch, 'fixed_b_count_diff': fixed, 'H_Y': hy, 'n_live': len(keep),
            'H_Y_live': {a: sum((Y[(r, a, '1')][i] - Y[(r, 'Z', '1')][i]) - (Y[(r, a, '0')][i] - Y[(r, 'Z', '0')][i]) for i in keep)
                         for a in ('0', '1', 'UP', 'DN')}}
