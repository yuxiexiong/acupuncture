"""Read-only CPU snapshot. Run in the server checkout; no model imports."""
import datetime,json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
RUN=Path(__file__).resolve().parent
OUT=ROOT/'external/wsp-vlm-channel-prep-v5-2026-11-05'
def rows(path):
 if not path.exists():return []
 lines=path.read_text().splitlines();out=[]
 for i,line in enumerate(lines):
  try:out.append(json.loads(line))
  except json.JSONDecodeError:
   if i!=len(lines)-1:raise
 return out
report=dict(timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),stages={},disks={})
for path in (ROOT,ROOT/'external/wsp-vlm-model-cache','/tmp'):
 d=shutil.disk_usage(path);report['disks'][str(path)]=dict(free_gib=d.free/2**30,total_gib=d.total/2**30)
for stage,expected in [('P0',64),('B_D',464),('C_D',2560),('B_H',704),('C_H',3840)]:
 p=OUT/stage;r=rows(p/'predictions.jsonl')
 durations=[x['elapsed_seconds'] for x in r if x.get('status')=='ok']
 item=dict(valid=sum(x.get('status')=='ok' for x in r),errors=sum(x.get('status')=='error' for x in r),expected=expected,attempts=len(rows(p/'attempts.jsonl')),mean_request_seconds=sum(durations)/len(durations) if durations else None)
 if (p/'receipt.json').exists():item['receipt']=json.loads((p/'receipt.json').read_text())
 launch=RUN/f'launch-{stage}.json'
 if launch.exists():
  info=json.loads(launch.read_text());item['launch']=info
  item['process']=subprocess.run(['ps','-p',str(info['pid']),'-o','pid=,etimes=,args='],capture_output=True,text=True).stdout.strip()
 report['stages'][stage]=item
report['budget_receipts']={str(p.relative_to(OUT)):json.loads(p.read_text()) for p in OUT.glob('*/receipt.json')}
report['output_bytes']=sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())
report['gpu']=subprocess.run(['nvidia-smi','--query-gpu=index,name,memory.used,utilization.gpu','--format=csv,noheader'],capture_output=True,text=True).stdout.strip()
print(json.dumps(report,ensure_ascii=False,indent=2))
