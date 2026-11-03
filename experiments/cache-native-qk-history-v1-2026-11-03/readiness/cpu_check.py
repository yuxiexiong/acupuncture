"""NQK-01 CPU readiness: torch kernel path; NCC-01 formal (C / T t1 tensors and natural records) and NSR-01 formal (CJ etc. for both needles);
plan doc.  CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import nqk_run as R  # noqa: E402


def main(out):
    import torch
    ki = R.kernel_identity()
    nc, ns = R.ncc_records(), R.nsr_records()
    miss = 0
    for a in nc:
        t = torch.load(nc[a]['_tensor_path'], map_location='cpu')
        miss += sum(int(k not in t) for k in ('t1|C', f't1|{R.L0}|T', f't1|{R.L12}|T'))
        del t
        t = torch.load(ns[a]['_tensor_path'], map_location='cpu')
        miss += sum(int(f't1|{d}|CJ' not in t) for d in R.NEEDLES) + sum(int('CJ' not in ns[a]['results'][d]) for d in R.NEEDLES)
        miss += int(ns[a]['formation_hashes'] != nc[a]['formation_hashes'])
        del t
    docs = {str(p.relative_to(R.REPO)): p.exists() for p in R.PLAN_DOCS}
    res = {'kernel_identity': ki, 'n_ncc': len(nc), 'n_nsr': len(ns), 'missing': miss, 'plan_docs': docs,
           'nsr_verification': R.exp.read(R.NSR_FORMAL / 'verification.json')['status']}
    res['passed'] = bool(not (ki['fla'] or ki['kernels'] or ki['causal_conv1d']) and len(nc) == len(ns) == 48 and miss == 0 and all(docs.values())
                         and res['nsr_verification'] == 'passed')
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(res))
    sys.exit(0 if res['passed'] else 1)


if __name__ == '__main__':
    main(sys.argv[1])
