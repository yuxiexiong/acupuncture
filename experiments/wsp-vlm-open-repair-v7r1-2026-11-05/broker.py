"""Durable request files decouple the observer from an SSH connection."""
import argparse,fcntl,json,time
from pathlib import Path
from common import write_json
from live import build_service

def ready(root):
    if not root.exists():return True
    with (root/'observer.lock').open('a') as f:
        try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:return False
    return all((p/'response.json').exists() for p in (root/'actions').iterdir())

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);a=p.parse_args()
    config=json.loads(a.config.read_text());root=Path(config['run_root']);resume=root.exists()
    deadline=(json.loads((root/'state.json').read_text())['started_unix'] if resume else time.time())+config['contract']['wall_seconds']
    while not ready(root):
        if time.time()>=deadline:raise SystemExit('Prior action did not settle inside original budget')
        time.sleep(2)
    service=build_service(config,resume=resume)
    if resume:
        from batch_acceptance import validate
        validate(service)
    else:
        from common import HERE,file_hash
        receipt=json.loads((HERE/'batch_acceptance.json').read_text())
        if not receipt['accepted'] or any(file_hash(HERE/n)!=h for n,h in receipt['source_hashes'].items()):
            raise RuntimeError('Batch implementation acceptance missing or changed')
    inbox=root/'inbox';inbox.mkdir(exist_ok=True)
    write_json(root/'broker-r1-ready.json',{'resumed':resume,'time_unix':time.time(),'original_started_unix':service.state['started_unix']})
    try:
        while service.remaining()>0 and not service.state['research_done']:
            for f in sorted(inbox.glob('*.json')):
                action=json.loads(f.read_text())
                if not (root/'actions'/action['id']/'response.json').exists():service.dispatch(action)
            time.sleep(.5)
    finally:service.close()
