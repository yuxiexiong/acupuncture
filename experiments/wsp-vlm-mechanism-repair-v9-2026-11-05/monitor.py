"""Read-only v9 evidence, cost, process and storage snapshot; no model loading."""
import json
from pathlib import Path
import shutil
import subprocess
import time
ROOT=Path(__file__).resolve().parents[2]
REL=Path(__file__).resolve().parent.name
result=dict(time_unix=time.time(),runs={},disks={})
for task in 'BC':
    root=ROOT/'external'/REL/task
    p=root/'state.json'
    if not p.exists():
        result['runs'][task]=dict(status='not_started');continue
    state=json.loads(p.read_text())
    row={k:state.get(k) for k in ('actions','samples','actual_target_tokens','python_seconds','best','current','research_done','frozen','repair_rounds_completed','round_budget_reached','storage_bytes')}
    row['elapsed_minutes']=(time.time()-state['started_unix'])/60
    row['round_target']=30
    counts={};last=None;failures=[]
    for f in sorted((root/'actions').glob('*/request.json')):
        action=json.loads(f.read_text());op=action.get('request',{}).get('op',action['kind'])
        counts[op]=counts.get(op,0)+1
        response=f.parent/'response.json';last=dict(action=f.parent.name,op=op,completed=response.exists(),modified_unix=(response if response.exists() else f).stat().st_mtime)
        if response.exists():
            r=json.loads(response.read_text())
            if r.get('failed'):failures.append(dict(action=f.parent.name,error=r.get('error',r.get('value',{}).get('output',''))[-1200:]))
    row.update(operation_counts=counts,last_action=last,recent_failures=failures[-3:])
    for e in state['evaluations'].values():
        p=root/e['path'];data=json.loads(p.read_text())
        if data['full_development'] and data['candidate'] in (state['best'],next((x for x in (state['best'],state['current']) if x.startswith('w0-')),'')):
            row.setdefault('summaries',{})[data['candidate']]=data['summary']
    receipt=root/'frozen-candidate.json'
    row['has_mechanism_report']=(root/'mechanism-report.json').exists()
    row['has_frozen_receipt']=receipt.exists()
    result['runs'][task]=row
for p in [ROOT,Path('/tmp')]:
    usage=shutil.disk_usage(p);result['disks'][str(p)]=dict(free_gib=usage.free/2**30,used_percent=100*usage.used/usage.total)
if shutil.which('nvidia-smi'):
    result['gpu']=subprocess.run(['nvidia-smi','--query-gpu=index,utilization.gpu,memory.used,memory.total','--format=csv,noheader'],capture_output=True,text=True).stdout
    result['gpu_processes']=subprocess.run(['nvidia-smi','--query-compute-apps=pid,gpu_uuid,used_memory','--format=csv,noheader'],capture_output=True,text=True).stdout
print(json.dumps(result,ensure_ascii=False,indent=2))
