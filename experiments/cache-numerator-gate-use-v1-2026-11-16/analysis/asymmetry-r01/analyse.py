"""CPU-only geometry of already recorded NGU/RCS activations; never instantiate a model."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time

os.environ['CUDA_VISIBLE_DEVICES'] = ''
HERE = Path(__file__).resolve().parent
NGU = HERE.parents[1]
RCS = HERE.parents[2]/'cache-readout-content-scale-v1-2026-11-15'
sys.path.insert(0, str(RCS/'analysis/background-response-r01'))
import analyse_saved as A


def norm(x):
    return float(x.double().norm())


def cosine(a, b):
    return A.ratio(float((a.double()*b.double()).sum()), norm(a)*norm(b))


def endpoint(x, z, inv, weight):
    import torch
    out = weight*(x.float()*inv.float()).to(x.dtype)
    return (out*torch.nn.functional.silu(z.float())).to(x.dtype)


def local(c, h, cx, hx, weight):
    import torch
    nd = lambda t: t.reshape(32, 128).double()
    ng = lambda t: torch.nn.functional.silu(t.float()).reshape(32,128).double()
    t, x = {'C':c,'H':h}, {'C':cx,'H':hx}
    d = {b:nd(v['x1'])-nd(v['x0']) for b,v in t.items()}
    inv = {b:v['inv_r1'].reshape(32,1).double() for b,v in t.items()}
    gates = {b:v['z'].reshape(32,128) for b,v in t.items()}
    gd = ng(gates['H'])-ng(gates['C'])
    w = weight.double()
    row, vectors = {'gate_difference_norm':norm(gd), 'd_HC_cos':cosine(d['H'],d['C'])}, {}
    for b in ('C','H'):
        v, xx = t[b], x[b]
        dn = norm(d[b]); row[b+'_d'] = dn
        row[b+'_raw_d'] = norm(v['raw1'].double()-v['raw0'].double())
        ideal = w*inv[b]*gd*d[b]
        f = {g:[endpoint(v[k].reshape(32,128),gates[g],inv[b],weight).double()
                for k in ('x0','x1')] for g in ('C','H')}
        finite = (f['H'][1]-f['H'][0])-(f['C'][1]-f['C'][0])
        # H removal is sign-aligned to C addition for the shared H-minus-C gate difference.
        sign = 1 if b == 'C' else -1
        direct = sign*(nd(xx['patch'])-nd(xx['native']))
        requested = sign*(nd(xx['delta_ref'])-nd(xx['delta_cur']))
        inherited = sign*(nd(xx['native'])-nd(v['native_norm']))
        total = sign*(nd(xx['patch'])-nd(v['native_norm']))
        assert torch.allclose(total, direct+inherited, atol=1e-12, rtol=1e-12)
        for key,value in {'ideal':ideal,'finite':finite,'direct':direct,'inherited':inherited}.items():
            row[b+'_'+key] = norm(value)
            vectors[b+'_'+key] = value.reshape(-1)
        row.update({b+'_total':norm(total), b+'_requested':norm(requested),
                    b+'_rounding_relative':A.ratio(norm(direct-requested),norm(requested)),
                    b+'_ideal_finite_relative':A.ratio(norm(finite-ideal),norm(finite)),
                    b+'_direct_fixed_relative':A.ratio(norm(direct-finite),norm(finite)),
                    b+'_direct_fixed_cos':cosine(direct,finite),
                    b+'_inherited_direct_cos':cosine(inherited,direct),
                    b+'_cancellation_ratio':A.ratio(norm(total),norm(direct)+norm(inherited)),
                    b+'_d_drift':A.ratio(norm(nd(xx['x1'])-nd(xx['x0'])-d[b]),dn),
                    b+'_x0_drift':A.ratio(norm(nd(xx['x0'])-nd(v['x0'])),norm(v['x0'])),
                    b+'_gate_drift_over_gate_difference':A.ratio(norm(ng(xx['z_cur'])-ng(v['z'])),norm(gd)),
                    b+'_inv_drift':A.ratio(norm(xx['inv_r1'].double()-v['inv_r1'].reshape_as(xx['inv_r1']).double()),norm(v['inv_r1'])),
                    b+'_cpu_native_max_abs':float((f[b][1]-nd(v['native_norm'])).abs().max())})
        for rb in ('C','H'):
            key='fit_r'+rb+'_d'+b
            vectors[key] = (w*inv[rb]*gd*d[b]/dn).reshape(-1) if dn else torch.zeros_like(d[b]).reshape(-1)
            row[key] = norm(vectors[key]) if dn else None
    for rb in ('C','H'):
        row['fit_r'+rb+'_HC_cos'] = cosine(vectors['fit_r'+rb+'_dH'],vectors['fit_r'+rb+'_dC'])
        row['fit_r'+rb+'_H_over_C'] = A.ratio(row['fit_r'+rb+'_dH'],row['fit_r'+rb+'_dC']) if row['C_d'] and row['H_d'] else None
    for b in ('C','H'):
        row['scale_d'+b+'_H_over_C'] = A.ratio(row['fit_rH_d'+b],row['fit_rC_d'+b]) if row[b+'_d'] else None
    for k in ('d','raw_d','ideal','finite','direct','inherited','total'):
        row['HC_ratio_'+k] = A.ratio(row['H_'+k],row['C_'+k])
    row['ideal_HC_cos'] = cosine(vectors['H_ideal'],vectors['C_ideal'])
    return row,vectors


def scan(output, model_dir):
    import torch
    from safetensors import safe_open
    torch.set_num_threads(4)
    start=time.monotonic(); files={}
    runs={'ngu':NGU/'runs/formal-20261116-r01','rcs':RCS/'runs/formal-20261115-r01'}
    receipts={k:json.loads((p/'receipt.json').read_text()) for k,p in runs.items()}
    for k,p in runs.items():
        assert receipts[k]['status']=='completed' and json.loads((p/'exit.json').read_text())['returncode']==0
    def load(which,rel):
        p=runs[which]/rel; h=A.sha(p); assert h==receipts[which]['files'][rel],p
        files[str(p)]={'sha256':h,'bytes':p.stat().st_size}
        return torch.load(p,map_location='cpu',weights_only=True)
    source=runs['ngu']/'analysis.json'
    assert A.sha(source)=='989032dbbaf7e6a10155a168c9bcfd4587918987fd8e370b52c24a27b266870c'
    analysis=json.loads(source.read_text()); pairs=analysis['continuous']['pairs']
    assert len(pairs)==168 and len({p['receiver'] for p in pairs})==48
    static=load('ngu','tensors/static.pt')
    rows=[]; matrices={l:{} for l in A.G}
    for i,p in enumerate(pairs):
        r,d=p['receiver'],p['donor']
        native={b:load('rcs',f'tensors/{r}/{d}-{b}11-t2.pt') for b in ('C','H')}
        actual={b:load('ngu',f'tensors/{r}/{d}-{b}X-t2.pt') for b in ('C','H')}
        for l in A.G:
            for b in ('C','H'):
                assert torch.equal(static[l]['norm_weight'],native[b][l]['weight'])
                assert torch.equal(actual[b][l]['z_ref'],native['H' if b=='C' else 'C'][l]['z'].reshape_as(actual[b][l]['z_ref']))
                if l==A.G[0]:
                    for xk,nk in (('x0','x0'),('x1','x1'),('z_cur','z'),('inv_r1','inv_r1'),('native','native_norm')):
                        assert torch.equal(actual[b][l][xk],native[b][l][nk].reshape_as(actual[b][l][xk])),('first tap drift',r,d,b,xk)
            metrics,vec=local(native['C'][l],native['H'][l],actual['C'][l],actual['H'][l],static[l]['norm_weight'])
            rows.append({'receiver':r,'donor':d,'scenario':p['scenario'],'layer':l,**metrics})
            for k,v in vec.items(): matrices[l].setdefault(k,[]).append(v)
        if (i+1)%42==0: print('read pairs',i+1,'seconds',round(time.monotonic()-start,1),flush=True)
    index_path=model_dir/'model.safetensors.index.json'
    index=json.loads(index_path.read_text())['weight_map']; weights={}
    for l in A.G:
        key=f'model.language_model.layers.{l}.linear_attn.out_proj.weight'
        with safe_open(model_dir/index[key],framework='pt',device='cpu') as f: w=f.get_tensor(key)
        wh=hashlib.sha256(w.contiguous().reshape(-1).view(torch.uint8).numpy().tobytes()).hexdigest()
        assert wh==static[l]['out_proj_weight_sha256'] and w.ndim==2 and w.shape[1]==4096
        weights[key]={'file':str(model_dir/index[key]),'shape':list(w.shape),'dtype':str(w.dtype),'tensor_sha256':wh}
        names=list(matrices[l]); batch=torch.cat([torch.stack(matrices[l][k]) for k in names])
        projected=(batch@w.double().T).reshape(len(names),len(pairs),w.shape[0]); localrows=[r for r in rows if r['layer']==l]
        for i,row in enumerate(localrows):
            pv={k:projected[j,i] for j,k in enumerate(names)}
            for k,v in pv.items(): row['Wo_'+k]=norm(v) if row[k] is not None else None
            for b in ('C','H'):
                d,u=pv[b+'_direct'],pv[b+'_inherited']
                row.update({b+'_Wo_total':norm(d+u),b+'_Wo_inherited_direct_cos':cosine(d,u),
                            b+'_Wo_cancellation_ratio':A.ratio(norm(d+u),norm(d)+norm(u))})
                for k in ('ideal','finite','direct','inherited'):
                    row[b+'_Wo_gain_'+k]=A.ratio(row['Wo_'+b+'_'+k],row[b+'_'+k])
            for k in ('ideal','finite','direct','inherited'):
                row['Wo_HC_ratio_'+k]=A.ratio(row['Wo_H_'+k],row['Wo_C_'+k])
            for rb in ('C','H'):
                row['Wo_fit_r'+rb+'_HC_cos']=cosine(pv['fit_r'+rb+'_dH'],pv['fit_r'+rb+'_dC'])
                a,b=row['Wo_fit_r'+rb+'_dH'],row['Wo_fit_r'+rb+'_dC']
                row['Wo_fit_r'+rb+'_H_over_C']=A.ratio(a,b) if a is not None and b is not None else None
        del batch,projected,w;matrices[l].clear()
        print('projected layer',l,'seconds',round(time.monotonic()-start,1),flush=True)
    fields=[k for k in rows[0] if k not in ('receiver','donor','scenario','layer')]
    summaries={}
    for l in A.G:
        rr=[r for r in rows if r['layer']==l]
        summaries[str(l)]={'means':{k:A.receiver_mean(rr,k) for k in fields},
            'undefined':{k:sum(r[k] is None for r in rr) for k in fields},
            'scenarios':{s:{k:A.receiver_mean([r for r in rr if r['scenario']==s],k) for k in fields} for s in sorted({r['scenario'] for r in rr})}}
    assert not torch.cuda.is_initialized()
    result={'kind':'posthoc CPU geometry, no new model experiment or inferential tests','rows':rows,'per_layer':summaries,
        'verified_input_files':files,'verified_activation_bytes':sum(v['bytes'] for v in files.values()),
        'weights':weights,'index_sha256':A.sha(index_path),'analysis_source_sha256':A.sha(source),
        'source_hashes':{str(p):A.sha(p) for p in (HERE/'analyse.py',HERE/'PLAN.zh-CN.md',Path(A.__file__))},
        'torch_version':torch.__version__,
        'model_forwards':0,'cuda_initialized':False,'torch_threads':torch.get_num_threads(),'wall_seconds':time.monotonic()-start}
    raw=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)
    assert len(raw.encode())<128*2**20
    with output.open('x') as f:f.write(raw)
    print('completed',len(rows),'rows',result['wall_seconds'],'seconds',len(raw.encode()),'bytes')


def self_test():
    import torch
    # Amplitude, orientation, scale and subsequent linear projection are distinguishable.
    c=torch.tensor([1.,0.],dtype=torch.float64);h=2*c;g=torch.tensor([1.,4.],dtype=torch.float64)
    assert norm(h)/norm(c)==2 and norm(g*h/norm(h))==norm(g*c/norm(c))
    h=torch.tensor([0.,1.],dtype=torch.float64)
    assert norm(h)==norm(c) and norm(g*h)/norm(g*c)==4
    assert norm(2*g*h)/norm(g*h)==2
    w=torch.tensor([[4.,0.],[0.,1.]],dtype=torch.float64)
    assert norm(w@(g*h))==norm(w@(g*c))
    native=torch.tensor([1.,2.]);base=torch.tensor([2.,3.]);patch=torch.tensor([4.,1.])
    assert torch.equal(patch.double()-base.double(),(patch.double()-native.double())+(native.double()-base.double()))
    assert A.receiver_mean([{'receiver':'a','v':1.},{'receiver':'a','v':3.},{'receiver':'b','v':8.}],'v')==5
    assert A.ratio(1,0) is None and cosine(c,torch.zeros_like(c)) is None
    for dtype in (torch.float32,torch.bfloat16):
        v0=torch.zeros(32,128,dtype=dtype);v1=torch.ones_like(v0);iv=torch.ones(32,1);wt=torch.ones(128,dtype=dtype)
        def fixture(d,g):
            n=endpoint(d,g,iv,wt)
            return {'x0':v0,'x1':d,'z':g,'inv_r1':iv,'raw0':v0.float(),'raw1':d.float(),'native_norm':n}
        cc,hh=fixture(v1,v0),fixture(2*v1,2*v1)
        def exchanged(t,g):
            nr=endpoint(t['x1'],g,iv,wt)
            return {'x0':v0,'x1':t['x1'],'z_cur':t['z'],'inv_r1':iv,'native':t['native_norm'],
                    'patch':nr,'delta_cur':t['native_norm'].double(),'delta_ref':nr.double()}
        r,_=local(cc,hh,exchanged(cc,hh['z']),exchanged(hh,cc['z']),wt)
        assert abs(r['HC_ratio_ideal']-2)<1e-12 and abs(r['HC_ratio_direct']-2)<1e-12
        assert abs(r['fit_rC_H_over_C']-1)<1e-12 and r['C_inherited']==r['H_inherited']==0
    assert not torch.cuda.is_initialized()
    print('self-test passed; model forwards 0; CUDA not initialized')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--self-test',action='store_true');parser.add_argument('--output',type=Path);parser.add_argument('--model-dir',type=Path)
    args=parser.parse_args()
    if args.self_test:self_test()
    else:
        assert args.output and args.model_dir and not args.output.exists()
        def timeout(*_):raise TimeoutError('30 minute CPU analysis limit')
        signal.signal(signal.SIGALRM,timeout);signal.alarm(1800)
        scan(args.output,args.model_dir)
