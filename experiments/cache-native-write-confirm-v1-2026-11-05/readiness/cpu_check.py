"""NWC-01 r02 CPU readiness (no weights): torch kernel path; frozen SRU / LVK and NWR-01 source trees unchanged; panel ledger passed and matches
the frozen input file; NWR-01 formal passed and holds the two bridge inputs with all 12 arms; calibration and offset vectors exist for every
family and direction.   CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import nwc_run as R  # noqa: E402


def main(out):
    ki = R.kernel_identity()
    led, nwr = R.nwc_ledger(), R.nwr_records()
    tree = {}
    for name, fn, path in (('sru_lvk', R.S.check_freeze, R.N.SRU_DIR / 'freeze-r01.json'), ('nwr', R.N.check_freeze, R.NWR_DIR / 'freeze-r01.json')):
        try:
            fn(path)
            tree[name] = True
        except AssertionError:
            tree[name] = False
    vecs = R.load_vectors()
    _, u, _ = R.ARMS_ALL['Rk']
    fams = sorted({v['plan']['base_id'] for v in led.values()})
    cal, vec = True, True
    for f in fams:
        try:
            R.QCR.nq_calibration(f'{f}-ABC-A')
        except KeyError:
            cal = False
        vec &= all(f'{f}|{d}' in vecs[u] for d in R.DIRS3)
    bridge = all(k in nwr and set(nwr[k]['arms']) == set(R.N.ARMS) and nwr[k]['direction'] == R.BRIDGE_DIR for k in R.BRIDGE_ITEMS)
    res = {'kernel_identity': ki, 'hook_target': hasattr(R.gdn_module(), 'torch_recurrent_gated_delta_rule'), 'trees_unchanged': tree,
           'nwr_formal_passed': R.exp.read(R.NWR_FORMAL / 'verification.json')['status'] == 'passed', 'n_ledger': len(led),
           'strata': {s: sum(1 for v in led.values() if v['plan']['stratum'] == s) for s in ('N', 'F')}, 'families': fams,
           'calibration_for_every_family': cal, 'offset_vectors_for_every_family_direction': vec, 'bridge_inputs_in_nwr': bridge,
           'ledger_failures': sum(1 for v in led.values() if v['failures'])}
    ok = (not (ki['fla'] or ki['kernels'] or ki['causal_conv1d']) and res['hook_target'] and all(tree.values()) and res['nwr_formal_passed']
          and len(led) == 72 and res['strata'] == {'N': 48, 'F': 24} and len(fams) == 6 and cal and vec and bridge and res['ledger_failures'] == 0)
    res['passed'] = bool(ok)
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(res, ensure_ascii=False))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
