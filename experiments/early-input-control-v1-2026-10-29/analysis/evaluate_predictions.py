"""Evaluate confirmation predictions C1-C6 of readiness/development-interpretation-r01 §4.

python analysis/evaluate_predictions.py CONF_SUMMARY CONF_JOINED MECH_CONF_JOINED_OR_- OUT_JSON
Reading fixed before any confirmation output was seen: C1/C2/C4 hold only if both signs hold;
C3 pools signs; 'majority' means > 1/2; empty denominators are 'undecidable'.
"""
import json
import sys

ABNORMAL = {'other_fact', 'other_wrong', 'not_delivered'}


def main(summary_path, joined_path, mech_path, out):
    s = json.load(open(summary_path))
    groups = {tuple(g['key']): g for g in s['groups']}

    def win(kind, w, sign, dose):
        return groups[('window', kind, w, sign, dose)]

    result = {}
    per = {}
    for sign in '+-':
        e, m, l = (win('native', w, sign, 1.0)['affected_condition_bases'] for w in ('early', 'middle', 'late'))
        e5, l5 = (win('native', w, sign, 0.5)['affected_condition_bases'] for w in ('early', 'late'))
        per[sign] = {'pm1': [e, m, l], 'pm05_early_late': [e5, l5], 'holds': e > m > l and e5 > l5}
    result['C1'] = {'holds': all(v['holds'] for v in per.values()), 'by_sign': per}
    per = {}
    for sign in '+-':
        g = win('native', 'early', sign, 1.0)
        f = g['fact_labels_clean_correct']
        n = g['clean_correct_inputs']
        per[sign] = {'not_delivered': f.get('not_delivered', 0), 'clean_correct_inputs': n,
                     'eos_first_token': g['eos_first_token'], 'other_fact': f.get('other_fact', 0),
                     'holds': n > 0 and f.get('not_delivered', 0) > n / 2 and g['eos_first_token'] > f.get('other_fact', 0)}
    result['C2'] = {'holds': all(v['holds'] for v in per.values()), 'by_sign': per}
    err = {w: sum(win('native', w, sign, 1.0)['fact_labels_clean_correct'].get(k, 0) for sign in '+-' for k in ('other_fact', 'other_wrong'))
           for w in ('early', 'middle')}
    result['C3'] = {'holds': err['middle'] >= err['early'], 'counts': err}
    per = {}
    for sign in '+-':
        e, l = (win('direction', w, sign, 1.0)['affected_condition_bases'] for w in ('early', 'late'))
        per[sign] = {'early_late': [e, l], 'holds': e > l}
    result['C4'] = {'holds': all(v['holds'] for v in per.values()), 'by_sign': per}
    if mech_path != '-':
        rows = json.load(open(mech_path))['rows']
        clean = {r['item_id']: r['label']['fact'] for r in json.load(open(joined_path))['rows'] if r['condition']['id'] == 'clean'}
        lab = {}
        for r in rows:
            i, c, m = r['key'].split('__')
            lab[(i, c, m)] = r
        cid = 'N_L00_C4146_D+1'
        eos = [i for (i, c, m), r in lab.items() if c == cid and m == 'full' and clean.get(i) == 'follows_fact'
               and r['mech']['tokens'] == 1 and r['mech']['end_reason'] == 'eos_token']
        match = [i for i in eos if lab[(i, cid, 'prompt_except_last')]['label']['fact'] == 'not_delivered'
                 and lab[(i, cid, 'prompt_last')]['label']['fact'] != 'not_delivered']
        result['C5'] = {'holds': (len(match) > len(eos) / 2) if eos else 'undecidable', 'denominator': len(eos), 'matching': len(match), 'items': sorted(match)}
        cid = 'N_L25_C2747_D+1'
        ab = lambda l: l['fact'] in ABNORMAL or l['contradiction']
        base = [i for (i, c, m), r in lab.items() if c == cid and m == 'full' and clean.get(i) == 'follows_fact' and ab(r['label'])
                and (i, cid, 'fork016_rebuild') in lab]
        still = [i for i in base if ab(lab[(i, cid, 'fork016_rebuild')]['label'])]
        result['C6'] = {'holds': (len(still) > len(base) / 2) if base else 'undecidable', 'denominator': len(base), 'rebuild_still_abnormal': len(still)}
    with open(out, 'x') as f:
        f.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v['holds'] for k, v in result.items()}))


if __name__ == '__main__':
    main(*sys.argv[1:5])
