"""Real-archive CPU rehearsal (no model, no CUDA): runs the exact lr_core functions the GPU run uses on the 12 archived
bridge inputs for background M, and checks every archived field the run will read exists with the expected shape.
N needs the shadow score (GPU) and is covered by preflight.

CUDA_VISIBLE_DEVICES= python readiness/cpu_real_data.py OUT_JSON
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import local_readout as LR  # noqa: E402
import lr_core as K  # noqa: E402
import torch  # noqa: E402

torch.set_num_threads(4)


def main(out):
    res = {'items': {}, 'model_calls': 0}
    for item in LR.items():
        rec_old, old = LR.CO.load_old(item['id'])           # verifies bridge record + tensor sha256
        sd, ex = old['score_drivers'], old['score_extras']
        L13 = LR.LAYER
        need = {'deep.C.13:recurrent_states': old['deep']['C'][f'{L13}:recurrent_states'],
                'deep.C.13:conv_states': old['deep']['C'][f'{L13}:conv_states'],
                'deep.T.13:recurrent_states': old['deep']['T'][f'{L13}:recurrent_states'],
                'extras.T_native.13:in': ex['T_native'][f'{L13}:in'], 'extras.Y_T.13:in': ex['Y_T'][f'{L13}:in']}
        shapes = {k: list(v.shape) for k, v in need.items()}
        assert all(f'{i}:in' in ex['T_native'] for i in range(L13, 32)), 'T_native deep residual entries missing'
        assert all(i in sd['T_native'] and i in sd['Y_T'] for i in LR.B.G_REAL), 'archived drivers missing'
        assert 'C' in rec_old['scores'] and 'T_native' in rec_old['scores'] and 'Y_T' in rec_old['scores']
        fm = K.four_cells(old['deep']['C'][f'{L13}:recurrent_states'][0], old['deep']['T'][f'{L13}:recurrent_states'][0],
                          sd['C'][L13], sd['Y_T'][L13])
        core = sd['Y_T'][L13]['core']
        num = {}
        for name, d in (('I', fm['I']), ('J', fm['J']),
                        ('Q0', K.match_heads(K.unit_dirs(item['id'], 0), fm['I'])),
                        ('Q1', K.match_heads(K.unit_dirs(item['id'], 1), fm['I']))):
            new = K.patch_core(core, d)
            num[name] = K.realized(core, new, d)
            num[name]['decidable'] = num[name]['rel_err'] <= K.TOL['deletion_rel']
        zero = torch.equal(K.patch_core(core, torch.zeros_like(fm['I'])), core)
        addback = torch.equal(K.patch_core(core, fm['I'], addback=True), core)
        res['items'][item['id']] = {
            'shapes': shapes, 'identity_ok': fm['identity_ok'], 'identity_abs': fm['identity_abs'],
            'recon': {'o11_vs_Y_T_core': K.core_recon(fm['o11'], core), 'o00_vs_C_core': K.core_recon(fm['o00'], sd['C'][L13]['core'])},
            'norms': fm['norms'], 'cos_I_vs_AS_plus_AF': fm['cos_I_vs_AS_plus_AF'], 'core_norm': float(core.double().norm()),
            'patch': num, 'zero_bitwise': zero, 'addback_bitwise': addback,
            'entry_M_eq_C': bool(torch.equal(ex['C'][f'{L13}:in'], ex['Y_T'][f'{L13}:in'])),
            'entry_M_ne_N': not torch.equal(ex['Y_T'][f'{L13}:in'], ex['T_native'][f'{L13}:in']),
            'D': {k: rec_old['scores'][k]['stop_advantage'] for k in ('C', 'Y_T', 'T_native')}}
        del old
    it = res['items'].values()
    res['passed'] = all(v['identity_ok'] and max(v['recon'].values()) <= K.TOL['core_recon_rel'] and v['zero_bitwise']
                        and v['addback_bitwise'] and v['entry_M_eq_C'] and v['entry_M_ne_N']
                        and all(p['decidable'] for p in v['patch'].values()) for v in it)
    res['n_items'] = len(res['items'])
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'passed': res['passed'], 'n_items': res['n_items']}))
    sys.exit(0 if res['passed'] else 1)


if __name__ == '__main__':
    main(sys.argv[1])
