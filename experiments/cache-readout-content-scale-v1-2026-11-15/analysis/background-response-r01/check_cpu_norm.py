"""Check CPU re-evaluation against saved GPU BF16 norm outputs; no model."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import json
from pathlib import Path
import sys
import time
import torch
from analyse_saved import sha

torch.set_num_threads(1)
start = time.monotonic()
root, manifest_path, output = map(Path, sys.argv[1:])
manifest = json.loads(manifest_path.read_text())
files = manifest['runs']['formal-20261115-r01']['files']
checked, different, max_units, examples = 0, 0, 0., []
for rel in sorted(p for p in files if p.endswith(('-C11-t2.pt','-H11-t2.pt'))):
    assert sha(root/rel) == files[rel]['sha256']
    tensors = torch.load(root/rel, map_location='cpu', weights_only=True)
    for layer, t in tensors.items():
        x = t['x1'].reshape(32,128)
        v = t['weight']*(x.float()*t['inv_r1'].float().reshape(32,1)).to(x.dtype)
        rebuilt = (v*torch.nn.functional.silu(t['z'].float()).reshape_as(v)).to(x.dtype)
        saved = t['native_norm'].reshape_as(rebuilt)
        mismatch = rebuilt != saved
        checked += saved.numel()
        if mismatch.any():
            different += int(mismatch.sum())
            ulps = torch.maximum(torch.nextafter(saved.abs(), torch.full_like(saved,float('inf')))-saved.abs(), torch.nextafter(rebuilt.abs(), torch.full_like(rebuilt,float('inf')))-rebuilt.abs()).double()
            units = float(((rebuilt.double()-saved.double()).abs()/ulps)[mismatch].max())
            max_units = max(max_units, units)
            examples.append({'file':rel,'layer':layer,'count':int(mismatch.sum()),'max_output_ulp':units,'max_abs':float((rebuilt.float()-saved.float()).abs().max())})
assert not torch.cuda.is_initialized()
result={'checked_values':checked,'different_values':different,'maximum_output_ulp':max_units,'mismatch_layers':examples,'elapsed_seconds':time.monotonic()-start,'cuda_initialized':False,'model_forwards':0}
with output.open('x') as f:json.dump(result,f,indent=2)
print(json.dumps({k:v for k,v in result.items() if k!='mismatch_layers'}))
