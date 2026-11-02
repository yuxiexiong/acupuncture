"""NVW-01 CPU readiness (no weights): torch kernel/conv paths and hook targets; KUC-01 formal passed; KUC records hold fF per direction,
V/F original arms and R01/R11/A01/A11/Z01/Z11 with natural tokens and M; KUC tensors hold t1 and C t2 logits for those keys; QCD T hashes
used by form_text present; formation tokens re-summed (6375 / 265).  CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import nvw_run as R  # noqa: E402


def main(out):
    import torch
    ki = R.kernel_identity()
    QM = R.gdn_module()
    qkd, kuc = R.qkd_records(), R.kuc_records()
    res = {'kernel_identity': ki, 'hook_targets': all(hasattr(QM, n) for n in ('causal_conv1d_update', 'torch_recurrent_gated_delta_rule', 'l2norm')),
           'kuc_formal_passed': R.exp.read(R.KUC_FORMAL / 'verification.json')['status'] == 'passed', 'n_kuc': len(kuc), 'items': {}}
    tf = sum(qkd[t['id']]['counts']['formation_token_forwards'] for t in R.items())
    tp = sum(qkd[a]['counts']['formation_token_forwards'] for a in R.PREFLIGHT_ITEMS)
    res['formation_tokens'] = {'formal': tf, 'preflight': tp, 'match': tf == 6375 and tp == 265}
    ok = not (ki['fla'] or ki['kernels'] or ki['causal_conv1d']) and res['hook_targets'] and res['kuc_formal_passed'] and len(kuc) == 48 and res['formation_tokens']['match']
    fFs = set()
    for t in R.items():
        a = t['id']
        r = kuc[a]
        tt = torch.load(r['_tensor_path'], map_location='cpu')
        x = {'dirs': set(r['directions']) == set(R.DIRECTIONS), 'arms': True, 'tensors': True, 'fF': True}
        for d in R.DIRECTIONS:
            kd = r['directions'][d]
            fFs.add(kd['fF'])
            x['fF'] &= kd['fF'] not in R.STOP
            x['arms'] &= all(b in kd['orig'] and kd['orig'][b]['N']['ids'] for b in ('V', 'F')) and all(kk in kd['new'] and kd['new'][kk]['N']['ids'] for kk in R.KUC_KEY.values())
            x['tensors'] &= all(f'{p}|{kk}|{d}' in tt for p in ('t1', 'C') for kk in ('V', 'F') + tuple(R.KUC_KEY.values()))
        x['passed'] = all(x.values())
        ok &= x['passed']
        res['items'][a] = x
        del tt
    res['distinct_fF_tokens'] = sorted(fFs)
    res['passed'] = bool(ok)
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in res.items() if k != 'items'}))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
