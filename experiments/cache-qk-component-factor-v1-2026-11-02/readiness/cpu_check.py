"""QKF-01 CPU readiness (no weights): QCO formal records for all 48 texts hold the replay arms (C, T_nat, V, F, R, A, R_rand,
A_rand) for the 3 directions; QCO offsets file matches its manifest; QCO collect tensors (base q/k for the r_post simulation)
hash-verify; QCD G hashes present.  CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import qkf_run as R  # noqa: E402


def main(out):
    qco = R.qco_traj()
    man = R.exp.read(R.QCO_MANIFEST)
    res = {'qco_offsets_match': R.exp.sha(R.QCO_OFFSETS_PT) == man['offsets_sha256'], 'items': {}}
    ok = res['qco_offsets_match']
    col = R.QCO_DIR / 'runs/collect-r01'
    n_col = 0
    for w in sorted(col.glob('worker-*')):
        if not w.is_dir():
            continue
        rc = R.exp.read(w / 'receipt.json')
        for rel, t in rc['tensor_hashes'].items():
            ok &= R.exp.sha(w / rel) == t
            n_col += 1
    res['collect_tensors'] = n_col
    ok &= n_col == 48
    for t in R.items():
        a = t['id']
        need = ['C|-'] + [f'{x}|{d}' for d in R.DIRECTIONS for x in ('T_nat', 'V', 'F', 'R', 'A', 'R_rand', 'A_rand')]
        g = R.QSTR._g_record(a)
        x = {'qco_refs': a in qco and all(k in qco[a] for k in need),
             'qcd_hashes': all(k in g['hashes'] for k in ['base_b', 'C_b'] + [f'T_b|{d}' for d in R.DIRECTIONS])}
        x['passed'] = all(x.values())
        ok &= x['passed']
        res['items'][a] = x
    res['passed'] = bool(ok)
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': res['passed'], 'n': len(res['items']), 'collect_tensors': n_col}))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
