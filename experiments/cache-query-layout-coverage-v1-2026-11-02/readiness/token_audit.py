"""QC-01 token audit with the real tokenizer (plan §2, §5.1).  Per input: boundary b = last token of boundary_text + newline (frozen
PK.label_tokens), no straddling token, window ids b+1..n-2.  Rules: LB / NA-tail / LA-tail window token ids == the NQ-01 frozen
window (fixed instruction + template tail) and every question token <= b; NA / LA window decodes to question + newline + the NQ
window, the question lies entirely inside the window; LA windows identical across inputs; NA windows identical within a queried
item within a scenario; shared first token / distinct second tokens.  CUDA_VISIBLE_DEVICES= python readiness/token_audit.py data/tokens-r01.json"""
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import qc_run as R  # noqa: E402


def main(out):
    from transformers import AutoTokenizer
    sys.path.insert(0, str(R.T1.SOURCE))
    from control_engine import encode_text
    src = R.exp.read(R.T1.SOURCE / 'contract.json')['source']
    tok = AutoTokenizer.from_pretrained(src['model_path'])
    nq_tok = R.exp.read(R.NQR.TOKENS)
    nq_win = nq_tok['window_token_sha256']
    rows = R.items()
    ctx = R.exp.contexts_for(tok, rows)
    res, wins = {'items': {}}, {}
    for r in rows:
        c = ctx[r['id']]
        seg = R.PK.label_tokens(tok, c, r['boundary_text'], encode_text)
        assert not seg['straddling_tokens'], (r['id'], seg['straddling_tokens'])
        ids, b, n = seg['ids'], seg['b'], seg['n']
        win = ids[b + 1:n - 1]
        wtext = tok.decode(win, skip_special_tokens=False)
        enc = tok(c, add_special_tokens=False, return_offsets_mapping=True)
        qs = c.index('\n' + r['question']) + 1 if r['layout'] == 'after' else c.index(r['question'])
        qe = qs + len(r['question'])
        q_tok = [k for k, (a, e) in enumerate(enc['offset_mapping']) if a < qe and e > qs]
        assert q_tok
        if r['condition'] in ('LB', 'NA-tail', 'LA-tail'):
            assert max(q_tok) <= b, ('question token inside the window', r['id'])
            assert R.exp.digest(win) == nq_win, ('window != NQ-01 window', r['id'], wtext)
        else:
            assert min(q_tok) > b, ('question token not inside the window', r['id'])
            assert wtext == r['question'] + '\n' + nq_tok['window_text'], (r['id'], wtext)
        wins.setdefault(r['condition'], {}).setdefault((r['base_id'], r['query']) if r['condition'] == 'NA' else '*', set()).add(R.exp.digest(win))
        q, t2, d2 = R.shared_tokens(tok, r)
        res['items'][r['id']] = {'prompt_token_sha256': R.exp.digest(ids), 'b': b, 'n': n, 'window_token_sha256': R.exp.digest(win),
                                 'window_len': len(win), 'window_text': wtext, 'q_shared': q,
                                 'second_tokens': {'target': t2, 'distractors': list(d2)}, 'context_sha256': hashlib.sha256(c.encode()).hexdigest()}
    for cond, g in wins.items():
        for key, s in g.items():
            assert len(s) == 1, ('window not constant', cond, key, len(s))
    res['window_len'] = {cond: sorted({v['window_len'] for k, v in res['items'].items() if k.startswith(cond + '-NQ')}) for cond in R.CONDITIONS}
    res['passed'] = True
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'passed': True, 'n': len(res['items']), 'window_len': res['window_len']}, ensure_ascii=False))


if __name__ == '__main__':
    main(sys.argv[1])
