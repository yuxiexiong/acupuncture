"""Fixed synthetic interface acceptance. Does not read any benchmark task."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import model_interface as MI

FIXTURES = [
    'Write a Python function fixture_add(x) that returns x + 1. Return one python code block.',
    'Write a Python function fixture_double(x) that returns x * 2. Return one python code block.',
    'Write a Python function fixture_identity(x) that returns x unchanged. Return one python code block.',
    'Write a Python function fixture_zero() that returns 0. Return one python code block.',
]


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--profile',choices=['0p8b','4b'],required=True)
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--gpu',type=int,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    lock=open(MI.FS.EXT/f'engineering-gpu-{a.gpu}.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    row=subprocess.check_output(['nvidia-smi',f'--id={a.gpu}','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True)
    mem,util=map(int,row.strip().split(','));assert mem<128 and util==0,'GPU_BUSY'
    start=time.monotonic()
    receipt=dict(profile=a.profile,scope='synthetic_engineering_only',formal_search_started=False,
                 gpu=a.gpu,generated_samples=0,tf_input_tokens=0,checks=[],generation=[])
    def save():
        receipt['device_seconds']=time.monotonic()-start
        (a.out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    save()
    try:
        import torch
        import numpy as np
        from transformers import AutoTokenizer
        prof=MI.FS.profile(a.profile);tok=AutoTokenizer.from_pretrained(prof['model'],local_files_only=True)
        layer=0;channels=list(range(8))
        MI.validate_gain(prof,layer,channels,0.5)
        reader=MI.FS.Reader(prof['model'],f'cuda:{a.gpu}')
        ids=[tok('def fixture_add(x):\n    return x + 1\n',add_special_tokens=False)['input_ids'],
             tok('A synthetic acceptance string. One plus one equals two.',add_special_tokens=False)['input_ids']]
        module=reader.layers[layer].mlp.down_proj
        def read(gain,compiled):
            cap={}
            def capture(mod,args,out): cap['branch']=out.detach().float().cpu()
            h=module.register_forward_hook(capture)
            try:
                with MI.intervention(reader,layer,channels,gain,compiled):
                    res=reader.run(ids,want_last=True)
                    lps=reader.logprobs(res['last'],ids)
                    lp=torch.cat([x[0][1:] for x in lps])
            finally: h.remove()
            receipt['tf_input_tokens']+=sum(map(len,ids));save()
            return cap['branch'],lp
        base=read(0,False)
        zero=read(0,True)
        assert torch.equal(base[0],zero[0]) and torch.equal(base[1],zero[1])
        receipt['checks'].append(dict(name='zero_identity',passed=True))
        for gain in (-1,-0.5,0.5,1):
            runtime=read(gain,False);compiled=read(gain,True)
            rel=float((runtime[0]-compiled[0]).norm()/runtime[0].norm().clamp_min(1e-6))
            lp=float((runtime[1]-compiled[1]).abs().max())
            receipt['checks'].append(dict(name='runtime_compiled_diagnostic',gain=gain,branch_relative_l2=rel,max_logprob_error=lp,matches_original_equivalence_gate=rel<=.01 and lp<=.05));save()
        w=module.weight.float();x=torch.arange(prof['inter'],device=w.device,dtype=torch.float32)[None,:].sin()
        xx=x.clone();xx[:,channels]*=1.5;ww=w.clone();ww[:,channels]*=1.5
        ref=xx@w.T;got=x@ww.T
        err=float((ref-got).norm()/ref.norm());assert err<1e-5
        receipt['checks'].append(dict(name='fp32_local_equivalence',relative_l2=err,passed=True))
        summary=MI.activation_summary(reader,ids[0],0,len(ids[0]));receipt['tf_input_tokens']+=len(ids[0])
        explicit=reader.run([ids[0]],mlp=[0]);receipt['tf_input_tokens']+=len(ids[0])
        assert torch.allclose(summary[0]['mean'],explicit['cap'][('mlp',0)][0].float().mean(0).cpu())
        assert len(summary)==prof['n_layers'] and all(v['mean'].numel()==prof['inter'] for v in summary.values())
        np.savez(a.out/'activation-summary.npz',**{f'mean_{i}':v['mean'].numpy() for i,v in summary.items()})
        receipt['checks'].append(dict(name='streaming_activation_summary',passed=True))
        del reader,module,w,x,xx,ww,ref,got,explicit,summary;__import__('gc').collect();torch.cuda.empty_cache()
        tasks=[dict(task_id='fixture-'+str(i),user=s) for i,s in enumerate(FIXTURES)]
        items=MI.coding_items(tok,tasks,True,128,2)
        assert MI.coding_items(tok,tasks,False,128,2)[0]['prompt_ids']!=items[0]['prompt_ids']
        (a.out/'items.json').write_text(json.dumps(items)+'\n')
        for name,gain in [('original',0),('zero',0),('minus',-.5),('plus',.5)]:
            built=a.out/name
            checkpoint,build=MI.compile_gain(prof,layer,channels,gain,built)
            if gain:
                from safetensors import safe_open
                with safe_open(str(checkpoint/'model.safetensors'),framework='pt',device='cpu') as edited, safe_open(str(prof['model']/'model.safetensors'),framework='pt',device='cpu') as original:
                    assert set(edited.keys())==set(original.keys())
                    changes=[]
                    for key in original.keys():
                        old=original.get_tensor(key);new=edited.get_tensor(key)
                        if key.endswith(f'layers.{layer}.mlp.down_proj.weight'):
                            expected=old.float();expected[:,channels]*=1+gain
                            assert torch.equal(new,expected.to(old.dtype)),'gain serialization differs'
                            changes.append(key)
                        else: assert torch.equal(old,new),'unrequested weight changed: '+key
                receipt['checks'].append(dict(name='all_tensor_identity_and_gain_roundtrip',arm=name,changed_tensors=changes,passed=True));save()
            output=built/'generation.jsonl'
            command=[sys.executable,str(Path(MI.__file__)), '--worker','--ckpt',str(checkpoint),
                     '--items',str(a.out/'items.json'),'--out',str(output),'--max-len','512','--eager']
            remaining=(1800 if a.profile=='0p8b' else 3600)-(time.monotonic()-start)
            assert remaining>0,'engineering device budget exhausted'
            with (built/'engine.log').open('w') as log:
                p=subprocess.Popen(command,env=dict(os.environ,CUDA_VISIBLE_DEVICES=str(a.gpu)),stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                try: p.wait(timeout=remaining)
                finally:
                    if p.poll() is None: os.killpg(p.pid,signal.SIGKILL);p.wait()
            assert p.returncode==0,'generation worker failed: '+name
            rows=[json.loads(l) for l in output.read_text().splitlines()]
            assert len(rows)==8 and all(len(r['token_ids'])<=128 for r in rows)
            receipt['generated_samples']+=len(rows)
            done=json.loads(Path(str(output)+'.done').read_text())
            receipt['generation'].append(dict(arm=name,**done));save()
            if name=='original': reference=rows
            if name=='zero': assert rows==reference,'zero needle generation differs'
            # Only disposable full copies; edits, snapshots, hashes and build records stay.
            if (built/'checkpoint-cache').exists(): shutil.rmtree(built/'checkpoint-cache')
        receipt['checks'].append(dict(name='paired_vllm_gain_generation',passed=True))
        receipt['status']='passed'
    except BaseException as exc:
        receipt['status']='failed';receipt['error']=type(exc).__name__+': '+str(exc);raise
    finally: save()
    print(json.dumps(receipt))


if __name__=='__main__': main()
