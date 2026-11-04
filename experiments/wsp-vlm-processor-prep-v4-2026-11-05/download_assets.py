"""Download fixed files and verify encoded bytes; never deserialize weights."""
import hashlib
import json
import os
import shutil
import time
from pathlib import Path

MODEL='Qwen/Qwen3-VL-4B-Instruct'
REVISION='ebb281ec70b05090aa6165b016eac8ec08e71b17'
HERE=Path(__file__).resolve().parent
CACHE=HERE.parents[1]/'external/wsp-vlm-model-cache/hub'
os.environ['HF_HUB_CACHE']=str(CACHE)
os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN']='1'
from huggingface_hub import HfApi,snapshot_download

start=time.time()
CACHE.mkdir(parents=True,exist_ok=True)
info=HfApi().model_info(MODEL,revision=REVISION,files_metadata=True)
assert info.sha==REVISION
official=json.loads((HERE/'audit/upstream_model_info.json').read_text())
assert official['sha']==REVISION
trusted={f['rfilename']:f for f in official['siblings']}
files=[f for f in info.siblings if Path(f.rfilename).suffix in ('.json','.jinja','.safetensors','.txt','.model')]
for f in files:
    assert f.size==trusted[f.rfilename]['size']
    if f.lfs:assert f.lfs.sha256==trusted[f.rfilename]['lfs']['sha256']
    else:assert f.blob_id==trusted[f.rfilename]['blobId']
size=sum(f.size for f in files)
assert shutil.disk_usage(CACHE).free>size*1.2
print(json.dumps(dict(stage='download',revision=info.sha,files=len(files),bytes=size,cache=str(CACHE))),flush=True)
folder=Path(snapshot_download(MODEL,revision=REVISION,cache_dir=str(CACHE),allow_patterns=[f.rfilename for f in files],max_workers=2))
records=[]
for f in files:
    path=folder/f.rfilename
    digest=hashlib.sha256();git=hashlib.sha1(f'blob {path.stat().st_size}\0'.encode())
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024*1024),b''):digest.update(block);git.update(block)
    assert path.stat().st_size==f.size
    if f.lfs:
        expected=f.lfs.sha256
        assert digest.hexdigest()==expected
        verification='upstream LFS SHA256'
    else:
        expected=f.blob_id
        assert git.hexdigest()==expected
        verification='upstream Git blob SHA1'
    records.append(dict(name=f.rfilename,bytes=f.size,sha256=digest.hexdigest(),upstream_hash=expected,verified_against=verification))
    print(json.dumps(dict(stage='verified',name=f.rfilename,bytes=f.size)),flush=True)
index=json.loads((folder/'model.safetensors.index.json').read_text())
assert set(index['weight_map'].values()) <= {r['name'] for r in records}
result=dict(model=MODEL,revision=REVISION,snapshot=str(folder),cache=str(CACHE),total_bytes=size,files=records,
            elapsed_seconds=time.time()-start,weight_deserializations=0,model_loads=0,model_calls=0)
(HERE/'audit/download_manifest.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(stage='complete',total_bytes=size,model_loads=0)),flush=True)
