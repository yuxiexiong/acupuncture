"""WIN-01 fact-answer auto judge (pre-written rule; implements stage2 RULE: core answer = last explicit conclusion).
Main readout is Y = follows_fact (1) vs not (0); the finer label is auxiliary.

ACCEPTANCE (written before any judge output was seen, 2026-11-04):
  on every stage2 G record with a blind label (both panels):
    A1  Y agreement >= 0.95 and Cohen kappa(Y) >= 0.90
    A2  agreement >= 0.95 on records whose blind label is follows_fact or other_fact
    A3  null demo: kappa against labels shuffled within panel (seed 20261104) within [-0.05, 0.05]
  plus synthetic cases (selftest) where the judge must return each label, and a case built to be judged wrong.
Fail of A1/A2 => auto judge not used; fall back to blind reading (plan v2 §7 option a/b)."""
import json, re, sys, random

UNSURE = re.compile('无法确定|不能确定|无法判断|不能判断|无法回答|不能回答|题目矛盾|信息不足|没有(?:给出|提供)')


def _diff(a, b):
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    j = 0
    while j < min(len(a), len(b)) - i and a[-1 - j] == b[-1 - j]:
        j += 1
    while i > 0 and a[i - 1].isdigit() and (a[i:i + 1].isdigit() or b[i:i + 1].isdigit()):
        i -= 1                                   # keep whole numbers: 17 vs 18 -> '17','18', not '7','8'
    while j > 0 and a[len(a) - j].isdigit() and (a[len(a) - j - 1:len(a) - j].isdigit() or b[len(b) - j - 1:len(b) - j].isdigit()):
        j -= 1
    return a[i:len(a) - j], b[i:len(b) - j], a[len(a) - j:]


def patterns(choices, target):
    t, o, suf = _diff(choices[target], choices[1 - target])
    suf = suf.rstrip('。')

    def pats(k):
        kk = re.escape(k)
        if k.isdigit():
            kk = rf'(?<!\d){kk}(?!\d)'
        levels = [re.compile(kk + r'\s*' + re.escape(suf[:n])) for n in (2, 1) if len(suf) >= n]
        return levels + [re.compile(kk)]
    return pats(t), pats(o)


def _last(pats, text):
    pos = [m.start() for p in pats for m in p.finditer(text)]
    return max(pos) if pos else -1


def judge(answer, choices, target):
    a = re.sub(r'<think>.*?</think>', '', answer or '', flags=re.S).strip()
    if not a:
        return 'not_delivered'
    tp, op = patterns(choices, target)
    for lv in range(len(tp)):
        t, o = _last([tp[lv]], a), _last([op[lv]], a)
        if t >= 0 or o >= 0:
            win, pos = ('follows_fact', t) if t > o else ('other_fact', o)
            if UNSURE.search(a[pos:]):
                return 'other_wrong'
            return win
    return 'other_wrong' if UNSURE.search(a) else 'not_delivered'


def kappa(x, y):
    n = len(x); po = sum(a == b for a, b in zip(x, y)) / n
    p1, q1 = sum(x) / n, sum(y) / n
    pe = p1 * q1 + (1 - p1) * (1 - q1)
    return (po - pe) / (1 - pe) if pe < 1 else float('nan')


def selftest():
    ch = ['钥匙在红抽屉。', '钥匙在蓝抽屉。']
    cases = [('钥匙在红抽屉。', 'follows_fact'), ('根据记录，票据在蓝抽屉，所以钥匙在红抽屉。', 'follows_fact'),
             ('钥匙在蓝抽屉。', 'other_fact'), ('无法确定钥匙在哪个抽屉。', 'other_wrong'), ('', 'not_delivered'),
             ('钥匙在红抽屉？不对，无法确定。', 'other_wrong'), ('好的。', 'not_delivered')]
    for txt, want in cases:
        assert judge(txt, ch, 0) == want, (txt, judge(txt, ch, 0), want)
    ch2 = ['现在共有17本书。', '现在共有18本书。']
    assert judge('原有 12 本，又买 5 本，共 17 本。', ch2, 0) == 'follows_fact'
    assert judge('共有 117 本书。', ch2, 0) == 'not_delivered'  # digit boundary
    # a case built so the rule judges it wrong (later mention of the other fact after the conclusion):
    wrong = judge('钥匙在红抽屉，而不是蓝抽屉。', ch, 0)
    return {'selftest': 'PASS', 'known_failure_case': wrong}


if __name__ == '__main__':
    print(selftest())
    items = {r['id']: r for r in json.load(open(sys.argv[1]))}
    rows = [json.loads(l) for l in open(sys.argv[2])]   # {panel, item_id, label, answer}
    Y = [int(r['label'] == 'follows_fact') for r in rows]
    J = [judge(r['answer'], items[r['item_id']]['choices'], items[r['item_id']]['target_index']) for r in rows]
    JY = [int(j == 'follows_fact') for j in J]
    agree = sum(a == b for a, b in zip(Y, JY)) / len(Y)
    dec = [(a, b) for a, b, r in zip(Y, JY, rows) if r['label'] in ('follows_fact', 'other_fact')]
    rnd = random.Random(20261104); sh = []
    for p in sorted({r['panel'] for r in rows}):
        lab = [y for y, r in zip(Y, rows) if r['panel'] == p]; rnd.shuffle(lab); sh += lab
    order = [i for p in sorted({r['panel'] for r in rows}) for i, r in enumerate(rows) if r['panel'] == p]
    k_null = kappa([JY[i] for i in order], sh)
    from collections import Counter
    conf = Counter((r['label'], j) for r, j in zip(rows, J))
    res = {'n': len(rows), 'Y_agreement': agree, 'kappa': kappa(Y, JY),
           'decisive_n': len(dec), 'decisive_agreement': sum(a == b for a, b in dec) / len(dec), 'kappa_shuffled_null': k_null,
           'A1': agree >= 0.95 and kappa(Y, JY) >= 0.90, 'A2': sum(a == b for a, b in dec) / len(dec) >= 0.95, 'A3': -0.05 <= k_null <= 0.05,
           'confusion': {f'{a}->{b}': c for (a, b), c in sorted(conf.items())},
           'disagreements': [dict(r, judged=j) for r, j, y, jy in zip(rows, J, Y, JY) if y != jy][:400]}
    json.dump(res, open(sys.argv[3], 'w'), ensure_ascii=False, indent=1)
    print({k: v for k, v in res.items() if k not in ('disagreements',)})
