"""SIT-01 CPU readiness: torch kernel path; NVB formal passed with 48 records whose tensors hold t1 / C logits for the 8 cells x 4 directions
and whose natural records exist for all 8 cells; NBR re-projection JSON present; plan documents present.
CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import sit_run as R  # noqa: E402


def main(out):
    import torch
    ki = R.kernel_identity()
    nv = R.nvb_records()
    ok = not (ki['fla'] or ki['kernels'] or ki['causal_conv1d']) and R.exp.read(R.NVB_FORMAL / 'verification.json')['status'] == 'passed' and len(nv) == 48
    miss, nmiss, stop = 0, 0, {c: 0 for c in R.MAIN}
    for a, r in nv.items():
        t = torch.load(r['_tensor_path'], map_location='cpu')
        miss += sum(1 for d in R.DIRECTIONS for c in R.MAIN for k in ('t1', 'C') if f'{k}|{c}|{d}' not in t)
        for d in R.DIRECTIONS:
            for c in R.MAIN:
                N = r['directions'][d]['cells'][c].get('N', {})
                nmiss += int(not (N.get('ids') and 'reached_t2' in N and 'termination' in N))
                stop[c] += int(not N.get('reached_t2', True))
        del t
    docs = {str(p.relative_to(R.REPO)): p.exists() for p in R.PLAN_DOCS}
    nbr = (R.HERE.parent / 'cache-native-bridge-record-v1-2026-11-03/analysis/nbr-reproject-r01.json').exists()
    res = {'kernel_identity': ki, 'n_nvb': len(nv), 'missing_tensors': miss, 'missing_natural': nmiss, 't1_stop_counts_nvb_all_directions': stop,
           'plan_docs': docs, 'nbr_reproject': nbr}
    res['passed'] = bool(ok and miss == 0 and nmiss == 0 and all(docs.values()) and nbr)
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(res))
    sys.exit(0 if res['passed'] else 1)


if __name__ == '__main__':
    main(sys.argv[1])
