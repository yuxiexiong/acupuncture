"""CFM-LOCAL-READOUT v1: pure CPU pieces (no model import). Plan docs/cache-local-readout-causal-plan-v1-2026-11-01 r3.

- GDN read-out algebra at one layer (plan §5): o(S,F;x) = S^T w(F;x) + n(F;x).
- Four local cells, I = o11 - o10 - o01 + o00 = dS^T dw, J = o11 - o00, A_S, A_F (§5, §7.2).
- Random reference directions (§6) and the output-edge patch arithmetic (§6, §10.4 r3: FP64 then one cast).
- Frozen tiers (§8.1) and scenario aggregation used by the analysis.
"""
import hashlib
import math
import statistics

LAYER = 13
TOL = {'identity_rel': 1e-10, 'identity_abs': 1e-12, 'core_recon_rel': 5e-3, 'deletion_rel': 0.05, 'ratio_den_min': 1.0}
TIER = {'count_min': 5, 'n_scen': 6, 'median_min': 0.05}
SEED_TAG = 'CFM-LOCAL-READOUT-v1'


# ---------------------------------------------------------------- algebra

def weights(row):
    """w = alpha [q - beta k (k^T q)], n = beta v (k^T q); q/k l2-normalised as the kernel does, q scaled by 1/sqrt(d).
    row: recorded kernel inputs of one layer (q, k, v [H, d]; g, beta [H])."""
    import torch
    q, k = row['q'].double(), row['k'].double()
    q = q * torch.rsqrt(q.square().sum(-1, keepdim=True) + 1e-6) / q.shape[-1] ** .5
    k = k * torch.rsqrt(k.square().sum(-1, keepdim=True) + 1e-6)
    kq = (k * q).sum(-1)
    b = row['beta'].double()
    w = row['g'].double().exp()[:, None] * (q - b[:, None] * k * kq[:, None])
    n = b[:, None] * row['v'].double() * kq[:, None]
    return w, n


def read(s, w):
    import torch
    return torch.einsum('hiv,hi->hv', s.double(), w.double())


def rel(a, b):
    return float((a - b).norm() / max(float(b.norm()), 1e-300))


def four_cells(s_c, s_t, row_fc, row_ft):
    """Plan §5 for one background: row_fc = drivers with F_C, row_ft = drivers with F_T, same entry x.
    s_*: [H, dk, dv] recurrent states before the step. Returns FP64 tensors and checks."""
    import torch
    for name in ('g', 'beta'):
        assert torch.equal(row_fc[name], row_ft[name]), f'{name} differs between F_C and F_T drivers (entry x not shared)'
    w0, n0 = weights(row_fc)
    w1, n1 = weights(row_ft)
    o00, o10 = read(s_c, w0) + n0, read(s_t, w0) + n0
    o01, o11 = read(s_c, w1) + n1, read(s_t, w1) + n1
    I = o11 - o10 - o01 + o00
    direct = read(s_t.double() - s_c.double(), w1 - w0)
    J = o11 - o00
    a_s, a_f = o10 - o00, o01 - o00
    nd = float(direct.norm())
    ident = float((I - direct).norm())
    ident_ok = ident <= (TOL['identity_rel'] * nd if nd > 0 else TOL['identity_abs'])
    cos = float(torch.nn.functional.cosine_similarity(I.flatten(), (a_s + a_f).flatten(), dim=0)) \
        if float((a_s + a_f).norm()) > 0 and nd > 0 else None
    return {'I': I, 'J': J, 'A_S': a_s, 'A_F': a_f, 'o00': o00, 'o01': o01, 'o10': o10, 'o11': o11,
            'identity_abs': ident, 'identity_ok': bool(ident_ok),
            'J_split_residual': float((J - (a_s + a_f + I)).norm()),
            'norms': {'I': float(I.norm()), 'J': float(J.norm()), 'A_S': float(a_s.norm()), 'A_F': float(a_f.norm())},
            'cos_I_vs_AS_plus_AF': cos}


def core_recon(o, core):
    """Relative error of the FP64 rebuild against the actual BF16 core (plan §10.3, <= 0.005)."""
    return rel(o, core.double())


# ---------------------------------------------------------------- random references

def seed_of(item_id, k):
    return int(hashlib.sha256(f'{SEED_TAG}|{item_id}|{k}'.encode()).hexdigest()[:16], 16)


def unit_dirs(item_id, k, shape=(32, 128)):
    """FP32 standard normal on a CPU generator (plan §6), normalised per head in FP64 so matched norms are exact."""
    import torch
    gen = torch.Generator().manual_seed(seed_of(item_id, k))
    u = torch.randn(shape, generator=gen, dtype=torch.float32).double()
    return u / u.norm(dim=-1, keepdim=True)


def match_heads(u, target):
    """Scale unit rows to the per-head L2 norm of target; zero-norm heads -> zero (no orthogonalisation)."""
    nrm = target.double().norm(dim=-1, keepdim=True)
    return u.double() * nrm


# ---------------------------------------------------------------- patch arithmetic

def patch_core(core, delta, addback=False):
    """core - delta (or core - delta + delta) in FP64, one cast back to core dtype. BF16 values are exact in FP64."""
    c = core.double()
    d = delta.to(device=core.device, dtype=c.dtype)
    new = (c - d + d) if addback else (c - d)
    return new.to(core.dtype)


def realized(core, new, delta):
    """Actual deletion core - new vs intended delta: relative L2 error overall and worst head."""
    real = core.double() - new.double()
    d = delta.double().to(real.device)
    nd = float(d.norm())
    if nd == 0:
        rn = float(real.norm())
        return {'delta_norm': 0.0, 'realized_norm': rn, 'rel_err': 0.0 if rn == 0 else math.inf, 'head_rel_err_max': 0.0}
    hn = d.norm(dim=-1)
    he = (real - d).norm(dim=-1)
    mask = hn > 0
    return {'delta_norm': nd, 'realized_norm': float(real.norm()), 'rel_err': float((real - d).norm()) / nd,
            'head_rel_err_max': float((he[mask] / hn[mask]).max()) if bool(mask.any()) else 0.0}


# ---------------------------------------------------------------- read-outs and frozen tiers (plan §7, §8.1)

def null_tail(count_min=TIER['count_min'], n=TIER['n_scen'], p=1 / 3):
    return sum(math.comb(n, j) * p ** j * (1 - p) ** (n - j) for j in range(count_min, n + 1))


def scenario_means(per_item, key_of):
    """per_item: {item_id: value}; key_of: item_id -> scenario. Mean of the two facts per scenario."""
    out = {}
    for item, v in per_item.items():
        out.setdefault(key_of[item], []).append(v)
    for s, v in out.items():
        assert len(v) == 2, (s, len(v))
    return {s: sum(v) / len(v) for s, v in sorted(out.items())}


def ratios(delta, gap):
    return {s: (delta[s] / gap[s] if abs(gap[s]) >= TOL['ratio_den_min'] else None) for s in delta}


def tier_I(dI, dQ0, dQ1, gap):
    """Plan §8.1. dI/dQ*/gap: scenario -> value. Returns label and the counts it was decided on."""
    scen = sorted(dI)
    assert len(scen) == TIER['n_scen'] and sorted(dQ0) == sorted(dQ1) == sorted(gap) == scen, scen
    rho = ratios(dI, gap)
    vals = [rho[s] for s in scen if rho[s] is not None]
    med = statistics.median(vals) if vals else None
    med_abs = statistics.median([abs(v) for v in vals]) if vals else None
    n_pos = sum(dI[s] > 0 for s in scen)
    n_neg = sum(dI[s] < 0 for s in scen)
    e = sum(abs(dI[s]) > max(abs(dQ0[s]), abs(dQ1[s])) for s in scen)
    m = TIER['count_min']
    if med is not None and e >= m and n_pos >= m and med >= TIER['median_min']:
        label = 'clear_push'
    elif med is not None and e >= m and n_neg >= m and med <= -TIER['median_min']:
        label = 'clear_suppress'
    elif med_abs is None or med_abs < TIER['median_min']:
        label = 'weak'
    else:
        label = 'nonspecific_or_unstable'
    return {'label': label, 'n_pos': n_pos, 'n_neg': n_neg, 'exceed_both_random': e, 'median_ratio': med,
            'median_abs_ratio': med_abs, 'n_ratio': len(vals), 'ratios': rho}


def tier_J(dJ, gap):
    scen = sorted(dJ)
    assert len(scen) == TIER['n_scen'] and sorted(gap) == scen, scen
    rho = ratios(dJ, gap)
    vals = [rho[s] for s in scen if rho[s] is not None]
    med_abs = statistics.median([abs(v) for v in vals]) if vals else None
    n_pos = sum(dJ[s] > 0 for s in scen)
    n_neg = sum(dJ[s] < 0 for s in scen)
    if med_abs is not None and max(n_pos, n_neg) >= TIER['count_min'] and med_abs >= TIER['median_min']:
        label = 'magnitude_clear_uncalibrated'
    elif med_abs is None or med_abs < TIER['median_min']:
        label = 'weak'
    else:
        label = 'unstable'
    return {'label': label, 'n_pos': n_pos, 'n_neg': n_neg, 'median_abs_ratio': med_abs, 'ratios': rho}


def background_contrast(tier_m, tier_n):
    clear = ('clear_push', 'clear_suppress')
    if tier_m in clear and tier_n == 'weak':
        return 'only_M'
    if tier_n in clear and tier_m == 'weak':
        return 'only_N'
    if tier_m in clear and tier_n in clear:
        return 'both_clear' + ('' if tier_m == tier_n else '_opposite')
    return 'no_background_claim'


def cell_readout(logits, stop_ids, s_b, u_b, r_x, r_ref):
    """Plan §7.1 per cell: D, fixed-pair L, fixed-denominator L, greedy token / EOS."""
    z = logits.double()
    non = z.clone()
    non[list(stop_ids)] = -math.inf
    d = float(z[list(stop_ids)].max() - non.max())
    lval = float(z[s_b] - z[u_b])
    tok = int(z.argmax())
    return {'D': d, 'L': lval, 'L_fixscale': lval * r_x / r_ref, 'token': tok, 'eos': tok in set(stop_ids),
            'stop_winner': int(stop_ids[int(z[list(stop_ids)].argmax())]), 'nonstop_winner': int(non.argmax())}
