"""One-shot authorized reconciliation. No model invocation, no request replay."""
from pathlib import Path
import json,fcntl,hashlib,subprocess,datetime
r=Path('/workspace/acupuncture/external/wsp/fleet-v1/math-0p8b')
a=r/'actions/turn-012';audit=r/'recovery-author-alignment-r1'
with (r/'broker.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not audit.exists(),'Reconciliation already recorded; inspect, never double charge'
 assert not (a/'response.json').exists()
 pending=[p.name for p in (r/'actions').iterdir() if p.is_dir() and not (p/'response.json').exists()]
 assert pending==['turn-012'],pending
 gpu=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True)
 assert not gpu.strip(),gpu
 state=json.loads((r/'state.json').read_text());assert state['forward_success']==4 and state['forward_attempts']==5
 assert abs(state['gpu_seconds']-2325.3487739041448)<1e-6
 proc=json.loads((a/'process.json').read_text())
 assert not Path('/proc/'+str(proc['pid'])).exists(),'worker still exists'
 request=json.loads((a/'input.json').read_text())
 assert hashlib.sha256(json.dumps(request,sort_keys=True).encode()).hexdigest()==(a/'request.sha256').read_text()
 assert not list(a.glob('pass_*.public.json')) and not list(a.glob('*.raw.jsonl'))
 idle=Path('/workspace/acupuncture/external/wcp01/user-stop-20261104/gpu-after.txt')
 assert idle.read_text()=='0, 0 %, 3 MiB\n1, 0 %, 3 MiB\n'
 charge=len(proc['gpu_slots'])*(idle.stat().st_mtime-proc['started_unix'])
 assert 1031.97<=charge<1600
 audit.mkdir();(audit/'state.before.json').write_bytes((r/'state.json').read_bytes())
 record={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'turn-012','reason':'user stop; authorized resume of 0.8B math only','charge_gpu_seconds_upper_bound':charge,'charge_lower_bound_until_term':1031.974169254303,'method':'allocated slots times elapsed until saved GPU-idle observation mtime; conservative upper bound, not exact compute time','gpu_idle_evidence':str(idle),'gpu_idle_mtime':idle.stat().st_mtime,'forward_success_unchanged':4,'request_replayed':False}
 (audit/'accounting.json').write_text(json.dumps(record,indent=2))
 state['gpu_seconds']+=charge
 for p,obj in [(r/'state.json',state),(a/'response.json',{'id':'turn-012','failed':True,'user_stopped':True,'editor_output':'The experimenter stopped this forward request before completion, then authorized continuation. No complete output was saved; this request does not count as a successful pass. Its interrupted GPU time has been charged conservatively to the existing budget. Previous successful outputs and weight files persist. Continue your experiment from the saved state.','state':state,'reconciliation_record':str(audit/'accounting.json')})]:
  q=p.with_suffix('.pending');q.write_text(json.dumps(obj,indent=2));q.replace(p)
 print(json.dumps({'accounting':record,'state':state,'remaining_gpu_seconds':28800-state['gpu_seconds']},indent=2))
