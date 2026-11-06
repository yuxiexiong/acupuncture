"""Score complete saved responses on the frozen source denominator; CPU only."""
import collections
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

def normalize(text):
    return ' '.join(text.strip().strip('.').strip().casefold().split())

def parse_answer(text,names):
    matched=[n for n in names if normalize(text)==normalize(n)]
    return matched[0] if len(matched)==1 else None

def score(predictions,gold):
    ids=[r['request_id'] for r in predictions]
    expected={r['request_id'] for r in gold}
    if len(ids)!=len(set(ids)) or set(ids)!=expected:
        raise ValueError('Missing, extra or duplicate response IDs; experiment incomplete')
    pred={r['request_id']:r for r in predictions};panels=collections.defaultdict(dict);conditions=collections.defaultdict(list)
    for g in gold:
        r=pred[g['request_id']]
        ok=not r.get('truncated',False) and parse_answer(r['text'],g['names'])==g['answer']
        panels[g['stratum'],g['source_id'],g['template'],g['order']][g['condition']]=int(ok)
        conditions[g['stratum'],g['source_id'],g['template'],g['condition']].append(int(ok))
    groups=collections.defaultdict(list)
    for (stratum,source,template,order),p in panels.items():
        groups[stratum,source,'Jcf',template].append(p['counterfact_usual']*p['counterfact_visual'])
        if stratum=='vlind':
            groups[stratum,source,'J5',template].append(int(all(p.values())))
    result=[dict(stratum=k[0],source_id=k[1],metric=k[2],template=k[3],score=sum(v)/len(v)) for k,v in sorted(groups.items())]
    single=[dict(stratum=k[0],source_id=k[1],template=k[2],condition=k[3],score=sum(v)/len(v)) for k,v in sorted(conditions.items())]
    return dict(group_scores=result,condition_scores=single)

if __name__=='__main__':
    gold=[json.loads(s) for s in (HERE/'gold.jsonl').read_text().splitlines()]
    perfect=[dict(request_id=g['request_id'],text=g['answer']) for g in gold]
    assert all(r['score']==1 for r in score(perfect,gold)['group_scores'])
    idx=next(i for i,g in enumerate(gold) if g['stratum']=='rome' and g['template']=='U2' and g['condition']=='counterfact_visual')
    changed=[dict(r) for r in perfect];changed[idx]['text']='Both objects'
    out=score(changed,gold)['group_scores']
    new=[r['score'] for r in out if r['stratum']=='rome' and r['template'] in ('U1','U2')]
    assert abs(sum(new)/len(new)-(1-1/320))<1e-12
    changed[idx]['text']=gold[idx]['answer'];changed[idx]['truncated']=True
    assert score(changed,gold)==score([dict(r,text='Both objects') if i==idx else r for i,r in enumerate(perfect)],gold)
    for bad in [perfect[:-1],perfect+[perfect[0]]]:
        try:score(bad,gold)
        except ValueError:pass
        else:raise AssertionError('Incomplete or duplicate IDs accepted')
    assert parse_answer('The answer is '+gold[0]['answer'],gold[0]['names']) is None
    print('PASS: source-weighted Jcf, malformed/truncated answers, missing/duplicate IDs')
