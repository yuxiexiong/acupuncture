"""Durable single-attempt queue: CPU ready -> idle GPU -> real acceptance -> 30 rounds."""
import argparse,fcntl,json,math,os,shlex,shutil,subprocess,sys,time,traceback
from pathlib import Path
from common import HERE,write_json,file_hash
ROOT=HERE.parents[1]
OUT=ROOT/'external'/HERE.name
VERSION='v9' if '-v9-' in HERE.name else 'v8'

def status(out,stage,**extra):
    write_json(out/'queue-status.json',dict(stage=stage,pid=os.getpid(),time_unix=time.time(),target_rounds=30,version=VERSION,**extra))

def check_sources():
    manifest=json.loads((HERE/'source-manifest.json').read_text())
    for name,h in manifest['files'].items():
        if file_hash(HERE/name)!=h:raise ValueError('Frozen source changed: '+name)
    assert json.loads((HERE/'audit/cpu-preflight.json').read_text())['status']=='passed'

def dependency_stage():
    # Existing authorized Qwen v9 50-round continuations have priority across their reload gaps.
    old=ROOT/'external/wsp-vlm-mechanism-repair-v9-2026-11-05'
    for task in ['B','C']:
        p=old/task/'state.json'
        if p.exists():
            d=json.loads(p.read_text())
            if not (d.get('research_done') and d.get('repair_rounds_completed',0)>=50):
                return 'waiting_existing_qwen4b'
    if VERSION=='v9':
        for task in ['B','C']:
            p=ROOT/f'external/wsp-vlm-gemma3-v8-2026-11-05/{task}/queue-status.json'
            if not p.exists():return 'waiting_gemma_v8'
            d=json.loads(p.read_text())
            if d['stage'] in ('failed','controller_failed','early_stopped','paused_by_user'):
                raise RuntimeError('Gemma v8 did not complete; inspect before proceeding')
            if d['stage']!='finished':return 'waiting_gemma_v8'
    return None

def idle_gpus():
    rows=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True)
    busy={r.split(',')[0].strip() for r in subprocess.check_output(['nvidia-smi','--query-compute-apps=gpu_uuid','--format=csv,noheader'],text=True).splitlines() if r.strip()}
    return [int(a) for a,u,m,p in (map(str.strip,r.split(',')) for r in rows.splitlines()) if u not in busy and int(m)<128 and int(p)==0]

def claim_gpu():
    folder=ROOT/'external/wsp';folder.mkdir(exist_ok=True)
    for gpu in idle_gpus():
        lock=(folder/f'engineering-gpu-{gpu}.lock').open('a')
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:lock.close();continue
        time.sleep(5)
        if gpu in idle_gpus() and dependency_stage() is None:return gpu,lock
        lock.close()
    return None

def server(task):
    out=OUT/task;out.mkdir(parents=True,exist_ok=True)
    lock=(out/'queue.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if (out/'queue-status.json').exists():raise RuntimeError('Existing queue identity; inspect, never restart blindly')
    service=None;gpu_lock=None
    try:
        check_sources()
        if shutil.disk_usage(out).free < 38*1024**3:
            raise RuntimeError('Insufficient disk for 12 GiB run, 6 GiB temporary and 20 GiB reserve')
        while True:
            if (out/'PAUSED_BY_USER.json').exists():status(out,'paused_by_user');return
            local=out/'controller-status.json'
            if local.exists() and json.loads(local.read_text())['stage']=='failed':raise RuntimeError('Local controller failed; inspect')
            waiting=dependency_stage()
            if waiting:status(out,waiting,task=task);time.sleep(15);continue
            status(out,'waiting_gpu',task=task)
            claimed=claim_gpu()
            if claimed is not None:break
            time.sleep(15)
        if shutil.disk_usage(out).free < 38*1024**3:
            claimed[1].close();raise RuntimeError('Disk reserve fell below launch threshold while queued')
        gpu,gpu_lock=claimed;os.environ['CUDA_VISIBLE_DEVICES']=str(gpu)
        cfg=json.loads((out/'config.json').read_text());cfg.update(physical_gpu=gpu,phase='engineering')
        write_json(out/'engineering-config.json',cfg)
        status(out,'engineering',task=task,physical_gpu=gpu)
        with (out/'engineering.log').open('x') as log:
            subprocess.run([sys.executable,'-u',str(HERE/'engineering.py'),'--config',str(out/'engineering-config.json'),'--out',str(out/'engineering')],stdout=log,stderr=log,check=True)
        cfg.update(phase='search',engineering_acceptance_sha256=file_hash(out/'engineering/acceptance.json'))
        write_json(out/'config.json',cfg)
        status(out,'baseline',task=task,physical_gpu=gpu)
        from live import build_service
        from progress import export
        service=build_service(cfg);export(service,cfg['model_id']+' '+VERSION+' '+task)
        write_json(service.root/'broker-ready.json',dict(pid=os.getpid(),physical_gpu=gpu,baseline_complete=True,target_rounds=30))
        while not service.state['research_done']:
            status(out,'search',task=task,physical_gpu=gpu,completed_rounds=service.state.get('repair_rounds_completed',0))
            if (out/'PAUSED_BY_USER.json').exists():status(out,'paused_by_user');return
            cp=out/'controller-status.json'
            if cp.exists() and json.loads(cp.read_text())['stage']=='failed':raise RuntimeError('Researcher/controller failed; no automatic retry')
            for p in sorted((service.root/'inbox').glob('*.json')):
                action=json.loads(p.read_text())
                if not (service.root/'actions'/action['id']/'response.json').exists():
                    before=service.state.get('repair_rounds_completed',0)
                    service.dispatch(action)
                    if service.state.get('repair_rounds_completed',0)!=before:export(service,cfg['model_id']+' '+VERSION+' '+task)
                    if service.state['research_done']:break
            time.sleep(1)
        export(service,cfg['model_id']+' '+VERSION+' '+task)
        count=service.state.get('repair_rounds_completed',0)
        status(out,'finished' if count==30 and service.state.get('frozen') else 'early_stopped',task=task,completed_rounds=count,frozen=service.state.get('frozen'))
    except BaseException as exc:
        (out/'failure.txt').write_text(traceback.format_exc());status(out,'failed',task=task,error=repr(exc));raise
    finally:
        if service is not None:service.close()
        if gpu_lock is not None:gpu_lock.close()
        lock.close()

def ssh_python(code,payload=None):
    r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gqa-h20','python3 -c '+shlex.quote(code)],input=json.dumps(payload),capture_output=True,text=True,timeout=60)
    if r.returncode:raise ConnectionError(r.stderr[-1200:])
    return json.loads(r.stdout)

class Remote:
    def __init__(self,cfg,local,pid,evidence):
        self.contract=cfg['contract'];self.remote=Path(cfg['run_root']);self.root=local;self.pid=pid;self.evidence=evidence;self.stop_sent=False
        self.state=self.wait_file('state.json');self.started=self.state['started_unix']
    def remaining(self):return math.inf
    def wait_file(self,rel):
        while True:
            d=ssh_python("import json,pathlib,sys; x=json.load(sys.stdin);p=pathlib.Path(x['path']);q=pathlib.Path('/proc')/str(x['pid'])/'cmdline';print(json.dumps({'value':json.loads(p.read_text()) if p.exists() else None,'alive':q.exists() and bool(q.read_bytes())}))",dict(path=str(self.remote/rel),pid=self.pid))
            if d['value'] is not None:return d['value']
            if not d['alive']:raise RuntimeError('Observer exited without durable response; do not replay')
            time.sleep(5)
    def dispatch(self,action):
        write_json(self.root/(action['id']+'-request.json'),action)
        code="""import json,pathlib,sys,os
x=json.load(sys.stdin);a=x['action'];p=pathlib.Path(x['root'])/'inbox'/(a['id']+'.json')
if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in a['id']):raise ValueError('bad action id')
if p.exists():
 if json.loads(p.read_text())!=a:raise ValueError('Action identity mismatch')
else:
 tmp=p.with_suffix('.pending');tmp.write_text(json.dumps(a));os.replace(tmp,p)
print(json.dumps({'queued':a['id']}))"""
        ssh_python(code,dict(root=str(self.remote),action=action))
        result=self.wait_file('actions/'+action['id']+'/response.json');assert result['id']==action['id']
        write_json(self.root/(action['id']+'-response.json'),result);self.state=result['budget'];return result
    def save(self):
        if self.state.get('research_done') and not self.stop_sent:
            self.stop_sent=True;self.dispatch(dict(id='observer-final',kind='forward',request=dict(op='stop',reason='Researcher stopped early; preserve actual rounds')))

def controller(task):
    from prepare import prepare_evidence
    from evidence import Evidence
    from controller import CodexResearcher,run_session
    out=OUT/task;out.mkdir(parents=True,exist_ok=True)
    local=out/'controller';local.mkdir(exist_ok=False)
    remote='/workspace/acupuncture/external/'+HERE.name+'/'+task
    def mark(stage,**extra):
        d=dict(stage=stage,pid=os.getpid(),time_unix=time.time(),**extra);write_json(local/'status.json',d)
        ssh_python("import json,pathlib,sys,os;x=json.load(sys.stdin);p=pathlib.Path(x['root'])/'controller-status.json';q=p.with_suffix('.tmp');q.write_text(json.dumps(x['status']));os.replace(q,p);print('{}')",dict(root=remote,status=d))
    try:
        mark('waiting_server')
        evidence_root=prepare_evidence(task)
        query="""import json,pathlib,sys
p=pathlib.Path(json.load(sys.stdin)['root']);s=p/'queue-status.json';r=p/'search/broker-ready.json';status=json.loads(s.read_text()) if s.exists() else None
proc=pathlib.Path('/proc')/str(status['pid'])/'cmdline' if status else None
print(json.dumps({'status':status,'alive':proc.exists() and bool(proc.read_bytes()) if proc else True,'ready':json.loads(r.read_text()) if r.exists() else None,'config':json.loads((p/'config.json').read_text()) if r.exists() else None}))"""
        while True:
            try:reply=ssh_python(query,dict(root=remote))
            except (ConnectionError,subprocess.TimeoutExpired):time.sleep(15);continue
            if reply['status'] and reply['status']['stage'] in ('failed','paused_by_user','early_stopped'):raise RuntimeError('Server queue stopped: '+repr(reply['status']))
            if not reply['alive']:raise RuntimeError('Server queue exited; inspect before restart')
            if reply['ready']:break
            time.sleep(15)
        cfg=reply['config'];cfg['researcher_cli']='/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex'
        cfg['researcher_cli_sha256']=file_hash(cfg['researcher_cli']);write_json(local/'config.json',cfg)
        service=Remote(cfg,local,reply['ready']['pid'],Evidence(evidence_root,cfg['evidence_sha256']))
        researcher=CodexResearcher(cfg,local/'researcher-empty');mark('running',broker_pid=service.pid)
        result=run_session(service,researcher,local/'conversation',(HERE/'RESEARCHER.md').read_text()+'\nBranch: '+task+'\nFrozen contract: '+json.dumps(cfg['contract']))
        write_json(local/'receipt.json',result)
        if not service.state.get('research_done'):raise RuntimeError('Researcher budget exhausted without terminal action')
        mark('finished',completed_rounds=service.state.get('repair_rounds_completed',0),result=result)
    except BaseException as exc:
        (local/'failure.txt').write_text(traceback.format_exc())
        try:mark('failed',error=repr(exc))
        except Exception:write_json(local/'status.json',dict(stage='failed',error=repr(exc),server_notification_failed=True))
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--task',choices=['B','C'],required=True);p.add_argument('--server',action='store_true');a=p.parse_args()
    server(a.task) if a.server else controller(a.task)
