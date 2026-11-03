"""WCP task adapter and restricted column-gain operations; reuse WSP engine."""
import argparse
import contextlib
import json
import os
from pathlib import Path
import sys

ENGINE = Path(os.environ.get('WCP_WSP_ENGINE', '/workspace/acupuncture/external/wsp/code-engineering-r2/engineering-r2'))
sys.path.insert(0, str(ENGINE)); sys.path.insert(0,str(ENGINE.parent))
import forward_service as FS

SAMPLING = dict(temperature=0.6, top_p=0.95, top_k=20, presence_penalty=0.0)


def validate_gain(prof, layer, channels, gain):
    if type(layer) is not int or not 0<=layer<prof['n_layers']:
        raise ValueError('invalid layer')
    if len(channels) not in (8,32) or len(set(channels))!=len(channels):
        raise ValueError('gain requires 8 or 32 unique channels')
    if not all(type(i) is int and 0<=i<prof['inter'] for i in channels):
        raise ValueError('invalid channel')
    if type(gain) not in (int,float) or not -1<=gain<=1:
        raise ValueError('gain outside [-1,1]')


@contextlib.contextmanager
def intervention(reader, layer, channels, gain, compiled=False):
    import torch
    module=reader.layers[layer].mlp.down_proj
    original=module.weight.detach().clone() if compiled else None
    handle=None
    try:
        if gain:
            if compiled:
                # float32 transform then BF16, exactly as checkpoint builder.
                new=module.weight.detach().float().clone()
                new[:,channels]*=1+gain
                module.weight.copy_(new.to(module.weight.dtype))
            else:
                def hook(mod,args):
                    x=args[0].clone(); x[...,channels]*=1+gain
                    return (x,)+args[1:]
                handle=module.register_forward_pre_hook(hook)
        yield
    finally:
        if handle is not None: handle.remove()
        if original is not None: module.weight.copy_(original)


def activation_summary(reader, ids, start, end):
    """One exact full-prefix replay; only requested window aggregates leave GPU."""
    if not 0<=start<end<=len(ids): raise ValueError('invalid activation window')
    results={}; handles=[]
    for i,layer in enumerate(reader.layers):
        def hook(mod,args,i=i):
            x=args[0][0,start:end].float()
            results[i]={'mean':x.mean(0).cpu(), 'rms':x.square().mean(0).sqrt().cpu(), 'tokens':end-start}
        handles.append(layer.mlp.down_proj.register_forward_pre_hook(hook))
    try: reader.run([ids])
    finally:
        for h in handles: h.remove()
    return results


def compile_gain(prof, layer, channels, gain, destination):
    import numpy as np
    from safetensors import safe_open
    from snapshot_edits import snapshot
    validate_gain(prof,layer,channels,gain)
    destination=Path(destination); destination.mkdir(parents=True,exist_ok=False)
    if gain==0:
        (destination/'identity.json').write_text(json.dumps({'gain':0,'model':str(prof['model'])})+'\n')
        return prof['model'], {'identity':'zero_gain','unchanged':True}
    with safe_open(str(prof['model']/'model.safetensors'),framework='pt',device='cpu') as f:
        name=next(n for n in f.keys() if n.endswith(f'layers.{layer}.mlp.down_proj.weight'))
        old=f.get_tensor(name).float(); new=old.clone(); new[:,channels]*=1+gain
    mask=__import__('torch').ones(new.shape[1],dtype=__import__('torch').bool); mask[channels]=False
    assert __import__('torch').equal(new[:,mask],old[:,mask])
    edits=destination/'edited'; edits.mkdir()
    np.save(edits/(name+'.npy'),new.numpy(),allow_pickle=False)
    manifest=snapshot(prof['model'],edits,destination/'snapshot')
    assert len(manifest['tensors'])==1
    path,build=FS.build_checkpoint(prof,destination/'snapshot',cache=destination/'checkpoint-cache')
    (destination/'build-record.json').write_text(json.dumps(build,indent=2)+'\n')
    (destination/'gain.json').write_text(json.dumps(dict(layer=layer,channels=channels,gain=gain,tensor=name))+'\n')
    return path,build


def coding_items(tok, tasks, thinking, max_tokens=16384, n=2):
    if not 1<=max_tokens<=16384 or n not in (1,2): raise ValueError('invalid generation budget')
    items=[]
    for task in tasks:
        key=str(task['task_id'])
        rendered=tok.apply_chat_template([{'role':'user','content':task['user']}],
            tokenize=False,add_generation_prompt=True,enable_thinking=thinking)
        items.append(dict(key=key,prompt_ids=tok(rendered,add_special_tokens=False)['input_ids'],
                          seed=FS.item_seed('wcp01:'+key),max_tokens=max_tokens,n=n))
    return items


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--worker',action='store_true');ap.add_argument('--ckpt');ap.add_argument('--items');ap.add_argument('--out')
    ap.add_argument('--max-len',type=int);ap.add_argument('--max-seqs',type=int,default=32)
    ap.add_argument('--mem',type=float,default=0.75);ap.add_argument('--eager',action='store_true')
    a=ap.parse_args()
    if not a.worker: raise SystemExit('FORMAL_SEARCH_DISABLED: engineering worker only')
    FS.SAMPLING=SAMPLING
    FS.vllm_worker(a)
