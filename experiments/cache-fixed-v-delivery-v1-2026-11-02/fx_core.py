"""FX-01 rules (plan §3).  Classification reuses the frozen FC-01 classifier."""
RULE = {'scen_count': 5, 'dir_count': 3, 'adv_wins': 2}


def scenario_pairs(values):
    out = {}
    for iid, v in values.items():
        s, f = iid.rsplit('-', 1)
        out.setdefault(s, {})[f] = v
    return {s: (d['f0'], d['f1']) for s, d in sorted(out.items())}


def rescued(c_ok, tnat_ok, arm_ok):
    """Per scenario: both facts have C correct, T_nat undelivered, and the arm correct."""
    cp, tp, ap = scenario_pairs(c_ok), scenario_pairs(tnat_ok), scenario_pairs(arm_ok)
    return {s: cp[s][0] and cp[s][1] and not tp[s][0] and not tp[s][1] and ap[s][0] and ap[s][1] for s in cp}


def direction_status(c_ok, tnat_ok, arm_ok):
    cp = scenario_pairs(c_ok)
    base = sum(a and b for a, b in cp.values())
    res = rescued(c_ok, tnat_ok, arm_ok)
    n = sum(res.values())
    if base < RULE['scen_count']:
        return {'status': 'baseline_insufficient', 'rescued': n, 'base': base}
    return {'status': 'support' if n >= RULE['scen_count'] else 'unsupported', 'rescued': n, 'base': base}


def overall(statuses):
    n = sum(s['status'] == 'support' for s in statuses.values())
    return {'met': n >= RULE['dir_count'], 'n_support': n, 'of': len(statuses)}


def fix_vs_u(c_ok, tnat_ok, fix_ok, u_ok):
    """Wins: scenarios FIX rescues both facts and U does not; losses: the reverse.  Advantage iff wins >= 2 and losses == 0."""
    rf, ru = rescued(c_ok, tnat_ok, fix_ok), rescued(c_ok, tnat_ok, u_ok)
    wins = sum(rf[s] and not ru[s] for s in rf)
    losses = sum(ru[s] and not rf[s] for s in rf)
    ties = len(rf) - wins - losses
    return {'wins': wins, 'losses': losses, 'ties': ties, 'advantage': wins >= RULE['adv_wins'] and losses == 0}
