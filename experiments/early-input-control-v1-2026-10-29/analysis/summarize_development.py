"""Tabulate locked, joined development labels; counts only, no scores or thresholds.

python analysis/summarize_development.py JOINED OUT_JSON
Units: input (item) counts and base-scenario counts (a base is affected when either fact is).
Inputs whose clean answer does not follow the fact are excluded from 'clean-correct' denominators and listed apart.
"""
import json
import sys
from collections import Counter, defaultdict

ABNORMAL = {'other_fact', 'other_wrong', 'not_delivered'}


def window(c):
    if c['kind'] == 'clean':
        return 'clean'
    return 'early' if c['layer'] < 4 else 'middle' if c['layer'] < 16 else 'late'


def main(joined, out):
    rows = json.load(open(joined))['rows']
    clean = {r['item_id']: r for r in rows if r['condition']['id'] == 'clean'}
    usable = {i for i, r in clean.items() if r['label']['fact'] == 'follows_fact'}
    family = lambda i: {'RD': 'reading', 'AR': 'arithmetic', 'RL': 'relation'}[i.removeprefix('C')[:2]]
    base = lambda i: i.split('-')[0]
    groups = defaultdict(list)
    for r in rows:
        c = r['condition']
        if c['kind'] == 'clean':
            continue
        sign = '+' if c['dose'] > 0 else '-'
        kind = 'native' if c['kind'] == 'native' else 'direction'
        keys = [('window', kind, window(c), sign, abs(c['dose'])), ('layer', kind, c['layer'], sign, abs(c['dose'])),
                ('window_family', kind, window(c), family(r['item_id']), sign, abs(c['dose']))]
        if kind == 'native':
            keys.append(('point', c['layer'], c['channel'], c['dose']))
        else:
            keys.append(('direction', c['direction_id'], c['layer'], c['dose']))
        for k in keys:
            groups[k].append(r)

    def describe(rs):
        inputs = [r for r in rs if r['item_id'] in usable]
        affected_bases = {(r['condition']['id'], base(r['item_id'])) for r in inputs
                          if r['label']['fact'] in ABNORMAL or r['label']['contradiction']}
        all_bases = {(r['condition']['id'], base(r['item_id'])) for r in inputs}
        return {'inputs': len(rs), 'clean_correct_inputs': len(inputs),
                'fact_labels_clean_correct': dict(Counter(r['label']['fact'] for r in inputs)),
                'contradiction': sum(r['label']['contradiction'] for r in inputs),
                'repetition_label': sum(r['label']['repetition'] for r in inputs),
                'affected_condition_bases': len(affected_bases), 'condition_bases': len(all_bases),
                'eos_first_token': sum(r['mech']['tokens'] == 1 and r['mech']['end_reason'] == 'eos_token' for r in rs),
                'hit_128': sum(r['mech']['hit_128'] for r in rs),
                'median_tokens': sorted(r['mech']['tokens'] for r in rs)[len(rs) // 2],
                'clean_wrong_inputs_labels': dict(Counter(r['label']['fact'] for r in rs if r['item_id'] not in usable))}
    value = {'clean': {i: {'fact': r['label']['fact'], 'note': r['label']['note'], 'tokens': r['mech']['tokens']} for i, r in sorted(clean.items())},
             'clean_not_following': sorted(set(clean) - usable),
             'groups': [{'key': list(k), **describe(v)} for k, v in sorted(groups.items(), key=lambda kv: str(kv[0]))]}
    with open(out, 'x') as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main(*sys.argv[1:3])
