"""CGV-01 CPU readiness (no weights): torch kernel path; assets manifest hashes (G2 ledger passed, mu_all, random u, QCO offsets); NQ scenario
calibrations hold residual_scales['12'] (G1 reuses them); SRU formal passed and its record for the bridge input exists; held-out ledger.
CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import cgv_run as R  # noqa: E402


def main(out):
    ki = R.kernel_identity()
    man = R.assets()
    cal = {s: R.QCR.nq_calibration(f'{s}-ABC-A')[0] for s in ('NQ01', 'NQ02', 'NQ03', 'NQ04', 'NQ05', 'NQ06')}
    sru = R.SRUR_records()
    res = {'kernel_identity': ki, 'assets': man, 'l12_scales': {s: c['residual_scales']['12'] for s, c in cal.items()},
           'sru_formal_passed': R.exp.read(R.SRU_FORMAL / 'verification.json')['status'] == 'passed', 'bridge_record': R.BRIDGE_ITEM in sru,
           'n_ledger': len(R.ledger()), 'n_g2': len(R.g2_ledger()), 'formal_limits': R.limits('formal'), 'preflight_limits': R.limits('preflight'),
           'prep_limits': R.limits('prep')}
    ok = not (ki['fla'] or ki['kernels'] or ki['causal_conv1d']) and man['g2_status'] == 'passed' and all('12' in c['residual_scales'] for c in cal.values()) \
        and res['sru_formal_passed'] and res['bridge_record'] and res['n_ledger'] == 48 and res['n_g2'] == 27
    res['passed'] = bool(ok)
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in res.items() if k != 'assets'}))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
