"""QC-01 CPU readiness (no weights): inputs == qc_make_inputs(NQ inputs) and pass its checks; frozen token audit consistent with a fresh
tokenization (prompt sha, b, n, window sha, shared/second tokens); the six NQ-01 calibrations and the six NQ-01 formal records for
the NB replays exist and hash-verify.  CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import qc_run as R  # noqa: E402
import qc_make_inputs as MI  # noqa: E402


def main(out):
    from transformers import AutoTokenizer
    sys.path.insert(0, str(R.T1.SOURCE))
    from control_engine import encode_text
    src = R.exp.read(R.T1.SOURCE / 'contract.json')['source']
    tok = AutoTokenizer.from_pretrained(src['model_path'])
    nq = json.load(open(MI.NQ_INPUTS))['items']
    rows = R.items()
    assert rows == json.loads(json.dumps(MI.build(nq), ensure_ascii=False)) and MI.check(rows, nq)
    tokrec = R.exp.read(R.TOKENS)
    ctx = R.exp.contexts_for(tok, rows)
    res, ok = {'items': {}}, tokrec['passed'] is True
    for r in rows:
        seg = R.PK.label_tokens(tok, ctx[r['id']], r['boundary_text'], encode_text)
        t = tokrec['items'][r['id']]
        q, t2, d2 = R.shared_tokens(tok, r)
        x = {'prompt': R.exp.digest(seg['ids']) == t['prompt_token_sha256'], 'b': seg['b'] == t['b'], 'n': seg['n'] == t['n'],
             'window': R.exp.digest(seg['ids'][seg['b'] + 1:seg['n'] - 1]) == t['window_token_sha256'],
             'tokens': (q, t2, list(d2)) == (t['q_shared'], t['second_tokens']['target'], t['second_tokens']['distractors'])}
        x['passed'] = all(x.values())
        ok &= x['passed']
        res['items'][r['id']] = x
    res['nq'] = {}
    for s in sorted({r['base_id'] for r in rows}):
        cal, csha = R.nq_calibration(f'{s}-ABC-A')
        rec = R.nq_record(f'{s}-ABC-A')
        res['nq'][s] = {'calibration_sha256': csha, 'record_trajectories': len(rec['trajectories']), 'calibration_matches_record': rec['calibration'] == cal}
        ok &= len(rec['trajectories']) == 13 and rec['calibration'] == cal
    res['passed'] = bool(ok)
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': res['passed'], 'n': len(res['items']), 'nq': res['nq']}))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
