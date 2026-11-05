"""Read-only CPU comparison of existing v8 50 and v9 first30 development outputs."""
from pathlib import Path
from collections import Counter, defaultdict
import gzip, hashlib, json
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
oldpath=ROOT/'experiments/wsp-vlm-open-repair-v8x50-2026-11-05/B-analysis/evidence.json.gz'
old=json.loads(gzip.decompress(oldpath.read_bytes()))
r=ROOT/'experiments/wsp-vlm-mechanism-repair-v9-2026-11-05/search-B'
evals8={e['candidate']:e for e in old['evaluations']}
v8=[evals8[x['candidate']] for x in old['rounds']]
w0=next(e for e in old['evaluations'] if e['candidate'].startswith('w0-'))
w={s['request_id']:s for s in w0['scored']};ids=sorted(w);wrong={i for i in ids if not w[i]['correct']}
v9=[];sources={str(oldpath.relative_to(ROOT)):hashlib.sha256(oldpath.read_bytes()).hexdigest()}
for p in sorted(r.glob('turn-*-request.json')):
 req=json.loads(p.read_text())
 if req.get('request',{}).get('op')!='evaluate':continue
 f=p.with_name(p.name.replace('request','response'));a=json.loads(f.read_text())
 if a['failed']:continue
 val=a['value'];e=val['results'][val['candidate']]
 if not e['full_development']:continue
 if len(v9)>=30:break
 base=val['results'][w0['candidate']]
 assert [(s['request_id'],s['parsed'],s['correct'],s['answer']) for s in base['scored']]==[(s['request_id'],s['parsed'],s['correct'],s['answer']) for s in w0['scored']]
 v9.append({k:e[k] for k in ['candidate','summary','scored']})
 sources[str(f.relative_to(ROOT))]=hashlib.sha256(f.read_bytes()).hexdigest()
assert len(v8)==50 and len(v9)==30

def rows(e):return {s['request_id']:s for s in e['scored']}
def repairs(e):return {i for i,s in rows(e).items() if i in wrong and s['correct']}
def damage(e):return {i for i,s in rows(e).items() if i not in wrong and not s['correct']}
def pairs(e):
 g=defaultdict(list)
 for s in e['scored']:
  if s['arm']=='B0':g[(s['group_id'],s['template'])].append(s['correct'])
 assert len(g)==116 and all(len(v)==2 for v in g.values())
 return {':'.join(k) for k,v in g.items() if all(v)}
def desc(e):
 rr=repairs(e);dd=damage(e);m=rows(e)
 return dict(candidate=e['candidate'],score=e['summary']['repair_score'],accuracy=e['summary']['accuracy'],repaired=sorted(rr),damaged=sorted(dd),changed=sum(m[i]['parsed']!=w[i]['parsed'] for i in ids),repair_direction=dict(Counter('down' if m[i]['parsed']<w[i]['parsed'] else 'up' for i in rr)),damage_direction=dict(Counter('down' if m[i]['parsed']<w[i]['parsed'] else 'up' for i in dd)))
for e in v8+v9:
 m=rows(e);assert sorted(m)==ids
 assert all(m[i]['answer']==w[i]['answer'] and m[i]['correct']==(m[i]['parsed']==m[i]['answer']) for i in ids)
 assert abs(e['summary']['repair_score']-len(pairs(e))/116)<1e-12
 assert abs(e['summary']['accuracy']-sum(s['correct'] for s in m.values())/464)<1e-12
r8=set.union(*(repairs(e) for e in v8));r9=set.union(*(repairs(e) for e in v9));p0=pairs(w0)
p8=p0.union(*(pairs(e) for e in v8));p9=p0.union(*(pairs(e) for e in v9))
stable8={i for i in wrong if all(rows(e)[i]['parsed']==w[i]['parsed'] for e in v8)}
new=sorted(r9-r8)
best9id=json.loads((r/'turn-0170-response.json').read_text())['budget']['best'];best9=next(e for e in v9 if e['candidate']==best9id)
best8=evals8[old['state']['best']]
comps={}
for label,e8,e9 in [('best8_best9',best8,best9),('round47_round30',v8[46],v9[29]),('round47_best9',v8[46],best9)]:
 a=rows(e8);b=rows(e9)
 comps[label]=dict(v8=desc(e8),v9=desc(e9),repair_overlap=sorted(repairs(e8)&repairs(e9)),v9_only_repairs=sorted(repairs(e9)-repairs(e8)),v8_only_repairs=sorted(repairs(e8)-repairs(e9)),v9_preserves_W0_on_v8_damage=sorted(damage(e8)-damage(e9)),joint_oracle_with_W0=len(p0|pairs(e8)|pairs(e9)),answer_oracle_with_W0=320+len(repairs(e8)|repairs(e9)))
coverage={}
for label,arr in [('v8',v8),('v9',v9),('combined',v8+v9)]:
 cov=wrong.intersection(set.union(*({i for i,s in rows(e).items() if s['correct']} for e in arr)))
 coverage[label]=dict(ever_repaired=len(cov),never_repaired=len(wrong-cov),repair_by_condition=dict(Counter(w[i]['condition'] for i in cov)),distinct_parsed_vectors=len({tuple(rows(e)[i]['parsed'] for i in ids) for e in arr}),same_as_W0_rounds=[j+1 for j,e in enumerate(arr) if all(rows(e)[i]['parsed']==w[i]['parsed'] for i in ids)])
examples=[]
for i in new:
 hits=[j+1 for j,e in enumerate(v9) if i in repairs(e)]
 examples.append(dict(id=i,gold=w[i]['answer'],W0=w[i]['parsed'],condition=w[i]['condition'],viewpoint=w[i]['viewpoint'],stratum=w[i]['stratum'],v8_unchanged=i in stable8,v9_repair_rounds=hits))
out=dict(status='ANALYZED_existing_outputs_only',rounds={'v8':50,'v9':30},inputs=464,source_groups=58,W0_correct=320,W0_wrong=144,W0_joint_correct=len(p0),baseline_parsed_and_labels_equal=True,coverage=coverage,repair_overlap=len(r8&r9),v9_unique_repair_count=len(r9-r8),v8_unique_repair_count=len(r8-r9),never_repaired_both=sorted(wrong-r8-r9),v8_unchanged_wrong_count=len(stable8),v8_unchanged_repaired_in_v9=sorted(stable8&r9),oracle_joint_pairs={'v8':len(p8),'v9':len(p9),'combined':len(p8|p9),'new_v9':sorted(p9-p8)},new_v9_examples=examples,comparisons=comps,v9_rounds=[dict(round=j+1,**desc(e)) for j,e in enumerate(v9)],source_sha256=sources)
(OUT/'analysis.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
with gzip.open(OUT/'v9-scored-evidence.json.gz','wt') as f:json.dump(dict(evaluations=v9,source_sha256=sources),f)
print(json.dumps({k:v for k,v in out.items() if k not in ['v9_rounds','source_sha256','never_repaired_both','comparisons']},ensure_ascii=False,indent=2))
for k,v in comps.items():print(k,json.dumps(v,ensure_ascii=False))
