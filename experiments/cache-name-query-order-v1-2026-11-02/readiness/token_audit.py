"""NQ-01 token audit with the real tokenizer (plan v2 §2, §7).  For every input: chat context, prompt token ids, boundary b
(last token of record+newline via the frozen PK.label_tokens), no straddling, query and record tokens at or before b, the
injection window ids b+1..n-2 identical across all 54 inputs, shared first token / distinct second tokens of the three codes.
CUDA_VISIBLE_DEVICES= python readiness/token_audit.py data/tokens-r01.json"""
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import nq_run as R  # noqa: E402


def digest(ids):
    return R.exp.digest(ids)


def main(out):
    from transformers import AutoTokenizer
    sys.path.insert(0, str(R.T1.SOURCE))
    from control_engine import encode_text
    src = R.exp.read(R.T1.SOURCE / 'contract.json')['source']
    tok = AutoTokenizer.from_pretrained(src['model_path'])
    rows = R.items()
    ctx = R.exp.contexts_for(tok, rows)
    res, windows = {'items': {}}, set()
    for r in rows:
        seg = R.PK.label_tokens(tok, ctx[r['id']], r['record'], encode_text)
        assert not seg['straddling_tokens'], (r['id'], seg['straddling_tokens'])
        ids, b, n = seg['ids'], seg['b'], seg['n']
        c = ctx[r['id']]
        q_end = c.index(r['question']) + len(r['question'])
        enc = tok(c, add_special_tokens=False, return_offsets_mapping=True)
        q_tok = [k for k, (a, e) in enumerate(enc['offset_mapping']) if a < q_end and e > c.index(r['question'])]
        assert q_tok and max(q_tok) <= b, ('query tokens beyond b', r['id'])
        win = ids[b + 1:n - 1]
        assert R.tok_text(tok, win).startswith(r['instruction']), (r['id'], R.tok_text(tok, win))
        windows.add(digest(win))
        q, t2, d2 = R.shared_tokens(tok, r)
        res['items'][r['id']] = {'prompt_token_sha256': digest(ids), 'b': b, 'n': n, 'window_token_sha256': digest(win),
                                 'window_len': len(win), 'q_shared': q, 'second_tokens': {'target': t2, 'distractors': list(d2)},
                                 'context_sha256': hashlib.sha256(c.encode()).hexdigest()}
    assert len(windows) == 1, ('injection window differs across inputs', len(windows))
    res['window_token_sha256'] = windows.pop()
    res['window_text'] = R.tok_text(tok, ids[b + 1:n - 1])
    res['passed'] = True
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'passed': True, 'n': len(res['items']), 'window': res['window_text'], 'window_len': len(ids[b + 1:n - 1])}, ensure_ascii=False))


if __name__ == '__main__':
    main(sys.argv[1])
