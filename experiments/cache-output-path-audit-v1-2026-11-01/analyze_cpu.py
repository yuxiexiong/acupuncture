"""Archived residual accounting only: no model imports, forwards, or CUDA."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time

assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import torch
from safetensors import safe_open
torch.set_num_threads(2)

ROOT = Path('/workspace/acupuncture')
MODEL = Path('/data/models/Qwen3.5-4B-851bf6e')
BR = 'experiments/cache-formation-readout-bridge-v1-2026-10-31'
LR = 'experiments/cache-local-readout-causal-v1-2026-11-01'
STOPS = [248044, 248046]


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(8*1024*1024), b''):
            h.update(b)
    return h.hexdigest()


def norm(x):
    return float(x.double().norm())


def value(x, w):
    return float(x.double() @ w)


def score(z):
    non = z.clone()
    non[STOPS] = -float('inf')
    e, n = STOPS[int(z[STOPS].argmax())], int(non.argmax())
    return {'D': float(z[e]-z[n]), 'stop': e, 'nonstop': n,
            'stop_logit':float(z[e]),'nonstop_logit':float(z[n]),
            'eos': int(z.argmax()) in STOPS}


def components(ex):
    parts = {'entry': ex['13:in'].double()}
    for l in range(13, 32):
        if l > 13:
            assert torch.equal(ex[f'{l}:in'], ex[f'{l-1}:out'])
        parts[str(l)] = ex[f'{l}:out'].double()-ex[f'{l}:in'].double()
    assert torch.equal(ex['31:out'], ex['final:h'])
    assert torch.equal(sum(parts.values()), ex['final:h'].double())
    return parts


def compare(a, b, za, zb, parts_a, parts_b, rows, rfix, eps):
    """b-a in a fixed pair, with exact scale/rounding/winner accounting."""
    ha, hb = a.double(), b.double()
    ra = float((ha.square().mean()+eps).sqrt())
    rb = float((hb.square().mean()+eps).sqrt())
    e, n, we, wn = rows
    w = we-wn
    fixed = value(hb-ha, w)/rfix
    own = value(hb, w)/rb-value(ha, w)/ra
    observed_pair = float(zb[e]-zb[n]-za[e]+za[n])
    dynamic = score(zb)['D']-score(za)['D']
    per_part = {k: {'stop': value(parts_b[k]-parts_a[k], we)/rfix,
                    'nonstop': value(parts_b[k]-parts_a[k], wn)/rfix,
                    'pair': value(parts_b[k]-parts_a[k], w)/rfix}
                for k in parts_a}
    closure = sum(v['pair'] for v in per_part.values())-fixed
    assert abs(closure) < 1e-9, closure
    out = {'fixed_pair': [e,n], 'r_fixed': rfix, 'r_a':ra, 'r_b':rb,
           'fixed_residual':fixed, 'scale':own-fixed,
           'rounding':observed_pair-own, 'winner':dynamic-observed_pair,
           'D_delta':dynamic, 'pair_delta_observed':observed_pair,
           'pair_delta_fp64':own, 'parts':per_part, 'closure_error':closure}
    sa,sb=score(za),score(zb)
    out['winner_stop']=float((zb[sb['stop']]-zb[e])-(za[sa['stop']]-za[e]))
    out['winner_nonstop']=float((zb[sb['nonstop']]-zb[n])-(za[sa['nonstop']]-za[n]))
    out['fixed_stop_change_observed']=float(zb[e]-za[e])
    out['fixed_nonstop_change_observed']=float(zb[n]-za[n])
    assert abs(out['winner_stop']-out['winner_nonstop']-out['winner'])<1e-9
    assert abs(sum(out[k] for k in ('fixed_residual','scale','rounding','winner'))-dynamic)<1e-9
    return out


def self_check():
    # Independent endpoint and telescoping examples, including a changed winner.
    x = torch.arange(6,dtype=torch.float64)
    p = {'entry':x, 'a':x.flip(0)-x, 'b':2*x-x.flip(0)}
    assert torch.equal(sum(p.values()),2*x)
    # Dynamic max can change while a fixed-pair delta stays positive.
    z0, z1 = [torch.tensor(v,dtype=torch.float64) for v in ([2.,1.,0.],[4.,2.,3.])]
    assert float((z1[0]-z1[1])-(z0[0]-z0[1])) == 1
    assert float((z1[0]-z1[1:].max())-(z0[0]-z0[1:].max())) == 0


def main():
    self_check()
    started=time.time()
    manifest=json.loads(Path(sys.argv[1]).read_text())
    result={'scope':'exploratory archived CPU accounting; not causal path shares',
            'source_commit':manifest['source_commit'], 'script_sha256':sha(Path(__file__)),
            'model_calls':0,'gpu_calls':0,'sources':[], 'items':{}, 'checks':{}}
    for rel,digest in manifest['receipts'].items():
        assert sha(ROOT/rel)==digest,rel
    index_path=MODEL/'model.safetensors.index.json'
    index=json.loads(index_path.read_text())['weight_map']
    cfg=json.loads((MODEL/'config.json').read_text())
    textcfg=cfg.get('text_config',cfg)
    assert textcfg.get('tie_word_embeddings',cfg.get('tie_word_embeddings')) is True
    normkey='model.language_model.norm.weight'
    headkey='model.language_model.embed_tokens.weight'
    with safe_open(MODEL/index[normkey],framework='pt',device='cpu') as f:
        gain=1+f.get_tensor(normkey).double()
    eps=textcfg['rms_norm_eps']
    weights={}
    def weight(t):
        if t not in weights:
            with safe_open(MODEL/index[headkey],framework='pt',device='cpu') as f:
                weights[t]=f.get_slice(headkey)[t:t+1].reshape(-1).double()*gain
        return weights[t]
    result['weight_sources']=[{'path':str(MODEL/n),'sha256':sha(MODEL/n)} for n in sorted(set([index[normkey],index[headkey],'config.json','model.safetensors.index.json']))]
    result['weight_semantics']={'tied_head':headkey,'norm':normkey,'gain':'1+weight','eps':eps}
    selected=['C','T_native','Y_T','Y_CT','Y_TC']
    contrasts=[('C','T_native'),('Y_T','T_native'),('C','Y_T'),('C','Y_CT'),('Y_TC','Y_T'),('Y_CT','Y_T')]
    fp64_errors=[]
    for unit in manifest['units']:
        tensors,records={},{}
        for tag in ('bridge','local'):
            spec=unit[tag]
            for field in ('record','tensor'):
                p=ROOT/spec[field]
                actual=sha(p)
                assert actual==spec[field+'_sha256'],str(p)
                result['sources'].append({'path':str(p),'sha256':actual,'bytes':p.stat().st_size})
            records[tag]=json.loads((ROOT/spec['record']).read_text())
            tensors[tag]=torch.load(ROOT/spec['tensor'],map_location='cpu',weights_only=True)
        br,lr=records['bridge'],records['local']
        tb,tl=tensors['bridge'],tensors['local']
        assert br['prompt_token_sha256']==lr['prompt_token_sha256']
        for a,b in [('Y_T','M:R'),('T_native','N:R')]:
            assert torch.equal(tb['logits'][a],tl['logits'][b])
            assert torch.equal(tb['score_extras'][a]['final:h'],tl['final_h'][b])
        ex=tb['score_extras']; zs=tb['logits']
        scores={k:score(zs[k].double()) for k in selected}
        for k in selected:
            assert scores[k]['D']==br['scores'][k]['stop_advantage']
            h=ex[k]['final:h'].double(); r=float((h.square().mean()+eps).sqrt())
            for t,z in br['scores'][k]['token_logits_fp64'].items():
                err=abs(value(h,weight(int(t)))/r-z)
                fp64_errors.append(err)
                assert err<1e-8, (k,t,err)
        rfix=float((ex['C']['final:h'].double().square().mean()+eps).sqrt())
        parts={k:components(ex[k]) for k in selected}
        out={'scores':scores,'contrasts':{},'deletion':{},'scenario':br['item']['scenario'] if 'scenario' in br['item'] else unit['id'].split('-')[0]}
        for anchor in ('T_native','C'):
            e,n=scores[anchor]['stop'],scores[anchor]['nonstop']
            rows=(e,n,weight(e),weight(n))
            out['contrasts'][anchor]={a+'->'+b:compare(ex[a]['final:h'],ex[b]['final:h'],zs[a].double(),zs[b].double(),parts[a],parts[b],rows,rfix,eps) for a,b in contrasts}
            for a,b in contrasts:
                d=out['contrasts'][anchor][a+'->'+b]
                d['full_attention_parts']={}
                for l in (15,19,23,27,31):
                    dv=ex[b][f'{l}:attn_out'].double()-ex[a][f'{l}:attn_out'].double()
                    attn=value(dv,rows[2]-rows[3])/rfix
                    d['full_attention_parts'][str(l)]={'attention':attn,
                        'block_remainder':d['parts'][str(l)]['pair']-attn}
        for bg in ('M','N'):
            ref=bg+':R'; sr=score(tl['logits'][ref].double())
            e,n=sr['stop'],sr['nonstop']; rows=(e,n,weight(e),weight(n))
            h=tl['final_h'][ref]; r=float((h.double().square().mean()+eps).sqrt())
            for c in ('mI','mJ','Q0','Q1'):
                key=bg+':'+c
                pa={'layer13':tl['decoder13_out'][ref].double(), 'later':tl['final_h'][ref].double()-tl['decoder13_out'][ref].double()}
                pb={'layer13':tl['decoder13_out'][key].double(), 'later':tl['final_h'][key].double()-tl['decoder13_out'][key].double()}
                d=compare(tl['final_h'][ref],tl['final_h'][key],tl['logits'][ref].double(),tl['logits'][key].double(),pa,pb,rows,r,eps)
                d['stages']={}
                for label,a,b in [('gated_norm',tl['extras13'][ref]['13:gated_norm_out'],tl['extras13'][key]['13:gated_norm_out']),('out_proj',tl['extras13'][ref]['13:out_proj'],tl['extras13'][key]['13:out_proj']),('decoder13',tl['decoder13_out'][ref],tl['decoder13_out'][key]),('final',h,tl['final_h'][key])]:
                    dv=b.double()-a.double()
                    d['stages'][label]={'delta_norm':norm(dv)}
                    if label!='gated_norm':
                        d['stages'][label]['fixed_pair_projection']=value(dv,rows[2]-rows[3])/r
                d['intended_delta_norm']=norm(tl['deltas'][bg][c])
                out['deletion'][key]=d
        result['items'][unit['id']]=out
        del tb,tl,tensors
    assert len(result['items'])==12
    result['checks']={'all_sources_match':True,'all_residual_telescopes_exact':True,
                      'reference_endpoints_bitwise_match':True,'fp64_record_max_abs_error':max(fp64_errors),
                      'fp64_values_checked':len(fp64_errors),'synthetic_self_check':'passed'}
    result['missing']=['native entry x_T + clean deep cache scoring cell',
                       'layers 14..31 intermediate residuals under local deletion',
                       'native shallow layers 0..12 residuals',
                       'comparable cross-direction held-out prediction test']
    vocab=json.loads((MODEL/'tokenizer.json').read_text())
    ids={v:k for k,v in vocab['model']['vocab'].items()}
    ids.update({v['id']:v['content'] for v in vocab.get('added_tokens',[])})
    seen={t for item in result['items'].values() for s in item['scores'].values() for t in (s['stop'],s['nonstop'])}
    result['token_labels']={str(t):ids.get(t) for t in sorted(seen)}
    result['seconds']=time.time()-started
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
