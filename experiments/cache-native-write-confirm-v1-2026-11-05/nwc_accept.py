"""NWC-01 panel acceptance (tokenizer only, no weights).  Builds pipeline items and the token ledger for the 72 frozen inputs; any failure stops
(no rewording, no output-based filtering).  Rules as for the LVK-01 held-out panel: B1 window = [b+1, n-2]; distractors = listed codes minus target
in listed order; calibration reference = '<family>-ABC-A'; every code is 3 tokens with a shared first token equal to the family's token in the
LVK ledger and pairwise distinct second tokens; no straddling token at the record boundary; length <= 2x the family's earlier inputs.
CUDA_VISIBLE_DEVICES= python nwc_accept.py OUT_JSON"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'cache-native-write-readout-v1-2026-11-05'))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import nwr_run as R  # noqa: E402

INPUTS = HERE / 'data/nwc-inputs-r01.json'
INPUTS_SHA = 'cd6c6b3a90cfaa8fa10bc753f3f4c78f1045cbd71f790857868c76b467f2becf'


def pipeline_item(h):
    return {'id': h['id'], 'base_id': h['scenario'], 'order': h['order'], 'query': h['query'], 'query_name': h['binding'][h['query']][0],
            'target': h['target'], 'distractors': [c for c in h['listed_codes'] if c != h['target']], 'listed_codes': h['listed_codes'],
            'first_listed': h['first_listed'], 'binding': h['binding'], 'record': h['record'], 'question': h['question'],
            'instruction': h['instruction'], 'prompt': h['prompt'], 'boundary_text': h['boundary_text'], 'reference_id': f"{h['scenario']}-ABC-A"}


def main(out):
    exp = R.exp
    assert exp.sha(INPUTS) == INPUTS_SHA, 'panel file hash'
    sys.path.insert(0, str(R.T1.SOURCE))
    from control_engine import encode_text
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(exp.read(R.T1.SOURCE / 'contract.json')['source']['model_path'])
    H = exp.read(INPUTS)['items']
    old = R.ledger()                                              # LVK held-out ledger: family reference values
    fam = {}
    for v in old.values():
        f = fam.setdefault(v['plan']['base_id'], {'q_shared': set(), 'n': 0, 'L': 0, 'ent': set(), 'codes': set()})
        f['q_shared'].add(v['tokens']['q_shared'])
        f['n'], f['L'] = max(f['n'], v['plan']['n']), max(f['L'], v['plan']['L'])
        f['codes'] |= set(v['item']['listed_codes'])
        f['ent'] |= {b[0] for b in v['item']['binding'].values()}
    assert len(H) == 72 and all(len(f['q_shared']) == 1 for f in fam.values())
    fails, ledger = [], {}
    for h in H:
        it, f, fm = pipeline_item(h), [], fam[h['scenario']]
        if h['binding'][h['query']][1] != h['target'] or h['binding'][h['query']][0] not in h['question']:
            f.append('binding')
        if h['listed_codes'][0] != h['first_listed'] or h['listed_codes'] != [h['binding'][s][1] for s in 'ABC']:
            f.append('listed codes')
        if (h['target'] == h['first_listed']) != (h['stratum'] == 'F'):
            f.append('stratum')
        if not h['prompt'].startswith(h['boundary_text']):
            f.append('boundary text')
        if set(h['listed_codes']) & fm['codes'] or {b[0] for b in h['binding'].values()} & fm['ent']:
            f.append('reuses an entity or code of the LVK panel')
        lens = [len(tok.encode(c, add_special_tokens=False)) for c in h['listed_codes']]
        if lens != [3, 3, 3]:
            f.append(f'code token lengths {lens}')
        try:
            q_shared, t2, d2 = R.QSTR.shared_tokens(tok, it)
        except AssertionError as e:
            f.append(f'shared tokens: {e}')
            q_shared, t2, d2 = None, None, None
        if q_shared is not None and {q_shared} != fm['q_shared']:
            f.append('shared first token != family token')
        ctx = exp.contexts_for(tok, [it])[it['id']]
        seg = R.PK.label_tokens(tok, ctx, it['boundary_text'], encode_text)
        if seg['straddling_tokens']:
            f.append('straddling tokens')
        b, n = seg['b'], seg['n']
        p_, e_ = b + 1, n - 2
        if not (0 < p_ <= e_ < n - 1):
            f.append('window')
        if n > 2 * fm['n'] or (e_ - p_ + 1) > 2 * fm['L']:
            f.append('length > 2x earlier')
        ledger[h['id']] = {'item': it, 'plan': {'base_id': h['scenario'], 'situation': h['situation'], 'version': h['version'], 'stratum': h['stratum'],
                                                 'partner_id': h['partner_id'], 'b': b, 'n': n, 'p': p_, 'e': e_, 'L': e_ - p_ + 1,
                                                 'prompt_token_sha256': exp.digest(seg['ids'])},
                           'tokens': {'q_shared': q_shared, 'target_second': t2, 'distractor_second': d2}, 'failures': f}
        if f:
            fails.append((h['id'], f))
    tot = {'prefix_tokens': sum(v['plan']['b'] + 1 for v in ledger.values()), 'window_tokens': sum(v['plan']['L'] for v in ledger.values()),
           'n_range': [min(v['plan']['n'] for v in ledger.values()), max(v['plan']['n'] for v in ledger.values())],
           'L_range': [min(v['plan']['L'] for v in ledger.values()), max(v['plan']['L'] for v in ledger.values())]}
    res = {'status': 'passed' if not fails else 'failed', 'inputs_sha256': INPUTS_SHA, 'n': len(H), 'failures': fails, 'totals': tot, 'items': ledger}
    with open(out, 'x') as fo:
        fo.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({k: v for k, v in res.items() if k != 'items'}, ensure_ascii=False))
    sys.exit(0 if not fails else 1)


if __name__ == '__main__':
    main(sys.argv[1])
