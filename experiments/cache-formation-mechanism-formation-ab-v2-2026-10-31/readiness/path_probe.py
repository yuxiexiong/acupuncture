"""Engineering probe before the contract freeze (not a contract stage, no scientific readout).

Only C and T (no XA/XB/XAB): on VAR03-f0, compare (1) the E2 chunk route with the E2 records (bitwise), and
(2) the single-token step route over L with the E2 records (bitwise flags and |dD|), plus per-step wall time.
Purpose: decide whether plan section 4.2-2 (bitwise replay on the new route) is attainable.

python path_probe.py OUT.json [--gpu 0]
"""
import argparse
import copy
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import form_ab as F  # noqa: E402

E2, L, T1, S2T, ST2, exp = F.E2, F.L, F.T1, F.S2T, F.ST2, F.exp


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
    ref = exp.read(F.REFERENCE)
    seg = exp.read(F.SEGMENTS)['items']
    rows = {r['id']: r for r in F.items()}
    item = rows[F.PREFLIGHT_ITEM]
    contexts = exp.contexts_for(engine.tokenizer, list(rows.values()))
    rid = item['reference_id']
    calib = engine.calibrate([contexts[rid]])[0]
    assert calib == ref['calibrations'][rid]
    prompt = encode_text(engine.tokenizer, contexts[item['id']])
    labels = seg[item['id']]['labels']
    assert exp.digest(prompt) == seg[item['id']]['prompt_token_sha256']
    e2 = F.e2_endpoints(exp.read(F.e2_records()[item['id']]))
    types = L.layer_types(engine.model)
    cond = T1.engine_condition(F.A0)
    out = {'item': item['id'], 'kernel_identity': T1.kernel_identity(), 'chunk': {}, 'step': {}}
    for name, needle, mask in (('C', None, None), ('T_native', cond, S2T.arm_mask('01', labels))):
        r, cache = F.chunk_route(engine, needle, mask, calib, prompt)
        out['chunk'][name] = {'manifest_bitwise': ST2.cache_manifest(cache, types) == e2['manifest'][name],
                              **{k: r[k] == e2[name][k] for k in ('token', 'stop_advantage', 'logits_sha256', 'top5')}}
    prefix, last, n = prompt[:-1], prompt[-1], len(prompt)
    b = S2T.boundary_b(labels)
    window = list(range(b + 1, n - 1))
    with torch.inference_mode():
        base = L.forward(engine.model, list(prefix[:b + 1]), 0, None).past_key_values
    caches = {}
    for name, needle in (('C', None), ('T_native', cond)):
        c = copy.deepcopy(base)
        torch.cuda.synchronize()
        t0 = time.monotonic()
        for t in window:
            c, _ = F.forward_tokens(engine, c, [prefix[t]], t, needle, calib)
        torch.cuda.synchronize()
        caches[name] = c
        r, _ = F.score(engine, c, last, n, keep_logits=False)
        out['step'][name] = {'seconds_per_step': (time.monotonic() - t0) / len(window),
                             'manifest_bitwise': ST2.cache_manifest(c, types) == e2['manifest'][name],
                             'logits_bitwise': r['logits_sha256'] == e2[name]['logits_sha256'],
                             'token_same': r['token'] == e2[name]['token'],
                             'step_D': r['stop_advantage'], 'e2_D': e2[name]['stop_advantage'],
                             'abs_dD': abs(r['stop_advantage'] - e2[name]['stop_advantage'])}
    out['delta_e2'] = e2['X0']['stop_advantage'] - e2['C']['stop_advantage']
    out['tolerance_preset'] = F.PATH_TOL * out['delta_e2']
    out['created_at'] = exp.utc()
    Path(a.out).write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
