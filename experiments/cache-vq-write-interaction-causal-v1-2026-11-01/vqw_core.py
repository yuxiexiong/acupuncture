"""CFM-VQ-WRITE-L13-v1 pure CPU pieces (plan docs/cache-vq-write-interaction-causal-plan-v1-2026-11-01 r2).

- I13 = n_TT - n_TC - n_CT + n_CC at layer 13 (n = beta v (k^T q), kernel conventions of lr_core.weights), and the
  product form beta (v_T - v_C) [(k_T^T q_T) - (k_C^T q_C)] under the four-corner dependence checks (plan §3.3).
- Patch precision gates (plan §7.4 r2), random references (§4), estimands and scenario rules (§5, §6).
"""
import hashlib
import math
import statistics

TAG = 'CFM-VQ-WRITE-L13-v1'
CORNERS = ('CC', 'CT', 'TC', 'TT')             # (Q, V)
BG_CELLS = {'M_T': {'CC': 'M:TCC', 'CT': 'M:TCT', 'TC': 'M:TTC', 'TT': 'M:TTT'},
            'N': {'CC': 'N:CC', 'CT': 'N:CT', 'TC': 'N:TC', 'TT': 'N:TT'}}
RULE = {'overall': 0.05, 'head_floor_ratio': 1.05, 'resolve_factor': 20.0, 'unresolved_energy_max': 0.02,
        'min_abs_I': 1.0, 'kappa_max': 0.75, 'margin': 0.1, 'min_scen': 5, 'n_scen': 6,
        'small_rho': 0.1, 'small_delta': 0.1, 'ident_abs': 1e-12, 'ident_rel': 1e-10}


def _norm_qk(row):
    import torch
    q, k = row['q'].double(), row['k'].double()
    q = q * torch.rsqrt(q.square().sum(-1, keepdim=True) + 1e-6) / q.shape[-1] ** .5
    k = k * torch.rsqrt(k.square().sum(-1, keepdim=True) + 1e-6)
    return q, k


def write_term(row):
    q, k = _norm_qk(row)
    return row['beta'].double()[:, None] * row['v'].double() * (k * q).sum(-1)[:, None]


def read_weights(row):
    q, k = _norm_qk(row)
    kq = (k * q).sum(-1)
    b = row['beta'].double()
    return row['g'].double().exp()[:, None] * (q - b[:, None] * k * kq[:, None])


def i13(rows, s_old):
    """rows: corner -> layer-13 driver dict (q, k, v, g, beta, z, core, ...); s_old [H, dk, dv] (shared S_T).
    Returns I13 (four-corner), product-form I13, dependence checks, read-term interaction and core reconstruction."""
    import torch
    eq = lambda a, b, f: torch.equal(rows[a][f], rows[b][f])   # noqa: E731
    checks = {
        'g_beta_z_shared': all(eq('CC', c, f) for c in CORNERS for f in ('g', 'beta', 'z')),
        'qk_depend_only_on_Q': all(eq(a, b, f) for a, b in (('CC', 'CT'), ('TC', 'TT')) for f in ('q', 'k')),
        'v_depends_only_on_V': all(eq(a, b, 'v') for a, b in (('CC', 'TC'), ('CT', 'TT'))),
    }
    n = {c: write_term(rows[c]) for c in CORNERS}
    I = n['TT'] - n['TC'] - n['CT'] + n['CC']
    qT, kT = _norm_qk(rows['TT'])
    qC, kC = _norm_qk(rows['CC'])
    beta = rows['TT']['beta'].double()[:, None]
    prod = beta * (rows['TT']['v'].double() - rows['CC']['v'].double()) * ((kT * qT).sum(-1) - (kC * qC).sum(-1))[:, None]
    r = {c: torch.einsum('hiv,hi->hv', s_old.double(), read_weights(rows[c])) for c in CORNERS}
    rI = r['TT'] - r['TC'] - r['CT'] + r['CC']
    tol = RULE['ident_abs'] + RULE['ident_rel'] * float(I.norm())
    checks['product_identity_residual'] = float((I - prod).norm())
    checks['product_identity_ok'] = checks['product_identity_residual'] <= tol
    checks['read_interaction_norm'] = float(rI.norm())
    checks['read_interaction_ok'] = checks['read_interaction_norm'] <= tol
    checks['saved_new_vs_rebuilt_max'] = max(float((rows[c]['new'].double() - n[c]).abs().max()) for c in CORNERS)
    recon = {}
    for c in CORNERS:
        o = r[c] + n[c]
        recon[c] = recon_check(o, rows[c]['core'])
    checks['core_recon'] = recon
    checks['core_recon_ok'] = all(v['ok'] for v in recon.values())
    return I, checks


def recon_check(o, core):
    """Same rule as CONV contract r02: error <= 1.05 x BF16 rounding floor of the exact value."""
    import torch
    o = o.double()
    err = float((o - core.double()).norm()) / max(float(core.double().norm()), 1e-300)
    floor = float((o.to(torch.bfloat16).double() - o).norm()) / max(float(o.norm()), 1e-300)
    ratio = err / floor if floor > 0 else (0.0 if err == 0 else math.inf)
    return {'err': err, 'floor': floor, 'ratio': ratio, 'ok': ratio <= 1.05}


# ---------------------------------------------------------------- patch precision (plan §7.4 r2)

def patch_core(core, delta, addback=False):
    c = core.double()
    d = delta.to(device=core.device, dtype=c.dtype)
    return ((c - d + d) if addback else (c - d)).to(core.dtype)


def precision(core, delta):
    """core [H, dv] BF16 (actual kernel output), delta [H, dv] FP64 target. Simulates the run's patch and checks:
    overall relative L2 <= 5%; every head's actual error <= 1.05 x its BF16 floor; heads with target < 20 x floor hold
    <= 2% of the target energy."""
    import torch
    new = patch_core(core, delta)
    real = core.double() - new.double()
    d = delta.double()
    exact = core.double() - d
    floor_h = (exact.to(core.dtype).double() - exact).norm(dim=-1)
    err_h = (real - d).norm(dim=-1)
    hn = d.norm(dim=-1)
    tot = float(d.norm())
    overall = float((real - d).norm()) / tot if tot > 0 else (0.0 if float(real.norm()) == 0 else math.inf)
    impl_ok = bool((err_h <= RULE['head_floor_ratio'] * floor_h + 1e-15).all())
    unres = hn < RULE['resolve_factor'] * floor_h
    share = float((hn[unres] ** 2).sum() / (hn ** 2).sum()) if tot > 0 else 0.0
    res = ~unres & (hn > 0)
    res_err = float((err_h[res] / hn[res]).max()) if bool(res.any()) else 0.0
    zero_heads_untouched = bool((real[hn == 0] == 0).all())
    ok = overall <= RULE['overall'] and impl_ok and share <= RULE['unresolved_energy_max'] and zero_heads_untouched
    return {'overall_rel_err': overall, 'head_impl_ok': impl_ok, 'unresolved_energy_share': share,
            'n_unresolved_heads': int(unres.sum()), 'max_err_resolved_head': res_err,
            'zero_heads_untouched': zero_heads_untouched, 'ok': ok, 'new_core': new}


# ---------------------------------------------------------------- random references (plan §4)

def seed_of(item_id, j):
    return int(hashlib.sha256(f'{TAG}|{item_id}|{j}'.encode()).hexdigest()[:16], 16)


def random_like(item_id, j, target):
    """CPU FP32 Gaussian [32, 128], FP64 per-head unit, scaled to target's per-head L2 norm (zero heads -> zero)."""
    import torch
    g = torch.Generator().manual_seed(seed_of(item_id, j))
    u = torch.randn(tuple(target.shape), generator=g, dtype=torch.float32).double()
    u = u / u.norm(dim=-1, keepdim=True)
    return u * target.double().norm(dim=-1, keepdim=True)


# ---------------------------------------------------------------- estimands and rules (plan §5, §6)

def estimands(z_tt, z_del, z_tc, z_ct, z_cc):
    I = z_tt - z_tc - z_ct + z_cc
    Ip = z_del - z_tc - z_ct + z_cc
    d = z_tt - z_del
    rho = d / I if abs(I) >= RULE['min_abs_I'] else None
    return {'I': I, 'I_prime': Ip, 'delta': d, 'rho': rho, 'kappa': abs(1 - rho) if rho is not None else None,
            'identity_residual': (I - Ip) - d}


def label(rho, delta):
    if rho is None:
        return 'ratio_undecidable'
    if abs(rho) <= RULE['small_rho'] and abs(delta) <= RULE['small_delta']:
        return 'small_change'
    if rho < 0 or rho > 2:
        return 'reversed_or_amplified'
    if 1 < rho < 2:
        return 'overshoot_smaller'
    if rho == 2:
        return 'equal_and_opposite'
    return 'reduced'          # 0 <= rho <= 1 (0: unchanged, 1: interaction removed)


def scenario_rule(facts):
    """facts: two dicts with I, delta, d_rand0, d_rand1 (one scenario). Plan §5.2-5.3."""
    mI = statistics.mean(f['I'] for f in facts)
    md = statistics.mean(f['delta'] for f in facts)
    same_sign = all(f['I'] > 0 for f in facts) or all(f['I'] < 0 for f in facts)
    evaluable = abs(mI) >= RULE['min_abs_I'] and same_sign
    rho = md / mI if evaluable else None
    kappa = abs(1 - rho) if rho is not None else None
    E = [math.copysign(1.0, f['I']) * f['delta'] for f in facts]
    rnd = max(statistics.mean(abs(f[f'd_rand{j}']) for f in facts) for j in (0, 1))
    c1 = evaluable and kappa <= RULE['kappa_max'] and all(f['delta'] * f['I'] > 0 for f in facts)
    c2 = all(e > 0 for e in E) and statistics.mean(E) > rnd + RULE['margin']
    return {'mean_I': mI, 'mean_delta': md, 'rho': rho, 'kappa': kappa, 'evaluable': evaluable,
            'label': label(rho, md), 'support': bool(c1 and c2), 'cond_ratio': bool(c1), 'cond_random': bool(c2),
            'max_mean_abs_random': rnd}


def combine(scen):
    n = sum(v['support'] for v in scen.values())
    return {'n_support': n, 'n_evaluable': sum(v['evaluable'] for v in scen.values()),
            'label': 'stable_support' if n >= RULE['min_scen'] else 'not_stable_support'}
