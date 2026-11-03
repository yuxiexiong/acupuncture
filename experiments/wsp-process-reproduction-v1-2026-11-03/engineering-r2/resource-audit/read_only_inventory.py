import os,stat,json,datetime,shutil
from pathlib import Path
from collections import defaultdict
W=Path('/workspace/acupuncture/external/wsp')
paths=[W/'forward-ckpt-cache',W/'fa01-0p8b-r1/ckpt',W/'fa01-0p8b-r2/ckpt',W/'fa01-4b-r1/ckpt',W/'uv-cache',W/'text-Qwen3.5-4B',W/'vllm-cache',W/'flashinfer-cache',W/'rustup/tmp',W/'cargo-mirror',Path('/workspace/miniconda/pkgs'),Path('/workspace/hf_cache'),Path('/root/.cache/pip'),Path('/root/.cache/uv')]
results=[]; allnodes={}; allcounts=defaultdict(int)
for root in paths:
 nodes={}; counts=defaultdict(int); regular=0; bysuffix=defaultdict(int)
 for base,dirs,files in os.walk(root,followlinks=False):
  for name in files:
   p=Path(base)/name
   try:s=p.lstat()
   except OSError:continue
   key=(s.st_dev,s.st_ino);nodes[key]=s;counts[key]+=1
   allnodes[key]=s;allcounts[key]+=1
   if stat.S_ISREG(s.st_mode):regular+=1;bysuffix[p.suffix]+=s.st_blocks*512
 results.append({'path':str(root),'filesystem_device':root.stat().st_dev if root.exists() else None,'regular_files':regular,
   'unique_allocated_bytes':sum(s.st_blocks*512 for s in nodes.values()),
   'reclaimable_bytes_if_whole_directory_removed':sum(s.st_blocks*512 for k,s in nodes.items() if counts[k]>=s.st_nlink),
   'linked_outside_bytes':sum(s.st_blocks*512 for k,s in nodes.items() if counts[k]<s.st_nlink),
   'largest_extensions':sorted(bysuffix.items(),key=lambda x:-x[1])[:6]})
refs=[]
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 hits=set()
 for link in [proc/'cwd',proc/'exe',*list((proc/'fd').glob('*'))]:
  try: target=os.readlink(link)
  except OSError:continue
  for root in paths:
   if target==str(root) or target.startswith(str(root)+'/'):hits.add(target)
 try:
  for line in (proc/'maps').read_text().splitlines():
   parts=line.split(maxsplit=5)
   if len(parts)==6 and any(parts[5].startswith(str(r)+'/') for r in paths):hits.add(parts[5])
 except OSError:pass
 if hits:
  try:name=(proc/'comm').read_text().strip()
  except OSError:name='unknown'
  refs.append({'pid':int(proc.name),'comm':name,'paths':sorted(hits)[:30]})
builds=[]
for root in paths[:4]:
 for p in root.glob('*/build.json'):
  r=json.loads(p.read_text());sp=Path(r['snapshot']);mp=sp/'manifest.json'
  builds.append({'build_json':str(p),'checkpoint_bytes':(p.parent/'model.safetensors').stat().st_size,
    'snapshot':str(sp),'snapshot_manifest_exists':mp.exists(),'snapshot_files_present':all((sp/(t['name']+'.npy')).exists() for t in json.loads(mp.read_text()).get('tensors',[])) if mp.exists() else False,
    'changed_values':r['changed_values'],'model_sha256':r['model_sha256']})
print(json.dumps({'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'operation':'read_only_no_deletion_no_search','disk':{p:dict(zip(['total','used','free'],shutil.disk_usage(p))) for p in ['/workspace','/data']},'candidates':results,'observed_process_references':refs,'checkpoint_builds':builds},indent=2))
