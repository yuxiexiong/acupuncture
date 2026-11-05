"""GPU-1 engineering throughput/equivalence trial; no task-score-based selection."""
import json,time,traceback,os
from pathlib import Path
from types import SimpleNamespace
from common import HERE,write_json,file_hash
from weights import TensorSource,Candidates
from evidence import Evidence
from backend import VLMBackend
start=time.time();deadline=start+600
cfg=json.loads((HERE.parent/'wsp-vlm-open-repair-v7-2026-11-05/config-C.json').read_text())
source=TensorSource(cfg['model_root'],cfg['aliases']);evidence=Evidence(cfg['evidence_root'],cfg['evidence_sha256'])
candidates=Candidates(source,Path(cfg['run_root']).parent/'search-B/candidates',cfg['contract']['temporary_scalars'],cfg['contract']['final_scalars'])
backend=VLMBackend(cfg,source,evidence);backend.initialize();torch=backend.torch
# Interleave all conditions/wordings and source groups, independent of correctness.
records=list(evidence.records.values());buckets={}
for row in records:
 g=row['gold'];key=(g['condition'],g['template'],g['arm'],g.get('order',g.get('option_order','')))
 buckets.setdefault(key,[]).append(row)
selected=[]
while len(selected)<256:
 for key in sorted(buckets):
  if buckets[key] and len(selected)<256:selected.append(buckets[key].pop(0))
requests=[r['input'] for r in selected]
prior={p['request_id']:p for p in evidence.package['previous_predictions']}
results=[];last_peak=None
for bs in (4,8,16,32,64,128,256):
 if time.time()>=deadline:break
 total=torch.cuda.get_device_properties(0).total_memory
 base=torch.cuda.memory_allocated()
 if last_peak and base+max(0,last_peak-base)*2.6+12*2**30>total*.9:
  results.append({'batch_size':bs,'skipped':'projected peak plus 12GiB reserve exceeds 90% VRAM'});break
 torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats();t=time.time();out=[]
 try:
  with backend.candidate(candidates,candidates.base_id):
   for offset in range(0,len(requests),bs):
    out.extend(backend.generate_batch(requests[offset:offset+bs],candidates,candidates.base_id,deadline-time.time()))
  elapsed=time.time()-t
  mismatches=[x['request_id'] for x in out if any(x[k]!=prior[x['request_id']][k] for k in ('generated_ids','input_ids_sha256','rendered_chat_sha256','processed_hw'))]
  peak=torch.cuda.max_memory_allocated();last_peak=peak
  result={'batch_size':bs,'inputs':len(out),'seconds':elapsed,'inputs_per_second':len(out)/elapsed,'peak_allocated_gib':peak/2**30,'peak_reserved_gib':torch.cuda.max_memory_reserved()/2**30,'mismatches':mismatches}
  results.append(result);write_json(HERE/f'batch-{bs}-outputs.json',out)
 except Exception as exc:
  results.append({'batch_size':bs,'failed':repr(exc),'traceback':traceback.format_exc()});break
 write_json(HERE/'batch_trials.json',{'trials':results,'started_unix':start});print(json.dumps(result),flush=True)
valid=[r for r in results if r.get('inputs')==len(requests) and not r['mismatches'] and r['peak_reserved_gib']<total/2**30-12]
if not valid:
 write_json(HERE/'batch_trials.json',{'trials':results,'started_unix':start});raise RuntimeError('No equivalent safe batch size')
best=max(r['inputs_per_second'] for r in valid);chosen=min((r for r in valid if r['inputs_per_second']>=best*.95),key=lambda r:r['batch_size'])
# Verify actual edited weights, natural outputs, and exception rollback as engineering only.
request=json.loads((Path(cfg['run_root']).parent/'search-B/actions/turn-0018/request.json').read_text());candidate=request['request']['candidate']
probe=requests[:2]
seq=[backend.generate(q,candidates,candidate,deadline-time.time()) for q in probe]
with backend.candidate(candidates,candidate):batch=backend.generate_batch(probe,candidates,candidate,deadline-time.time())
if [x['generated_ids'] for x in seq]!=[x['generated_ids'] for x in batch]:raise RuntimeError('Edited batch differs from sequential')
class Expected(Exception):pass
try:
 with backend.candidate(candidates,candidate):raise Expected()
except Expected:pass
restored=backend.generate(probe[0],candidates,candidates.base_id,deadline-time.time())
if restored['generated_ids']!=prior[probe[0]['request_id']]['generated_ids']:raise RuntimeError('W0 rollback mismatch')
receipt={'accepted':True,'physical_gpu':os.environ.get('CUDA_VISIBLE_DEVICES'),'chosen_batch_size':chosen['batch_size'],'choice':'smallest within 5% of best measured throughput, >=12GiB reserved headroom','trials':results,'edited_equivalence':True,'rollback':True,'new_model_calls':sum(r.get('inputs',0) for r in results)+5,'elapsed_seconds':time.time()-start,'engineering_only':True,'source_hashes':{n:file_hash(HERE/n) for n in ('backend.py','service.py','live.py','broker.py','benchmark_batch.py')}}
write_json(HERE/'batch_acceptance.json',receipt)
cfg['execution_batch_size']=chosen['batch_size'];cfg['physical_gpu']=1
cfg['authorization_record']['parallel_and_batch_update']='User 2026-11-05: H20 GPU1 run C; enlarge inference batches, improve throughput while retaining memory headroom'
write_json(HERE/'config-C.json',cfg)
print(json.dumps({'accepted':True,'chosen':chosen,'total_engineering_seconds':receipt['elapsed_seconds']}),flush=True)
