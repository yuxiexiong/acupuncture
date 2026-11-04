"""One-shot budget amendment at a durable action boundary. No model calls."""
from pathlib import Path
import os,json,signal,time,fcntl,hashlib,datetime,sys
root=Path('/workspace/acupuncture/external/wsp/fleet-v1/math-0p8b')
cfg=Path('/workspace/acupuncture/external/wsp/fleet-v1/configs/math-0p8b.json')
a=root/'actions/turn-059';audit=root/'budget-amendment-r1'
if not (a/'response.json').exists():
 print(json.dumps({'status':'waiting_current_forward'}));sys.exit(0)
response=json.loads((a/'response.json').read_text());state=json.loads((root/'state.json').read_text())
assert response['id']=='turn-059' and response['state']==state
assert state['forward_attempts']==24 and state['python_attempts']==32
assert state['forward_success'] in [22,23]
assert not (root/'actions/turn-060').exists()
assert not [p for p in (root/'actions').iterdir() if p.is_dir() and not (p/'response.json').exists()]
if (audit/'receipt.json').exists():
 print((audit/'receipt.json').read_text());sys.exit(0)
old=json.loads(cfg.read_text());assert old==json.loads((root/'config.json').read_text())
assert old['gpu_seconds_limit']==28800 and old['forward_limit']==50
worker=json.loads((a/'process.json').read_text())['pid']
assert not Path('/proc/'+str(worker)).exists(),'GPU worker has not exited'
pid=1297889;proc=Path('/proc/'+str(pid))
if proc.exists():
 cmd=(proc/'cmdline').read_bytes().replace(b'\0',b' ').decode()
 assert 'broker.py' in cmd and str(cfg) in cmd
 os.kill(pid,signal.SIGINT)
lock=(root/'broker.lock').open('a')
for _ in range(60):
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);break
 except BlockingIOError:time.sleep(1)
else:raise RuntimeError('OLD_BROKER_NOT_STOPPED')
assert json.loads((root/'state.json').read_text())==state
assert not audit.exists(),'Partial amendment requires review'
audit.mkdir();(audit/'external-config.before.json').write_bytes(cfg.read_bytes());(audit/'run-config.before.json').write_bytes((root/'config.json').read_bytes());(audit/'state.before.json').write_bytes((root/'state.json').read_bytes())
new=dict(old,gpu_seconds_limit=172800)
assert [k for k in old if old[k]!=new[k]]==['gpu_seconds_limit']
for p in [cfg,root/'config.json']:
 q=p.with_suffix('.budget-pending');q.write_text(json.dumps(new,indent=2)+'\n');q.replace(p)
receipt={'status':'applied','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'authorization':'User 2026-11-04: increase only0.8B math budget enough to finish50 successful passes; other experiments unchanged','old_gpu_seconds_limit':28800,'new_gpu_seconds_limit':172800,'forward_limit':50,'state_preserved':state,'response_sha256':hashlib.sha256((a/'response.json').read_bytes()).hexdigest(),'only_changed_key':'gpu_seconds_limit','inflight_result_preserved':True}
(audit/'config.after.json').write_text(json.dumps(new,indent=2));(audit/'receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
