"""QCD-01 zero-GPU failure-step analysis (post hoc, descriptive; not in the freeze).  Locates every natural output at three
decision points using stored token ids, first-step values and step-2 watch values:
  D1 start: first token = shared first token q / a stop token / other.
  D2 selection (only if D1 = q): natural step-2 token = target / first-listed / other listed code / other token.
  D3 completion (only if a whole code was emitted first): token right after the first complete code = stop (single delivery) /
     separator or text (continuation; 'listing' if a second listed code follows).
Plus per-policy nat -> V transition tables and the cells that V restoration breaks.
CUDA_VISIBLE_DEVICES= python analysis/failure_steps_r01.py OUT_JSON"""
import json
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'cache-name-query-order-v1-2026-11-02'))
import qcd_run as R  # noqa: E402
import nq_analysis as NQA  # noqa: E402

STOP = (248044, 248046)
DIRS = R.DIRECTIONS
POL = {'B1': ('T_b|{d}|nat', 'T_b|{d}|V_b'), 'N1': ('T_u|{d}|nat', 'T_u|{d}|V_b'), 'E1': ('E1|{d}|nat', 'E1|{d}|V_b'),
       'N-A': ('N-A|{d}|nat', 'N-A|{d}|V_b'), 'N-Q': ('N-Q|{d}|nat', 'N-Q|{d}|V_b'), 'B-A': ('B-A|{d}|nat', 'B-A|{d}|V_b'),
       'B-Q': ('B-Q|{d}|nat', 'B-Q|{d}|V_b')}


def mean(x):
    return st.mean(x) if x else None


def main(out):
    from transformers import AutoTokenizer
    src = R.exp.read(R.T1.SOURCE / 'contract.json')['source']
    tok = AutoTokenizer.from_pretrained(src['model_path'])
    g, s = NQA.load(HERE / 'runs/gformal-r01'), NQA.load(HERE / 'runs/sformal-r01')
    recs = {i: dict(g[i], trajectories={**g[i]['trajectories'], **s[i]['trajectories']}) for i in g}
    code_ids = {}

    def codes_of(r):
        it = r['item']
        if it['id'] not in code_ids:
            code_ids[it['id']] = {c: tok.encode(c, add_special_tokens=False) for c in it['listed_codes']}
        return code_ids[it['id']]

    def locate(r, name):
        t = r['trajectories'][name]
        it = r['item']
        ids = t['ids']
        cid = codes_of(r)
        q = r['q_shared']
        tgt, first = it['target'], it['first_listed']
        sec = {v[1]: c for c, v in cid.items()}
        cell = NQA.cell(r, name)
        row = {'main': cell['main'], 'delivered': cell['delivered']}
        row['D1'] = 'q' if ids[0] == q else ('stop' if ids[0] in STOP else 'other')
        row['E'] = t['first']['q_shared'] - max(t['first']['stop'].values())
        w = t['diag']['watch']
        z = {c: w[str(cid[c][1])] for c in cid}
        row['M'] = z[tgt] - max(v for c, v in z.items() if c != tgt)
        row['F'] = (z[first] - z[tgt]) if first != tgt else None          # first-listed lead over target (diag)
        row['target_first'] = first == tgt
        if row['D1'] == 'q' and len(ids) > 1:
            c2 = sec.get(ids[1])
            row['D2'] = 'target' if c2 == tgt else ('first_listed' if c2 == first else ('other_code' if c2 else 'other_token'))
            code = c2
            if code and ids[:len(cid[code])] == cid[code]:
                k = len(cid[code])
                nxt = ids[k] if k < len(ids) else None
                rest = tok.decode(ids[k:], skip_special_tokens=False)
                if nxt in STOP:
                    row['D3'] = 'stop'
                else:
                    others = [c for c in cid if c != code and c in rest]
                    row['D3'] = 'listing' if others else 'continue_text'
                row['D3_next'] = tok.decode([nxt]) if nxt is not None else None
        return row

    res = {'by_policy': {}, 'transitions': {}, 'broken': {}}
    for tmpl in ('NA', 'LA'):
        ids_t = sorted(i for i in recs if recs[i]['plan_text']['template'] == tmpl)
        for d in DIRS:
            for p, (na, va) in POL.items():
                key = f'{tmpl}|{d}|{p}'
                rows_n = {i: locate(recs[i], na.format(d=d)) for i in ids_t}
                rows_v = {i: locate(recs[i], va.format(d=d)) for i in ids_t}
                summ = {}
                for arm, rows in (('nat', rows_n), ('V', rows_v)):
                    D1 = Counter(x['D1'] for x in rows.values())
                    D2 = Counter(x.get('D2') for x in rows.values() if x['D1'] == 'q')
                    D2_nf = Counter(x.get('D2') for x in rows.values() if x['D1'] == 'q' and not x['target_first'])
                    D3 = Counter(x.get('D3') for x in rows.values() if 'D3' in x)
                    D3_by_D2 = {k: dict(Counter(x.get('D3') for x in rows.values() if x.get('D2') == k)) for k in ('target', 'first_listed', 'other_code')}
                    byD2M = {k: mean([x['M'] for x in rows.values() if x.get('D2') == k and not x['target_first']]) for k in ('target', 'first_listed')}
                    summ[arm] = {'D1': dict(D1), 'D2': dict(D2), 'D2_nonfirst': dict(D2_nf), 'D3': dict(D3), 'D3_by_D2': D3_by_D2,
                                 'M_nonfirst_by_D2': byD2M, 'E_mean': mean([x['E'] for x in rows.values()]),
                                 'main': dict(Counter(x['main'] for x in rows.values()))}
                res['by_policy'][key] = summ
                tr = Counter((rows_n[i]['main'], rows_v[i]['main']) for i in ids_t)
                res['transitions'][key] = {f'{a}->{b}': n for (a, b), n in sorted(tr.items())}
                br = [i for i in ids_t if rows_n[i]['delivered'] and not rows_v[i]['delivered']]
                if br:
                    res['broken'][key] = [{'id': i, 'V': {k: rows_v[i].get(k) for k in ('main', 'D1', 'D2', 'D3', 'M', 'E')},
                                           'target_position': recs[i]['item']['target_position'],
                                           'V_text': recs[i]['trajectories'][va.format(d=d)]['text'][:60]} for i in br]
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print('written', len(res['by_policy']))


if __name__ == '__main__':
    main(sys.argv[1])
