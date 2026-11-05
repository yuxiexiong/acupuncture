"""Reconcile the already-live B broker; detach C with Python rather than shell '&'."""
import argparse,json,os,signal,subprocess,sys,time
from pathlib import Path
import recovery as r
from common import HERE,write_json

def start_broker(task,deadline):
    if task=='B':
        # Explicitly reconciled once by the observer: do not launch B again.
        check=r.ssh_python("import pathlib,json; p=pathlib.Path('/proc/1711513/cmdline'); print(json.dumps({'cmd':p.read_bytes().replace(bytes([0]),b' ').decode()}))")
        if 'python -u experiments/wsp-vlm-open-repair-v7r1-2026-11-05/broker.py --config experiments/wsp-vlm-open-repair-v7-2026-11-05/config-B.json' not in check['cmd']:
            raise RuntimeError('Previously reconciled B broker is missing or changed; do not relaunch blindly')
        write_json(HERE/'audit/broker-B-reconciled-r2.json',dict(pid=1711513,cmd=check['cmd'],time_unix=time.time(),new_processes=0))
        return
    rel=str(HERE.relative_to(HERE.parents[1]))
    command=['timeout',str(max(1,int(deadline-time.time()))),'.venv-bench/bin/python','-u',rel+'/broker.py','--config','experiments/wsp-vlm-open-repair-v7-2026-11-05/config-C.json']
    code="""import json,pathlib,subprocess,sys,time
x=json.load(sys.stdin);root=pathlib.Path('/workspace/acupuncture');p=root/x['receipt']
with p.open('x') as marker:
 with (root/x['log']).open('x') as log:
  child=subprocess.Popen(x['command'],cwd=root,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True,close_fds=True)
 result={'pid':child.pid,'time_unix':time.time(),'command':x['command']};json.dump(result,marker)
print(json.dumps(result))"""
    result=r.ssh_python(code,{'command':command,'receipt':rel+'/broker-C-launch-r2.json','log':rel+'/broker-C.log'})
    write_json(HERE/'audit/broker-C-launch-r2.json',result)

r.start_broker=start_broker
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--worker',choices=['B','C']);a=p.parse_args()
    if a.worker:r.worker(a.worker)
    else:
        marker=HERE/'sequence-r2.json'
        with marker.open('x') as f:json.dump({'status':'starting','pid':os.getpid()},f)
        stages=[]
        for task in 'BC':
            cfg=json.loads((r.OLD/'config-B.json').read_text())
            remaining=cfg['contract']['wall_seconds'] if task=='C' else max(0,r.read(Path(cfg['run_root'])/'state.json')['started_unix']+cfg['contract']['wall_seconds']-time.time())
            write_json(marker,{'status':'running','task':task,'stages':stages,'pid':os.getpid()})
            child=subprocess.Popen([sys.executable,__file__,'--worker',task],start_new_session=True)
            try:code=child.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid,signal.SIGKILL);child.wait();code=124
            stages.append({'task':task,'returncode':code,'time_unix':time.time()})
            if code not in (0,124):
                write_json(marker,{'status':'stopped_on_error','stages':stages});raise SystemExit(code)
        write_json(marker,{'status':'complete','stages':stages})
