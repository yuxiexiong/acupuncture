"""QCD-01 frozen per-text plan (design v2, CONTRACT §2): from the QC-01 frozen inputs and token audit only.
Texts = the 108 QC texts of NA and LA (broad ids); each also has its QC tail twin (same text, boundary after the question).
Zero-based positions: n prompt tokens, broad boundary b_b (record end), p = b_b + 1, e = n - 2 (last injected position; n - 1 is the
read-out), L = e - p + 1 in {26, 27}.  Windows: B = [p, e]; N = [e - 19, e] (= QC tail window, b_s = e - 20); E20 = [p, p + 19].
Policies (positive multiplier a; signed dose = -a): B1 (B, 1), N1 (N, 1), E1 (E20, 1), N-A (N, L/20), N-Q (N, sqrt(L/20)),
B-A (B, 20/L), B-Q (B, sqrt(20/L)).  python qcd_make_plan.py data/plan-r01.json"""
import hashlib
import json
import math
import sys
from pathlib import Path

QC = Path(__file__).resolve().parent.parent / 'cache-query-layout-coverage-v1-2026-11-02'


def policies(L):
    return {'B1': {'window': 'B', 'a': 1.0}, 'N1': {'window': 'N', 'a': 1.0}, 'E1': {'window': 'E20', 'a': 1.0},
            'N-A': {'window': 'N', 'a': L / 20}, 'N-Q': {'window': 'N', 'a': math.sqrt(L / 20)},
            'B-A': {'window': 'B', 'a': 20 / L}, 'B-Q': {'window': 'B', 'a': math.sqrt(20 / L)}}


def build():
    items = {r['id']: r for r in json.load(open(QC / 'data/inputs-r01.json'))['items']}
    tok = json.load(open(QC / 'data/tokens-r01.json'))['items']
    rows = []
    for cond in ('NA', 'LA'):
        for iid, r in items.items():
            if r['condition'] != cond:
                continue
            tid = f'{cond}-tail-{r["nq_id"]}'
            tb, ts = tok[iid], tok[tid]
            assert tb['prompt_token_sha256'] == ts['prompt_token_sha256'] and tb['n'] == ts['n']
            n, bb, bs = tb['n'], tb['b'], ts['b']
            p, e = bb + 1, n - 2
            L = e - p + 1
            assert L in (26, 27) and bs == e - 20 and ts['window_len'] == 20 and tb['window_len'] == L
            rows.append({'id': iid, 'template': cond, 'nq_id': r['nq_id'], 'qc_broad_id': iid, 'qc_tail_id': tid, 'base_id': r['base_id'],
                         'n': n, 'b_b': bb, 'b_s': bs, 'p': p, 'e': e, 'L': L,
                         'windows': {'B': [p, e], 'N': [e - 19, e], 'E20': [p, p + 19]}, 'policies': policies(L)})
    return rows


def check(rows):
    assert len(rows) == 108 and len({r['id'] for r in rows}) == 108
    for r in rows:
        w = r['windows']
        assert w['B'][1] - w['B'][0] + 1 == r['L'] and w['N'][1] - w['N'][0] + 1 == 20 and w['E20'][1] - w['E20'][0] + 1 == 20
        assert w['N'][1] == w['B'][1] == r['n'] - 2 and w['E20'][0] == w['B'][0] == r['b_b'] + 1
        ov = len(set(range(w['N'][0], w['N'][1] + 1)) & set(range(w['E20'][0], w['E20'][1] + 1)))
        assert ov == 40 - r['L'], (r['id'], ov)
        P = r['policies']
        assert abs(P['N-A']['a'] * 20 - r['L']) < 1e-12 and abs(P['N-Q']['a'] ** 2 * 20 - r['L']) < 1e-12
        assert abs(P['B-A']['a'] * r['L'] - 20) < 1e-12 and abs(P['B-Q']['a'] ** 2 * r['L'] - 20) < 1e-12
    return True


if __name__ == '__main__':
    rows = build()
    check(rows)
    with open(sys.argv[1], 'x') as f:
        f.write(json.dumps({'schema': 1, 'design': 'QCD-01 v2', 'qc_inputs_sha256': hashlib.sha256((QC / 'data/inputs-r01.json').read_bytes()).hexdigest(),
                            'qc_tokens_sha256': hashlib.sha256((QC / 'data/tokens-r01.json').read_bytes()).hexdigest(), 'texts': rows}, indent=1) + '\n')
    from collections import Counter
    print(len(rows), Counter((r['template'], r['L']) for r in rows))
