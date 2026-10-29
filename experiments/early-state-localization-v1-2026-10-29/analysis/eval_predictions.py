"""Evaluate the locked confirmation predictions (readiness/development-interpretation-r01.zh-CN.md) from an analyze_localize output.

python eval_predictions.py ANALYSIS_JSON OUT_JSON      (written before any confirmation output was read)
"""
import json
import sys

ANCHORS = ('N_L00_C4146_D+1', 'N_L02_C5251_D-1', 'N_L02_C5063_D+1')


def main(path, out):
    d = json.load(open(path))
    eos, conds = d['first_step_eos'], d['conditions']
    res = {'main_prediction': d['main_prediction']}
    decays = {c: conds[c]['decay']['verdict'] for c in ANCHORS if 'decay' in conds.get(c, {})}
    res['decay_H_rec'] = {'by_anchor': decays, 'holds': sum(v == 'decay_holds' for v in decays.values()) >= 2}
    stop = [c for c in conds if eos.get(f'{c}|A0', 0) >= 12]
    ok = [c for c in stop if eos[f'{c}|A3'] < eos[f'{c}|A0'] and eos[f'{c}|A2'] >= eos[f'{c}|A3']]
    res['P_dev1'] = {'denominator': len(stop), 'matching': len(ok), 'conditions': stop,
                     'holds': (len(ok) > len(stop) / 2) if stop else 'undecidable'}
    res['P_dev2'] = {'by_anchor': decays, 'holds': sum(v == 'reversed' for v in decays.values()) >= 2}
    early = [c for c, v in conds.items() if v['tiers']['A0'] == 'failed' and c != 'N_L25_C2747_D+1'
             and (c.startswith('N_L0') or c.startswith('V'))
             and int(c.split('_L')[1][:2]) < 4]
    either = [c for c in early if conds[c]['carrier'] == 'either_needed']
    res['P_dev3'] = {'denominator': len(early), 'either_needed': len(either),
                     'holds': (len(either) > len(early) / 2) if early else 'undecidable'}
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v['holds'] for k, v in res.items()}))


if __name__ == '__main__':
    main(*sys.argv[1:3])
