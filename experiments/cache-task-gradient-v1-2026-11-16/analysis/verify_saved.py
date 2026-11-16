"""CPU integrity check of saved gradients, inputs and the frozen projection records."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
from pathlib import Path
import sys
import torch
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import tg_run as R
from tg_analysis import projection

torch.set_num_threads(1)
fr=R.W.read(HERE/'readiness/freeze-server-r01.json')
files={};checked=0
for stage in ('engineering','formal'):
    root=HERE/'runs'/f'{stage}-20261116-r01'
    rc=R.W.read(root/'receipt.json');assert rc['status']=='completed'
    for rel,h in rc['files'].items():assert R.W.sha(root/rel)==h
    for path in sorted((root/'records').glob('*/*.json')):
        rec=R.W.read(path);r,d=rec['receiver'],rec['donor'];grads={};physical={}
        for bg in ('C','H'):
            grads[bg]=torch.load(root/f'gradients/{r}/{d}-{bg}.pt',map_location='cpu',weights_only=True)
            assert set(grads[bg])==set(R.K.G)
            assert all(g.dtype==torch.float64 and g.shape==(32,128) and torch.isfinite(g).all() for g in grads[bg].values())
            src=R.NGU_OLD/f'tensors/{r}/{d}-{bg}X-t2.pt'
            assert R.W.sha(src)==fr['task_assets'][str(src.relative_to(R.ROOT))]
            old=torch.load(src,map_location='cpu',weights_only=True)
            physical[bg]={l:old[l]['patch'].double()-old[l]['native'].double() for l in R.K.G}
        assert projection(grads,physical)==rec['projection'];checked+=1
for p in sorted((HERE/'runs').rglob('*')):
    if p.is_file():files[str(p.relative_to(HERE))]={'sha256':R.W.sha(p),'bytes':p.stat().st_size}
assert not torch.cuda.is_initialized()
a=dict(status='passed',files=files,total_bytes=sum(x['bytes'] for x in files.values()),
       all_gradient_files=376,projection_records_reproduced=checked,model_forwards=0,cuda_initialized=False,
       audit_script_sha256=R.W.sha(__file__))
R.W.write(HERE/'readiness/artifacts-final-r01.json',a,immutable=True)
print({k:v for k,v in a.items() if k!='files'})
