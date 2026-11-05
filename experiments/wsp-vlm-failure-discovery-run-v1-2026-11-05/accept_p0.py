"""Validate saved P0 artifacts only; never loads a model."""
from pathlib import Path
import json,hashlib,datetime,re
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Local archived artifacts or the server's canonical cumulative run root.
OUT=ROOT/'external/wsp-vlm-channel-prep-v5-2026-11-05'
if not (OUT/'P0/predictions.jsonl').exists():OUT=HERE/'evidence'
p=OUT/'P0/predictions.jsonl';rows=[json.loads(x) for x in p.read_text().splitlines()]
receipt=read(OUT/'P0/receipt.json');assert receipt['status']=='complete' and receipt['attempts']==64
expected=read(ROOT/'experiments/wsp-vlm-channel-prep-v5-2026-11-05/audit/processor_receipt.json')['p0_serialization']
assert len(rows)==64 and len({x['request_id'] for x in rows})==64
assert [x['request_id'] for x in rows]==[x['request_id'] for x in expected]
for r,e in zip(rows,expected):
 assert r['status']=='ok' and r['finish_reason']=='eos' and not r['truncated']
 assert all(r[k]==e[k] for k in ('input_tokens','visual_tokens','image_grid_thw','rendered_chat_sha256','input_ids_sha256'))
 assert len(r['generated_ids'])==r['output_tokens']<=128
 if ':B:' in r['request_id']:assert re.fullmatch('[0-9]+',r['text'].strip())
 elif ':no_image:' in r['request_id']:assert r['text'].strip() in ('dog','ant')
 else:assert r['text'].strip() in ('red square','blue circle')
env=read(OUT/'P0/environment.json')
assets=read(ROOT/'experiments/wsp-vlm-processor-prep-v4-2026-11-05/audit/download_manifest.json')
missing={f['name'] for f in assets['files']} - env['snapshot_file_sha256'].keys()
supplement=OUT/'P0/supplemental_asset_sha256.json'
if not supplement.exists():
 snapshot=Path(assets['snapshot'])
 supplement.write_text(json.dumps({name:sha(snapshot/name) for name in sorted(missing)},indent=2)+'\n')
hashes=dict(env['snapshot_file_sha256'],**read(supplement))
for f in assets['files']:assert hashes[f['name']]==f['sha256']
means={}
for key,needle,n in [('B_image',':B:',1168),('C_image',':C:image:',5120),('C_no_image',':C:no_image:',1280)]:
 times=[r['elapsed_seconds'] for r in rows if needle in r['request_id']]
 means[key]=dict(n=len(times),mean_seconds=sum(times)/len(times),formal_requests=n)
request_estimate=sum(v['mean_seconds']*v['formal_requests'] for v in means.values())
spent=sum(read(f)['elapsed_seconds'] for f in OUT.glob('*/receipt.json'))
assert request_estimate*1.2+4*receipt['elapsed_seconds']<43200-spent
result=dict(accepted=True,timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),predictions_sha256=sha(p),p0_requests=64,status='real GPU engineering acceptance; not scientific accuracy acceptance',checks=['64 IDs in frozen order','exact CPU serialization hashes and visual tokens','64 EOS outputs; zero truncation and format failures','all 12 model assets match download manifest','BF16/SDPA model execution completed without infrastructure error'],timing_by_type=means,rough_formal_request_seconds=request_estimate,rough_with_20pct_and_four_P0_wall_load_allowances=request_estimate*1.2+4*receipt['elapsed_seconds'],spent_gpu_seconds=spent,eta_limit='P0 geometry images are not representative; update using B_D and C_D; memory peak was not instrumented in v5')
(OUT/'P0_acceptance.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
