"""Read-only round progress and GPU/disk status; no model imports."""
import json,time,shutil,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;root=HERE.parents[1]
out={'time_unix':time.time(),'runs':{},'disks':{}}
for task in 'BC':
 p=root/f'external/wsp-vlm-open-repair-v8-2026-11-05/{task}/state.json'
 if not p.exists():out['runs'][task]={'status':'not_started'};continue
 s=json.loads(p.read_text());out['runs'][task]={k:s.get(k) for k in ('actions','forwards','samples','best','current','research_done','frozen','repair_rounds_completed')}
 out['runs'][task].update(round_target=30,elapsed_minutes=(time.time()-s['started_unix'])/60,wall_deadline=None,evaluations=len(s['evaluations']))
for p in (root,Path('/tmp')):out['disks'][str(p)]={'free_gib':shutil.disk_usage(p).free/2**30}
if shutil.which('nvidia-smi'):out['gpu']=subprocess.run(['nvidia-smi','--query-gpu=index,utilization.gpu,memory.used,memory.total','--format=csv,noheader'],capture_output=True,text=True).stdout
print(json.dumps(out,ensure_ascii=False,indent=2))
