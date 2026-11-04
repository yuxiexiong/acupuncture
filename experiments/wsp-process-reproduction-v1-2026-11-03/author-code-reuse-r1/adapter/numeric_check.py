"""Independent standard HF forward versus saved short interface outputs. No search."""
import json
from pathlib import Path
import sys
import time
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import forward_service as F

root=Path(sys.argv[1]); started=time.monotonic()
assert not (root/'numeric-receipt.json').exists()
torch.set_grad_enabled(False)
prof=F.profile('0p8b'); base=prof['model']; L=prof['n_layers']
tok=AutoTokenizer.from_pretrained(base,local_files_only=True)
d=root/'work/fwd_1'; meta=json.loads((d/'meta.json').read_text())
inputs=np.load(d/'input_ids.npy')
model=AutoModelForCausalLM.from_pretrained(base,dtype=torch.bfloat16,attn_implementation='eager',local_files_only=True).cuda().eval()
errors=[]
for i,n in enumerate(meta['lengths']):
    x=torch.tensor(inputs[i:i+1,:n],device='cuda')
    captured={}
    def mlp_input(module,args):
        captured['input']=args[0].clone()
    handle=model.model.layers[0].mlp.register_forward_pre_hook(mlp_input)
    try:
        out=model(input_ids=x,attention_mask=torch.ones_like(x),output_hidden_states=True,use_cache=False)
    finally:
        handle.remove()
    for l in (0,1,L):
        ref=out.hidden_states[l][0].float().cpu().numpy().astype(np.float16)
        saved=np.load(d/f'hidden_{l}.npy')[i,:n]
        assert np.array_equal(saved,ref),('hidden',i,l,float(np.max(np.abs(saved-ref))))
    mlp=model.model.layers[0].mlp
    h=captured['input']
    ref=(mlp.act_fn(mlp.gate_proj(h))*mlp.up_proj(h))[0].float().cpu().numpy().astype(np.float16)
    saved=np.load(d/'mlp_act_0.npy')[i,:n]
    assert np.array_equal(saved,ref),('mlp',i)
    lp=out.logits[0,:n-1].float().log_softmax(-1).gather(1,x[0,1:,None])[:,0].cpu().numpy()
    error=float(np.max(np.abs(lp-np.load(d/'token_logprobs.npy')[i,:n-1])))
    assert error<=1e-5,('logprob',i,error)
    errors.append(error)
    again=model(input_ids=x,attention_mask=torch.ones_like(x),use_cache=False)
    assert torch.equal(out.logits,again.logits),'empty-edit repeat mismatch'
    for l in (0,1,L):
        assert np.all(np.load(d/f'hidden_{l}.npy')[i,n:]==0)
    assert np.isnan(np.load(d/'token_logprobs.npy')[i,n-1:]).all()
receipt={'status':'passed','reference':'standard AutoModelForCausalLM.forward with output_hidden_states; MLP explicitly recomputed from gate/up on captured input',
         'hidden_fp16_exact':True,'mlp_fp16_exact':True,'logprob_max_abs_errors':errors,
         'same_weights_repeat_logits_exact':True,'right_padding_valid':True,'gpu_slots':1,
         'gpu_seconds':time.monotonic()-started,'formal_started':False}
(root/'numeric-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
