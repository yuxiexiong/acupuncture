"""Read-only live identity, raw/token integrity, progress, resources and measured ETA."""
from collections import defaultdict
import datetime
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys

STAGE = sys.argv[1]
assert STAGE in ('broad','dose')
NAME = 'llama31-layer-survey-v1-2026-10-28' if STAGE == 'broad' else 'llama31-single-point-dose-survey-v1-2026-10-28'
ROOT = Path(__file__).resolve().parents[2]/NAME
sys.path.insert(0,str(ROOT))
import survey

mode = sys.argv[2] if len(sys.argv)>2 else 'survey-r01'
run = ROOT/mode
c,e = (survey.io.read(run/n) for n in ('controller.json','execution.json'))
authfile = ROOT/'readiness'/('formal-authorization-r01.json' if mode.startswith('survey') else 'preflight-authorization-r01.json')
a = survey.io.read(authfile)
assert c['freeze_sha256'] == e['freeze_sha256'] == a['freeze_sha256'] == survey.check_freeze()
assert c['controller_pid'] == e['controller_pid']
assert c['controller_sha256'] == e['controller_sha256'] == a['controller_sha256'] == survey.io.sha(ROOT/'launch_survey.py')
assert c['authorization_sha256'] == e['authorization_sha256'] == survey.io.sha(authfile)
stage = 'survey' if mode.startswith('survey') else 'preflight'
r = dict(checked_utc=survey.io.utc(),mode=mode,controller=c,execution_sha256=survey.io.sha(run/'execution.json'),
    workers=[],verified_record_hashes={},formal_intervention_total=2560 if STAGE=='broad' else 2304,formal_baseline_total=8 if STAGE=='broad' else 0)
qids = {f'Q{i:02}' for i in range(1,9)}
for shard in (0,1):
    key=f'{survey.MODEL}-shard-{shard}';p=run/key
    if not (p/'receipt.json').exists():continue
    receipt=survey.io.read(p/'receipt.json');assert receipt['freeze_sha256']==c['freeze_sha256']
    assert receipt['model_id']==survey.MODEL and receipt['shard']==shard
    specs={f'records/{n}__{q["id"]}.json':(n,point,q,d) for n,point,q,d in survey.make_specs(stage,survey.MODEL,shard)}
    rows=[];groups=defaultdict(set);points=defaultdict(list)
    if receipt['record_hashes']:
        for name,h in receipt['asset_hashes'].items():assert survey.io.sha(p/name)==h
        cals=survey.io.read(p/'calibrations.json')
        for name,h in receipt['record_hashes'].items():
            assert name in specs and survey.io.sha(p/name)==h
            row=survey.io.read(p/name);survey.check_record(row,specs[name],cals)
            rows.append(row);r['verified_record_hashes'][f'{key}/{name}']=h
            if row['kind']=='dose':
                groups[(row['layer'],row['channel'],row['dose'])].add(row['question_id'])
                points[row['point_id']].append(row)
    rows.sort(key=lambda x:x['ended_utc']);doses=[v for v in rows if v['kind']=='dose']
    complete=sorted([v for v in points.values() if len(v)==(8 if STAGE=='broad' else 72)],key=lambda v:max(x['ended_utc'] for x in v))
    recent=[x for v in complete[-2:] for x in v] if complete else doses
    long=[x['output']['batch_seconds']/x['output']['generated_token_count'] for x in recent if x['output']['generated_token_count']>=32]
    seconds=sum(x['output']['batch_seconds'] for x in recent)
    log=run/f'{key}.log';lines=log.read_text(errors='replace').splitlines() if log.exists() else []
    w=dict(worker=key,shard=shard,status=receipt['status'],completed_records=len(rows),interventions=len(doses),
        baselines=sum(x['kind']=='baseline' for x in rows),expected_records=receipt['expected_records'],
        full_eight_question_conditions=sum(v==qids for v in groups.values()),complete_points=len(complete),
        recent_complete_points=[v[0]['point_id'] for v in complete[-2:]],recent_records=len(recent),
        recent_mean_intervention_seconds=seconds/len(recent) if recent else None,
        recent_mean_tokens=statistics.mean(x['output']['generated_token_count'] for x in recent) if recent else None,
        long_output_median_seconds_per_token=statistics.median(long) if long else None,
        generated_tokens=sum(x['output']['generated_token_count'] for x in rows),
        generation_seconds=sum(x['output']['batch_seconds'] for x in rows),started_utc=receipt['started_utc'],
        latest_record_utc=rows[-1]['ended_utc'] if rows else None,latest_layer=rows[-1]['layer'] if rows else None,
        wall_seconds=receipt.get('wall_seconds'),error=receipt.get('error'),
        exit=(run/f'{key}.exit').read_text().strip() if (run/f'{key}.exit').exists() else None,
        log_tail=lines[-4:],error_markers=[s for s in lines if any(t in s for t in ('Traceback','AssertionError','RuntimeError','CUDA out of memory'))])
    r['workers'].append(w)
r['formal_interventions_completed']=sum(w['interventions'] for w in r['workers']) if stage=='survey' else 0
r['formal_baselines_completed']=sum(w['baselines'] for w in r['workers']) if stage=='survey' else 0
r['completed_records']=sum(w['completed_records'] for w in r['workers'])
r['full_eight_question_conditions']=sum(w['full_eight_question_conditions'] for w in r['workers'])
pids=[c['controller_pid'],*c['worker_pids'].values()]
r['processes']=subprocess.run(['ps','-p',','.join(map(str,pids)),'-o','pid=,stat=,etimes=,args='],capture_output=True,text=True).stdout
r['gpu_csv']=subprocess.check_output(['nvidia-smi','--query-gpu=index,name,memory.used,memory.total,utilization.gpu','--format=csv,noheader'],text=True)
r['gpu_apps']=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_gpu_memory','--format=csv,noheader'],text=True)
r['filesystem_df_bytes']=subprocess.check_output(['df','-B1','/workspace/acupuncture','/data/models','/tmp'],text=True)
r['experiment_logical_bytes']=sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())
r['output_logical_bytes']=sum(p.stat().st_size for p in run.rglob('*') if p.is_file())
if stage=='survey':
    prior=survey.io.read(ROOT/'readiness/timing-estimate-r01.json')['workers'] if (ROOT/'readiness/timing-estimate-r01.json').exists() else [];etas=[]
    for w in r['workers']:
        reference=next((x for x in prior if x['shard']==w['shard']),None)
        if reference is None: continue
        use_recent=w['complete_points']>0
        mean=w['recent_mean_intervention_seconds'] if use_recent else reference['mean_intervention_seconds']
        rate=(w['long_output_median_seconds_per_token'] if use_recent else None) or reference['median_seconds_per_token']
        left=max(0,(1280 if STAGE=='broad' else 1152)-w['interventions']);baseleft=max(0,(8 if STAGE=='broad' and w['shard']==0 else 0)-w['baselines'])
        elapsed=(datetime.datetime.fromisoformat(r['checked_utc'])-datetime.datetime.fromisoformat(w['started_utc'])).total_seconds()
        overhead=max(0,reference['non_generation_seconds']-elapsed) if not w['completed_records'] else 0
        etas.append(dict(worker=w['worker'],remaining_interventions=left,main_seconds=left*mean+baseleft*reference['mean_baseline_seconds']+overhead,
            all128_seconds=(left+baseleft)*128*rate+overhead,mean_seconds_used=mean,seconds_per_token_used=rate,
            method='recent complete points' if use_recent else 'own preflight until one full eight-question point is complete'))
    main=max((x['main_seconds'] for x in etas),default=0);cap=max((x['all128_seconds'] for x in etas),default=0)
    now=datetime.datetime.fromisoformat(r['checked_utc']);bj=datetime.timezone(datetime.timedelta(hours=8))
    r['eta']=dict(workers=etas,main_remaining_seconds=main,all128_remaining_seconds=cap,
        main_finish_beijing=(now+datetime.timedelta(seconds=main)).astimezone(bj).isoformat(),
        all128_finish_beijing=(now+datetime.timedelta(seconds=cap)).astimezone(bj).isoformat(),
        limits='Only this stage; no estimate if workers list empty. Recent complete points cover all eight questions when available. Otherwise sparse partial/preflight scenario. Depth and question distribution can change; not CI or hard limit. Export/archive/reading excluded.')
if stage=='survey' and not etas:
    r['eta']={'status':'unavailable until this stage has measured timing evidence'}
print(json.dumps(r,ensure_ascii=False,indent=2))
