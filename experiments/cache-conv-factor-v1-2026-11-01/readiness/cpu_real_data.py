"""Real-archive CPU rehearsal for CFM-CONV-FACTOR v1 (no model, no CUDA). Runs the run's own assembly and random
displacement code on all 12 archived inputs and checks every archived field / replay reference the run will read.

CUDA_VISIBLE_DEVICES= python readiness/cpu_real_data.py OUT_JSON
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import conv_factor as CF  # noqa: E402
import cf_core as K  # noqa: E402
import torch  # noqa: E402

torch.set_num_threads(4)


def main(out):
    d = CF.design()
    G = CF.B.G_REAL
    res, ok = {}, True
    for item in CF.items():
        iid = item['id']
        rec_old, old = CF.CO.load_old(iid)
        crec, _ = CF.combo_record(iid)
        r = {'a_matches_bridge_C_nonstop': d['clean_candidate_ids'][iid] == rec_old['scores']['C']['nonstop_winner'],
             'combo_corners_present': all(f'S={s},F={f},K=T' in crec['scores'] for s in 'CT' for f in 'CT'),
             'x_t_present': f'{CF.SPLIT}:in' in old['score_extras']['T_native']}
        asm = {}
        for i in G:
            key = f'{i}:conv_states'
            fc, ft = old['deep']['C'][key], old['deep']['T'][key]
            assert tuple(ft.shape) == (1, 8192, 4), ft.shape
            asm[i] = torch.equal(K.assemble(ft, ft), ft) and torch.equal(K.assemble(fc, ft)[:, 4096:], ft[:, 4096:]) \
                and torch.equal(K.assemble(fc, ft)[:, :4096], fc[:, :4096])
        r['assembly_ok'] = all(asm.values())
        rnd = {}
        for part in ('Q', 'V'):
            for j in (0, 1):
                _, checks = CF.random_overrides(old, iid, part, j, G)
                rnd[f'{part}{j}'] = {'all_ok': all(v['ok'] for v in checks.values()),
                                     'max_rel_err': max(v['rel_err'] for v in checks.values()),
                                     'cos_with_clean_median': sorted(v.get('cos_with_clean_dir', 0.0) for v in checks.values())[len(checks) // 2]}
        r['random'] = rnd
        cz = lambda k: crec['scores'][k]['stop_advantage']   # noqa: E731
        r['known_G_D'] = {'G_T': cz('S=T,F=T,K=T') - cz('S=T,F=C,K=T'), 'G_C': cz('S=C,F=T,K=T') - cz('S=C,F=C,K=T')}
        r['passed'] = r['a_matches_bridge_C_nonstop'] and r['combo_corners_present'] and r['x_t_present'] and r['assembly_ok'] \
            and all(v['all_ok'] for v in rnd.values())
        ok &= r['passed']
        res[iid] = r
        del old
    value = {'passed': ok, 'n_items': len(res), 'items': res, 'model_calls': 0}
    with open(out, 'x') as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'passed': ok, 'n_items': len(res)}))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
