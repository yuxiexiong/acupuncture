"""Read archived tensors on CPU; no model imports or forwards."""
import hashlib
import json
import os
from pathlib import Path
import time
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import torch
torch.set_num_threads(2)
root=Path('/workspace/acupuncture')
manifest=json.loads(Path('/tmp/acupuncture-output-path-audit-20261101-r01/input-manifest.json').read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
 return h.hexdigest()
started=time.time();out={'model_calls':0,'gpu_calls':0,'items':{},'sources':[]}
for unit in manifest['units']:
 spec=unit['bridge'];p=root/spec['tensor'];assert sha(p)==spec['tensor_sha256']
 rec=json.loads((root/spec['record']).read_text());assert sha(root/spec['record'])==spec['record_sha256']
 tb=torch.load(p,map_location='cpu',weights_only=True)
 c=tb['logits']['C'].double();a=int(rec['scores']['C']['nonstop_winner'])
 ids=list(dict.fromkeys([a,248044,248046,248068]))
 row={'clean_first_token':a,'scores':{},'conv_shapes':{k:list(v.shape) for k,v in tb['deep']['C'].items() if k.endswith(':conv_states')}}
 for name in ('C','T_native','Y_T','Y_CT','Y_TC'):
  z=tb['logits'][name].double();mean=z.mean();lp=z-torch.logsumexp(z,0)
  row['scores'][name]={str(t):{'logit':float(z[t]),'centered_logit':float(z[t]-mean),'logprob':float(lp[t])} for t in ids}
 out['items'][unit['id']]=row
 out['sources'].append({'tensor':spec['tensor'],'sha256':spec['tensor_sha256'],'record':spec['record'],'record_sha256':spec['record_sha256']})
 del tb
out['seconds']=time.time()-started
print(json.dumps(out,ensure_ascii=False,indent=2))
