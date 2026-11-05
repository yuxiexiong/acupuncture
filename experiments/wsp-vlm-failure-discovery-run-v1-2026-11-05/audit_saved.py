"""CPU final integrity audit; no model calls and no score-dependent selection."""
from pathlib import Path
import hashlib,json,datetime
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OUT=ROOT/'external/wsp-vlm-channel-prep-v5-2026-11-05'
if not (OUT/'P0/predictions.jsonl').exists():OUT=HERE/'evidence'
def read(p):return json.loads(p.read_text())
def rows(p):return [json.loads(x) for x in p.read_text().splitlines()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
v3=ROOT/'experiments/wsp-vlm-screen-ready-v3-2026-11-05'
env=read(OUT/'P0/environment.json');stage_counts={};all_ids=[]
for stage,n in [('P0',64),('B_D',464),('C_D',2560),('B_H',704),('C_H',3840)]:
 folder=OUT/stage;rr=rows(folder/'predictions.jsonl');expected=rows(v3/'prepared'/f'{stage}_inputs.jsonl')
 assert len(rr)==n and [r['request_id'] for r in rr]==[r['request_id'] for r in expected]
 assert len(rows(folder/'attempts.jsonl'))==n and all(r['status']=='ok' for r in rr)
 assert read(folder/'receipt.json')['status']=='complete'
 assert read(folder/'environment.json')==env
 all_ids += [r['request_id'] for r in rr];stage_counts[stage]=dict(n=n,predictions_sha256=sha(folder/'predictions.jsonl'))
assert len(all_ids)==len(set(all_ids))==7632
h_start=min(read(HERE/f'launch-{task}_H.json')['timestamp_utc'] for task in 'BC')
for task in 'BC':
 reg=read(HERE/f'{task}_D_registration.json')
 assert reg['timestamp_utc']<h_start
 assert reg['D_predictions_sha256']==sha(OUT/f'{task}_D/predictions.jsonl')
 assert reg==read(OUT/f'{task}_H/diagnostic_registration.json')
 receipts=[read(p) for p in OUT.glob('*/receipt.json')]
spent=sum(r['elapsed_seconds'] for r in receipts);attempts=sum(r['attempts'] for r in receipts)
assert spent<43200 and attempts<=7888
results={}
for task in 'BC':
 s=rows(HERE/f'{task}_full_scored.jsonl')
 rr=[r for r in s if r['split']=='H' and r['primary']]
 groups={}
 for r in rr:groups.setdefault(r['group_id'],{})[r['condition']]=r
 a,b=('total','subset') if task=='B' else ('original_usual','counterfact_usual')
 n=len(groups);ctrl=sum(g[a]['correct'] for g in groups.values());challenge=sum(g[b]['correct'] for g in groups.values())
 bcount=sum(g[a]['correct'] and not g[b]['correct'] for g in groups.values());ccount=sum(not g[a]['correct'] and g[b]['correct'] for g in groups.values())
 stat=read(HERE/f'{task}_full_statistics.json');cell=stat['splits']['H']['cells']['B0:T0' if task=='B' else 'B0:T0:Oprimary']
 assert (n,bcount,ccount)==(cell['n'],cell['b'],cell['c'])
 assert ctrl/n==cell['control_accuracy'] and challenge/n==cell['challenge_accuracy']
 results[task]=dict(n=n,control_correct=ctrl,challenge_correct=challenge,b=bcount,c=ccount,decision=stat['decision'])
result=dict(timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),passed=True,stages=stage_counts,unique_requests=len(all_ids),attempts=attempts,gpu_seconds=spent,primary_counts=results,checks=['frozen queue IDs/order exact','no missing/duplicate/error outputs','same complete model/runtime metadata','both D descriptions precede either H','matching registration output SHA','all startup and run costs counted','independent aggregation of saved scored rows matches frozen statistics'],limits='Aggregation audit does not independently validate dataset labels or prove a mechanism; no rerun.')
(HERE/'audit/final_integrity.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
