"""Freeze user-authorized 30-repair-round contracts; reuse verified batch backend."""
import json
from pathlib import Path
from common import HERE,write_json,file_hash,packed,digest
old=HERE.parent/'wsp-vlm-open-repair-v7r2-2026-11-05'
accept=json.loads((old/'batch_acceptance.json').read_text())
if not accept['accepted'] or file_hash(HERE/'backend.py')!=accept['source_hashes']['backend.py']:raise RuntimeError('Batch backend changed')
for task,groups,inputs in [('B',58,464),('C',64,2560)]:
 cfg=json.loads((HERE.parent/f'wsp-vlm-open-repair-v7-2026-11-05/config-{task}.json').read_text())
 cfg.update(task=task,researcher_usage_mode="thread_cumulative",execution_batch_size=64,physical_gpu=0 if task=='B' else 1,run_root=str(HERE.parents[1]/f'external/wsp-vlm-open-repair-v8-2026-11-05/{task}'))
 c=cfg['contract'];c.update(wall_seconds=None,repair_rounds=30,actions=2000,researcher_turns=2000,python_seconds=36000,researcher_tokens=50000000,forwards=inputs*30*5,samples=inputs*30*5,target_tokens=inputs*30*5*(4096+128))
 cfg['contract_sha256']=digest(packed(c))
 cfg['authorization_record']['2026-11-05_update']='User: GPU1 C, GPU0 B reuse verified batching; cancel hard GPU wall deadlines; each card 30 candidate-weight repair plus full-development evaluation rounds. Diagnosis does not count.'
 write_json(HERE/f'config-{task}.json',cfg)
 if task=='C':write_json(HERE/'batch-acceptance-C.json',{'accepted':True,'backend_sha256':file_hash(HERE/'backend.py'),'reused_real_receipt':str(old/'batch_acceptance.json'),'reused_receipt_sha256':file_hash(old/'batch_acceptance.json'),'batch_size':64,'physical_gpu':1,'full_new_baseline_required':True})
