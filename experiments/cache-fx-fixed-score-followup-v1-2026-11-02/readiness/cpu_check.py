"""FXS-01 CPU readiness (no weights): for all 12 P inputs the B3 record (calibration, prompt sha, GPU = plan), NR cells, and the
FX-01 formal record (C_nat + the five old T arms with first-step hashes for every direction) exist and hash-verify; the frozen q0
(FX C_nat first token) is not a stop token; U/Ubar sets build.  CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import fxs_run as R  # noqa: E402


def main(out):
    from transformers import AutoTokenizer
    sys.path.insert(0, str(R.T1.SOURCE))
    from control_engine import encode_text
    src = R.exp.read(R.T1.SOURCE / 'contract.json')['source']
    tok = AutoTokenizer.from_pretrained(src['model_path'])
    rows = R.items()
    ctx = R.exp.contexts_for(tok, rows)
    gpu_of = {u['item_id']: w for w in range(2) for u in R.plan('formal', w, 2)}
    G = (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
    fixed = R.exp.read(R.FIXED)['heads']
    res, ok = {'items': {}}, True
    for r in rows:
        rec, gpu = R.b3_record(r['id'])
        seg = R.PK.label_tokens(tok, ctx[r['id']], r['record'], encode_text)
        nr = R.nr_record(r['id'])
        fx = R.fx_record(r['id'])
        q0 = fx['trajectories']['C_nat']['ids'][0]
        fx_ok = all('logits_sha256' in fx['trajectories'][f'{a}|{d}']['first'] for a in R.OLD_ARMS for d in R.DIRECTIONS)
        nr_ok = 'C_native' in nr['cells'] and all(f'T_native|{d}' in nr['cells'] for d in R.DIRECTIONS)
        R.heads_sets(G, fixed, R.exp.read(R.URAND)['subsets'][r['id']][0])
        x = {'calibration_present': bool(rec.get('calibration')), 'prompt_sha_match': R.exp.digest(seg['ids']) == rec['prompt_token_sha256'] == fx['prompt_token_sha256'],
             'straddle': seg['straddling_tokens'], 'b3_gpu': gpu, 'plan_gpu': gpu_of[r['id']] % 2, 'q0': q0, 'q0_text': tok.decode([q0]),
             'q0_not_stop': q0 not in R.STOP, 'fx_first_present': fx_ok, 'nr_cells_present': nr_ok}
        x['passed'] = bool(x['calibration_present'] and x['prompt_sha_match'] and not x['straddle'] and x['b3_gpu'] == x['plan_gpu']
                           and x['q0_not_stop'] and fx_ok and nr_ok)
        ok &= x['passed']
        res['items'][r['id']] = x
    res['passed'] = bool(ok)
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': res['passed'], 'n': len(res['items']), 'q0': {i: v['q0_text'] for i, v in res['items'].items()}}, ensure_ascii=False))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
