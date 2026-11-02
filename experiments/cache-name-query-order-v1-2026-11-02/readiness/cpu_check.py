"""NQ-01 CPU readiness (no weights): panel structure (make_inputs.check), frozen token audit consistent with a fresh tokenization
(prompt sha, b, n, window sha, shared/second tokens), SVQ-01 formal record and SP-01 calibration for the SP01-f0 replay exist
and hash-verify.  CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import nq_run as R  # noqa: E402
import make_inputs as MI  # noqa: E402


def main(out):
    from transformers import AutoTokenizer
    sys.path.insert(0, str(R.T1.SOURCE))
    from control_engine import encode_text
    src = R.exp.read(R.T1.SOURCE / 'contract.json')['source']
    tok = AutoTokenizer.from_pretrained(src['model_path'])
    rows = R.items()
    assert rows == json.loads(json.dumps(MI.build(), ensure_ascii=False)) and MI.check(rows)
    tokrec = R.exp.read(R.TOKENS)
    ctx = R.exp.contexts_for(tok, rows)
    res, ok = {'items': {}}, tokrec['passed'] is True
    for r in rows:
        seg = R.PK.label_tokens(tok, ctx[r['id']], r['record'], encode_text)
        t = tokrec['items'][r['id']]
        q, t2, d2 = R.shared_tokens(tok, r)
        x = {'prompt': R.exp.digest(seg['ids']) == t['prompt_token_sha256'], 'b': seg['b'] == t['b'], 'n': seg['n'] == t['n'],
             'window': R.exp.digest(seg['ids'][seg['b'] + 1:seg['n'] - 1]) == tokrec['window_token_sha256'],
             'tokens': (q, t2, list(d2)) == (t['q_shared'], t['second_tokens']['target'], t['second_tokens']['distractors']),
             'reference_in_panel': r['reference_id'] in ctx}
        x['passed'] = all(x.values())
        ok &= x['passed']
        res['items'][r['id']] = x
    svq = R.svq_record(R.REPLAY_ITEM)
    res['replay'] = {'svq_record_trajectories': len(svq['trajectories']), 'sp_calibration': bool(R.SVQ.sp_calibration(R.REPLAY_ITEM))}
    ok &= res['replay']['svq_record_trajectories'] == 17 and res['replay']['sp_calibration']
    res['passed'] = bool(ok)
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': res['passed'], 'n': len(res['items']), 'replay': res['replay']}))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
