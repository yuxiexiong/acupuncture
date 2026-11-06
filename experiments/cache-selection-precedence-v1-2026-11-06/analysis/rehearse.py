"""SPF-01 offline rehearsal of the frozen read-outs (draft r02) on the REAL design table with SYNTHETIC outputs (no model).

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
    S, Bv, Bqk, Kk, _donors, _scope = K.ARMS[arm]
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
    donor_buf = Bv in ('d', 'd2')
    if w == 'qk_carrier' and v_clean and k_clean:                # the selection travels with the q/k channels, not with V
        b_sel = SELF[r] if Bqk == 'oc' else pred(d, reading)
    if w == 'v_alone' and v_clean:                               # donor V redirects even with needle-formed q/k
        b_sel = SELF[r] if Bv == 'oc' else pred(bdon, reading)
    if w == 'no_open' and bg == 'T' and donor_buf and s_sel is None:
        return 'stop'                                            # a donor buffer does not even open the answer
    if w == 'prefail' and arm == 'C0':
        return SELF[r] if rng.random() < 0.5 else 'other'
    if w == 'chaos':                                             # outputs unrelated to anything: a random listed row
        return rng.choice((0, 1, 2)) if d is not None else world_out('flip', arm, r, d, d2, rng)
    if w == 'patchy':                                            # the hypothesis holds in half of the scenarios, nothing transfers in the others
        return world_out('flip' if CLU[r] in ORDER[:3] else 'never', arm, r, d, d2, rng)
    if w in ('flip', 'prefail', 'weak', 'half', 'faint', 'leaky_c', 'qk_carrier', 'v_alone', 'no_open'):
        out = s_sel if s_sel is not None else (b_sel if b_sel is not None else (0 if opens else 'stop'))
        if w in ('weak', 'half', 'faint') and d is not None and rng.random() < {'weak': 0.72, 'half': 0.5, 'faint': 0.9}[w]:   # some donor selections do not transfer
            out = SELF[r] if S == 'oc' or Bv == 'oc' else 0
        if w == 'leaky_c' and bg == 'T' and S == 'oc' and donor_buf and b_sel is not None and rng.random() < 0.7:
            out = b_sel                                          # restoring the state suppresses the donor buffer only part of the time
        return out
    if w == 'buffer_general':                                    # a clean buffer always decides
        return b_sel if b_sel is not None else (s_sel if s_sel is not None else (0 if opens else 'stop'))
    if w == 'background':                                        # the buffer decides whenever the rest of the run is intervened, whatever the state
        if bg == 'T' and b_sel is not None:
            return b_sel
        if s_sel is not None:
            return s_sel
        return SELF[r] if (bg == 'C' and v_clean and k_clean) else (0 if opens else 'stop')
    if w == 'needs_both':                                        # the buffer decides only with a needle-formed state AND an intervened rest
        if bg == 'T' and S == 'on' and b_sel is not None:
            return b_sel
        if s_sel is not None:
            return s_sel
        return SELF[r] if bg == 'C' else (0 if opens else 'stop')
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


def run(world, dirn=K.MAIN):
    rng = random.Random(7)
    Y, cells, conflicts = {}, {}, {}
    for arm in K.arms_for(dirn):
        donors = K.ARMS[arm][4]
        if donors is None:
            Y[arm] = {r: int(world_out(world, arm, r, rng=rng) == SELF[r]) for r in items}
        elif donors == 'pair':
            conflicts[arm] = {}
            for r in items:
                ps = K.conflict_pairs(TAB[r])
                o = {(s['id'], b['id']): world_out(world, arm, r, s, b, rng) for s, b in ps}
                conflicts[arm][r] = K.w_conflict(TAB[r], o)
        else:
            use_os = donors == 'same+os' and dirn == K.MAIN
            out = {r: {d['id']: world_out(world, arm, r, d, rng=rng) for d in TAB[r] if use_os or d['type'] != 'OS'} for r in items}
            cells[arm] = K.cell(out, TAB, CLU, SELF, N_BOOT, n_perm=200 if arm in K.CELLS.values() else 0)   # the real analysis uses 2000
    return K.decide(dirn, Y, cells, conflicts, CLU, N_BOOT), (Y, cells, conflicts)


def fmt(b):
    return 'None' if b is None else f"{b['mean']:+.2f}[{b['lo']:+.2f},{b['hi']:+.2f}]p={b['perm_p']:.3f}"


EXPECT = {'flip': 'source_modulates', 'flip_key': 'source_modulates', 'kv': 'source_modulates', 'qk_carrier': 'source_modulates', 'v_alone': 'source_modulates',
          'needs_both': 'restore_suppresses_only', 'buffer_general': 'not_source_dependent', 'background': 'not_source_dependent',
          'state_only': 'no_transfer', 'never': 'no_transfer', 'no_open': 'no_transfer', 'faint': 'no_transfer', 'patchy': 'indeterminate',
          'leaky_c': 'partial', 'prefail': 'prerequisite_fail', 'weak': None, 'half': None}
seen_outcomes, seen = set(), {}
for world, want in EXPECT.items():
    dec, _parts = run(world)
    seen_outcomes.add(dec['outcome'])
    for k, v in dec['labels'].items():
        seen.setdefault(k, set()).add(v)
    print(f"{world:15s} outcome={dec['outcome']:24s} D(a,b,c,d)=" + ' '.join(f"{dec['D'][k]['mean']:+.2f}" for k in 'abcd')
          + f" | D_needle={fmt(dec['D_needle'])} D_clean={fmt(dec['D_clean'])} | null arm {fmt(dec['null_arm'])} anchor {fmt(dec['anchor_arm'])}")
    print('                labels', dec['labels'])
    assert want is None or dec['outcome'] == want, (world, dec['outcome'], want)     # 'half' is shown for calibration only
print()
sec, _p = run('flip', K.SECOND)
print('second direction (reduced arm set), flip world:', sec['outcome'], sec['labels'])
assert sec['outcome'] == 'source_modulates' and 'KV' not in sec['labels']
# margin check.  (1) what the by-construction null looks like on this panel when outputs are unrelated to the donor
ch, _p = run('chaos')
print(f"chaos world: D(d)={fmt(ch['D']['d'])} permutation-null 97.5% over the four cells = {ch['perm_null_hi']:+.3f} margin_check={ch['labels']['margin_check']} "
      f"outcome={ch['outcome']}")
assert ch['labels']['margin_check'] == 'passed' and ch['outcome'] in ('no_transfer', 'indeterminate') and ch['labels']['E'] != 'holds'
# (2) if that null reached the margin, every 'holds' is downgraded
ok, (Y_, cells_, conf_) = run('flip')
cells_['T_Bd']['perm_null']['hi'] = 0.30
bad = K.decide(K.MAIN, Y_, cells_, conf_, CLU, N_BOOT)
print('flip world with the permutation null forced to 0.30:', bad['outcome'], {k: bad['labels'][k] for k in ('margin_check', 'E', 'D_needle', 'D_clean', 'R_S')})
assert ok['outcome'] == 'source_modulates' and bad['outcome'] == 'indeterminate' and bad['labels']['margin_check'] == 'failed' and 'holds' not in (
    bad['labels']['E'], bad['labels']['D_needle'], bad['labels']['D_clean'], bad['labels']['R_S'])
seen.setdefault('margin_check', set()).update({'passed', 'failed'})
print('outcomes seen', sorted(seen_outcomes))
assert seen_outcomes >= {'source_modulates', 'restore_suppresses_only', 'not_source_dependent', 'no_transfer', 'indeterminate', 'partial', 'prerequisite_fail'}
for k, v in sorted(seen.items()):
    print(f'  {k:16s} {sorted(v)}')
need = {'E': {'holds', 'below', 'indeterminate'}, 'D_needle': {'holds', 'below', 'indeterminate'}, 'D_clean': {'holds', 'below'},
        'buffer_in_clean': {'holds', 'below'}, 'R_S': {'holds', 'below'}, 'R_QK': {'holds', 'fails'}, 'V': {'holds', 'fails', 'unjudgeable'},
        'VQ': {'holds', 'fails'}, 'S_T': {'holds', 'below'}, 'KV': {'holds', 'below'}, 'OPEN': {'holds', 'fails'}, 'READ': {'row', 'key', 'unjudgeable'},
        'X_C': {'state', 'buffer', 'undetermined'}, 'X_T': {'state', 'buffer', 'undetermined'}}
missing = {k: sorted(v - seen.get(k, set())) for k, v in need.items() if v - seen.get(k, set())}
print('label values required but not reached:', missing)
assert not missing, missing
print('REHEARSAL PASS: every outcome and every required label value is reachable and avoidable')
