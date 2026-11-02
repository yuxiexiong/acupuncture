"""QSR-01 consumer (CPU).  python qsr_analysis.py PRE_DIR RUN_DIR OUT_JSON"""
import hashlib
import json
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'cache-query-state-transfer-v1-2026-11-02'))
import qsr_core as K  # noqa: E402
import qst_core as QK  # noqa: E402

DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'N_L00_C1343_D-1')
GAP = DIRECTIONS[:3]
PAIRS = (('V', 'F'), ('Rk', 'V'), ('Ak', 'F'), ('Rrk', 'V'), ('Ark', 'F'))
ARMS = ('V', 'F', 'Rk', 'Ak', 'Rrk', 'Ark')
QKF_NAME = {'V': 'V', 'F': 'F', 'Rk': 'R_mu_k', 'Ak': 'A_mu_k', 'Rrk': 'R_post_k', 'Ark': 'A_post_k'}
QKD_FORMAL = HERE.parent / 'cache-k-computation-diagnostic-v1-2026-11-03/runs/formal-r02'
QKF_FORMAL = HERE.parent / 'cache-qk-component-factor-v1-2026-11-02/runs/formal-r01'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(run_dir, stage):
    ver = json.load(open(Path(run_dir) / 'verification.json'))
    assert ver['status'] == 'passed' and ver['stage'] == stage
    recs = {}
    for w in sorted(Path(run_dir).glob('worker-*')):
        if not w.is_dir():
            continue
        rc = json.load(open(w / 'receipt.json'))
        for rel, dg in rc['record_hashes'].items():
            assert sha(w / rel) == dg, rel
            r = json.load(open(w / rel))
            recs[r['text']] = r
    return ver, recs


def behaviour():
    """Y_full per (input, arm, direction) from the frozen QKF (old directions) and QKD (C1343) answers."""
    qkf, qkd = {}, {}
    for root, dst in ((QKF_FORMAL, qkf), (QKD_FORMAL, qkd)):
        for w in sorted(root.glob('worker-*')):
            if not w.is_dir():
                continue
            rc = json.load(open(w / 'receipt.json'))
            for rel, dg in rc['record_hashes'].items():
                assert sha(w / rel) == dg, rel
                r = json.load(open(w / rel))
                dst[r['text']] = r
    Y = {}
    for i, r in qkd.items():
        it = r['item']
        for d in DIRECTIONS:
            for a in ARMS:
                t = r['c1343_trajectories'][a] if d == DIRECTIONS[3] else qkf[i]['trajectories'][f'{QKF_NAME[a]}|{d}']
                Y[(i, a, d)] = int(QK.y_full(t['text'], t['termination'], it['target'], it['listed_codes'], it['question']))
    return Y


def examples(recs, key):
    ex = {}
    for i, r in recs.items():
        p = r['pairs'][key]
        ex[i] = {'coverage': p['coverage'], 'sS': p['median_sS'], 'sq': p['median_sq'], 'sa': p['median_sa'], 'sI': p['median_sI'], 'absI': p['median_abs_sI']}
    return ex


def analyse(pre, recs):
    scen = {i: r['scenario'] for i, r in recs.items()}
    Y = behaviour()
    tnf = {i for i, r in recs.items() if r['item']['target'] != r['item']['first_listed']}
    out = {'error': {'threshold': next(iter(recs.values()))['err_threshold'], 'formal_e_max': max(r['err_max'] for r in recs.values()),
                     'preflight_e_max': max(r['err_max'] for r in pre.values())},
           'n_target_not_first': len(tnf), 'directions': {}}
    labels, dms = {}, {}
    for d in DIRECTIONS:
        M = {a: {i: r['arms'][d][a]['M'] for i, r in recs.items()} for a in ARMS}
        dres = {'Y_totals': {a: sum(Y[(i, a, d)] for i in recs) for a in ARMS}, 'M_mean': {a: st.mean(M[a].values()) for a in ARMS},
                'n_D': sum(int(Y[(i, 'F', d)] == 1 and Y[(i, 'V', d)] == 0) for i in recs), 'pairs': {}}
        for e1, e0 in PAIRS:
            pk = f'{e1}-{e0}'
            dM = {i: M[e1][i] - M[e0][i] for i in recs}
            dms[(pk, d)] = dM
            for s_ in (1, 2):
                lab = K.label(examples(recs, f'{pk}|t{s_}|{d}'), scen)
                if s_ == 2:
                    labels[(pk, d)] = lab
                    trans = {}
                    for i in recs:
                        k_ = f'{Y[(i, e0, d)]}->{Y[(i, e1, d)]}'
                        trans[k_] = trans.get(k_, 0) + 1
                    lab['Y_transitions'] = trans
                    for nm, sub in (('all48', set(recs)), ('target_not_first', tnf), ('target_first', set(recs) - tnf)):
                        sm = K.dm_scen(dM, scen, sub)
                        lab[f'dM_{nm}'] = {'scen_means': sm, 'n_pos_scen': sum(v > 0 for v in sm.values()), 'n_neg_scen': sum(v < 0 for v in sm.values()),
                                           'mean': st.mean(dM[i] for i in sub) if sub else None}
                dres['pairs'][f'{pk}|t{s_}'] = lab
        out['directions'][d] = dres
    out['card'] = K.card(labels, dms, scen, tnf, GAP)
    out['card']['controls'] = {f'{p}|{d}': labels[(p, d)]['label'] for p in ('Rk-V', 'Ak-F', 'Rrk-V', 'Ark-F', 'V-F') for d in DIRECTIONS}
    return out


def main(pre_dir, run_dir, out_path):
    _, pre = load(pre_dir, 'preflight')
    ver, recs = load(run_dir, 'formal')
    assert len(recs) == 48
    res = analyse(pre, recs)
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256']}
    with open(out_path, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps(res['error']))
    for d, x in res['directions'].items():
        print(d, x['Y_totals'], 'n_D', x['n_D'])
        for k, v in x['pairs'].items():
            print('  ', k, v['label'], {j: round(e, 3) for j, e in v.get('eq', {}).items()}, 'absI', round(v['eq_absI'], 3) if 'eq_absI' in v else None,
                  'wins', v.get('scen_wins'), 'valid', v['n_valid'])
    print('card', json.dumps(res['card'], ensure_ascii=False))


if __name__ == '__main__':
    main(*sys.argv[1:4])
