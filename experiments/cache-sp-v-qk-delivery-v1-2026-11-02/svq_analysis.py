"""SVQ-01 consumer: verified formal records (CPU).  python svq_analysis.py RUN_DIR OUT_JSON"""
import hashlib
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import svq_core as K  # noqa: E402

FK = K.FK
DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'N_L00_C1343_D-1')
T_ARMS = ('T_nat', 'T_V', 'T_QK', 'T_F')
MAINS = ('correct', 'distractor', 'other_code', 'multi_code', 'stopped_no_code', 'budget_no_code')


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


def analyse(recs):
    ids = sorted(recs)
    items = {i: recs[i]['item'] for i in ids}
    cls = {}
    for i in ids:
        st = recs[i]['second_tokens']
        cls[i] = {name: {**FK.classify(t['text'], t['termination'], recs[i]['answer'], recs[i]['distractors'], recs[i]['item']['question']),
                         'first_token': t['ids'][0], 'n_tokens': len(t['ids']),
                         'step1_qshared_minus_s0': t['first']['q_shared'] - t['first']['s0'],
                         'step1_qshared_minus_other_max': t['first']['q_shared'] - t['first']['other_max'],
                         'M_diag': K.margin(t['diag']['watch'], st['target'], st['distractors'])}
                  for name, t in recs[i]['trajectories'].items()}
    c_ok = {i: cls[i]['C_nat']['Y_delivery'] for i in ids}
    out = {'C_nat': {'Y_delivery': sum(c_ok.values()), 'Y_strict': sum(cls[i]['C_nat']['Y_strict'] for i in ids),
                     'M_diag': {i: cls[i]['C_nat']['M_diag'] for i in ids}}, 'directions': {}}
    stV, stQ, stF = {}, {}, {}
    for d in DIRECTIONS:
        ok = {a: {i: cls[i][f'{a}|{d}']['Y_delivery'] for i in ids} for a in T_ARMS}
        st = {a: K.rescue_status(c_ok, ok['T_nat'], ok[a]) for a in ('T_V', 'T_QK', 'T_F')}
        stV[d], stQ[d], stF[d] = st['T_V'], st['T_QK'], st['T_F']
        out['directions'][d] = {
            'arms': {a: {'Y_delivery': sum(ok[a].values()), 'Y_strict': sum(cls[i][f'{a}|{d}']['Y_strict'] for i in ids),
                         'main': {m: sum(cls[i][f'{a}|{d}']['main'] == m for i in ids) for m in MAINS},
                         'first_token_is_shared': sum(cls[i][f'{a}|{d}']['first_token'] == recs[i]['q_shared'] for i in ids),
                         'M_diag_mean': statistics.mean(cls[i][f'{a}|{d}']['M_diag'] for i in ids),
                         'M_diag_positive_inputs': sum(cls[i][f'{a}|{d}']['M_diag'] > 0 for i in ids),
                         'step1_qshared_minus_other_max_mean': statistics.mean(cls[i][f'{a}|{d}']['step1_qshared_minus_other_max'] for i in ids),
                         'selection_non_first': K.selection({i: cls[i][f'{a}|{d}'] for i in ids}, items)} for a in T_ARMS},
            'status': st,
            'pairing': {'F_vs_V': K.pairing(ok['T_F'], ok['T_V']), 'F_vs_QK': K.pairing(ok['T_F'], ok['T_QK']),
                        'V_vs_QK': K.pairing(ok['T_V'], ok['T_QK'])},
            'transitions_vs_T_nat': {a: FK.transitions(ok['T_nat'], ok[a]) for a in ('T_V', 'T_QK', 'T_F')},
            'samples': {i: {a: (cls[i][f'{a}|{d}']['main'], cls[i][f'{a}|{d}']['visible'][:60]) for a in T_ARMS} for i in ids}}
    out['P_SV'] = K.overall(stV)
    out['P_SQK'] = K.overall(stQ)
    out['F_reference'] = K.overall(stF)
    out['C_selection_non_first'] = K.selection({i: cls[i]['C_nat'] for i in ids}, items)
    out['per_input'] = cls
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
    brief = {k: res[k] for k in ('C_nat', 'P_SV', 'P_SQK', 'F_reference', 'C_selection_non_first')}
    brief['directions'] = {d: {'status': {a: v['status'] for a, v in x['status'].items()}, 'rescued': {a: v['rescued'] for a, v in x['status'].items()},
                               'Y': {a: (v['Y_delivery'], v['Y_strict']) for a, v in x['arms'].items()}, 'pairing': x['pairing'],
                               'selection': {a: v['selection_non_first'] for a, v in x['arms'].items()},
                               'M_mean': {a: round(v['M_diag_mean'], 2) for a, v in x['arms'].items()}} for d, x in res['directions'].items()}
    print(json.dumps(brief, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
