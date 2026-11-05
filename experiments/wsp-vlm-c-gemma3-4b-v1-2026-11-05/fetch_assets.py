"""Use the existing HF account via official TLS; never send its token to a mirror."""
import hashlib
import json
import os
import shlex
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


class OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        result=super().redirect_request(req,fp,code,msg,headers,newurl)
        if urllib.parse.urlsplit(newurl).hostname!='huggingface.co':
            result.remove_header('Authorization')
        return result


def run():
    info=json.loads((HERE/'upstream-4B.json').read_text())
    remote='/workspace/acupuncture/external/'+HERE.name+'/4B'
    # Credentials stay in process memory and are used only at the official HF host.
    r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gqa-h20',
        "cd /workspace/acupuncture && .venv-bench/bin/python -c 'from huggingface_hub import get_token; print(get_token() or \"\")'"],
        capture_output=True,text=True,timeout=30)
    if r.returncode or not r.stdout.strip(): raise RuntimeError('Existing HF credential unavailable')
    token=r.stdout.strip()
    opener=urllib.request.build_opener(OfficialRedirect())
    dest=ROOT/'external'/HERE.name/'4B/model';dest.mkdir(parents=True,exist_ok=True)
    links={}
    for f in info['siblings']:
        name=f['rfilename']
        if '/' in name or Path(name).suffix not in ('.json','.jinja','.safetensors','.txt','.model'):continue
        url=f'https://huggingface.co/{info["id"]}/resolve/{info["sha"]}/{name}'
        req=urllib.request.Request(url,headers={'Authorization':'Bearer '+token},
                                  method='HEAD' if name.endswith('.safetensors') else 'GET')
        with opener.open(req,timeout=60) as response:
            if name.endswith('.safetensors'):
                final=response.geturl();host=urllib.parse.urlsplit(final).hostname
                if host=='huggingface.co' or not (host.endswith('.hf.co') or host.endswith('.huggingface.co')):
                    raise RuntimeError('Expected an official signed CDN location')
                links[name]=final
            else:
                data=response.read();assert len(data)==f['size']
                expected=f.get('lfs',{}).get('sha256')
                actual=hashlib.sha256(data).hexdigest() if expected else hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()
                assert actual==(expected or f['blobId'])
                (dest/name).write_bytes(data)
        print(json.dumps(dict(prepared=name,bytes=f['size'],signed_url_printed=False)),flush=True)
    code="""import os,pathlib,json,sys
x=json.load(sys.stdin);p=pathlib.Path(x['root']);p.mkdir(parents=True,exist_ok=True)
fd=os.open(p/'download-links.json',os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
with os.fdopen(fd,'w') as f:json.dump(x['links'],f)
print('Signed links stored privately; no HF token stored')"""
    r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gqa-h20','python3 -c '+shlex.quote(code)],
        input=json.dumps(dict(root=remote,links=links)),text=True,capture_output=True,timeout=30)
    if r.returncode: raise RuntimeError('Link delivery failed; no secret printed')
    subprocess.run(['rsync','-a',str(dest)+'/',f'gqa-h20:{remote}/model/'],check=True)
    print('Official access verified; small files delivered; weight links ready')


if __name__=='__main__':run()
