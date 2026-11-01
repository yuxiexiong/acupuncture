"""EH-XC consumer: verified formal records only (CPU, no model calls).  python xc_analysis.py RUN_DIR OUT_JSON"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import xc_core as K  # noqa: E402

CHANNELS = (1343, 2191, 3152, 3959, 6137, 6547, 6616, 8215)
VALIDATION = tuple(f'N_L00_C{c}_D-1' for c in CHANNELS)
RANDOM = ('R0_L00_D-1', 'R1_L00_D-1', 'R2_L00_D-1', 'R3_L00_D-1')
ANCHORS = ('N_L00_C1210_D-1', 'N_L00_C4146_D-1')
ALL = VALIDATION + ANCHORS + RANDOM
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


def terms(rec, key, s0, q0):
    ro, sc = rec['cells'][key]['readout'], rec['cells'][key]['score']
    z = {STOP[0]: ro['raw']['s44'], STOP[1]: ro['raw']['s46']}
    smax = max(z.values())
    D = ro['D']
    return {'D': D, 'F': z[s0] - ro['raw']['a'], 'A': smax - z[s0], 'B': (smax - D) - ro['raw']['a'],
            'eos': bool(sc['first_step_eos']), 'stop_winner': sc['stop_winner'], 'nonstop_winner': sc['nonstop_winner'],
            'spacing': max(x for x in (K.bf16_spacing(smax), K.bf16_spacing(smax - D)) if x is not None), 'tie': D == 0}


def analyse(recs):
    ids = sorted(recs)
    out = {'needles': {}}
    for d in ALL:
        per, status = {}, {}
        for i in ids:
            r = recs[i]
            cn = r['cells']['C_native']['score']
            s0, q0 = cn['stop_winner'], cn['nonstop_winner']
            t = {c: terms(r, c if c == 'C_native' else f'{c}|{d}', s0, q0) for c in ('C_native', 'X10', 'H01', 'XH11', 'T_native')}
            e = K.effects(t['C_native']['D'], t['X10']['D'], t['H01']['D'], t['XH11']['D'], t['T_native']['D'])
            eF = K.effects(t['C_native']['F'], t['X10']['F'], t['H01']['F'], t['XH11']['F'], t['T_native']['F'])
            st = K.fact_status(e)
            status[i] = st
            per[i] = {'effects_D': e, 'effects_F': eF, 'status': st, 'I_threshold': K.i_threshold(e['E']),
                      'I_D_passes_F_not': st['inter'] in ('support', 'violate') and K.p_i(e) and not (eF['I'] >= K.i_threshold(eF['E'])),
                      'eos': {c: t[c]['eos'] for c in t}, 'ties': [c for c in t if t[c]['tie']],
                      'max_spacing': max(t[c]['spacing'] for c in t), 'D': {c: t[c]['D'] for c in t},
                      'tv_P_C': r['cells'][f'T_native|{d}'].get('tv_vs_C'), 'tv_11_C': r['cells'][f'XH11|{d}'].get('tv_vs_C')}
        labels = {rel: K.needle_label(status, rel) for rel in ('hist', 'inter', 'joint')}
        mean = lambda xs: sum(xs) / len(xs)   # noqa: E731
        app_counts = {}
        for i in ids:
            app_counts[status[i]['applicability']] = app_counts.get(status[i]['applicability'], 0) + 1
        out['needles'][d] = {'labels': labels, 'applicability_counts': app_counts,
                             'means': {k: mean([per[i]['effects_D'][k] for i in ids]) for k in ('N', 'E', 'H0', 'H1', 'X0', 'X1', 'I')},
                             'means_F': {k: mean([per[i]['effects_F'][k] for i in ids]) for k in ('N', 'E', 'H0', 'X0', 'I')},
                             'eos_counts': {c: sum(per[i]['eos'][c] for i in ids) for c in ('C_native', 'X10', 'H01', 'XH11', 'T_native')},
                             'n_I_D_passes_F_not': sum(per[i]['I_D_passes_F_not'] for i in ids),
                             'max_spacing': max(per[i]['max_spacing'] for i in ids),
                             'ties': {i: per[i]['ties'] for i in ids if per[i]['ties']},
                             'per_input': per}
    J = {d: out['needles'][d]['labels']['joint'] for d in ALL}
    out['P_XC'] = K.panel(J, VALIDATION, K.RULE['xc_count'])
    out['P_R'] = K.panel(J, RANDOM, K.RULE['r_count'])
    for rel in ('hist', 'inter'):
        L_ = {d: out['needles'][d]['labels'][rel] for d in ALL}
        out[f'validation_{rel}'] = K.panel(L_, VALIDATION, K.RULE['xc_count'])
        out[f'random_{rel}'] = K.panel(L_, RANDOM, K.RULE['r_count'])
    out['anchors'] = {d: {rel: out['needles'][d]['labels'][rel]['n_support'] for rel in ('hist', 'inter', 'joint')} for d in ANCHORS}
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
    summ = {d: {'means': {k: round(v, 2) for k, v in res['needles'][d]['means'].items()}, 'app': res['needles'][d]['applicability_counts'],
                'support': {rel: res['needles'][d]['labels'][rel]['n_support'] for rel in ('hist', 'inter', 'joint')},
                'eos': res['needles'][d]['eos_counts']} for d in ALL}
    print(json.dumps({'P_XC': res['P_XC'], 'P_R': res['P_R'], 'validation_hist': res['validation_hist'], 'validation_inter': res['validation_inter'],
                      'random_hist': res['random_hist'], 'random_inter': res['random_inter'], 'needles': summ}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
