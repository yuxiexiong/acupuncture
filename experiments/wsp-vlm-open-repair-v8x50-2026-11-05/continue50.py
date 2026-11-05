"""Continue the same researcher and development run at its clean 30-round boundary."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'wsp-vlm-open-repair-v8-2026-11-05'
sys.path.insert(0,str(OLD))
from common import write_json,packed
from controller import CodexResearcher,run_session

def transition(state,contract):
 if state.get('repair_rounds_completed')!=30 or not state.get('research_done') or not state.get('frozen'):
  raise ValueError('Only the completed, frozen 30-round boundary can continue')
 if contract.get('repair_rounds')!=30:raise ValueError('Unexpected original target')
 updated=dict(state,research_done=False,frozen=None)
 return updated,dict(contract,repair_rounds=50)

def broker(task):
 from live import build_service
 cfg=json.loads((OLD/f'config-{task}.json').read_text())
 root=Path(cfg['run_root']);original=json.loads((root/'state.json').read_text())
 transition(original,cfg['contract'])
 service=build_service(cfg,resume=True)
 try:
  checkpoint=root/'checkpoint-round30';checkpoint.mkdir(exist_ok=False)
  for name in ('state.json','identity.json','config.json','frozen-candidate.json'):
   (checkpoint/name).write_bytes((root/name).read_bytes())
  service.state,service.contract=transition(service.state,service.contract)
  write_json(root/'round-limit-amendment.json',dict(original=30,total=50,authorization=json.loads((HERE/'authorization.json').read_text()),effective_contract=service.contract,original_identity_preserved=True,protocol_unchanged=True,time_unix=time.time()))
  service.save()
  write_json(root/'broker-50-ready.json',dict(pid=os.getpid(),round_target=50,resumed_at=30,baseline_replayed=False,time_unix=time.time()))
  while not service.state['research_done']:
   for f in sorted((root/'inbox').glob('*.json')):
    action=json.loads(f.read_text())
    if not (root/'actions'/action['id']/'response.json').exists():service.dispatch(action)
   time.sleep(.5)
 finally:service.close()

def run(task):
 from run_rounds import Remote,ssh_python
 cfg=json.loads((OLD/f'search-{task}/local_config.json').read_text());remote=cfg['run_root']
 marker=HERE/f'continuation-{task}.json'
 write_json(marker,dict(status='waiting_for_original_30_rounds',total_target=50,pid=os.getpid(),time_unix=time.time()))
 while True:
  sup=json.loads((OLD/f'supervisor-{task}.json').read_text())
  if sup['status'] not in ('starting','running'):
   if sup.get('returncode')!=0:raise RuntimeError('Original supervisor failed; inspect before continuing')
   break
  time.sleep(15)
 # Verify a complete boundary and old observer exit before launching anything.
 check="""import pathlib,json,sys
x=json.load(sys.stdin);p=pathlib.Path(x['root']);old=json.loads(pathlib.Path(x['launch']).read_text())['pid'];cmd=pathlib.Path('/proc/'+str(old)+'/cmdline')
print(json.dumps({'state':json.loads((p/'state.json').read_text()),'old_alive':cmd.exists() and bool(cmd.read_bytes()),'incomplete':[f.name for f in (p/'actions').iterdir() if not (f/'response.json').exists()]}))"""
 while True:
  try:r=ssh_python(check,dict(root=remote,launch='/workspace/acupuncture/'+str(OLD.relative_to(OLD.parents[1]))+f'/launch-{task}.json'))
  except (ConnectionError,subprocess.TimeoutExpired):time.sleep(15);continue
  transition(r['state'],cfg['contract'])
  if r['incomplete']:raise RuntimeError('Incomplete action; never replay')
  if not r['old_alive']:break
  time.sleep(5)
 rel=str(HERE.relative_to(HERE.parents[1]))
 launch="""import pathlib,json,subprocess,os,sys,time
x=json.load(sys.stdin);root=pathlib.Path('/workspace/acupuncture');p=root/x['rel']
with (p/('launch-'+x['task']+'.json')).open('x') as receipt:
 with (p/('broker-'+x['task']+'.log')).open('x') as log:
  q=subprocess.Popen(['.venv-bench/bin/python','-u',str(p/'continue50.py'),'--task',x['task'],'--broker'],cwd=root,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True,close_fds=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES=str(x['gpu'])))
 out={'pid':q.pid,'time_unix':time.time(),'physical_gpu':x['gpu']};json.dump(out,receipt)
print(json.dumps(out))"""
 # An uncertain launch is not retried automatically.
 launched=ssh_python(launch,dict(rel=rel,task=task,gpu=cfg['physical_gpu']));write_json(HERE/f'launch-{task}.json',launched)
 local=OLD/f'search-{task}';service=Remote(cfg,task,local,launched['pid']);service.wait_file('broker-50-ready.json')
 service.state=service.wait_file('state.json');service.contract=dict(cfg['contract'],repair_rounds=50)
 folders=sorted((local/'conversation').glob('turn-*'));last=folders[-1]
 receipt=json.loads((last/'receipt.json').read_text());feedback=json.loads((last/'tool_result.json').read_text())
 researcher=CodexResearcher(cfg,local/'researcher-50')
 researcher.thread=receipt['thread'];researcher.used_turns=int(last.name.split('-')[-1]);researcher.previous_usage=receipt['usage'];researcher.used_tokens=receipt['usage'].get('input_tokens',0)+receipt['usage'].get('output_tokens',0)
 prompt=('User-authorized continuation: total target is now 50 unique nonzero repairs with full development evaluation. The original 30 count toward 50; continue 20 more, not 50 new rounds. Same researcher thread, data, baseline, candidates, scores and protections. Original 30-round freeze is archived; observer now freezes at 50. Python kernel variables were reset on safe observer reload; saved work/stage and artifacts persist, reconstruct variables as needed. No edit direction or parameter location is prescribed. Inspect full prior feedback at ARTIFACTS/'+last.name+'.json. Do not replay old actions.\n'+packed(feedback).decode()[:10000])
 write_json(marker,dict(status='running',total_target=50,started_at_round=30,pid=os.getpid(),broker_pid=launched['pid'],thread=researcher.thread,time_unix=time.time()))
 result=run_session(service,researcher,local/'conversation',prompt,start_turn=researcher.used_turns+1,resuming=True)
 write_json(HERE/f'receipt-{task}.json',result)
 write_json(marker,dict(status='completed_or_early_stopped',total_target=50,actual_rounds=service.state.get('repair_rounds_completed'),result=result,time_unix=time.time()))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--task',choices=['B','C'],required=True);p.add_argument('--broker',action='store_true');a=p.parse_args()
 try:
  if a.broker:broker(a.task)
  else:run(a.task)
 except Exception as exc:
  write_json(HERE/f'failure-{a.task}-{"broker" if a.broker else "controller"}.json',dict(error=repr(exc),time_unix=time.time()))
  raise
