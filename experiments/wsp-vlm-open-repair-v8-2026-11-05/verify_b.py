"""Check B's batch-64 W0 and historical edited outputs, no new patch search."""
import json,time
from pathlib import Path
from common import HERE,write_json,file_hash
from weights import TensorSource,Candidates
from evidence import Evidence
from backend import VLMBackend
start=time.time();cfg=json.loads((HERE/'config-B.json').read_text())
source=TensorSource(cfg['model_root'],cfg['aliases']);evidence=Evidence(cfg['evidence_root'],cfg['evidence_sha256'])
old=HERE.parents[1]/'external/wsp-vlm-open-repair-v7-2026-11-05/search-B'
candidates=Candidates(source,old/'candidates',cfg['contract']['temporary_scalars'],cfg['contract']['final_scalars'])
backend=VLMBackend(cfg,source,evidence)
prior=json.loads((old/'actions/turn-0018/response.json').read_text())['value'];candidate=prior['candidate'];records=list(evidence.records.values())
trials=[];chosen=None
for bs in (64,32,16,8,4):
 panels=[]
 for cid in (candidates.base_id,candidate):
  outputs=[];t=time.time()
  with backend.candidate(candidates,cid):
   for offset in range(0,len(records),bs):outputs.extend(backend.generate_batch([r['input'] for r in records[offset:offset+bs]],candidates,cid,600))
  reference={r['request_id']:r for r in prior['results'][cid]['predictions']}
  different=[r['request_id'] for r in outputs if r['generated_ids']!=reference[r['request_id']]['generated_ids']]
  panels.append({'candidate':cid,'inputs':len(outputs),'seconds':time.time()-t,'mismatches':different})
  write_json(HERE/f'B-batch-{bs}-{cid[:10]}-outputs.json',outputs)
 trials.append({'batch_size':bs,'panels':panels})
 if all(not p['mismatches'] for p in panels):chosen=bs;break
if chosen is None:raise RuntimeError('B batch equivalence failed; no search launched')
write_json(HERE/'batch-acceptance-B.json',{'accepted':True,'backend_sha256':file_hash(HERE/'backend.py'),'batch_size':chosen,'trials':trials,'elapsed_seconds':time.time()-start,'engineering_only':True,'physical_gpu':0,'peak_reserved_gib':backend.torch.cuda.max_memory_reserved()/2**30})
cfg['execution_batch_size']=chosen;write_json(HERE/'config-B.json',cfg)
print(json.dumps({'accepted':True,'batch_size':chosen,'seconds':time.time()-start,'trials':trials}),flush=True)
