"""Download exactly the authorized official checkpoint; verify every byte identity."""
import argparse
import concurrent.futures
import hashlib
import json
import os
import shutil
import time
from pathlib import Path
from common import HERE, file_hash, write_json


def run():
    import requests
    start=time.time();out=HERE.parents[1]/'external'/HERE.name/'4B';view=out/'model'
    info=json.loads((HERE/'upstream-4B.json').read_text())
    links=json.loads((out/'download-links.json').read_text())
    if (out/'download.json').exists():raise RuntimeError('Frozen manifest already exists')
    files=[f for f in info['siblings'] if '/' not in f['rfilename'] and
           Path(f['rfilename']).suffix in ('.json','.jinja','.safetensors','.txt','.model')]
    weights=[f for f in files if f['rfilename'].endswith('.safetensors')]
    needed=sum(f['size'] for f in weights if not (view/f['rfilename']).exists())
    if shutil.disk_usage(out).free<needed+25*1024**3:raise RuntimeError('Insufficient disk reserve')
    def transfer(f):
        name=f['rfilename'];final=view/name
        if final.exists():return
        partial=final.with_suffix('.safetensors.partial')
        offset=partial.stat().st_size if partial.exists() else 0
        try:
            with requests.get(links[name],headers={'Range':f'bytes={offset}-'} if offset else {},
                              stream=True,timeout=(15,90)) as response:
                if response.status_code!=(206 if offset else 200):
                    raise RuntimeError(f'CDN status {response.status_code} for {name}')
                with partial.open('ab' if offset else 'xb') as stream:
                    for chunk in response.iter_content(8*1024**2):stream.write(chunk)
        except requests.RequestException as exc:
            raise RuntimeError('CDN transfer failed: '+type(exc).__name__) from None
        assert partial.stat().st_size==f['size']
        assert file_hash(partial)==f['lfs']['sha256']
        partial.rename(final)
        print(json.dumps(dict(verified=name,bytes=f['size'])),flush=True)
    print(json.dumps(dict(stage='download',model=info['id'],revision=info['sha'],bytes=needed)),flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(transfer,weights))
    hashes={}
    for f in files:
        path=view/f['rfilename'];assert path.stat().st_size==f['size']
        sha=file_hash(path);expected=f.get('lfs',{}).get('sha256')
        if expected:assert sha==expected
        else:assert hashlib.sha1(f"blob {f['size']}\0".encode()+path.read_bytes()).hexdigest()==f['blobId']
        hashes[f['rfilename']]=sha
    write_json(out/'download.json',dict(model=info['id'],revision=info['sha'],model_root=str(view),
        files=hashes,total_bytes=sum(f['size'] for f in files),elapsed_seconds=time.time()-start,
        source_endpoint='Official HF authorized signed CDN URLs; no mirror',
        verified_against='Official metadata LFS SHA256 / Git blob SHA1',model_loads=0))
    print('COMPLETE: all files verified',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--size',choices=['4B'],default='4B');p.parse_args();run()
