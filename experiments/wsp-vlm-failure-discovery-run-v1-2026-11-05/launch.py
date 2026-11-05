"""Hard deadline supervisor. Defaults to dry validation; --execute needs run authorization."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent


def bounded(command,seconds,env=None):
    """Stop the whole child group, including a stuck model forward."""
    start=time.monotonic()
    parent_pid=os.getpid()
    def stop_if_parent_dies():
        import ctypes
        if ctypes.CDLL(None,use_errno=True).prctl(1,signal.SIGKILL)!=0:raise OSError('Cannot set parent-death signal')
        if os.getppid()!=parent_pid:os._exit(125)
    child=subprocess.Popen(command,env=env,start_new_session=True,
        preexec_fn=stop_if_parent_dies if sys.platform=='linux' else None)
    timed_out=False
    try:
        code=child.wait(timeout=seconds)
    except (subprocess.TimeoutExpired,KeyboardInterrupt):
        timed_out=True
        os.killpg(child.pid,signal.SIGTERM)
        try:child.wait(timeout=2)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGKILL)
            child.wait()
        code=child.returncode
    return dict(returncode=code,timed_out=timed_out,elapsed_seconds=time.monotonic()-start)


def reconcile(root,result,known):
    # Only reconcile this launch's receipt; a pre-existing running receipt is never erased.
    for path in root.glob('*/receipt.json'):
        if str(path) in known:continue
        receipt=json.loads(path.read_text())
        journal=path.with_name('attempts.jsonl')
        receipt['attempts']=len(journal.read_text().splitlines()) if journal.exists() else 0
        receipt['elapsed_seconds']=max(receipt['elapsed_seconds'],result['elapsed_seconds'])
        if receipt['status']=='running':
            receipt.update(status='interrupted',error='worker exited before closing receipt')
        receipt['supervisor']=result
        temp=path.with_suffix('.tmp');temp.write_text(json.dumps(receipt,indent=2)+'\n');temp.replace(path)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--task',choices=('B','C'),default='B')
    p.add_argument('--stage',choices=('P0','D','H'),required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--diagnosis',type=Path)
    p.add_argument('--execute',action='store_true')
    a=p.parse_args()
    command=[sys.executable,str(HERE/'runner.py'),'--task',a.task,'--stage',a.stage,'--out',str(a.out)]
    if a.diagnosis:command+=['--diagnosis',str(a.diagnosis)]
    if not a.execute:
        raise SystemExit(subprocess.call(command))
    a.out.mkdir(parents=True,exist_ok=True)
    with (a.out/'supervisor.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        known={str(path) for path in a.out.glob('*/receipt.json')}
        receipts=[json.loads(Path(path).read_text()) for path in known]
        if any(r['status']=='running' for r in receipts):raise RuntimeError('Unclosed run requires explicit reconciliation')
        remaining=43200-sum(r['elapsed_seconds'] for r in receipts)
        if remaining<=5:raise RuntimeError('No time left in cumulative budget')
        env=dict(os.environ,WSP_SUPERVISED='1',HF_HUB_OFFLINE='1',
                 HF_HUB_CACHE=str(HERE.parents[1]/'external/wsp-vlm-model-cache/hub'))
        result=bounded(command+['--execute'],remaining-5,env)
        reconcile(a.out,result,known)
        raise SystemExit(124 if result['timed_out'] else result['returncode'])


if __name__=='__main__':main()
