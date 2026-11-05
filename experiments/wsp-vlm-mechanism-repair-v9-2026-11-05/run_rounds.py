"""One independent researcher per GPU; stop by 30 completed repairs, not wall time."""
import argparse,json,math,os,subprocess,sys,time
from pathlib import Path
from common import HERE,packed,write_json,file_hash
from controller import CodexResearcher,run_session
from evidence import Evidence
sys.path.append(str(HERE.parent/'wsp-vlm-open-repair-v7r1-2026-11-05'))
from recovery import ssh_python

class Remote:
 def __init__(self,cfg,task,root,pid):
  self.contract=cfg['contract'];self.remote=Path(cfg['run_root']);self.root=root;self.pid=pid;self.stop_sent=False
  self.evidence=Evidence(HERE.parents[1]/f'external/wsp-vlm-open-repair-v7-2026-11-05/{task}_D',cfg['evidence_sha256'])
  self.state=self.wait_file('state.json');self.started=self.state['started_unix']
 def remaining(self):return math.inf
 def wait_file(self,rel):
  code="import json,pathlib; p=pathlib.Path("+repr(str(self.remote/rel))+"); process=pathlib.Path('/proc/"+str(self.pid)+"/cmdline'); print(json.dumps({'value':json.loads(p.read_text()) if p.exists() else None,'alive':process.exists() and bool(process.read_bytes())}))"
  while True:
   try:
    status=ssh_python(code)
    if status['value'] is not None:return status['value']
    if not status['alive']:raise RuntimeError('Observer exited without durable reply; inspect, do not replay')
   except (ConnectionError,subprocess.TimeoutExpired):time.sleep(15);continue
   time.sleep(10)
 def dispatch(self,action):
  write_json(self.root/(action['id']+'-request.json'),action)
  code="""import json,pathlib,sys,os
x=json.load(sys.stdin);a=x['action'];p=pathlib.Path(x['root'])/'inbox'/(a['id']+'.json')
if any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in a['id']):raise ValueError('bad id')
if p.exists():
 if json.loads(p.read_text())!=a:raise ValueError('identity mismatch')
else:
 tmp=p.with_suffix('.pending');tmp.write_text(json.dumps(a));os.replace(tmp,p)
print(json.dumps({'queued':a['id']}))"""
  while True:
   try:ssh_python(code,{'root':str(self.remote),'action':action});break
   except (ConnectionError,subprocess.TimeoutExpired):time.sleep(15)
  result=self.wait_file('actions/'+action['id']+'/response.json')
  if result['id']!=action['id']:raise ValueError('Response mismatch')
  write_json(self.root/(action['id']+'-response.json'),result);self.state=result['budget'];return result
 def save(self):
  if self.state.get('research_done') and not self.stop_sent:
   self.stop_sent=True;self.dispatch({'id':'observer-final','kind':'forward','request':{'op':'stop','reason':'Researcher ended early; report actual completed repair rounds, not 30'}})

def worker(task):
 cfg=json.loads((HERE/f'config-{task}.json').read_text());local=HERE/f'search-{task}';local.mkdir(exist_ok=False)
 cfg['researcher_cli']='/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex';cfg['researcher_cli_sha256']=file_hash(cfg['researcher_cli']);write_json(local/'local_config.json',cfg)
 rel=str(HERE.relative_to(HERE.parents[1]));gpu=cfg['physical_gpu']
 code="""import json,pathlib,subprocess,sys,time,os
x=json.load(sys.stdin);root=pathlib.Path('/workspace/acupuncture');p=root/x['receipt']
active=subprocess.check_output(['nvidia-smi','-i',str(x['gpu']),'--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
if active:raise RuntimeError('Assigned GPU occupied; do not interrupt another task')
with p.open('x') as f:
 with (root/x['log']).open('x') as log:
  q=subprocess.Popen(x['cmd'],cwd=root,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True,close_fds=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES=str(x['gpu'])))
 result={'pid':q.pid,'time_unix':time.time(),'physical_gpu':x['gpu'],'no_wall_timeout':True};json.dump(result,f)
print(json.dumps(result))"""
 # Never retry an uncertain launch automatically; durable launch marker remains.
 launched=ssh_python(code,{'receipt':rel+f'/launch-{task}.json','log':rel+f'/broker-{task}.log','gpu':gpu,'cmd':['.venv-bench/bin/python','-u',rel+'/round_broker.py','--config',rel+f'/config-{task}.json']})
 write_json(HERE/f'launch-{task}.json',launched)
 service=Remote(cfg,task,local,launched['pid']);service.wait_file('broker-ready.json')
 researcher=CodexResearcher(cfg,local/'researcher-empty')
 instructions=(HERE/'RESEARCHER.md').read_text()+'\nBranch: '+task+'\nFrozen contract: '+json.dumps(cfg['contract'])+'\nUse status/evidence to inspect W0; all layer/channel choices are yours.'
 result=run_session(service,researcher,local/'conversation',instructions);write_json(local/'receipt.json',result)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--task',choices=['B','C'],required=True);p.add_argument('--worker',action='store_true');a=p.parse_args()
 if a.worker:worker(a.task)
 else:
  marker=HERE/f'supervisor-{a.task}.json'
  with marker.open('x') as f:json.dump({'status':'starting','pid':os.getpid()},f)
  child=subprocess.Popen([sys.executable,__file__,'--task',a.task,'--worker'],start_new_session=True)
  write_json(marker,{'status':'running','pid':os.getpid(),'worker_pid':child.pid,'started_unix':time.time(),'repair_round_target':30,'wall_deadline':None})
  code=child.wait();write_json(marker,{'status':'completed_or_early_stopped' if code==0 else 'failed','returncode':code,'time_unix':time.time(),'repair_round_target':30,'wall_deadline':None})
