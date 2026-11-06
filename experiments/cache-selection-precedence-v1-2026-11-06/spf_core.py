"""SPF-01 frozen read-outs, draft r02 (CONTRACT §4-§6).  Pure Python, no model code.  Every label is computed from the measurement named next to it.

Panel: LVK new panel, 48 inputs, 6 scenarios (cluster unit).  A scenario fixes three entities A/B/C with their codes; an input is (rotation of the
record list, queried entity).  Rows are 0-based positions in the receiver's record list.

Arms are swaps of cache tensors at the boundary before the last prompt token (no hooks).  Components:
  S    recurrent_states of the deep GDN layers G (S4: layers 16-18 only; So: G without 16-18)
  Bv   V channels of conv_states of G        Bqk  q/k channels of conv_states of G
  K    keys/values of the deep full-attention layers (own clean: all cached positions; donor: the last 4 cached positions)
Sources: oc own clean run, on own needle run (same direction), d donor's clean run, d2 the partner donor's clean run.

Per (receiver, donor): self = receiver's target row; row = donor's target row in the donor's list; key = row, in the RECEIVER's list, of the entity
the donor asks about (None for a donor from another scenario).  Donor types:
  AL same rotation, other query (row == key)      KS other rotation, same query (key == self)
  RS other rotation, row == self                  BD other rotation, self/row/key all distinct      OS other scenario (row only)
Output of a trajectory: 0/1/2 = the row of the single listed code in the natural full answer; 'stop' / 'other' otherwise.

Statistics.  Each is exactly 0 for ANY donor-independent output (always self, always first-listed, always stop):
  D_tr  transfer, on AL donors: 1[out_d == p_d] minus the rate of that same row p_d among donors that do not predict it (contrast set).
  D_rk  on balanced BD sets: +1 output at the donor's row, -1 output at the donor's key row.
  D_ks  on the two KS donors: +1 output at the donor's row (key reading predicts self).      D_rs  on two RS donors: +1 output at the donor's key row.
  D_os  on the two other-scenario donors: +1 output at the donor's row.
  W     conflict (S from one AL donor, buffer from the other, both orders): +1 follows the S donor, -1 follows the buffer donor.
Uncertainty: 95% percentile interval from resampling the scenarios with replacement (10000 draws, seed 20261106); exact sign-flip permutation p over
scenarios for paired contrasts.  With 6 scenarios these express development-stage uncertainty only.

Three-way reading of an effect x against one margin M = 0.25 (smallest effect of interest: a quarter of the answers, net, determined by the donor):
  'holds' lo >= M        'below' hi <= M        'indeterminate' otherwise
Primary read-outs per direction (cells a = C_Bd, b = C_ST_Bd, c = T_Sown_Bd, d = T_Bd):
  E        D_tr(d)                       the buffer-donor effect exists in the native intervened run
  D_needle D_tr(d) - D_tr(c), paired     putting the receiver's own clean recurrent state back suppresses it
  D_clean  D_tr(b) - D_tr(a), paired     putting the needle-formed recurrent state into the clean run enables it
"""
import itertools
import random

M = 0.25
TH = {'self': 0.75, 'clean': 0.90, 'dmg': 0.25, 'up': 0.75, 'open': 0.90, 'first': 0.50, 'label_follow': 0.50, 'label_null': 0.15}
MAIN, SECOND = 'N_L00_C4146_D-1', 'N_L00_C1210_D-1'
DIRS = (MAIN, SECOND)
G = (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
G4 = (16, 17, 18)            # inferred from the 9B block convention of arXiv 2611.01909; the paper gives no layer range for 4B
ATTN = (15, 19, 23, 27, 31)
DONOR_TYPES = ('AL', 'KS', 'RS', 'BD', 'OS')

# name: (S, Bv, Bqk, K, donors, scope).  donors: None, 'same', 'same+os', 'pair'.  scope: 'once' (no needle), 'both' directions, 'main' direction only.
# '-' leaves the background's own value.  In the second direction 'same+os' runs the same-scenario donors only.
ARMS = {
    'C0':           ('-',  '-',  '-',  '-',  None,      'once'),
    'C_Sd':         ('d',  '-',  '-',  '-',  'same',    'once'),
    'C_S4d':        ('d4', '-',  '-',  '-',  'same',    'once'),
    'C_Sod':        ('do', '-',  '-',  '-',  'same',    'once'),
    'C_Bd':         ('-',  'd',  'd',  '-',  'same',    'once'),
    'C_Sd1_Bd2':    ('d',  'd2', 'd2', '-',  'pair',    'once'),
    'C_ST':         ('on', '-',  '-',  '-',  None,      'both'),
    'C_ST_Bd':      ('on', 'd',  'd',  '-',  'same+os', 'both'),
    'T0':           ('-',  '-',  '-',  '-',  None,      'both'),
    'T_Bown':       ('-',  'oc', 'oc', '-',  None,      'both'),
    'T_Sown':       ('oc', '-',  '-',  '-',  None,      'both'),
    'T_Bd':         ('-',  'd',  'd',  '-',  'same+os', 'both'),
    'T_Sown_Bd':    ('oc', 'd',  'd',  '-',  'same',    'both'),
    'T_Bvd_Bqkown': ('-',  'd',  'oc', '-',  'same',    'both'),
    'T_Bvown_Bqkd': ('-',  'oc', 'd',  '-',  'same',    'both'),
    'T_Bvown':      ('-',  'oc', '-',  '-',  None,      'main'),
    'T_Kown':       ('-',  '-',  '-',  'oc', None,      'main'),
    'T_Bvd':        ('-',  'd',  '-',  '-',  'same',    'main'),
    'T_Sd':         ('d',  '-',  '-',  '-',  'same',    'main'),
    'T_Sd1_Bd2':    ('d',  'd2', 'd2', '-',  'pair',    'main'),
    'T_Kd':         ('-',  '-',  '-',  'd',  'same',    'main'),
}
CELLS = {'a': 'C_Bd', 'b': 'C_ST_Bd', 'c': 'T_Sown_Bd', 'd': 'T_Bd'}
NULL_ARM, ANCHOR_ARM = 'T_Bvown_Bqkd', 'C_Sd'      # known-null transplant (QST-01) and known-effect transplant (NSR-01 / published)


def arms_for(dirn):
    return [a for a, s in ARMS.items() if s[5] in ('once', 'both') or dirn == MAIN]


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


def _pair(a, b, o, f):
    return (float(o[a['id']] == a[f]) - float(o[a['id']] == b[f]) + float(o[b['id']] == b[f]) - float(o[b['id']] == a[f])) / 2


def d_pair(D, o, typ, f):
    """Paired statistic on the two donors of one type whose predictions under field f differ and are not the self row."""
    ds = [d for d in D if d['type'] == typ]
    if len(ds) != 2 or ds[0][f] == ds[1][f] or any(d['id'] not in o for d in ds):
        return None
    return _pair(ds[0], ds[1], o, f)


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
    n = {d: 0 for d in ('once',) + DIRS}
    for R in items.values():
        D = donor_table(R, items, scen_order)
        same = sum(1 for d in D if d['type'] != 'OS')
        for name, (_s, _v, _q, _k, donors, scope) in ARMS.items():
            for dirn in (('once',) if scope == 'once' else (DIRS if scope == 'both' else (MAIN,))):
                k = {None: 1, 'same': same, 'same+os': same + (2 if dirn == MAIN else 0), 'pair': len(conflict_pairs(D))}[donors]
                n[dirn] += k
    n['total'] = sum(n.values())
    return n


def boot(values, clusters, n=10000, seed=20261106):
    """values: {receiver: x or None}.  Mean over receivers with a value; 95% scenario-cluster bootstrap; exact sign-flip permutation p over scenarios."""
    by = {}
    for r, x in values.items():
        if x is not None:
            by.setdefault(clusters[r], []).append(x)
    cs = sorted(by)
    if not cs:
        return None
    flat = [x for c in cs for x in by[c]]
    obs = sum(flat) / len(flat)
    rng = random.Random(seed)
    v = []
    for _ in range(n):
        xs = [x for c in (rng.choice(cs) for _ in cs) for x in by[c]]
        v.append(sum(xs) / len(xs))
    v.sort()
    sums = [sum(by[c]) for c in cs]
    hits = sum(1 for sg in itertools.product((1, -1), repeat=len(cs)) if abs(sum(s * t for s, t in zip(sg, sums))) >= abs(sum(sums)) - 1e-12)
    return {'mean': obs, 'lo': v[int(0.025 * n)], 'hi': v[int(0.975 * n) - 1], 'n': len(flat), 'clusters': len(cs), 'perm_p': hits / 2 ** len(cs)}


def perm_null(arm_out, tables, n=2000, seed=20261107):
    """Null of the mean D_tr by construction: within each receiver, shuffle which same-scenario donor produced which output."""
    rng = random.Random(seed)
    v = []
    for _ in range(n):
        xs = []
        for r, o in sorted(arm_out.items()):
            ids = [d['id'] for d in tables[r] if d['type'] != 'OS' and d['id'] in o]
            vals = [o[i] for i in ids]
            rng.shuffle(vals)
            x = d_transfer(tables[r], dict(zip(ids, vals)))
            if x is not None:
                xs.append(x)
        v.append(sum(xs) / len(xs))
    v.sort()
    return {'mean': sum(v) / n, 'hi': v[int(0.975 * n) - 1]}


def three(b, m=M):
    if b is None:
        return 'unjudgeable'
    return 'holds' if b['lo'] >= m else ('below' if b['hi'] <= m else 'indeterminate')


def diff(xa, xb):
    return {r: (xa[r] - xb[r]) if (xa.get(r) is not None and xb.get(r) is not None) else None for r in xa}


def cell(arm_out, tables, clusters, self_row, n_boot=10000, n_perm=0):
    """arm_out: {receiver: {donor id: output}} for one donor arm in one direction.  n_perm > 0 (required for the four cells): permutation null."""
    per = {k: {} for k in ('tr', 'rk', 'ks', 'rs', 'os')}
    n_self = n_sd = n_open = n_all = n_first = n_nf = 0
    for r, o in arm_out.items():
        D = tables[r]
        per['tr'][r] = d_transfer(D, o)
        per['rk'][r] = d_reading(D, o)
        per['ks'][r] = d_pair(D, o, 'KS', 'row')
        per['rs'][r] = d_pair(D, o, 'RS', 'key')
        per['os'][r] = d_pair(D, o, 'OS', 'row')
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
    b = {k: boot(v, clusters, n_boot) for k, v in per.items()}
    y_self = n_self / n_sd if n_sd else 0.0
    # development label, thresholds not calibrated: descriptive only, enters no outcome
    if b['tr'] is None:
        tag = 'unjudgeable'
    elif b['tr']['mean'] >= TH['label_follow']:
        tag = 'FOLLOW'
    elif b['tr']['mean'] <= TH['label_null']:
        tag = 'SELF' if y_self >= TH['self'] else 'DEGRADED'
    else:
        tag = 'INTERMEDIATE'
    return {'D_tr': b['tr'], 'D_rk': b['rk'], 'D_ks': b['ks'], 'D_rs': b['rs'], 'D_os': b['os'], 'per_receiver': per['tr'], 'effect': three(b['tr']),
            'perm_null': perm_null(arm_out, tables, n_perm) if n_perm else None,
            'tag': tag, 'y_self': y_self, 'open': n_open / n_all if n_all else 0.0, 'first_when_self_not_first': n_first / n_nf if n_nf else 0.0}


def reading(c):
    """Only meaningful when the transfer effect holds.  A D_rk interval that straddles 0 is 'undetermined', never 'mixed'."""
    if c['effect'] != 'holds':
        return 'unjudgeable'
    rk = c['D_rk']
    if rk is not None and rk['lo'] >= M:
        return 'row'
    if rk is not None and rk['hi'] <= -M:
        return 'key'
    if three(c['D_ks']) == 'holds' and three(c['D_rs']) == 'holds':
        return 'both'                                    # row-following shown where the key predicts self, AND key-following where the row predicts self
    return 'undetermined'


def rate(y):
    return sum(y.values()) / len(y) if y else 0.0


def decide(dirn, Y, cells, conflicts, clusters, n_boot=10000):
    """One direction.  Y: {arm: {receiver: 1/0}} full-answer correct for donor-free arms; cells: {arm: cell(...)}; conflicts: {arm: {receiver: W}}."""
    y = {a: rate(Y[a]) for a in Y}
    pre = {'clean': y['C0'] >= TH['clean'], 'damage': y['T0'] <= TH['dmg'], 'own_buffer': y['T_Bown'] >= TH['up'], 'own_state': y['T_Sown'] >= TH['up']}
    c = {k: cells[a] for k, a in CELLS.items()}
    # margin check: the by-construction null of D_tr (donor labels shuffled within receiver) must stay below M in the four cells;
    # otherwise M does not separate an effect from donor-independent variation on this panel and every 'holds' is downgraded
    null_hi = max(c[k]['perm_null']['hi'] for k in c)
    margin_ok = null_hi < M
    for x in cells.values():
        if not margin_ok and x['effect'] == 'holds':
            x['effect'] = 'indeterminate'

    def eff(lab):
        return 'indeterminate' if (lab == 'holds' and not margin_ok) else lab

    E = c['d']['effect']
    dn = boot(diff(c['d']['per_receiver'], c['c']['per_receiver']), clusters, n_boot) if pre['own_state'] else None
    dc = boot(diff(c['b']['per_receiver'], c['a']['per_receiver']), clusters, n_boot)
    inter = boot(diff(diff(c['d']['per_receiver'], c['c']['per_receiver']), diff(c['b']['per_receiver'], c['a']['per_receiver'])), clusters, n_boot)
    Ln, Lc = eff(three(dn)), eff(three(dc))
    if not (pre['clean'] and pre['damage'] and pre['own_buffer']):
        outcome = 'prerequisite_fail'
    elif E == 'below':
        outcome = 'no_transfer'
    elif E != 'holds':
        outcome = 'indeterminate'
    elif Ln == 'holds' and Lc == 'holds':
        outcome = 'source_modulates'                     # the pattern H predicts
    elif Ln == 'holds' and Lc == 'below':
        outcome = 'restore_suppresses_only'              # the needle-formed state alone does not enable the effect in a clean run
    elif Ln == 'below' and Lc == 'below':
        outcome = 'not_source_dependent'                 # the buffer-donor effect does not depend on where the recurrent state comes from
    else:
        outcome = 'partial'
    lab = {'E': E, 'D_needle': Ln, 'D_clean': Lc, 'buffer_in_clean': c['a']['effect'], 'margin_check': 'passed' if margin_ok else 'failed'}
    lab['R_S'] = cells['C_Sd']['effect']                                  # known effect: donor state redirects a clean receiver
    lab['R_S4'] = cells['C_S4d']['effect']
    lab['R_So'] = cells['C_Sod']['effect']
    q = cells[NULL_ARM]                                                   # known null: donor q/k alone keeps the receiver's answer (QST-01)
    lab['R_QK'] = 'holds' if (q['effect'] == 'below' and q['y_self'] >= TH['self']) else ('fails' if q['effect'] == 'holds' else 'indeterminate')
    v = cells['T_Bvd_Bqkown']
    lab['V'] = 'unjudgeable' if E != 'holds' else ('holds' if (v['effect'] == 'holds' and q['effect'] == 'below') else
                                                   ('fails' if v['effect'] == 'below' else 'indeterminate'))
    lab['OPEN'] = 'holds' if min(cells[a]['open'] for a in ('T_Bd', 'T_Bvd_Bqkown', NULL_ARM, 'T_Sown_Bd')) >= TH['open'] else 'fails'
    lab['READ'] = reading(c['d'])
    xs = {}
    if dirn == MAIN:
        vq = cells['T_Bvd']
        lab['VQ'] = 'holds' if (vq['effect'] == 'below' and vq['first_when_self_not_first'] >= TH['first']) else ('fails' if vq['effect'] == 'holds' else 'indeterminate')
        lab['S_T'] = cells['T_Sd']['effect']
        lab['KV'] = cells['T_Kd']['effect']
    for a in ('C_Sd1_Bd2',) + (('T_Sd1_Bd2',) if dirn == MAIN else ()):
        b = boot(conflicts.get(a, {}), clusters, n_boot)
        xs[a] = b
        lab['X_' + a[0]] = 'unjudgeable' if b is None else ('state' if b['lo'] >= M else ('buffer' if b['hi'] <= -M else 'undetermined'))
    return {'direction': dirn, 'outcome': outcome, 'prerequisites': pre, 'labels': lab, 'Y': y, 'conflict': xs,
            'D': {k: c[k]['D_tr'] for k in c}, 'D_needle': dn, 'D_clean': dc, 'interaction': inter,
            'null_arm': q['D_tr'], 'anchor_arm': cells[ANCHOR_ARM]['D_tr'], 'perm_null_hi': null_hi, 'tags': {a: cells[a]['tag'] for a in cells}}
