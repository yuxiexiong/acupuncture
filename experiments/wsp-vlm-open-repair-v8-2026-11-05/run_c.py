"""C-only GPU-1 durable observer and existing open researcher, same 2h search budget."""
import argparse,json,os,signal,subprocess,sys,time
from pathlib import Path
from common import HERE,write_json,file_hash
from controller import CodexResearcher,run_session
sys.path.append(str(HERE.parent/'wsp-vlm-open-repair-v7r1-2026-11-05'))
from recovery import DurableService,ssh_python,retry_read
OLD=HERE.parent/'wsp-vlm-open-repair-v7-2026-11-05'

def worker():
 cfg=json.loads((HERE/'config-C.json').read_text());local=OLD/'search-C';local.mkdir(exist_ok=False)
 cfg['researcher_cli']='/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex'
 cfg['researcher_cli_sha256']=file_hash(cfg['researcher_cli']);write_json(local/'local_config.json',cfg)
 rel=str(HERE.relative_to(HERE.parents[1]))
 code="""import json,pathlib,subprocess,sys,time,os
x=json.load(sys.stdin);root=pathlib.Path('/workspace/acupuncture');p=root/x['receipt']
with p.open('x') as marker:
 with (root/x['log']).open('x') as log:
  child=subprocess.Popen(x['command'],cwd=root,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True,close_fds=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='1'))
 result={'pid':child.pid,'time_unix':time.time(),'command':x['command'],'physical_gpu':1};json.dump(result,marker)
print(json.dumps(result))"""
 result=ssh_python(code,{'receipt':rel+'/C-broker-launch.json','log':rel+'/C-broker.log','command':['timeout','7200','.venv-bench/bin/python','-u',rel+'/broker.py','--config',rel+'/config-C.json']})
 write_json(HERE/'C-broker-launch.json',result)
 retry_read(Path(cfg['run_root'])/'broker-r1-ready.json',time.time()+180)
 service=DurableService(cfg,'C',local)
 researcher=CodexResearcher(cfg,local/'researcher-gpu1')
 instructions=(HERE/'RESEARCHER.md').read_text()+'\nCurrent branch: C. GPU 1. Observer inference batch size: '+str(cfg['execution_batch_size'])+'; engineer-validated against prior original outputs. Parameter choice and edits remain yours.\nFrozen contract: '+json.dumps(cfg['contract'])
 result=run_session(service,researcher,local/'conversation',instructions)
 write_json(local/'receipt-gpu1.json',result)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--worker',action='store_true');a=p.parse_args()
 if a.worker:worker()
 else:
  with (HERE/'C-supervisor.json').open('x') as f:json.dump({'status':'starting','pid':os.getpid(),'started_unix':time.time(),'wall_seconds':7200},f)
  started=time.time();child=subprocess.Popen([sys.executable,__file__,'--worker'],start_new_session=True)
  write_json(HERE/'C-supervisor.json',{'status':'running','pid':os.getpid(),'worker_pid':child.pid,'started_unix':started,'wall_seconds':7200})
  try:code=child.wait(timeout=7200)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=124
  write_json(HERE/'C-supervisor.json',{'status':'budget_exhausted' if code==124 else ('complete' if code==0 else 'failed'),'returncode':code,'started_unix':started,'elapsed_seconds':time.time()-started,'wall_seconds':7200})
