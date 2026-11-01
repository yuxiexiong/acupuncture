"""C2 pure pieces: signed per-side criteria (plan docs/cache-c2-fixed-list-cross-direction-plan-v1-2026-11-01 §5)."""
import statistics

DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'R1_L00_D-1')
ANCHOR = 'N_L00_C4146_D-1'
RANDOM_DIRS = ('R0_L00_D-1', 'R1_L00_D-1')
SIGN = {'stop': 1.0, 'answer': -1.0}
RULE = {'F_min': 1.0, 'retain': 0.5, 'E_min': 0.2, 'min_scen': 5, 'write_rel': 0.01, 'rebuild_rel': 0.02}


def scenario_check(facts, arm, s):
    """facts: two dicts with F, arm value and U (list). All quantities multiplied by sign s before the rule."""
    F = [s * f['F'] for f in facts]
    X = [s * f[arm] for f in facts]
    E = [s * (f[arm] - statistics.median(f['U'])) for f in facts]
    mF, mX, mE = statistics.mean(F), statistics.mean(X), statistics.mean(E)
    f_ok = mF >= RULE['F_min'] and all(x > 0 for x in F)
    r_ok = f_ok and mX >= RULE['retain'] * mF and all(x > 0 for x in X)
    e_ok = mE >= RULE['E_min'] and all(x > 0 for x in E)
    return {'sF': mF, 'sX': mX, 'sE': mE, 'F_ok': f_ok, 'retain_ok': r_ok, 'E_ok': e_ok, 'pass': bool(f_ok and r_ok and e_ok)}


def judge(scen):
    n_f = sum(v['F_ok'] for v in scen.values())
    n_pass = sum(v['pass'] for v in scen.values())
    n_ret = sum(v['retain_ok'] for v in scen.values())
    if n_pass >= RULE['min_scen']:
        d = 'support'
    elif n_f < RULE['min_scen']:
        d = 'insufficient_F'
    elif n_ret >= RULE['min_scen']:
        d = 'subset_effective_no_advantage'
    else:
        d = 'list_not_realized'
    return {'n_F_ok': n_f, 'n_retain_ok': n_ret, 'n_pass': n_pass, 'decision': d}


def prediction(decisions):
    """Pre-registered: FIX transfers to random directions iff both R0 and R1 stop-side decisions are 'support'."""
    return all(decisions[d] == 'support' for d in RANDOM_DIRS)
