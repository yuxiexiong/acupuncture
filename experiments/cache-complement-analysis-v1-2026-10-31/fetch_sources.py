import concurrent.futures, hashlib, json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PREFIX='experiments/early-state-localization-stage2-v2-2026-10-30/'
COMMIT='73185a40de0c779d55beac204c7d46683736b5ef'
tree={x['path']:x for x in json.loads((ROOT/'source-tree-index.json').read_text())}
paths=['analysis/b_validate-r01.json','data/validation-r01.json','exports/b_validate-r01-answers.jsonl.zst','exports/exports-manifest.json','freeze-r01.json','stage2.py','analyze_stage2.py','IMPLEMENTATION.zh-CN.md','reading/validation-r01/joined.json.zst','reading/validation-r01/key.json.zst','reading/validation-r01/lock.json','readiness/a-lock-r01.json','runs/b_validate-r01/verification.json','runs/b_validate-r01/worker-0/metadata.json','readiness/ops/export_runs.py']
paths += [f'runs/b_validate-r01/worker-{i}/receipt.json' for i in range(8)]
def get(p):
 url=f'https://raw.githubusercontent.com/yuxiexiong/acupuncture/{COMMIT}/{PREFIX}{p}'
 dst=ROOT/'source'/p
 b=dst.read_bytes() if dst.exists() else subprocess.check_output(['curl','-sSL','--fail','--max-time','60',url])
 sha=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
 assert sha==tree[PREFIX+p]['sha'],p
 dst=ROOT/'source'/p;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(b)
 return dict(path=p,url=url,size=len(b),git_blob_sha=sha,sha256=hashlib.sha256(b).hexdigest())
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex: rows=list(ex.map(get,paths))
(ROOT/'source-manifest.json').write_text(json.dumps(dict(commit=COMMIT,files=rows),indent=2))
print('Downloaded and Git-blob-verified',len(rows),'files;',sum(r['size'] for r in rows),'bytes')
