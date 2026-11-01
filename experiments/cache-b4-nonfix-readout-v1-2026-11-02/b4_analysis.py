"""B4 consumer (CONTRACT §4–5): reads the verified formal records + frozen shadow file; no model calls.
python b4_analysis.py RUN_DIR OUT_JSON"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import b4_core as K  # noqa: E402

ARMS = ('K0', 'K', 'K_early', 'K_late', 'M_nat', 'M_rand')


def unit_readouts(rec, d, side='cz_s46'):
    z = {a: rec['cells'][f'{a}|{d}']['readout']['primary'][side] for a in ('CC', 'CFIX') + ARMS}
    X = z['CFIX'] - z['CC']
    out = {'X': X, 'X_arm': {a: z[a] - z['CC'] for a in ARMS}}
    out['rho'] = {a: K.rho(out['X_arm'][a], X) for a in ARMS}
    m = rec['matching'][d]
    for a in ('M_nat', 'M_rand'):
        out[f'{a}_matched'] = bool(m[a]['matched'])
        if not m[a]['matched']:
            out['rho'][a] = None                       # comparison not judgeable for this unit
    out['eos'] = {a: rec['cells'][f'{a}|{d}']['score']['first_step_eos'] for a in ('CC', 'CFIX') + ARMS}
    return out


def analyse(recs, shadow):
    ids = sorted(recs)
    res = {'directions': {}}
    rho_k, rho_sh = {}, {}
    for d in K.DIRECTIONS:
        u = {i: unit_readouts(recs[i], d) for i in ids}
        ua = {i: unit_readouts(recs[i], d, 'cz_a') for i in ids}
        a4 = {i: K.axis_a(u[i]['rho']['K']) for i in ids}
        am = {i: K.axis_a_main(u[i]['rho']['K']) for i in ids}
        ab = {i: K.axis_b(u[i]['rho']['K'], u[i]['rho']['M_nat'], u[i]['rho']['M_rand']) for i in ids}
        p4, pm, pb = K.scenario_pairs(a4), K.scenario_pairs(am), K.scenario_pairs(ab)
        lab_main, c_main = K.direction_label(pm)
        lab_b, c_b = K.direction_label(pb)
        lab_4, c_4 = K.direction_label(p4)
        joint = K.joint_scenarios(p4, pb)
        rho_k[d] = {i: u[i]['rho']['K'] for i in ids}
        rho_sh[d] = {i: shadow['per_direction'][d][i]['rho_shadow'] for i in ids}
        mean = lambda xs: sum(xs) / len(xs) if xs else None   # noqa: E731
        res['directions'][d] = {
            'axis_a_main': {'label': lab_main, 'counts': c_main}, 'axis_a_four_bin': {'label': lab_4, 'counts': c_4},
            'axis_b': {'label': lab_b, 'counts': c_b}, 'joint_scenarios': joint, 'n_joint': len(joint),
            'mean_X': mean([u[i]['X'] for i in ids]),
            'mean_rho': {a: mean([u[i]['rho'][a] for i in ids if u[i]['rho'][a] is not None]) for a in ARMS},
            'n_matched': {a: sum(u[i][f'{a}_matched'] for i in ids) for a in ('M_nat', 'M_rand')},
            'mean_rho_shadow': mean(list(rho_sh[d].values())),
            'eos_counts': {a: sum(u[i]['eos'][a] for i in ids) for a in ('CC', 'CFIX') + ARMS},
            'answer_side_mean_X': {a: mean([ua[i]['X_arm'][a] for i in ids]) for a in ARMS} | {'CFIX': mean([ua[i]['X'] for i in ids])},
            'per_input': {i: {'X': u[i]['X'], 'rho': u[i]['rho'], 'axis_a': a4[i], 'axis_b': ab[i], 'rho_shadow': rho_sh[d][i]} for i in ids}}
    D = res['directions']
    res['cross'] = {'axis_a_main': K.cross_label({d: D[d]['axis_a_main']['label'] for d in D}),
                    'axis_b': K.cross_label({d: D[d]['axis_b']['label'] for d in D}),
                    'joint_strong_and_exceeds_both': K.joint_label({d: D[d]['n_joint'] for d in D})}
    res['predictions'] = K.predictions(rho_k, rho_sh)
    k0 = all(abs(D[d]['mean_rho']['K0'] or 0.0) == 0.0 for d in D)
    res['K0_exact_zero'] = k0
    return res


def main(run_dir, out):
    run_dir = Path(run_dir)
    ver = json.loads((run_dir / 'verification.json').read_text())
    assert ver['status'] == 'passed' and ver['stage'] == 'formal'
    recs = {}
    for w in sorted(run_dir.glob('worker-*')):
        if w.is_dir():
            for f in sorted((w / 'records').glob('*.json')):
                r = json.loads(f.read_text())
                recs[r['item']['id']] = r
    assert len(recs) == 12
    shadow = json.loads((HERE / 'readiness/shadow-r01.json').read_text())
    res = analyse(recs, shadow)
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256']}
    with open(out, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({'cross': res['cross'], 'predictions': {k: v for k, v in res['predictions'].items()},
                      'per_dir': {d: {k: res['directions'][d][k] for k in ('mean_rho', 'n_matched', 'mean_rho_shadow')} for d in K.DIRECTIONS}},
                     ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
