"""Run authorized B then C once; infrastructure errors stop the queue for repair."""
import datetime,json,os,subprocess,sys,time
from pathlib import Path
from common import HERE,write_json

identity=HERE/'sequence.json'
with identity.open('x') as f:
    json.dump(dict(status='starting',pid=os.getpid(),started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()),f)
stages=[]
for task in 'BC':
    started=time.time()
    write_json(identity,dict(status='running',task=task,pid=os.getpid(),completed=stages,started_unix=started))
    with (HERE/('search-'+task+'.log')).open('x') as log:
        p=subprocess.run([sys.executable,str(HERE/'remote_search.py'),'--task',task,'--config',str(HERE/('config-'+task+'.json'))],stdout=log,stderr=log)
    stages.append(dict(task=task,returncode=p.returncode,elapsed_seconds=time.time()-started))
    if p.returncode:
        write_json(identity,dict(status='stopped_on_error',failed=task,stages=stages));raise SystemExit(p.returncode)
write_json(identity,dict(status='complete',stages=stages))
