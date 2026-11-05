"""B uses a new, matched batch-64 comparison regime; do not claim batch-1 equivalence."""
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
prior=json.loads((old/'actions/turn-0018/response.json').read_text())['value'];candidate=prior['candidate'];records=list(evidence.records.values());panels=[]
for cid in (candidates.base_id,candidate):
 reference=json.loads((HERE/f'B-batch-64-{cid[:10]}-outputs.json').read_text());ref={r['request_id']:r for r in reference};old_ref={r['request_id']:r for r in prior['results'][cid]['predictions']}
 outputs=[];t=time.time()
 with backend.candidate(candidates,cid):
  for offset in range(0,len(records),64):outputs.extend(backend.generate_batch([r['input'] for r in records[offset:offset+64]],candidates,cid,600))
 repeat=[r['request_id'] for r in outputs if r['generated_ids']!=ref[r['request_id']]['generated_ids']]
 inputs=[r['request_id'] for r in outputs if any(r[k]!=old_ref[r['request_id']][k] for k in ('input_ids_sha256','rendered_chat_sha256','processed_hw'))]
 old_differences=[r['request_id'] for r in outputs if r['generated_ids']!=old_ref[r['request_id']]['generated_ids']]
 panel={'candidate':cid,'inputs':len(outputs),'seconds':time.time()-t,'repeat_mismatches':repeat,'input_mismatches':inputs,'batch1_answer_differences':old_differences};panels.append(panel)
 write_json(HERE/f'B-batch-64-repeat-{cid[:10]}.json',outputs);print(json.dumps(panel),flush=True)
 if repeat or inputs:raise RuntimeError('Batch-64 repeat or input identity check failed')
write_json(HERE/'batch-acceptance-B.json',{'accepted':True,'backend_sha256':file_hash(HERE/'backend.py'),'batch_size':64,'panels':panels,'elapsed_seconds':time.time()-start,'engineering_only':True,'physical_gpu':0,'peak_reserved_gib':backend.torch.cuda.max_memory_reserved()/2**30,'batch1_equivalent':False,'require_fresh_full_batch64_baseline':True,'claim_boundary':'Only within-batch64 repair comparisons; do not count batch1-to-batch64 answer changes as WSP effect'})
