"""Read frozen WSB tensors on CPU; no model imports, forwards or GPU calls."""
import argparse
import hashlib
import io
import json
import math
import os
from pathlib import Path
import statistics
import time

os.environ['CUDA_VISIBLE_DEVICES'] = ''
import torch
torch.set_num_threads(1)
G = (13,14,16,17,18,20,21,22,24,25,26,28,29,30)


def normalize(x):
    x = x.float()
    return (x*torch.rsqrt((x*x).sum(-1, keepdim=True)+1e-6)).double()


def cosine(x, y):
    den = float(x.norm()*y.norm())
    return float((x*y).sum())/den if den else None


def features(dc, dh, c, h):
    deltas = {'C': dc[0], 'H': dh[0]}
    local = {'C': c, 'H': h}
    q, k, dv, beta, norms = {}, {}, {}, {}, {}
    out = {}
    for s in ('C', 'H'):
        a = local[s]
        q[s] = (normalize(a['q'][0,0]).float()/math.sqrt(128)).double()
        k[s] = normalize(a['k'][0,0])
        dv[s] = a['v_d'][0,0].double()-a['v_o'][0,0].double()
        beta[s] = a['beta'][0,0].double()
        norms[s] = float(deltas[s].norm())
        expected = beta[s][:,None,None]*k[s][:,:,None]*dv[s][:,None,:]
        out['oracle_'+s] = float((deltas[s]-expected).abs().max())/max(1.,float(expected.abs().max()))
        assert out['oracle_'+s] <= 1e-5
        out['formula_relative_residual_'+s] = float((deltas[s]-expected).norm())/max(norms[s],1e-300)
        out['norm_'+s] = norms[s]
        out['beta_rms_'+s] = float(beta[s].square().mean().sqrt())
        out['knorm_min_'+s] = float(k[s].norm(dim=-1).min())
        out['knorm_mean_'+s] = float(k[s].norm(dim=-1).mean())
        out['dv_rms_'+s] = float(dv[s].square().sum(-1).mean().sqrt())
    out['dot'] = float((deltas['C']*deltas['H']).sum())
    out['cosine'] = cosine(deltas['C'], deltas['H'])
    out['norm_ratio_H_C'] = norms['H']/norms['C'] if norms['C'] else None
    out['scalar_residual_fraction'] = math.sqrt(max(0.,1-out['cosine']**2)) if out['cosine'] is not None else None
    for r in ('C', 'H'):
        for s in ('C', 'H'):
            v = torch.einsum('hkv,hk->hv', deltas[s], q[r])
            out['projection_'+r+s] = float(v.norm())
            out['efficiency_'+r+s] = float(v.norm())/norms[s] if norms[s] else None
    for name, bs, ks, vs in [('CCC','C','C','C'), ('HCC','H','C','C'),
                              ('CHC','C','H','C'), ('CCH','C','C','H'), ('HHH','H','H','H')]:
        amp = beta[bs]*k[ks].norm(dim=-1)*dv[vs].norm(dim=-1)
        out['factor_norm_'+name] = float(amp.norm())
    head = {'beta_C': beta['C'].tolist(), 'beta_H': beta['H'].tolist(),
            'knorm_C': k['C'].norm(dim=-1).tolist(), 'knorm_H': k['H'].norm(dim=-1).tolist(),
            'dvnorm_C': dv['C'].norm(dim=-1).tolist(), 'dvnorm_H': dv['H'].norm(dim=-1).tolist(),
            'k_cosine': [cosine(x,y) for x,y in zip(k['C'],k['H'])],
            'dv_cosine': [cosine(x,y) for x,y in zip(dv['C'],dv['H'])]}
    for name in ('k_cosine', 'dv_cosine'):
        valid = [v for v in head[name] if v is not None]
        out[name+'_mean'] = statistics.mean(valid) if valid else None
        out[name+'_undefined_heads'] = len(head[name])-len(valid)
    return out, head


def pooled(layers):
    keys = ['norm_C','norm_H']+['projection_'+c for c in ('CC','CH','HC','HH')]+[
        'factor_norm_'+c for c in ('CCC','HCC','CHC','CCH','HHH')]
    out = {k: math.sqrt(sum(v[k]**2 for v in layers.values())) for k in keys}
    den = out['norm_C']*out['norm_H']
    out['cosine'] = sum(v['dot'] for v in layers.values())/den if den else None
    out['norm_ratio_H_C'] = out['norm_H']/out['norm_C'] if out['norm_C'] else None
    out['scalar_residual_fraction'] = math.sqrt(max(0.,1-out['cosine']**2)) if den else None
    for c in ('CC','CH','HC','HH'):
        out['efficiency_'+c] = out['projection_'+c]/out['norm_'+c[1]] if out['norm_'+c[1]] else None
    return out


def summarize(rows, field):
    vals = [r[field] for r in rows]
    result = {}
    for key in vals[0]:
        good = [(r, v[key]) for r,v in zip(rows,vals) if v[key] is not None]
        if not good:
            result[key] = {'defined_pairs':0}; continue
        xs = sorted(x for _,x in good)
        receivers = sorted({r['receiver'] for r,_ in good})
        rm = {i:statistics.mean(x for r,x in good if r['receiver']==i) for i in receivers}
        result[key] = dict(defined_pairs=len(xs), receiver_mean=statistics.mean(rm.values()),
            pair_median=statistics.median(xs), pair_p10=xs[int(.1*(len(xs)-1))],
            pair_p90=xs[int(.9*(len(xs)-1))], pair_min=xs[0], pair_max=xs[-1])
    return result


def check():
    k = torch.zeros(1,1,32,128); k[...,0]=1
    q = torch.zeros_like(k); q[...,1]=1
    c = dict(k=k,q=q,v_o=torch.zeros_like(k),v_d=k,beta=torch.ones(1,1,32)*.25)
    h = {**c,'q':k,'beta':c['beta']*2}
    kc = normalize(k[0,0]); dc=(.25*kc[:,:,None]*k[0,0,:,None,:]).unsqueeze(0)
    dh=dc*2
    f,_=features(dc,dh,c,h)
    assert abs(f['norm_ratio_H_C']-2)<1e-12 and abs(f['cosine']-1)<1e-12
    assert f['projection_CC']==f['projection_CH']==0
    assert abs(f['projection_HH']/f['projection_HC']-2)<1e-12
    assert f['scalar_residual_fraction']<1e-7
    zero = {**c, 'v_d': c['v_o']}
    f,_=features(torch.zeros_like(dc),torch.zeros_like(dc),zero,zero)
    assert f['cosine'] is None and f['efficiency_CC'] is None and f['projection_CC']==0
    assert not torch.cuda.is_initialized()


def run(root, output):
    start=time.monotonic(); check()
    root=Path(root); output=Path(output); output.mkdir(parents=True,exist_ok=False)
    manifest={}
    def read(p, expected=None):
        raw=p.read_bytes(); digest=hashlib.sha256(raw).hexdigest()
        assert expected is None or digest==expected, str(p)
        manifest[str(p.relative_to(root))]=digest
        return raw
    receipt=json.loads(read(root/'receipt.json'))
    assert receipt['status']=='completed' and receipt['stage']=='formal'
    assert json.loads(read(root/'exit.json'))['returncode']==0
    answers=json.loads(read(root/'answers.json',receipt['files']['answers.json']))
    lookup={(v['receiver'],v['donor']):v for v in answers['delivery']['HH']}
    records=sorted(p for p in receipt['files'] if p.startswith('records/') and not p.endswith('bases.json'))
    assert len(records)==348
    rows=[]
    with (output/'pairs.jsonl').open('x') as log:
        for index,rel in enumerate(records):
            rec=json.loads(read(root/rel,receipt['files'][rel])); receiver=Path(rel).parts[1]; donor=Path(rel).stem
            packages={}
            for s in ('C','H'):
                path=rec['R_'+s]['package']
                packages[s]=torch.load(io.BytesIO(read(root/path,receipt['files'][path])),map_location='cpu',weights_only=True)
                assert tuple(packages[s]['delta'])==G
                assert all(t.dtype==torch.float64 and tuple(t.shape)==(1,32,128,128) for t in packages[s]['delta'].values())
            row=dict(receiver=receiver,donor=donor,scenario=receiver.split('-')[3],donor_type=lookup[receiver,donor]['donor_type'],
                     outputs={c:rec[c]['answer']['row'] for c in ('CC','CH','HC','HH')})
            heads={}
            for l in G:
                row[str(l)],heads[str(l)]=features(packages['C']['delta'][l],packages['H']['delta'][l],packages['C']['local'][l],packages['H']['local'][l])
                old=rec['delta_geometry_descriptive_only'][str(l)]
                for name in ('norm_C','norm_H','cosine'):
                    if old[name] is None:
                        assert row[str(l)][name] is None
                    else:
                        assert abs(row[str(l)][name]-old[name]) <= 1e-6*max(1.,abs(old[name])),(l,name)
            row['pooled']=pooled({str(l):row[str(l)] for l in G})
            log.write(json.dumps({**row,'heads':heads},allow_nan=False)+'\n'); log.flush(); rows.append(row)
            if (index+1)%30==0:print(json.dumps({'pairs_completed':index+1,'wall_seconds':time.monotonic()-start}),flush=True)
            del packages,heads
    fields=['pooled']+[str(l) for l in G]
    result={'status':'completed','kind':'posthoc CPU geometry and frozen-reference-query diagnostic',
            'pairs':len(rows),'receivers':len({r['receiver'] for r in rows}),'scenarios':sorted({r['scenario'] for r in rows}),
            'all':{f:summarize(rows,f) for f in fields},
            'per_scenario':{s:{f:summarize([r for r in rows if r['scenario']==s],f) for f in fields} for s in sorted({r['scenario'] for r in rows})},
            'manifest':manifest,'wall_seconds':time.monotonic()-start,'torch_version':torch.__version__,
            'cuda_initialized':torch.cuda.is_initialized(),'model_forwards':0,'gpu_hours':0,
            'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    assert result['receivers']==48 and len(result['scenarios'])==6 and not result['cuda_initialized']
    (output/'summary.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','pairs','wall_seconds','cuda_initialized','gpu_hours')}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run');p.add_argument('--output');p.add_argument('--check',action='store_true')
    a=p.parse_args()
    if a.check:check();print('CPU synthetic identities passed')
    else:run(a.run,a.output)
