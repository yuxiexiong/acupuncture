"""NBR-01 real-model gradient-path smoke on CPU (no GPU, no experiment data): prefill a fixed short prompt under inference mode, then run
nbr_run.grad_forward exactly as the runner does.  Passes iff it completes, logits equal the inference forward bit for bit, 14 finite gradients.
CUDA_VISIBLE_DEVICES= python readiness/grad_smoke.py OUT"""
import copy
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import nbr_run as R  # noqa: E402


def main(out):
    import torch
    sys.path.insert(0, str(R.T1.SOURCE))
    from control_engine import ControlEngine
    src = R.exp.read(R.T1.SOURCE / 'contract.json')['source']
    eng = ControlEngine(src['model_path'], R.exp.model_spec(), 'cpu')
    model = eng.model
    types = R.L.layer_types(model)
    G = R.B.g_layers(types, R.NVBR.SPLIT)
    R.KRDR.QHOOK_ORIG[0] = R.gdn_module().torch_recurrent_gated_delta_rule
    ids = eng.tokenizer.encode('The code for the blue box is ABC-17. The code for the red box is', add_special_tokens=False)
    with torch.inference_mode():
        c = R.L.forward(model, ids[:-1], 0, None).past_key_values
        c = R.L.forward(model, [ids[-1]], len(ids) - 1, c).past_key_values
    counts = {k: 0 for k in R.COUNT_KEYS}
    M, z, gd = R.grad_forward(eng, c, ids[2], len(ids), counts, G, types, {'target': 'A', 'listed_codes': ['A', 'B']}, {'A': ids[3], 'B': ids[5]}, 'B')
    with torch.inference_mode():
        z2 = R.L.forward(model, [ids[2]], len(ids), copy.deepcopy(c)).logits[0, -1].float()
    res = {'M': M, 'logit_maxdiff': float((z - z2).abs().max()), 'n_grad_layers': len(gd), 'finite': bool(all(torch.isfinite(x).all() for x in gd.values()))}
    res['passed'] = res['logit_maxdiff'] == 0.0 and res['n_grad_layers'] == len(G) and res['finite']
    with open(out, 'x') as f:
        f.write(json.dumps(res, indent=2) + '\n')
    print(json.dumps(res))
    sys.exit(0 if res['passed'] else 1)


if __name__ == '__main__':
    main(sys.argv[1])
