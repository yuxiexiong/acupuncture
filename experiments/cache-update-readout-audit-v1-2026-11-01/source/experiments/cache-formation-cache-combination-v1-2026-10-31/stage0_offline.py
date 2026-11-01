"""Stage 0 (CPU, descriptive only): how the old recurrent-state crossings J differ from their receivers inside the
scoring step, using the bridge formal-r01 score_drivers / score_extras. Not a gate for stage A; no model forward.

python stage0_offline.py OUT.json
"""
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

J_PAIRS = (('J_T_SU', 'Y_T'), ('J_U_ST', 'Y_U'), ('J_W_SH', 'Y_W'), ('J_H_SW', 'Y_H'))


def norm(x):
    return float(x.float().norm())


def cos(a, b):
    import torch
    a, b = a.float().reshape(-1), b.float().reshape(-1)
    na, nb = float(a.norm()), float(b.norm())
    return None if na < 1e-12 or nb < 1e-12 else float(torch.dot(a, b) / (na * nb))


def compare(drivers, extras, j, rcv, deep_layers):
    dj, dr = drivers[j], drivers[rcv]
    out = {'G': {}, 'residual': {}}
    for layer in sorted(dr):
        a, b = dj[layer], dr[layer]
        d_old, d_new, d_core = a['old'] - b['old'], a['new'] - b['new'], a['core'].float() - b['core'].float()
        out['G'][str(layer)] = {'d_old': norm(d_old), 'd_new': norm(d_new), 'd_core': norm(d_core),
                                'old_rcv': norm(b['old']), 'new_rcv': norm(b['new']), 'core_rcv': norm(b['core']),
                                'cos_dold_dcore': cos(d_old, d_core), 'd_z': norm(a['z'].float() - b['z'].float())}
    ej, er = extras[j], extras[rcv]
    for i in deep_layers:
        din = ej[f'{i}:in'].float() - er[f'{i}:in'].float()
        dout = ej[f'{i}:out'].float() - er[f'{i}:out'].float()
        out['residual'][str(i)] = {'d_in': norm(din), 'd_out': norm(dout), 'd_own_contribution': norm(dout - din)}
    out['final_h'] = norm(ej['final:h'].float() - er['final:h'].float())
    return out


def analyse_tensor(t, rec, deep_layers):
    s = rec['scores']
    res = {}
    for j, rcv in J_PAIRS:
        c = compare(t['score_drivers'], t['score_extras'], j, rcv, deep_layers)
        c['dD'] = s[j]['stop_advantage'] - s[rcv]['stop_advantage']
        res[f'{j}|{rcv}'] = c
    return res


def main():
    import torch
    sys.path.insert(0, str(HERE.parent / 'early-input-control-v1-2026-10-29'))
    import combo as CB
    p = argparse.ArgumentParser()
    p.add_argument('out')
    a = p.parse_args()
    out = {'source': 'bridge formal-r01 (ef4fe2a) score_drivers/score_extras; descriptive only', 'items': {}}
    for item_id, (rec_path, t_path, t_sha, r_sha) in sorted(CB.bridge_assets().items()):
        assert CB.exp.sha(t_path) == t_sha and CB.exp.sha(rec_path) == r_sha
        t = torch.load(t_path, map_location='cpu', weights_only=True)
        rec = CB.exp.read(rec_path)
        out['items'][item_id] = analyse_tensor(t, rec, range(13, 32))
        del t
    CB.exp.write(Path(a.out), out, immutable=True)
    print(json.dumps({'items': len(out['items'])}))


if __name__ == '__main__':
    main()
