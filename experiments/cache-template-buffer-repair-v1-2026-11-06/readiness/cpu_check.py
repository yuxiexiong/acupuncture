"""FBR-01 CPU readiness (no weights): torch kernel path; frozen SRU / LVK, NWR-01 and NWC-01 source trees unchanged; LVK-01 formal passed and its
new-panel records hold the C_clean, L00 and F arms with t1 tensors for all four directions; offset vectors and calibrations exist.
CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import fbr_run as R  # noqa: E402


def main(out):
    import torch
    ki = R.kernel_identity()
    led, lv = R.LVKR.ledger(), R.lvk_records()
    tree = {}
    for name, fn, path in (('sru_lvk', R.S.check_freeze, R.N.SRU_DIR / 'freeze-r01.json'), ('nwr', R.N.check_freeze, R.W.NWR_DIR / 'freeze-r01.json'),
                           ('nwc', R.W.check_freeze, R.NWC_DIR / 'freeze-r03.json')):
        try:
            fn(path)
            tree[name] = True
        except AssertionError:
            tree[name] = False
    vecs = R.load_vectors()
    _, u, _ = R.ARMS_ALL['Rk']
    scen = sorted({v['plan']['base_id'] for v in led.values()})
    vec = all(f'{s}|{d}' in vecs[u] for s in scen for d in R.DIRS)
    cal = True
    for s in scen:
        try:
            R.QCR.nq_calibration(f'{s}-ABC-A')
        except KeyError:
            cal = False
    arms, f_correct = True, {d: 0 for d in R.DIRS}
    for a in led:
        r = lv[a]
        tt = torch.load(r['_tensor_path'], map_location='cpu')
        arms &= 't1|C|all' in tt and bool(r['directions']['C_clean']['N']['ids'])
        for d in R.DIRS:
            x = r['directions'][d]['arms']
            arms &= all(k in x and bool(x[k]['N']['ids']) for k in ('L00', 'F')) and all(f't1|{k}|{d}' in tt for k in ('L00', 'F'))
            f_correct[d] += int(x['F']['N']['text'].replace('<|im_end|>', '').strip() == r['item']['target'])
        del tt
    res = {'kernel_identity': ki, 'trees_unchanged': tree, 'lvk_formal_passed': R.exp.read(R.LVK_FORMAL / 'verification.json')['status'] == 'passed',
           'n_ledger': len(led), 'n_lvk_new': len(lv), 'scenarios': scen, 'lvk_arms_and_tensors': bool(arms), 'lvk_F_strict_correct': f_correct,
           'offset_vectors': vec, 'calibrations': cal}
    ok = (not (ki['fla'] or ki['kernels'] or ki['causal_conv1d']) and all(tree.values()) and res['lvk_formal_passed'] and len(led) == len(lv) == 48
          and len(scen) == 6 and arms and vec and cal)
    res['passed'] = bool(ok)
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(res, ensure_ascii=False))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
