# zero-GPU, descriptive: does the forced-prefix margin predict per-input natural errors?
import json, sys, statistics as st, torch
from pathlib import Path
sys.path.insert(0, '/workspace/acupuncture/experiments/cache-query-state-transfer-v1-2026-11-02')
import qst_core as QK
E = Path('/workspace/acupuncture/experiments')
D = ['N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'N_L00_C1343_D-1']
qkd, qkf = {}, {}
for w in sorted((E / 'cache-k-computation-diagnostic-v1-2026-11-03/runs/formal-r02').glob('worker-*')):
    if not w.is_dir(): continue
    for rel in json.load(open(w / 'receipt.json'))['record_hashes']:
        r = json.load(open(w / rel)); qkd[r['text']] = r
for w in sorted((E / 'cache-qk-component-factor-v1-2026-11-02/runs/formal-r01').glob('worker-*')):
    if not w.is_dir(): continue
    for rel in json.load(open(w / 'receipt.json'))['record_hashes']:
        r = json.load(open(w / rel)); qkf[r['text']] = r['trajectories']
def yfull(t, it): return int(QK.y_full(t['text'], t['termination'], it['target'], it['listed_codes'], it['question']))
def auroc(pos, neg):  # P(score_pos > score_neg) with ties 0.5
    if not pos or not neg: return None
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))
for d in D:
    rows = []
    for i, r in qkd.items():
        it = r['item']
        tV = r['c1343_trajectories']['V'] if d == D[3] else qkf[i][f'V|{d}']
        rows.append({'s': r['scenario'], 'pos': it['target_position'], 'yV': yfull(tV, it), 'MF': r['arms'][d]['F']['M'], 'MV': r['arms'][d]['V']['M']})
    wrong = [x for x in rows if x['yV'] == 0]; right = [x for x in rows if x['yV'] == 1]
    nf = [x for x in rows if x['pos'] != 'first']
    print('   NON-FIRST only: n', len(nf), 'wrong', sum(1-x['yV'] for x in nf), 'AUROC(M_F)', auroc([x['MF'] for x in nf if x['yV']], [x['MF'] for x in nf if not x['yV']]), 'mean drop right %.2f wrong %s' % (st.mean(x['MF']-x['MV'] for x in nf if x['yV']) if any(x['yV'] for x in nf) else float('nan'), ('%.2f' % st.mean(x['MF']-x['MV'] for x in nf if not x['yV'])) if any(not x['yV'] for x in nf) else '-'), 'AUROC(drop: wrong>right)', auroc([x['MF']-x['MV'] for x in nf if not x['yV']], [x['MF']-x['MV'] for x in nf if x['yV']]))
    agree = sum((x['MV'] > 0) == (x['yV'] == 1) for x in rows)
    a_MF = auroc([x['MF'] for x in right], [x['MF'] for x in wrong])
    a_MV = auroc([x['MV'] for x in right], [x['MV'] for x in wrong])
    print(d, f'V wrong {len(wrong)}/48 | sign(M_V) agrees with V correctness {agree}/48 | AUROC(M_F: right vs wrong) {a_MF} | AUROC(M_V) {a_MV}')
    print('   wrong by target position', {p: sum(x['pos'] == p for x in wrong) for p in ('first', 'middle', 'last')},
          '| mean M_F right %.2f wrong %s' % (st.mean(x['MF'] for x in right) if right else float('nan'), ('%.2f' % st.mean(x['MF'] for x in wrong)) if wrong else '-'))
    sc = {}
    for x in rows: sc.setdefault(x['s'], []).append(x)
    print('   per scenario: wrong / mean drop(M_F-M_V)', {s: (sum(1 - x['yV'] for x in v), round(st.mean(x['MF'] - x['MV'] for x in v), 2)) for s, v in sorted(sc.items())})
