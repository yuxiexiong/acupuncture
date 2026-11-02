import json,hashlib,re,math,random
from pathlib import Path
r=Path(__file__).resolve().parents[2]; d=Path(__file__).resolve().parent
m=json.loads((d/'design-manifest.json').read_text()); checks={}
checks['source_hashes']=all(hashlib.sha256((r/p).read_bytes()).hexdigest()==h for p,h in m['source_sha256'].items())
checks['inputs48_unique']=len(m['inputs'])==len({i['id'] for i in m['inputs']})==48
checks['scenes6']=len({i['scene'] for i in m['inputs']})==6
b=m['budget'];checks['budget']= b['normal']['formations']==250 and b['normal']['decode_forwards_max']==14844 and b['with_one_preflight_retry']['decode_forwards_max']==15576
records=list((r/'experiments/cache-qk-component-factor-v1-2026-11-02/runs/formal-r01').glob('worker-*/records/*.json'))
checks['qkf_record_ids']=sorted(json.loads(p.read_text())['unit']['item_id'] for p in records)==sorted(i['id'] for i in m['inputs'])
hashes_ok=True
for w in (r/'experiments/cache-qk-component-factor-v1-2026-11-02/runs/formal-r01').glob('worker-*'):
 if not w.is_dir():continue
 for p,h in json.loads((w/'receipt.json').read_text())['record_hashes'].items():
  hashes_ok &= hashlib.sha256((w/p).read_bytes()).hexdigest()==h
checks['qkf_record_hashes']=hashes_ok
rng=random.Random(20261103)
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def proj(S,k):return [sum(S[i][j]*k[i] for i in range(4)) for j in range(3)]
def f(S,q,k,v,a,b):
 p=proj(S,k); z=dot(q,k)
 return [a*x+b*z*(y-a*t) for x,y,t in zip(proj(S,q),v,p)]
worst=0
for n in range(300):
 S=[[rng.uniform(-2,2) for _ in range(3)] for _ in range(4)]
 q,k0,k1=([rng.uniform(-2,2) for _ in range(4)] for _ in range(3)); v=[rng.uniform(-2,2) for _ in range(3)]
 a=0 if n%11==0 else rng.random();b=0 if n%13==0 else rng.random()
 if n%7==0:k1=k0[:]
 if n%5==0:k1=[-x for x in k0]
 a0,a1=dot(q,k0),dot(q,k1);p0,p1=proj(S,k0),proj(S,k1)
 y0,y1=f(S,q,k0,v,a,b),f(S,q,k1,v,a,b)
 S1=[[a*S[i][j]+b*k1[i]*(v[j]-a*p1[j]) for j in range(3)] for i in range(4)]
 direct=proj(S1,q)
 assert max(abs(x-y) for x,y in zip(direct,y1))<1e-10
 Jh=[b*((a1-a0)*(z-a*(x+y)/2)-a*(a1+a0)/2*(y-x)) for x,y,z in zip(p0,p1,v)]
 err=math.sqrt(sum((y-x-z)**2 for x,y,z in zip(y0,y1,Jh)))
 scale=max(1,math.sqrt(sum((y-x)**2 for x,y in zip(y0,y1))))
 worst=max(worst,err/scale)
checks['symmetric_identity_300_cases']=worst<1e-10
plan=r/'docs/cache-k-computation-diagnostic-plan-v1-2026-11-03.zh-CN.md';review=r/'docs/cache-qkd-self-check-v1-2026-11-03.zh-CN.md'
checks['C01_C14_E01_E26']=all(x in review.read_text() for x in [*[f'C{i:02}' for i in range(1,15)],*[f'E{i:02}' for i in range(1,27)]])
missing=[]
for p in [plan,review,d/'README.zh-CN.md']:
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' not in link and not (p.parent/link.split('#')[0]).exists():missing.append(link)
checks['local_links']=not missing
out={'status':'passed' if all(checks.values()) else 'failed','scope':'CPU_document_and_algebra_checks_only_not_model_acceptance','checks':checks,'identity_max_scaled_error':worst,'qkf_records_checked':len(records),'missing_links':missing,'new_model_runs':0,'independent_review':False,'files_sha256':{str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [plan,review,d/'design-manifest.json',d/'README.zh-CN.md']}}
(d/'delivery-check.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n'); print(json.dumps(out,ensure_ascii=False,indent=2)); assert all(checks.values())
