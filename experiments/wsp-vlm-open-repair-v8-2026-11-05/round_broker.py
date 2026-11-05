"""Thirty completed distinct full-development repair evaluations; no run wall cutoff."""
import argparse,json,time,os
from pathlib import Path
from common import HERE,write_json,file_hash
from live import build_service
p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);a=p.parse_args()
cfg=json.loads(a.config.read_text());task=cfg['task']
receipt=json.loads((HERE/f'batch-acceptance-{task}.json').read_text())
if not receipt['accepted'] or receipt['backend_sha256']!=file_hash(HERE/'backend.py'):raise RuntimeError('Batch acceptance absent/mismatched')
service=build_service(cfg)
root=service.root;inbox=root/'inbox';inbox.mkdir(exist_ok=True)
if task=='B':
 old=HERE.parents[1]/'external/wsp-vlm-open-repair-v7-2026-11-05/search-B/actions/turn-0018/response.json'
 history=json.loads(old.read_text());write_json(root/'artifacts/history-B-v7-first-evaluation.json',history)
write_json(root/'broker-ready.json',{'time_unix':time.time(),'physical_gpu':os.environ.get('CUDA_VISIBLE_DEVICES'),'round_target':30,'wall_deadline':None,'baseline_complete':True})
try:
 while not service.state['research_done']:
  for f in sorted(inbox.glob('*.json')):
   action=json.loads(f.read_text())
   if not (root/'actions'/action['id']/'response.json').exists():service.dispatch(action)
  time.sleep(.5)
finally:service.close()
