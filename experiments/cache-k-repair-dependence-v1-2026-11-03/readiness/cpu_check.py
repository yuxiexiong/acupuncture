"""KRD-01 CPU readiness (no weights): torch kernel path; QSR formal verification passed; QKD-r02 records/tensors (C route anchors: M and
bf16 t2 logits for 6 arms x 4 directions); natural references with ids/termination/first hashes for all 6 arms (QKF old directions,
QKD C1343); F first token present and non-stop; r_post manifests; formation-token budget re-summed (6375 / 265).
CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import krd_run as R  # noqa: E402


def main(out):
    import torch
    ki = R.kernel_identity()
    qkf, qco, qkd = R.qkf_traj(), R.QKFR.qco_traj(), R.qkd_records()
    rp, rc = R.exp.read(R.QKFR.RPOST_MANIFEST), R.exp.read(R.QKDR.RPOST_C_MANIFEST)
    qv = R.exp.read(R.QSR_FORMAL / 'verification.json')
    res = {'kernel_identity': ki, 'qsr_formal_passed': qv['status'] == 'passed',
           'qkf_rpost_match': R.exp.sha(R.QKFR.RPOST_PT) == rp['rpost_sha256'],
           'qkd_rpost_c_match': rc['status'] == 'passed' and R.exp.sha(R.QKDR.RPOST_C) == rc['rpost_sha256'], 'n_qkd': len(qkd), 'items': {}}
    tf = sum(qkd[t['id']]['counts']['formation_token_forwards'] for t in R.items())
    tp = sum(qkd[a]['counts']['formation_token_forwards'] for a in R.PREFLIGHT_ITEMS)
    res['formation_tokens'] = {'formal': tf, 'preflight': tp, 'match': tf == R.LIMITS['formal']['formation_token_forwards'] and tp == R.LIMITS['preflight']['formation_token_forwards']}
    ok = not (ki['fla'] or ki['kernels'] or ki['causal_conv1d']) and res['qsr_formal_passed'] and res['qkf_rpost_match'] and res['qkd_rpost_c_match'] \
        and len(qkd) == 48 and res['formation_tokens']['match']
    for t in R.items():
        a = t['id']
        r = qkd[a]
        tt = torch.load(r['_tensor_path'], map_location='cpu')
        refs = {(arm, d): (qkf[a][f'{R.QKF_NAME[arm]}|{d}'] if d in R.OLD_DIRS else r['c1343_trajectories'][arm]) for arm in R.ARMS for d in R.DIRECTIONS}
        fF = {d: (qkf[a][f'F|{d}']['ids'] if d in R.OLD_DIRS else qco[a][f'F|{d}']['ids']) for d in R.DIRECTIONS}
        x = {'qkd_M': all('M' in r['arms'][d][arm] for d in R.DIRECTIONS for arm in R.ARMS),
             'qkd_t2_logits': all(f'Ct2|{arm}|{d}' in tt for d in R.DIRECTIONS for arm in R.ARMS),
             'refs_complete': all(v.get('ids') and v.get('termination') in ('stop', 'budget') and 'logits_sha256' in v['first'] and 'cache_sha256' in v['first']
                                  and len(v['ids']) <= R.MAX_NEW for v in refs.values()),
             'f_first_token': all(fF[d] and fF[d][0] not in R.STOP for d in R.DIRECTIONS)}
        x['n_first_token_stop'] = sum(1 for v in refs.values() if v['ids'][0] in R.STOP)
        x['passed'] = all(v for k, v in x.items() if k != 'n_first_token_stop')
        ok &= x['passed']
        res['items'][a] = x
        del tt
    res['n_first_token_stop_total'] = sum(v['n_first_token_stop'] for v in res['items'].values())
    res['passed'] = bool(ok)
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in res.items() if k != 'items'}))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
