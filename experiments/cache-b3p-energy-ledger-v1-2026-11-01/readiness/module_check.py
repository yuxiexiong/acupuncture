"""B3-P0 readiness: FP64 CPU recompute of every MLP branch (layers 13-31) on the C_native cell of each of the 12 inputs
(C_native is not part of any 2x2 estimand) versus the recorded GPU BF16 MLP output.  Sets the engineering floor from
which CONTRACT §3 fixes the per-cell recompute tolerance.  CUDA_VISIBLE_DEVICES= python readiness/module_check.py B3_RUN OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import p0_model as M  # noqa: E402


def main(run_dir, out):
    import torch
    torch.set_num_threads(8)
    mods = M.MLPs(M.model_path())
    rows = {}
    for w in sorted(Path(run_dir).glob('worker-*')):
        if not w.is_dir():
            continue
        for tf in sorted((w / 'tensors').glob('*.pt')):
            ten = torch.load(tf, map_location='cpu', weights_only=False)
            ex, tr = ten['extras']['C_native'], ten['trace']['C_native']
            per = {}
            for l in M.LAYERS:
                a = ex[f'{l}:in'] + tr[f'{l}:mix']                 # BF16 add, bitwise as in the model (B3 closure gate)
                rec = (ex[f'{l}:out'].double() - a.double())       # actual residual increment of the MLP branch
                f = mods.mlp(l, a)
                per[l] = {'rel_err': float((f - rec).norm() / rec.norm()), 'rel_err_vs_raw': float((f - tr[f'{l}:mlp'].double()).norm() / tr[f'{l}:mlp'].double().norm())}
            rows[tf.stem] = per
    worst = max(v['rel_err'] for r in rows.values() for v in r.values())
    res = {'cell': 'C_native', 'n_inputs': len(rows), 'max_rel_err': worst,
           'per_layer_max': {l: max(r[l]['rel_err'] for r in rows.values()) for l in M.LAYERS}, 'rows': rows}
    with open(out, 'x') as f:
        f.write(json.dumps(res, indent=2) + '\n')
    print(json.dumps({'n_inputs': len(rows), 'max_rel_err': worst, 'per_layer_max': res['per_layer_max']}, indent=1))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
