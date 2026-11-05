"""CPU analysis using frozen scorers; D-only until explicitly passed --full."""
import argparse,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'wsp-vlm-screen-ready-v3-2026-11-05'))
import statistics_b as b
import statistics_c as c
from prepare_inputs import all_pairs,read_jsonl
p=argparse.ArgumentParser();p.add_argument('--full',action='store_true');args=p.parse_args()
out=ROOT/'external/wsp-vlm-channel-prep-v5-2026-11-05'
reports={};primaries={};saved={}
for task,mod in [('B',b),('C',c)]:
 stages=['D','H'] if args.full else ['D']
 preds=[]
 for stage in stages:
  folder=out/f'{task}_{stage}'
  receipt=json.loads((folder/'receipt.json').read_text());assert receipt['status']=='complete'
  preds+=read_jsonl(folder/'predictions.jsonl')
 pairs=[(i,g) for i,g in all_pairs(task) if g['split'] in stages]
 gold=[g for i,g in pairs];rows=mod.score(preds,gold)
 inputs={i['request_id']:i for i,g in pairs};raw={r['request_id']:r for r in preds}
 prefix='full' if args.full else 'D'
 with (HERE/f'{task}_{prefix}_scored.jsonl').open('w') as f:
  for r in rows:f.write(json.dumps(dict(r,input=inputs[r['request_id']],raw=raw[r['request_id']]),ensure_ascii=False)+'\n')
 if args.full:
  report=mod.report(preds,gold);saved[task]=(mod,preds,gold)
  primaries[task]=report['splits']['H']['cells']['B0:T0' if task=='B' else 'B0:T0:Oprimary']['p_one_sided']
 else:
  eng,ok=c.engineering_check(rows)
  report=dict(D=mod.summarize(rows),engineering=eng,engineering_pass=ok,status='D only; exploratory; H unopened')
 reports[task]=report
if args.full:
 family=dict(A=1.,**primaries)
 (HERE/'family_pvalues.json').write_text(json.dumps(family,indent=2)+'\n')
 for task,(mod,preds,gold) in saved.items():reports[task]=mod.report(preds,gold,family)
for task,r in reports.items():
 (HERE/f'{task}_{"full" if args.full else "D"}_statistics.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
 s=r['splits']['H'] if args.full else r['D'];key='B0:T0' if task=='B' else 'B0:T0:Oprimary'
 print(json.dumps(dict(task=task,engineering_pass=r['engineering_pass'],primary=s['cells'][key],decision=r.get('decision')),ensure_ascii=False))
