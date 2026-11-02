"""QCO-01 frozen rules (plan §7).  Per direction, with E_s = scenario-equal mean of per-input means (6 scenarios):
G = E_s[Y_F - Y_V]; applicable iff G > 0 and >= 4 scenarios have a positive gap.
P = E_s[Y_R - Y_V] / G, P_rand likewise with R_rand.  D_i = 1[Y_F = 1 and Y_V = 0].
B = E_s[D_i * 1(ids_A == ids_V)] / E_s[D_i], B_rand likewise with A_rand.
'Common offset carries a substantial two-way effect' iff: edit-norm checks pass (R vs R_rand and A vs A_rand, every input);
applicable; P >= 0.5 and B >= 0.5; P - P_rand >= 0.25 and B - B_rand >= 0.25; >= 4/6 scenarios with mean(Y_R - Y_V) > 0;
>= 4/6 scenarios with at least one exact reproduction of the V token sequence by A.  Thresholds are pre-set minimum
substantive effects, not significance.  No directional prediction beyond the plan's candidate."""
TH = {'P_min': 0.5, 'B_min': 0.5, 'P_gap': 0.25, 'B_gap': 0.25, 'scen_min': 4, 'gap_scen_min': 4}


def scen_means(vals, scen_of):
    out = {}
    for i, v in vals.items():
        out.setdefault(scen_of[i], []).append(v)
    return {s: sum(x) / len(x) for s, x in out.items()}


def eq(vals, scen_of):
    m = scen_means(vals, scen_of)
    return sum(m.values()) / len(m)


def judge(Y, match_A, match_Ar, scen_of, norm_ok_R=True, norm_ok_A=True):
    """Y: arm -> {input: 0/1} for V, F, R, A, R_rand, A_rand; match_A / match_Ar: {input: ids_A == ids_V}."""
    ids = list(Y['V'])
    gap = scen_means({i: Y['F'][i] - Y['V'][i] for i in ids}, scen_of)
    G = sum(gap.values()) / len(gap)
    n_pos = sum(v > 0 for v in gap.values())
    out = {'G': G, 'gap_by_scenario': gap, 'n_pos_gap_scen': n_pos, 'applicable': G > 0 and n_pos >= TH['gap_scen_min']}
    D = {i: int(Y['F'][i] == 1 and Y['V'][i] == 0) for i in ids}
    eD = eq(D, scen_of)
    if G > 0:
        out['P'] = eq({i: Y['R'][i] - Y['V'][i] for i in ids}, scen_of) / G
        out['P_rand'] = eq({i: Y['R_rand'][i] - Y['V'][i] for i in ids}, scen_of) / G
    else:
        out['P'] = out['P_rand'] = None
    if eD > 0:
        out['B'] = eq({i: D[i] * int(match_A[i]) for i in ids}, scen_of) / eD
        out['B_rand'] = eq({i: D[i] * int(match_Ar[i]) for i in ids}, scen_of) / eD
    else:
        out['B'] = out['B_rand'] = None
    rv = scen_means({i: Y['R'][i] - Y['V'][i] for i in ids}, scen_of)
    rep = scen_means({i: D[i] * int(match_A[i]) for i in ids}, scen_of)
    out['scen_R_pos'] = sum(v > 0 for v in rv.values())
    out['scen_repro'] = sum(v > 0 for v in rep.values())
    out['norm_ok_R'], out['norm_ok_A'] = norm_ok_R, norm_ok_A
    out['n_D'] = sum(D.values())
    if not (norm_ok_R and norm_ok_A):
        out['verdict'] = 'engineering_not_judgeable'
    elif not out['applicable'] or out['B'] is None:
        out['verdict'] = 'not_applicable'
    else:
        r_ok = out['P'] >= TH['P_min'] and out['P'] - out['P_rand'] >= TH['P_gap'] and out['scen_R_pos'] >= TH['scen_min']
        a_ok = out['B'] >= TH['B_min'] and out['B'] - out['B_rand'] >= TH['B_gap'] and out['scen_repro'] >= TH['scen_min']
        out['R_ok'], out['A_ok'] = r_ok, a_ok
        out['verdict'] = {(True, True): 'two_way', (True, False): 'R_only', (False, True): 'A_only', (False, False): 'neither'}[(r_ok, a_ok)]
    return out
