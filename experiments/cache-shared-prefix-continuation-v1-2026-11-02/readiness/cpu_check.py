"""SP-01 CPU readiness: real-tokenizer panel audit (shared unspaced first token, distinct second tokens, no straddling
segment tokens, answer regex), before any model output.  CUDA_VISIBLE_DEVICES= python readiness/cpu_check.py OUT"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import sp_run as R  # noqa: E402


def main(out):
    from transformers import AutoTokenizer
    sys.path.insert(0, str(R.T1.SOURCE))
    from control_engine import encode_text
    tok = AutoTokenizer.from_pretrained(R.exp.read(R.T1.SOURCE / 'contract.json')['source']['model_path'])
    rows = R.items()
    ctx = R.exp.contexts_for(tok, rows)
    res, ok = {'items': {}}, True
    for r in rows:
        q, t2, d2 = R.shared_tokens(tok, r)
        seg = R.PK.label_tokens(tok, ctx[r['id']], r['record'], encode_text)
        a, o = R.K.answer_and_distractors(r['record'])
        spaced = tok.encode(' ' + r['target'], add_special_tokens=False)[0]
        x = {'q_shared': q, 'q_shared_text': tok.decode([q]), 'second_target': t2, 'second_distractors': d2, 'spaced_first_differs': spaced != q,
             'straddle': seg['straddling_tokens'], 'b': seg['b'], 'n': seg['n'], 'answer_regex_ok': a == r['target'] and sorted(o) == sorted(r['distractors'])}
        x['passed'] = not x['straddle'] and x['answer_regex_ok']
        ok &= x['passed']
        res['items'][r['id']] = x
    res['passed'] = bool(ok)
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': res['passed'], 'n': len(res['items'])}))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main(sys.argv[1])
