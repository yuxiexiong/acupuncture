"""QST-01 frozen rules (plan §6, CONTRACT §4).  No directional prediction is registered (CONTRACT §4.0).

Y_full(j) = Y_delivery(text; target=j, distractors=other listed codes) AND termination == 'stop' AND NOT think_unclosed.
Primary contrast for receiver a with foreign donors b, c (fixed by id), within one arm type X:
  J = [y_b(b) - y_b(c) + y_c(c) - y_c(b)] / 2,   W = 1[donor b -> delivers b AND donor c -> delivers c],
  W_rev = 1[donor b -> delivers c AND donor c -> delivers b].
Stable direction (forward): over the 4 primary scenarios (scenario means, equal weight): >= 3 scenarios with mean J > 0, equal-weight
mean J >= 1/3 and mean W >= 1/3; the same three conditions on the 12-receiver subset whose two foreign targets are both non-first.
Reverse: J -> -J, W -> W_rev, same thresholds.
Attenuation by needle-formed donors (direction d): H_C forward-stable; H_T not reverse-stable; on all 36: >= 3 scenarios with mean
dJ > 0, equal-weight dJ >= 1/3 and dW >= 1/3; on the 12 subset: equal-weight means of dJ and dW > 0 (dJ = J(H_C) - J(H_T)).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'cache-first-token-continuation-v1-2026-11-02'))
import fc_core as FK  # noqa: E402

TH = {'positive_scenarios_min': 3, 'scenario_count': 4, 'J_mean_min': 1 / 3, 'W_mean_min': 1 / 3,
      'attenuation_delta_J_min': 1 / 3, 'attenuation_delta_W_min': 1 / 3}


def y_full(text, termination, code, listed, question=None):
    c = FK.classify(text, termination, code, [x for x in listed if x != code], question)
    return bool(c['Y_delivery'] and termination == 'stop' and not c['tags']['think_unclosed'])


def contrast(y):
    """y: {(donor, code): bool} for donors b, c (keys ('b','b'), ('b','c'), ('c','c'), ('c','b'))."""
    J = (int(y[('b', 'b')]) - int(y[('c', 'b')]) + int(y[('c', 'c')]) - int(y[('b', 'c')])) / 2
    W = int(y[('b', 'b')] and y[('c', 'c')])
    Wr = int(y[('b', 'c')] and y[('c', 'b')])
    return {'J': J, 'W': W, 'W_rev': Wr}


def scen_means(rows, key):
    """rows: list of {'scenario', key}; returns scenario -> mean."""
    out = {}
    for r in rows:
        out.setdefault(r['scenario'], []).append(r[key])
    return {s: sum(v) / len(v) for s, v in out.items()}


def eq_mean(m):
    return sum(m.values()) / len(m)


def stable(rows_all, rows_sub, reverse=False):
    sign = -1 if reverse else 1
    wk = 'W_rev' if reverse else 'W'

    def one(rows):
        rr = [dict(r, Js=sign * r['J']) for r in rows]
        mJ, mW = scen_means(rr, 'Js'), scen_means(rr, wk)
        ok = (sum(v > 0 for v in mJ.values()) >= TH['positive_scenarios_min'] and eq_mean(mJ) >= TH['J_mean_min'] and eq_mean(mW) >= TH['W_mean_min'])
        return {'ok': ok, 'J_by_scenario': mJ, 'W_by_scenario': mW, 'J_eq': eq_mean(mJ), 'W_eq': eq_mean(mW),
                'n_pos_scen': sum(v > 0 for v in mJ.values())}
    a, s = one(rows_all), one(rows_sub)
    return {'ok': a['ok'] and s['ok'], 'all': a, 'subset': s}


def attenuation(hc_all, ht_all, hc_sub, ht_sub):
    """Each argument: list of rows {'receiver', 'scenario', 'J', 'W', 'W_rev'} aligned by receiver."""
    fwd = stable(hc_all, hc_sub)
    rev_t = stable(ht_all, ht_sub, reverse=True)

    def deltas(hc, ht):
        m = {r['receiver']: r for r in ht}
        return [{'scenario': r['scenario'], 'dJ': r['J'] - m[r['receiver']]['J'], 'dW': r['W'] - m[r['receiver']]['W']} for r in hc]
    da, ds = deltas(hc_all, ht_all), deltas(hc_sub, ht_sub)
    mJ, mW = scen_means(da, 'dJ'), scen_means(da, 'dW')
    sJ, sW = scen_means(ds, 'dJ'), scen_means(ds, 'dW')
    cond2 = sum(v > 0 for v in mJ.values()) >= TH['positive_scenarios_min'] and eq_mean(mJ) >= TH['attenuation_delta_J_min'] and eq_mean(mW) >= TH['attenuation_delta_W_min']
    cond3 = eq_mean(sJ) > 0 and eq_mean(sW) > 0
    return {'ok': fwd['ok'] and not rev_t['ok'] and cond2 and cond3, 'H_C_forward': fwd['ok'], 'H_T_reverse': rev_t['ok'],
            'dJ_by_scenario': mJ, 'dW_by_scenario': mW, 'dJ_eq': eq_mean(mJ), 'dW_eq': eq_mean(mW),
            'subset_dJ_eq': eq_mean(sJ), 'subset_dW_eq': eq_mean(sW), 'cond_all': cond2, 'cond_subset': cond3}
