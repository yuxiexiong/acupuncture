"""NWR-01 r02 frozen read-outs (CONTRACT-r02 §4-5; Proposal v8 §4.4).  Operational effect-size gates, not significance tests.

Output categories (exclusive; FC-01 classifier unchanged, special tokens kept):
  correct        Y_full: only the target code, termination == 'stop', no unclosed <think>
  wrong_num      exactly one distinct code, not the target, termination == 'stop', no unclosed <think>   (E_num numerator)
                 sub: first_listed / other_listed / unlisted
  stop_no_code   stopped with no code (includes receivers that never reached t2)
  multi_code     more than one distinct code
  budget         hit the token budget (any content)
  other          anything else (e.g. unclosed <think>)
Scenario-equal rates: mean over the 6 scenarios of the within-scenario mean.
  b   = Y(L11) - Y(L00)             local-write repair reference
  l_X = Y(L11) - Y(X)               loss caused by arm X in receiver L11 (X = D00, E00, D10, R1..R5); l_R = mean over the five seeds
  e_X = E_num(X) - E_num(L11)       increase in explicit wrong numbers; e_R = mean over the five seeds
H-WR strong standard (all point estimates):
  b >= 0.25; l_D >= 0.20 and l_D - 0.5 b > 0; l_D - l_E > 0; l_D - l_R > 0; e_D >= 0.15 and e_D - e_R > 0.
Outcome (first match):
  unjudgeable     b < 0.25, or receiver L11 not reaching t2 on >= 25% of inputs, or budget terminations in D00 on >= 25% of inputs
  strong          every strong-standard inequality holds
  weak_or_opposite  l_D < 0.20 or l_D - 0.5 b <= 0
  not_selective   l_D - l_E <= 0 or l_D - l_R <= 0
  stop_only       remaining case: selective loss without the explicit-wrong-number gate (e_D < 0.15 or e_D - e_R <= 0)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'cache-first-token-continuation-v1-2026-11-02'))
import fc_core as FK  # noqa: E402

TH = {'b': 0.25, 'l': 0.20, 'half': 0.5, 'e': 0.15, 'unreached': 0.25, 'budget': 0.25}
CATS = ('correct', 'wrong_num', 'stop_no_code', 'multi_code', 'budget', 'other')
RAND = tuple(f'R{j}' for j in range(1, 6))


def category(text, termination, it, reached_t2=True):
    """Returns (category, sub)."""
    target, listed = it['target'], it['listed_codes']
    c = FK.classify(text, termination, target, [x for x in listed if x != target], it.get('question'))
    if termination == 'budget':
        return 'budget', c['main']
    if c['tags']['think_unclosed']:
        return 'other', 'think_unclosed'
    if c['main'] == 'correct':
        return 'correct', None
    if c['main'] in ('distractor', 'other_code'):
        code = c['tags']['first_code']
        sub = 'unlisted' if c['main'] == 'other_code' else ('first_listed' if code == it['first_listed'] else 'other_listed')
        return 'wrong_num', sub
    if c['main'] == 'multi_code':
        return 'multi_code', None
    if c['main'] == 'stopped_no_code':
        return 'stop_no_code', ('unreached' if not reached_t2 else None)
    return 'other', c['main']


def seq(vals, scen):
    """Scenario-equal mean of {input: value}; also the per-scenario means."""
    by = {}
    for i, v in vals.items():
        by.setdefault(scen[i], []).append(v)
    sm = {s: sum(x) / len(x) for s, x in sorted(by.items())}
    return sum(sm.values()) / len(sm), sm


def rates(cat, scen):
    """cat: {arm: {input: category}} -> {arm: {'Y','E','by_scenario'}} (scenario-equal)."""
    out = {}
    for arm, cs in cat.items():
        y, ys = seq({i: float(c == 'correct') for i, c in cs.items()}, scen)
        e, es = seq({i: float(c == 'wrong_num') for i, c in cs.items()}, scen)
        out[arm] = {'Y': y, 'E': e, 'Y_scen': ys, 'E_scen': es, 'counts': {k: sum(1 for c in cs.values() if c == k) for k in CATS}}
    return out


def decide(r, unreached_frac=0.0, budget_frac_D=0.0):
    """r: output of rates() with arms L00, L11, D00, E00, R1..R5 (D10 optional)."""
    b = r['L11']['Y'] - r['L00']['Y']
    lD, lE = r['L11']['Y'] - r['D00']['Y'], r['L11']['Y'] - r['E00']['Y']
    lRs = [r['L11']['Y'] - r[x]['Y'] for x in RAND]
    eRs = [r[x]['E'] - r['L11']['E'] for x in RAND]
    lR, eR = sum(lRs) / len(lRs), sum(eRs) / len(eRs)
    eD, eE = r['D00']['E'] - r['L11']['E'], r['E00']['E'] - r['L11']['E']
    g = {'b': b >= TH['b'], 'l_D': lD >= TH['l'], 'l_D_half_b': lD - TH['half'] * b > 0, 'l_D_gt_l_E': lD - lE > 0, 'l_D_gt_l_R': lD - lR > 0,
         'e_D': eD >= TH['e'], 'e_D_gt_e_R': eD - eR > 0}
    if (not g['b']) or unreached_frac >= TH['unreached'] or budget_frac_D >= TH['budget']:
        lab = 'unjudgeable'
    elif all(g.values()):
        lab = 'strong'
    elif not (g['l_D'] and g['l_D_half_b']):
        lab = 'weak_or_opposite'
    elif not (g['l_D_gt_l_E'] and g['l_D_gt_l_R']):
        lab = 'not_selective'
    else:
        lab = 'stop_only'
    out = {'label': lab, 'gates': g, 'b': b, 'l_D': lD, 'l_E': lE, 'l_R': lR, 'l_R_seeds': lRs, 'e_D': eD, 'e_E': eE, 'e_R': eR, 'e_R_seeds': eRs,
           'unreached_frac': unreached_frac, 'budget_frac_D': budget_frac_D}
    if 'D10' in r:
        out['l_D10'] = r['L11']['Y'] - r['D10']['Y']
        out['e_D10'] = r['D10']['E'] - r['L11']['E']
    return out


def scen_boot(cat, scen, n=10000, seed=20261105):
    """Descriptive 95% percentile intervals over a resample of the 6 scenarios (with replacement) for the gate quantities.  Not a confirmation."""
    import random
    rng = random.Random(seed)
    ss = sorted(set(scen.values()))
    r0 = rates(cat, scen)
    per = {arm: (r0[arm]['Y_scen'], r0[arm]['E_scen']) for arm in r0}

    def q(sel):
        Y = {arm: sum(per[arm][0][s] for s in sel) / len(sel) for arm in per}
        E = {arm: sum(per[arm][1][s] for s in sel) / len(sel) for arm in per}
        b, lD, lE = Y['L11'] - Y['L00'], Y['L11'] - Y['D00'], Y['L11'] - Y['E00']
        lR = sum(Y['L11'] - Y[x] for x in RAND) / len(RAND)
        eD = E['D00'] - E['L11']
        eR = sum(E[x] - E['L11'] for x in RAND) / len(RAND)
        return {'b': b, 'l_D': lD, 'l_D-0.5b': lD - 0.5 * b, 'l_D-l_E': lD - lE, 'l_D-l_R': lD - lR, 'e_D': eD, 'e_D-e_R': eD - eR}
    draws = [q([rng.choice(ss) for _ in ss]) for _ in range(n)]
    out = {}
    for k in draws[0]:
        v = sorted(d[k] for d in draws)
        out[k] = {'point': q(ss)[k], 'lo': v[int(0.025 * n)], 'hi': v[int(0.975 * n) - 1]}
    return out
