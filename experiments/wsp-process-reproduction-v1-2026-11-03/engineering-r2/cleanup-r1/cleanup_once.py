"""One authorized WSP cache cleanup; fixed allowlist, preserved records, no model runs."""
import gzip,hashlib,json,os,shutil,stat,sys,tarfile,time
from pathlib import Path
from collections import Counter
W=Path('/workspace/acupuncture/external/wsp')
DEST=W/'cleanup-r1-2026-11-03'
TARGETS=[W/'forward-ckpt-cache',W/'fa01-0p8b-r1/ckpt',W/'fa01-0p8b-r2/ckpt',W/'fa01-4b-r1/ckpt',W/'uv-cache']
ENV=Path('/workspace/acupuncture/.venv-wsp')

def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(name,obj):
 (DEST/name).write_text(json.dumps(obj,indent=2)+'\n')
def inside(p,root):return p==root or root in p.parents
def files(root):
 for base,dirs,names in os.walk(root,followlinks=False):
  for name in names:yield Path(base)/name

def inventory(roots,protected=False):
 out={}
 for root in roots:
  for p in files(root):
   if protected and (inside(p,DEST) or any(inside(p,t) for t in TARGETS)):continue
   s=p.lstat()
   r={'inode':s.st_ino,'device':s.st_dev,'size':s.st_size,'mtime_ns':s.st_mtime_ns,'mode':s.st_mode}
   if stat.S_ISLNK(s.st_mode):r['link']=os.readlink(p)
   if not protected:r.update(nlink=s.st_nlink,allocated=s.st_blocks*512)
   elif stat.S_ISREG(s.st_mode) and not inside(p,ENV) and p.suffix in ('.json','.jsonl','.log','.txt','.npy','.pt','.yaml','.yml'):
    r['sha256']=sha(p)
   out[str(p)]=r
 return out

def no_users():
 refs=[]
 for proc in Path('/proc').iterdir():
  if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
  for p in [proc/'cwd',proc/'exe',*list((proc/'fd').glob('*'))]:
   try:target=Path(os.readlink(p))
   except OSError:continue
   if any(inside(target,t) for t in TARGETS):refs.append([proc.name,str(target)])
  try:
   for line in (proc/'maps').read_text().splitlines():
    parts=line.split(maxsplit=5)
    if len(parts)==6 and any(inside(Path(parts[5]),t) for t in TARGETS):refs.append([proc.name,parts[5]])
  except OSError:pass
 assert not refs,refs
 for base,dirs,names in os.walk(ENV,followlinks=False):
  for name in dirs+names:
   p=Path(base)/name
   if p.is_symlink():assert not any(inside(p.resolve(),t) for t in TARGETS),str(p)

def dump_gz(name,obj):
 with gzip.open(DEST/name,'wt') as f:json.dump(obj,f)
def read_gz(name):
 with gzip.open(DEST/name,'rt') as f:return json.load(f)

mode=sys.argv[1]
if mode=='prepare':
 DEST.mkdir(exist_ok=False)
 assert all(p.is_dir() and not p.is_symlink() and p.resolve()==p for p in TARGETS)
 no_users()
 selected=inventory(TARGETS)
 # Back up every non-weight checkpoint file, plus any download-cache logs.
 archive={}
 builds=[]
 for ptext,r in selected.items():
  p=Path(ptext)
  if any(inside(p,t) for t in TARGETS[:4]) and p.name!='model.safetensors' or inside(p,TARGETS[4]) and p.suffix=='.log':
   assert stat.S_ISREG(p.lstat().st_mode),str(p)
   archive[str(p.relative_to(W))]=sha(p)
  if p.name=='build.json' and any(inside(p,t) for t in TARGETS[:4]):
   b=json.loads(p.read_text());sp=Path(b['snapshot']);mp=sp/'manifest.json'
   assert sha(mp)==b['snapshot_manifest_sha256']
   for t in json.loads(mp.read_text())['tensors']:
    assert sha(sp/(t['name']+'.npy'))==t['snapshot_sha256']
   builds.append({'original_path':ptext,'record':b})
 with tarfile.open(DEST/'preserved-cache-records.tgz','w:gz') as tar:
  for rel in archive:tar.add(W/rel,arcname=rel,recursive=False)
 with tarfile.open(DEST/'preserved-cache-records.tgz') as tar:
  for rel,digest in archive.items():
   assert hashlib.sha256(tar.extractfile(rel).read()).hexdigest()==digest
 protected=inventory([W,ENV,Path('/data/models/Qwen3.5-4B-851bf6e')],True)
 dump_gz('selected-before.json.gz',selected);dump_gz('protected-before.json.gz',protected)
 save('preserved-files.json',archive);save('build-records.json',builds)
 nodes={};counts=Counter()
 for r in selected.values():
  key=(r['device'],r['inode']);nodes[key]=r;counts[key]+=1
 estimated=sum(r['allocated'] for k,r in nodes.items() if counts[k]>=r['nlink'])
 receipt={'status':'prepared_not_deleted','targets':list(map(str,TARGETS)),'selected_files':len(selected),
          'protected_files':len(protected),'preserved_record_files':len(archive),'build_records':len(builds),
          'estimated_reclaimable_bytes':estimated,'backup_bytes':(DEST/'preserved-cache-records.tgz').stat().st_size,
          'backup_sha256':sha(DEST/'preserved-cache-records.tgz'),'free_bytes':shutil.disk_usage(W).free}
 save('prepare.json',receipt);print(json.dumps(receipt),flush=True)
elif mode=='apply':
 prepared=json.loads((DEST/'prepare.json').read_text())
 assert sha(DEST/'preserved-cache-records.tgz')==prepared['backup_sha256']
 assert inventory(TARGETS)==read_gz('selected-before.json.gz'),'cache changed since preparation'
 no_users()
 before=shutil.disk_usage(W).free
 for p in TARGETS:
  assert p.is_dir() and not p.is_symlink() and p.resolve()==p
  shutil.rmtree(p)
 after=shutil.disk_usage(W).free
 protected_before=read_gz('protected-before.json.gz')
 protected_after=inventory([W,ENV,Path('/data/models/Qwen3.5-4B-851bf6e')],True)
 removed=[p for p in protected_before if p not in protected_after]
 changed=[p for p in protected_before if p in protected_after and protected_after[p]!=protected_before[p]]
 receipt={'status':'passed' if not removed and not changed else 'preservation_check_failed',
          'deleted_cache_directories':list(map(str,TARGETS)),'free_before_bytes':before,'free_after_bytes':after,
          'observed_freed_bytes':after-before,'protected_files':len(protected_before),'protected_missing':removed,
          'protected_changed':changed,'backup_sha256':prepared['backup_sha256'],'formal_search_started':False,
          'checked_unix':time.time()}
 save('receipt.json',receipt);print(json.dumps(receipt),flush=True)
 assert not removed and not changed
else:raise ValueError(mode)
