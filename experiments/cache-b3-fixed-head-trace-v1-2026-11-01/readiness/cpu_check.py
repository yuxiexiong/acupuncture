"""B3 CPU readiness (no model weights): C2 formal records for all 12 inputs carry every replay cell and the C1-P
calibration; C2 worker/GPU assignment equals the B3 plan; prompt tokens match; frozen lists load; token-forward
count of the formation windows expanded to integers.  CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import b3_run as V  # noqa: E402


def main(out):
    from transformers import AutoTokenizer
    sys.path.insert(0, str(V.T1.SOURCE))
    from control_engine import encode_text
    src = V.exp.read(V.T1.SOURCE / 'contract.json')['source']
    tok = AutoTokenizer.from_pretrained(src['model_path'])
    rows = V.items()
    ctx = V.exp.contexts_for(tok, rows)
    gpu_of = {u['item_id']: w for w in range(2) for u in V.plan('formal', w, 2)}
    res, ok = {'items': {}}, True
    fu = V.exp.read(V.V.FIXU)
    fixed = V.exp.read(V.P.FIXED)['heads']
    windows = {}
    for r in rows:
        rec, gpu = V.c2_record(r['id'])
        _, cal = V.V.c1p_assets(r['id'])
        seg = V.PK.label_tokens(tok, ctx[r['id']], r['record'], encode_text)
        need = ['C_native'] + [f'{c}|{d}' for c in V.REPLAY for d in V.K.DIRECTIONS]
        windows[r['id']] = seg['n'] - seg['b'] - 2
        x = {'c2_cells_present': all(c in rec['cells'] for c in need), 'calibration_equal_c1p': rec['calibration'] == cal,
             'prompt_sha_match': V.exp.digest(seg['ids']) == rec['prompt_token_sha256'], 'straddle': seg['straddling_tokens'],
             'c2_gpu': gpu, 'b3_gpu': gpu_of[r['id']] % 2, 'ufix_lists': len(fu['subsets'][r['id']]) == 4,
             'window': windows[r['id']]}
        x['passed'] = (x['c2_cells_present'] and x['calibration_equal_c1p'] and x['prompt_sha_match'] and not x['straddle']
                       and x['c2_gpu'] == x['b3_gpu'] and x['ufix_lists'])
        ok &= x['passed']
        res['items'][r['id']] = x
    pre = sum(windows[i] for i in V.PREFLIGHT_ITEMS)
    formal = sum(windows.values())
    n_dir = len(V.K.DIRECTIONS)
    res['forward_accounting'] = {
        'prefix_prefills': 2 + 12, 'formation_sequences': 10 + 60,
        'formation_token_forwards': (1 + n_dir) * (pre + formal), 'single_step_scores': V.LIMITS['preflight']['scores'] + V.LIMITS['formal']['scores'],
        'calibrations': V.LIMITS['preflight']['calibrations'] + V.LIMITS['formal']['calibrations']}
    res['fixed_heads'] = len(fixed)
    res['passed'] = bool(ok)
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': res['passed'], 'n': len(res['items']), 'forward_accounting': res['forward_accounting']}))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
