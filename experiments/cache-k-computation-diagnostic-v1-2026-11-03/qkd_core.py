"""QKD-01 frozen readouts (plan §5-6).  Per example (input x pair x step x route): median over resolvable layer-heads and both
recipients of the J / H projection shares.  'Local H dominant' (descriptive label, no significance): scenario-equal mean of the
example medians of sH >= 0.75 and >= 4 of 6 scenarios with mean sH > mean sJ; 'local J dominant' symmetric; else 'neither'.
Primary step: C route t2 (the forced-prefix competition step); t1 and t3 and the N route are reported alongside."""
TH = {'share': 0.75, 'scen': 4}


def smeans(vals, scen):
    out = {}
    for i, v in vals.items():
        if v is None:
            continue
        out.setdefault(scen[i], []).append(v)
    return {s: sum(x) / len(x) for s, x in out.items()}


def label(sJ, sH, scen):
    """sJ, sH: {input: example median} (None = not resolvable)."""
    mJ, mH = smeans(sJ, scen), smeans(sH, scen)
    common = sorted(set(mJ) & set(mH))
    if not common:
        return {'label': 'not_resolvable', 'n_scen': 0}
    eqJ = sum(mJ[s] for s in common) / len(common)
    eqH = sum(mH[s] for s in common) / len(common)
    nH = sum(mH[s] > mJ[s] for s in common)
    nJ = sum(mJ[s] > mH[s] for s in common)
    if eqH >= TH['share'] and nH >= TH['scen']:
        lab = 'H_dominant'
    elif eqJ >= TH['share'] and nJ >= TH['scen']:
        lab = 'J_dominant'
    else:
        lab = 'neither'
    return {'label': lab, 'eq_sJ': eqJ, 'eq_sH': eqH, 'n_scen_H_gt_J': nH, 'n_scen_J_gt_H': nJ, 'n_scen': len(common)}


def err_threshold(e_pre):
    """Formal decomposition-error threshold frozen from the preflight maximum e: min(0.02, max(1e-5, 2e))."""
    return min(0.02, max(1e-5, 2 * e_pre))
