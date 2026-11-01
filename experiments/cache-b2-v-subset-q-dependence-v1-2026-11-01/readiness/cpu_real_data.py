"""Real-archive CPU rehearsal for CFM-B2 (no model): selection, sources and the run's own 8-cell conv assembly on all
12 inputs. CUDA_VISIBLE_DEVICES= python readiness/cpu_real_data.py OUT_JSON"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import b2_run as V  # noqa: E402
import b2_core as K  # noqa: E402
import torch  # noqa: E402


def main(out):
    sel = V.selection()
    res, ok = {}, True
    for item in V.items():
        iid = item['id']
        _, old = V.CO.load_old(iid)
        cf_rec, _, _ = V.cf_assets(iid)
        H, R = K.partition(sel[iid]['H'])
        r = {'n_H': len(H), 'n_R': len(R), 'endpoints_present': all(c in cf_rec['cells'] for c in K.ENDPOINT.values()),
             'H_layers': sorted({l for l, _ in H})}
        checks = []
        for cell in K.CELLS:
            ov = V.conv_overrides(old, cell, H)
            for l in K.G:
                key = f'{l}:conv_states'
                fT, fC = old['deep']['T'][key], old['deep']['C'][key]
                o = ov[key]
                qd = fT if cell[0] == '1' else fC
                checks.append(torch.equal(o[:, :4096], qd[:, :4096]))
                for j in range(K.NV):
                    a = 4096 + 128 * j
                    src = fT if K.donor_of(l, j, cell, H) == 'T' else fC
                    checks.append(torch.equal(o[:, a:a + 128], src[:, a:a + 128]))
                if cell in K.ENDPOINT:
                    vd = fT if cell[1] == '1' else fC
                    checks.append(torch.equal(o, V.CFK.assemble(qd, vd)))
        r['assembly_ok'] = all(checks)
        r['passed'] = r['n_H'] == 45 and r['n_R'] == 403 and r['endpoints_present'] and r['assembly_ok']
        ok &= r['passed']
        res[iid] = r
        del old
    value = {'passed': ok, 'n_items': len(res), 'items': res, 'model_calls': 0}
    with open(out, 'x') as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': ok, 'n_items': len(res)}))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
