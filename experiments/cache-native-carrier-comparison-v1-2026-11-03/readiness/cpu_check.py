"""NCC-01 CPU readiness: torch kernel path; NVB formal (B000 t1 + natural for L0), LVK new-panel arm V (t1 + natural for L0), CGV G1
(C, L00, L10 t1 + natural for L12; formation hashes); plan docs.  CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import ncc_run as R  # noqa: E402


def main(out):
    import torch
    ki = R.kernel_identity()
    nv, cv, lv = R.nvb_records(), R.cgv_records(), R.SRUR.lvk_records()
    miss = {'nvb': 0, 'lvk': 0, 'cgv': 0}
    for a in nv:
        t = torch.load(nv[a]['_tensor_path'], map_location='cpu')
        miss['nvb'] += int(f't1|000|{R.L0}' not in t) + int('ids' not in nv[a]['directions'][R.L0]['cells']['000']['N'])
        del t
        t = torch.load(lv[a]['_tensor_path'], map_location='cpu')
        miss['lvk'] += int(f't1|V|{R.L0}' not in t) + int('V' not in lv[a]['directions'][R.L0]['arms']) + int(f'T_b|{R.L0}' not in lv[a]['formation_hashes'])
        del t
        t = torch.load(cv[a]['_tensor_path'], map_location='cpu')
        miss['cgv'] += sum(int(k not in t) for k in ('t1|C', f't1|{R.L12}|L00', f't1|{R.L12}|L10'))
        miss['cgv'] += int(f'T_b|{R.L12}' not in (cv[a]['formation_hashes'] or {}))
        del t
    docs = {str(p.relative_to(R.REPO)): p.exists() for p in R.PLAN_DOCS}
    res = {'kernel_identity': ki, 'n': {'nvb': len(nv), 'lvk': len(lv), 'cgv_g1': len(cv)}, 'missing': miss, 'plan_docs': docs,
           'cgv_verification': R.exp.read(R.CGV_FORMAL / 'verification.json')['status']}
    res['passed'] = bool(not (ki['fla'] or ki['kernels'] or ki['causal_conv1d']) and len(nv) == len(lv) == len(cv) == 48 and not any(miss.values())
                         and all(docs.values()) and res['cgv_verification'] == 'passed')
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(res))
    sys.exit(0 if res['passed'] else 1)


if __name__ == '__main__':
    main(sys.argv[1])
