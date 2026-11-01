"""Verify the E2 reciprocal cell against fixed Git JSON; stdlib only."""
import hashlib
import json
from pathlib import Path
import sys
root=Path(sys.argv[1]); rows=[];sources={};maxdiff={k:0 for k in ('C','T_native','Y_T')}
def read(p):
 sources[str(p.relative_to(root))]=hashlib.sha256(p.read_bytes()).hexdigest()
 return json.loads(p.read_text())
e=root/'experiments/cache-formation-mechanism-e2-depth-transplant-v1-2026-10-31'
b=root/'experiments/cache-formation-readout-bridge-v1-2026-10-31'
for ep in sorted(e.glob('runs/formal-r01/worker-*/records/*.json')):
 x=read(ep);bp=next(b.glob('runs/formal-r01/worker-*/records/'+ep.name));y=read(bp)
 for p in (ep,bp):
  receipt=read(p.parent.parent/'receipt.json')
  assert receipt['record_hashes']['records/'+p.name]==sources[str(p.relative_to(root))]
 assert x['prompt_token_sha256']==y['prompt_token_sha256'] and x['b']==y['b']
 assert x['item']==y['item']
 d=lambda z:z['first_step']['stop_advantage']
 c,t,a,dv=d(x['natives']['00']),d(x['natives']['L0-01']),d(x['cells']['a']),d(x['cells']['d'])
 diffs={k:v-y['scores'][k]['stop_advantage'] for v,k in [(c,'C'),(t,'T_native'),(a,'Y_T')]}
 for k,v in diffs.items():maxdiff[k]=max(maxdiff[k],abs(v))
 rows.append({'id':ep.stem,'C':c,'T':t,'a':a,'d':dv,'a_ratio':(a-c)/(t-c),'d_ratio':(dv-c)/(t-c),'interaction':t-a-dv+c,'interaction_ratio':(t-a-dv+c)/(t-c),'D_route_differences':diffs})
assert len(rows)==12
result={'source_commit':'233ab5822a48099066ce7f948b25b0f915c9624f','scope':'E2 is a prior reciprocal-cache test; route endpoint proximity does not prove identical missing-cell output','items':rows,'endpoint_max_abs_D_difference':maxdiff,'ranges':{k:[min(r[k] for r in rows),max(r[k] for r in rows)] for k in ['a_ratio','d_ratio','interaction_ratio','interaction']},'sources':sources,'model_calls':0,'gpu_calls':0}
print(json.dumps(result,ensure_ascii=False,indent=2))
