"""Record a demonstrably unaccepted CPU request; never execute its code."""
from pathlib import Path
import json,sys,base64,fcntl,hashlib,subprocess,datetime
request=json.loads(base64.b64decode(sys.argv[1]));assert request['id']=='turn-048' and request['kind']=='python'
r=Path('/workspace/acupuncture/external/wsp/fleet-v1/math-0p8b');p=r/'actions'/request['id']
with (r/'broker.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not p.exists(),'Action exists: inspect it instead of overwriting/replaying'
 assert not [x for x in (r/'actions').iterdir() if x.is_dir() and not (x/'response.json').exists()]
 assert not subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
 state=json.loads((r/'state.json').read_text());previous=json.loads((r/'actions/turn-047/response.json').read_text())
 assert state==previous['state'] and state['python_attempts']==25 and state['forward_success']==19
 assert not (r/'work/natural_repetition_scores.npy').exists()
 proof={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action_directory_absent_before_reconciliation':True,'broker_lock_free':True,'gpu_idle':True,'state_unchanged_from_turn047':True,'python_attempts':25,'forward_success':19,'gpu_seconds':state['gpu_seconds'],'executed_or_replayed':False,'cpu_code_not_evaluated':True}
 p.mkdir();(p/'input.json').write_text(json.dumps(request,indent=2));(p/'request.sha256').write_text(hashlib.sha256(json.dumps(request,sort_keys=True).encode()).hexdigest());(p/'transport-reconciliation.json').write_text(json.dumps(proof,indent=2))
 result={'id':request['id'],'failed':True,'not_accepted':True,'state':state,'editor_output':'SSH disconnected before this Python action was accepted. Observer verified that its action directory did not exist, the ledger was unchanged from the preceding response, and no worker remained. This code was NOT executed and no Python/GPU budget was consumed by it. The Python kernel is gone: variables must be reconstructed from your own saved files before continuing. Saved weights and all completed results persist. No model action was replayed.'}
 q=p/'response.pending';q.write_text(json.dumps(result,indent=2));q.replace(p/'response.json');print(json.dumps(proof,indent=2))
