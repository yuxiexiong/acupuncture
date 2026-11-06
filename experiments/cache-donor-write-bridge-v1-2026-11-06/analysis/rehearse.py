"""DWB-01 offline rehearsal on the REAL design table with SYNTHETIC outputs (no model): every outcome of the three readings must be both
reachable and avoidable.  Also prints the design table and the trajectory budget.   python3 analysis/rehearse.py"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import dwb_core as K  # noqa: E402
S = K.S

items = json.load(open(os.path.join(K.SPF_DIR, 'data', 'panel-items-lvk48.json')))['items']
ORDER = sorted({it['scenario'] for it in items.values()})
TAB = {r: S.donor_table(R, items, ORDER) for r, R in items.items()}
CLU = {r: R['scenario'] for r, R in items.items()}
SELF = {r: S.row_of(R, R['target']) for r, R in items.items()}
N_BOOT, N_PERM = 1500, 150

print('design: receivers', len(items), '| same-scenario donors per receiver', sorted({len(K.same_donors(TAB[r])) for r in items}),
      '| receivers with a computable D_tr', sum(1 for r in items if S.d_transfer(TAB[r], {d['id']: 0 for d in TAB[r]}) is not None))
print('trajectories', K.count_trajectories(items, ORDER))

# a world: {arm: rule(receiver, donor) -> output}; 'self' / 'donor' / 'first' / 'stop', optionally with a probability of following the donor
BASE = {'C0': 'self', 'L00': 'stop', 'OO': 'self', 'L11o': 'self', 'DD': 'donor', 'DO': 'donor', 'OD': 'self', 'L11d': 'donor', 'CSTd': 'self'}
WORLDS = {
    'write_carries':        ({}, ('write_carries', 'local_write_redirects', 'own_answer_without_own_state')),
    'both_routes':          ({'OD': 'donor'}, ('both_routes', 'local_write_redirects', 'own_answer_without_own_state')),
    'retained_buffer':      ({'DO': 'self', 'OD': 'donor', 'L11d': 'first'}, ('retained_buffer_carries', 'local_write_does_not_redirect', 'own_answer_without_own_state')),
    'neither_alone':        ({'DO': 'self', 'OD': 'self', 'L11d': 'first'}, ('neither_alone', 'local_write_does_not_redirect', 'own_answer_without_own_state')),
    'reference_absent':     ({'DD': 'self', 'DO': 'self', 'L11d': 'first'}, ('reference_absent', 'local_write_does_not_redirect', 'own_answer_without_own_state')),
    'needle_state_carries': ({'CSTd': 'donor'}, ('write_carries', 'local_write_redirects', 'needle_state_carries_selection')),
    'state_swap_degrades':  ({'CSTd': 'stop'}, ('write_carries', 'local_write_redirects', 'degraded')),
    'patchy':               ({'DO': ('donor', 'half_scenarios'), 'L11d': ('donor', 'half_scenarios'), 'CSTd': ('donor', 'half_scenarios')},
                             ('indeterminate', 'indeterminate', 'indeterminate')),
    'weak_write':           ({'DO': ('donor', 0.35), 'OD': ('donor', 0.35)}, None),
    'own_local_fails':      ({'L11o': 'stop'}, ('write_carries', 'unjudgeable', 'own_answer_without_own_state')),
    'no_damage':            ({'L00': 'self'}, ('prerequisite_fail', 'unjudgeable', 'own_answer_without_own_state')),
    'clean_fails':          ({'C0': 'stop'}, ('prerequisite_fail', 'unjudgeable', 'unjudgeable')),
}


def out_of(rule, r, d, rng):
    p = 1.0
    if isinstance(rule, tuple):
        rule, p = rule
        if p == 'half_scenarios':
            p = 1.0 if CLU[r] in ORDER[:3] else 0.0
    if rule == 'donor':
        return d['row'] if rng.random() < p else SELF[r]
    return {'self': SELF[r], 'first': 0, 'stop': 'stop'}[rule]


def run(over):
    rng = random.Random(11)
    w = dict(BASE)
    w.update(over)
    Y = {a: {r: int(out_of(w[a], r, None, rng) == SELF[r]) for r in items} for a in ('C0', 'L00', 'OO', 'L11o')}
    cells = {}
    for a in K.DONOR_ARMS:
        arm_out = {r: {d['id']: out_of(w[a], r, d, rng) for d in K.same_donors(TAB[r])} for r in items}
        cells[a] = S.cell(arm_out, TAB, CLU, SELF, N_BOOT, N_PERM)
    return K.decide(K.MAIN, Y, cells, CLU, N_BOOT), cells


seen = {'bridge_2x2': set(), 'local_form': set(), 'needle_state': set(), 'NEC': set()}
for name, (over, want) in WORLDS.items():
    dec, cells = run(over)
    got = (dec['bridge_2x2'], dec['local_form'], dec['needle_state'])
    for k, v in zip(('bridge_2x2', 'local_form', 'needle_state'), got):
        seen[k].add(v)
    seen['NEC'].add(dec['labels']['NEC'])
    print(f"{name:22s} 2x2={got[0]:24s} local={got[1]:30s} state={got[2]:32s} | D: " + ' '.join(f"{a}={dec['D'][a]['mean']:+.2f}" for a in K.DONOR_ARMS)
          + f" | NEC {dec['NEC']['mean']:+.2f}[{dec['NEC']['lo']:+.2f},{dec['NEC']['hi']:+.2f}] {dec['labels']['NEC']} | null97.5 {dec['perm_null_hi']:.3f}")
    assert want is None or got == want, (name, got, want)
# margin check: if the by-construction null reached the margin, nothing may 'hold'
dec, cells = run({})
cells['DO']['perm_null']['hi'] = 0.30
Y = {a: {r: int(BASE[a] == 'self') for r in items} for a in ('C0', 'L00', 'OO', 'L11o')}
bad = K.decide(K.MAIN, Y, cells, CLU, N_BOOT)
print('margin check forced to fail:', bad['bridge_2x2'], bad['local_form'], bad['needle_state'], bad['labels'])
assert bad['labels']['margin_check'] == 'failed' and 'holds' not in bad['labels'].values() and bad['bridge_2x2'] == 'indeterminate'
print()
for k, v in seen.items():
    print(f'  {k:12s} {sorted(v)}')
need = {'bridge_2x2': {'write_carries', 'both_routes', 'retained_buffer_carries', 'neither_alone', 'reference_absent', 'indeterminate', 'prerequisite_fail'},
        'local_form': {'local_write_redirects', 'local_write_does_not_redirect', 'indeterminate', 'unjudgeable'},
        'needle_state': {'needle_state_carries_selection', 'own_answer_without_own_state', 'degraded', 'indeterminate', 'unjudgeable'},
        'NEC': {'holds', 'below'}}
missing = {k: sorted(v - seen[k]) for k, v in need.items() if v - seen[k]}
print('outcomes required but not reached:', missing)
assert not missing, missing
print('REHEARSAL PASS: every outcome of the three readings is reachable and avoidable')
