"""QC-01 inputs (plan v1 §2): five new conditions over the NQ-01 panel (sole source: NQ data/inputs-r01.json).
LB  label-marked record, generic question BEFORE the record, default window (after the record).
NA  plain record, name question AFTER the record, default window (question + instruction + template tail).
LA  label-marked record, generic question AFTER the record, default window.
NA-tail / LA-tail  same text as NA / LA, window starts after the question line (boundary_text = record + newline + question).
NB (= NQ-01, name question before) is not regenerated; it is replayed from NQ-01.
python qc_make_inputs.py data/inputs-r01.json"""
import json
import sys
from pathlib import Path

NQ_INPUTS = Path(__file__).resolve().parent.parent / 'cache-name-query-order-v1-2026-11-02/data/inputs-r01.json'
LABEL = '目标条目'
GENERIC_Q = '目标条目的编号是什么？'
CONDITIONS = {'LB': ('label', 'before', 'default'), 'NA': ('name', 'after', 'default'), 'LA': ('label', 'after', 'default'),
              'NA-tail': ('name', 'after', 'tail'), 'LA-tail': ('label', 'after', 'tail')}


def label_record(nq):
    name = nq['query_name']
    rec = nq['record']
    old = f'{name}编号为'
    assert rec.count(old) == 1
    return rec.replace(old, f'{LABEL}{name}编号为')


def build(nq_rows):
    rows = []
    for cond, (spec, layout, cov) in CONDITIONS.items():
        for nq in nq_rows:
            record = label_record(nq) if spec == 'label' else nq['record']
            question = GENERIC_Q if spec == 'label' else nq['question']
            prompt = f'{question}\n{record}\n{nq["instruction"]}' if layout == 'before' else f'{record}\n{question}\n{nq["instruction"]}'
            boundary = record if cov == 'default' else f'{record}\n{question}'
            r = {k: nq[k] for k in ('base_id', 'order', 'query', 'query_name', 'instruction', 'target', 'distractors', 'listed_codes',
                                    'first_listed', 'target_position', 'binding')}
            r.update({'id': f'{cond}-{nq["id"]}', 'nq_id': nq['id'], 'condition': cond, 'specification': spec, 'layout': layout,
                      'coverage': cov, 'record': record, 'question': question, 'prompt': prompt, 'boundary_text': boundary,
                      'reference_id': nq['reference_id']})
            rows.append(r)
    return rows


def check(rows, nq_rows):
    assert len(rows) == 5 * 54 and len({r['id'] for r in rows}) == 270
    nq = {r['id']: r for r in nq_rows}
    by = {}
    for r in rows:
        by.setdefault(r['condition'], {})[r['nq_id']] = r
        n = nq[r['nq_id']]
        assert r['target'] == n['target'] and r['listed_codes'] == n['listed_codes'] and r['binding'] == n['binding']
        if r['specification'] == 'label':
            assert r['record'].count(LABEL) == 1 and f'{LABEL}{n["query_name"]}编号为{n["target"]}' in r['record']
            assert r['question'] == GENERIC_Q
        else:
            assert LABEL not in r['prompt'] and r['record'] == n['record'] and r['question'] == n['question']
        p = r['prompt']
        if r['layout'] == 'before':
            assert p.index(r['question']) < p.index(r['record'])
        else:
            assert p.index(r['record']) < p.index('\n' + r['question']) < p.index(r['instruction'])
        assert p.count(r['boundary_text'] + '\n') == 1
    for a, b in (('NA', 'NA-tail'), ('LA', 'LA-tail')):                 # tail = identical text, only the window differs
        for k in by[a]:
            assert by[a][k]['prompt'] == by[b][k]['prompt'] and by[a][k]['boundary_text'] != by[b][k]['boundary_text']
    for cond in ('LB', 'LA'):                                          # label moves with the target: same order, different record
        for sid in {r['base_id'] for r in rows}:
            recs = {by[cond][f'{sid}-ABC-{q}']['record'] for q in 'ABC'}
            assert len(recs) == 3
    return True


if __name__ == '__main__':
    nq_rows = json.load(open(NQ_INPUTS))['items']
    rows = build(nq_rows)
    check(rows, nq_rows)
    with open(sys.argv[1], 'x') as f:
        f.write(json.dumps({'schema': 1, 'plan': 'QC-01 v1', 'nq_inputs_sha256': __import__('hashlib').sha256(NQ_INPUTS.read_bytes()).hexdigest(),
                            'items': rows}, ensure_ascii=False, indent=1) + '\n')
    for c in CONDITIONS:
        print(c, repr([r for r in rows if r['condition'] == c][1]['prompt']))
