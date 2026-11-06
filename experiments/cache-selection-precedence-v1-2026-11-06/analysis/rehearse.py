"""SPF-01 offline rehearsal of the frozen read-outs on the REAL design table with SYNTHETIC outputs (no model).

Each "world" is a rule that turns (arm, receiver, donor) into an output.  The rehearsal must show every outcome and every label value both
reachable and avoidable.  Run from the experiment directory:  python3 analysis/rehearse.py
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import spf_core as K  # noqa: E402

items = json.load(open(os.path.join(ROOT, 'data', 'panel-items-lvk48.json')))['items']
ORDER = sorted({it['scenario'] for it in items.values()})
TAB = {r: K.donor_table(R, items, ORDER) for r, R in items.items()}
CLU = {r: R['scenario'] for r, R in items.items()}
SELF = {r: K.row_of(R, R['target']) for r, R in items.items()}
N_BOOT = 2000


def pred(d, reading):
    if reading == 'key':
        return d['key'] if d['key'] is not None else 0          # no shared entity: nothing to follow, default
    return d['row']


def world_out(world, arm, r, d=None, d2=None, rng=None):
    S, Bv, Bqk, Kk, _donors, _pd = K.ARMS[arm]
    bg = arm[0]                                                  # 'C' or 'T'
    base = 'oc' if bg == 'C' else 'on'
    S = base if S == '-' else S
    Bv = base if Bv == '-' else Bv
    Bqk = base if Bqk == '-' else Bqk
    reading = 'key' if world.endswith('_key') else 'row'
    w = world.replace('_key', '')
    bdon = d2 if Bv == 'd2' else d
    # what each carrier would select
    s_sel = {'oc': SELF[r], 'on': None, 'd': pred(d, reading) if d else None, 'd4': pred(d, reading) if d else None, 'do': SELF[r] if bg == 'C' else None}[S]
    v_clean, k_clean = Bv != 'on', Bqk != 'on'
    b_sel = None
    if v_clean and k_clean:
        b_sel = SELF[r] if Bv == 'oc' else pred(bdon, reading)
    opens = v_clean or S in ('oc', 'd', 'd4')
    if w == 'qk_carrier' and v_clean and k_clean:                # the selection travels with the q/k channels, not with V
        b_sel = SELF[r] if Bqk == 'oc' else pred(d, reading)
    if w == 'v_alone' and v_clean:                               # donor V redirects even with needle-formed q/k
        b_sel = SELF[r] if Bv == 'oc' else pred(bdon, reading)
    if w == 'no_open' and bg == 'T' and Bv in ('d', 'd2') and s_sel is None:
        return 'stop'                                            # a donor buffer does not even open the answer
    if w == 'prefail' and arm == 'C0':
        return SELF[r] if rng.random() < 0.5 else 'other'
    if w in ('flip', 'prefail', 'weak', 'half', 'leaky', 'qk_carrier', 'v_alone', 'no_open'):
        out = s_sel if s_sel is not None else (b_sel if b_sel is not None else (0 if opens else 'stop'))
        if w in ('weak', 'half') and d is not None and rng.random() < {'weak': 0.72, 'half': 0.5}[w]:   # some donor selections do not transfer
            out = SELF[r] if S == 'oc' or Bv == 'oc' else 0
        if w == 'leaky' and bg == 'C' and S == 'oc' and b_sel is not None and Bv != 'oc' and rng.random() < 0.35:
            out = b_sel                                                          # the donor buffer sometimes wins even with an intact state
        return out
    if w == 'buffer_general':
        return b_sel if b_sel is not None else (s_sel if s_sel is not None else (0 if opens else 'stop'))
    if w == 'background':                                        # the buffer decides whenever the rest of the run is intervened
        if bg == 'T' and b_sel is not None:
            return b_sel
        if s_sel is not None:
            return s_sel
        return SELF[r] if (bg == 'C' and v_clean and k_clean) else (0 if opens else 'stop')
    if w == 'state_only':                                        # donor state redirects, a donor buffer never does
        if s_sel is not None:
            return s_sel
        if v_clean and k_clean:
            return SELF[r] if Bv == 'oc' else 0
        return 0 if opens else 'stop'
    if w == 'never':                                             # no donor component ever redirects
        own = S == 'oc' or (Bv == 'oc' and k_clean) or (bg == 'C' and S in ('d', 'd4', 'do'))
        return SELF[r] if own else (0 if opens else 'stop')
    if w == 'kv':                                                # flip, and donor tail KV also redirects
        if Kk == 'd':
            return pred(d, reading)
        return world_out('flip', arm, r, d, d2, rng)
    raise ValueError(world)


def run(world, dirn=K.DIRS[0]):
    rng = random.Random(7)
    Y, cells, conflicts = {}, {}, {}
    for arm, (_S, _v, _q, _k, donors, _pd) in K.ARMS.items():
        if donors is None:
            Y[arm] = {r: int(world_out(world, arm, r, rng=rng) == SELF[r]) for r in items}
        elif donors == 'pair':
            conflicts[arm] = {}
            for r in items:
                ps = K.conflict_pairs(TAB[r])
                o = {(s['id'], b['id']): world_out(world, arm, r, s, b, rng) for s, b in ps}
                conflicts[arm][r] = K.w_conflict(TAB[r], o)
        else:
            out = {}
            for r in items:
                out[r] = {d['id']: world_out(world, arm, r, d, rng=rng) for d in TAB[r] if donors == 'same+os' or d['type'] != 'OS'}
            cells[arm] = K.cell(out, TAB, CLU, SELF, N_BOOT)
    return K.decide(dirn, Y, cells, conflicts, CLU, N_BOOT), cells


EXPECT = {'flip': 'precedence_flip', 'flip_key': 'precedence_flip', 'buffer_general': 'buffer_general', 'background': 'background_dependent',
          'state_only': 'no_transfer', 'never': 'no_transfer', 'weak': 'indeterminate', 'half': None, 'leaky': 'partial', 'prefail': 'prerequisite_fail',
          'kv': 'precedence_flip', 'qk_carrier': 'precedence_flip', 'v_alone': 'precedence_flip', 'no_open': 'no_transfer'}
seen_outcomes, seen = set(), {}
for world, want in EXPECT.items():
    dec, cells = run(world)
    seen_outcomes.add(dec['outcome'])
    for k, v in list(dec['labels'].items()) + [('cell_' + k, v) for k, v in dec['cells'].items()]:
        seen.setdefault(k, set()).add(v)
    d = cells['T_Bd']
    print(f"{world:15s} outcome={dec['outcome']:22s} cells={dec['cells']} D_tr(T_Bd)={d['D_tr']['mean']:+.2f} [{d['D_tr']['lo']:+.2f},{d['D_tr']['hi']:+.2f}] "
          f"D_rk={d['D_rk']['mean']:+.2f} D_os={d['D_os']['mean']:+.2f}")
    print('                labels', dec['labels'])
    assert want is None or dec['outcome'] == want, (world, dec['outcome'], want)     # 'half' is shown for threshold calibration only
print()
print('outcomes seen', sorted(seen_outcomes))
assert seen_outcomes == {'precedence_flip', 'buffer_general', 'background_dependent', 'no_transfer', 'indeterminate', 'partial', 'prerequisite_fail'}
for k, v in sorted(seen.items()):
    print(f'  {k:10s} {sorted(v)}')
need = {'R_S': {'FOLLOW', 'SELF'}, 'R_QK': {'SELF', 'FOLLOW'}, 'V': {'holds', 'fails', 'unjudgeable'}, 'VQ': {'holds', 'fails'},
        'S_T': {'FOLLOW', 'DEGRADED'}, 'KV': {'FOLLOW', 'DEGRADED'}, 'OPEN': {'holds', 'fails'}, 'READ': {'row', 'key', 'unjudgeable'},
        'X_C': {'state_wins', 'buffer_wins', 'neither'},
        'X_T': {'state_wins', 'buffer_wins', 'neither'}, 'cell_a': {'SELF', 'FOLLOW'}, 'cell_b': {'FOLLOW', 'SELF'}, 'cell_c': {'SELF', 'FOLLOW'},
        'cell_d': {'FOLLOW', 'DEGRADED', 'INTERMEDIATE'}}
missing = {k: sorted(v - seen.get(k, set())) for k, v in need.items() if v - seen.get(k, set())}
print('label values required but not reached:', missing)
assert not missing, missing
print('REHEARSAL PASS: every outcome and every required label value is reachable and avoidable')
