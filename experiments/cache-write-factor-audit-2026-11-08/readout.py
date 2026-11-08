"""CPU re-projection of existing NBR tensors, no model imports/forwards.
Usage: CUDA_VISIBLE_DEVICES='' python readout.py /workspace/acupuncture > readout.json
All layer sums below are first-order diagnostics, NOT additive causal shares.
"""
import hashlib
import io
import json
import sys
from pathlib import Path

import torch

torch.set_num_threads(1)
root = Path(sys.argv[1]) / 'experiments'
nbr = root / 'cache-native-bridge-record-v1-2026-11-03'
layers = [13,14,16,17,18,20,21,22,24,25,26,28,29,30]
manifest, items, reference_checks = {}, [], []
alpha_min = 1.0


def read(path, expected=None):
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    assert expected is None or digest == expected, str(path)
    manifest[str(path.relative_to(root))] = digest
    return raw


for w in (0,1):
    worker = nbr / 'runs/formal-r01' / f'worker-{w}'
    receipt = json.loads(read(worker / 'receipt.json'))
    for rel, expected in sorted(receipt['record_hashes'].items()):
        record = json.loads(read(worker / rel, expected))
        if record['item']['target'] == record['item']['first_listed']:
            continue
        rel_t = record['tensor_file']
        t = torch.load(io.BytesIO(read(worker / rel_t, receipt['tensor_hashes'][rel_t])), map_location='cpu', weights_only=True)
        fields = record['state_fields']
        results, old = {}, {}
        for d in record['directions']:
            st = t[f'state|{d}'].double()
            for b in '01':
                n0,n1 = [st[:,:,fields.index(f'nSa{s}_b{b}')] for s in '01']
                assert bool((n0>0).all()) and bool((n1>0).all())
                cu,cd = n1/n0,n0/n1
                cu[0],cd[0] = 1.0,1.0
                x = {(s,r):t[f'XA|{s}|{r}|{b}|{d}'].double() for s in '01' for r in '01'}
                a = {r:t[f'al|{r}0{b}|{d}'].double() for r in '01'}
                alpha_min = min(alpha_min,float(a['0'].min()),float(a['1'].min()))
                assert bool((a['0']>0).all()) and bool((a['1']>0).all())
                for scale in ('high','low'):
                    # Equal per-block norms: source 1 minus rescaled source 0, or reverse endpoint scale.
                    rd = {r: x[('1',r)]-cu[...,None]*x[('0',r)] for r in '01'}
                    if scale=='low':
                        rd = {r:cd[...,None]*v for r,v in rd.items()}
                    # Swap q only while alpha remains at reader 0; then change alpha.
                    q1a0 = rd['1']*(a['0']/a['1'])[...,None]
                    vectors = {'reader0':rd['0'],'reader1':rd['1'],
                               'q_change':q1a0-rd['0'],'alpha_change':rd['1']-q1a0}
                    assert torch.allclose(vectors['q_change']+vectors['alpha_change'],rd['1']-rd['0'],rtol=1e-10,atol=1e-12)
                    for gc in '01':
                        for pt in '01':
                            g = t[f'g|{gc}{pt}{b}|{d}'].double()
                            for kind,v in vectors.items():
                                key=f'{d}|{scale}|b{b}|g{gc}{pt}|{kind}'
                                results[key]=(g*v).sum((-1,-2)).tolist()
                            # Hold the identical gradient across the two k conditions.
                            for gb in '01':
                                common_g=t[f'g|{gc}{pt}{gb}|{d}'].double()
                                for r in '01':
                                    key=f'{d}|{scale}|b{b}|common_g{gc}{pt}{gb}|reader{r}'
                                    results[key]=(common_g*rd[r]).sum((-1,-2)).tolist()
                # Independently reproduce the archived NMT first-order reference.
                for r in '01':
                    for pt in '01':
                        g=t[f'g|{r}{pt}{b}|{d}'].double()
                        for arm,v in {'0':x[('0',r)],'1':x[('1',r)],'UP':cu[...,None]*x[('0',r)],
                                      'DN':cd[...,None]*x[('1',r)],'UPG':(n1.norm()/n0.norm())*x[('0',r)]}.items():
                            old[f'{d}|r{r}|p{pt}|{arm}|b{b}']=float((g*v).sum())
        items.append(dict(item=record['text'],scenario=record['scenario'],projections=results,reference=old))
        del t

assert len(items)==32
scenarios=sorted({r['scenario'] for r in items})
assert len(scenarios)==6


def seq(values):
    return sum(sum(values[i] for i,r in enumerate(items) if r['scenario']==s)/sum(r['scenario']==s for r in items) for s in scenarios)/len(scenarios)


means={k:[seq([r['projections'][k][j] for r in items]) for j in range(14)] for k in items[0]['projections']}
oldmean={k:seq([r['reference'][k] for r in items]) for k in items[0]['reference']}
refpath=root/'cache-increment-norm-match-v2-2026-11-03/readiness/first-order-ref-r01.json'
ref=json.loads(read(refpath))['values']
max_ref_error=0.0
for d,v in ref.items():
    for r in '01':
        for pt,label in [('0','A'),('1','B')]:
            h={arm:oldmean[f'{d}|r{r}|p{pt}|{arm}|b1']-oldmean[f'{d}|r{r}|p{pt}|{arm}|b0'] for arm in ('0','1','UP','DN','UPG')}
            den=h['1']-h['0']
            got=dict(D_src=den,phi_up=(h['UP']-h['0'])/den,phi_dn=(h['1']-h['DN'])/den,phi_UPG=(h['UPG']-h['0'])/den)
            for key,value in got.items():
                err=abs(value-v[f'r{r}_{label}'][key])
                max_ref_error=max(max_ref_error,err)
                assert err<1e-6,(d,r,pt,key,err)
print(json.dumps(dict(scope='32 target-not-first existing inputs, six-scenario equal means; no new forwards',
    layers=layers,source_sha256=manifest,alpha_min=alpha_min,archived_reference_max_abs_error=max_ref_error,
    projection_key='direction|high/low matched norm|b|g(background)(endpoint0/1)|reader0/reader1/q_change/alpha_change',
    note='q_change fixes alpha at reader0; alpha_change follows q swap. Gradients fixed in each comparison. Layer sums diagnostic only.',
    layer_means=means,items=[dict(item=r['item'],scenario=r['scenario'],
        projection_sums={k:sum(v) for k,v in r['projections'].items()},reference=r['reference'])
        for r in items]),ensure_ascii=False,indent=1))
