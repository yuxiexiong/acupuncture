"""NMT-01 CPU readiness: torch kernel path; NVB formal (48 records, t1 / C logits for 8 cells x 4 directions, natural records); SIT formal
(48 records, C logits and natural records for the 4 cross cells); NBR formal tensors hold XA / g / state for every direction; plan docs.
CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import nmt_run as R  # noqa: E402


def main(out):
    import torch
    ki = R.kernel_identity()
    nv, sv = R.SITR.nvb_records(), R.sit_records()
    ok = not (ki['fla'] or ki['kernels'] or ki['causal_conv1d']) and len(nv) == 48 and len(sv) == 48
    ok &= R.exp.read(R.SIT_FORMAL / 'verification.json')['status'] == 'passed'
    miss = {'nvb_tensors': 0, 'nvb_natural': 0, 'sit_tensors': 0, 'sit_natural': 0, 'nbr_tensors': 0}
    for a in nv:
        t = torch.load(nv[a]['_tensor_path'], map_location='cpu')
        miss['nvb_tensors'] += sum(1 for d in R.DIRECTIONS for c in R.MAIN for k in ('t1', 'C') if f'{k}|{c}|{d}' not in t)
        miss['nvb_natural'] += sum(1 for d in R.DIRECTIONS for c in R.MAIN if 'reached_t2' not in nv[a]['directions'][d]['cells'][c]['N'])
        del t
        t = torch.load(sv[a]['_tensor_path'], map_location='cpu')
        miss['sit_tensors'] += sum(1 for d in R.DIRECTIONS for c in R.SIT_CELLS if f'C|{c}|{d}' not in t)
        miss['sit_natural'] += sum(1 for d in R.DIRECTIONS for c in R.SIT_CELLS if 'reached_t2' not in sv[a]['directions'][d]['new'][c]['N'])
        del t
    nbr = R.NBR_DIR / 'runs/formal-r01'
    n_nbr = 0
    for w in sorted(nbr.glob('worker-*')):
        if not w.is_dir():
            continue
        for tf in sorted((w / 'tensors').glob('*.pt')):
            t = torch.load(tf, map_location='cpu')
            n_nbr += 1
            need = [f'state|{d}' for d in R.DIRECTIONS] + [f'XA|{s}|{r}|{b}|{d}' for s in '01' for r in '01' for b in '01' for d in R.DIRECTIONS]
            need += [f'g|{c}|{d}' for c in R.MAIN for d in R.DIRECTIONS]
            miss['nbr_tensors'] += sum(1 for k in need if k not in t)
            del t
    docs = {str(p.relative_to(R.REPO)): p.exists() for p in R.PLAN_DOCS}
    res = {'kernel_identity': ki, 'n_nvb': len(nv), 'n_sit': len(sv), 'n_nbr_tensor_files': n_nbr, 'missing': miss, 'plan_docs': docs}
    res['passed'] = bool(ok and n_nbr == 48 and not any(miss.values()) and all(docs.values()))
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(res))
    sys.exit(0 if res['passed'] else 1)


if __name__ == '__main__':
    main(sys.argv[1])
