"""QKD-01 consumer (CPU): preflight + formal records.  python qkd_analysis.py PRE_DIR RUN_DIR OUT_JSON"""
import hashlib
import json
import statistics as st
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'cache-query-state-transfer-v1-2026-11-02'))
import qkd_core as K  # noqa: E402
import qst_core as QK  # noqa: E402

DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'N_L00_C1343_D-1')
PAIRS = (('Rk', 'V'), ('Ak', 'F'), ('Rrk', 'V'), ('Ark', 'F'))
ARMS = ('V', 'F', 'Rk', 'Ak', 'Rrk', 'Ark')
QKF_NAME = {'V': 'V', 'F': 'F', 'Rk': 'R_mu_k', 'Ak': 'A_mu_k', 'Rrk': 'R_post_k', 'Ark': 'A_post_k'}


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


def qkf_behaviour():
    p = HERE.parent / 'cache-qk-component-factor-v1-2026-11-02/runs/formal-r01'
    out = {}
    for w in sorted(p.glob('worker-*')):
        if not w.is_dir():
            continue
        rc = json.load(open(w / 'receipt.json'))
        for rel in rc['record_hashes']:
            r = json.load(open(w / rel))
            out[r['text']] = (r['item'], r['trajectories'])
    return out


def y_full(t, it):
    return int(QK.y_full(t['text'], t['termination'], it['target'], it['listed_codes'], it['question']))


def analyse(pre, recs):
    e_pre = max(r['err_max'] for r in pre.values())
    thr = K.err_threshold(e_pre)
    scen = {i: r['scenario'] for i, r in recs.items()}
    qkf = qkf_behaviour()
    out = {'error': {'preflight_e_max': e_pre, 'formal_threshold': thr, 'formal_e_max': max(r['err_max'] for r in recs.values())},
           'directions': {}}
    out['error']['formal_within_threshold'] = out['error']['formal_e_max'] <= thr
    for d in DIRECTIONS:
        Y = {a: {} for a in ARMS}
        for i, r in recs.items():
            it = r['item']
            for a in ARMS:
                t = r['c1343_trajectories'][a] if d == 'N_L00_C1343_D-1' else qkf[i][1][f'{QKF_NAME[a]}|{d}']
                Y[a][i] = y_full(t, it)
        M = {a: {i: r['arms'][d][a].get('M') for i, r in recs.items()} for a in ARMS}
        dres = {'Y_totals': {a: sum(v.values()) for a, v in Y.items()},
                'M_mean': {a: st.mean([x for x in M[a].values() if x is not None]) for a in ARMS}, 'labels': {}}
        D_ = {i: int(Y['F'][i] == 1 and Y['V'][i] == 0) for i in recs}
        dres['n_D'] = sum(D_.values())
        for x, y in PAIRS:
            for route_step in ('C1', 'C2', 'C3', 'N2', 'N3'):
                sJ, sH, sD, sE, sW, res = {}, {}, {}, {}, {}, {}
                for i, r in recs.items():
                    vals = [r['pairs'].get(f'{x}|{y}|r={rc}|{route_step}|{d}') for rc in (x, y)]
                    vals = [v for v in vals if v and v['median_sJ'] is not None]
                    if not vals:
                        sJ[i] = sH[i] = None
                        continue
                    sJ[i] = st.mean(v['median_sJ'] for v in vals)
                    sH[i] = st.mean(v['median_sH'] for v in vals)
                    sD[i] = st.mean(v['median_sD'] for v in vals if v['median_sD'] is not None) if any(v['median_sD'] is not None for v in vals) else None
                    sE[i] = st.mean(v['median_sE'] for v in vals if v['median_sE'] is not None) if any(v['median_sE'] is not None for v in vals) else None
                    sW[i] = st.mean(v['median_sW'] for v in vals if v['median_sW'] is not None) if any(v['median_sW'] is not None for v in vals) else None
                    res[i] = st.mean(v['median_n_res'] / v['median_n_dact'] if v['median_n_dact'] else float('nan') for v in vals)
                lab = K.label(sJ, sH, scen)
                eqm = lambda dd: (lambda m: sum(m.values()) / len(m) if m else None)(K.smeans(dd, scen))   # noqa: E731
                lab.update({'eq_real_sD': eqm(sD), 'eq_real_sE': eqm(sE), 'eq_real_sW': eqm(sW), 'eq_resid_frac': eqm(res),
                            'n_examples': sum(v is not None for v in sH.values())})
                if route_step == 'C2':
                    base = y
                    dM = {i: (M[x][i] - M[base][i]) if M[x][i] is not None and M[base][i] is not None else None for i in recs}
                    grp = {}
                    for i in recs:
                        k_ = ('repaired' if (Y[base][i] == 0 and Y[x][i] == 1) else 'unrepaired' if (Y[base][i] == 0 and Y[x][i] == 0)
                              else 'broken' if (Y[base][i] == 1 and Y[x][i] == 0) else 'kept')
                        grp.setdefault(k_, []).append(i)
                    lab['groups'] = {k_: {'n': len(v), 'mean_dM': st.mean([dM[i] for i in v if dM[i] is not None]) if any(dM[i] is not None for i in v) else None,
                                          'mean_sH': st.mean([sH[i] for i in v if sH[i] is not None]) if any(sH[i] is not None for i in v) else None}
                                     for k_, v in grp.items()}
                dres['labels'][f'{x}|{y}|{route_step}'] = lab
        out['directions'][d] = dres
    return out


def main(pre_dir, run_dir, out_path):
    _, pre = load(pre_dir, 'preflight')
    ver, recs = load(run_dir, 'formal')
    assert len(recs) == 48
    res = analyse(pre, recs)
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256']}
    with open(out_path, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps(res['error'], indent=1))
    for d, x in res['directions'].items():
        print(d, x['Y_totals'], {k: round(v, 2) for k, v in x['M_mean'].items()})
        for k, v in x['labels'].items():
            if k.endswith(('C1', 'C2')):
                print('  ', k, v['label'], {kk: (round(vv, 2) if isinstance(vv, float) else vv) for kk, vv in v.items() if kk not in ('label', 'groups')})
                if 'groups' in v:
                    print('      groups', v['groups'])


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
