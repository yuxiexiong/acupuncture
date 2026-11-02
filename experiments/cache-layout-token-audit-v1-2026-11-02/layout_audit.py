"""CPU-only token-position audit of candidate layouts for the next experiment (design input, no model run).
Texts: the 54 NQ-01 scenario x order x query cells, in two target-specification styles (name: '{item}的编号是什么？';
label: record marks the queried item with '目标条目', question '目标条目的编号是什么？') and three layouts:
  L0 question -> record -> instruction   (NQ / QC-NB style; reference)
  L1 record -> question -> instruction   (QC / QCD NA, LA)
  L2 record -> instruction -> question   (question last; instruction reworded, see below)
  L2s record -> instruction -> question  (question last; instruction identical to L0/L1)
Instruction (L0/L1): '请根据上面的记录，简短回答，只需给出编号。'; in L2 the question is the last line, so the instruction is reworded
to end before it: '请根据上面的记录，简短回答下面的问题，只需给出编号。' (stated, not hidden).
For every prompt: real-tokenizer ids, per-token segment label (head / record / question / instruction / tail), segment token
intervals, straddling tokens at segment boundaries, b = last record token (frozen label_tokens semantics), read-out n-1.
Candidate windows (all end <= n-2): B = [b+1, n-2]; E20 = first 20 after b; N20 = last 20 before the read-out; Q = exactly the
question tokens.  For each window: covered tokens per segment, distance of its last token to the read-out, number of
uninjected formation updates after it.  python layout_audit.py OUT_JSON OUT_MD"""
import json
import sys
from collections import Counter
from pathlib import Path

E = Path(__file__).resolve().parent.parent
QC = E / 'cache-query-layout-coverage-v1-2026-11-02'
sys.path.insert(0, str(QC))
import qc_run as R  # noqa: E402

INSTR = '请根据上面的记录，简短回答，只需给出编号。'
INSTR_L2 = '请根据上面的记录，简短回答下面的问题，只需给出编号。'
LABEL, GQ = '目标条目', '目标条目的编号是什么？'


def texts(nq):
    rows = []
    for r in nq:
        name = r['query_name']
        rec_n = r['record']
        rec_l = rec_n.replace(f'{name}编号为', f'{LABEL}{name}编号为')
        for spec, rec, q in (('name', rec_n, r['question']), ('label', rec_l, GQ)):
            for lay in ('L0', 'L1', 'L2', 'L2s'):
                if lay == 'L0':
                    parts = [('question', q), ('record', rec), ('instruction', INSTR)]
                elif lay == 'L1':
                    parts = [('record', rec), ('question', q), ('instruction', INSTR)]
                elif lay == 'L2':
                    parts = [('record', rec), ('instruction', INSTR_L2), ('question', q)]
                else:                                   # L2s: same instruction text as L0/L1, question moved last
                    parts = [('record', rec), ('instruction', INSTR), ('question', q)]
                rows.append({'id': f'{spec}-{lay}-{r["id"]}', 'spec': spec, 'layout': lay, 'nq_id': r['id'], 'base_id': r['base_id'],
                             'parts': parts, 'prompt': '\n'.join(p for _, p in parts), 'record': rec, 'question': q,
                             'target_position': r['target_position']})
    return rows


def main(out_json, out_md):
    from transformers import AutoTokenizer
    sys.path.insert(0, str(R.T1.SOURCE))
    from control_engine import encode_text
    tok = AutoTokenizer.from_pretrained(R.exp.read(R.T1.SOURCE / 'contract.json')['source']['model_path'])
    nq = R.NQR.items()
    rows = texts(nq)
    ctx = R.exp.contexts_for(tok, rows)
    res, agg = [], {}
    q_ids = {}
    for r in rows:
        c = ctx[r['id']]
        ids = encode_text(tok, c)
        enc = tok(c, add_special_tokens=False, return_offsets_mapping=True)
        assert enc['input_ids'] == ids
        start = c.index(r['prompt'])
        spans, pos = {}, start
        for name, txt in r['parts']:
            spans[name] = (pos, pos + len(txt))
            pos += len(txt) + 1
        lab, straddle = [], []
        for k, (a, b) in enumerate(enc['offset_mapping']):
            seg = 'head' if a < start else ('tail' if a >= pos - 1 else None)
            if seg is None:
                seg = next((nm for nm, (s, e) in spans.items() if s <= a < e), 'newline')
            for nm, (s, e) in spans.items():
                if a < s < b or a < e < b:
                    straddle.append((k, nm))
            lab.append(seg)
        n = len(ids)
        seg_iv = {nm: [min(k for k, x in enumerate(lab) if x == nm), max(k for k, x in enumerate(lab) if x == nm)] for nm in ('record', 'question', 'instruction')}
        b = seg_iv['record'][1]
        while lab[b + 1] == 'newline':          # label_tokens' boundary includes the record's trailing newline
            b += 1
        seg_b = R.PK.label_tokens(tok, c, r['record'], encode_text)
        assert seg_b['b'] == b and seg_b['ids'] == ids, (r['id'], seg_b['b'], b)
        qs, qe = seg_iv['question']
        wins = {'B': (b + 1, n - 2), 'E20': (b + 1, b + 20), 'N20': (n - 21, n - 2), 'Q': (qs, qe)}
        wrow = {}
        for wn, (s, e) in wins.items():
            if e > n - 2 or s <= b and wn != 'Q':
                wrow[wn] = None
                continue
            cov = Counter(lab[k] for k in range(s, e + 1))
            wrow[wn] = {'start': s, 'end': e, 'len': e - s + 1, 'covers': dict(cov), 'end_to_readout': (n - 1) - e,
                        'uninjected_updates_after': max(0, (n - 2) - e), 'inside_formation_window': s > b}
        q_ids.setdefault((r['spec'], r['nq_id']), {})[r['layout']] = ids[qs:qe + 1]
        row = {'id': r['id'], 'spec': r['spec'], 'layout': r['layout'], 'n': n, 'b': b, 'segments': seg_iv,
               'straddle': straddle, 'windows': wrow, 'prompt': r['prompt']}
        res.append(row)
        key = (r['spec'], r['layout'])
        a = agg.setdefault(key, {'n': Counter(), 'straddle': 0, 'win': {}})
        a['n'][n] += 1
        a['straddle'] += bool(straddle)
        for wn, w in wrow.items():
            if w:
                a['win'].setdefault(wn, Counter())[(w['len'], json.dumps(w['covers'], ensure_ascii=False, sort_keys=True), w['end_to_readout'], w['uninjected_updates_after'])] += 1
            else:
                a['win'].setdefault(wn, Counter())['n/a'] += 1
    same_q = Counter(len({tuple(v) for v in d.values()}) == 1 for d in q_ids.values())
    with open(out_json, 'x') as f:
        f.write(json.dumps({'rows': res, 'question_token_ids_identical_across_layouts': dict(same_q)}, ensure_ascii=False, indent=1) + '\n')
    lines = ['# 候选布局 token 位置（CPU 审计，真实分词器）', '',
             f'问题 token 在三种布局中是否逐位相同（按 规格×输入）：{dict(same_q)}', '',
             '| 规格 | 布局 | 提示长度 n | 跨段 token | 窗口 | 长度 | 覆盖（段: token 数） | 末 token 到读出 | 窗口后未注入更新 | 文本数 |', '|---|---|---|---|---|---:|---|---:|---:|---:|']
    for (spec, lay), a in sorted(agg.items()):
        for wn, cnt in a['win'].items():
            for k, m in sorted(cnt.items(), key=lambda x: -x[1]):
                if k == 'n/a':
                    lines.append(f'| {spec} | {lay} | {dict(a["n"])} | {a["straddle"]} | {wn} | — | 不适用 | — | — | {m} |')
                else:
                    ln, cov, d, u = k
                    lines.append(f'| {spec} | {lay} | {dict(a["n"])} | {a["straddle"]} | {wn} | {ln} | {cov} | {d} | {u} | {m} |')
    ex = {lay: next(r for r in res if r['spec'] == 'name' and r['layout'] == lay) for lay in ('L0', 'L1', 'L2', 'L2s')}
    lines += ['', '## 例（name，第一个输入）', '']
    for lay, r in ex.items():
        lines.append(f'- {lay}：`{r["prompt"]!r}`，n={r["n"]}，b={r["b"]}，段区间 {r["segments"]}')
    Path(out_md).write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines[:6]))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
