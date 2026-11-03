"""Four fixed jobs, durable progress, continue after recorded failures. No search by default."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
MATH=HERE.parent/'engineering-r2'
CODING=REPO/'experiments/wsp-coding-painpoint-v1-2026-11-03/orchestration'
SERVER='/workspace/acupuncture/external/wcp01/code/orchestration'
ENV='/workspace/acupuncture/external/wsp/code-engineering-r2/engineering-r2/server_env.sh'
ORDER=['math-0p8b','math-4b','coding-0p8b','coding-4b']


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.pending');tmp.write_text(json.dumps(value,indent=2));tmp.replace(path)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ssh(command,data=None,readonly=False):
    # Only reads reconnect automatically. Never replay a model/editor action after an uncertain reply.
    for attempt in range(3 if readonly else 1):
        p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','ServerAliveInterval=5','-o','ServerAliveCountMax=3','-o','ControlMaster=auto','-o','ControlPath=/tmp/acupuncture-wsp-fleet-%C','-o','ControlPersist=600','gqa-h20',command],input=data,text=True,capture_output=True)
        if p.returncode==0:return p.stdout
        if p.returncode!=255 or not readonly:break
        time.sleep(attempt+1)
    raise RuntimeError(p.stderr[-4000:] or p.stdout[-4000:] or 'SSH failed')


def remote_json(path):
    return json.loads(ssh('cat '+shlex.quote(path),readonly=True))


def upload(path,value):
    q=shlex.quote(path);parent=shlex.quote(str(Path(path).parent))
    ssh('mkdir -p '+parent+' && cat > '+q+'.pending && mv '+q+'.pending '+q,json.dumps(value))


def prepare():
    jobs=[]
    for name in ORDER:
        kind,profile=name.split('-');local=REPO/'external/wsp-fleet-v1'/name
        if kind=='math':
            cfg=json.loads((MATH/f'search-{profile}-local.json').read_text())
            server_cfg=json.loads((MATH/f'search-{profile}-server.json').read_text())
            server_cfg['run_root']='/workspace/acupuncture/external/wsp/fleet-v1/'+name
            cfg.update(local_run_root=str(local/'experiment'),server_config='/workspace/acupuncture/external/wsp/fleet-v1/configs/'+name+'.json',acceptance_receipt_sha256=sha(MATH/'receipts/editor-integrated/receipt.json'))
        else:
            cfg=json.loads((CODING/f'receipts/search-{profile}.json').read_text());server_cfg=None
            cfg['run_root']='/workspace/acupuncture/external/wcp01/runs/fleet-v1-'+profile
        jobs.append(dict(id=name,kind=kind,profile=profile,local_root=str(local),config=cfg,server_config=server_cfg))
    sources=[HERE/'fleet.py',HERE/'acceptance.py',MATH/'controller.py',*CODING.glob('*.py'),* (HERE.parent/'frozen-prompts').glob('*.txt')]
    write(HERE/'fleet.json',dict(mode='research',authorized=False,authorization_record=None,root=str(REPO/'external/wsp-fleet-v1'),jobs=jobs,source_hashes={str(p):sha(p) for p in sources}))


def authorize(cfg):
    if [j['id'] for j in cfg['jobs']]!=ORDER:raise ValueError('FLEET_ORDER_CHANGED')
    if cfg['mode']=='fixture':
        if any(j.get('config') or j.get('server_config') for j in cfg['jobs']):raise ValueError('FIXTURE_HAS_RESEARCH_CONFIG')
        return
    if not cfg.get('authorized') or not cfg.get('authorization_record'):raise ValueError('FORMAL_SEARCH_DISABLED')
    for path,expected in cfg['source_hashes'].items():
        if sha(path)!=expected:raise ValueError('SOURCE_CHANGED: '+path)


def coding_status(root):
    # Observer-only status; no benchmark data is returned to the editor.
    code='''import json,subprocess,sys
from pathlib import Path
r=Path(sys.argv[1]);launch=r/'launch.json';value={}
if launch.exists():
 s=json.loads(launch.read_text())['session'];value['active']=subprocess.run(['tmux','has-session','-t',s],capture_output=True).returncode==0
for key,file in [('receipt','receipt.json'),('error','controller-stopped.json')]:
 p=r/file
 if p.exists():value[key]=json.loads(p.read_text())
print(json.dumps(value))'''
    return json.loads(ssh(shlex.join(['python3','-c',code,root]),readonly=True))


def coding_child(config,out):
    cfg=json.loads(config.read_text());path='/workspace/acupuncture/external/wcp01/fleet-configs/'+out.parent.name+'.json'
    upload(path,cfg)
    try:ssh(shlex.join(['sh',ENV,SERVER+'/launch.py','--config',path]))
    except RuntimeError:
        # Lost launch reply: reconcile an existing session; never blindly launch again.
        status=coding_status(cfg['run_root'])
        if not status:raise
    while True:
        status=coding_status(cfg['run_root']);write(out.parent/'remote-status.json',status)
        if status.get('receipt') and not status.get('active'):
            write(out,status['receipt']);return
        if not status.get('active'):raise RuntimeError('REMOTE_STOPPED: '+json.dumps(status))
        time.sleep(10)


def execute(job,record,out):
    cfg=dict(job['config'],authorized=True,authorization_record=record)
    local=Path(job['local_root']);runtime=local/'runtime.json'
    if job['kind']=='math':
        server=dict(job['server_config'],authorized=True,authorization_record=record)
        upload(cfg['server_config'],server)
        command=[sys.executable,str(MATH/'controller.py'),'--config',str(runtime)]
        receipt=Path(cfg['local_run_root'])/'receipt.json'
    else:
        command=[sys.executable,str(HERE/'fleet.py'),'--coding-child',str(runtime),'--out',str(out/'receipt.json')]
        receipt=out/'receipt.json'
    write(runtime,cfg)
    return command,receipt


def check_previous_idle(jobs):
    # If a disconnected child is still running, do not overlap it with a later experiment.
    roots=[j['server_config']['run_root'] if j['kind']=='math' else j['config']['run_root'] for j in jobs]
    code='''import fcntl,json,subprocess,sys
from pathlib import Path
for name in json.loads(sys.argv[1]):
 r=Path(name)
 if (r/'broker.lock').exists():
  with (r/'broker.lock').open('a') as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if (r/'launch.json').exists():
  s=json.loads((r/'launch.json').read_text())['session']
  if subprocess.run(['tmux','has-session','-t',s],capture_output=True).returncode==0:raise RuntimeError('PREVIOUS_REMOTE_JOB_STILL_ACTIVE')
print('previous_jobs_idle')'''
    ssh(shlex.join(['python3','-c',code,json.dumps(roots)]),readonly=True)


def run(cfg,fixture=False):
    authorize(cfg)
    if fixture!=(cfg['mode']=='fixture'):raise ValueError('FIXTURE_MODE_MISMATCH')
    root=Path(cfg['root']);root.mkdir(parents=True,exist_ok=True)
    lock=open(root/'fleet.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    state_path=root/'state.json';frozen=root/'config.json'
    if frozen.exists() and json.loads(frozen.read_text())!=cfg:raise ValueError('FLEET_CONFIG_CHANGED')
    write(frozen,cfg)
    state=json.loads(state_path.read_text()) if state_path.exists() else dict(status='running',jobs=[],formal_search_started=not fixture)
    try:
        for job in cfg['jobs']:
            prior=next((j for j in state['jobs'] if j['id']==job['id']),None)
            if prior and prior['status']!='running':continue
            out=root/job['id'];out.mkdir(parents=True,exist_ok=True)
            if prior:
                # Parent interruption does not authorize replaying a possibly consumed action.
                if prior.get('pid'):
                    cmd=subprocess.run(['ps','-p',str(prior['pid']),'-o','args='],capture_output=True,text=True).stdout
                    if str(out) in cmd:raise RuntimeError('PREVIOUS_CHILD_STILL_RUNNING')
                receipt=Path(job['config']['local_run_root'])/'receipt.json' if not fixture and job['kind']=='math' else out/'receipt.json'
                if receipt.exists():
                    result=json.loads(receipt.read_text())
                    if result['status'] in ('completed','stopped'):
                        prior.update(status='completed' if result['status']=='completed' else 'negative_or_no_target',receipt=str(receipt),receipt_sha256=sha(receipt),ended=time.time())
                        write(state_path,state);continue
                prior.update(status='skipped_engineering',error='Interrupted; preserved, no automatic replay',needs_review=True)
                write(state_path,state);continue
            entry=dict(id=job['id'],status='running',started=time.time());state['jobs'].append(entry);write(state_path,state)
            try:
                if fixture:
                    command=[sys.executable,str(HERE/'acceptance.py'),'--child',job['id'],'--out',str(out)]
                    receipt=out/'receipt.json'
                else:
                    check_previous_idle(cfg['jobs'][:cfg['jobs'].index(job)])
                    command,receipt=execute(job,cfg['authorization_record'],out)
                with open(out/'process.log','a') as log:
                    proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
                    entry['pid']=proc.pid;write(state_path,state);exit_code=proc.wait()
                entry['exit_code']=exit_code
                if exit_code:raise RuntimeError('Child failed; see process.log')
                result=json.loads(receipt.read_text())
                if result['status'] not in ('completed','stopped'):raise ValueError('NO_TERMINAL_EXPERIMENT_RECEIPT')
                entry.update(status='completed' if result['status']=='completed' else 'negative_or_no_target',receipt=str(receipt),receipt_sha256=sha(receipt))
            except Exception as exc:
                entry.update(status='skipped_engineering',error=type(exc).__name__+': '+str(exc),needs_review=True)
                write(out/'failure.json',entry)
            entry['ended']=time.time();write(state_path,state)
        state['status']='finished_with_skips' if any(j['status']=='skipped_engineering' for j in state['jobs']) else 'finished'
        write(state_path,state);write(root/'receipt.json',state);return state
    finally:lock.close()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,default=HERE/'fleet.json');ap.add_argument('--prepare',action='store_true');ap.add_argument('--check',action='store_true');ap.add_argument('--coding-child',type=Path);ap.add_argument('--out',type=Path);a=ap.parse_args()
    if a.prepare:prepare();return
    if a.coding_child:coding_child(a.coding_child,a.out);return
    cfg=json.loads(a.config.read_text());authorize(cfg)
    if a.check:print('FLEET_GATE_OK');return
    print(json.dumps(run(cfg,fixture=cfg['mode']=='fixture')))


if __name__=='__main__':main()
