"""Real-archive CPU rehearsal for CFM-VQ-WRITE-L13-v1 (no model, no CUDA): the run's own I13 algebra and patch
precision gates on all 12 archived inputs x 2 backgrounds, plus every source field the run will read.

CUDA_VISIBLE_DEVICES= python readiness/cpu_real_data.py OUT_JSON
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import vq_write as V  # noqa: E402
import vqw_core as K  # noqa: E402
import torch  # noqa: E402

torch.set_num_threads(4)


def main(out):
    res, ok = {}, True
    d = V.CF.design()
    for item in V.items():
        iid = item['id']
        rec_old, old = V.CO.load_old(iid)
        cf_rec, cft, _ = V.cf_assets(iid)
        r = {'a_match': d['clean_candidate_ids'][iid] == cf_rec['a_token'],
             'x_t_present': f'{V.LAYER}:in' in old['score_extras']['T_native'],
             'base_cells_present': all(V.BASE[bg] in cf_rec['cells'] for bg in V.BASE)}
        for bg in ('M_T', 'N'):
            I, chk, core = V.interaction_inputs(old, cft, bg)
            ps = {}
            for name, dl in (('DEL', I), ('RAND0', K.random_like(iid, 0, I)), ('RAND1', K.random_like(iid, 1, I))):
                p = K.precision(core, dl)
                ps[name] = {k: v for k, v in p.items() if k != 'new_core'}
            zero = torch.equal(K.patch_core(core, torch.zeros_like(I)), core)
            addb = torch.equal(K.patch_core(core, I, addback=True), core)
            r[bg] = {'I13_norm': float(I.norm()), 'core_norm': float(core.double().norm()),
                     'checks': {k: v for k, v in chk.items() if k != 'core_recon'},
                     'core_recon_max_ratio': max(v['ratio'] for v in chk['core_recon'].values()),
                     'precision': ps, 'zero_bitwise': zero, 'addback_bitwise': addb}
            r[bg]['passed'] = (chk['g_beta_z_shared'] and chk['qk_depend_only_on_Q'] and chk['v_depends_only_on_V']
                               and chk['product_identity_ok'] and chk['read_interaction_ok'] and chk['core_recon_ok']
                               and all(v['ok'] for v in ps.values()) and zero and addb)
        r['passed'] = r['a_match'] and r['x_t_present'] and r['base_cells_present'] and r['M_T']['passed'] and r['N']['passed']
        ok &= r['passed']
        res[iid] = r
        del old, cft
    value = {'passed': ok, 'n_items': len(res), 'items': res, 'model_calls': 0}
    with open(out, 'x') as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'passed': ok, 'n_items': len(res)}))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
