"""SVQ-01 CPU readiness (no weights): for all 12 SP inputs the SP-01 formal record exists and hash-verifies, carries C_nat and
T_nat/T_shared/T_F for every direction with first-step hashes and the step-2 watch values the diagnostic replay gate needs; the
SP-01 calibration exists; q_shared / second tokens recomputed with the real tokenizer equal the record; prompt tokens match;
the SP-01 worker of each input equals this plan's worker.  CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import svq_run as R  # noqa: E402


def main(out):
    from transformers import AutoTokenizer
    sys.path.insert(0, str(R.T1.SOURCE))
    from control_engine import encode_text
    src = R.exp.read(R.T1.SOURCE / 'contract.json')['source']
    tok = AutoTokenizer.from_pretrained(src['model_path'])
    rows = R.items()
    ctx = R.exp.contexts_for(tok, rows)
    w_of = {u['item_id']: w for w in range(2) for u in R.plan('formal', w, 2)}
    res, ok = {'items': {}}, True
    for r in rows:
        rec, w = R.sp_record(r['id'])
        seg = R.PK.label_tokens(tok, ctx[r['id']], r['record'], encode_text)
        q, t2, d2 = R.shared_tokens(tok, r)
        tr = rec['trajectories']
        need = ['C_nat'] + [f'{a}|{d}' for a in ('T_nat', 'T_shared', 'T_F') for d in R.DIRECTIONS]
        present = all(k in tr and 'logits_sha256' in tr[k]['first'] for k in need)
        shared_step2 = all('step2' in tr[f'T_shared|{d}']['first'] for d in R.DIRECTIONS)
        x = {'records_present': present, 'T_shared_step2_present': shared_step2,
             'C_first_is_shared': tr['C_nat']['ids'][0] == q,
             'T_F_first_is_shared': {d: tr[f'T_F|{d}']['ids'][0] == q for d in R.DIRECTIONS},
             'tokens_match': (q, t2, list(d2)) == (rec['q_shared'], rec['second_tokens']['target'], list(rec['second_tokens']['distractors'])),
             'prompt_sha_match': R.exp.digest(seg['ids']) == rec['prompt_token_sha256'], 'straddle': seg['straddling_tokens'],
             'calibration_present': bool(R.sp_calibration(r['reference_id'])), 'sp_worker': int(w.name.split('-')[1]), 'plan_worker': w_of[r['id']]}
        x['passed'] = bool(present and shared_step2 and x['tokens_match'] and x['prompt_sha_match'] and not x['straddle']
                           and x['calibration_present'] and x['sp_worker'] == x['plan_worker'])
        ok &= x['passed']
        res['items'][r['id']] = x
    res['passed'] = bool(ok)
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': res['passed'], 'n': len(res['items']),
                      'C_first_shared': sum(v['C_first_is_shared'] for v in res['items'].values()),
                      'T_F_first_shared': sum(sum(v['T_F_first_is_shared'].values()) for v in res['items'].values())}))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
