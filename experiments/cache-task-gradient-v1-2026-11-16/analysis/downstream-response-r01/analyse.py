"""A024: old tensors only, CPU. No model imports or forward calls."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import hashlib
import json
import math
from pathlib import Path
import statistics as st
import sys
import time
import torch

HERE = Path(__file__).resolve().parent
TGA = HERE.parents[1]
ROOT = TGA.parents[1]
RUN = TGA/'runs/formal-20261116-r01'
NGU = TGA.parent/'cache-numerator-gate-use-v1-2026-11-16'
sys.path.insert(0, str(TGA))
from tg_analysis import projection, receiver_mean


def read(p):
    return json.loads(p.read_text())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def geometry(c, h):
    nc, nh = c.norm().item(), h.norm().item()
    assert min(nc, nh) > 0
    k = (h*c).sum().item()/nc**2
    rem = h-k*c
    return dict(C_norm=nc, H_norm=nh, norm_ratio=nh/nc,
                cosine=(c*h).sum().item()/(nc*nh), k=k,
                residual_fraction=rem.norm().item()/nh), rem


def means(rows):
    fields = [k for k,v in rows[0].items() if isinstance(v, (float,int)) and k!='layer']
    return {k:receiver_mean(rows,k) for k in fields}


def half_bin(x):
    t=torch.tensor(x,dtype=torch.bfloat16)
    assert float(t)==x
    up=float(torch.nextafter(t,torch.tensor(float('inf'),dtype=t.dtype)))
    down=float(torch.nextafter(t,torch.tensor(-float('inf'),dtype=t.dtype)))
    return max(up-x,x-down)/2


def main():
    torch.set_num_threads(1)
    start=time.monotonic(); verified={}
    manifest=read(TGA/'readiness/artifacts-final-r01.json')['files']
    freeze=read(TGA/'readiness/freeze-server-r01.json')
    priorpath=NGU/'analysis/asymmetry-r01/result-r01.json'
    assert sha(priorpath)=='de2c6079124d02f912e629efa9dc432d9bbc57958f659260ba059404efaaed5f'
    prior=read(priorpath)
    old={(r['receiver'],r['donor'],r['layer']):r for r in prior['rows']}
    verified[str(priorpath.relative_to(ROOT))]=sha(priorpath)
    rows=[]; layers=[]
    for path in sorted((RUN/'records').glob('*/*.json')):
        assert sha(path)==manifest[str(path.relative_to(TGA))]['sha256']
        verified[str(path.relative_to(ROOT))]=sha(path)
        rec=read(path); r,d=rec['receiver'],rec['donor']
        base={k:rec[k] for k in ('receiver','donor','scenario')}
        grads={};physical={}
        for b in ('C','H'):
            p=RUN/f'gradients/{r}/{d}-{b}.pt'
            assert sha(p)==manifest[str(p.relative_to(TGA))]['sha256']
            verified[str(p.relative_to(ROOT))]=sha(p)
            grads[b]=torch.load(p,map_location='cpu',weights_only=True)
            p=NGU/f'runs/formal-20261116-r01/tensors/{r}/{d}-{b}X-t2.pt'
            assert sha(p)==freeze['task_assets'][str(p.relative_to(ROOT))]
            verified[str(p.relative_to(ROOT))]=sha(p)
            tensors=torch.load(p,map_location='cpu',weights_only=True)
            physical[b]={l:t['patch'].double()-t['native'].double() for l,t in tensors.items()}
        assert projection(grads,physical)==rec['projection']
        ls=sorted(grads['C']); assert len(ls)==14
        g={b:torch.cat([grads[b][l].flatten() for l in ls]) for b in grads}
        geo,rem=geometry(g['C'],g['H']); row={**base,**geo}
        units={b:{} for b in grads}
        for l in ls:
            c,h=physical['C'][l],-physical['H'][l]
            scale=math.sqrt(c.norm().item()*h.norm().item())
            assert scale>0
            units['C'][l]=scale*c/c.norm();units['H'][l]=scale*h/h.norm()
            lg,lr=geometry(grads['C'][l],grads['H'][l])
            z={**base,'layer':l,**lg}
            for b in ('C','H'):
                u=units[b][l]
                z[b+'_response_C']=(grads['C'][l]*u).sum().item()
                z[b+'_response_H']=(grads['H'][l]*u).sum().item()
                z[b+'_scale_component']=(lg['k']-1)*z[b+'_response_C']
                z[b+'_orientation_component']=(lr*u).sum().item()
            prev=old[r,d,l]
            for b in ('C','H'):
                for f in ('rounding_relative','d_drift','x0_drift','inv_drift','direct'):
                    z[b+'_'+f]=prev[b+'_'+f]
            layers.append(z)
        for dsource in ('C','H'):
            u=torch.cat([units[dsource][l].flatten() for l in ls])
            c=(g['C']*u).sum().item();h=(g['H']*u).sum().item()
            scale=(geo['k']-1)*c;orient=(rem*u).sum().item()
            assert math.isclose(h-c,scale+orient,abs_tol=1e-11)
            row.update({dsource+'_response_C':c,dsource+'_response_H':h,
                        dsource+'_scale_component':scale,dsource+'_orientation_component':orient})
            for bg in ('C','H'):
                terms=list(rec['projection']['terms']['equal_amplitude'][bg][dsource].values())
                row[f'{dsource}_{bg}_positive']=sum(max(t,0) for t in terms)
                row[f'{dsource}_{bg}_negative']=sum(min(t,0) for t in terms)
        for b in ('C','H'):
            obs=rec[b]['observed'];pred=rec['projection']['totals']['raw'][b][b]
            # Bound ONLY the four final BF16 output roundings, not upstream quantization.
            contract=rec[b+'_score_contract'];idx=[contract['donor_row'],contract['target_row']]
            bound=sum(half_bin(rec[b]['endpoints'][e]['candidate_logits'][i]) for e in ('native','frozen') for i in idx)
            native=rec[b]['endpoints']['native']['candidate_logits']
            row.update({b+'_observed':obs,b+'_prediction':pred,b+'_error':pred-obs,
                        b+'_absolute_error':abs(pred-obs),b+'_abs_observed':abs(obs),
                        b+'_final_round_bound':bound,b+'_error_exceeds_final_bound':int(abs(pred-obs)>bound),
                        b+'_positive_error':int(pred>obs),b+'_native_L':native[idx[0]]-native[idx[1]],
                        b+'_physical_norm':math.sqrt(sum(v.square().sum().item() for v in physical[b].values()))})
            for f in ('rounding_relative','d_drift','x0_drift','inv_drift'):
                row[b+'_layermean_'+f]=st.mean(old[r,d,l][b+'_'+f] for l in ls)
        rows.append(row)
    assert len(rows)==168 and len({r['receiver'] for r in rows})==48
    assert not torch.cuda.is_initialized()
    scene={s:means([r for r in rows if r['scenario']==s]) for s in sorted({r['scenario'] for r in rows})}
    receiver={r:means([x for x in rows if x['receiver']==r]) for r in sorted({r['receiver'] for r in rows})}
    output=dict(kind='seen-panel descriptive; no module attribution', rows=rows,layer_rows=layers,
                means=means(rows),scenarios=scene,receivers=receiver,
                layers={str(l):means([r for r in layers if r['layer']==l]) for l in ls},
                sources=verified,source_sha256=sha(Path(__file__)),torch_version=torch.__version__,
                torch_threads=torch.get_num_threads(),wall_seconds=time.monotonic()-start,
                model_forwards=0,cuda_initialized=False,projection_records_reproduced=168)
    p=HERE/'result-r01.json'
    encoded=json.dumps(output,indent=2,allow_nan=False)+'\n'
    assert len(encoded.encode())<=30*2**20, 'output budget exceeded'
    with p.open('x') as f:f.write(encoded)
    print(json.dumps({'status':'completed','rows':len(rows),'layers':len(layers),'files':len(verified),
                      'seconds':output['wall_seconds'],'result_sha256':sha(p),'model_forwards':0,'cuda_initialized':False}))


if __name__=='__main__':main()
