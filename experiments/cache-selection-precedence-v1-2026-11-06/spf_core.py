"""SPF-01 frozen read-outs (CONTRACT §4-§6).  Pure Python, no model code.  Every label is computed from the measurement named next to it.

Panel: LVK new panel, 48 inputs, 6 scenarios (cluster unit).  A scenario fixes three entities A/B/C with their codes; an input is (rotation of the
record list, queried entity).  Rows are 0-based positions in the receiver's record list.

Arms are swaps of cache tensors at the boundary before the last prompt token (no hooks).  Components:
  S    recurrent_states of the deep GDN layers G (S4: layers 16-18 only; So: G without 16-18)
  Bv   V channels of conv_states of G        Bqk  q/k channels of conv_states of G
  K    keys/values of the deep full-attention layers (own clean: all cached positions; donor: the last 4 cached positions)
Sources: oc own clean run, on own needle run (direction dir), d donor's clean run, d2 the partner donor's clean run.

Per (receiver, donor): self = receiver's target row; row = donor's target row in the donor's list; key = row, in the RECEIVER's list, of the entity
the donor asks about (None for a donor from another scenario).  Donor types:
  AL same rotation, other query (row == key)      KS other rotation, same query (key == self)
  RS other rotation, row == self                  BD other rotation, self/row/key all distinct      OS other scenario (row only)
Output of a trajectory: 0/1/2 = the row of the single listed code in the natural full answer; 'stop' / 'other' otherwise.

Statistics (each is exactly 0 for ANY donor-independent output: self, first-listed default, stop):
  D_tr  transfer, on aligned donors: 1[out_d == p_d] minus the rate of that same row p_d among donors that do not predict it (contrast set).
  D_rk  reading, on balanced BD sets: +1 output at the donor's row, -1 output at the donor's key row.
  D_os  transfer from other-scenario donors (two donors with the two non-self rows).
  W     conflict (S from one aligned donor, buffer from the other, both orders): +1 follows the S donor, -1 follows the buffer donor.
Cell label, from D_tr (mean over receivers, 95% scenario-cluster bootstrap [lo, hi]) and y_self (share of AL/BD-donor outputs at the self row):
  FOLLOW        D >= 0.50 and lo >= 0.25
  SELF          D <= 0.15 and hi <= 0.30 and y_self >= 0.75
  DEGRADED      D <= 0.15 and hi <= 0.30 and y_self <  0.75      (neither the donor nor the receiver's own target)
  INTERMEDIATE  anything else
"""
import random

TH = {'follow': 0.50, 'follow_lo': 0.25, 'null': 0.15, 'null_hi': 0.30, 'self': 0.75, 'clean': 0.90, 'dmg': 0.25, 'up': 0.75, 'v_ratio': 0.75,
      'open': 0.90, 'first': 0.50}
DIRS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1')
G = (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
G4 = (16, 17, 18)
ATTN = (15, 19, 23, 27, 31)
DONOR_TYPES = ('AL', 'KS', 'RS', 'BD', 'OS')

# name: (S, Bv, Bqk, K, donors, per_dir).  donors: None, 'same', 'same+os', 'pair'.  '-' leaves the background's own value.
ARMS = {
    'C0':           ('-',  '-',  '-',  '-',  None,      False),
    'C_Sd':         ('d',  '-',  '-',  '-',  'same',    False),
    'C_S4d':        ('d4', '-',  '-',  '-',  'same',    False),
    'C_Sod':        ('do', '-',  '-',  '-',  'same',    False),
    'C_Bd':         ('-',  'd',  'd',  '-',  'same',    False),
    'C_Sd1_Bd2':    ('d',  'd2', 'd2', '-',  'pair',    False),
    'C_ST':         ('on', '-',  '-',  '-',  None,      True),
    'C_ST_Bd':      ('on', 'd',  'd',  '-',  'same+os', True),
    'T0':           ('-',  '-',  '-',  '-',  None,      True),
    'T_Bown':       ('-',  'oc', 'oc', '-',  None,      True),
    'T_Bvown':      ('-',  'oc', '-',  '-',  None,      True),
    'T_Sown':       ('oc', '-',  '-',  '-',  None,      True),
    'T_Kown':       ('-',  '-',  '-',  'oc', None,      True),
    'T_Bd':         ('-',  'd',  'd',  '-',  'same+os', True),
    'T_Bvd_Bqkown': ('-',  'd',  'oc', '-',  'same',    True),
    'T_Bvown_Bqkd': ('-',  'oc', 'd',  '-',  'same',    True),
    'T_Bvd':        ('-',  'd',  '-',  '-',  'same',    True),
    'T_Sd':         ('d',  '-',  '-',  '-',  'same',    True),
    'T_Sown_Bd':    ('oc', 'd',  'd',  '-',  'same',    True),
    'T_Sd1_Bd2':    ('d',  'd2', 'd2', '-',  'pair',    True),
    'T_Kd':         ('-',  '-',  '-',  'd',  'same',    True),
}
# the four cells of the S-integrity x rest-of-background table for the buffer donor
CELLS = {'a': 'C_Bd', 'b': 'C_ST_Bd', 'c': 'T_Sown_Bd', 'd': 'T_Bd'}


def row_of(item, code):
    return item['listed_codes'].index(code)


def donor_table(R, items, scen_order):
    """Donors of receiver R: every other input of its scenario, plus two inputs of the next scenario whose target rows are the two non-self rows."""
    rs = row_of(R, R['target'])
    out = []
    for i, D in sorted(items.items()):
        if D['scenario'] != R['scenario'] or i == R['id']:
            continue
        rd = row_of(D, D['target'])
        kd = row_of(R, D['target'])                 # same scenario: same entity -> same code
        if D['order'] == R['order']:
            t = 'AL'
        elif D['query'] == R['query']:
            t = 'KS'
        elif rd == rs:
            t = 'RS'
        else:
            t = 'BD'
        out.append({'id': i, 'type': t, 'row': rd, 'key': kd})
    nxt = scen_order[(scen_order.index(R['scenario']) + 1) % len(scen_order)]
    for want in [r for r in (0, 1, 2) if r != rs]:
        cand = sorted(i for i, D in items.items() if D['scenario'] == nxt and row_of(D, D['target']) == want)
        assert cand, (R['id'], nxt, want)
        out.append({'id': cand[0], 'type': 'OS', 'row': want, 'key': None})
    return out


def contrast_set(d, D):
    """Same-scenario donors that predict the row p = d['row'] under neither reading."""
    p = d['row']
    return [x for x in D if x['type'] != 'OS' and x['id'] != d['id'] and x['row'] != p and x['key'] != p]


def d_transfer(D, o):
    al = [d for d in D if d['type'] == 'AL']
    v = []
    for d in al:
        cs = contrast_set(d, D)
        if not cs:
            return None
        v.append(float(o[d['id']] == d['row']) - sum(float(o[x['id']] == d['row']) for x in cs) / len(cs))
    return sum(v) / len(v) if v else None


def rk_balanced(D):
    bd = [d for d in D if d['type'] == 'BD']
    return bool(bd) and sorted(d['row'] for d in bd) == sorted(d['key'] for d in bd)


def d_reading(D, o):
    if not rk_balanced(D):
        return None
    bd = [d for d in D if d['type'] == 'BD']
    return sum(float(o[d['id']] == d['row']) - float(o[d['id']] == d['key']) for d in bd) / len(bd)


def d_other(D, o):
    os_ = [d for d in D if d['type'] == 'OS']
    assert len(os_) == 2
    a, b = os_
    return (float(o[a['id']] == a['row']) - float(o[a['id']] == b['row']) + float(o[b['id']] == b['row']) - float(o[b['id']] == a['row'])) / 2


def conflict_pairs(D):
    al = [d for d in D if d['type'] == 'AL']
    return [(al[0], al[1]), (al[1], al[0])] if len(al) == 2 else []


def w_conflict(D, o):
    """o maps (S donor id, buffer donor id) -> output."""
    ps = conflict_pairs(D)
    if not ps:
        return None
    return sum(float(o[(s['id'], b['id'])] == s['row']) - float(o[(s['id'], b['id'])] == b['row']) for s, b in ps) / len(ps)


def count_trajectories(items, scen_order):
    n = 0
    for R in items.values():
        D = donor_table(R, items, scen_order)
        same = sum(1 for d in D if d['type'] != 'OS')
        for name, (_s, _v, _q, _k, donors, per_dir) in ARMS.items():
            k = {None: 1, 'same': same, 'same+os': same + 2, 'pair': len(conflict_pairs(D))}[donors]
            n += k * (len(DIRS) if per_dir else 1)
    return n


def boot(values, clusters, n=10000, seed=20261106):
    """values: {receiver: x or None}; clusters: {receiver: cluster}.  Mean over receivers with a value; 95% cluster bootstrap."""
    by = {}
    for r, x in values.items():
        if x is not None:
            by.setdefault(clusters[r], []).append(x)
    cs = sorted(by)
    if not cs:
        return None
    flat = [x for c in cs for x in by[c]]
    rng = random.Random(seed)
    v = []
    for _ in range(n):
        xs = [x for c in (rng.choice(cs) for _ in cs) for x in by[c]]
        v.append(sum(xs) / len(xs))
    v.sort()
    return {'mean': sum(flat) / len(flat), 'lo': v[int(0.025 * n)], 'hi': v[int(0.975 * n) - 1], 'n': len(flat), 'clusters': len(cs)}


def label(b, y_self):
    if b is None:
        return 'unjudgeable'
    if b['mean'] >= TH['follow'] and b['lo'] >= TH['follow_lo']:
        return 'FOLLOW'
    if b['mean'] <= TH['null'] and b['hi'] <= TH['null_hi']:
        return 'SELF' if y_self >= TH['self'] else 'DEGRADED'
    return 'INTERMEDIATE'


def cell(arm_out, tables, clusters, self_row, n_boot=10000):
    """arm_out: {receiver: {donor id: output}} for one donor arm in one direction."""
    dtr, drk, dos = {}, {}, {}
    n_self = n_sd = n_open = n_all = n_first = n_nf = 0
    for r, o in arm_out.items():
        D = tables[r]
        dtr[r] = d_transfer(D, o)
        drk[r] = d_reading(D, o)
        if all(d['id'] in o for d in D if d['type'] == 'OS'):
            dos[r] = d_other(D, o)
        for d in D:
            if d['type'] == 'OS' or d['id'] not in o:
                continue
            n_all += 1
            n_open += int(o[d['id']] != 'stop')
            if d['type'] in ('AL', 'BD'):
                n_sd += 1
                n_self += int(o[d['id']] == self_row[r])
                if self_row[r] != 0:
                    n_nf += 1
                    n_first += int(o[d['id']] == 0)
    y_self = n_self / n_sd if n_sd else 0.0
    b = boot(dtr, clusters, n_boot)
    return {'D_tr': b, 'label': label(b, y_self), 'y_self': y_self, 'open': n_open / n_all if n_all else 0.0,
            'first_when_self_not_first': n_first / n_nf if n_nf else 0.0, 'D_rk': boot(drk, clusters, n_boot), 'D_os': boot(dos, clusters, n_boot) if dos else None}


def reading(c):
    if c['label'] != 'FOLLOW' or c['D_rk'] is None:
        return 'unjudgeable'
    return 'row' if c['D_rk']['lo'] > 0 else ('key' if c['D_rk']['hi'] < 0 else 'mixed')


def rate(y):
    return sum(y.values()) / len(y) if y else 0.0


def decide(dirn, Y, cells, conflicts, clusters, n_boot=10000):
    """One direction.  Y: {arm: {receiver: 1/0}} full-answer correct for donor-free arms; cells: {arm: cell(...)}; conflicts: {arm: {receiver: W}}."""
    y = {a: rate(Y[a]) for a in Y}
    pre = {'clean': y['C0'] >= TH['clean'], 'damage': y['T0'] <= TH['dmg'], 'own_buffer': y['T_Bown'] >= TH['up'], 'own_state': y['T_Sown'] >= TH['up']}
    L = {k: cells[a]['label'] for k, a in CELLS.items()}
    if not (pre['clean'] and pre['damage'] and pre['own_buffer']):
        outcome = 'prerequisite_fail'
    elif L['d'] in ('INTERMEDIATE', 'unjudgeable'):
        outcome = 'indeterminate'                                           # neither confirmed nor refuted at the frozen thresholds
    elif L['d'] != 'FOLLOW':
        outcome = 'no_transfer'
    elif L['a'] == 'FOLLOW':
        outcome = 'buffer_general'
    elif L['a'] == 'SELF' and L['b'] == 'FOLLOW' and L['c'] == 'SELF' and pre['own_state']:
        outcome = 'precedence_flip'
    elif L['a'] == 'SELF' and L['b'] in ('SELF', 'DEGRADED'):
        outcome = 'background_dependent'
    else:
        outcome = 'partial'
    lab = {}
    lab['R_S'] = cells['C_Sd']['label']                                     # published baseline: donor state redirects a clean receiver
    lab['R_S4'] = cells['C_S4d']['label']
    lab['R_So'] = cells['C_Sod']['label']
    lab['R_QK'] = cells['T_Bvown_Bqkd']['label']                            # QST-01: donor q/k alone keeps the receiver's answer -> SELF
    d, v = cells['T_Bd'], cells['T_Bvd_Bqkown']
    if d['label'] != 'FOLLOW':
        lab['V'] = 'unjudgeable'
    else:
        lab['V'] = 'holds' if (v['label'] == 'FOLLOW' and v['D_tr']['mean'] >= TH['v_ratio'] * d['D_tr']['mean']) else 'fails'
    q = cells['T_Bvd']
    lab['VQ'] = 'holds' if (q['label'] == 'DEGRADED' and q['first_when_self_not_first'] >= TH['first']) else ('unjudgeable' if q['D_tr'] is None else 'fails')
    lab['S_T'] = cells['T_Sd']['label']
    lab['KV'] = cells['T_Kd']['label']
    opens = [cells[a]['open'] for a in ('T_Bd', 'T_Bvd_Bqkown', 'T_Bvown_Bqkd', 'T_Sown_Bd')]
    lab['OPEN'] = 'holds' if min(opens) >= TH['open'] else 'fails'
    lab['READ'] = reading(d)
    xs = {}
    for a in ('C_Sd1_Bd2', 'T_Sd1_Bd2'):
        b = boot(conflicts.get(a, {}), clusters, n_boot)
        xs[a] = b
        if b is None:
            lab['X_' + a[0]] = 'unjudgeable'
        elif b['mean'] >= TH['follow'] and b['lo'] >= TH['follow_lo']:
            lab['X_' + a[0]] = 'state_wins'
        elif b['mean'] <= -TH['follow'] and b['hi'] <= -TH['follow_lo']:
            lab['X_' + a[0]] = 'buffer_wins'
        else:
            lab['X_' + a[0]] = 'neither'
    return {'direction': dirn, 'outcome': outcome, 'prerequisites': pre, 'cells': L, 'labels': lab, 'Y': y, 'conflict': xs}
