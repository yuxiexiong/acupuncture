"""Pre-freeze engineering smoke on the real model (not a contract stage): run_item on VAR03-f0 with every gate,
A5 replay and the preflight inertness extras. Prints and stores ONLY gate outcomes, counts, timing, storage and the
CPU reconstruction diagnostic. No score readout (D, logits, ratios) is printed or written.

python real_smoke.py OUT.json [--gpu 0]
"""
import argparse
import io
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import bridge as B  # noqa: E402

F, L, T1, exp = B.F, B.L, B.T1, B.exp


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
    ref = exp.read(B.REFERENCE)
    seg = exp.read(F.SEGMENTS)['items']
    tok = exp.read(B.TOKENS)
    rows = {r['id']: r for r in B.items()}
    item = rows[B.PREFLIGHT_ITEM]
    contexts = exp.contexts_for(engine.tokenizer, list(rows.values()))
    calib = engine.calibrate([contexts[item['reference_id']]])[0]
    assert calib == ref['calibrations'][item['reference_id']]
    prompt = encode_text(engine.tokenizer, contexts[item['id']])
    labels = seg[item['id']]['labels']
    a5 = exp.read(B.fab_records()[item['id']])
    token_set = list(tok['stop_ids']) + list(tok['items'][item['id']]['nonstop'])
    out = {'item': item['id']}
    t0 = time.monotonic()
    try:
        body, tensors = B.run_item(engine, calib, prompt, labels, item['id'], token_set, a5=a5, preflight_extras=True)
        buf = io.BytesIO()
        torch.save(tensors, buf)
        out.update(status='gates_passed', gates=body['gates'], counts=body['counts'], n_window=body['n_window'],
                   reconstruction=body['reconstruction'], tensor_file_bytes=buf.getbuffer().nbytes,
                   eta_max=max(s['eta'] for s in body['scores'].values()),
                   normed_bitwise=all(s['final_norm']['normed_bitwise'] for s in body['scores'].values()))
        del body, tensors, buf
    except AssertionError as e:
        out.update(status='gate_failed', error=repr(e)[:3000])
    out['seconds'] = time.monotonic() - t0
    out['peak_gpu_mib'] = torch.cuda.max_memory_allocated() / 2 ** 20
    engine.verify_unchanged()
    Path(a.out).write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
