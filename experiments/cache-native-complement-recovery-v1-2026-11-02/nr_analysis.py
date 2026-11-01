"""NR-01 consumer: verified formal records (CPU, no model calls).  python nr_analysis.py RUN_DIR OUT_JSON"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import nr_core as K  # noqa: E402

DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'N_L00_C1343_D-1')
STOP = (248044, 248046)


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


def val(rec, key, fld):
    ro = rec['cells'][key]['readout']
    if fld == 'D':
        return ro['D']
    s0 = rec['cells']['C_native']['score']['stop_winner']
    z = {STOP[0]: ro['raw']['s44'], STOP[1]: ro['raw']['s46']}
    smax = max(z.values())
    return {'Q': z[s0] - ro['raw']['a'], 'A': smax - z[s0], 'B': (smax - ro['D']) - ro['raw']['a']}[fld]


def analyse(recs):
    ids = sorted(recs)
    out = {'directions': {}}
    mean = lambda xs: sum(xs) / len(xs)   # noqa: E731
    for d in DIRECTIONS:
        per = {}
        for i in ids:
            r = recs[i]
            k = lambda c: f'{c}|{d}'   # noqa: E731
            dec = {}
            for fld in ('D', 'Q', 'A', 'B'):
                P = val(r, k('T_native'), fld)
                N = P - val(r, 'C_native', fld)
                R = K.recoveries(P, {code: val(r, k(f'R{code}'), fld) for code in K.CODES.values()})
                dec[fld] = {'N': N, 'R': R, **K.decompose(R, N)}
            N = dec['D']['N']
            per[i] = {'dec': dec, 'pred': K.fact_predictions(dec['D'], N), 'desc': K.descriptive(dec['D'], N), 'near': K.near_boundaries(dec['D'], N),
                      'D_abs': {c: val(r, c if c == 'C_native' else k(c), 'D') for c in ['C_native', 'T_native'] + [f'R{x}' for x in K.CODES.values()]},
                      'eos': {c: bool(r['cells'][c if c == 'C_native' else k(c)]['score']['first_step_eos']) for c in ['C_native', 'T_native'] + [f'R{x}' for x in K.CODES.values()]},
                      'D_not_Q': {kk: (K.sign_label(dec['D'][kk], K.tau(N)) != 'small' and K.sign_label(dec['Q'][kk], K.tau(N)) == 'small')
                                  for kk in ('i_XF', 'i_XH', 'i_FH', 'i_XFH')}}
        status = {p: K.direction_status(K.scenario_pairs({i: per[i]['pred'][p] for i in ids})) for p in ('P_X', 'P_XH')}
        keys = ('r_X', 'r_F', 'r_H', 'i_XF', 'i_XH', 'i_FH', 'i_XFH', 'L_X', 'L_F', 'L_H', 'E_XFH')
        app = [i for i in ids if per[i]['desc'].get('applicable')]
        out['directions'][d] = {
            'P_X': status['P_X'], 'P_XH': status['P_XH'],
            'mean_N': mean([per[i]['dec']['D']['N'] for i in ids]),
            'means_D': {x: mean([per[i]['dec']['D'][x] for i in ids]) for x in keys},
            'means_Q': {x: mean([per[i]['dec']['Q'][x] for i in ids]) for x in keys},
            'share_of_N': {x: mean([per[i]['dec']['D'][x] / per[i]['dec']['D']['N'] for i in app]) for x in keys} if app else None,
            'strong_single_recovery_counts': {f: sum(f in per[i]['desc']['strong_single_recovery'] for i in app) for f in 'XFH'},
            'single_retention_majority_counts': {f: sum(f in per[i]['desc']['single_retention_majority'] for i in app) for f in 'XFH'},
            'interaction_sign_counts': {kk: {s: sum(per[i]['desc']['interaction_signs'][kk] == s for i in app) for s in ('positive', 'small', 'negative')}
                                        for kk in ('i_XF', 'i_XH', 'i_FH', 'i_XFH')},
            'additive_compatible_count': sum(per[i]['desc']['additive_compatible'] for i in app),
            'D_not_Q_counts': {kk: sum(per[i]['D_not_Q'][kk] for i in ids) for kk in ('i_XF', 'i_XH', 'i_FH', 'i_XFH')},
            'eos_counts': {c: sum(per[i]['eos'][c] for i in ids) for c in per[ids[0]]['eos']},
            'n_near_boundary': sum(bool(per[i]['near']) for i in ids),
            'max_identity_err': max(abs(per[i]['dec']['D']['identity_err']) for i in ids),
            'per_input': per}
    D_ = out['directions']
    for p in ('P_X', 'P_XH'):
        out[p + '_k_of_4'] = sum(D_[d][p][0] == 'support' for d in D_)
    return out


def main(run_dir, out_path):
    ver = json.load(open(Path(run_dir) / 'verification.json'))
    assert ver['status'] == 'passed' and ver['stage'] == 'formal'
    recs = load(run_dir)
    assert len(recs) == 12
    res = analyse(recs)
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256']}
    with open(out_path, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'P_X_k_of_4': res['P_X_k_of_4'], 'P_XH_k_of_4': res['P_XH_k_of_4'],
                      'dirs': {d: {k: v for k, v in res['directions'][d].items() if k != 'per_input'} for d in DIRECTIONS}}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
