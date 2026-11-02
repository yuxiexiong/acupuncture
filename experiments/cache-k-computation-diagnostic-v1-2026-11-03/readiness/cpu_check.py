"""QKD-01 CPU readiness (no weights): kernel identity (torch path, no FLA / Hub kernels / causal_conv1d); QKF formal records hold the
six arms for the three old directions; QCO formal records hold V/F for C1343 with two non-stop F tokens; QKF r_post manifest and QCO
offsets match; QCD G hashes present for the 4 directions.  CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import qkd_run as R  # noqa: E402


def main(out):
    ki = R.kernel_identity()
    qkf, qco = R.qkf_traj(), R.QKFR.qco_traj()
    rp = R.exp.read(R.QKFR.RPOST_MANIFEST)
    res = {'kernel_identity': ki, 'qkf_rpost_match': R.exp.sha(R.QKFR.RPOST_PT) == rp['rpost_sha256'], 'items': {}}
    ok = (not ki['fla'] and not ki['kernels'] and not ki['causal_conv1d']) and res['qkf_rpost_match']
    for t in R.items():
        a = t['id']
        g = R.QSTR._g_record(a)
        fids = qco[a]['F|N_L00_C1343_D-1']['ids']
        x = {'qkf_arms': all(f'{R.QKF_NAME[arm]}|{d}' in qkf[a] for arm in R.ARMS for d in R.OLD_DIRS),
             'qco_c1343': all(f'{arm}|N_L00_C1343_D-1' in qco[a] for arm in ('V', 'F')),
             'f_tokens': len(fids) >= 2 and fids[0] not in R.STOP and fids[1] not in R.STOP,
             'qcd_hashes': all(k in g['hashes'] for k in ['base_b', 'C_b'] + [f'T_b|{d}' for d in R.DIRECTIONS])}
        x['passed'] = all(x.values())
        ok &= x['passed']
        res['items'][a] = x
    res['passed'] = bool(ok)
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': res['passed'], 'n': len(res['items']), 'kernel': ki}))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
