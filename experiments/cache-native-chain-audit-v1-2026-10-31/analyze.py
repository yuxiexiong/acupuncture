"""CPU-only audit of saved S2 tensors; no model loading, no patched forward.

Usage: CUDA_VISIBLE_DEVICES='' python analyze.py /workspace/acupuncture > result.json
Reuses frozen S1 account.py. Results describe native traces, not causal shares.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import time

os.environ['CUDA_VISIBLE_DEVICES'] = ''
import torch

torch.set_num_threads(2)
torch.set_grad_enabled(False)
root = Path(sys.argv[1])
s1 = root / 'experiments/cache-formation-mechanism-s1-native-trace-v1-2026-10-31'
run = root / 'experiments/cache-formation-mechanism-s2-formation-test-v3-2026-10-31/runs/formal-r01'
sys.path.insert(0, str(s1))
import account as A


def sha(path):
    with open(path, 'rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def norm(x):
    return float(x.double().norm())


def ip(x, y):
    return float((x * y).sum())


def relative(x, y):
    return norm(x - y) / max(norm(y), 1e-30)


def load_record(path):
    r = json.loads(path.read_text())
    p = path.parent.parent / r['tensor_file']
    assert sha(p) == r['tensor_sha256'], str(p)
    cap = torch.load(p, map_location='cpu', weights_only=False)
    return r, cap, A.from_capture(cap)


def compare(r, cap_c, cap_t, c, t, layer):
    pc, pt = A.prepare(c['main']), A.prepare(t['main'])
    shape = c['exposed']['prefix'].shape
    sc, st = torch.zeros(shape, dtype=torch.float64), torch.zeros(shape, dtype=torch.float64)
    b = r['b']
    n = pc['q'].shape[0]
    rows = []
    errors = {'state_rel_max': 0., 'raw_rel_max': 0., 'read_identity_abs_max': 0.}
    for i in range(n):
        vals = []
        for p, s, raw in ((pc, sc, c['main']['core_out']), (pt, st, t['main']['core_out'])):
            alpha, beta, k, v, q = (p[z][i] for z in ('alpha', 'beta', 'k', 'v', 'q'))
            decayed = alpha[:, None, None] * s
            m = A.readout(decayed, k)
            e = v - m
            delta = A.write_term(beta, k, e)
            sn = decayed + delta
            old_read = A.readout(decayed, q)
            correction_read = beta[:, None] * (k * q).sum(-1)[:, None] * e
            out = A.readout(sn, q)
            errors['read_identity_abs_max'] = max(errors['read_identity_abs_max'], norm(out-old_read-correction_read))
            errors['raw_rel_max'] = max(errors['raw_rel_max'], relative(out, raw[i].double()))
            vals.append((sn, m, e, delta, old_read, correction_read, out))
        vc, vt = vals
        sc, st = vc[0], vt[0]
        if i in (n-2, n-1):
            key = 'prefix' if i == n-2 else 'last'
            errors['state_rel_max'] = max(errors['state_rel_max'], relative(sc,c['exposed'][key]), relative(st,t['exposed'][key]))
        if i <= b:
            continue
        dv, dm, de = pt['v'][i]-pc['v'][i], vt[1]-vc[1], vt[2]-vc[2]
        dr_old, dr_corr, dr = vt[4]-vc[4], vt[5]-vc[5], vt[6]-vc[6]
        row = {'position': i, 'segment': r['segments']['labels'][i], 'after_flush': i >= b+4,
               'dv2': ip(dv,dv), 'dm2': ip(dm,dm), 'de2': ip(de,de),
               'ip_dv_de': ip(dv,de), 'ip_minus_dm_de': -ip(dm,de),
               'ip_dv_dm': ip(dv,dm), 'do2': ip(dr,dr),
               'old_read_diff2': ip(dr_old,dr_old), 'correction_read_diff2': ip(dr_corr,dr_corr),
               'ip_old_do': ip(dr_old,dr), 'ip_correction_do': ip(dr_corr,dr),
               'correction_state_diff': norm(vt[3]-vc[3]),
               'core_out_actual_diff': norm(t['main']['core_out'][i].double()-c['main']['core_out'][i].double()),
               'norm_out_diff': norm(t['main']['norm_out'][i].double()-c['main']['norm_out'][i].double()),
               'out_proj_diff': norm(t['main']['out_proj'][i].double()-c['main']['out_proj'][i].double())}
        for name in ('q','k','v','alpha','beta'):
            row[name+'_rel_diff'] = relative(pt[name][i],pc[name][i])
        phase, j = ('prefix',i) if i < n-1 else ('last',0)
        row['qkv_pre_rel_diff'] = relative(cap_t[phase][str(layer)]['qkv_pre'][0][j].double(),cap_c[phase][str(layer)]['qkv_pre'][0][j].double())
        rows.append(row)
    assert errors['state_rel_max'] <= 1e-3, errors
    assert errors['raw_rel_max'] <= 1e-2, errors
    return {'layer':layer,'errors':errors,'steps':rows}


started = time.time()
paths = sorted(run.glob('worker-*/records/*__clean__00.json'))
assert len(paths) == 12
result = {'schema':1,'source_commit':'69e140d81dcb101b98dbea43bbc392b9e08b7663',
          'scope':'36 saved native traces, 10 versus 00; CPU replay of local recurrence only; no model forward or gradients',
          'account_sha256':sha(s1/'account.py'),'records':[],'sources':[]}
for path in paths:
    rc, cc, tc = load_record(path)
    result['sources'].append({'record':str(path.relative_to(root)),'record_sha256':sha(path),'tensor_sha256':rc['tensor_sha256']})
    item = rc['item']['id']
    for anchor, needle_layer in (('N_L00_C4146_D-1',0),('N_L12_C3621_D-1',12)):
        tp = path.with_name(item+'__'+anchor+'__10.json')
        rt, ct, tt = load_record(tp)
        assert rc['prompt_token_ids'] == rt['prompt_token_ids']
        result['sources'].append({'record':str(tp.relative_to(root)),'record_sha256':sha(tp),'tensor_sha256':rt['tensor_sha256']})
        first = needle_layer+1
        same = {k:rc['prefix_manifest'][k]==v for k,v in rt['prefix_manifest'].items()}
        rec = {'item':item,'base':rc['item']['base_id'],'anchor':anchor,'b':rc['b'],
               'tail_tokens_before_tau':len(rc['prompt_token_ids'])-2-rc['b'],
               'cache_hash_equal':same,
               'upstream_including_needle_equal':all(v for k,v in same.items() if int(k.split(':')[0])<=needle_layer),
               'first_affected_layer':first,'first_conv_equal':same[f'{first}:conv_states'],
               'first_recurrent_equal':same[f'{first}:recurrent_states'],
               'layers':[compare(rc,cc,ct,tc['layers'][str(l)],tt['layers'][str(l)],l) for l in (16,17,18)]}
        result['records'].append(rec)
        print(item,anchor,'done',file=sys.stderr,flush=True)
        del ct,tt
    del cc,tc
result['wall_seconds'] = time.time()-started
result['torch_version'] = torch.__version__
result['gpu_visible'] = os.environ['CUDA_VISIBLE_DEVICES']
json.dump(result,sys.stdout,ensure_ascii=False,indent=2,allow_nan=False)
print()
