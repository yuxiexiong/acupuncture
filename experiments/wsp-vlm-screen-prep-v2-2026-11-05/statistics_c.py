"""Offline C scoring. Reads saved answers only; no model imports or calls."""
import argparse
import json
import math
import sys
from pathlib import Path
from statistics import NormalDist

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'wsp-vlm-screen-data-v1-2026-11-05'))
from prepare_c import CONDITIONS, validate_predictions

SEED = 20261105
CONDITIONS = [c[0] for c in CONDITIONS]


def holm(pvalues):
    if set(pvalues) - set('ABC'):
        raise ValueError('Family is fixed to A/B/C')
    ps = {k: pvalues.get(k, 1.) for k in 'ABC'}
    if any(not math.isfinite(p) or not 0 <= p <= 1 for p in ps.values()):
        raise ValueError('Invalid p value')
    result, previous = {}, 0.
    for i, k in enumerate(sorted(ps, key=ps.get)):
        previous = max(previous, min(1., (3-i)*ps[k]))
        result[k] = previous
    return result


def paired(control, challenge, resamples=10000):
    x, y = np.asarray(control, dtype=int), np.asarray(challenge, dtype=int)
    if x.shape != y.shape or x.ndim != 1 or not len(x):
        raise ValueError('Nonempty paired source groups required')
    if not np.isin(x, [0, 1]).all() or not np.isin(y, [0, 1]).all():
        raise ValueError('Correctness must be binary')
    n = len(x)
    b, c = int(((x == 1) & (y == 0)).sum()), int(((x == 0) & (y == 1)).sum())
    p = sum(math.comb(b+c, k) for k in range(b, b+c+1)) / 2**(b+c)
    # Each resampling index selects a complete source group, not a prompt variant.
    draws = np.random.default_rng(SEED).integers(0, n, size=(resamples, n))
    ci = np.quantile((x-y)[draws].mean(axis=1), [.025, .975]).tolist()
    return dict(n=n, b=b, c=c, delta=(b-c)/n, p_one_sided=p,
                ci95=ci, control_accuracy=float(x.mean()), challenge_accuracy=float(y.mean()),
                joint_accuracy=float((x*y).mean()))


def wilson_lower(successes, n):
    z = NormalDist().inv_cdf(.95)
    p = successes/n
    return (p+z*z/(2*n)-z*math.sqrt(p*(1-p)/n+z*z/(4*n*n)))/(1+z*z/n)


def score(predictions, gold):
    for p in predictions:
        if not isinstance(p.get('text'), str) or type(p.get('truncated')) is not bool:
            raise ValueError('Each answer requires text:str and truncated:bool')
        if p.get('status', 'ok') != 'ok':
            raise ValueError('Infrastructure failure: do not score as task error')
    scored = validate_predictions(predictions, gold)
    pred = {p['request_id']: p for p in predictions}
    by_id = {g['request_id']: g for g in gold}
    return [dict(by_id[s['request_id']], **{k:v for k,v in s.items() if k!='request_id'},
                 truncated=pred[s['request_id']]['truncated']) for s in scored]


def summarize(rows, resamples=10000):
    cells = {}
    for arm in ('B0', 'B1'):
        for t in ('T0', 'T1'):
            for order in (0, 1, 'primary'):
                # Primary order applies to both B0 and B1; B1 gold.primary is false.
                primary_ids = {(r['group_id'], r['order']) for r in rows if r['primary']}
                rs = [r for r in rows if r['arm']==arm and r['template']==t and
                      ((r['group_id'],r['order']) in primary_ids if order=='primary' else r['order']==order)]
                groups = {}
                for r in rs:
                    groups.setdefault(r['group_id'], {})[r['condition']] = r
                if not groups or any(set(v)!=set(CONDITIONS) for v in groups.values()):
                    raise ValueError('Incomplete condition cells')
                gs = [groups[k] for k in sorted(groups)]
                acc = {c:sum(g[c]['correct'] for g in gs)/len(gs) for c in CONDITIONS}
                comparison = paired([g['original_usual']['correct'] for g in gs],
                                    [g['counterfact_usual']['correct'] for g in gs], resamples)
                pattern = sum(g['no_image_usual']['correct'] and g['original_usual']['correct'] and
                              g['counterfact_visual']['correct'] and not g['counterfact_usual']['correct'] and
                              g['counterfact_usual']['parsed']==g['counterfact_visual']['answer'] for g in gs)
                cells[f'{arm}:{t}:O{order}'] = dict(comparison, accuracy=acc,
                    five_way_joint=sum(all(g[c]['correct'] for c in CONDITIONS) for g in gs)/len(gs),
                    error_pattern_groups=pattern, error_pattern_denominator=len(gs))
    # Compare each fixed template/order to the registered T0 per-group order.
    reference = {(r['group_id'], r['condition']):r for r in rows if r['primary']}
    agreement, prompt_effect = {}, {}
    for t in ('T0','T1'):
        for order in (0,1):
            base = [r for r in rows if r['arm']=='B0' and r['template']==t and r['order']==order]
            agreement[f'{t}:O{order}'] = dict(
                n=len(base),
                same_parsed=sum(r['parsed']==reference[r['group_id'],r['condition']]['parsed'] for r in base),
                both_format_valid=sum(r['format_valid'] and reference[r['group_id'],r['condition']]['format_valid'] for r in base),
                same_correctness=sum(r['correct']==reference[r['group_id'],r['condition']]['correct'] for r in base))
            strong = {(r['group_id'],r['condition']):r for r in rows if r['arm']=='B1' and r['template']==t and r['order']==order}
            prompt_effect[f'{t}:O{order}'] = {}
            for cond in CONDITIONS:
                bb = [r for r in base if r['condition']==cond]
                prompt_effect[f'{t}:O{order}'][cond] = dict(n=len(bb),
                    repaired=sum(not r['correct'] and strong[r['group_id'],cond]['correct'] for r in bb),
                    worsened=sum(r['correct'] and not strong[r['group_id'],cond]['correct'] for r in bb))
    return dict(cells=cells, variant_agreement=agreement, B1_changes=prompt_effect)


def classify(d, h, adjusted_p, engineering_pass):
    primary = h['cells']['B0:T0:Oprimary']
    if not engineering_pass:
        return 'measurement_protocol_failed'
    if (d['cells']['B0:T0:Oprimary']['delta']>0 and primary['delta']>=.15 and adjusted_p<.05
        and primary['challenge_accuracy']<=.8 and primary['control_accuracy']>=.7
        and primary['accuracy']['no_image_usual']>=.7
        and all(h['cells'][f'B0:{t}:O{o}']['delta']>0 for t in ('T0','T1') for o in (0,1))):
        return 'behavior_gap_priority_not_WSP_repairability'
    lower = wilson_lower(round(primary['challenge_accuracy']*primary['n']), primary['n'])
    if lower>=.9 or primary['ci95'][1]<.15:
        return 'not_priority_on_current_distribution'
    return 'unresolved'


def engineering_check(rows):
    engineering = {}
    for arm in ('B0','B1'):
        rr = [r for r in rows if r['arm']==arm]
        engineering[arm] = dict(n=len(rr), truncated=sum(r['truncated'] for r in rr),
                                format_invalid=sum(not r['format_valid'] for r in rr))
    ok = all(max(v['truncated'],v['format_invalid'])/v['n']<=.05 for v in engineering.values())
    return engineering, ok


def report(predictions, gold, family=None, resamples=10000):
    rows = score(predictions, gold)
    splits = {s:summarize([r for r in rows if r['split']==s], resamples) for s in ('D','H')}
    engineering, ok = engineering_check(rows)
    pvalues = dict(family or {})
    p = splits['H']['cells']['B0:T0:Oprimary']['p_one_sided']
    if 'C' in pvalues and pvalues['C'] != p:
        raise ValueError('C p value must come from these predictions')
    pvalues['C'] = p
    adjusted = holm(pvalues)
    return dict(status='saved-answer analysis; no model called', splits=splits, engineering=engineering,
                engineering_pass=ok, family_p={k:pvalues.get(k,1.) for k in 'ABC'}, holm=adjusted,
                missing_family_candidates=[k for k in 'ABC' if k not in pvalues],
                decision=classify(splits['D'],splits['H'],adjusted['C'],ok),
                diagnostic_registration='Must be timestamped after D and before opening H; counts alone do not prove registration.',
                bootstrap=dict(seed=SEED, resamples=resamples, unit='source_group', numpy=np.__version__),
                model_loads=0, model_calls=0)


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--predictions', type=Path, required=True)
    parser.add_argument('--gold', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--family-pvalues', type=Path)
    parser.add_argument('--split', choices=('D','all'), default='D',
                        help='Analyze D before registering a diagnostic description; all only after H is opened.')
    args=parser.parse_args()
    # Enforce exact frozen gold rather than accepting a modified/subselected denominator.
    from prepare_c import requests, selected_groups
    gold=read_jsonl(args.gold)
    expected=[g for _,g in requests(selected_groups())]
    if gold != expected: raise ValueError('Gold differs from frozen C manifest/order')
    predictions=read_jsonl(args.predictions)
    if args.split=='D':
        rows=score(predictions,[g for g in gold if g['split']=='D'])
        engineering,ok=engineering_check(rows)
        result=dict(status='D only; H not analyzed; register diagnostic description before opening H',
                    D=summarize(rows),engineering=engineering,engineering_pass=ok,
                    model_loads=0,model_calls=0)
    else:
        result=report(predictions,gold,
                      json.loads(args.family_pvalues.read_text()) if args.family_pvalues else None)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
