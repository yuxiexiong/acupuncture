"""NQ-01 panel generator (plan v2 §2): 6 scenarios x 3 cyclic orders x 3 queried items = 54 prompts.  Query before the record,
record without a target label, fixed trailing instruction.  python make_inputs.py data/inputs-r01.json"""
import json
import sys

SCENARIOS = [('NQ01', '仓储台账', [('铁锚', 'U17'), ('竹篮', 'U43'), ('陶罐', 'U86')]),
             ('NQ02', '巡检名册', [('松针', 'V28'), ('石桥', 'V54'), ('芦苇', 'V91')]),
             ('NQ03', '图纸目录', [('齿轮', 'W35'), ('弹簧', 'W62'), ('轴承', 'W19')]),
             ('NQ04', '标本登记', [('蝶翼', 'X46'), ('贝壳', 'X73'), ('羽毛', 'X28')]),
             ('NQ05', '航线编排', [('北港', 'Y57'), ('南屿', 'Y14'), ('东滩', 'Y82')]),
             ('NQ06', '乐谱清单', [('短笛', 'Z63'), ('竖琴', 'Z39'), ('铜锣', 'Z15')])]
ORDERS = ('ABC', 'BCA', 'CAB')
QUERIES = ('A', 'B', 'C')
INSTRUCTION = '请根据上面的记录，简短回答，只需给出编号。'
POS = ('first', 'middle', 'last')


def build():
    rows = []
    for sid, prefix, ents in SCENARIOS:
        ent = dict(zip('ABC', ents))
        for order in ORDERS:
            record = prefix + '：' + '，'.join(f'{ent[k][0]}编号为{ent[k][1]}' for k in order) + '。'
            for q in QUERIES:
                question = f'{ent[q][0]}的编号是什么？'
                listed = [ent[k][1] for k in order]
                rows.append({'id': f'{sid}-{order}-{q}', 'base_id': sid, 'order': order, 'query': q, 'query_name': ent[q][0],
                             'record': record, 'question': question, 'instruction': INSTRUCTION,
                             'prompt': f'{question}\n{record}\n{INSTRUCTION}', 'reference_id': f'{sid}-ABC-A',
                             'target': ent[q][1], 'distractors': [c for c in listed if c != ent[q][1]],
                             'listed_codes': listed, 'first_listed': listed[0], 'target_position': POS[order.index(q)],
                             'binding': {k: list(v) for k, v in ent.items()}})
    return rows


def check(rows):
    assert len(rows) == 54 and len({r['id'] for r in rows}) == 54
    for sid, _, _ in SCENARIOS:
        rs = [r for r in rows if r['base_id'] == sid]
        assert sorted((r['order'], r['query']) for r in rs) == sorted((o, q) for o in ORDERS for q in QUERIES)
        for q in QUERIES:                                         # each item first/middle/last exactly once as the queried item
            assert sorted(r['target_position'] for r in rs if r['query'] == q) == sorted(POS)
        for o in ORDERS:                                          # same order -> identical record bytes
            assert len({r['record'] for r in rs if r['order'] == o}) == 1
        for q in QUERIES:                                         # same query -> identical question, binding unchanged
            assert len({r['question'] for r in rs if r['query'] == q}) == 1
        assert len({json.dumps(r['binding'], ensure_ascii=False) for r in rs}) == 1
    for r in rows:
        assert '目标' not in r['prompt'] and r['prompt'].count(r['record'] + '\n') == 1
        assert r['prompt'].index(r['question']) < r['prompt'].index(r['record']) < r['prompt'].index(INSTRUCTION)
    return True


if __name__ == '__main__':
    rows = build()
    check(rows)
    with open(sys.argv[1], 'x') as f:
        f.write(json.dumps({'schema': 1, 'plan': 'NQ-01 v2', 'items': rows}, ensure_ascii=False, indent=1) + '\n')
    print(len(rows), rows[0]['prompt'])
