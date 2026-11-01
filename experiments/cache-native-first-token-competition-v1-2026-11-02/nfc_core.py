"""NFC-01 pure functions (no model).  CONTRACT.zh-CN.md r01 (plan v1 §3 readouts + plan v2 chain/exits).

Per cell r (raw logits z_r, stop set S = {248044, 248046}):
    D_r = max_S z_r - max_{V\\S} z_r                     (recorded readout.D, full vocabulary)
    fixed candidates from C_native: s0 = C_native stop winner, q0 = C_native non-stop winner (== a_token)
    F_r = z_r(s0) - z_r(q0);  A_r = max_S z_r - z_r(s0);  B_r = max_{V\\S} z_r - z_r(q0);   D_r = F_r + A_r - B_r
Chain: C_native -> N:CC -> N:CFIX -> N:CT -> N:TT (== T_native):  e1..e4, delta_native = e1 + e2 + e3 + e4.
"""
STOP = (248044, 248046)
CHAIN = ('C_native', 'N:CC', 'N:CFIX', 'N:CT', 'N:TT')
EDGES = ('e1', 'e2', 'e3', 'e4')
RULE = {
    'small': 0.5,            # |delta| < 0.5 logit -> small (descriptive, plan v1 §4)
    'close_abs': 0.25, 'close_rel': 0.25,
    'conc_tiny': 1e-6,       # sum |e| <= tiny -> concentration not formable
    'recon_tol': 1e-6,       # recorded summaries vs reconstruction (FP64 from stored values)
    'identity_rel': 1e-9,
    'scen_count': 5, 'dir_count': 3,
}


def cell_terms(ro, score, s0, q0):
    """ro: recorded readout (raw s44/s46/a, D); score: recorded score dict.  Exact recombination of stored summaries."""
    z = {STOP[0]: ro['raw']['s44'], STOP[1]: ro['raw']['s46']}
    stop_max = max(z.values())
    D = ro['D']
    nonstop_max = stop_max - D
    zq0 = ro['raw']['a']
    F = z[s0] - zq0
    A = stop_max - z[s0]
    B = nonstop_max - zq0
    err = D - (F + A - B)
    return {'D': D, 'F': F, 'A': A, 'B': B, 'identity_err': err, 'stop_max': stop_max, 'nonstop_max': nonstop_max,
            'z_s0': z[s0], 'z_q0': zq0, 'vocab_mean': ro['vocab_mean'],
            'stop_winner': score['stop_winner'], 'nonstop_winner': score['nonstop_winner'], 'eos': bool(score['first_step_eos']),
            'stop_advantage_recorded': score['stop_advantage']}


def checks(t):
    """Cross-checks between recorded fields with a shared source (implementation acceptance, not independent validation)."""
    out = {'D_vs_stop_advantage': abs(t['D'] - t['stop_advantage_recorded']),
           'eos_sign_consistent': (t['D'] > 0) == t['eos'] if t['D'] != 0 else None,
           'stop_winner_is_max': None}
    return out


def edge(u, v):
    """Differences of D, F, A, B and the mean-reference two-sided split of dF along u -> v."""
    d = {k: v[k] - u[k] for k in ('D', 'F', 'A', 'B')}
    b_mean = v['vocab_mean'] - u['vocab_mean']
    dzs, dzq = v['z_s0'] - u['z_s0'], v['z_q0'] - u['z_q0']
    d['S_mean'] = dzs - b_mean
    d['Q_mean'] = -(dzq - b_mean)
    d['split_err'] = d['F'] - (d['S_mean'] + d['Q_mean'])
    d['dz_s0'], d['dz_q0'], d['b_mean'] = dzs, dzq, b_mean
    d['winner_change'] = {'stop': u['stop_winner'] != v['stop_winner'], 'nonstop': u['nonstop_winner'] != v['nonstop_winner'],
                          'eos': (u['eos'], v['eos'])}
    return d


def median_split(du_s0, du_q0, b_median):
    return {'S_median': du_s0 - b_median, 'Q_median': -(du_q0 - b_median)}


def chain(cells):
    """cells: name -> cell_terms for the five chain cells.  Returns e1..e4 and their edge decompositions."""
    out = {}
    for i, k in enumerate(EDGES):
        out[k] = edge(cells[CHAIN[i]], cells[CHAIN[i + 1]])
    total = cells[CHAIN[-1]]['D'] - cells[CHAIN[0]]['D']
    s = sum(out[k]['D'] for k in EDGES)
    absum = sum(abs(out[k]['D']) for k in EDGES)
    conc = {k: abs(out[k]['D']) / absum for k in EDGES} if absum > RULE['conc_tiny'] else None
    largest = max(EDGES, key=lambda k: abs(out[k]['D'])) if absum > RULE['conc_tiny'] else None
    eos_path = [cells[c]['eos'] for c in CHAIN]
    flips = [EDGES[i] for i in range(4) if eos_path[i] != eos_path[i + 1]]
    nonstop_changes = [EDGES[i] for i in range(4) if cells[CHAIN[i]]['nonstop_winner'] != cells[CHAIN[i + 1]]['nonstop_winner']]
    return {'edges': out, 'delta_native': total, 'telescope_err': total - s, 'abs_sum': absum, 'concentration': conc,
            'largest_abs_edge': largest, 'eos_path': eos_path, 'eos_flip_edges': flips, 'nonstop_winner_change_edges': nonstop_changes}


def transition(c_eos, t_eos):
    return {(False, True): 'nonstop_to_stop', (True, False): 'stop_to_nonstop', (True, True): 'both_stop', (False, False): 'both_nonstop'}[(c_eos, t_eos)]


def aux_label(d_fix, d_native):
    """Plan v1 §4 descriptive correspondence (auxiliary only under plan v2)."""
    if d_fix is None or d_native is None:
        return 'not_comparable'
    if abs(d_native) < RULE['small']:
        return 'native_small'
    if abs(d_fix) < RULE['small']:
        return 'mixed_small'
    if (d_fix > 0) != (d_native > 0):
        return 'opposite'
    if abs(d_fix - d_native) <= max(RULE['close_abs'], RULE['close_rel'] * abs(d_native)):
        return 'same_direction_close'
    return 'same_direction_different_size'


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


def crest_split(cells_d):
    """e3 = R_D + I_D on the D readout (plan v2 §2 label correction)."""
    R = cells_d['N:CREST'] - cells_d['N:CC']
    I = cells_d['N:CT'] - cells_d['N:CFIX'] - cells_d['N:CREST'] + cells_d['N:CC']
    return {'R_D': R, 'I_D': I, 'e3': cells_d['N:CT'] - cells_d['N:CFIX'], 'err': (cells_d['N:CT'] - cells_d['N:CFIX']) - (R + I)}
