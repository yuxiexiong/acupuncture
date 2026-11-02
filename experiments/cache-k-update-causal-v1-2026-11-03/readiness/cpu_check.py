"""KUC-01 CPU readiness (no weights): torch kernel and conv paths (no fla / hub kernels / causal_conv1d package); module functions to be
hooked exist; KRD r02 formal and KHC freeze present; QKD anchors and natural references complete for the five original endpoints; formation
tokens re-summed (6375 / 265).  CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import kuc_run as R  # noqa: E402


def main(out):
    import torch
    ki = R.kernel_identity()
    QM = R.gdn_module()
    qkf, qco, qkd, krd = R.qkf_traj(), R.QKFR.qco_traj(), R.qkd_records(), R.krd_records()
    res = {'kernel_identity': ki, 'hook_targets': all(hasattr(QM, n) for n in ('causal_conv1d_update', 'torch_recurrent_gated_delta_rule', 'l2norm')),
           'krd_formal_passed': R.exp.read(R.KRD_FORMAL / 'verification.json')['status'] == 'passed', 'khc_freeze': (R.KHC_DIR / 'freeze-r01.json').exists(),
           'n_qkd': len(qkd), 'n_krd': len(krd), 'items': {}}
    tf = sum(qkd[t['id']]['counts']['formation_token_forwards'] for t in R.items())
    tp = sum(qkd[a]['counts']['formation_token_forwards'] for a in R.PREFLIGHT_ITEMS)
    res['formation_tokens'] = {'formal': tf, 'preflight': tp, 'match': tf == 6375 and tp == 265}
    ok = not (ki['fla'] or ki['kernels'] or ki['causal_conv1d']) and res['hook_targets'] and res['krd_formal_passed'] and res['khc_freeze'] \
        and len(qkd) == 48 and len(krd) == 48 and res['formation_tokens']['match']
    for t in R.items():
        a = t['id']
        r = qkd[a]
        tt = torch.load(r['_tensor_path'], map_location='cpu')
        refs = {(arm, d): (qkf[a][f'{R.QKF_NAME[arm]}|{d}'] if d in R.OLD_DIRS else r['c1343_trajectories'][arm]) for arm in R.ORIG for d in R.DIRECTIONS}
        x = {'qkd_M': all('M' in r['arms'][d][arm] for d in R.DIRECTIONS for arm in R.ORIG),
             'qkd_t2_logits': all(f'Ct2|{arm}|{d}' in tt for d in R.DIRECTIONS for arm in R.ORIG),
             'refs_complete': all(v.get('ids') and v.get('termination') in ('stop', 'budget') and 'logits_sha256' in v['first'] and 'cache_sha256' in v['first']
                                  for v in refs.values()),
             'krd_x': all(krd[a]['directions'][d]['x'][arm] == refs[(arm, d)]['ids'][0] for arm in R.ORIG for d in R.DIRECTIONS),
             'f_first_token': all((qkf[a][f'F|{d}']['ids'] if d in R.OLD_DIRS else qco[a][f'F|{d}']['ids'])[0] not in R.STOP for d in R.DIRECTIONS)}
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
