"""NWC-01 confirmation panel: 6 structure families x 4 new base situations x 3 versions = 72 inputs.  Text is fixed here, before any model output.
Rules (all deterministic):
  - family template, header and code letter are those of the existing panels; entity names below were not used in either earlier panel;
  - codes are the family letter + two distinct digits 1-9; numbers used by the earlier panels in the same family are excluded; within a record the
    three codes have distinct first digits and distinct second digits; no number is reused inside a family;
    numbers are drawn by random.Random(20261105 + family index) from the remaining pool (greedy, fixed order);
  - each base situation has two code sets: version a (query = second-listed) and version c (query = first-listed) use set 1, version b
    (query = third-listed) uses set 2;  stratum N = versions a, b;  stratum F = version c;
  - partner of a stratum-N input for the cross-input arm: same family, next situation (cyclic), same version.
python3 -I make_panel.py OUT_JSON"""
import json
import random
import sys

INSTR = '请根据上面的记录，简短回答，只需给出编号。'
FAM = {
    'NQ01': ('仓储台账', 'U', [17, 43, 86, 94, 25, 68], [['麻绳', '铜壶', '蜡烛'], ['油桶', '布袋', '锡罐'], ['木桶', '铁钉', '砖块'], ['草席', '瓦片', '石磨']]),
    'NQ02': ('巡检名册', 'V', [28, 54, 91, 83, 16, 47], [['柳树', '石阶', '苔藓'], ['竹林', '凉亭', '荷叶'], ['古井', '梧桐', '篱笆'], ['山泉', '杏树', '木栈']]),
    'NQ03': ('图纸目录', 'W', [35, 62, 19, 97, 24, 58], [['活塞', '螺栓', '皮带'], ['阀门', '链条', '滑轮'], ['飞轮', '铆钉', '曲柄'], ['连杆', '销钉', '凸轮']]),
    'NQ04': ('标本登记', 'X', [46, 73, 28, 92, 15, 64], [['蝉蜕', '珊瑚', '树皮'], ['蛇蜕', '松果', '蛾翅'], ['鹿角', '海星', '蕨叶'], ['龟甲', '蚌壳', '苔片']]),
    'NQ05': ('航线编排', 'Y', [57, 14, 82, 93, 26, 48], [['东湾', '西屿', '南港'], ['北滩', '东礁', '西岛'], ['南岬', '北湾', '东屿'], ['西港', '南滩', '北礁']]),
    'NQ06': ('乐谱清单', 'Z', [63, 39, 15, 84, 27, 51], [['琵琶', '唢呐', '古筝'], ['扬琴', '洞箫', '腰鼓'], ['月琴', '木鱼', '铜钹'], ['柳琴', '排箫', '堂鼓']]),
}
USED_ENTITIES = {'铁锚', '竹篮', '陶罐', '瓷瓶', '木箱', '纸袋', '松针', '石桥', '芦苇', '藤蔓', '枫叶', '木桥', '齿轮', '弹簧', '轴承', '转轴', '螺母', '垫圈',
                 '蝶翼', '贝壳', '羽毛', '兽骨', '花瓣', '鱼鳞', '北港', '南屿', '东滩', '南礁', '西湾', '北岛', '短笛', '竖琴', '铜锣', '木鼓', '长笛', '二胡'}
VERS = {'a': ('B', 0, 'N'), 'b': ('C', 1, 'N'), 'c': ('A', 0, 'F')}       # version: (query slot, code set, stratum)


def code_sets(fi, used):
    rng = random.Random(20261105 + fi)
    pool = [10 * a + b for a in range(1, 10) for b in range(1, 10) if a != b and 10 * a + b not in used]
    rng.shuffle(pool)
    out = []
    while len(out) < 8:
        tri = []
        for x in list(pool):
            if all(x // 10 != y // 10 and x % 10 != y % 10 for y in tri):
                tri.append(x)
                pool.remove(x)
                if len(tri) == 3:
                    break
        assert len(tri) == 3
        out.append(tri)
    return out


def main(out):
    items, seen = [], set()
    for fi, (fam, (head, letter, used, sits)) in enumerate(sorted(FAM.items())):
        cs = code_sets(fi, set(used))
        for k, ents in enumerate(sits):
            assert not (set(ents) & USED_ENTITIES) and not (set(ents) & seen)
            seen |= set(ents)
            for ver, (slot, cset, stratum) in VERS.items():
                codes = [f'{letter}{x}' for x in cs[2 * k + cset]]
                binding = {s: [e, c] for s, e, c in zip('ABC', ents, codes)}
                record = f'{head}：' + '，'.join(f'{e}编号为{c}' for e, c in zip(ents, codes)) + '。'
                q = f'{binding[slot][0]}的编号是什么？'
                items.append({'id': f'NWC-{fam}-S{k + 1}-{ver}', 'scenario': fam, 'situation': f'{fam}-S{k + 1}', 'version': ver, 'stratum': stratum,
                              'order': 'ABC', 'query': slot, 'target': binding[slot][1], 'first_listed': codes[0], 'listed_codes': codes, 'binding': binding,
                              'record': record, 'question': q, 'instruction': INSTR, 'prompt': f'{record}\n{q}\n{INSTR}', 'boundary_text': record,
                              'partner_id': (f'NWC-{fam}-S{(k + 1) % 4 + 1}-{ver}' if stratum == 'N' else None)})
    assert len(items) == 72 and len({i['id'] for i in items}) == 72 and len({i['prompt'] for i in items}) == 72
    assert sum(i['stratum'] == 'N' for i in items) == 48 and all((i['target'] == i['first_listed']) == (i['stratum'] == 'F') for i in items)
    ids = {i['id'] for i in items}
    assert all(i['partner_id'] in ids and i['partner_id'] != i['id'] for i in items if i['stratum'] == 'N')
    doc = {'plan': 'NWC-01-r02', 'status': 'text_frozen_before_model_outputs; tokenizer_acceptance_pending',
           'generation': 'make_panel.py: fixed entity lists; codes drawn by a seeded rule excluding numbers used by earlier panels; no output-based filtering',
           'items': items}
    with open(out, 'x', encoding='utf-8') as f:
        f.write(json.dumps(doc, ensure_ascii=False, indent=1) + '\n')
    for i in items[:6]:
        print(i['id'], i['stratum'], i['record'], i['question'], '->', i['target'], '| partner', i['partner_id'])


if __name__ == '__main__':
    main(sys.argv[1])
