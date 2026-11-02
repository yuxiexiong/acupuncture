"""SVQ-01 frozen rules.  Direction status and the overall count reuse the frozen SP-01 rules (sp_core): baseline C correct in
both facts of >= 5/6 scenarios, damage T_nat undelivered in both facts of >= 4/6, support arm correct in both facts of >= 5/6,
overall >= 3 of 4 directions (fixed denominator).  Added here (plan §3 and amendments v2 A2): per-input pairing tables against
T_F (a reference, not a ceiling), the target-vs-first-listed selection count on non-first-position inputs, and the shared-prefix
diagnostic margin M."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'cache-shared-prefix-continuation-v1-2026-11-02'))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'cache-first-token-continuation-v1-2026-11-02'))
import sp_core as SC  # noqa: E402
import fc_core as FK  # noqa: E402  (frozen classifier and its code regex)

RULE = dict(SC.RULE)
direction_status, overall, scenario_pairs, margin = SC.direction_status, SC.overall, SC.scenario_pairs, SC.margin


def rescue_status(c_ok, tnat_ok, arm_ok):
    """Plan §3 'recovery support': >= 5/6 scenarios where both facts have C correct, T_nat undelivered and the arm correct.
    Applied on top of the SP baseline/damage preconditions (sp_core.direction_status)."""
    st = direction_status(c_ok, tnat_ok, arm_ok)
    cp, tp, ap = scenario_pairs(c_ok), scenario_pairs(tnat_ok), scenario_pairs(arm_ok)
    n = sum(cp[s][0] and cp[s][1] and not tp[s][0] and not tp[s][1] and ap[s][0] and ap[s][1] for s in cp)
    st = dict(st, rescued=n)
    if st['status'] in ('support', 'unsupported'):
        st['status'] = 'support' if n >= RULE['scen_count'] else 'unsupported'
    return st


def pairing(a_ok, b_ok):
    """Per-input 2x2 on Y_delivery: a right / b wrong, b right / a wrong, both right, both wrong."""
    out = {'a_only': 0, 'b_only': 0, 'both': 0, 'neither': 0}
    for i in a_ok:
        x, y = a_ok[i], b_ok[i]
        out['both' if x and y else 'a_only' if x else 'b_only' if y else 'neither'] += 1
    return out


def first_listed(record, codes):
    pos = {c: record.find(c) for c in codes}
    assert all(p >= 0 for p in pos.values()), pos
    return min(codes, key=lambda c: pos[c])


def selection(cls_by_input, items):
    """Only inputs whose target is not first-listed (the two rules are indistinguishable otherwise).
    cls_by_input: id -> FC classification; items: id -> panel item.  Counts single-code outputs equal to the target / to the
    first-listed code / anything else."""
    out = {'n': 0, 'target': 0, 'first_listed': 0, 'other': 0}
    for i, c in cls_by_input.items():
        it = items[i]
        fl = first_listed(it['record'], [it['target']] + it['distractors'])
        if fl == it['target']:
            continue
        out['n'] += 1
        codes = list(dict.fromkeys(FK.CODE_RE.findall(c['visible'])))
        if codes == [it['target']]:
            out['target'] += 1
        elif codes == [fl]:
            out['first_listed'] += 1
        else:
            out['other'] += 1
    return out
