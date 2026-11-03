"""LVK-01 frozen read-outs (plan §5 with the review amendments; CONTRACT §5).  Operational labels, not significance tests.
Per panel and direction, Z in {G, M, Y}, per input then scenario-equal (M on target-not-first, G and Y on all 48):
  e0 = L01 - L00; e1 = L11 - L10; vmain0 = L10 - L00; vmain1 = L11 - L01; I_local = e1 - e0;
  I_block = (VW - V) - e0; gap = I_local - I_block = d0 - d1 with d0 = V - L10, d1 = VW - L11.
  d0 / d1: conditional total effect of keeping the restored V history (old slots) without / with the write-term k operation.
  gap: how keeping the restored history moderates the k effect (sign opposite to d1 - d0).
  On G, d0 = d1 = 0 by construction (t1 bridge) -> engineering check only.
Stable directional (expected sign +): eq >= 0.25 and >= 4/6 scenario means > 0; 'opposite' symmetric.
Ratio I_local / I_block only when |I_block| >= 0.5: 'effect ratio relative to the whole-V-restoration interaction reference' (descriptive).
Delivery: net (Y_b - Y_a) >= 2 and >= 2 scenarios with fixes -> multi_scenario.
New-panel replication: NVW relation I_block(M) stable +; KUC relation on V: W (VW - V) joint support (M stable + and Y net >= 2), E (VE - V)
not joint -> single_W; W/K ratio when |VK - V| >= 0.5 (descriptive)."""
TH = {'abs': 0.25, 'scen': 4, 'y_net': 2, 'y_scen': 2, 'den': 0.5}


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def smeans(vals, scen):
    out = {}
    for i, v in vals.items():
        out.setdefault(scen[i], []).append(v)
    return {s: sum(x) / len(x) for s, x in out.items()}


def stable(vals, scen, sign=1):
    sm = smeans(vals, scen)
    eq = mean(sm.values())
    npos = sum(1 for v in sm.values() if sign * v > 0)
    nneg = sum(1 for v in sm.values() if sign * v < 0)
    lab = 'expected' if (sign * eq >= TH['abs'] and npos >= TH['scen']) else ('opposite' if (-sign * eq >= TH['abs'] and nneg >= TH['scen']) else 'not_stable')
    return {'eq': eq, 'scen': sm, 'label': lab, 'n_pos': npos, 'n_neg': nneg}


def delivery(Ya, Yb, scen):
    net = sum(Yb[i] - Ya[i] for i in Ya)
    fixed = {}
    for i in Ya:
        if Ya[i] == 0 and Yb[i] == 1:
            fixed[scen[i]] = fixed.get(scen[i], 0) + 1
    broken = sum(1 for i in Ya if Ya[i] == 1 and Yb[i] == 0)
    return {'net': net, 'fixed': sum(fixed.values()), 'broken': broken, 'n_scen_fixed': len(fixed),
            'label': 'multi_scenario' if (net >= TH['y_net'] and len(fixed) >= TH['y_scen']) else 'none'}


def ratio(num, den):
    return num / den if (num is not None and den is not None and abs(den) >= TH['den']) else None


def contrasts(Z, ids):
    """Z[arm][i] -> per-input contrast dicts."""
    c = {}
    for i in ids:
        L00, L01, L10, L11, Vv, VW = (Z[a][i] for a in ('L00', 'L01', 'L10', 'L11', 'V', 'VW'))
        e0, e1 = L01 - L00, L11 - L10
        c.setdefault('e0', {})[i] = e0
        c.setdefault('e1', {})[i] = e1
        c.setdefault('vmain0', {})[i] = L10 - L00
        c.setdefault('vmain1', {})[i] = L11 - L01
        c.setdefault('I_local', {})[i] = e1 - e0
        c.setdefault('I_block', {})[i] = (VW - Vv) - e0
        c.setdefault('gap', {})[i] = (e1 - e0) - ((VW - Vv) - e0)
        c.setdefault('d0', {})[i] = Vv - L10
        c.setdefault('d1', {})[i] = VW - L11
    return c


def panel_direction(Z, scen, tnf, allids, new_panel):
    """Z[readout][arm][input] with arms L00..L11, V, VW (+ VE, VK, F on the new panel)."""
    res = {}
    for r, ids in (('M', sorted(tnf)), ('G', sorted(allids))):
        c = contrasts(Z[r], ids)
        res[r] = {k: stable(v, scen) for k, v in c.items()}
        res[r]['ratio_local_over_block'] = ratio(res[r]['I_local']['eq'], res[r]['I_block']['eq'])
    gd = [abs(v) for k in ('d0', 'd1') for v in contrasts(Z['G'], sorted(allids))[k].values()]
    res['G_identity_max_abs'] = max(gd)
    Y = Z['Y']
    res['Y'] = {k: sum(v.values()) for k, v in contrasts(Y, sorted(allids)).items()}
    res['Y_totals'] = {a: sum(Y[a].values()) for a in Y}
    res['delivery'] = {'k_increment_L11_vs_L10': delivery(Y['L10'], Y['L11'], scen), 'total_L11_vs_L00': delivery(Y['L00'], Y['L11'], scen),
                       'k_native_L01_vs_L00': delivery(Y['L00'], Y['L01'], scen), 'v_main_L10_vs_L00': delivery(Y['L00'], Y['L10'], scen)}
    res['labels'] = {'I_local_M': res['M']['I_local']['label'], 'I_block_M': res['M']['I_block']['label']}
    if new_panel:
        ids = sorted(tnf)
        W = stable({i: Z['M']['VW'][i] - Z['M']['V'][i] for i in ids}, scen)
        E = stable({i: Z['M']['VE'][i] - Z['M']['V'][i] for i in ids}, scen)
        Kk = stable({i: Z['M']['VK'][i] - Z['M']['V'][i] for i in ids}, scen)
        yW, yE = delivery(Y['V'], Y['VW'], scen), delivery(Y['V'], Y['VE'], scen)
        jW = W['label'] == 'expected' and yW['net'] >= TH['y_net']
        jE = E['label'] == 'expected' and yE['net'] >= TH['y_net']
        res['kuc_replication'] = {'W': W, 'E': E, 'K': Kk, 'Y_W': yW, 'Y_E': yE, 'W_over_K': ratio(W['eq'], Kk['eq']), 'E_over_K': ratio(E['eq'], Kk['eq']),
                                  'label': 'single_W' if (jW and not jE) else ('both' if (jW and jE) else ('single_E' if jE else 'none'))}
        res['labels']['kuc_replication'] = res['kuc_replication']['label']
        res['F_minus_V_M'] = stable({i: Z['M']['F'][i] - Z['M']['V'][i] for i in ids}, scen)
    return res


def multi(labels_by_dir, key, value):
    n = sum(1 for lab in labels_by_dir.values() if lab.get(key) == value)
    return {'n': n, 'multi': n >= 2}
