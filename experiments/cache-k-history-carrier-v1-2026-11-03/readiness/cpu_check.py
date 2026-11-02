"""KHC-01 CPU readiness (no weights): torch kernel path; KRD-01 r02 formal verification passed and readouts present; KRD records hold cells
01 / 11 of the six ordered pairs in four directions with C and N t2 bf16 logits (N where reached) and N trajectories (>= 2 tokens when
reached); QKD anchors as in KRD; formation-token budget re-summed (6375 / 265).  CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import khc_run as R  # noqa: E402


def main(out):
    import torch
    ki = R.kernel_identity()
    qkd, krd = R.qkd_records(), R.krd_records()
    kv = R.exp.read(R.KRD_FORMAL / 'verification.json')
    res = {'kernel_identity': ki, 'krd_formal_passed': kv['status'] == 'passed', 'n_krd': len(krd), 'n_qkd': len(qkd), 'items': {}}
    tf = sum(qkd[t['id']]['counts']['formation_token_forwards'] for t in R.items())
    tp = sum(qkd[a]['counts']['formation_token_forwards'] for a in R.PREFLIGHT_ITEMS)
    res['formation_tokens'] = {'formal': tf, 'preflight': tp, 'match': tf == 6375 and tp == 265}
    ok = not (ki['fla'] or ki['kernels'] or ki['causal_conv1d']) and res['krd_formal_passed'] and len(krd) == 48 and len(qkd) == 48 and res['formation_tokens']['match']
    n_unreached = 0
    for t in R.items():
        a = t['id']
        r = krd[a]
        tt = torch.load(r['_tensor_path'], map_location='cpu')
        x = {'cells': True, 'c_logits': True, 'n_logits': True, 'n_traj': True}
        for d in R.DIRECTIONS:
            kd = r['directions'][d]
            for rr, dd in R.ORDERED:
                for kc in ('01', '11'):
                    key = f'{rr}<-{dd}|{kc}'
                    if key not in kd['cells']:
                        x['cells'] = False
                        continue
                    nn = kd['cells'][key]['N']
                    x['c_logits'] &= f'C|{key}|{d}' in tt
                    if nn['reached_t2']:
                        x['n_logits'] &= f'N|{key}|{d}' in tt
                        x['n_traj'] &= len(nn['ids']) >= 2 and nn['termination'] in ('stop', 'budget')
                    else:
                        n_unreached += 1
        x['passed'] = all(x.values())
        ok &= x['passed']
        res['items'][a] = x
        del tt
    res['n_unreached_old_cells'] = n_unreached
    res['passed'] = bool(ok)
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in res.items() if k != 'items'}))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
