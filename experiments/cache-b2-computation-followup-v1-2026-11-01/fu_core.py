"""B2 computation follow-up: pure pieces (plan docs/cache-b2-computation-followup-plan-v1-2026-11-01, a03b14a).

K(X) = X101 - X001 - X111 + X011 equals B_H(1) (cells q h r, R = T). Local diagnostic: d = out(core111 - I) - out(core111),
P_local = sum_l u . d_l; P_local > 0 means the local Q x V_H write interaction acts in the direction of the observed
saturation (removing it restores Q's effect).
"""
import statistics

RULE = {'sub': 0.2, 'min_scen': 5}
TOL = {'rebuild_rel': 0.02, 'ident_abs': 1e-12, 'ident_rel': 1e-10, 'head_sum_rel': 1e-10, 'closure_rel': 1e-8}
TAIL = (27, 28, 29, 30, 31)


def K(x):
    """x: cell -> value (scalar or tensor)."""
    return x['101'] - x['001'] - x['111'] + x['011']


def local_projection(core, I, out_fn, u):
    """Projection of out(core - I) - out(core) on u."""
    return float(u @ (out_fn(core - I) - out_fn(core)))


def classify_positive(f0, f1):
    m = (f0 + f1) / 2
    if m >= RULE['sub'] and f0 > 0 and f1 > 0:
        return 'positive'
    if m <= -RULE['sub'] and f0 < 0 and f1 < 0:
        return 'negative'
    return 'neither'


def screen(pairs):
    """pairs: scenario -> (f0, f1). >= 5/6 positive -> candidate; >= 5/6 negative -> reverse prediction."""
    lab = {s: classify_positive(*v) for s, v in sorted(pairs.items())}
    npos = sum(x == 'positive' for x in lab.values())
    nneg = sum(x == 'negative' for x in lab.values())
    d = 'candidate' if npos >= RULE['min_scen'] else ('reverse' if nneg >= RULE['min_scen'] else 'no_candidate')
    return {'labels': lab, 'n_positive': npos, 'n_negative': nneg, 'decision': d,
            'means': {s: statistics.mean(v) for s, v in pairs.items()}}


def decide(local, tail):
    a, b = local['decision'] == 'candidate', tail['decision'] == 'candidate'
    if a and b:
        return 'both_candidates'
    if a:
        return 'local_write_candidate'
    if b:
        return 'tail_27_31_candidate'
    return 'no_qualified_candidate'


def closure_ok(parts, total):
    s = sum(parts)
    scale = max(1.0, sum(abs(p) for p in parts) + abs(total))
    return abs(s - total) <= TOL['closure_rel'] * scale, abs(s - total)
