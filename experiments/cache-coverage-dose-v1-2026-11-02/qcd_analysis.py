"""QCD-01 consumer (CPU).
python qcd_analysis.py gate RUN_DIR(gformal) OUT_JSON           -> stage G gate (blocking; analysis/g-gate-r01.json)
python qcd_analysis.py final GRUN_DIR SRUN_DIR OUT_JSON          -> full readouts"""
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'cache-name-query-order-v1-2026-11-02'))
sys.path.insert(0, str(HERE))
import nq_analysis as NQA  # noqa: E402
import qcd_core as K  # noqa: E402

DIRECTIONS = NQA.DIRECTIONS
TEMPLATES = ('NA', 'LA')
POLICIES = ('B1', 'N1', 'E1', 'N-A', 'N-Q', 'B-A', 'B-Q')


def load(run_dir, stage):
    ver = json.load(open(Path(run_dir) / 'verification.json'))
    assert ver['status'] == 'passed' and ver['stage'] == stage
    recs = NQA.load(run_dir)
    assert len(recs) == 108
    return ver, recs


def cells(recs, names):
    return {i: {n: NQA.cell(r, n) for n in names if n in r['trajectories']} for i, r in recs.items()}


def by_template(recs, t):
    return sorted(i for i in recs if recs[i]['plan_text']['template'] == t)


def gate(run_dir, out):
    ver, recs = load(run_dir, 'gformal')
    names = {f'{x}|{d}|{a}' for d in DIRECTIONS for x, arms in (('T_b', ('nat', 'V_b', 'V_s', 'F_b')), ('T_s', ('nat', 'V_s', 'V_b')), ('T_u', ('nat', 'V_b', 'F_b'))) for a in arms} | {'C_b', 'C_s'}
    cl = cells(recs, names)
    classes, detail, flips = {}, {}, {}
    for t in TEMPLATES:
        ids = by_template(recs, t)
        scen = {i: recs[i]['item']['base_id'] for i in ids}
        for d in DIRECTIONS:
            row, det = {}, {}
            for k, (lft, rgt) in K.G_COMBOS.items():
                L_ = {i: cl[i][lft.format(d=d)]['delivered'] for i in ids}
                R_ = {i: cl[i][rgt.format(d=d)]['delivered'] for i in ids}
                c, net, tot = K.stable_class(L_, R_, scen)
                row[k] = c
                det[k] = {'class': c, 'net_by_scenario': net, 'total': tot, 'left_Y': sum(L_.values()), 'right_Y': sum(R_.values()), 'paired': K.paired(L_, R_)}
            classes[(t, d)] = row
            detail[f'{t}|{d}'] = det
            for a, b, lab in ((f'T_b|{d}|V_b', f'T_b|{d}|V_s', 'T_b donor b->s'), (f'T_s|{d}|V_s', f'T_s|{d}|V_b', 'T_s donor s->b'),
                              (f'T_s|{d}|V_b', f'T_u|{d}|V_b', 'bridge T_s->T_u (donor C_b)')):
                fl = [i for i in ids if cl[i][a]['delivered'] != cl[i][b]['delivered']]
                dm = [cl[i][b]['M'] - cl[i][a]['M'] for i in ids]
                de = [cl[i][b]['step1_qshared_minus_stopmax'] - cl[i][a]['step1_qshared_minus_stopmax'] for i in ids]
                msign = [i for i in ids if (cl[i][a]['M'] > 0) != (cl[i][b]['M'] > 0)]
                flips[f'{t}|{d}|{lab}'] = {'n_flips': len(fl), 'to_right': sum(cl[i][b]['delivered'] for i in fl), 'flips': fl,
                                           'by_scenario': {s: sum(scen[i] == s for i in fl) for s in sorted(set(scen.values()))},
                                           'by_target_position': {p: sum(recs[i]['item']['target_position'] == p for i in fl) for p in ('first', 'middle', 'last')},
                                           'M_sign_changes': len(msign), 'M_sign_changes_both_abs_le_0.5': sum(abs(cl[i][a]['M']) <= 0.5 and abs(cl[i][b]['M']) <= 0.5 for i in msign),
                                           'dM_abs_max': max(abs(x) for x in dm), 'dM_abs_median': statistics.median(abs(x) for x in dm),
                                           'dE_abs_max': max(abs(x) for x in de), 'dE_abs_median': statistics.median(abs(x) for x in de)}
    g = K.gate(classes)
    res = {'status': g['status'], 'freeze_sha256': ver['freeze_sha256'], 'classes': {f'{t}|{d}': v for (t, d), v in classes.items()},
           'disagreements': g['disagreements'], 'detail': detail, 'flips': flips, 'source': str(run_dir)}
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'status': res['status'], 'classes': res['classes'],
                      'flips': {k: (v['n_flips'], v['M_sign_changes'], round(v['dM_abs_max'], 2)) for k, v in flips.items()}}, ensure_ascii=False, indent=1))


def final(g_dir, s_dir, out):
    gv, grecs = load(g_dir, 'gformal')
    sv, srecs = load(s_dir, 'sformal')
    assert gv['freeze_sha256'] == sv['freeze_sha256']
    recs = {}
    for i in grecs:
        r = dict(grecs[i])
        r['trajectories'] = {**grecs[i]['trajectories'], **srecs[i]['trajectories']}
        r['dose_audits'] = srecs[i]['dose_audits']
        r['e1_n1_steps'] = srecs[i]['e1_n1_steps']
        recs[i] = r
    names = {'C_b'} | {f.format(d=d) for d in DIRECTIONS for m in (K.ARM, K.NAT) for f in m.values()}
    cl = cells(recs, names)
    out_d = {'per_template': {}, 'comparisons': {}, 'patterns': {}, 'dose_rule': {}, 'dose_checks': {}}
    for t in TEMPLATES:
        ids = by_template(recs, t)
        scen = {i: recs[i]['item']['base_id'] for i in ids}
        sids = sorted(set(scen.values()))
        c_by = {s: [cl[i]['C_b'] for i in ids if scen[i] == s] for s in sids}
        capp = K.NK.c_applicable(c_by)
        pt = {'C': {'delivered': sum(cl[i]['C_b']['delivered'] for i in ids), 'applicability': capp}, 'policies': {}}
        dmg = {}
        for p in POLICIES:
            pt['policies'][p] = {}
            for d in DIRECTIONS:
                t_by = {s: [cl[i][K.NAT[p].format(d=d)] for i in ids if scen[i] == s] for s in sids}
                dm = K.NK.damage_transfer(c_by, t_by)
                dmg[(p, d)] = dm['transferred']
                Yv = sum(cl[i][K.ARM[p].format(d=d)]['delivered'] for i in ids)
                Yn = sum(cl[i][K.NAT[p].format(d=d)]['delivered'] for i in ids)
                nonfirst = [i for i in ids if recs[i]['item']['target_position'] != 'first']
                pt['policies'][p][d] = {'Y_V': Yv, 'Y_nat': Yn, 'R': Yv - Yn, 'damage_transferred': dm['transferred'],
                                        'nonfirst_target': sum(cl[i][K.ARM[p].format(d=d)]['delivered'] for i in nonfirst),
                                        'nonfirst_first_listed': sum(cl[i][K.ARM[p].format(d=d)]['unique'] == recs[i]['item']['first_listed'] for i in nonfirst),
                                        'M_V_mean': statistics.mean(cl[i][K.ARM[p].format(d=d)]['M'] for i in ids),
                                        'M_nat_mean': statistics.mean(cl[i][K.NAT[p].format(d=d)]['M'] for i in ids),
                                        'repaired_C_ok_nat_wrong': sum(cl[i]['C_b']['delivered'] and not cl[i][K.NAT[p].format(d=d)]['delivered'] and cl[i][K.ARM[p].format(d=d)]['delivered'] for i in ids),
                                        'A_mean': statistics.mean(recs[i]['dose_audits'][f'{K.AUDIT[p]}|{d}']['summary']['A'] for i in ids),
                                        'Q_mean': statistics.mean(recs[i]['dose_audits'][f'{K.AUDIT[p]}|{d}']['summary']['Q'] for i in ids),
                                        'P_mean': statistics.mean(recs[i]['dose_audits'][f'{K.AUDIT[p]}|{d}']['summary']['P'] for i in ids)}
        out_d['per_template'][t] = pt
        cls_all = {}
        for cname, (lp, rp, qs) in K.COMPARISONS.items():
            for d in DIRECTIONS:
                L_ = {i: cl[i][K.ARM[lp].format(d=d)]['delivered'] for i in ids}
                R_ = {i: cl[i][K.ARM[rp].format(d=d)]['delivered'] for i in ids}
                c, net, tot = K.stable_class(L_, R_, scen)
                appl = capp['panel_ok'] and dmg[(lp, d)] and dmg[(rp, d)]
                dose = None
                if qs:
                    ls = {i: recs[i]['dose_audits'][f'{K.AUDIT[lp]}|{d}']['summary'] for i in ids}
                    rs = {i: recs[i]['dose_audits'][f'{K.AUDIT[rp]}|{d}']['summary'] for i in ids}
                    dose = K.dose_ok(ls, rs, qs)
                    pdiff = [abs(ls[i]['P'] - rs[i]['P']) / max(ls[i]['P'], rs[i]['P']) for i in ids]
                    dose['P_max_rel_diff_report_only'] = max(pdiff)
                status = c if (appl and (dose is None or dose['ok'])) else ('not_applicable' if not appl else 'dose_unmatched')
                cls_all[(cname, d)] = status
                out_d['comparisons'][f'{t}|{cname}|{d}'] = {'class': c, 'status': status, 'net_by_scenario': net, 'total': tot,
                                                            'left_Y_V': sum(L_.values()), 'right_Y_V': sum(R_.values()), 'paired': K.paired(L_, R_),
                                                            'applicable': appl, 'dose': dose,
                                                            'left_Y_nat': pt['policies'][lp][d]['Y_nat'], 'right_Y_nat': pt['policies'][rp][d]['Y_nat'],
                                                            'delta_R': pt['policies'][rp][d]['R'] - pt['policies'][lp][d]['R']}
        for cname in K.COMPARISONS:
            out_d['patterns'][f'{t}|{cname}'] = K.cross_direction({d: cls_all[(cname, d)] for d in DIRECTIONS})
        for d in DIRECTIONS:
            Y = {p: pt['policies'][p][d]['Y_V'] for p in POLICIES}
            ref = cls_all[('B1|N1', d)] in ('right_better', 'left_better')
            out_d['dose_rule'][f'{t}|{d}'] = K.dose_preferred(Y, {c: cls_all[(c, d)] for c in K.COMPARISONS}, ref)
        out_d['e1_n1_steps'] = {f'{t}|{d}': {'max': max(recs[i]['e1_n1_steps'][d]['max_rel_step_diff'] for i in ids),
                                             'mean': statistics.mean(recs[i]['e1_n1_steps'][d]['mean_rel_step_diff'] for i in ids)} for d in DIRECTIONS}
    out_d['source'] = {'g': str(g_dir), 's': str(s_dir), 'freeze_sha256': sv['freeze_sha256']}
    with open(out, 'x') as f:
        f.write(json.dumps(out_d, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'patterns': out_d['patterns'], 'dose_rule': out_d['dose_rule'],
                      'status': {k: v['status'] for k, v in out_d['comparisons'].items()}}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    if sys.argv[1] == 'gate':
        gate(sys.argv[2], sys.argv[3])
    else:
        final(sys.argv[2], sys.argv[3], sys.argv[4])
