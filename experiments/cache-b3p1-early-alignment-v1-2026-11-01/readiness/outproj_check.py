"""B3-P1 readiness: FP64 W_o @ gated_norm_out versus the recorded out_proj output and the actual mixer residual increment, on
the C_native cell of every input (not part of any estimand), for the 14 G layers.  CUDA_VISIBLE_DEVICES= python readiness/outproj_check.py B3_RUN OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import p1_run as R  # noqa: E402
import p1_weights as PW  # noqa: E402


def main(run_dir, out):
    import torch
    W = PW.load_out_proj(R.P0.M.model_path(), R.G_LAYERS)
    rows = {}
    for w in sorted(Path(run_dir).glob('worker-*')):
        if not w.is_dir():
            continue
        for tf in sorted((w / 'tensors').glob('*.pt')):
            ten = torch.load(tf, map_location='cpu', weights_only=False)
            ex, tr, cn = ten['extras']['C_native'], ten['trace']['C_native'], ten['counter']['C_native']
            per = {}
            for l in R.G_LAYERS:
                y = W[l] @ cn[f'{l}:gated_norm_out'].double()
                inc = (ex[f'{l}:in'] + tr[f'{l}:mix']).double() - ex[f'{l}:in'].double()
                per[l] = {'rel_vs_outproj': float((y - cn[f'{l}:out_proj'].double()).norm() / cn[f'{l}:out_proj'].double().norm()),
                          'rel_vs_increment': float((y - inc).norm() / inc.norm())}
            rows[tf.stem] = per
    res = {'cell': 'C_native', 'max_rel_vs_increment': max(v['rel_vs_increment'] for r in rows.values() for v in r.values()),
           'max_rel_vs_outproj': max(v['rel_vs_outproj'] for r in rows.values() for v in r.values()), 'rows': rows}
    with open(out, 'x') as f:
        f.write(json.dumps(res, indent=1) + '\n')
    print(json.dumps({k: v for k, v in res.items() if k != 'rows'}))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
