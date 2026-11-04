"""One-time authorized budget handover; reuse the existing recovery runner."""
from pathlib import Path
import json,subprocess,sys,time,os,signal,fcntl
R=Path(__file__).resolve().parent
ROOT=R.parents[4]/'external/wsp-fleet-v2/math-0p8b-budget-r1'
ROOT.mkdir(parents=True,exist_ok=True)
lock=(ROOT/'amendment.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
def record(status,**kw):
 p=ROOT/'amendment-state.json';q=p.with_suffix('.pending');q.write_text(json.dumps(dict(status=status,updated=time.time(),**kw),indent=2));q.replace(p)
ssh=['ssh','-o','ConnectTimeout=60','-o','ServerAliveInterval=10','-o','ServerAliveCountMax=2','-o','ControlMaster=auto','-o','ControlPersist=600','-o','ControlPath=/tmp/acupuncture-wsp-fleet-%C','gqa-h20','python3 -']
try:
 assert not (ROOT/'state.json').exists(),'Already started; do not duplicate'
 record('waiting_current_forward',action='turn-059',local_dispatch_pid=70747,new_gpu_hours=48)
 for _ in range(180):
  try:p=subprocess.run(ssh,input=(R/'apply_budget.py').read_text(),capture_output=True,text=True,timeout=90)
  except subprocess.TimeoutExpired:
   time.sleep(15);continue
  (ROOT/'last-ssh-stderr.txt').write_text(p.stderr)
  if p.returncode==255:
   time.sleep(15);continue
  if p.returncode:raise RuntimeError(p.stderr[-2000:])
  result=json.loads(p.stdout)
  if result['status']=='applied':break
  assert result['status']=='waiting_current_forward'
  time.sleep(15)
 else:raise RuntimeError('Budget handover deadline; inspect before resuming')
 (R/'applied-receipt.json').write_text(json.dumps(result,indent=2))
 cmd=subprocess.check_output(['ps','-p','70747','-o','command='],text=True)
 assert 'controller.py' in cmd and 'transport-r3/resume-controller.json' in cmd
 os.kill(70747,signal.SIGTERM);os.kill(70747,signal.SIGCONT)
 for _ in range(20):
  if subprocess.run(['ps','-p','70747','-o','pid='],capture_output=True).returncode:break
  time.sleep(.5)
 else:raise RuntimeError('Old local controller still exists')
 record('budget_applied_starting_resume',receipt=str(R/'applied-receipt.json'))
 with (ROOT/'launcher.log').open('a') as log:
  code=subprocess.call([sys.executable,str(R.parents[1]/'resume_after_fleet.py'),'--config',str(R/'resume-queue.json'),'--out',str(ROOT)],stdout=log,stderr=subprocess.STDOUT)
 record('resume_runner_exited',exit_code=code,see_state=str(ROOT/'state.json'))
except Exception as e:
 record('blocked_engineering',error=str(e));raise
