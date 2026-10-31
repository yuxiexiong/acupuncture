"""CFM-CROSS-CHANNEL v1 readouts (CONTRACT.zh-CN.md section 5). Pure Python except `geometry` (reads torch tensors).
Every cut is a declared reporting convention or a description; nothing here is a significance test.

python xchan_analysis.py run RUN_DIR --out ANALYSIS_DIR
python xchan_analysis.py geometry RUN_DIR --out ANALYSIS_DIR
python xchan_analysis.py selftest
"""
import argparse
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
STOP = (248044, 248046)
D_SCALE, TV_SCALE = 1.0, 0.05                 # declared reporting scales (plan v2 section 5.1), not significance
WEAK, PARTIAL, NEAR_HI, CONTRA = 0.3, 0.7, 1.3, 0.5
MAIN = '-1'


def band(x):
    if x is None:
        return None
    if x < 0:
        return 'reverse'
    if x <= WEAK:
        return 'weak'
    if x < PARTIAL:
        return 'partial'
    if x <= NEAR_HI:
        return 'near'
    return 'overshoot'


def cells_from_record(rec):
    out = {}
    for k, s in rec['scores'].items():
        out[k] = {'D': s['stop_advantage'], 'r': s['final_norm']['r'], 'tl': s['token_logits'], 'H': s['entropy'],
                  'H_fix': s['entropy_fix_scale'], 'eta': s['eta'], 'EOS': int(bool(s['first_step_eos'])),
                  'token': s['token'], 'stop_winner': s['stop_winner'], 'nonstop_winner': s['nonstop_winner'],
                  'tv': s['tv_vs_C']}
    return out


def frozen_diffs(cell, nonstop, stop=STOP):
    tl = cell['tl']
    return {f'{s}-{c}': tl[str(s)] - tl[str(c)] for s in stop for c in nonstop if str(c) in tl}


def effect(cells, a, b, nonstop, stop=STOP):
    """Paired D effect a - b with numeric bound, fixed-scale value and frozen-token contradictions."""
    ca, cb, rc = cells[a], cells[b], cells['C']['r']
    e = ca['D'] - cb['D']
    bound = 2 * (ca['eta'] + cb['eta'])
    fa, fb = frozen_diffs(ca, nonstop, stop), frozen_diffs(cb, nonstop, stop)
    ft = {k: fa[k] - fb[k] for k in fa if k in fb}
    contra = [k for k, v in ft.items() if e != 0 and (v > 0) != (e > 0) and abs(v) >= CONTRA * abs(e)]
    return {'pair': [a, b], 'D': e, 'D_fix': ca['D'] * ca['r'] / rc - cb['D'] * cb['r'] / rc, 'bound': bound,
            'within_bound': abs(e) <= bound, 'frozen': ft, 'frozen_contradicting_D': contra}


def status(eff, tv, winner_changed):
    """Plan v2 section 5.1: reporting scale, other output change, or not detected (all on declared scales)."""
    if abs(eff['D']) >= D_SCALE and not eff['within_bound']:
        return 'reaches_D_scale'
    if tv >= TV_SCALE or winner_changed:
        return 'other_output_change'
    return 'not_detected'


def needle_fact(cells, x, mech, nonstop, stop=STOP):
    """Readout of one needle on one input."""
    C = cells['C']
    out = {}
    for tag, key in (('native', f'P|{x}'), ('deep', f'Y|{x}')):
        e = effect(cells, key, 'C', nonstop, stop)
        changed = cells[key]['token'] != C['token']
        out[tag] = {**e, 'tv': cells[key]['tv'], 'EOS': cells[key]['EOS'], 'winner_changed': changed,
                    'status': status(e, cells[key]['tv'], changed)}
    if x in mech:
        out['add'] = effect(cells, f'Y_CT|{x}', 'C', nonstop, stop)
        out['remove'] = effect(cells, f'Y|{x}', f'Y_TC|{x}', nonstop, stop)
        out['null'] = [effect(cells, f'Y|{x}', f'Y_TR{k}|{x}', nonstop, stop) for k in (0, 1)]
    return out


def relation(d_deep, e_add, e_remove, e_null, deep_reaches):
    """Ratios (NA below the reporting scale) and the carried N4146 prediction of plan v2 section 5.2."""
    if not deep_reaches:
        return {'ratios': None, 'label': 'NA_deep_below_scale'}
    r_add, r_rem = e_add / d_deep, e_remove / d_deep
    r_null = [n / d_deep for n in e_null]
    exceeds = e_remove > max(e_null) if d_deep > 0 else e_remove < min(e_null)
    b_add = band(r_add)
    if b_add in ('weak', 'reverse'):
        label = 'add_not_transferred'
    elif not exceeds:
        label = 'remove_not_above_own_TR'
    elif b_add == 'near' and 0 < r_rem < r_add:
        label = 'consistent'
    else:
        label = 'partial_or_other'
    return {'ratios': {'r_add': r_add, 'r_remove': r_rem, 'r_null': r_null,
                       'bands': {'add': b_add, 'remove': band(r_rem), 'null': [band(v) for v in r_null]}},
            'remove_exceeds_both_TR': exceeds, 'label': label}


def mean2(a, b):
    return (a + b) / 2


def scenario_readout(facts, x, mech):
    """facts: {0: needle_fact, 1: needle_fact}. Scenario mean; reaching the scale needs both facts' bounds exceeded."""
    f0, f1 = facts[0], facts[1]
    out = {'per_fact': {'0': f0, '1': f1}}
    for tag in ('native', 'deep'):
        d = mean2(f0[tag]['D'], f1[tag]['D'])
        reaches = abs(d) >= D_SCALE and not (f0[tag]['within_bound'] or f1[tag]['within_bound'])
        out[tag] = {'D': d, 'D_fix': mean2(f0[tag]['D_fix'], f1[tag]['D_fix']), 'tv': mean2(f0[tag]['tv'], f1[tag]['tv']),
                    'EOS': f0[tag]['EOS'] + f1[tag]['EOS'], 'reaches_D_scale': reaches,
                    'fact_status': [f0[tag]['status'], f1[tag]['status']],
                    'facts_disagree': f0[tag]['status'] != f1[tag]['status']}
    if x in mech:
        e_add = mean2(f0['add']['D'], f1['add']['D'])
        e_rem = mean2(f0['remove']['D'], f1['remove']['D'])
        e_null = [mean2(f0['null'][k]['D'], f1['null'][k]['D']) for k in (0, 1)]
        rel = relation(out['deep']['D'], e_add, e_rem, e_null, out['deep']['reaches_D_scale'])
        per = [relation(f[ 'deep']['D'], f['add']['D'], f['remove']['D'], [n['D'] for n in f['null']],
                        f['deep']['status'] == 'reaches_D_scale')['label'] for f in (f0, f1)]
        contra = sorted(set(f0['add']['frozen_contradicting_D']) | set(f1['add']['frozen_contradicting_D'])
                        | set(f0['remove']['frozen_contradicting_D']) | set(f1['remove']['frozen_contradicting_D']))
        out['relation'] = {**rel, 'E_add': e_add, 'E_remove': e_rem, 'E_null': e_null, 'fact_labels': per,
                           'facts_disagree': per[0] != per[1], 'frozen_contradictions': contra}
    return out


def needle_summary(rows, x):
    """Across scenarios: majority rule of plan v2 section 5.2 among scenarios whose deep effect reaches the scale."""
    labs = [r[x]['relation']['label'] for r in rows.values() if 'relation' in r[x]]
    reach = [l for l in labs if l != 'NA_deep_below_scale']
    n = len(reach)
    neg = sum(l in ('add_not_transferred', 'remove_not_above_own_TR') for l in reach)
    pos = sum(l == 'consistent' for l in reach)
    contra_sc = sum(bool(r[x]['relation']['frozen_contradictions']) for r in rows.values() if 'relation' in r[x])
    if n == 0:
        verdict = 'not_testable_deep_below_scale'
    elif neg * 2 > n:
        verdict = 'relation_not_transferred'
    elif pos * 2 > n:
        verdict = 'consistent_with_carried_prediction'
    else:
        verdict = 'uncertain'
    return {'scenarios_reaching_scale': n, 'consistent': pos, 'negative': neg, 'labels': labs,
            'scenarios_with_frozen_contradiction': contra_sc, 'verdict': verdict}


def ranks(rows, natives, randoms, tag):
    """Rank (1 = largest |D|) of each native channel among itself and the random directions, per scenario.
    Under exchangeability the rank is uniform on 1..len(randoms)+1."""
    hist, per = {}, {}
    for b, r in rows.items():
        rv = [abs(r[q][tag]['D']) for q in randoms]
        for x in natives:
            v = abs(r[x][tag]['D'])
            rank = 1 + sum(u > v for u in rv)
            per.setdefault(x, {})[b] = rank
            hist[rank] = hist.get(rank, 0) + 1
    m = len(randoms) + 1
    total = sum(hist.values())
    return {'histogram': {str(k): hist.get(k, 0) for k in range(1, m + 1)}, 'per_channel': per,
            'exchangeable_expected_each': total / m if total else None, 'n': total}


def summarize(table, nonstop, needle_ids, mech, natives_main, randoms, stop=STOP):
    rows = {}
    for b, facts in sorted(table.items()):
        rows[b] = {}
        for x in needle_ids:
            nf = {t: needle_fact(facts[t], x, mech, nonstop[b][t], stop) for t in (0, 1)}
            rows[b][x] = scenario_readout(nf, x, mech)
    summ = {x: needle_summary(rows, x) for x in mech}
    reach = {x: sum(rows[b][x]['deep']['reaches_D_scale'] for b in rows) for x in needle_ids}
    reach_native = {x: sum(rows[b][x]['native']['reaches_D_scale'] for b in rows) for x in needle_ids}
    return {'rows': rows, 'mechanism_summary': summ, 'deep_reaches_scale_scenarios': reach,
            'native_reaches_scale_scenarios': reach_native,
            'rank_vs_random': {t: ranks(rows, natives_main, randoms, t) for t in ('deep', 'native')},
            'scales': {'D': D_SCALE, 'TV': TV_SCALE, 'note': 'declared reporting scales, not significance'}}


def load_run(run_dir):
    sys.path.insert(0, str(HERE.parent / 'early-input-control-v1-2026-10-29'))
    import experiment as ex
    run_dir = Path(run_dir)
    v = ex.read(run_dir / 'verification.json')
    assert v['status'] == 'passed' and v['stage'] == 'formal'
    recs = []
    for w in sorted(p for p in run_dir.glob('worker-*') if p.is_dir()):
        rcp = ex.read(w / 'receipt.json')
        for p in sorted((w / 'records').glob('*.json')):
            assert ex.sha(p) == rcp['record_hashes'][str(p.relative_to(w))]
            recs.append((w, p, ex.read(p)))
    assert len(recs) == 12
    return ex, recs


def run(run_dir, out):
    ex, recs = load_run(run_dir)
    tok = ex.read(HERE.parent / 'cache-formation-readout-bridge-v1-2026-10-31/data/frozen-tokens-r01.json')
    table, nonstop = {}, {}
    needle_ids = [n['id'] for n in recs[0][2]['needles']]
    mech = recs[0][2]['mech']
    natives_main = [n['id'] for n in recs[0][2]['needles'] if n['kind'] == 'native' and n['dose'] == -1.0]
    randoms = [n['id'] for n in recs[0][2]['needles'] if n['kind'] == 'direction']
    for _w, _p, rec in recs:
        assert [n['id'] for n in rec['needles']] == needle_ids and rec['mech'] == mech
        b, t = rec['item']['base_id'], rec['item']['target_index']
        table.setdefault(b, {})[t] = cells_from_record(rec)
        nonstop.setdefault(b, {})[t] = tok['items'][rec['item']['id']]['nonstop']
    result = summarize(table, nonstop, needle_ids, mech, natives_main, randoms)
    result['write_audit'] = {rec['item']['id']: rec['write_audit'] for _w, _p, rec in recs}
    Path(out).mkdir(parents=True, exist_ok=True)
    ex.write(Path(out) / 'xchan-readouts-r01.json', result, immutable=True)
    return {'mechanism_verdicts': {x: s['verdict'] for x, s in result['mechanism_summary'].items()},
            'deep_reaches_scale_scenarios': result['deep_reaches_scale_scenarios'],
            'rank_vs_random_deep': result['rank_vs_random']['deep']['histogram']}


# ---------------------------------------------------------------- Delta V geometry (CPU, descriptive)

def cos(a, b):
    na, nb = float(a.norm()), float(b.norm())
    return None if na == 0 or nb == 0 else float((a * b).sum() / (na * nb))


def geometry_item(v_nat, needle_rows, layers):
    """v_nat: {'C' or needle id: {layer: [positions, vd]}}. Per-layer cosines of flattened dV = V_T(x) - V_C."""
    dv = {x: {i: (v_nat[x][i].double() - v_nat['C'][i].double()).flatten() for i in layers} for x in v_nat if x != 'C'}
    nat_main = [n['id'] for n in needle_rows if n['kind'] == 'native' and n['dose'] == -1.0]
    rnd = [n['id'] for n in needle_rows if n['kind'] == 'direction']
    groups = {'native_native': [(a, b) for k, a in enumerate(nat_main) for b in nat_main[k + 1:]],
              'native_random': [(a, b) for a in nat_main for b in rnd],
              'random_random': [(a, b) for k, a in enumerate(rnd) for b in rnd[k + 1:]]}
    out = {'groups': {}, 'sign': {}, 'dose': {}, 'norms': {x: {str(i): float(dv[x][i].norm()) for i in layers} for x in dv}}
    for gname, pairs in groups.items():
        out['groups'][gname] = {str(i): [cos(dv[a][i], dv[b][i]) for a, b in pairs] for i in layers}
        out['groups'][gname]['pairs'] = [list(p) for p in pairs]
    for n in needle_rows:
        if n['kind'] != 'native' or n['dose'] != -1.0:
            continue
        c = n['channel']
        ids = {d: f'N_L{n["layer"]:02d}_C{c}_D{d:+g}' for d in (-1.0, 1.0, -0.5)}
        if ids[1.0] in dv:
            out['sign'][str(c)] = {str(i): cos(dv[ids[1.0]][i], dv[ids[-1.0]][i]) for i in layers}
        if ids[-0.5] in dv:
            out['dose'][str(c)] = {str(i): {'cos': cos(dv[ids[-0.5]][i], dv[ids[-1.0]][i]),
                                            'norm_ratio': float(dv[ids[-0.5]][i].norm() / max(float(dv[ids[-1.0]][i].norm()), 1e-30))}
                                   for i in layers}
    return out


def _stats(vals):
    v = sorted(x for x in vals if x is not None)
    if not v:
        return None
    mid = v[len(v) // 2] if len(v) % 2 else (v[len(v) // 2 - 1] + v[len(v) // 2]) / 2
    return {'n': len(v), 'min': v[0], 'median': mid, 'max': v[-1]}


def geometry(run_dir, out):
    import torch
    ex, recs = load_run(run_dir)
    per_item, pooled = {}, {}
    for w, _p, rec in recs:
        rcp = ex.read(w / 'receipt.json')
        tpath = w / f'tensors/{rec["unit"]["key"]}.pt'
        assert ex.sha(tpath) == rcp['tensor_hashes'][str(tpath.relative_to(w))]
        t = torch.load(tpath, map_location='cpu', weights_only=False)
        g = geometry_item(t['v_natural'], rec['needles'], rec['G'])
        per_item[rec['item']['id']] = g
        for gname, d in g['groups'].items():
            for layer, vals in d.items():
                if layer != 'pairs':
                    pooled.setdefault(gname, {}).setdefault(layer, []).extend(vals)
        del t
    summary = {gname: {layer: _stats(vals) for layer, vals in d.items()} for gname, d in pooled.items()}
    for kind in ('sign', 'dose'):
        acc = {}
        for g in per_item.values():
            for c, d in g[kind].items():
                for layer, v in d.items():
                    acc.setdefault(layer, []).append(v if kind == 'sign' else v['cos'])
        summary[f'{kind}_cos'] = {layer: _stats(v) for layer, v in acc.items()}
    result = {'per_item': per_item, 'pooled_summary': summary,
              'note': 'descriptive; random_random is the direction-agnostic reference, not a null distribution'}
    Path(out).mkdir(parents=True, exist_ok=True)
    ex.write(Path(out) / 'xchan-geometry-r01.json', result, immutable=True)
    return {g: {l: (s['median'] if s else None) for l, s in d.items()} for g, d in summary.items()}


# ---------------------------------------------------------------- selftest

def _cell(D, tv=0.0, token=7, eta=0.01, r=1.0):
    return {'D': D, 'r': r, 'tl': {'248044': D, '248046': D - 1.0, '7': 0.0}, 'H': 1.0, 'H_fix': 1.0, 'eta': eta,
            'EOS': int(D > 0), 'token': token, 'stop_winner': 248044, 'nonstop_winner': 7, 'tv': tv}


def _cells(x, deep=10.0, add=1.0, rem=0.6, null=(0.1, 0.1), native=None, C=-12.0, tv=0.0, token=7):
    """Score cells for one needle with chosen ratios to the deep effect."""
    Y = C + deep
    return {'C': _cell(C), f'P|{x}': _cell(C + (deep if native is None else native), tv, token), f'Y|{x}': _cell(Y, tv, token),
            f'Y_CT|{x}': _cell(C + add * deep), f'Y_TC|{x}': _cell(Y - rem * deep),
            f'Y_TR0|{x}': _cell(Y - null[0] * deep), f'Y_TR1|{x}': _cell(Y - null[1] * deep)}


def _scen(x, **kw):
    nf = {t: needle_fact(_cells(x, **kw), x, [x], [7]) for t in (0, 1)}
    return scenario_readout(nf, x, [x])


def selftest():
    x = 'n'
    assert [band(v) for v in (-0.1, 0.0, 0.3, 0.5, 0.7, 1.3, 1.4)] == ['reverse', 'weak', 'weak', 'partial', 'near', 'near', 'overshoot']
    # status: each of the three can occur and not occur
    assert _scen(x)['deep']['fact_status'] == ['reaches_D_scale'] * 2
    assert _scen(x, deep=0.5, tv=0.2)['deep']['fact_status'] == ['other_output_change'] * 2
    assert _scen(x, deep=0.5, token=9)['deep']['fact_status'] == ['other_output_change'] * 2
    assert _scen(x, deep=0.5)['deep']['fact_status'] == ['not_detected'] * 2
    # numeric bound blocks the scale
    nf = needle_fact({**_cells(x), f'Y|{x}': _cell(-11.0 + 0.0, eta=1.0)}, x, [x], [7])
    assert nf['deep']['within_bound'] and nf['deep']['status'] != 'reaches_D_scale'
    # carried prediction: consistent, and each negative branch, and NA below the scale
    assert _scen(x, add=1.0, rem=0.6)['relation']['label'] == 'consistent'
    assert _scen(x, add=0.2)['relation']['label'] == 'add_not_transferred'
    assert _scen(x, add=-0.5)['relation']['label'] == 'add_not_transferred'
    assert _scen(x, add=1.0, rem=0.1, null=(0.3, 0.05))['relation']['label'] == 'remove_not_above_own_TR'
    assert _scen(x, add=0.5, rem=0.4)['relation']['label'] == 'partial_or_other'
    s = _scen(x, deep=0.5)['relation']
    assert s['label'] == 'NA_deep_below_scale' and s['ratios'] is None
    assert _scen(x)['relation']['remove_exceeds_both_TR'] is True
    # negative deep effect: direction-aware comparison with the TR draws
    s = _scen(x, deep=-10.0, add=1.0, rem=0.6, null=(0.1, 0.1))['relation']
    assert s['label'] == 'consistent' and s['remove_exceeds_both_TR'] is True
    # frozen-token contradiction both ways
    assert _scen(x)['relation']['frozen_contradictions'] == []
    c = _cells(x)
    c[f'Y_CT|{x}']['tl']['7'] = 100.0          # stop-7 falls although D(add) rises
    nf = {t: needle_fact(c, x, [x], [7]) for t in (0, 1)}
    assert scenario_readout(nf, x, [x])['relation']['frozen_contradictions']
    # majority summary both ways
    rows = {f'b{k}': {x: _scen(x)} for k in range(6)}
    assert needle_summary(rows, x)['verdict'] == 'consistent_with_carried_prediction'
    rows = {f'b{k}': {x: _scen(x, add=0.1 if k < 4 else 1.0)} for k in range(6)}
    assert needle_summary(rows, x)['verdict'] == 'relation_not_transferred'
    rows = {f'b{k}': {x: _scen(x, add=[0.1, 1.0, 0.5][k % 3])} for k in range(6)}
    assert needle_summary(rows, x)['verdict'] == 'uncertain'
    rows = {f'b{k}': {x: _scen(x, deep=0.3)} for k in range(6)}
    assert needle_summary(rows, x)['verdict'] == 'not_testable_deep_below_scale'
    # ranks: native above all randoms -> rank 1; below all -> rank 5
    row = {'a': {'deep': {'D': 9.0}}, 'r0': {'deep': {'D': 1.0}}, 'r1': {'deep': {'D': -2.0}}, 'r2': {'deep': {'D': 3.0}},
           'r3': {'deep': {'D': 0.5}}, 'z': {'deep': {'D': 0.1}}}
    rk = ranks({'b': row}, ['a', 'z'], ['r0', 'r1', 'r2', 'r3'], 'deep')
    assert rk['per_channel']['a']['b'] == 1 and rk['per_channel']['z']['b'] == 5 and rk['exchangeable_expected_each'] == 0.4
    return {'status': 'passed'}


def selftest_geometry():
    """Identical dV -> cos 1; orthogonal dV -> cos 0; opposite -> -1 (both outcomes of the descriptive readout occur)."""
    import torch
    layers = (5,)
    base = torch.zeros(3, 4)
    e = torch.eye(4)[:3]
    v = {'C': {5: base}, 'N_L00_C1_D-1': {5: e}, 'N_L00_C2_D-1': {5: e.clone()}, 'N_L00_C1_D+1': {5: -e},
         'N_L00_C1_D-0.5': {5: 0.5 * e}, 'R0_L00_D-1': {5: e.roll(1, dims=1)}}
    rows = [{'id': 'N_L00_C1_D-1', 'kind': 'native', 'layer': 0, 'channel': 1, 'dose': -1.0},
            {'id': 'N_L00_C2_D-1', 'kind': 'native', 'layer': 0, 'channel': 2, 'dose': -1.0},
            {'id': 'N_L00_C1_D+1', 'kind': 'native', 'layer': 0, 'channel': 1, 'dose': 1.0},
            {'id': 'N_L00_C1_D-0.5', 'kind': 'native', 'layer': 0, 'channel': 1, 'dose': -0.5},
            {'id': 'R0_L00_D-1', 'kind': 'direction', 'layer': 0, 'dose': -1.0}]
    g = geometry_item(v, rows, layers)
    assert abs(g['groups']['native_native']['5'][0] - 1.0) < 1e-12
    assert abs(g['groups']['native_random']['5'][0]) < 1e-12
    assert abs(g['sign']['1']['5'] + 1.0) < 1e-12
    assert abs(g['dose']['1']['5']['cos'] - 1.0) < 1e-12 and abs(g['dose']['1']['5']['norm_ratio'] - 0.5) < 1e-12
    return {'status': 'passed'}


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    for name in ('run', 'geometry'):
        q = sub.add_parser(name)
        q.add_argument('run')
        q.add_argument('--out', required=True)
    sub.add_parser('selftest')
    a = p.parse_args()
    if a.cmd == 'run':
        value = run(a.run, a.out)
    elif a.cmd == 'geometry':
        value = geometry(a.run, a.out)
    else:
        value = {'selftest': selftest(), 'geometry': selftest_geometry()}
    print(json.dumps(value, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
