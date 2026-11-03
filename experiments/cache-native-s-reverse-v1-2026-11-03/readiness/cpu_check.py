"""NSR-01 CPU readiness: torch kernel path; NCC-01 formal passed with 48 records holding C / T results and t1 tensors for both needles;
LVK formation hashes for every donor; donor map is a within-scenario permutation; plan doc present.
CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import nsr_run as R  # noqa: E402


def main(out):
    import torch
    ki = R.kernel_identity()
    nc, lv, dm = R.ncc_records(), R.SRUR.lvk_records(), R.donor_map()
    miss = 0
    for a, r in nc.items():
        t = torch.load(r['_tensor_path'], map_location='cpu')
        miss += sum(int(k not in t) for k in ('t1|C', f't1|{R.L0}|T', f't1|{R.L12}|T'))
        miss += int('C' not in r['results'] or any('T' not in r['results'][d] for d in R.NEEDLES))
        miss += int('C_b' not in lv[dm[a]]['formation_hashes'])
        del t
    docs = {str(p.relative_to(R.REPO)): p.exists() for p in R.PLAN_DOCS}
    res = {'kernel_identity': ki, 'n_ncc': len(nc), 'missing': miss, 'donor_permutation': sorted(dm.values()) == sorted(dm), 'plan_docs': docs,
           'ncc_verification': R.exp.read(R.NCC_FORMAL / 'verification.json')['status']}
    res['passed'] = bool(not (ki['fla'] or ki['kernels'] or ki['causal_conv1d']) and len(nc) == 48 and miss == 0 and res['donor_permutation']
                         and all(docs.values()) and res['ncc_verification'] == 'passed')
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(res))
    sys.exit(0 if res['passed'] else 1)


if __name__ == '__main__':
    main(sys.argv[1])
