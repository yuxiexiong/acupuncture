"""Append a specifically reviewed recovery after the existing fleet releases its jobs."""
import argparse
import fcntl
import json
from pathlib import Path
import subprocess
import sys
import time

import fleet


def run(config, root):
    cfg=json.loads(config.read_text());root.mkdir(parents=True,exist_ok=True)
    lock=(root/'recovery.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    state=root/'state.json'
    if state.exists():raise RuntimeError('RECOVERY_ALREADY_STARTED: inspect existing evidence')
    record=dict(status='waiting_for_fleet',started=time.time(),config=str(config))
    fleet.write(state,record)
    try:
        while True:
            prior=json.loads(Path(cfg['wait_state']).read_text())
            if prior['status'] in ('finished','finished_with_skips'):break
            if prior['status']!='running':raise RuntimeError('UNKNOWN_FLEET_STATE')
            time.sleep(10)
        jobs=json.loads(Path(cfg['fleet_config']).read_text())['jobs']
        fleet.check_previous_idle(jobs)
        if fleet.sha(fleet.MATH/'controller.py')!=cfg['controller_sha256']:raise RuntimeError('RECOVERY_SOURCE_CHANGED')
        with (root/'process.log').open('a') as log:
            p=subprocess.Popen([sys.executable,str(fleet.MATH/'controller.py'),'--config',cfg['controller_config']],stdout=log,stderr=subprocess.STDOUT)
            record.update(status='running',pid=p.pid);fleet.write(state,record)
            record['exit_code']=p.wait()
        if record['exit_code']:raise RuntimeError('RECOVERY_CHILD_FAILED: see process.log')
        controller=json.loads(Path(cfg['controller_config']).read_text())
        receipt=Path(controller['local_run_root'])/'receipt.json'
        result=json.loads(receipt.read_text())
        if result['status']!='completed':raise RuntimeError('NO_COMPLETED_RECEIPT')
        record.update(status='completed',receipt=str(receipt),receipt_sha256=fleet.sha(receipt))
    except Exception as exc:
        record.update(status='blocked_engineering',error=str(exc),needs_review=True)
    finally:
        record['updated']=time.time();fleet.write(state,record);lock.close()
    return record


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();print(json.dumps(run(args.config,args.out)))
