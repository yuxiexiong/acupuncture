"""Review archived COMBO JSON endpoints using fixed receipt hashes; no model or tensor loading."""
import argparse
import hashlib
import json
from pathlib import Path
import time
p=argparse.ArgumentParser();p.add_argument('root');p.add_argument('manifest');args=p.parse_args()
root=Path(args.root);mf=json.loads(Path(args.manifest).read_text());start=time.time()
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
 return h.hexdigest()
out={'source_commit':mf['source_commit'],'model_calls':0,'gpu_calls':0,'items':[],'tensors_checked':False}
for unit in mf['units']:
 recpath=root/unit['record'];assert sha(recpath)==unit['record_sha256']
 x=json.loads(recpath.read_text());sc=x['scores'];a=str(x['scores']['B:C']['nonstop_winner'])
 metric={'D':{k:s['stop_advantage'] for k,s in sc.items()},'stop_minus_a':{k:s['token_logits']['248046']-s['token_logits'][a] for k,s in sc.items()}}
 results={}
 for m,z in metric.items():
  gt=z['S=T,F=T,K=T']-z['S=T,F=C,K=T'];gc=z['S=C,F=T,K=T']-z['S=C,F=C,K=T'];delta=z['S=T,F=T,K=T']-z['S=C,F=C,K=C']
  results[m]={'G_T':gt,'G_C':gc,'S_F_interaction':gt-gc,'deep_delta':delta,'G_T_over_deep':gt/delta if abs(delta)>=1 else None,'G_C_over_deep':gc/delta if abs(delta)>=1 else None}
 # Older TC/T F addition is a different estimand from present F_V addition.
 z=metric['D'];pair=x['pairs']['TC|T'];d=z[pair['SFK']]-z[pair['0']]
 results['old_TC_T_F']={'add':z[pair['F']]-z[pair['0']],'delta':d,'ratio':(z[pair['F']]-z[pair['0']])/d}
 out['items'].append({'id':unit['id'],'candidate':int(a),'results':results})
out['ranges']={m:{v:[min(row['results'][m][v] for row in out['items'] if row['results'][m][v] is not None),max(row['results'][m][v] for row in out['items'] if row['results'][m][v] is not None)] for v in out['items'][0]['results'][m]} for m in out['items'][0]['results']}
out['seconds']=time.time()-start
print(json.dumps(out,ensure_ascii=False,indent=2))
