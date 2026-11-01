"""C2 CPU readiness (no model): C1-P anchor assets and calibrations for all 12 inputs, direction file and needle
definitions, frozen FIX random lists, segment rule on the P inputs.  CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import c2_run as V  # noqa: E402


def main(out):
    from transformers import AutoTokenizer
    sys.path.insert(0, str(V.T1.SOURCE))
    from control_engine import encode_text
    src = V.exp.read(V.T1.SOURCE / 'contract.json')['source']
    tok = AutoTokenizer.from_pretrained(src['model_path'])
    rows = V.items()
    ctx = V.exp.contexts_for(tok, rows)
    res, ok = {'items': {}}, True
    conds = V.conditions()
    res['conditions'] = {d: {k: v for k, v in c.items() if k != 'vector'} for d, c in conds.items()}
    for r in rows:
        rec, cal = V.c1p_assets(r['id'])
        seg = V.PK.label_tokens(tok, ctx[r['id']], r['record'], encode_text)
        need = ['C_native', 'T_native', 'N:CC', 'N:CT', 'N:CFIX']
        x = {'c1p_cells_present': all(c in rec['cells'] for c in need), 'c1p_calibration_layers': len(cal['residual_scales']),
             'prompt_sha_match': V.exp.digest(seg['ids']) == rec['prompt_token_sha256'], 'straddle': seg['straddling_tokens']}
        x['passed'] = x['c1p_cells_present'] and x['prompt_sha_match'] and not x['straddle'] and x['c1p_calibration_layers'] > 0
        ok &= x['passed']
        res['items'][r['id']] = x
    res['passed'] = bool(ok)
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': res['passed'], 'n': len(res['items'])}))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
