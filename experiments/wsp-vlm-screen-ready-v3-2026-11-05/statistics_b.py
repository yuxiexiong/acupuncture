"""Strict integer scoring and source-group B statistics; saved answers only."""
import argparse
import json
import re
import sys

from prepare_inputs import HERE, V2, all_pairs, read_jsonl
sys.path.insert(0,str(V2))
from statistics_c import paired, holm, wilson_lower, engineering_check


def parse_integer(text):
    value=text.strip()
    # Whole reply: no extraction from prose, decimals, ranges, units or arithmetic.
    return int(value) if re.fullmatch(r'[0-9]+',value) else None


def score(predictions,gold):
    expected={g['request_id']:g for g in gold}
    if len(expected)!=len(gold):raise ValueError('Duplicate gold')
    seen=set();rows=[]
    for p in predictions:
        rid=p['request_id']
        if rid not in expected or rid in seen:raise ValueError('Unknown or duplicate prediction')
        if not isinstance(p.get('text'),str) or type(p.get('truncated')) is not bool:
            raise ValueError('text:str and truncated:bool required')
        if p.get('status','ok')!='ok':raise ValueError('Infrastructure failure; not a task error')
        seen.add(rid);g=expected[rid];parsed=parse_integer(p['text'])
        rows.append(dict(g,parsed=parsed,format_valid=parsed is not None,truncated=p['truncated'],
                         correct=parsed==g['answer'] and not p['truncated']))
    if seen!=set(expected):raise ValueError('Missing predictions; denominator cannot shrink')
    return rows


def cell(rows,resamples):
    groups={}
    for r in rows:groups.setdefault(r['group_id'],{})[r['condition']]=r
    if not groups or any(set(g)!={'total','subset'} for g in groups.values()):raise ValueError('Incomplete pairs')
    gs=[groups[k] for k in sorted(groups)]
    result=paired([g['total']['correct'] for g in gs],[g['subset']['correct'] for g in gs],resamples)
    eligible=[g for g in gs if g['total']['answer']!=g['subset']['answer']]
    pattern=sum(g['total']['correct'] and not g['subset']['correct'] and not g['subset']['truncated']
                and g['subset']['parsed']==g['total']['answer'] for g in eligible)
    result.update(error_pattern_groups=pattern,error_pattern_eligible=len(eligible),
                  error_pattern_all_groups=len(gs),
                  subset_format_errors=sum(not g['subset']['format_valid'] for g in gs),
                  subset_truncated=sum(g['subset']['truncated'] for g in gs))
    return result


def summarize(rows,resamples=10000):
    cells={};strata={};changes={}
    fields=('stratum','viewpoint','total_answer','subset_answer','difference','zero_subset','equal_answers')
    for arm in ('B0','B1'):
        for t in ('T0','T1'):
            rr=[r for r in rows if r['arm']==arm and r['template']==t]
            key=f'{arm}:{t}';cells[key]=cell(rr,resamples)
            strata[key]={}
            for field in fields:
                by={}
                for r in rr:
                    value=(r['total_answer']-r['subset_answer'] if field=='difference' else
                           r['subset_answer']==0 if field=='zero_subset' else
                           r['total_answer']==r['subset_answer'] if field=='equal_answers' else r[field])
                    by.setdefault(str(value),[]).append(r)
                strata[key][field]={v:cell(rs,resamples) for v,rs in sorted(by.items())}
    for t in ('T0','T1'):
        base=[r for r in rows if r['arm']=='B0' and r['template']==t]
        strong={(r['group_id'],r['condition']):r for r in rows if r['arm']=='B1' and r['template']==t}
        changes[t]={}
        for cond in ('total','subset'):
            rr=[r for r in base if r['condition']==cond]
            changes[t][cond]=dict(n=len(rr),
                repaired=sum(not r['correct'] and strong[r['group_id'],cond]['correct'] for r in rr),
                worsened=sum(r['correct'] and not strong[r['group_id'],cond]['correct'] for r in rr))
    agreement={}
    for arm in ('B0','B1'):
        a={(r['group_id'],r['condition']):r for r in rows if r['arm']==arm and r['template']=='T0'}
        b=[r for r in rows if r['arm']==arm and r['template']=='T1']
        agreement[arm]=dict(n=len(b),same_correctness=sum(r['correct']==a[r['group_id'],r['condition']]['correct'] for r in b),
            same_valid_answer=sum(r['format_valid'] and a[r['group_id'],r['condition']]['format_valid'] and
                                  r['parsed']==a[r['group_id'],r['condition']]['parsed'] for r in b))
    return dict(cells=cells,strata=strata,B1_changes=changes,template_agreement=agreement)


def report(predictions,gold,family=None,resamples=10000):
    rows=score(predictions,gold)
    stages={s:summarize([r for r in rows if r['split']==s],resamples) for s in sorted({r['split'] for r in rows})}
    engineering,ok=engineering_check(rows)
    out=dict(splits=stages,engineering=engineering,engineering_pass=ok,model_loads=0,model_calls=0,
             bootstrap=dict(seed=20261105,resamples=resamples,unit='source_group'),
             note='Strata are descriptive, not extra primary hypothesis tests; behavior gap is not WSP repairability.')
    if set(stages)=={'D'}:return dict(out,decision='D_only_register_before_H')
    if set(stages)!={'D','H'}:raise ValueError('Analyze D first; full report requires D and H')
    d,h=stages['D']['cells']['B0:T0'],stages['H']['cells']['B0:T0']
    ps=dict(family or {})
    if 'B' in ps and ps['B']!=h['p_one_sided']:raise ValueError('Cannot override B p value')
    ps['B']=h['p_one_sided'];adjusted=holm(ps)
    decision='unresolved'
    if not ok:decision='measurement_protocol_failed'
    elif (d['delta']>0 and h['delta']>=.15 and adjusted['B']<.05 and h['challenge_accuracy']<=.8
          and h['control_accuracy']>=.7 and stages['H']['cells']['B0:T1']['delta']>0):
        decision='behavior_gap_priority_not_WSP_repairability'
    elif wilson_lower(round(h['challenge_accuracy']*h['n']),h['n'])>=.9 or h['ci95'][1]<.15:
        decision='not_priority_on_current_distribution'
    return dict(out,decision=decision,family_p={k:ps.get(k,1.) for k in 'ABC'},holm=adjusted,
                missing_family_candidates=[k for k in 'ABC' if k not in ps])


if __name__=='__main__':
    from pathlib import Path
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--predictions',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--split',choices=('D','all'),default='D');p.add_argument('--family-pvalues',type=Path)
    args=p.parse_args()
    gold=[g for i,g in all_pairs('B') if args.split=='all' or g['split']=='D']
    result=report(read_jsonl(args.predictions),gold,json.loads(args.family_pvalues.read_text()) if args.family_pvalues else None)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
