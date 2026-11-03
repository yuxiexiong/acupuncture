"""NVB-01 frozen read-outs (CONTRACT r01 §5).  Operational labels, not significance tests.  CPU only.

Cells B(c, a, b): c = v used by the t1 output computation (0 native v0, 1 shadow v1); a = v used by the stored recurrent state (0 v0, 1 v1,
'r<j>' v0 + matched random rho_j, only with c = 0); b = write-term k (0 k0, 1 k1).  M is the C-route t2 margin.
k effect in background (c, a): e(c, a) = M(c, a, 1) - M(c, a, 0), per input.
Paired differences (per input, then target-not-first 32 inputs, six scenarios equally weighted):
  DS0 = e(0,1) - e(0,0)   storage use of v1 with the native t1 output kept           (PRIMARY)
  DS1 = e(1,1) - e(1,0)   storage use of v1 with the restored output branch
  DO0 = e(1,0) - e(0,0)   output-branch use of v1 with native storage
  DO1 = e(1,1) - e(0,1)   output-branch use of v1 with v1 storage
  DF  = e(1,1) - e(0,0)   joint (replays LVK I_local)
  DR_j = e(0,r_j) - e(0,0)  matched random storage change, j = 0..K-1 (same rho_j for b = 0 / 1)
Support of a difference (expected sign +): scenario-equal mean >= 0.25 and >= 4/6 scenario means > 0; 'opposite' symmetric; else not_stable.
Matched-random comparison of DS0: one-sided finite-sample rank p = (1 + #{j: DR_j >= DS0}) / (K + 1), on the scenario-equal mean; beyond the
random family iff p <= 0.05 (K = 19: DS0 above every draw).  Valid only for the defined random family (per-head direction, norm matched).
Ratio rho = DS0 / DF only when DF >= 0.5; otherwise not classified.
Primary label P (first match): opposite; beyond_random_substantial (supported, p <= 0.05, rho >= 0.5); beyond_random_partial (supported,
p <= 0.05, rho < 0.5); beyond_random_unscaled (supported, p <= 0.05, DF < 0.5); not_beyond_random (supported, p > 0.05); not_supported.
Reading R (frozen map, first match): P substantial -> storage_main; P partial / unscaled -> storage_partial; P not_beyond_random ->
generic_not_excluded; P opposite -> storage_opposite; DO0 supported and DO0 / DF >= 0.5 (DF >= 0.5) -> output_main; DS1 supported ->
storage_needs_output; DF supported -> joint_effective_singles_uncertain; else weak.  Two single conditions failing never yields 'jointly
required'.  Multi-direction: >= 2 of 3 gap directions.  C1343 diagnostic only.
Y (natural, all 48): support = net >= 2 and >= 2 scenarios with an expected-direction change; reported for the S-only natural contrasts
Y(1,1,b) - Y(1,0,b) and Y(0,1,b) - Y(0,0,b), never used for P."""
TH = {'abs': 0.25, 'scen': 4, 'y_net': 2, 'y_scen': 2, 'den': 0.5, 'ratio': 0.5, 'alpha': 0.05}
K_DRAWS = 19
MAIN = ('000', '001', '100', '101', '010', '011', '110', '111')
DIFFS = {'DS0': (('01', +1), ('00', -1)), 'DS1': (('11', +1), ('10', -1)), 'DO0': (('10', +1), ('00', -1)),
         'DO1': (('11', +1), ('01', -1)), 'DF': (('11', +1), ('00', -1))}


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def smeans(vals, scen):
    out = {}
    for i, v in vals.items():
        out.setdefault(scen[i], []).append(v)
    return {s: sum(x) / len(x) for s, x in sorted(out.items())}


def seq(vals, scen):
    return mean(smeans(vals, scen).values())


def stable(vals, scen):
    sm = smeans(vals, scen)
    eq = mean(sm.values())
    npos = sum(1 for v in sm.values() if v > 0)
    nneg = sum(1 for v in sm.values() if v < 0)
    lab = 'expected' if (eq >= TH['abs'] and npos >= TH['scen']) else ('opposite' if (-eq >= TH['abs'] and nneg >= TH['scen']) else 'not_stable')
    return {'eq': eq, 'scen': sm, 'label': lab, 'n_pos': npos, 'n_neg': nneg}


def keffect(M, ca, ids):
    """e(c, a) per input; M[cell][i] with cell = c + a + b."""
    return {i: M[ca + '1'][i] - M[ca + '0'][i] for i in ids}


def rank_p(obs, draws):
    """One-sided finite-sample rank p of obs among K draws (ties count against obs)."""
    return (1 + sum(1 for x in draws if x >= obs)) / (len(draws) + 1)


def ysupport(Y0, Y1, scen):
    net = sum(Y1[i] - Y0[i] for i in Y0)
    moved = {scen[i] for i in Y0 if Y1[i] - Y0[i] > 0}
    return {'net': net, 'toward': sum(1 for i in Y0 if Y1[i] > Y0[i]), 'away': sum(1 for i in Y0 if Y1[i] < Y0[i]), 'n_scen': len(moved),
            'support': net >= TH['y_net'] and len(moved) >= TH['y_scen']}


def direction(M, MR, Y, scen, tnf):
    """M[cell][i] for the 8 main cells; MR[j][b][i] for random draws (c = 0, a = r_j); Y[cell][i] natural full-correct for the 8 main cells."""
    ids = sorted(tnf)
    e = {ca: keffect(M, ca, ids) for ca in ('00', '01', '10', '11')}
    eR = [{i: MR[j]['1'][i] - MR[j]['0'][i] for i in ids} for j in range(len(MR))]
    diffs = {name: stable({i: sum(s * e[ca][i] for ca, s in terms) for i in ids}, scen) for name, terms in DIFFS.items()}
    draws = [seq({i: eR[j][i] - e['00'][i] for i in ids}, scen) for j in range(len(MR))]
    ds0, df = diffs['DS0']['eq'], diffs['DF']['eq']
    p = rank_p(ds0, draws) if draws else None
    beyond = p is not None and p <= TH['alpha']
    rho = ds0 / df if df >= TH['den'] else None
    sup = diffs['DS0']['label']
    if sup == 'opposite':
        P = 'opposite'
    elif sup == 'expected' and beyond:
        P = 'beyond_random_unscaled' if rho is None else ('beyond_random_substantial' if rho >= TH['ratio'] else 'beyond_random_partial')
    elif sup == 'expected':
        P = 'not_beyond_random'
    else:
        P = 'not_supported'
    rO = diffs['DO0']['eq'] / df if df >= TH['den'] else None
    if P == 'beyond_random_substantial':
        R = 'storage_main'
    elif P in ('beyond_random_partial', 'beyond_random_unscaled'):
        R = 'storage_partial'
    elif P == 'not_beyond_random':
        R = 'generic_not_excluded'
    elif P == 'opposite':
        R = 'storage_opposite'
    elif diffs['DO0']['label'] == 'expected' and rO is not None and rO >= TH['ratio']:
        R = 'output_main'
    elif diffs['DS1']['label'] == 'expected':
        R = 'storage_needs_output'
    elif diffs['DF']['label'] == 'expected':
        R = 'joint_effective_singles_uncertain'
    else:
        R = 'weak'
    # random-family scenario-level description for DS0
    sm_obs = diffs['DS0']['scen']
    sm_draws = [smeans({i: eR[j][i] - e['00'][i] for i in ids}, scen) for j in range(len(MR))]
    scen_above_all = sum(1 for s in sm_obs if all(sm_obs[s] > d[s] for d in sm_draws)) if sm_draws else None
    # main effects of the storage change without the k operation (b = 0) and with it (b = 1)
    main_eff = {f'S{c}_b{b}': seq({i: M[f'{c}1{b}'][i] - M[f'{c}0{b}'][i] for i in ids}, scen) for c in '01' for b in '01'}
    main_eff.update({f'R_b{b}_draws': [seq({i: MR[j][b][i] - M[f'00{b}'][i] for i in ids}, scen) for j in range(len(MR))] for b in '01'})
    ys = {}
    if Y is not None:
        for c in '01':
            for b in '01':
                ys[f'S{c}_b{b}'] = ysupport(Y[f'{c}0{b}'], Y[f'{c}1{b}'], scen)
        allid = list(Y['000'])
        ys['JS_c1'] = sum((Y['111'][i] - Y['101'][i]) - (Y['110'][i] - Y['100'][i]) for i in allid)
        ys['totals'] = {c: sum(Y[c].values()) for c in MAIN}
    return {'e': {ca: seq(e[ca], scen) for ca in e}, 'diffs': diffs, 'random_DS0_draws': draws, 'p_rank': p, 'beyond_random': beyond,
            'rho_DS0_DF': rho, 'rho_DO0_DF': rO, 'P': P, 'R': R, 'scen_above_all_draws': scen_above_all, 'main_effects': main_eff, 'Y': ys}


def summary(per_dir, gap):
    n = sum(1 for d in gap if per_dir[d]['P'] == 'beyond_random_substantial')
    return {'n_storage_main': n, 'multi_direction_storage_main': n >= 2, 'R_by_direction': {d: per_dir[d]['R'] for d in per_dir}}
