"""Thirty completed distinct full-development repair evaluations; no run wall cutoff."""
import argparse,json,time,os
from pathlib import Path
from common import HERE,write_json,file_hash
from live import build_service
p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);a=p.parse_args()
cfg=json.loads(a.config.read_text());task=cfg['task']
service=build_service(cfg)
root=service.root;inbox=root/'inbox';inbox.mkdir(exist_ok=True)
write_json(root/'broker-ready.json',{'time_unix':time.time(),'physical_gpu':os.environ.get('CUDA_VISIBLE_DEVICES'),'round_target':30,'wall_deadline':None,'baseline_complete':True})
try:
 while not service.state['research_done']:
  for f in sorted(inbox.glob('*.json')):
   action=json.loads(f.read_text())
   if not (root/'actions'/action['id']/'response.json').exists():service.dispatch(action)
  time.sleep(.5)
finally:service.close()
