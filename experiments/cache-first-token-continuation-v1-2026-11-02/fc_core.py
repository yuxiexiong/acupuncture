"""FC-01 pure rules (plan §5–6, CONTRACT r01).  Classification of a decoded continuation (special tokens kept).

Visible text = generated text with stop tokens removed and every <think>...</think> block removed (an unclosed <think>
removes everything after it).  Codes = (?<![A-Za-z0-9])[A-Z][0-9]+(?![A-Za-z0-9]).
Y_delivery: visible text contains the target code and no other distinct code.  Y_strict: visible text stripped == target.
Main (exclusive): multi_code > correct / distractor / other_code > stopped_no_code / budget_no_code.
"""
import re

ANSWER_RE = re.compile(r'目标条目\S*?编号为([A-Za-z0-9]+)')
CODE_IN_RECORD = re.compile(r'编号为([A-Za-z0-9]+)')
CODE_RE = re.compile(r'(?<![A-Za-z0-9])[A-Z][0-9]+(?![A-Za-z0-9])')
STOP_TEXT = ('<|endoftext|>', '<|im_end|>')
THINK_OPEN, THINK_CLOSE = '<think>', '</think>'
RULE = {'scen_count': 5, 'dir_count': 3}


def answer_and_distractors(record_text):
    ans = ANSWER_RE.search(record_text).group(1)
    return ans, [c for c in CODE_IN_RECORD.findall(record_text) if c != ans]


def visible(text):
    t = text
    for s in STOP_TEXT:
        t = t.replace(s, '')
    out, think_present, unclosed = '', False, False
    while True:
        i = t.find(THINK_OPEN)
        if i < 0:
            out += t
            break
        think_present = True
        out += t[:i]
        j = t.find(THINK_CLOSE, i + len(THINK_OPEN))
        if j < 0:
            unclosed = True
            break
        t = t[j + len(THINK_CLOSE):]
    return out, think_present, unclosed


def classify(text, termination, target, distractors, question=None):
    vis, think, unclosed = visible(text)
    codes = CODE_RE.findall(vis)
    distinct = list(dict.fromkeys(codes))
    if len(distinct) > 1:
        main = 'multi_code'
    elif len(distinct) == 1:
        main = 'correct' if distinct[0] == target else ('distractor' if distinct[0] in distractors else 'other_code')
    else:
        main = 'stopped_no_code' if termination == 'stop' else 'budget_no_code'
    y_delivery = target in distinct and len(distinct) == 1
    tags = {'think_present': think, 'think_unclosed': unclosed, 'n_codes': len(codes), 'n_distinct_codes': len(distinct),
            'first_code': codes[0] if codes else None, 'first_code_correct': bool(codes) and codes[0] == target,
            'target_repeated': codes.count(target) > 1,
            'contains_question': bool(question) and question in vis,
            'question_repeats': vis.count(question) if question else 0}
    return {'main': main, 'Y_delivery': y_delivery, 'Y_strict': vis.strip() == target, 'visible': vis, 'tags': tags}


def scenario_pairs(values):
    out = {}
    for iid, v in values.items():
        s, f = iid.rsplit('-', 1)
        out.setdefault(s, {})[f] = v
    return {s: (d['f0'], d['f1']) for s, d in sorted(out.items())}


def p_f_direction(c_ok, tf_ok):
    """c_ok / tf_ok: input -> bool (Y_delivery of C_nat / T_F).  Scenario supports if both facts have C correct and T_F correct.
    Baseline insufficient if fewer than 5 scenarios have C correct in both facts."""
    cp, tp = scenario_pairs(c_ok), scenario_pairs(tf_ok)
    base = sum(a and b for a, b in cp.values())
    sup = sum(cp[s][0] and cp[s][1] and tp[s][0] and tp[s][1] for s in cp)
    if base < RULE['scen_count']:
        return 'baseline_insufficient', sup, base
    return ('support' if sup >= RULE['scen_count'] else 'unsupported'), sup, base


def transitions(nat_ok, arm_ok):
    out = {'wrong_to_right': 0, 'both_right': 0, 'right_to_wrong': 0, 'both_wrong': 0}
    for i in nat_ok:
        a, b = nat_ok[i], arm_ok[i]
        out['both_right' if a and b else 'wrong_to_right' if b else 'right_to_wrong' if a else 'both_wrong'] += 1
    return out


def q0_audit(q0_text, target, distractors):
    """Zero-model audit (plan §4): which codes are compatible with the forced prefix q0."""
    p = q0_text.strip()
    return {'q0': p, 'covers_full_answer': p == target, 'target_compatible': target.startswith(p),
            'distractors_compatible': [d for d in distractors if d.startswith(p)]}
