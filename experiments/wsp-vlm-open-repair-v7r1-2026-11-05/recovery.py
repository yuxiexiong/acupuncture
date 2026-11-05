"""Resume B from the completed durable reply; start C once. Never replay uncertain actions."""
import argparse,json,os,shlex,signal,subprocess,sys,time
from pathlib import Path
from common import HERE,packed,write_json,file_hash
from controller import CodexResearcher,run_session
from evidence import Evidence
OLD=HERE.parent/'wsp-vlm-open-repair-v7-2026-11-05'
SERVER='/workspace/acupuncture/'

def ssh_python(code,payload=None):
    command=['ssh','-o','ConnectTimeout=15','gqa-h20','python3 -c '+shlex.quote(code)]
    r=subprocess.run(command,input=None if payload is None else packed(payload).decode(),capture_output=True,text=True,timeout=60)
    if r.returncode:raise ConnectionError(r.stderr[-1200:])
    return json.loads(r.stdout)

def read(path):
    return ssh_python('import pathlib,json; p=pathlib.Path('+repr(str(path))+'); print(p.read_text() if p.exists() else "null")')

def retry_read(path,deadline):
    while time.time()<deadline:
        try:
            result=read(path)
            if result is not None:return result
        except (ConnectionError,subprocess.TimeoutExpired):pass
        time.sleep(5)
    raise TimeoutError('Original wall budget exhausted while awaiting durable receipt')

class DurableService:
    def __init__(self,cfg,task,local):
        self.contract=cfg['contract'];self.remote=Path(cfg['run_root']);self.root=local;self.stop_sent=False
        self.evidence=Evidence(HERE.parents[1]/'external/wsp-vlm-open-repair-v7-2026-11-05'/f'{task}_D',cfg['evidence_sha256'])
        self.state=retry_read(self.remote/'state.json',time.time()+60);self.started=self.state['started_unix']
    def remaining(self):return self.contract['wall_seconds']-(time.time()-self.started)
    def dispatch(self,action):
        write_json(self.root/(action['id']+'-request.json'),action)
        code="""import json,pathlib,sys,os
x=json.load(sys.stdin);root=pathlib.Path(x['root']);a=x['action'];p=root/'inbox'/(a['id']+'.json')
if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in a['id']):raise ValueError('bad id')
if p.exists():
 if json.loads(p.read_text())!=a:raise ValueError('identity mismatch')
else:
 tmp=p.with_suffix('.pending');tmp.write_text(json.dumps(a));os.replace(tmp,p)
print(json.dumps({'queued':a['id']}))"""
        deadline=self.started+self.contract['wall_seconds']
        while time.time()<deadline:
            try:ssh_python(code,{'root':str(self.remote),'action':action});break
            except (ConnectionError,subprocess.TimeoutExpired):time.sleep(5)
        result=retry_read(self.remote/'actions'/action['id']/'response.json',deadline)
        if result['id']!=action['id']:raise ValueError('response mismatch')
        write_json(self.root/(action['id']+'-response.json'),result);self.state=result['budget'];return result
    def save(self):
        if self.state.get('research_done') and not self.stop_sent:
            self.stop_sent=True;self.dispatch({'id':'observer-final-r1','kind':'forward','request':{'op':'stop','reason':'Researcher stopped'}})

def start_broker(task,deadline):
    rel=str(HERE.relative_to(HERE.parents[1]))
    command=f'cd {SERVER} && nohup timeout {max(1,int(deadline-time.time()))} .venv-bench/bin/python -u {rel}/broker.py --config experiments/wsp-vlm-open-repair-v7-2026-11-05/config-{task}.json > {rel}/broker-{task}.log 2>&1 < /dev/null &'
    # Called once; uncertain launch is reconciled by ready marker, never reissued.
    r=subprocess.run(['ssh','gqa-h20',command],capture_output=True,text=True,timeout=30)
    if r.returncode:raise RuntimeError('Broker launch uncertain; inspect before retry: '+r.stderr)

def worker(task):
    local=OLD/('search-'+task);cfg=json.loads((OLD/('config-'+task+'.json')).read_text())
    cfg['researcher_cli']='/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex'
    cfg['researcher_cli_sha256']=file_hash(cfg['researcher_cli'])
    remote=Path(cfg['run_root']);resume=task=='B'
    if resume:
        state=read(remote/'state.json');deadline=state['started_unix']+cfg['contract']['wall_seconds']
    else:
        if read(remote/'state.json') is not None:raise RuntimeError('C already exists; do not duplicate')
        local.mkdir(exist_ok=False);write_json(local/'local_config.json',cfg);deadline=time.time()+cfg['contract']['wall_seconds']
    start_broker(task,deadline)
    retry_read(remote/'broker-r1-ready.json',deadline)
    service=DurableService(cfg,task,local)
    researcher=CodexResearcher(cfg,local/'researcher-recovery-r1')
    if resume:
        folders=sorted((local/'conversation').glob('turn-*'))
        receipts=[json.loads((f/'receipt.json').read_text()) for f in folders]
        researcher.thread=receipts[-1]['thread'];researcher.used_turns=len(receipts)
        researcher.used_tokens=sum(r['usage'].get('input_tokens',0)+r['usage'].get('output_tokens',0) for r in receipts)
        last=folders[-1];result=retry_read(remote/'actions'/last.name/'response.json',deadline)
        write_json(last/'tool_result.json',result);write_json(local/(last.name+'-response.json'),result)
        prompt=packed(result).decode()
        if len(prompt)>16000:prompt=prompt[:16000]+'\nFull result in ARTIFACTS/'+last.name+'.json; inspect omitted evidence.'
        prompt+='\nObserver recovery: SSH disconnected after submission; this is the original completed response, not a rerun. Original budget and counters remain. Python variables reset on observer restart; saved work/staged files, artifacts and candidates persist. Continue your own diagnosis; no parameter choice was supplied by the observer.'
        start=len(folders)+1
    else:
        prompt=(HERE/'RESEARCHER.md').read_text()+'\nCurrent branch: '+task+'\nFrozen contract: '+json.dumps(cfg['contract']);start=1
    result=run_session(service,researcher,local/'conversation',prompt,start_turn=start,resuming=resume)
    write_json(local/'receipt-r1.json',result)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--worker',choices=['B','C']);a=p.parse_args()
    if a.worker:worker(a.worker)
    else:
        marker=HERE/'sequence.json'
        with marker.open('x') as f:json.dump({'status':'starting','pid':os.getpid()},f)
        stages=[]
        for task in 'BC':
            old=json.loads((OLD/'config-B.json').read_text())
            remaining=old['contract']['wall_seconds'] if task=='C' else max(0,read(Path(old['run_root'])/'state.json')['started_unix']+old['contract']['wall_seconds']-time.time())
            write_json(marker,{'status':'running','task':task,'stages':stages,'pid':os.getpid()})
            child=subprocess.Popen([sys.executable,__file__,'--worker',task],start_new_session=True)
            try:code=child.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid,signal.SIGKILL);child.wait();code=124
            stages.append({'task':task,'returncode':code,'time_unix':time.time()})
            if code not in (0,124):
                write_json(marker,{'status':'stopped_on_error','stages':stages});raise SystemExit(code)
        write_json(marker,{'status':'complete','stages':stages})
