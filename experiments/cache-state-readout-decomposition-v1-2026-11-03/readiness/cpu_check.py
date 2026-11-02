"""QSR-01 CPU readiness (no weights): kernel identity (torch path); QKD-r02 formal records: 48 texts, M for 6 arms x 4 directions,
saved t2 bf16 logits per arm/direction, record and tensor hashes; QKF/QCO references for t1 anchors and F first tokens; r_post manifests;
inherited error threshold == QKD readouts formal threshold; formation-token budget re-summed from the QKD records (formal 6375,
preflight 265).  CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import qsr_run as R  # noqa: E402


def main(out):
    import torch
    ki = R.kernel_identity()
    qkf, qco, qkd = R.qkf_traj(), R.QKFR.qco_traj(), R.qkd_records()
    rp = R.exp.read(R.QKFR.RPOST_MANIFEST)
    rc = R.exp.read(R.QKDR.RPOST_C_MANIFEST)
    thr, e_pre = R.qkd_err_threshold()
    rd = R.exp.read(R.QKD_DIR / 'analysis/qkd-readouts-r02.json')
    res = {'kernel_identity': ki, 'qkf_rpost_match': R.exp.sha(R.QKFR.RPOST_PT) == rp['rpost_sha256'],
           'qkd_rpost_c_match': rc['status'] == 'passed' and R.exp.sha(R.QKDR.RPOST_C) == rc['rpost_sha256'],
           'threshold': thr, 'threshold_matches_qkd_readouts': thr == rd['error']['formal_threshold'], 'n_qkd': len(qkd), 'items': {}}
    tok_formal = sum(qkd[t['id']]['counts']['formation_token_forwards'] for t in R.items())
    tok_pre = sum(qkd[a]['counts']['formation_token_forwards'] for a in R.PREFLIGHT_ITEMS)
    res['formation_tokens'] = {'formal': tok_formal, 'preflight': tok_pre,
                               'match_limits': tok_formal == R.LIMITS['formal']['formation_token_forwards'] and tok_pre == R.LIMITS['preflight']['formation_token_forwards']}
    ok = (not ki['fla'] and not ki['kernels'] and not ki['causal_conv1d']) and res['qkf_rpost_match'] and res['qkd_rpost_c_match'] \
        and res['threshold_matches_qkd_readouts'] and len(qkd) == 48 and res['formation_tokens']['match_limits']
    for t in R.items():
        a = t['id']
        r = qkd[a]
        tt = torch.load(r['_tensor_path'], map_location='cpu')
        fF = {d: (qkf[a][f'F|{d}']['ids'] if d in R.OLD_DIRS else qco[a][f'F|{d}']['ids']) for d in R.DIRECTIONS}
        x = {'qkd_M': all('M' in r['arms'][d][arm] for d in R.DIRECTIONS for arm in R.ARMS),
             'qkd_t2_logits': all(f'Ct2|{arm}|{d}' in tt for d in R.DIRECTIONS for arm in R.ARMS),
             'qkf_arms': all(f'{R.QKF_NAME[arm]}|{d}' in qkf[a] for arm in R.ARMS for d in R.OLD_DIRS),
             'c1343_first': all('first' in r['c1343_trajectories'][arm] for arm in R.ARMS),
             'f_first_token': all(fF[d] and fF[d][0] not in R.STOP for d in R.DIRECTIONS)}
        x['passed'] = all(x.values())
        ok &= x['passed']
        res['items'][a] = x
        del tt
    res['passed'] = bool(ok)
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in res.items() if k != 'items'}))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
