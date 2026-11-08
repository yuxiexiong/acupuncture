"""NGC-01: source-blind cross-scenario gain targets and one-token write-use intervention.

No model loading. CPU tests use synthetic tensors, not research observations.
"""
import torch

G = (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'N_L00_C1343_D-1')
PRE = ('LVK-H-NA-NQ01-ABC-A', 'LVK-H-NA-NQ02-ABC-B')
CAP_SECONDS = {'preflight': 720, 'formal': 5760}


def positive(x):
    assert torch.isfinite(x).all() and (x > 0).all(), 'gain undefined: zero/nonfinite; no clipping allowed'


def profiles(gains, scenarios):
    """gains[item][C or direction]: [layer, head]; scenario means then leave-one-scenario-out.

    Uses only raw gains, no labels/answers. In preflight the other single scenario is engineering-only.
    """
    assert set(gains) == set(scenarios)
    groups = sorted(set(scenarios.values()))
    assert len(groups) >= 2
    means, result = {}, {}
    for d in DIRECTIONS:
        for s in groups:
            diffs = []
            for i in gains:
                if scenarios[i] == s:
                    c, t = gains[i]['C'].double(), gains[i][d].double()
                    positive(c); positive(t)
                    diffs.append(c.log() - t.log())
            means[s, d] = torch.stack(diffs).mean(0)
        for s in groups:
            result[s, d] = torch.stack([means[x, d] for x in groups if x != s]).mean(0)
    return result, means


def targets(native, profile, background):
    assert background in ('C', 'T')
    x = native.double()
    positive(x)
    p = x * ((-1 if background == 'C' else 1) * profile.double()).exp()
    positive(p)
    u = x * (p.norm() / x.norm())
    p, u = p.float(), u.float()
    positive(p); positive(u)
    assert torch.allclose(p.double().norm(), u.double().norm(), rtol=2e-6, atol=0)
    return p, u


def update(original, l2norm, query, key, value, g, beta, initial_state,
           output_final_state=False, use_qk_l2norm_in_kernel=False, target=None, **kw):
    """Call native kernel in original order, then add only the specified write-use difference.

    target is [head] or [batch, head]. 'g' in the upstream signature is log decay,
    distinct from effective gain beta*||normalized_key||. E retains native beta and key.
    """
    assert query.shape[1] == 1 and initial_state is not None
    out, state = original(query, key, value, g=g, beta=beta, initial_state=initial_state,
                          output_final_state=True, use_qk_l2norm_in_kernel=use_qk_l2norm_in_kernel, **kw)
    q, k, v = [x[:, 0].float() for x in (query, key, value)]
    raw_knorm = k.norm(dim=-1)
    if use_qk_l2norm_in_kernel:
        q, k = l2norm(q, dim=-1, eps=1e-6), l2norm(k, dim=-1, eps=1e-6)
    q = q / (q.shape[-1] ** 0.5)
    b, alpha = beta[:, 0].float(), g[:, 0].float().exp()
    knorm = k.norm(dim=-1)
    actual = b * knorm
    positive(actual)
    wanted = actual if target is None else target.to(device=actual.device, dtype=torch.float32).reshape_as(actual)
    positive(wanted)
    u = k / knorm.unsqueeze(-1)
    # Exact identity uses the original result; avoids a numerically redundant output recomputation.
    if not torch.equal(wanted, actual):
        state = state + ((wanted - actual).unsqueeze(-1) * u).unsqueeze(-1) * v.unsqueeze(-2)
        out = (state * q.unsqueeze(-1)).sum(-2).unsqueeze(1).to(query.dtype)
    # Independent FP64 decomposition checks both persistent state and current output.
    kd, vd, qd = k.double(), v.double(), q.double()
    D = initial_state.double() * alpha.double()[..., None, None]
    E = -b.double()[..., None, None] * kd.unsqueeze(-1) * (D * kd.unsqueeze(-1)).sum(-2).unsqueeze(-2)
    W = wanted.double()[..., None, None] * u.double().unsqueeze(-1) * vd.unsqueeze(-2)
    oracle = D + E + W
    err_s = float((state.double() - oracle).abs().max() / max(1., float(oracle.abs().max())))
    # Compare FP32 state readout before BF16 rounding; BF16 output is separately checked exactly.
    read = (state * q.unsqueeze(-1)).sum(-2)
    oracle_o = (oracle * qd.unsqueeze(-1)).sum(-2)
    err_o = float((read.double() - oracle_o).abs().max() / max(1., float(oracle_o.abs().max())))
    assert max(err_s, err_o) <= 1e-5, ('FP64 write oracle', err_s, err_o)
    assert torch.equal(out[:, 0], read.to(out.dtype)), 'output and persistent state disagree'
    fields = {'beta': b, 'alpha': alpha, 'k': k, 'q': q, 'v': v, 'k_norm_raw': raw_knorm,
              'k_norm': knorm, 'v_norm': v.norm(dim=-1), 'gain_actual': actual, 'gain_target': wanted,
              'D_read': (D * qd.unsqueeze(-1)).sum(-2), 'E_read': (E * qd.unsqueeze(-1)).sum(-2),
              'W_read': ((actual.double()[..., None, None] * u.double().unsqueeze(-1) * vd.unsqueeze(-2)) * qd.unsqueeze(-1)).sum(-2),
              'W_target_read': (W * qd.unsqueeze(-1)).sum(-2)}
    record = {name: tensor.detach().float().cpu() for name, tensor in fields.items()}
    record['oracle_error'] = max(err_s, err_o)
    return out, state if output_final_state else None, record


def limits(stage):
    assert stage in CAP_SECONDS
    n = 2 if stage == 'preflight' else 48
    refs = 10 if stage == 'preflight' else 0
    return dict(prefix_prefills=2*n, formations=10*n,
                formation_token_forwards=600 if n == 2 else 12780,
                t1=21*n, refs=refs, n_steps=21*n*31, c_t2=21*n,
                decode_forwards=21*n*33+refs, trajectories=21*n, shadow=0)


def difference(a, b, scenarios, binary=False):
    assert set(a) == set(b) == set(scenarios)
    by = {s: [a[i]-b[i] for i in a if scenarios[i] == s] for s in sorted(set(scenarios.values()))}
    sm = {s: sum(v)/len(v) for s,v in by.items()}
    out = {'scenario_means': sm, 'scenario_equal_mean': sum(sm.values())/len(sm),
           'paired': {i: a[i]-b[i] for i in a}}
    if binary:
        fixed = [i for i in a if a[i] == 1 and b[i] == 0]
        broken = [i for i in a if a[i] == 0 and b[i] == 1]
        out.update(fixed=fixed, broken=broken, net=len(fixed)-len(broken),
                   multi_scenario=len(fixed)-len(broken) >= 2 and len({scenarios[i] for i in fixed}) >= 2
                   and out['scenario_equal_mean'] > 0)
    return out
