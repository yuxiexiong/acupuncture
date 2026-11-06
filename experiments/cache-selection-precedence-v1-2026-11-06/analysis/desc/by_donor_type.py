"""Descriptive (contract §5 'only described'): output distribution by donor type for the donor arms.  Run in the experiment directory on the server."""
import json
import sys
sys.path.insert(0, '.')
import spf_analysis as A
import spf_core as K

ver, recs = A.load('runs/A-formal-r02', 'formal')
print('verification', ver['status'], 'receivers', ver['receivers'], 'wall', round(ver['workers'][0]['wall_seconds']), 'calls', {k: ver['model_calls'][k] for k in ('formations', 't1', 'trajectories', 'decode_forwards')})
nb = {}
for r in recs.values():
    for k, v in r['gates']['bridges'].items():
        nb[k] = nb.get(k, 0) + v
print('bridges passed (bit-exact t1 logits + natural tokens):', nb)
ARMS = {K.MAIN: ('C_Sd', 'C_S4d', 'C_Bd', 'C_ST_Bd', 'T_Bd', 'T_Bvd_Bqkown', 'T_Bvown_Bqkd', 'T_Sown_Bd', 'T_Sd', 'T_Bvd'), K.SECOND: ('C_ST_Bd', 'T_Bd', 'T_Bvd_Bqkown', 'T_Sown_Bd')}
for d, arms in ARMS.items():
    print('==', d)
    for arm in arms:
        tab = {t: {'n': 0, 'self': 0, 'row': 0, 'key': 0, 'first': 0, 'stop/other': 0} for t in K.DONOR_TYPES}
        for r, rec in recs.items():
            runs = A.runs_of(rec, d, arm)
            for x in rec['donors']:
                if x['id'] not in runs:
                    continue
                o = A.row_out(runs[x['id']], rec['item'])
                t = tab[x['type']]
                t['n'] += 1
                if o not in (0, 1, 2):
                    t['stop/other'] += 1
                    continue
                t['self'] += int(o == rec['self_row'])
                t['row'] += int(o == x['row'])
                t['key'] += int(x['key'] is not None and o == x['key'])
                t['first'] += int(o == 0)
        print(f'  {arm:13s}', ' | '.join(f"{t}: n={v['n']} self={v['self']} row={v['row']} key={v['key']} first={v['first']} x={v['stop/other']}" for t, v in tab.items() if v['n']))
# first-listed share by receiver target row in cell d, aligned donors only: does following depend on where the donor points?
for d in (K.MAIN, K.SECOND):
    by = {}
    for r, rec in recs.items():
        runs = A.runs_of(rec, d, 'T_Bd')
        for x in rec['donors']:
            if x['type'] != 'AL':
                continue
            o = A.row_out(runs[x['id']], rec['item'])
            c = by.setdefault(x['row'], [0, 0])
            c[1] += 1
            c[0] += int(o == x['row'])
    print('cell d, aligned donors: followed / n by donor target row', d, {k: v for k, v in sorted(by.items())})
# what T_Sown answers in the second direction
ex = {}
for r, rec in recs.items():
    nr = A.runs_of(rec, K.SECOND, 'T_Sown')['']
    k = (A.row_out(nr, rec['item']) == rec['self_row'], nr['termination'], nr['text'][:40])
    ex[k] = ex.get(k, 0) + 1
print('T_Sown second direction, (correct, termination, text[:40]) counts:')
for k, v in sorted(ex.items(), key=lambda kv: -kv[1])[:8]:
    print('  ', v, k)
