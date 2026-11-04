"""Bounded synthetic end-to-end interface acceptance; never run formal search."""
import argparse
import json
from pathlib import Path
import time
import numpy as np
from broker import Broker, stop, write_json
import forward_service as FS


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config',required=True); ap.add_argument('--retry-suffix')
    a=ap.parse_args(); cfg=json.loads(Path(a.config).read_text())
    b=Broker(cfg); prof=b.prof; root=b.root; L=prof['n_layers']; rows=[]
    def call(ident,kind,**kw):
        previous=root/'actions'/ident/'response.json'
        if a.retry_suffix and previous.exists() and json.loads(previous.read_text())['failed']:
            ident+='-'+a.retry_suffix
        result=b.dispatch(dict(id=ident,kind=kind,**kw)); rows.append(result)
        write_json(root/'acceptance.progress.json',rows)
        assert not result['failed'],result
        return result
    start=time.time()
    try:
        call('cpu-init','python',code="import os, torch\nassert not torch.cuda.is_available()\nassert not os.path.exists('/root/.ssh')\nassert not os.path.exists('/workspace/acupuncture/external/wsp/observer-upstream')\nprobe_value=41\n'ISOLATION_OK'")
        call('cpu-resume','python',code="assert probe_value+1==42\nassert tok.encode('2 + 2').ids and tok.encode('2 + 2').offsets\n'PERSISTENCE_OK'")
        req={'type':'teacher_forced','model':'original','texts':['2 + 2 = 4','One plus one equals two.'],
             'return':{'token_logprobs':True,'topk':3,'hidden_states':[0,1,L],'mlp_act':[0], 'attn_layers':[prof['full_attn'][-1]]}}
        call('tf-original','forward',request=req)
        d=b.work/'fwd_1'; meta=json.loads((d/'meta.json').read_text()); T=meta['padded_length']
        assert np.load(d/'token_logprobs.npy').shape==(2,T-1)
        for l in [0,1,L]:
            arr=np.load(d/f'hidden_{l}.npy'); assert arr.dtype==np.float16 and arr.shape==(2,T,prof['hidden'])
            assert np.isfinite(arr).all()
        assert np.load(d/'mlp_act_0.npy').dtype==np.float16
        att=np.load(d/f'attn_{prof["full_attn"][-1]}.npy')
        for i,n in enumerate(meta['lengths']):
            assert np.isfinite(np.load(d/'token_logprobs.npy')[i,:n-1]).all()
            assert np.max(np.abs(np.triu(att[i,:,:n,:n],k=1)))==0
            # BF16 softmax probabilities: per-value rounding relative error <= 2^-8.
            # Subsequent FP16 storage adds <= 2^-11 plus subnormal absolute rounding.
            rounding_bound=2**-8 + 2**-11 + n*2**-25
            assert np.max(np.abs(att[i,:,:n,:n].astype('float32').sum(-1)-1))<=rounding_bound
        # Tiny up-projection edit tests loading only; never reuses the author's final output-column patch.
        call('synthetic-edit','python',code="name=next(n for n in NAMES if n.endswith('layers.0.mlp.up_proj.weight'))\na=load_original(name)\na[0,0]+=1\nsave_edit(name,a)\nname")
        req['model']='edited'; req['return']={'token_logprobs':True,'hidden_states':[1]}
        call('tf-edited','forward',request=req)
        build=json.loads((root/'actions/tf-edited/pass_2.result.json').read_text())['builds']['edited']
        assert list(build['changed_values'].values())==[1]
        call('gen-both','forward',request={'type':'generate','model':'both','prompts':['What is 2 + 2?'],
             'n':2,'max_tokens':16,'activations':{'layers':[0,L],'mlp':True}})
        for arm in ['original','edited']:
            lines=[json.loads(x) for x in (b.work/f'gen_3_{arm}.jsonl').read_text().splitlines()]
            assert len(lines)==1 and len(lines[0]['samples'])==2
            d=b.work/'gen_3_acts'/arm; index=json.loads((d/'index.json').read_text())
            assert index['mlp_layers']==[0] and index['layers']==[0,L]
            assert np.load(d/'hidden_last_prompt.npy').shape==(2,2,prof['hidden'])
            assert np.load(d/'mlp_last_prompt.npy').shape==(2,1,prof['inter'])
        before=dict(b.state)
        invalid=b.dispatch({'id':'invalid','kind':'forward','request':{'type':'generate','model':'bad'}})
        assert invalid['failed'] and b.state==before
        cached=b.dispatch({'id':'invalid','kind':'forward','request':{'type':'generate','model':'bad'}})
        assert cached==invalid and b.state==before
        call('clear-test-edit','python',code="drop_edit('model.language_model.layers.0.mlp.up_proj.weight')\nassert edited()==[]\n'EDIT_CLEARED'")
        receipt={'status':'passed','profile':cfg['profile'],'seconds':time.time()-start,'state':b.state,
                 'checks':['sandbox','persistent CPU','TF shapes/dtypes','attention index and mask','snapshot loaded one changed value',
                           'grouped generation n=2','requested-only MLP activations','failure budget','idempotent response','synthetic edit cleared'],
                 'source_sha256':{p.name:FS.sha256_file(p) for p in Path(__file__).parent.glob('*.py') if not p.name.startswith('.')},
                 'formal_search_started':False}
        write_json(root/'receipt.json',receipt); print(json.dumps(receipt),flush=True)
    finally: stop(b.kernel)


if __name__=='__main__': main()
