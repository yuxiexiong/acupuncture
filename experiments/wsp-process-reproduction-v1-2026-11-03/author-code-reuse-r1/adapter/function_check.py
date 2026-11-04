"""Original intervention functions on tiny synthetic tensors; zero model calls."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import torch

root=Path(sys.argv[1]); fixtures=json.loads((root/'function-fixture.json').read_text())
edits={}
w=torch.tensor([[1.,2.,3.],[4.,5.,6.]])
u=torch.tensor([1.,0.])
ns=dict(torch=torch,diffH={20:np.array([1.,0.],dtype=np.float32)},downweights={19:w},
        edited=lambda:list(edits),drop_edit=lambda name:edits.pop(name),save_edit=lambda name,t:edits.__setitem__(name,t.clone()),
        base_mlp_weights={15:w,19:w},u_rep={15:u,19:u},writer_subsets={15:torch.tensor([1]),19:torch.tensor([1])})
for f in fixtures:
    assert hashlib.sha256(f['source'].encode()).hexdigest()==f['sha256']
    exec(compile(f['source'],f"author-action-{f['action']}:{f['name']}",'exec'),ns)
ns['mlp_direction_edit']([19],1.)
assert torch.equal(edits['model.language_model.layers.19.mlp.down_proj.weight'],torch.tensor([[0.,0.,0.],[4.,5.,6.]]))
ns['set_subset_edit'](6)
for v in edits.values():
    assert torch.equal(v,torch.tensor([[1.,-10.,3.],[4.,5.,6.]]))
receipt={'status':'passed','checks':['unchanged author dense direction function','unchanged author subset direction function','unselected columns unchanged'],
         'function_sources':[{k:v for k,v in f.items() if k!='source'} for f in fixtures],
         'gpu_seconds':0,'formal_started':False,'scope':'synthetic algebra and call contract; not a scientific candidate or ranking result'}
(root/'function-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
