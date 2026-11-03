"""LVK-01 held-out input acceptance (tokenizer only, no weights).  Builds pipeline items for the 48 frozen new texts and the frozen token
ledger; any failure stops (no rewording).  Rules taken from the old panel (verified on all 48 old inputs): B1 window = [b+1, n-2], a = 1.0;
distractors = listed codes minus target in listed order; calibration reference = '<scenario>-ABC-A'.
CUDA_VISIBLE_DEVICES= python heldout_accept.py OUT_JSON"""
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE.parent / 'cache-native-v-write-interaction-v1-2026-11-03'))
assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
import nvw_run as NV  # noqa: E402

HELDOUT = HERE.parent / 'cache-local-v-k-design-v1-2026-11-03/heldout-inputs-r01.json'
HELDOUT_SHA = '1d772dcd6ae9d56d1b273a1d64a3e6319d1cb08c4a745a395f6c7959683bf021'


def pipeline_item(h):
    return {'id': h['id'], 'base_id': h['scenario'], 'order': h['order'], 'query': h['query'], 'query_name': h['binding'][h['query']][0],
            'target': h['target'], 'distractors': [c for c in h['listed_codes'] if c != h['target']], 'listed_codes': h['listed_codes'],
            'first_listed': h['first_listed'], 'binding': h['binding'], 'record': h['record'], 'question': h['question'],
            'instruction': h['instruction'], 'prompt': h['prompt'], 'boundary_text': h['boundary_text'], 'reference_id': f"{h['scenario']}-ABC-A"}


def main(out):
    assert NV.exp.sha(HELDOUT) == HELDOUT_SHA, 'held-out file hash'
    sys.path.insert(0, str(NV.T1.SOURCE))
    from control_engine import encode_text
    from transformers import AutoTokenizer
    src = NV.exp.read(NV.T1.SOURCE / 'contract.json')['source']
    tok = AutoTokenizer.from_pretrained(src['model_path'])
    H = NV.exp.read(HELDOUT)['items']
    old = {t['id']: t for t in NV.items()}
    qi = NV.QCDR.qc_items()
    kuc = NV.kuc_records()
    fails, ledger = [], {}
    assert len(H) == 48 and len({h['id'] for h in H}) == 48 and len({h['prompt'] for h in H}) == 48, 'ids/prompts not unique'
    assert {h['old_id'] for h in H} == set(old), 'old ids mismatch'
    for h in H:
        it = pipeline_item(h)
        o = old[h['old_id']]
        op, oq = o['plan'], qi[o['plan']['qc_broad_id']]
        f = []
        if h['scenario'] != op['base_id'] or (h['order'], h['query']) != (oq['order'], oq['query']):
            f.append('scenario/order/query differs from old')
        if h['binding'][h['query']][1] != h['target'] or h['binding'][h['query']][0] not in h['question']:
            f.append('binding')
        if h['listed_codes'][0] != h['first_listed'] or sorted(h['listed_codes']) != sorted(v[1] for v in h['binding'].values()):
            f.append('listed codes')
        if (h['target'] == h['first_listed']) != (oq['target'] == oq['first_listed']):
            f.append('target-first status differs from old')
        if h['boundary_text'] not in h['prompt'] or not h['prompt'].startswith(h['boundary_text']):
            f.append('boundary text')
        if h['old_calibration_reference_id'] != oq['reference_id']:
            f.append('calibration reference')
        try:
            q_shared, t2, d2 = NV.QSTR.shared_tokens(tok, it)
        except AssertionError as e:
            f.append(f'shared tokens: {e}')
            q_shared = None
        ctx = NV.exp.contexts_for(tok, [it])[it['id']]
        seg = NV.PK.label_tokens(tok, ctx, it['boundary_text'], encode_text)
        if seg['straddling_tokens']:
            f.append('straddling tokens')
        b, n = seg['b'], seg['n']
        p_, e_ = b + 1, n - 2
        if not (0 < p_ <= e_ < n - 1):
            f.append('window')
        if n > 2 * op['n'] or (e_ - p_ + 1) > 2 * op['L']:
            f.append('length > 2x old')
        for d in NV.DIRECTIONS:
            fF_old = kuc[h['old_id']]['directions'][d]['fF']
            if h['forced_prefix_ids_by_direction'][d] != fF_old:
                f.append(f'fF attachment != KUC old fF ({d})')
            if q_shared is not None and q_shared != fF_old:
                f.append(f'new shared first token != fF ({d})')
        old_q = NV.QSTR.shared_tokens(tok, oq)[0]
        if any(kuc[h['old_id']]['directions'][d]['fF'] != old_q for d in NV.DIRECTIONS):
            f.append('old fF != old shared first token')
        ledger[h['id']] = {'item': it, 'plan': {'old_id': h['old_id'], 'base_id': h['scenario'], 'b': b, 'n': n, 'p': p_, 'e': e_, 'L': e_ - p_ + 1,
                                                 'prompt_token_sha256': NV.exp.digest(seg['ids'])},
                           'tokens': {'q_shared': q_shared, 'target_second': t2 if q_shared is not None else None, 'distractor_second': d2 if q_shared is not None else None},
                           'old': {'n': op['n'], 'L': op['L']}, 'failures': f}
        if f:
            fails.append((h['id'], f))
    tot = {'prefix_tokens_new': sum(v['plan']['b'] + 1 for v in ledger.values()), 'formation_tokens_new': sum(5 * v['plan']['L'] for v in ledger.values()),
           'prefix_tokens_old': sum(o['plan']['b_b'] + 1 for o in old.values()), 'formation_tokens_old': sum(5 * o['plan']['L'] for o in old.values())}
    res = {'status': 'passed' if not fails else 'failed', 'heldout_sha256': HELDOUT_SHA, 'n': len(H), 'failures': fails, 'totals': tot, 'items': ledger}
    with open(out, 'x') as fo:
        fo.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({k: v for k, v in res.items() if k != 'items'}, ensure_ascii=False))
    sys.exit(0 if not fails else 1)


if __name__ == '__main__':
    main(sys.argv[1])
