"""Initial Llama-only timing scenarios from completed bounded preflight; no model load."""
import datetime
import json
from pathlib import Path
import statistics
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import survey

runs=[ROOT/'preflight-r02'/f'{survey.MODEL}-shard-{i}' for i in (0,1)]
receipts=survey.check_pair(runs,'preflight');workers=[]
for run,receipt in zip(runs,receipts):
    rows=[survey.io.read(run/f) for f in receipt['record_hashes']]
    doses=[r for r in rows if r['kind']=='dose'];base=[r for r in rows if r['kind']=='baseline']
    seconds=sum(r['output']['batch_seconds'] for r in rows)
    long=[r['output']['batch_seconds']/r['output']['generated_token_count'] for r in doses if r['output']['generated_token_count']>=32]
    rate=statistics.median(long or [r['output']['batch_seconds']/r['output']['generated_token_count'] for r in doses])
    mean=statistics.mean(r['output']['batch_seconds'] for r in doses)
    bmean=statistics.mean(r['output']['batch_seconds'] for r in base)
    overhead=max(0,receipt['wall_seconds']-seconds);shard=receipt['shard'];n=12800+(8 if shard==0 else 0)
    workers.append(dict(shard=shard,worker=run.name,preflight_receipt_sha256=survey.io.sha(run/'receipt.json'),
        intervention_samples=len(doses),mean_intervention_tokens=statistics.mean(r['output']['generated_token_count'] for r in doses),
        mean_intervention_seconds=mean,mean_baseline_seconds=bmean,median_seconds_per_token=rate,
        long_output_samples=len(long),non_generation_seconds=overhead,
        formal_interventions=12800,formal_baselines=8 if shard==0 else 0,
        initial_main_seconds=12800*mean+(8 if shard==0 else 0)*bmean+overhead,
        initial_all128_seconds=n*128*rate+overhead))
result=dict(status='measured_preflight_scenarios',created_utc=survey.io.utc(),freeze_sha256=survey.check_freeze(),
    workers=workers,main_wall_seconds=max(w['initial_main_seconds'] for w in workers),
    all128_wall_seconds=max(w['initial_all128_seconds'] for w in workers),
    main_worker_gpu_hours=sum(w['initial_main_seconds'] for w in workers)/3600,
    all128_worker_gpu_hours=sum(w['initial_all128_seconds'] for w in workers)/3600,
    method='Max of two parallel workers; each uses only its Llama preflight ten signed doses at first/middle/last assigned point and Q01/Q04/Q08. Model loading, asset hash and calibration overhead included once. Formal baseline8 only on shard0.',
    limitations=['Only three question/depth anchors per worker; depth/channel/question distributions may change. Early scenario, not confidence interval or hard bound.',
        'All128 uses measured median seconds/token from own intervention outputs >=32 tokens (or all if none), times128; not a maximum runtime guarantee.',
        'Initial record IO growth is not separately measured; subsequent actual wall/progress estimates must account for it if material.',
        'No queued models. Export, transfer/archive, and open reading are separate; unmeasured durations omitted.',
        'Do not extrapolate Qwen speed or stop a healthy run because an ETA was exceeded.'])
survey.io.immutable(ROOT/'readiness/timing-estimate-r01.json',result)
print(json.dumps(result,ensure_ascii=False,indent=2))
