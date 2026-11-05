"""Read-only status, no model imports. Works on server and local evidence copies."""
import datetime,json,shutil,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
root=HERE.parents[1]
result=dict(timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),runs={},disks={})
for task in 'BC':
    path=root/'external/wsp-vlm-open-repair-v7-2026-11-05'/('search-'+task)
    state=path/'state.json'
    if state.exists():
        s=json.loads(state.read_text())
        result['runs'][task]={k:v for k,v in s.items() if k!='evaluations'}
        result['runs'][task].update(evaluations=len(s['evaluations']),elapsed_seconds=time.time()-s['started_unix'],
            budget_seconds_remaining=max(0,7200-(time.time()-s['started_unix'])))
    else:result['runs'][task]={'status':'not_started'}
for path in (root,Path('/tmp')):
    d=shutil.disk_usage(path);result['disks'][str(path)]={'free_gib':d.free/2**30}
gpu=shutil.which('nvidia-smi')
if gpu:result['gpu']=subprocess.run([gpu,'--query-gpu=index,memory.used,utilization.gpu','--format=csv,noheader'],capture_output=True,text=True).stdout
print(json.dumps(result,ensure_ascii=False,indent=2))
