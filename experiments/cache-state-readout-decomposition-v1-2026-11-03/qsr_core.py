"""QSR-01 frozen read-outs (plan §5; CONTRACT §5).  Screening rules, not significance tests.
Example = (input, pair, step, direction).  Example share s_j = median over resolvable layer-heads (j in S, q, a, I); example valid when
coverage (resolvable fraction of 14 x 32 layer-heads) >= 0.90.  Comparison (pair, step, direction) judgeable when every one of the six
scenarios has >= 80% valid examples.  Scenario mean over valid examples, then scenario-equal mean.
Single-component label j in {S, q, a}: eq_j >= 0.60; eq_j - eq_k >= 0.15 for both other k in {S, q, a}; in >= 4/6 scenarios j has the
highest scenario mean among {S, q, a} and it is > 0; scenario-equal mean of example median |s_I| <= 0.25.  Otherwise 'mixed'.
Candidate card (gap directions N4146, N1210, R0, step t2): the same j labelled on Rk-V and Ak-F in all three directions, and on the
target-not-first subset the scenario means of dM = M(Rk)-M(V) are > 0 in >= 4/6 scenarios and of dM = M(Ak)-M(F) are < 0 in >= 4/6."""
TH = {'coverage': 0.90, 'scen_valid': 0.80, 'n_scen': 6, 'share': 0.60, 'margin': 0.15, 'scen_win': 4, 'abs_I': 0.25, 'dM_scen': 4}
COMPS = ('S', 'q', 'a')


def smeans(vals, scen):
    out = {}
    for i, v in vals.items():
        if v is None:
            continue
        out.setdefault(scen[i], []).append(v)
    return {s: sum(x) / len(x) for s, x in out.items()}


def judgeable(cov, scen):
    """cov: {input: coverage}.  Returns (ok, {scenario: valid fraction}, valid set)."""
    tot, val = {}, {}
    valid = {i for i, c in cov.items() if c is not None and c >= TH['coverage']}
    for i in cov:
        tot[scen[i]] = tot.get(scen[i], 0) + 1
        val[scen[i]] = val.get(scen[i], 0) + (i in valid)
    frac = {s: val[s] / tot[s] for s in tot}
    ok = len(frac) == TH['n_scen'] and all(f >= TH['scen_valid'] for f in frac.values())
    return ok, frac, valid


def label(ex, scen):
    """ex: {input: {'coverage', 'sS', 'sq', 'sa', 'sI', 'absI'}} (example medians; None when nothing resolvable)."""
    ok, frac, valid = judgeable({i: e['coverage'] for i, e in ex.items()}, scen)
    out = {'judgeable': ok, 'scen_valid_frac': frac, 'n_valid': len(valid)}
    if not ok:
        out['label'] = 'not_judgeable'
        return out
    m = {j: smeans({i: ex[i]['s' + j] for i in valid}, scen) for j in COMPS + ('I',)}
    mabs = smeans({i: ex[i]['absI'] for i in valid}, scen)
    eq = {j: sum(m[j].values()) / len(m[j]) for j in COMPS + ('I',)}
    eq_abs = sum(mabs.values()) / len(mabs)
    wins = {j: sum(1 for s in m[j] if m[j][s] > 0 and all(m[j][s] > m[k][s] for k in COMPS if k != j)) for j in COMPS}
    out.update({'eq': eq, 'eq_absI': eq_abs, 'scen_wins': wins, 'scen_means': m})
    lab = 'mixed'
    for j in COMPS:
        if (eq[j] >= TH['share'] and all(eq[j] - eq[k] >= TH['margin'] for k in COMPS if k != j)
                and wins[j] >= TH['scen_win'] and eq_abs <= TH['abs_I']):
            lab = j
    out['label'] = lab
    return out


def dm_scen(dM, scen, subset):
    """Scenario means of dM over subset (inputs with a value)."""
    return smeans({i: dM[i] for i in subset if dM.get(i) is not None}, scen)


def card(labels, dms, scen, subset, gap_dirs):
    """labels[(pair, d)] = label output at t2; dms[(pair, d)] = {input: dM}.  Returns the candidate-card decision."""
    res = {'per_direction': {}, 'candidate': None}
    js = set()
    for d in gap_dirs:
        lr, la = labels[('Rk-V', d)]['label'], labels[('Ak-F', d)]['label']
        pr = dm_scen(dms[('Rk-V', d)], scen, subset)
        pa = dm_scen(dms[('Ak-F', d)], scen, subset)
        npos, nneg = sum(v > 0 for v in pr.values()), sum(v < 0 for v in pa.values())
        same = lr == la and lr in COMPS
        dm_ok = npos >= TH['dM_scen'] and nneg >= TH['dM_scen']
        res['per_direction'][d] = {'Rk-V': lr, 'Ak-F': la, 'same_component': same, 'dM_Rk_pos_scen': npos, 'dM_Ak_neg_scen': nneg, 'dM_ok': dm_ok}
        js.add(lr if (same and dm_ok) else None)
    if len(js) == 1 and None not in js:
        res['candidate'] = js.pop()
    return res
