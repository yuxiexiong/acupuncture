"""EH pure functions.  CONTRACT.zh-CN.md r01 §4–5.  D = max_S z - max_{V\\S} z (raw logits; readout.D).

2x2 (entry x, deep history H; conv histories clean):  00 = C_native, 10 = X10, 01 = H01, 11 = XH11 (= N:CC).
    e1 = D11 - D00;  hist|clean entry = D01 - D00;  hist|T entry = D11 - D10;  entry|clean hist = D10 - D00;
    entry|T hist = D11 - D01;  I = D11 - D10 - D01 + D00.
FIX order:  e2_rev = D(FIX0) - D00 (clean background);  e2_fwd = D(N:CFIX) - D(N:CC) (NFC e2, from B3 records).
"""
RULE = {
    'e1_min': 1.0,          # |e1| below this -> shares not formable
    'major': 0.75, 'minor': 0.25,
    'e2_min': 1.0,          # |e2_fwd| below this -> order ratio not formable
    'close_rel': 0.25,      # |e2_rev - e2_fwd| <= 0.25 |e2_fwd| -> order-independent
    'needs_ctx': 0.5,       # e2_rev / e2_fwd <= 0.5 -> needs the e1 context
    'larger': 1.5,          # ratio >= 1.5 -> larger in the clean background
    'scen_count': 5, 'dir_count': 3,
}


def two_by_two(D00, D10, D01, D11):
    e1 = D11 - D00
    out = {'e1': e1, 'hist_clean_entry': D01 - D00, 'hist_T_entry': D11 - D10, 'entry_clean_hist': D10 - D00,
           'entry_T_hist': D11 - D01, 'I': D11 - D10 - D01 + D00}
    if abs(e1) >= RULE['e1_min']:
        out['s_H'] = out['hist_clean_entry'] / e1
        out['s_X'] = out['entry_clean_hist'] / e1
    else:
        out['s_H'] = out['s_X'] = None
    return out


def label_2x2(s_H, s_X):
    if s_H is None:
        return 'not_formable'
    hi, lo = RULE['major'], RULE['minor']
    if s_H >= hi and s_X >= hi:
        return 'both_alone_strong'
    if s_H >= hi and s_X <= lo:
        return 'history_alone_suffices'
    if s_X >= hi and s_H <= lo:
        return 'entry_alone_suffices'
    if s_H <= lo and s_X <= lo:
        return 'joint_needed'
    return 'partial'


def label_order(e2_rev, e2_fwd):
    if abs(e2_fwd) < RULE['e2_min']:
        return 'not_formable', None
    r = e2_rev / e2_fwd
    if abs(e2_rev - e2_fwd) <= RULE['close_rel'] * abs(e2_fwd):
        return 'order_independent', r
    if r <= RULE['needs_ctx']:
        return 'needs_context', r
    if r >= RULE['larger']:
        return 'larger_in_clean', r
    return 'partial', r


def scenario_pairs(values):
    out = {}
    for iid, v in values.items():
        s, f = iid.rsplit('-', 1)
        out.setdefault(s, {})[f] = v
    return {s: (d['f0'], d['f1']) for s, d in sorted(out.items())}


def direction_label(pairs):
    counts = {}
    for s, (a, b) in pairs.items():
        if a == b:
            counts[a] = counts.get(a, 0) + 1
    best = [k for k, v in counts.items() if v >= RULE['scen_count']]
    return (best[0] if best else None), counts


def cross_label(per_dir):
    vals = [v for v in per_dir.values() if v is not None]
    for v in set(vals):
        if vals.count(v) >= RULE['dir_count']:
            return v
    return 'condition_dependent'


def predictions(rows):
    """rows: direction -> {input: {'s_H','s_X','order_ratio'}}.  Speculative tier, frozen before the run.
    P1: s_H >= 0.5 and s_H > s_X (both facts) in >= 5/6 scenarios of >= 3/4 directions.
    P2: e2_rev / e2_fwd <= 0.5 (FIX V history needs the e1 context), same counting."""
    def count(d, ok):
        pairs = scenario_pairs({i: ok(v) for i, v in rows[d].items()})
        return sum(a and b for a, b in pairs.values())
    p1 = {d: count(d, lambda v: v['s_H'] is not None and v['s_H'] >= 0.5 and v['s_H'] > v['s_X']) for d in rows}
    p2 = {d: count(d, lambda v: v['order_ratio'] is not None and v['order_ratio'] <= RULE['needs_ctx']) for d in rows}
    need = RULE['scen_count']
    return {'P1': sum(x >= need for x in p1.values()) >= RULE['dir_count'], 'P1_counts': p1,
            'P2': sum(x >= need for x in p2.values()) >= RULE['dir_count'], 'P2_counts': p2}
