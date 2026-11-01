"""Read existing bridge/combo artifacts only. No model import, forward, or CUDA.
Run on the archive host with CUDA_VISIBLE_DEVICES='' and redirect stdout locally.
"""
import hashlib
import json
import os
from pathlib import Path
import time

assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import torch
torch.set_num_threads(2)

ROOT = Path('/workspace/acupuncture/experiments')
BR = ROOT / 'cache-formation-readout-bridge-v1-2026-10-31'
CO = ROOT / 'cache-formation-cache-combination-v1-2026-10-31'


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def norm(x):
    return float(x.double().norm())


def interaction(xs):
    a, s, f, sf = xs
    return sf.double() - s.double() - f.double() + a.double()


def read(s, w):
    return torch.einsum('hiv,hi->hv', s.double(), w.double())


def weight(r):
    q, k = r['q'].double(), r['k'].double()
    q = q * torch.rsqrt(q.square().sum(-1, keepdim=True) + 1e-6) / q.shape[-1] ** .5
    k = k * torch.rsqrt(k.square().sum(-1, keepdim=True) + 1e-6)
    kq = (k*q).sum(-1)
    w = r['g'].double().exp()[:, None] * (q - r['beta'].double()[:, None]*k*kq[:, None])
    new = r['beta'].double()[:, None]*r['v'].double()*kq[:, None]
    return w, new


def self_check():
    # Exact four-corner algebra with independently changing drivers, no RNG.
    sa = torch.arange(12, dtype=torch.float64).reshape(1, 3, 4)
    sb = sa.flip(-1) + 2
    w = [torch.tensor([[a, b, c]], dtype=torch.float64) for a,b,c in [(1,2,3),(2,0,4),(3,2,0),(2,4,1)]]
    lhs = interaction([read(sa,w[0]),read(sb,w[1]),read(sa,w[2]),read(sb,w[3])])
    rhs = read(sb-sa,w[2]-w[0]) + read(sb,(w[3]-w[2])-(w[1]-w[0]))
    assert torch.equal(lhs, rhs)
    assert interaction([torch.tensor(x) for x in (0.,1.,2.,3.)]) == 0


def main():
    self_check()
    start = time.time()
    result = {'scope':'existing tensors, CPU only; descriptive decomposition, not causal mediation',
              'script_sha256':sha(Path(__file__)) if Path(__file__).is_file() else None,
              'sources':[], 'items':{}, 'model_calls':0, 'gpu_calls':0, 'self_check':'passed'}
    result['code_receipt_hashes']={str(p):sha(p) for base in (BR,CO) for p in [
        base/('bridge.py' if base==BR else 'combo.py'),base/'freeze-r01.json',
        base/'runs/formal-r01/worker-0/receipt.json',base/'runs/formal-r01/worker-1/receipt.json']}
    for worker in (0,1):
        bd = BR / f'runs/formal-r01/worker-{worker}'
        cd = CO / f'runs/formal-r01/worker-{worker}'
        br, cr = [json.loads((d/'receipt.json').read_text()) for d in (bd,cd)]
        for rel in sorted(cr['record_hashes']):
            item = Path(rel).stem
            paths = [bd/rel,cd/rel,bd/'tensors'/f'{item}.pt',cd/'tensors'/f'{item}.pt']
            expected = [br['record_hashes'][rel],cr['record_hashes'][rel],
                        br['tensor_hashes'][f'tensors/{item}.pt'],cr['tensor_hashes'][f'tensors/{item}.pt']]
            for p, h in zip(paths, expected):
                actual=sha(p)
                assert actual == h, str(p)
                result['sources'].append({'path':str(p),'bytes':p.stat().st_size,'sha256':actual,'receipt_match':True})
            rb, rc = [json.loads(p.read_text()) for p in paths[:2]]
            tb, tc = [torch.load(p,map_location='cpu',weights_only=True) for p in paths[2:]]
            assert rb['prompt_token_sha256'] == rc['prompt_token_sha256']
            endpoint_map={'C':'C','T':'Y_T','CT':'Y_CT','TC':'Y_TC'}
            for x, key in endpoint_map.items():
                # Use pair metadata rather than guessing cell-name conventions.
                cell=rc['pairs']['C|T']['0'] if x=='C' else rc['pairs']['C|CT']['SFK'] if x=='CT' else rc['pairs']['TC|T']['0'] if x=='TC' else rc['pairs']['C|T']['SFK']
                assert torch.equal(tc['logits'][cell],tb['logits'][key])
            out={'scores_bridge':rb['scores'],'scores_combo':rc['scores'],'pairs':rc['pairs'],
                 'gates_bridge':rb['gates'],'gates_combo':rc['gates'],'layers':{},'checks':{'endpoint_tensor_replay':True}}
            for pname, pm in rc['pairs'].items():
                a,b=pname.split('|')
                for kbg, masks in [('base',('0','S','F','SF')),('donor',('K','SK','FK','SFK'))]:
                    cells=[pm[m] for m in masks]
                    ls={}
                    for layer in rb['G']:
                        rs=[tc['score_drivers'][c][layer] for c in cells]
                        ws, ns=zip(*(weight(r) for r in rs))
                        sa=tb['deep'][a][f'{layer}:recurrent_states'][0].double()
                        sb=tb['deep'][b][f'{layer}:recurrent_states'][0].double()
                        states=[sa,sb,sa,sb]
                        old=[read(s,w) for s,w in zip(states,ws)]
                        core=[r['core'].double() for r in rs]
                        oldi,newi,corei=interaction(old),interaction(ns),interaction(core)
                        direct=read(sb-sa,ws[2]-ws[0])
                        upstream=read(sb,(ws[3]-ws[2])-(ws[1]-ws[0]))
                        extras=[tc['score_extras'][c] for c in cells]
                        ins=[x[f'{layer}:in'] for x in extras]
                        outs=[x[f'{layer}:out'] for x in extras]
                        ls[str(layer)]={
                            'old_I_norm':norm(oldi),'new_I_norm':norm(newi),'core_I_norm':norm(corei),
                            'core_SF_minus_0_norm':norm(core[3]-core[0]),
                            'core_I_over_SF_change':norm(corei)/max(norm(core[3]-core[0]),1e-30),
                            'direct_old_x_read_norm':norm(direct),'upstream_driver_term_norm':norm(upstream),
                            'old_algebra_residual':norm(oldi-direct-upstream),
                            'old_record_max_abs_error':max(float((o-r['old'].double()).abs().max()) for o,r in zip(old,rs)),
                            'new_record_max_abs_error':max(float((n-r['new'].double()).abs().max()) for n,r in zip(ns,rs)),
                            'core_reconstruction_max_relative_error':max(norm(o+n-c)/max(norm(c),1e-30) for o,n,c in zip(old,ns,core)),
                            'core_I_reconstruction_error':norm(corei-oldi-newi),
                            'input_I_norm':norm(interaction(ins)),'output_I_norm':norm(interaction(outs)),
                            'input_S_minus_0_norm':norm(ins[1].float()-ins[0].float()),
                            'input_SF_minus_F_norm':norm(ins[3].float()-ins[2].float()),
                        }
                    zs=[tc['logits'][c].double() for c in cells]
                    fixed_tokens=sorted(set(rc['token_set']))
                    # Freeze token pair at base-cell winners to avoid max changing identity.
                    e=rc['scores'][cells[0]]['stop_winner']; n=rc['scores'][cells[0]]['nonstop_winner']
                    out['layers'][pname+'|K_'+kbg]={'G':ls,'logit_I_norm':norm(interaction(zs)),
                        'D_I':sum(sign*rc['scores'][c]['stop_advantage'] for sign,c in zip((1,-1,-1,1),cells)),
                        'base_winner_pair':[e,n], 'fixed_pair_I':float(interaction(zs)[e]-interaction(zs)[n]),
                        'all_frozen_token_I':{str(t):float(interaction(zs)[t]) for t in fixed_tokens}}
            result['items'][item]=out
            del tb,tc
    assert len(result['items'])==12
    result['seconds']=time.time()-start
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
