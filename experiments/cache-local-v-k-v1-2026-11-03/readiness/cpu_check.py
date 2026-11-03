"""LVK-01 CPU readiness (no weights): torch kernel/conv paths and hook targets; NVW formal passed and its records/tensors hold T, RTW, V, RVW
(natural tokens, M, first-step G, t1 logits; C t2 logits for T, RTW); held-out ledger passed and matches the frozen input file; formation tokens
old 6375 + new 6390.  CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import lvk_run as R  # noqa: E402


def main(out):
    import torch
    ki = R.kernel_identity()
    QM = R.gdn_module()
    led = R.ledger()
    nv = R.nvw_records()
    qkd = R.qkd_records()
    res = {'kernel_identity': ki, 'hook_targets': all(hasattr(QM, x) for x in ('causal_conv1d_update', 'torch_recurrent_gated_delta_rule', 'l2norm')),
           'nvw_formal_passed': R.exp.read(R.NVW_FORMAL / 'verification.json')['status'] == 'passed', 'n_nvw': len(nv), 'n_ledger': len(led), 'items': {}}
    tf_old = sum(qkd[t['id']]['counts']['formation_token_forwards'] for t in R.items())
    tf_new = sum(5 * v['plan']['L'] for v in led.values())
    res['formation_tokens'] = {'old': tf_old, 'new': tf_new, 'match': tf_old + tf_new == R.LIMITS['formal']['formation_token_forwards']}
    ok = not (ki['fla'] or ki['kernels'] or ki['causal_conv1d']) and res['hook_targets'] and res['nvw_formal_passed'] and len(nv) == 48 and len(led) == 48 \
        and res['formation_tokens']['match']
    for t in R.items():
        a = t['id']
        r = nv[a]
        tt = torch.load(r['_tensor_path'], map_location='cpu')
        x = {'arms': all(k in r['directions'][d]['arms'] and r['directions'][d]['arms'][k]['N']['ids'] for d in R.DIRECTIONS for k in ('T', 'RTW', 'V', 'RVW')),
             't1': all(f't1|{k}|{d}' in tt for d in R.DIRECTIONS for k in ('T', 'RTW', 'V', 'RVW')),
             'C': all(f'C|{k}|{d}' in tt for d in R.DIRECTIONS for k in ('T', 'RTW')),
             'fF': all(r['directions'][d]['fF'] not in R.STOP for d in R.DIRECTIONS)}
        x['passed'] = all(x.values())
        ok &= x['passed']
        res['items'][a] = x
        del tt
    res['passed'] = bool(ok)
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in res.items() if k != 'items'}))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
