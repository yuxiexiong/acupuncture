"""DWB-01 frozen read-outs (CONTRACT §4-§5).  Pure Python.  Statistic, margin, bootstrap, permutation null and donor rule are imported unchanged
from the frozen SPF-01 module (spf_core): D_tr is exactly 0 for any donor-independent output.

Panel: LVK new panel, 48 inputs, 6 scenarios.  Donors of a receiver: every other input of its scenario.
Arms (per direction; receiver = the input's native intervened run T unless stated):
  L00   T unchanged                                                                  (bridge: LVK-01 L00)
  L11o  T; at t1 only, write-term v from the receiver's own clean V history, k de-offset      (bridge: LVK-01 L11)
  L11d  T; at t1 only, write-term v from the DONOR's clean V history, k de-offset            pure local form
  OO    T with the receiver's own clean conv buffer (V and q/k)                                (bridge: LVK-01 F)
  DD    T with the donor's clean V channels and the receiver's own clean q/k channels          (bridge: SPF-01 T_Bvd_Bqkown)
  DO    cache of OO; at t1 only, write-term v from the donor's clean V history                 donor write, own V retained
  OD    cache of DD; at t1 only, write-term v from the receiver's own clean V history          own write, donor V retained
  CSTd  the receiver's CLEAN run with the deep recurrent state of the DONOR's needle run       discriminating arm
  C0    the receiver's clean run (once, no direction)                                          (bridge: LVK-01 clean)
Read-outs per direction (three-way against the margin M: 'holds' lo >= M, 'below' hi <= M, else 'indeterminate'):
  REF  D_tr(DD)                          the effect to be bridged is present in this run
  SUF  D_tr(DO)                          one donor write at t1 is enough
  RET  D_tr(OD)                          the retained donor V without the donor's t1 write is enough
  NEC  D_tr(DD) - D_tr(OD), paired       taking the donor's t1 write away removes the effect
  LOC  D_tr(L11d)                        the LVK endpoint with the donor's v redirects the answer
  SRC  D_tr(CSTd)                        a needle-formed state still carries a transferable selection
"""
import os
import sys

SPF_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cache-selection-precedence-v1-2026-11-06')
sys.path.insert(0, SPF_DIR)
import spf_core as S  # noqa: E402

M = S.M
TH = {'clean': 0.90, 'dmg': 0.25, 'own_buffer': 0.75, 'own_local': 0.50, 'self': 0.75}
MAIN, SECOND = S.MAIN, S.SECOND
DIRS = S.DIRS
# name: (donors, hooked at t1, background)
ARMS = {
    'L00':  (None,   False, 'T'),
    'L11o': (None,   True,  'T'),
    'OO':   (None,   False, 'T'),
    'DD':   ('same', False, 'T'),
    'DO':   ('same', True,  'T'),
    'OD':   ('same', True,  'T'),
    'L11d': ('same', True,  'T'),
    'CSTd': ('same', False, 'C'),
}
ORDER = ('L00', 'OO', 'L11o', 'DD', 'DO', 'OD', 'L11d', 'CSTd')       # prerequisite and reference arms first
DONOR_ARMS = tuple(a for a in ORDER if ARMS[a][0])
NULL_CHECK = ('DD', 'DO', 'OD', 'L11d', 'CSTd')


def same_donors(D):
    return [d for d in D if d['type'] != 'OS']


def count_trajectories(items, scen_order):
    n = {'once': len(items), 'per_direction': 0, 'hooked_per_direction': 0}
    for R in items.values():
        k = len(same_donors(S.donor_table(R, items, scen_order)))
        for a, (donors, hooked, _bg) in ARMS.items():
            m = k if donors else 1
            n['per_direction'] += m
            n['hooked_per_direction'] += m if hooked else 0
    n['total'] = n['once'] + len(DIRS) * n['per_direction']
    n['hooked_total'] = len(DIRS) * n['hooked_per_direction']
    return n


def decide(dirn, Y, cells, clusters, n_boot=10000):
    """One direction.  Y: {arm: {receiver: 1/0}} for C0, L00, OO, L11o; cells: {arm: spf_core.cell(...)} for the donor arms (n_perm > 0)."""
    y = {a: S.rate(Y[a]) for a in Y}
    pre = {'clean': y['C0'] >= TH['clean'], 'damage': y['L00'] <= TH['dmg'], 'own_buffer': y['OO'] >= TH['own_buffer'], 'own_local': y['L11o'] >= TH['own_local']}
    null_hi = max(cells[a]['perm_null']['hi'] for a in NULL_CHECK)
    margin_ok = null_hi < M

    def eff(lab):                      # margin check: if the by-construction null reaches M, no 'holds' is allowed
        return 'indeterminate' if (lab == 'holds' and not margin_ok) else lab

    lab = {a: eff(cells[a]['effect']) for a in DONOR_ARMS}
    nec_b = S.boot(S.diff(cells['DD']['per_receiver'], cells['OD']['per_receiver']), clusters, n_boot)
    base_ok = pre['clean'] and pre['damage'] and pre['own_buffer']
    out = {'REF': lab['DD'], 'SUF': lab['DO'], 'RET': lab['OD'], 'NEC': eff(S.three(nec_b)), 'LOC': lab['L11d'], 'SRC': lab['CSTd'], 'margin_check': 'passed' if margin_ok else 'failed'}
    # 2x2: who supplies the t1 write x whose V stays in the buffer afterwards
    if not base_ok:
        q = 'prerequisite_fail'
    elif out['REF'] == 'below':
        q = 'reference_absent'
    elif out['REF'] != 'holds':
        q = 'indeterminate'
    elif out['SUF'] == 'holds' and out['RET'] == 'below' and out['NEC'] == 'holds':
        q = 'write_carries'
    elif out['SUF'] == 'holds' and out['RET'] == 'holds':
        q = 'both_routes'
    elif out['SUF'] == 'below' and out['RET'] == 'holds':
        q = 'retained_buffer_carries'
    elif out['SUF'] == 'below' and out['RET'] == 'below':
        q = 'neither_alone'
    else:
        q = 'indeterminate'
    # pure local form on the native intervened run
    if not (base_ok and pre['own_local']):
        loc = 'unjudgeable'
    else:
        loc = {'holds': 'local_write_redirects', 'below': 'local_write_does_not_redirect'}.get(out['LOC'], 'indeterminate')
    # discriminating arm
    c = cells['CSTd']
    if not pre['clean']:
        src = 'unjudgeable'
    elif out['SRC'] == 'holds':
        src = 'needle_state_carries_selection'
    elif out['SRC'] == 'below':
        src = 'own_answer_without_own_state' if c['y_self'] >= TH['self'] else 'degraded'
    else:
        src = 'indeterminate'
    return {'direction': dirn, 'bridge_2x2': q, 'local_form': loc, 'needle_state': src, 'labels': out, 'prerequisites': pre, 'Y': y,
            'D': {a: cells[a]['D_tr'] for a in DONOR_ARMS}, 'NEC': nec_b, 'perm_null_hi': null_hi,
            'ratio_DO_over_DD': (cells['DO']['D_tr']['mean'] / cells['DD']['D_tr']['mean']) if cells['DD']['D_tr']['mean'] > 0 else None,
            'ratio_L11d_over_DD': (cells['L11d']['D_tr']['mean'] / cells['DD']['D_tr']['mean']) if cells['DD']['D_tr']['mean'] > 0 else None,
            'y_self': {a: cells[a]['y_self'] for a in DONOR_ARMS}, 'open': {a: cells[a]['open'] for a in DONOR_ARMS}}
