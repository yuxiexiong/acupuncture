
from pathlib import Path
import subprocess,sys,json,time,concurrent.futures
p=Path(/workspace/acupuncture/experiments/layer-survey-toy-v1-2026-10-27)
started=time.time()
def worker(gpu,models):
 result={}
 for model in models:
  with (p/fpreflight-r01/{model}.log).open(x) as log:
   cmd=[sys.executable,str(p/survey.py),run,--mode,preflight,--model,model,--gpu,str(gpu),--authorization,str(p/readiness/preflight-authorization.json),--output,str(p/fpreflight-r01/{model}),--execute]
   proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,cwd=p)
   (p/fpreflight-r01/{model}.pid).write_text(str(proc.pid))
   code=proc.wait()
   (p/fpreflight-r01/{model}.exit).write_text(str(code)+n)
   result[model]=code
   if code: break
 return result
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 futures=[pool.submit(worker,0,[2b,4b]),pool.submit(worker,1,[9b])]
 results=[f.result() for f in futures]
(p/preflight-r01/controller.json).write_text(json.dumps({completed_at:time.time(),wall_seconds:time.time()-started,worker_exit_codes:results},indent=2)+n)
