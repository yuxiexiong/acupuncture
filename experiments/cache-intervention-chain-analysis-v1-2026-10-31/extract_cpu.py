"""Read frozen S2 traces and two checkpoint tensors on CPU; no model construction/forward.

Run on the archive host with PYTHONDONTWRITEBYTECODE=1, sending JSON to stdout.
The checkpoint read recovers the rounded injection constant, NOT actual per-token additions.
"""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import hashlib
import json
from pathlib import Path
import sys
import time
import torch
from safetensors import safe_open

torch.set_num_threads(2)
torch.set_grad_enabled(False)
ROOT = Path(sys.argv[1])
S1 = ROOT / 'experiments/cache-formation-mechanism-s1-native-trace-v1-2026-10-31'
S2 = ROOT / 'experiments/cache-formation-mechanism-s2-formation-test-v3-2026-10-31'
RUN = S2 / 'runs/formal-r01'
sys.path.insert(0, str(S1))
import account as A

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def norm(x):
    return float(x.double().norm())

def metric(x, y):
    x, y = x.double(), y.double()
    dx = norm(x-y)
    return {'diff': dx, 'ref': norm(y), 'target': norm(x), 'relative': dx/max(norm(y), 1e-30)}

def ip(x,y):
    return float((x*y).sum())

def load(p):
    r=json.loads(p.read_text())
    tp=p.parent.parent/r['tensor_file']
    assert sha(tp)==r['tensor_sha256'], str(tp)
    cap=torch.load(tp,map_location='cpu',weights_only=False)
    out['sources'].append({'record':str(p.relative_to(ROOT)), 'record_sha256':sha(p),
                           'tensor':str(tp.relative_to(ROOT)), 'tensor_sha256':r['tensor_sha256']})
    return r,cap,A.from_capture(cap)

def compare(rx,cx,tx,ry,cy,ty,layer):
    X,Y=tx['layers'][str(layer)],ty['layers'][str(layer)]
    px,py=A.prepare(X['main']),A.prepare(Y['main'])
    sx=torch.zeros_like(X['exposed']['prefix']);sy=torch.zeros_like(sx)
    n=px['q'].shape[0];b=rx['b'];rows=[]
    err={'state_relative_max':0.,'raw_relative_max':0.}
    for t in range(n):
        vals=[]
        for p,s,rec in [(px,sx,X),(py,sy,Y)]:
            a,be,k,v,q=(p[z][t] for z in ('alpha','beta','k','v','q'))
            m=A.readout(a[:,None,None]*s,k);e=v-m
            sn=a[:,None,None]*s+A.write_term(be,k,e)
            o=A.readout(sn,q)
            err['raw_relative_max']=max(err['raw_relative_max'],metric(o,rec['main']['core_out'][t])['relative'])
            vals.append((sn,m,e,o,A.write_term(be,k,v)))
        if t==b:
            assert torch.equal(vals[0][0],vals[1][0]), 'same-start state mismatch'
        if t>b:
            row={'position':t,'segment':rx['segments']['labels'][t]}
            for name,j in [('state',0),('old_prediction',1),('error',2),('raw_read',3),('write_B',4)]:
                row[name]=metric(vals[0][j],vals[1][j])
            dv=px['v'][t]-py['v'][t];dm=vals[0][1]-vals[1][1]
            row['value']=metric(px['v'][t],py['v'][t])
            row['dv_dm_cos']=ip(dv,dm)/max(norm(dv)*norm(dm),1e-30)
            proc=A.apply_A((sx+sy)/2,px['alpha'][t],px['beta'][t],px['k'][t])-A.apply_A((sx+sy)/2,py['alpha'][t],py['beta'][t],py['k'][t])
            db=vals[0][4]-vals[1][4]
            row['processing_action_norm']=norm(proc)
            row['write_processing_cos']=ip(db,proc)/max(norm(db)*norm(proc),1e-30)
            for name in ('q','k','alpha','beta'):
                row[name]=metric(px[name][t],py[name][t])
            phase,j=('prefix',t) if t<n-1 else ('last',0)
            prex=cx[phase][str(layer)]['qkv_pre'][0][j]
            prey=cy[phase][str(layer)]['qkv_pre'][0][j]
            vd=px['v'][t].numel()
            row['preconv_value']=metric(prex[-vd:],prey[-vd:])
            for name in ('norm_out','out_proj'):
                row[name]=metric(X['main'][name][t],Y['main'][name][t])
            rows.append(row)
        sx,sy=vals[0][0],vals[1][0]
        if t in (n-2,n-1):
            key='prefix' if t==n-2 else 'last'
            err['state_relative_max']=max(err['state_relative_max'],metric(sx,X['exposed'][key])['relative'],metric(sy,Y['exposed'][key])['relative'])
    assert err['state_relative_max']<1e-3 and err['raw_relative_max']<1e-2,err
    return {'layer':layer,'errors':err,'steps':rows}

started=time.time()
out={'scope':'CPU analysis of existing native S2 traces; no patched state or model execution',
     'account_sha256':sha(S1/'account.py'),'sources':[],'dose':[],'pairs':[]}
freeze=json.loads((S2/'freeze-r02.json').read_text())
assert out['account_sha256']==freeze['files'][str((S1/'account.py').relative_to(ROOT))]
model=Path('/data/models/Qwen3.5-4B-851bf6e')
index=json.loads((model/'model.safetensors.index.json').read_text())['weight_map']
meta=json.loads((RUN/'worker-0/metadata.json').read_text())
columns={}
for layer,channel in [(0,4146),(12,3621)]:
    key=f'model.language_model.layers.{layer}.mlp.down_proj.weight'
    with safe_open(model/index[key],framework='pt',device='cpu') as f:
        w=f.get_tensor(key)
    h=hashlib.sha256(w.contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()
    assert h==meta['target_weight_sha256_before'][str(layer)]
    columns[layer]=(float(w.float().norm(dim=0)[channel]),h)
    del w
for cp in sorted(RUN.glob('worker-*/records/*__clean__00.json')):
    rc,cc,tc=load(cp);item=rc['item']['id'];ref=json.loads((cp.parent.parent/f'calibrations/{rc["item"]["reference_id"]}.json').read_text())
    for layer,channel in [(0,4146),(12,3621)]:
        anchor=f'N_L{layer:02d}_C{channel}_D-1'
        cn,h=columns[layer];scale=ref['residual_scales'][str(layer)]
        amount=float(torch.tensor(-scale/cn,dtype=torch.bfloat16))
        out['dose'].append({'item':item,'anchor':anchor,'scale':scale,'column_norm_cpu_fp32':cn,
                            'weight_sha256':h,'requested_offset':-scale/cn,'bf16_constant':amount,
                            'constant_projected_norm':abs(amount)*cn,
                            'constant_norm_over_reference':abs(amount)*cn/scale,
                            'actual_per_token_increment_saved':False})
        loaded={'00':(rc,cc,tc)}
        for arm in ('01','10','11'):
            loaded[arm]=load(cp.with_name(f'{item}__{anchor}__{arm}.json'))
        for arm,refarm in [('01','00'),('11','10')]:
            rx,cx,tx=loaded[arm];ry,cy,ty=loaded[refarm]
            assert rx['prompt_token_sha256']==ry['prompt_token_sha256']
            assert rx['reference_sha256']==ry['reference_sha256']
            p={'item':item,'base':rc['item']['base_id'],'anchor':anchor,'pair':arm+'v'+refarm,
               'b':rx['b'],'n':len(rx['prompt_token_ids']),'layers':[],'boundary':[]}
            for l in (16,17,18):
                p['layers'].append(compare(rx,cx,tx,ry,cy,ty,l))
            for t in range(rx['b']+1,len(rx['prompt_token_ids'])):
                phase,j=('prefix',t) if t<len(rx['prompt_token_ids'])-1 else ('last',0)
                p['boundary'].append({'position':t,**{key:metric(cx[phase]['boundary'][key][0][j],cy[phase]['boundary'][key][0][j]) for key in ('L16_in','L19_in','L19_out')}})
            out['pairs'].append(p)
        del loaded
        print(item,anchor,'done',file=sys.stderr,flush=True)
assert len(out['sources'])==84 and len(out['pairs'])==48 and len(out['dose'])==24
out['cpu_wall_seconds']=time.time()-started
json.dump(out,sys.stdout,ensure_ascii=False,indent=2,allow_nan=False)
