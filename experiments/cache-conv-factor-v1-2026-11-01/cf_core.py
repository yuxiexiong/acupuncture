"""CFM-CONV-FACTOR v1: pure CPU pieces (no model import). Plan docs/cache-conv-value-qk-readout-plan-v1-2026-11-01 r2.

- conv_states [1, 8192, 4] split into q | k | V channel segments; Q = (q, k) joint (plan §3.2).
- Random displacement references (plan §4): seed 20261101 + 1000*j + crc32(input|segment), float64, layers ascending,
  per layer a [4 slots, heads, 128] normal draw, unit per (slot, head), scaled to the per-(slot, head) norm of C - T.
- Read-outs (plan §5.1), factorial effects (§5.2), frozen hypotheses (§6.1) and random rule (§6.2).
"""
import math
import statistics
import zlib

SEG = {'q': (0, 2048), 'k': (2048, 4096), 'v': (4096, 8192)}
HEADS = {'q': 16, 'k': 16, 'v': 32}
HD = 128
N_SLOTS = 4
CONSUMED = (1, 2, 3)          # causal_conv1d_update: cat([state(4), x]) -> width-4 conv, last output reads slots 1..3 + x
PART_SEGS = {'Q': ('q', 'k'), 'V': ('v',)}
STOP = (248044, 248046)
STOP_MAIN, THINK = 248046, 248068
SEED_BASE = 20261101
RULE = {'min_scen': 5, 'n_scen': 6, 'min_abs_G': 1.0, 'margin': 0.1, 'near_lo': 0.7, 'near_hi': 1.3, 'other_max': 0.3,
        'add_max': 0.2, 'transfer': (0.75, 1.33), 'disp_tol': 0.05, 'recon_floor_ratio': 1.05}


# ---------------------------------------------------------------- conv segments

def assemble(f_q, f_v):
    """F with channels 0:4096 (q, k) from f_q and 4096:8192 (V) from f_v; all 4 slots copied (plan §3.2)."""
    out = f_v.clone()
    out[:, :SEG['k'][1], :] = f_q[:, :SEG['k'][1], :]
    return out


def seg_view(f, seg):
    """[1, C, 4] -> [4 slots, heads, 128] for one segment (copy, float64)."""
    a, b = SEG[seg]
    return f[0, a:b, :].double().t().reshape(N_SLOTS, HEADS[seg], HD)


def seg_put(f, seg, x):
    """Inverse of seg_view: write [4, heads, 128] back into a clone of f (dtype of f)."""
    a, b = SEG[seg]
    out = f.clone()
    out[0, a:b, :] = x.reshape(N_SLOTS, HEADS[seg] * HD).t().to(f.dtype)
    return out


def seed_of(input_id, j, seg):
    return SEED_BASE + 1000 * j + zlib.crc32(f'{input_id}|{seg}'.encode())


def random_xi(input_id, j, seg, layers, diffs):
    """diffs: layer -> [4, heads, 128] float64 (C - T for this segment). Returns layer -> xi with per-(slot, head) norm
    equal to the diff's; zero-norm (slot, head) -> zero. One generator per (input, draw, segment), layers ascending."""
    import torch
    gen = torch.Generator().manual_seed(seed_of(input_id, j, seg))
    out = {}
    for layer in sorted(layers):
        u = torch.randn((N_SLOTS, HEADS[seg], HD), generator=gen, dtype=torch.float64)
        u = u / u.norm(dim=-1, keepdim=True)
        out[layer] = u * diffs[layer].norm(dim=-1, keepdim=True)
    return out


def displacement_check(f_t, f_new, seg, target):
    """Actual displacement on the consumed slots vs target (xi) norm on those slots; zero target must be untouched."""
    act = seg_view(f_new, seg) - seg_view(f_t, seg)
    sl = list(CONSUMED)
    tn = float(target[sl].norm())
    an = float(act[sl].norm())
    if tn == 0:
        return {'target': 0.0, 'actual': an, 'rel_err': 0.0 if an == 0 else math.inf, 'ok': an == 0}
    rel = abs(an - tn) / tn
    import torch
    cos = float(torch.nn.functional.cosine_similarity(act[sl].flatten(), target[sl].flatten(), dim=0))
    return {'target': tn, 'actual': an, 'rel_err': rel, 'cos_actual_target': cos, 'ok': rel <= RULE['disp_tol']}


# ---------------------------------------------------------------- read-outs

def readout(logits, a):
    """Plan §5.1: centered (minus vocabulary mean) and raw logits, log-probs for a, stops, think; derived margins; D."""
    import torch
    z = logits.double()
    mu = float(z.mean())
    lp = torch.log_softmax(z, -1)
    toks = {'a': a, 's46': STOP_MAIN, 's44': STOP[0], 'think': THINK}
    raw = {k: float(z[t]) for k, t in toks.items()}
    out = {'raw': raw, 'centered': {k: v - mu for k, v in raw.items()}, 'logprob': {k: float(lp[t]) for k, t in toks.items()},
           'vocab_mean': mu}
    non = z.clone()
    non[list(STOP)] = -math.inf
    out['D'] = float(z[list(STOP)].max() - non.max())
    out['derived'] = {'s46_minus_a': raw['s46'] - raw['a'], 'think_minus_a': raw['think'] - raw['a'],
                      's44_minus_a': raw['s44'] - raw['a'], 's46_minus_think': raw['s46'] - raw['think'], 'D': out['D']}
    out['primary'] = {'cz_a': out['centered']['a'], 'cz_s46': out['centered']['s46']}
    out['token'] = int(z.argmax())
    out['eos'] = out['token'] in STOP
    return out


def value(ro, m):
    """Read-out m of a cell: 'cz_a', 'cz_s46' (primary) or a derived name."""
    return ro['primary'][m] if m in ro['primary'] else ro['derived'][m]


# ---------------------------------------------------------------- factorial effects (plan §5.2)

def m_cell(s, q, v):
    return f'M:{s}{q}{v}'


def factorial(Z, bg):
    """Z: cell id -> scalar. bg in {'M_T', 'M_C', 'N'}. Returns G, A_V, R_V, A_Q, R_Q, I."""
    if bg == 'N':
        z = {(q, v): Z[f'N:{q}{v}'] for q in 'CT' for v in 'CT'}
    else:
        s = bg[-1]
        z = {(q, v): Z[m_cell(s, q, v)] for q in 'CT' for v in 'CT'}
    return {'G': z['T', 'T'] - z['C', 'C'],
            'A_V': z['C', 'T'] - z['C', 'C'], 'R_V': z['T', 'T'] - z['T', 'C'],
            'A_Q': z['T', 'C'] - z['C', 'C'], 'R_Q': z['T', 'T'] - z['C', 'T'],
            'I': z['T', 'T'] - z['T', 'C'] - z['C', 'T'] + z['C', 'C']}


def scen_mean(per_item, scen_of):
    out = {}
    for i, v in per_item.items():
        out.setdefault(scen_of[i], []).append(v)
    for s, v in out.items():
        assert len(v) == 2, (s, v)
    return {s: sum(v) / 2 for s, v in sorted(out.items())}


def material_dominance(eff, part):
    """eff: scenario -> factorial dict (two-fact mean differences). H_V / H_Q rule (plan §6). Returns per scenario
    status in {'pass', 'fail', 'undecidable'} and the overall label."""
    other = 'Q' if part == 'V' else 'V'
    st = {}
    for s, e in eff.items():
        g = e['G']
        if abs(g) < RULE['min_abs_G']:
            st[s] = 'undecidable'
            continue
        ra, rr = e[f'A_{part}'] / g, e[f'R_{part}'] / g
        oa, orr = e[f'A_{other}'] / g, e[f'R_{other}'] / g
        ok = (RULE['near_lo'] <= ra <= RULE['near_hi'] and RULE['near_lo'] <= rr <= RULE['near_hi']
              and abs(oa) <= RULE['other_max'] and abs(orr) <= RULE['other_max'])
        st[s] = 'pass' if ok else 'fail'
    n = sum(v == 'pass' for v in st.values())
    return {'scenarios': st, 'n_pass': n, 'label': 'supported' if n >= RULE['min_scen'] else 'not_supported'}


def additivity(eff):
    st = {}
    for s, e in eff.items():
        if abs(e['G']) < RULE['min_abs_G']:
            st[s] = 'undecidable'
        else:
            st[s] = 'pass' if abs(e['I'] / e['G']) <= RULE['add_max'] else 'fail'
    n = sum(v == 'pass' for v in st.values())
    return {'scenarios': st, 'n_pass': n, 'label': 'supported' if n >= RULE['min_scen'] else 'not_supported'}


def transfer(g_n, g_t):
    """H_transfer on D: scenario G_N / G_T in [0.75, 1.33] in >= 5/6 scenarios."""
    st, ratio = {}, {}
    lo, hi = RULE['transfer']
    for s in g_n:
        if abs(g_t[s]) < RULE['min_abs_G']:
            st[s], ratio[s] = 'undecidable', None
            continue
        ratio[s] = g_n[s] / g_t[s]
        st[s] = 'pass' if lo <= ratio[s] <= hi else 'fail'
    n = sum(v == 'pass' for v in st.values())
    return {'scenarios': st, 'ratio': ratio, 'n_pass': n, 'label': 'supported' if n >= RULE['min_scen'] else 'not_supported'}


def random_rule(per_item, scen_of):
    """Plan §6.2 for one (background, part, read-out). per_item: input -> {'G', 'R', 'R0', 'R1'} (R* = m(all T) - m(cell)).
    Scenario evaluable iff both facts |G| >= 1; exceeds iff both E_i = sign(G_i) R_i > 0 and
    mean(E_i) > max_j mean(|R_ij|) + 0.1. Combination 'stable_exceed' iff >= 5/6 scenarios exceed."""
    by = {}
    for i, d in per_item.items():
        by.setdefault(scen_of[i], []).append(d)
    st = {}
    for s, ds in sorted(by.items()):
        assert len(ds) == 2
        if any(abs(d['G']) < RULE['min_abs_G'] for d in ds):
            st[s] = 'undecidable'
            continue
        e = [math.copysign(1.0, d['G']) * d['R'] for d in ds]
        rnd = max(statistics.mean(abs(d[f'R{j}']) for d in ds) for j in (0, 1))
        st[s] = 'exceed' if (all(x > 0 for x in e) and statistics.mean(e) > rnd + RULE['margin']) else 'not_exceed'
    n_ex = sum(v == 'exceed' for v in st.values())
    n_ev = sum(v != 'undecidable' for v in st.values())
    if n_ex >= RULE['min_scen']:
        label = 'stable_exceed'
    elif n_ev < RULE['min_scen']:
        label = 'insufficient_evaluable'
    else:
        label = 'rule_not_met'
    return {'scenarios': st, 'n_exceed': n_ex, 'n_evaluable': n_ev, 'label': label}


def recon_check(o, core):
    """Contract r02 / DECISIONS D8: FP64 reconstruction o vs actual BF16 core. The residual of a correct path is the BF16
    rounding of the exact value, so the gate is err <= 1.05 * floor with floor = ||bf16(o) - o|| / ||o||; a wrong
    source or route gives err >> floor."""
    import torch
    o = o.double()
    c = core.double()
    on = float(o.norm())
    err = float((o - c).norm()) / max(float(c.norm()), 1e-300)
    floor = float((o.to(torch.bfloat16).double() - o).norm()) / max(on, 1e-300)
    if floor == 0:
        return {'err': err, 'floor': 0.0, 'ratio': 0.0 if err == 0 else math.inf, 'ok': err == 0}
    ratio = err / floor
    return {'err': err, 'floor': floor, 'ratio': ratio, 'ok': ratio <= RULE['recon_floor_ratio']}
