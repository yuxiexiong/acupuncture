"""QCO-01 CPU readiness (no weights): QST design inputs; QCD G records for all 48 texts carry base_b/C_b/T_b hashes; QST formal
records hold the 624 reference trajectories (C, T_nat, V = H_T(a,a), F = H_C(a,a)); NQ calibrations; NumPy PCG64 available.
CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import qco_run as R  # noqa: E402


def main(out):
    import numpy as np
    qst = R.qst_traj()
    res, ok = {'items': {}}, True
    for t in R.items():
        a = t['id']
        g = R.QSTR._g_record(a)
        need = [f'U|-|{a}|{a}'] + [f'{x}|{d}|{a}|{a}' for d in R.DIRECTIONS for x in ('T_nat', 'H_T', 'H_C')]
        x = {'qcd_hashes': all(k in g['hashes'] for k in ['base_b', 'C_b'] + [f'T_b|{d}' for d in R.DIRECTIONS]),
             'qst_refs': all(k in qst for k in need), 'calibration': bool(R.QCR.nq_calibration(f"{t['plan']['base_id']}-ABC-A")[0])}
        x['passed'] = all(x.values())
        ok &= x['passed']
        res['items'][a] = x
    res['numpy'] = np.__version__
    res['pcg64'] = float(np.random.Generator(np.random.PCG64(1)).standard_normal())
    res['n'] = len(res['items'])
    ok &= res['n'] == 48
    res['passed'] = bool(ok)
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': res['passed'], 'n': res['n'], 'numpy': res['numpy']}))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
