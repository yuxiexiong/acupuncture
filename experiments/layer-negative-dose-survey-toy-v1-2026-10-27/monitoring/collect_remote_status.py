from pathlib import Path
import json,sys,hashlib,subprocess,datetime,collections,shutil
p=Path('/workspace/acupuncture/experiments/layer-negative-dose-survey-toy-v1-2026-10-27')
mode=sys.argv[1] if len(sys.argv)>1 else 'preflight-r01'
out=p/mode
read=lambda f:json.loads(f.read_text())
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
c=read(out/'controller.json');e=read(out/'execution.json')
a=read(p/('readiness/preflight-authorization-r01.json' if mode.startswith('preflight') else 'readiness/formal-authorization-r01.json'))
assert c['freeze_sha256']==e['freeze_sha256']==a['freeze_sha256']==sha(p/'freeze.json')
assert c['controller_pid']==e['controller_pid']
assert c['controller_sha256']==e['controller_sha256']==a['controller_sha256']==sha(p/('preflight_controller.py' if mode.startswith('preflight') else 'launch_survey.py'))
assert c['authorization_sha256']==e['authorization_sha256']==sha(p/('readiness/preflight-authorization-r01.json' if mode.startswith('preflight') else 'readiness/formal-authorization-r01.json'))
r={'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'mode':mode,'controller':c,'execution_sha256':sha(out/'execution.json'),'workers':[],'verified_record_hashes':{}}
for m in ('2b','4b','9b'):
 for shard in (0,1):
  name=f'{m}-shard-{shard}';d=out/name
  if not (d/'receipt.json').exists():continue
  receipt=read(d/'receipt.json');rows=[];groups=collections.defaultdict(set)
  for f,h in receipt['record_hashes'].items():
   assert sha(d/f)==h
   row=read(d/f);tokens=row['output']['token_ids'];tsha=hashlib.sha256(json.dumps(tokens,separators=(',',':')).encode()).hexdigest()
   assert tsha==row['output']['token_sha256'] and len(tokens)==row['output']['generated_token_count']<=128
   rows.append(row);r['verified_record_hashes'][f'{name}/{f}']=h
   if row['kind']=='dose':groups[(row['layer'],row['channel'],row['dose'])].add(row['question_id'])
  rows.sort(key=lambda x:x['ended_utc'])
  r['workers'].append(dict(worker=name,status=receipt['status'],completed=len(rows),expected=receipt['expected_records'],full_eight_question_groups=sum(len(v)==8 for v in groups.values()),tokens=sum(len(x['output']['token_ids']) for x in rows),generation_seconds=sum(x['output']['batch_seconds'] for x in rows),started_utc=receipt['started_utc'],last_record_utc=rows[-1]['ended_utc'] if rows else None,last_layer=rows[-1]['layer'] if rows else None,wall_seconds=receipt.get('wall_seconds'),error=receipt.get('error'),exit=(out/f'{name}.exit').read_text().strip() if (out/f'{name}.exit').exists() else None))
pids=[c['controller_pid'],*c['worker_pids'].values()]
r['processes']=subprocess.run(['ps','-p',','.join(map(str,pids)),'-o','pid=,stat=,etimes=,args='],capture_output=True,text=True).stdout
r['gpu_csv']=subprocess.check_output(['nvidia-smi','--query-gpu=index,name,memory.used,memory.total,utilization.gpu','--format=csv,noheader'],text=True)
r['gpu_apps']=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_gpu_memory','--format=csv,noheader'],text=True)
r['filesystem_df_bytes']=subprocess.check_output(['df','-B1','/workspace/acupuncture','/data/models','/tmp'],text=True)
r['experiment_logical_bytes']=sum(f.stat().st_size for f in p.rglob('*') if f.is_file())
r['output_logical_bytes']=sum(f.stat().st_size for f in out.rglob('*') if f.is_file())
r['total_completed']=sum(w['completed'] for w in r['workers']);r['expected_total']=c['expected_records']
print(json.dumps(r,ensure_ascii=False,indent=2))
