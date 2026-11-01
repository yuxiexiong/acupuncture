"""B4 CPU readiness (no weights): B3 formal records for all 12 inputs carry C_native/T_native/N:CC/N:CFIX for every
direction and the calibration; B3 worker/GPU assignment equals the B4 plan; prompt tokens match; next-scenario template
inputs exist; shadow file covers every unit.  CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import b4_run as R  # noqa: E402


def main(out):
    from transformers import AutoTokenizer
    sys.path.insert(0, str(R.T1.SOURCE))
    from control_engine import encode_text
    src = R.exp.read(R.T1.SOURCE / 'contract.json')['source']
    tok = AutoTokenizer.from_pretrained(src['model_path'])
    rows = R.items()
    ctx = R.exp.contexts_for(tok, rows)
    gpu_of = {u['item_id']: w for w in range(2) for u in R.plan('formal', w, 2)}
    shadow = json.loads(R.SHADOW.read_text())
    res, ok = {'items': {}}, True
    ids = {r['id'] for r in rows}
    for r in rows:
        rec, gpu = R.b3_record(r['id'])
        seg = R.PK.label_tokens(tok, ctx[r['id']], r['record'], encode_text)
        need = ['C_native'] + [f'{c}|{d}' for c in ('T_native', 'N:CC', 'N:CFIX') for d in R.K.DIRECTIONS]
        x = {'b3_cells_present': all(c in rec['cells'] for c in need), 'calibration_present': bool(rec.get('calibration')),
             'prompt_sha_match': R.exp.digest(seg['ids']) == rec['prompt_token_sha256'], 'straddle': seg['straddling_tokens'],
             'b3_gpu': gpu, 'b4_gpu': gpu_of[r['id']] % 2, 'next_scenario': R.next_scenario(r['id']),
             'shadow_present': all(r['id'] in shadow['per_direction'][d] for d in R.K.DIRECTIONS)}
        x['passed'] = (x['b3_cells_present'] and x['calibration_present'] and x['prompt_sha_match'] and not x['straddle']
                       and x['b3_gpu'] == x['b4_gpu'] and x['next_scenario'] in ids and x['shadow_present'])
        ok &= x['passed']
        res['items'][r['id']] = x
    res['passed'] = bool(ok)
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': res['passed'], 'n': len(res['items'])}))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
