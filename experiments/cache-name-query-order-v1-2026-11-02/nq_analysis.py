"""NQ-01 consumer: verified formal records (CPU).  python nq_analysis.py RUN_DIR OUT_JSON"""
import hashlib
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'cache-first-token-continuation-v1-2026-11-02'))
import fc_core as FK  # noqa: E402
import nq_core as K  # noqa: E402

DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'N_L00_C1343_D-1')
T_ARMS = ('T_nat', 'T_V', 'T_F')
MAINS = ('correct', 'distractor', 'other_code', 'multi_code', 'stopped_no_code', 'budget_no_code')
POS = ('first', 'middle', 'last')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(run_dir):
    recs = {}
    for w in sorted(Path(run_dir).glob('worker-*')):
        if not w.is_dir():
            continue
        rc = json.load(open(w / 'receipt.json'))
        for rel, dg in rc['record_hashes'].items():
            assert sha(w / rel) == dg, rel
            r = json.load(open(w / rel))
            recs[r['item']['id']] = r
    return recs


def cell(rec, name):
    t = rec['trajectories'][name]
    it = rec['item']
    c = FK.classify(t['text'], t['termination'], it['target'], it['distractors'], it['question'])
    codes = list(dict.fromkeys(FK.CODE_RE.findall(c['visible'])))
    unique = codes[0] if len(codes) == 1 else None
    letter = {v[1]: k for k, v in it['binding'].items()}
    z = {letter[code]: t['diag']['watch'][str(tok)] for code, tok in rec['code_tokens'].items()}
    zt = z[it['query']]
    first_letter = it['order'][0]
    return {'delivered': c['Y_delivery'], 'strict': c['Y_strict'], 'main': c['main'], 'unique': unique, 'first_listed': it['first_listed'],
            'unique_pos': (POS[it['listed_codes'].index(unique)] if unique in it['listed_codes'] else None),
            'z': z, 'M': zt - max(v for k, v in z.items() if k != it['query']),
            'first_minus_others': z[first_letter] - max(v for k, v in z.items() if k != first_letter),
            'step1_qshared_minus_stopmax': t['first']['q_shared'] - max(t['first']['stop'].values()),
            'step1_qshared_minus_other_max': t['first']['q_shared'] - t['first']['other_max'],
            'visible': c['visible'][:60]}


def analyse(recs):
    ids = sorted(recs)
    scen = sorted({recs[i]['item']['base_id'] for i in ids})
    by = {s: [i for i in ids if recs[i]['item']['base_id'] == s] for s in scen}
    for s in scen:
        assert len(by[s]) == 9
    cells = {i: {name: cell(recs[i], name) for name in recs[i]['trajectories']} for i in ids}
    arm_cells = lambda name: {s: [cells[i][name] for i in by[s]] for s in scen}   # noqa: E731
    c_by = arm_cells('C_nat')
    capp = K.c_applicable(c_by)
    out = {'C': {'applicability': capp, 'delivered': sum(cells[i]['C_nat']['delivered'] for i in ids),
                 'strict': sum(cells[i]['C_nat']['strict'] for i in ids),
                 'scenario_category': {s: K.scenario_category(c_by[s]) for s in scen}}, 'directions': {}}
    st = {'P_pos': {}, 'P_target': {}}
    for d in DIRECTIONS:
        A = {a: arm_cells(f'{a}|{d}') for a in T_ARMS}
        dmg = K.damage_transfer(c_by, A['T_nat'])
        cats = {a: {s: K.scenario_category(A[a][s]) for s in scen} for a in T_ARMS}
        labels = {a: K.direction_label(cats[a]) for a in T_ARMS}
        st['P_pos'][d] = K.status(capp['panel_ok'], dmg['transferred'], labels['T_V'], 'follow_first')
        st['P_target'][d] = K.status(capp['panel_ok'], dmg['transferred'], labels['T_F'], 'follow_query')
        flat = {a: [c for s in scen for c in A[a][s]] for a in T_ARMS}
        cflat = [c for s in scen for c in c_by[s]]
        nonfirst = {a: [cells[i][f'{a}|{d}'] for i in ids if recs[i]['item']['target_position'] != 'first'] for a in T_ARMS}
        q = {a: {s: {o: K.q_values({recs[i]['item']['query']: cells[i][f'{a}|{d}']['z'] for i in by[s] if recs[i]['item']['order'] == o})
                     for o in ('ABC', 'BCA', 'CAB')} for s in scen} for a in ('C_nat',) + T_ARMS if a != 'C_nat'}
        out['directions'][d] = {
            'damage': dmg, 'scenario_categories': cats, 'labels': labels,
            'status': {'T_V_follow_first': st['P_pos'][d], 'T_F_follow_query': st['P_target'][d]},
            'arms': {a: {'delivered': sum(c['delivered'] for c in flat[a]), 'strict': sum(c['strict'] for c in flat[a]),
                         'main': {m: sum(c['main'] == m for c in flat[a]) for m in MAINS},
                         'unique_first_listed': sum(c['unique'] is not None and c['unique'] == c['first_listed'] for c in flat[a]),
                         'unique_pos': {p: sum(c['unique_pos'] == p for c in flat[a]) for p in POS},
                         'nonfirst_36': {'target': sum(c['delivered'] for c in nonfirst[a]),
                                         'first_listed': sum(c['unique'] == c['first_listed'] for c in nonfirst[a])},
                         'paired_improvement': (K.paired_improvement(cflat, flat['T_nat'], flat[a]) if a != 'T_nat' else None),
                         'M_mean': statistics.mean(c['M'] for c in flat[a]),
                         'M_positive': sum(c['M'] > 0 for c in flat[a]),
                         'first_minus_others_mean': statistics.mean(c['first_minus_others'] for c in flat[a]),
                         'step1_qshared_minus_stopmax_mean': statistics.mean(c['step1_qshared_minus_stopmax'] for c in flat[a])}
                     for a in T_ARMS},
            'pairing_F_vs_V': K.pairing(flat['T_F'], flat['T_V']),
            'Q': {a: {'mean': statistics.mean(v for s in scen for o in q[a][s].values() for v in o.values()),
                      'positive': sum(v > 0 for s in scen for o in q[a][s].values() for v in o.values()), 'n': 54,
                      'per_scenario_mean': {s: statistics.mean(v for o in q[a][s].values() for v in o.values()) for s in scen}} for a in T_ARMS}}
    cq = {s: {o: K.q_values({recs[i]['item']['query']: cells[i]['C_nat']['z'] for i in by[s] if recs[i]['item']['order'] == o})
              for o in ('ABC', 'BCA', 'CAB')} for s in scen}
    out['C']['Q'] = {'mean': statistics.mean(v for s in scen for o in cq[s].values() for v in o.values()),
                     'positive': sum(v > 0 for s in scen for o in cq[s].values() for v in o.values()), 'n': 54}
    out['P_pos'] = dict(K.overall(st['P_pos']), statuses=st['P_pos'])
    out['P_target'] = dict(K.overall(st['P_target']), statuses=st['P_target'])
    out['per_cell'] = cells
    return out


def main(run_dir, out_path):
    ver = json.load(open(Path(run_dir) / 'verification.json'))
    assert ver['status'] == 'passed' and ver['stage'] == 'formal'
    recs = load(run_dir)
    assert len(recs) == 54
    res = analyse(recs)
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256']}
    with open(out_path, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    brief = {'C': {k: v for k, v in res['C'].items()}, 'P_pos': res['P_pos'], 'P_target': res['P_target'],
             'directions': {d: {'damage': x['damage']['transferred'], 'labels': x['labels'], 'cats': x['scenario_categories'],
                                'arms': {a: {k: v[k] for k in ('delivered', 'strict', 'unique_first_listed', 'unique_pos', 'nonfirst_36', 'paired_improvement', 'M_positive')}
                                         for a, v in x['arms'].items()},
                                'pairing_F_vs_V': x['pairing_F_vs_V'], 'Q_mean': {a: round(v['mean'], 2) for a, v in x['Q'].items()}}
                            for d, x in res['directions'].items()}}
    print(json.dumps(brief, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
