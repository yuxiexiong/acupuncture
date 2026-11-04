"""Read-only CPU audit of existing directions; no model construction or forward."""
import hashlib
import json
from pathlib import Path
import numpy as np
import torch
from safetensors import safe_open
from tokenizers import Tokenizer

torch.set_num_threads(4)
base=Path('/workspace/acupuncture/external/wsp/text-Qwen3.5-4B-r2')
work=Path('/workspace/acupuncture/external/wsp/fleet-v1/math-4b/work')
out=Path('/workspace/acupuncture/external/wsp-observer-audit/author-comparison-r1')
index=base/'model.safetensors.index.json'
mapping=json.loads(index.read_text())['weight_map'] if index.exists() else None
def tensor(name, rows=None):
    path=base/mapping[name] if mapping else next(base.glob('*.safetensors'))
    with safe_open(path,framework='pt',device='cpu') as f:
        if rows is None:return f.get_tensor(name).float()
        s=f.get_slice(name)
        return torch.stack([s[i:i+1][0].float() for i in rows])
tok=Tokenizer.from_file(str(base/'tokenizer.json'))
nf=tensor('model.language_model.norm.weight')
ename='model.language_model.embed_tokens.weight'
def orth(x,b):
    q=torch.linalg.qr(b,mode='reduced').Q
    u=x-q@(q.T@x)
    return u/u.norm()
positive=['Wait',' Wait','But',' But','However',' However','Maybe',' Maybe','Perhaps',' Perhaps',' check',' verify',' again',' reconsider']
neutral=['Therefore',' Therefore','Thus',' Thus','Hence',' Hence','Next',' Next',' calculate',' simplify',' substitute',' obtain']
protect=['<think>','</think>','<|im_end|>','<|endoftext|>','=','+','-','0','1','2','3','4','5','6','7','8','9']
groups=[tensor(ename,[tok.encode(s).ids[-1] for s in group]) for group in [positive,neutral,protect]]
def reconsider(gain):
    return orth((groups[0].mean(0)-groups[1].mean(0))*gain,(groups[2]*gain).T)
old66=reconsider(nf);new66=reconsider(1+nf)
saved66=torch.load(work/'reconsideration_direction.pt',map_location='cpu',weights_only=True)
h=np.load(work/'fwd_11/hidden_31.npy',mmap_mode='r')
m=json.loads((work/'fwd_11/meta.json').read_text())
sp=[(0,96,49,6),(1,85,47,6)]
def mean(i,a,b):return torch.from_numpy(np.asarray(h[i,a:b],dtype=np.float32)).mean(0)
ds=[mean(i,s+(n-1)*w,s+n*w)-mean(i,s,s+w) for i,s,w,n in sp]
raw=sum(d/d.norm() for d in ds);raw/=raw.norm()
fixed=[mean(i,s,s+w) for i,s,w,n in sp]
for i in [2,3]:
    length=m['lengths'][i]
    fixed += [mean(i,70,length//2),mean(i,length//2,length)]
boundary=tensor(ename,[tok.encode(s).ids[0] for s in ['<think>','</think>','<|im_end|>']])
def final_direction(gain):
    vectors=fixed+list(boundary*gain)
    return orth(raw,torch.stack([v/v.norm() for v in vectors],1))
old87=final_direction(nf);new87=final_direction(1+nf)
saved87=torch.load(work/'attention_loop_direction.pt',map_location='cpu',weights_only=True)
true_boundary=boundary*(1+nf)
cos=lambda a,b:float(torch.dot(a/a.norm(),b/b.norm()))
result={'scope':'static CPU vector algebra only; no inference, edits, or counterfactual performance claim',
 'runtime_norm_formula':'normalize(x) * (1 + norm.weight)',
 'norm_weight_quantiles':torch.quantile(nf,torch.tensor([0.,.25,.5,.75,1.])).tolist(),
 'turn66':{'recomputed_old_vs_saved_cosine':cos(old66,saved66),'correct_formula_vs_saved_cosine':cos(new66,saved66)},
 'turn87':{'recomputed_old_vs_saved_cosine':cos(old87,saved87),'correct_formula_vs_saved_cosine':cos(new87,saved87),
           'saved_cosines_with_true_boundary_readout':[cos(saved87,v) for v in true_boundary],
           'corrected_cosines_with_true_boundary_readout':[cos(new87,v) for v in true_boundary]},
 'runtime_source_sha256':hashlib.sha256(Path('/workspace/acupuncture/.venv-wsp/lib/python3.11/site-packages/transformers/models/qwen3_5/modeling_qwen3_5.py').read_bytes()).hexdigest()}
(out/'norm-formula-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
