"""B4 pre-registered shadow prediction (CONTRACT §5), computed on CPU from the B3 formal tensors BEFORE any B4 run:
h' = h_CFIX - sum_l W_l[:, nonFIX] (gno_CFIX - gno_CC)[nonFIX];  rho_shadow = (z(h') - z(h_CC)) / (z(h_CFIX) - z(h_CC)),
z(h) = u.h / sqrt(mean(h^2) + eps) with the stored FP64 stop readout vector.  Frozen downstream; not a fit to any B4 data.
CUDA_VISIBLE_DEVICES= python readiness/shadow.py OUT"""
import json
import math
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
P1_DIR = HERE.parent / 'cache-b3p1-early-alignment-v1-2026-11-01'
P0_DIR = HERE.parent / 'cache-b3p-energy-ledger-v1-2026-11-01'
sys.path.insert(0, str(P1_DIR))
sys.path.insert(0, str(P0_DIR))
import b4_core as K  # noqa: E402
import p1_weights as PW  # noqa: E402
import p0_run as P0  # noqa: E402


def z_of(h, u, eps):
    return float(u @ h) / math.sqrt(float((h * h).mean()) + eps)


def main(out):
    import torch
    units, ver = P0.load_units(P0.B3_DIR / 'runs/formal-r01')          # hash-checked B3 records + tensors
    W = PW.load_out_proj(P0.M.model_path(), K.G_LAYERS)
    res = {d: {} for d in K.DIRECTIONS}
    for rec, ten in units:
        iid = rec['item']['id']
        fix = {(x[0], x[1]) for x in rec['FIX']}
        u, eps = ten['readout_vectors']['stop'].double(), ten['readout_vectors']['eps']
        for d in K.DIRECTIONS:
            h_fix = ten['extras'][f'N:CFIX|{d}']['final:h'].double()
            h_cc = ten['extras'][f'N:CC|{d}']['final:h'].double()
            corr = torch.zeros_like(h_fix)
            for l in K.G_LAYERS:
                dg = (ten['counter'][f'N:CFIX|{d}'][f'{l}:gated_norm_out'].double()
                      - ten['counter'][f'N:CC|{d}'][f'{l}:gated_norm_out'].double()).reshape(K.NV, K.HD)
                for h in range(K.NV):
                    if (l, h) in fix:
                        dg[h] = 0
                corr += W[l] @ dg.reshape(-1)
            zf, zc, zs = z_of(h_fix, u, eps), z_of(h_cc, u, eps), z_of(h_fix - corr, u, eps)
            res[d][iid] = {'rho_shadow': (zs - zc) / (zf - zc), 'X_rec': zf - zc, 'z_shadow': zs, 'corr_norm': float(corr.norm())}
    value = {'b3_verification_sha256': P0.sha(P0.B3_DIR / 'runs/formal-r01/verification.json'), 'per_direction': res,
             'mean_rho_shadow': {d: sum(v['rho_shadow'] for v in res[d].values()) / len(res[d]) for d in res}}
    with open(out, 'x') as f:
        f.write(json.dumps(value, indent=1) + '\n')
    print(json.dumps(value['mean_rho_shadow']))


if __name__ == '__main__':
    main(sys.argv[1])
