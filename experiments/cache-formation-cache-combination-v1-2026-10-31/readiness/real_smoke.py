"""Pre-freeze engineering smoke on the real model (not a contract stage): run_item on VAR03-f0 with all gates and the
preflight extras. Prints and stores ONLY gate outcomes, counts, timing and storage; no score readout.

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
import combo as CB  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument('out')
    p.add_argument('--gpu', type=int, default=0)
    a = p.parse_args()
    exp, T1, F = CB.exp, CB.T1, CB.F
    sys.path.insert(0, str(T1.SOURCE))
    from control_engine import ControlEngine, encode_text
    import torch
    source = exp.read(T1.SOURCE / 'contract.json')['source']
    engine = ControlEngine(source['model_path'], exp.model_spec(), f'cuda:{a.gpu}')
    exp.metadata_check(engine)
    ref = exp.read(CB.REFERENCE)
    seg = exp.read(F.SEGMENTS)['items']
    tok = exp.read(CB.TOKENS)
    rows = {r['id']: r for r in CB.items()}
    item = rows[CB.PREFLIGHT_ITEM]
    contexts = exp.contexts_for(engine.tokenizer, list(rows.values()))
    calib = engine.calibrate([contexts[item['reference_id']]])[0]
    assert calib == ref['calibrations'][item['reference_id']]
    prompt = encode_text(engine.tokenizer, contexts[item['id']])
    labels = seg[item['id']]['labels']
    rec_old, old = CB.load_old(item['id'])
    token_set = list(tok['stop_ids']) + list(tok['items'][item['id']]['nonstop'])
    out = {'item': item['id']}
    t0 = time.monotonic()
    try:
        body, tensors = CB.run_item(engine, calib, prompt, labels, item['id'], token_set, old, rec_old, preflight_extras=True)
        buf = io.BytesIO()
        torch.save(tensors, buf)
        out.update(status='gates_passed', gates=body['gates'], counts=body['counts'], tensor_file_bytes=buf.getbuffer().nbytes,
                   eta_max=max(s['eta'] for s in body['scores'].values()))
    except AssertionError as e:
        out.update(status='gate_failed', error=repr(e)[:3000])
    out['seconds'] = time.monotonic() - t0
    out['peak_gpu_mib'] = torch.cuda.max_memory_allocated() / 2 ** 20
    engine.verify_unchanged()
    Path(a.out).write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
