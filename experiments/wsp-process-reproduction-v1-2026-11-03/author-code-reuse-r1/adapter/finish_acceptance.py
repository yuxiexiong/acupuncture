"""Finish only the bounded acceptance after other jobs release GPUs. Never runs author actions."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

here=Path(__file__).resolve().parent
cfgpath=here.parent/'acceptance-config.json'
cfg=json.loads(cfgpath.read_text()); root=Path(cfg['run_root'])
assert cfg['forward_limit']==3 and cfg['gpu_seconds_limit']==3000 and not cfg['authorized']
lock=open(root/'acceptance-wait.lock','a')
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)


def idle(count):
    deadline=time.monotonic()+1800
    while time.monotonic()<deadline:
        rows=subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True)
        cards=[int(a) for a,b,c in (s.split(',') for s in rows.splitlines()) if int(b)<128 and int(c)==0]
        if len(cards)>=count:
            return cards[:count]
        print('Waiting for free GPUs; no jobs interrupted',flush=True)
        time.sleep(15)
    raise TimeoutError('Acceptance waiting deadline; formal execution remains disabled')


print(json.dumps({'pid':os.getpid(),'scope':'acceptance only','formal_started':False}),flush=True)
idle(2)
subprocess.run([sys.executable,str(here/'acceptance.py'),'--config',str(cfgpath),'--retry-suffix','r3'],check=True)
card=idle(1)[0]
gpu_lock=open(Path('/workspace/acupuncture/external/wsp')/f'engineering-gpu-{card}.lock','a')
fcntl.flock(gpu_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
start=time.monotonic()
try:
    subprocess.run([sys.executable,str(here/'numeric_check.py'),str(root)],check=True,timeout=600,
                   env=dict(os.environ,CUDA_VISIBLE_DEVICES=str(card)))
finally:
    (root/'reference-usage.json').write_text(json.dumps({'gpu_seconds':time.monotonic()-start,'gpu_slots':[card],'hard_limit_seconds':600},indent=2)+'\n')
print('BOUNDED_ACCEPTANCE_FINISHED; no formal launch',flush=True)
