"""SK-01 consumer: verified formal records (CPU, no model calls).  python sk_analysis.py RUN_DIR OUT_JSON"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sk_core as K  # noqa: E402

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


def val(rec, key, field):
    ro = rec['cells'][key]['readout']
    if field == 'D':
        return ro['D']
    s0 = rec['cells']['C_native']['score']['stop_winner']
    z = {STOP[0]: ro['raw']['s44'], STOP[1]: ro['raw']['s46']}
    if field == 'F':
        return z[s0] - ro['raw']['a']
    smax = max(z.values())
    if field == 'A':
        return smax - z[s0]
    return (smax - ro['D']) - ro['raw']['a']          # B


def analyse(recs):
    ids = sorted(recs)
    out = {'directions': {}}
    mean = lambda xs: sum(xs) / len(xs)   # noqa: E731
    for d in DIRECTIONS:
        per = {}
        for i in ids:
            r = recs[i]
            k = lambda c: f'{c}|{d}'   # noqa: E731
            eff = {}
            for fld in ('D', 'F', 'A', 'B'):
                m = K.main_effects(*(val(r, k(c), fld) for c in ('SK00', 'SK10', 'SK01', 'SK11')))
                nat = K.native_effects(val(r, 'C_native', fld), *(val(r, k(c), fld) for c in ('T_native', 'P_S0', 'P_K0', 'P_SK0')))
                eff[fld] = {**m, **nat}
            m, nat = K.main_effects(*(val(r, k(c), 'D') for c in ('SK00', 'SK10', 'SK01', 'SK11'))), \
                K.native_effects(val(r, 'C_native', 'D'), *(val(r, k(c), 'D') for c in ('T_native', 'P_S0', 'P_K0', 'P_SK0')))
            per[i] = {'effects': eff, 'category': K.main_category(m, nat), 'p_native': K.p_native(nat), 'native_pattern': K.native_pattern(nat),
                      'near': K.near_boundaries(m, nat),
                      'eos': {c: bool(r['cells'][c if c == 'C_native' else k(c)]['score']['first_step_eos'])
                              for c in ('C_native', 'T_native', 'SK00', 'SK10', 'SK01', 'SK11', 'P_S0', 'P_K0', 'P_SK0')},
                      'J_D_without_J_F': abs(eff['D']['J']) >= K.eps(eff['D']['H']) and abs(eff['F']['J']) < K.eps(eff['F']['H'])}
        s_ok, s_counts = K.direction_label(K.scenario_pairs({i: per[i]['category'] for i in ids}), 'S_concentrated')
        lab, cat_counts = K.direction_label(K.scenario_pairs({i: per[i]['category'] for i in ids}))
        pn_ok, pn_counts = K.direction_label(K.scenario_pairs({i: per[i]['p_native'] for i in ids}), 'support')
        npat, np_counts = K.direction_label(K.scenario_pairs({i: per[i]['native_pattern'] for i in ids}))
        cross = {}
        for i in ids:
            key = f"{'S_concentrated' if per[i]['category'] == 'S_concentrated' else 'not_S_concentrated'}|{per[i]['p_native']}"
            cross[key] = cross.get(key, 0) + 1
        keys = ('S0', 'S1', 'K0', 'K1', 'H', 'J', 'N', 'R_S', 'R_K', 'R_SK', 'J_native')
        out['directions'][d] = {
            'P_S_direction': s_ok, 'category_label': lab, 'category_scenario_counts': cat_counts,
            'P_native_direction': pn_ok, 'p_native_scenario_counts': pn_counts, 'native_pattern_label': npat, 'native_pattern_counts': np_counts,
            'cross_table_facts': cross,
            'means_D': {x: mean([per[i]['effects']['D'][x] for i in ids]) for x in keys},
            'means_F': {x: mean([per[i]['effects']['F'][x] for i in ids]) for x in keys},
            'eos_counts': {c: sum(per[i]['eos'][c] for i in ids) for c in per[ids[0]]['eos']},
            'n_near_boundary': sum(bool(per[i]['near']) for i in ids),
            'n_J_D_without_J_F': sum(per[i]['J_D_without_J_F'] for i in ids),
            'per_input': per}
    D_ = out['directions']
    out['P_S_k_of_4'] = sum(D_[d]['P_S_direction'] for d in D_)
    out['P_native_k_of_4'] = sum(D_[d]['P_native_direction'] for d in D_)
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
    print(json.dumps({'P_S_k_of_4': res['P_S_k_of_4'], 'P_native_k_of_4': res['P_native_k_of_4'],
                      'dirs': {d: {k: v for k, v in res['directions'][d].items() if k != 'per_input'} for d in DIRECTIONS}}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
