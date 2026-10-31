"""Pre-freeze engineering smoke on the real model (not a contract stage): run_item on VAR03-f0 with every gate,
the inert-hook rerun and the E2 route gate. Prints and stores ONLY gate outcomes, route-gate rows (C, T_native, X0:
E2-known endpoints), counts and timing. No XA/XB/XAB readout is printed or written.

python real_smoke.py OUT.json [--gpu 0]
"""
import argparse
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import form_ab as F  # noqa: E402

L, T1, exp = F.L, F.T1, F.exp


def main():
    p = argparse.ArgumentParser()
    p.add_argument('out')
    p.add_argument('--gpu', type=int, default=0)
    a = p.parse_args()
    sys.path.insert(0, str(T1.SOURCE))
    from control_engine import ControlEngine, encode_text
    import torch
    source = exp.read(T1.SOURCE / 'contract.json')['source']
    engine = ControlEngine(source['model_path'], exp.model_spec(), f'cuda:{a.gpu}')
    exp.metadata_check(engine)
    base = F.hook_baseline(engine.model)
    ref = exp.read(F.REFERENCE)
    seg = exp.read(F.SEGMENTS)['items']
    rows = {r['id']: r for r in F.items()}
    item = rows[F.PREFLIGHT_ITEM]
    contexts = exp.contexts_for(engine.tokenizer, list(rows.values()))
    calib = engine.calibrate([contexts[item['reference_id']]])[0]
    assert calib == ref['calibrations'][item['reference_id']]
    prompt = encode_text(engine.tokenizer, contexts[item['id']])
    labels = seg[item['id']]['labels']
    e2 = F.e2_endpoints(exp.read(F.e2_records()[item['id']]))
    out = {'item': item['id'], 'modules_with_bare_hooks': sum(1 for c in base if c != (0, 0))}
    t0 = time.monotonic()
    try:
        body, tensors = F.run_item(engine, calib, prompt, labels, e2=e2, inert_rerun=True, keep_tensors=True)
        out.update(status='gates_passed', gates=body['gates'], counts=body['counts'], n_window=body['n_window'],
                   route_gate=body['route_gate'],
                   tensor_bytes=sum(v.numel() * v.element_size() for d in tensors['donor'] for v in d.values())
                   + sum(v.numel() * v.element_size() for d in tensors['deep'].values() for v in d.values()))
        del body, tensors
    except AssertionError as e:
        out.update(status='gate_failed', error=repr(e)[:2000])
    out['seconds'] = time.monotonic() - t0
    out['peak_gpu_mib'] = torch.cuda.max_memory_allocated() / 2**20
    engine.verify_unchanged()
    Path(a.out).write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
