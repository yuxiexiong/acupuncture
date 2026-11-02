"""SP-01 rules (plan §4).  Classification reuses the frozen FC-01 classifier (fc_core.classify)."""
RULE = {'scen_count': 5, 'damage_count': 4, 'dir_count': 3}


def scenario_pairs(values):
    out = {}
    for iid, v in values.items():
        s, f = iid.rsplit('-', 1)
        out.setdefault(s, {})[f] = v
    return {s: (d['f0'], d['f1']) for s, d in sorted(out.items())}


def both(pairs, pred=lambda x: x):
    return sum(pred(a) and pred(b) for a, b in pairs.values())


def direction_status(c_ok, tnat_ok, arm_ok):
    """Baseline: C correct in both facts of >= 5/6 scenarios.  Damage: T_nat undelivered in both facts of >= 4/6.
    Support: arm correct in both facts of >= 5/6 (only judged when baseline and damage hold)."""
    base = both(scenario_pairs(c_ok))
    dmg = both(scenario_pairs(tnat_ok), lambda x: not x)
    sup = both(scenario_pairs(arm_ok))
    if base < RULE['scen_count']:
        return {'status': 'baseline_insufficient', 'base': base, 'damage': dmg, 'support': sup}
    if dmg < RULE['damage_count']:
        return {'status': 'effect_not_transferred', 'base': base, 'damage': dmg, 'support': sup}
    return {'status': 'support' if sup >= RULE['scen_count'] else 'unsupported', 'base': base, 'damage': dmg, 'support': sup}


def overall(statuses):
    """Fixed denominator of 4 directions: >= 3 'support' needed."""
    n = sum(s['status'] == 'support' for s in statuses.values())
    return {'met': n >= RULE['dir_count'], 'n_support': n, 'of': len(statuses)}


def margin(step2, target_tok, distractor_toks):
    """M = z(target second token) - max z(distractor second tokens) at step 2."""
    if not step2:
        return None
    return step2[str(target_tok)] - max(step2[str(d)] for d in distractor_toks)
