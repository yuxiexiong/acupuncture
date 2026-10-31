"""Read archived FORM-AB tensors only; no model imports or forward calls."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import hashlib
import json
from pathlib import Path
import sys
import time
import torch

torch.set_num_threads(2)
torch.set_grad_enabled(False)
root = Path('/workspace/acupuncture/experiments/cache-formation-mechanism-formation-ab-v2-2026-10-31')
started = time.monotonic()

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def schema(x):
    if isinstance(x, torch.Tensor):
        assert x.device.type == 'cpu'
        return {'shape': list(x.shape), 'dtype': str(x.dtype)}
    if isinstance(x, dict):
        return {str(k): schema(v) for k, v in x.items()}
    if isinstance(x, list):
        return {'length': len(x), 'first': schema(x[0]) if x else None,
                'last': schema(x[-1]) if x else None}
    return x

out = {'status': 'completed', 'device': 'cpu', 'model_calls': 0, 'rows': [], 'receipts': {}}
for worker in (0, 1):
    run = root / f'runs/formal-r01/worker-{worker}'
    receipt = json.loads((run / 'receipt.json').read_text())
    out['receipts'][str(worker)] = receipt
    for rel, expected in sorted(receipt['tensor_hashes'].items()):
        p = run / rel
        actual = sha(p)
        assert actual == expected, str(p)
        rp = run / 'records' / (p.stem + '.json')
        assert sha(rp) == receipt['record_hashes']['records/' + rp.name]
        r = json.loads(rp.read_text())
        x = torch.load(p, map_location='cpu', weights_only=True)
        assert set(x) == {'delta0', 'r0_C', 'r0_T', 'positions', 'donor', 'logits', 'deep'}
        assert torch.equal(x['delta0'], x['r0_T'].float() - x['r0_C'].float())
        assert x['positions'] == list(range(r['window'][0], r['window'][1] + 1))
        assert len(x['donor']) == r['n_window'] == len(x['delta0'])
        for t, donor in zip(x['positions'], x['donor']):
            assert {int(k.split(':')[0]) for k in donor} == set(range(1, 13))
            for k, v in donor.items():
                if k.endswith(':keys') or k.endswith(':values'):
                    assert v.shape[-2] == t
        for d in x['deep'].values():
            assert {int(k.split(':')[0]) for k in d} == set(range(13, 32))
        scores = {}
        e, c = r['fixed_tokens']['e_star'], r['fixed_tokens']['c_star']
        for name, z in x['logits'].items():
            assert z.ndim == 1 and torch.isfinite(z).all()
            non = z.clone(); non[[248044, 248046]] = -torch.inf
            stop = z[[248044, 248046]]
            es = [248044, 248046][int(stop.argmax())]
            ns = int(non.argmax())
            d = float(stop.max() - non.max())
            m = float(z[e] - z[c])
            ge, gn = float(stop.max() - z[e]), float(non.max() - z[c])
            old = r['scores'][name]
            assert d == old['stop_advantage'] and m == old['m_fixed']
            assert es == old['stop_winner'] and ns == old['nonstop_winner']
            assert int(z.argmax()) == old['token']
            assert abs(d - m - ge + gn) < 1e-6
            scores[name] = {'D': d, 'm': m, 'gE': ge, 'gN': gn,
                            'stop_winner': es, 'nonstop_winner': ns,
                            'eos': int(z.argmax()) in (248044, 248046),
                            'fixed_stop_logit': float(z[e]), 'fixed_nonstop_logit': float(z[c])}
        a, b = scores['X0'], scores['XB']
        effect = {'D': a['D'] - b['D'], 'm': a['m'] - b['m'],
                  'stop_selection': a['gE'] - b['gE'],
                  'nonstop_selection': -(a['gN'] - b['gN'])}
        assert abs(effect['D'] - sum(effect[k] for k in ('m', 'stop_selection', 'nonstop_selection'))) < 1e-6
        out['rows'].append({'id': p.stem, 'tensor_path': str(p), 'sha256': actual,
                            'bytes': p.stat().st_size, 'schema': schema(x),
                            'scores': scores, 'B_effect': effect, 'record': r})
        print('verified ' + p.stem, file=sys.stderr, flush=True)
        del x
assert len(out['rows']) == 12
out['wall_seconds'] = time.monotonic() - started
json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
print()
