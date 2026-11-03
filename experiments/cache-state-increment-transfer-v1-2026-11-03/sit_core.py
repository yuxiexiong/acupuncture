"""SIT-01 core (CPU-testable): the state-increment transplant and the frozen read-outs (CONTRACT §3–§4).

Cells.  NVB B(c, a, b): c = v of the t1 output (0 native v0, 1 restored v1), a = v of the stored state, b = write key (0 k0, 1 k1).
S(c, a, b) = G-layer recurrent state after the whole t1.  Increment of the storage operation from background s:
    dS(s, b) = S(s, 1, b) - S(s, 0, b)
Transplant into receiver r (after t1, before t2, all 14 G layers, nothing else changed):
    S*(r <- s, b) = S(r, 0, b) + dS(s, b)          (FP64 sum, one cast back to the cache dtype)
r == s reproduces B(r, 1, b) (old cell, reused); the new conditions are (r, s) = (0, 1) and (1, 0) for b = 0 / 1.

Read-outs (continuous only; no success / failure labels, CONTRACT §4).  M = C-route t2 margin, per input:
    F(r, s, b) = M of the transplant run (F(r, r, b) = M(B(r, 1, b))),  Z(r, b) = M(B(r, 0, b))
    H(r, s) = [F(r,s,1) - Z(r,1)] - [F(r,s,0) - Z(r,0)]     (H(0,0) = DS0, H(1,1) = DS1 of NVB)
    A0 = H(0,1) - H(0,0)      A1 = H(1,1) - H(1,0)      G = H(1,1) - H(0,0) = DS1 - DS0
Aggregation: per input, then six scenarios equally weighted; per-scenario means and signs; per-input signs; a scenario-stratified bootstrap
interval (descriptive, fixed seed).  Ratios A0/G and A1/G only when the scenario-equal G >= 0.5 (else None).  Main subset: target not first
listed (32); all 48 and the first-listed 16 supplementary.  Y (natural full-correct, all 48) uses the same differences, plus the subset whose
receiver t1 token did not stop."""
import random

G_MIN = 0.5            # ratio guard (as NVB rho)
BOOT_N = 2000
BOOT_SEED = 20261103
NEW = ('01', '10')     # (r, s) of the new conditions
PAIRS = ('00', '01', '10', '11')


def transplant_state(base, src1, src0):
    """S(r,0,b) + [S(s,1,b) - S(s,0,b)] in FP64, cast once to base.dtype.  Returns (new, exact_fp64, normalised cast error)."""
    import torch
    assert base.shape == src1.shape == src0.shape and base.dtype == src1.dtype == src0.dtype
    exact = base.double() + (src1.double() - src0.double())
    new = exact.to(base.dtype)
    err = float((new.double() - exact).abs().max() / max(float(exact.abs().max()), 1e-30))
    return new.contiguous(), exact, err


def increment_stats(S, G):
    """Per G layer: ||dS(s, b)|| (s, b in 0/1, Frobenius over heads), cos(dS(0,b), dS(1,b)), ||I_S(s)|| = ||dS(s,1) - dS(s,0)||,
    cos(I_S(0), I_S(1)).  S[cell][layer] float tensors."""
    import torch
    rows = {}
    for l in G:
        d = {(s, b): (S[f'{s}1{b}'][l].double() - S[f'{s}0{b}'][l].double()).flatten() for s in '01' for b in '01'}
        cos = lambda x, y: float(torch.dot(x, y) / max(float(x.norm() * y.norm()), 1e-300))   # noqa: E731
        I = {s: d[(s, '1')] - d[(s, '0')] for s in '01'}
        rows[str(l)] = {**{f'norm_dS_s{s}_b{b}': float(d[(s, b)].norm()) for s in '01' for b in '01'},
                        **{f'cos_dS_b{b}': cos(d[('0', b)], d[('1', b)]) for b in '01'},
                        **{f'norm_IS_s{s}': float(I[s].norm()) for s in '01'}, 'cos_IS': cos(I['0'], I['1'])}
    return rows


# ---------------------------------------------------------------- aggregation

def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def smeans(vals, scen):
    out = {}
    for i, v in vals.items():
        out.setdefault(scen[i], []).append(v)
    return {s: sum(x) / len(x) for s, x in sorted(out.items())}


def boot(vals, scen, n=BOOT_N, seed=BOOT_SEED):
    """Scenario-stratified bootstrap of the scenario-equal mean (inputs resampled within scenario).  Descriptive 2.5 / 97.5 percentiles."""
    by = {}
    for i in sorted(vals):
        by.setdefault(scen[i], []).append(vals[i])
    rng = random.Random(seed)
    draws = []
    for _ in range(n):
        draws.append(mean(mean(rng.choice(v) for _ in v) for _s, v in sorted(by.items())))
    draws.sort()
    return [draws[int(0.025 * n)], draws[int(0.975 * n) - 1]]


def describe(vals, scen):
    """Continuous description of a per-input quantity: scenario-equal mean, scenario means, signs, bootstrap interval."""
    if not vals:
        return None
    sm = smeans(vals, scen)
    return {'eq': mean(sm.values()), 'scen': sm, 'scen_pos': sum(1 for v in sm.values() if v > 0), 'scen_neg': sum(1 for v in sm.values() if v < 0),
            'n': len(vals), 'inp_pos': sum(1 for v in vals.values() if v > 0), 'inp_neg': sum(1 for v in vals.values() if v < 0),
            'boot95': boot(vals, scen)}


def per_input(M, ids):
    """M[(r, s, b)][i] with (r, s, b) strings; M[(r, '-', b)] = Z(r, b).  Returns per-input dicts H(r,s), A0, A1, G and per-b effects."""
    eff = {f'{r}{s}{b}': {i: M[(r, s, b)][i] - M[(r, '-', b)][i] for i in ids} for r in '01' for s in '01' for b in '01'}
    H = {f'{r}{s}': {i: eff[f'{r}{s}1'][i] - eff[f'{r}{s}0'][i] for i in ids} for r in '01' for s in '01'}
    A0 = {i: H['01'][i] - H['00'][i] for i in ids}
    A1 = {i: H['11'][i] - H['10'][i] for i in ids}
    Gp = {i: H['11'][i] - H['00'][i] for i in ids}
    return eff, H, A0, A1, Gp


def ratio(num, den):
    return num / den if (den is not None and den >= G_MIN) else None


def margins_block(M, scen, ids):
    ids = sorted(ids)
    if not ids:
        return None
    eff, H, A0, A1, Gp = per_input(M, ids)
    sc = {i: scen[i] for i in ids}
    out = {'H': {k: describe(v, sc) for k, v in H.items()}, 'A0': describe(A0, sc), 'A1': describe(A1, sc), 'G': describe(Gp, sc),
           'effects': {k: describe(v, sc) for k, v in eff.items()},
           'cells': {f'{r}{s}{b}': mean(M[(r, s, b)][i] for i in ids) for r in '01' for s in '01-' for b in '01'}}
    g = out['G']['eq']
    out['ratio_A0_G'] = ratio(out['A0']['eq'], g)
    out['ratio_A1_G'] = ratio(out['A1']['eq'], g)
    out['interaction_A1_minus_A0'] = describe({i: A1[i] - A0[i] for i in ids}, sc)
    out['per_input'] = {'A0': A0, 'A1': A1, 'G': Gp}
    return out


def y_block(Y, scen, ids, stopped):
    """Y[(r, s, b)][i] in {0, 1}.  stopped[(r, b)] = set of inputs whose receiver t1 token is a stop token (cannot change).
    Counts per cell, per-b changes (toward / away), H_Y, A0_Y, A1_Y totals; and the same restricted to receiver-not-stopped inputs."""
    ids = sorted(ids)
    tot = {f'{r}{s}{b}': sum(Y[(r, s, b)][i] for i in ids) for r in '01' for s in '01-' for b in '01'}
    ch = {}
    for r in '01':
        for s in '01':
            for b in '01':
                dif = {i: Y[(r, s, b)][i] - Y[(r, '-', b)][i] for i in ids}
                ch[f'{r}{s}{b}'] = {'net': sum(dif.values()), 'toward': sum(1 for v in dif.values() if v > 0), 'away': sum(1 for v in dif.values() if v < 0),
                                    'n_scen_toward': len({scen[i] for i, v in dif.items() if v > 0})}
    hy = {f'{r}{s}': sum((Y[(r, s, '1')][i] - Y[(r, '-', '1')][i]) - (Y[(r, s, '0')][i] - Y[(r, '-', '0')][i]) for i in ids) for r in '01' for s in '01'}
    live = {}
    for r in '01':
        keep = [i for i in ids if i not in stopped[(r, '0')] and i not in stopped[(r, '1')]]
        live[r] = {'n': len(keep), 'n_stopped_b0': sum(1 for i in ids if i in stopped[(r, '0')]), 'n_stopped_b1': sum(1 for i in ids if i in stopped[(r, '1')]),
                   'H_Y': {s: sum((Y[(r, s, '1')][i] - Y[(r, '-', '1')][i]) - (Y[(r, s, '0')][i] - Y[(r, '-', '0')][i]) for i in keep) for s in '01'},
                   'totals': {f'{s}{b}': sum(Y[(r, s, b)][i] for i in keep) for s in '01-' for b in '01'}}
    return {'n': len(ids), 'totals': tot, 'changes': ch, 'H_Y': hy, 'A0_Y': hy['01'] - hy['00'], 'A1_Y': hy['11'] - hy['10'], 'receiver_live': live}
