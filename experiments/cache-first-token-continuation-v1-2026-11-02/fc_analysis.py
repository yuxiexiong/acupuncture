"""FC-01 consumer: verified formal records only (CPU).  python fc_analysis.py RUN_DIR OUT_JSON"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fc_core as K  # noqa: E402

DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'N_L00_C1343_D-1')
T_ARMS = ('T_nat', 'T_noEOS1', 'T_q0', 'T_F')


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
    cls = {}
    for i in ids:
        r = recs[i]
        q = r['item'].get('question')
        cls[i] = {name: {**K.classify(t['text'], t['termination'], r['answer'], r['distractors'], q),
                         'n_tokens': len(t['ids']), 'stop_step': len(t['ids']) if t['termination'] == 'stop' else None,
                         'first_token': t['ids'][0]} for name, t in r['trajectories'].items()}
    out = {'audit': {i: K.q0_audit(recs[i]['q0_text'], recs[i]['answer'], recs[i]['distractors']) for i in ids},
           'C': {a: {'Y_delivery': sum(cls[i][a]['Y_delivery'] for i in ids), 'Y_strict': sum(cls[i][a]['Y_strict'] for i in ids),
                     'main': {m: sum(cls[i][a]['main'] == m for i in ids) for m in ('correct', 'distractor', 'other_code', 'multi_code', 'stopped_no_code', 'budget_no_code')}}
                 for a in ('C_nat', 'C_noEOS1')},
           'directions': {}}
    c_ok = {i: cls[i]['C_nat']['Y_delivery'] for i in ids}
    for d in DIRECTIONS:
        arms = {}
        for a in T_ARMS:
            key = f'{a}|{d}'
            arms[a] = {'Y_delivery': sum(cls[i][key]['Y_delivery'] for i in ids), 'Y_strict': sum(cls[i][key]['Y_strict'] for i in ids),
                       'main': {m: sum(cls[i][key]['main'] == m for i in ids) for m in ('correct', 'distractor', 'other_code', 'multi_code', 'stopped_no_code', 'budget_no_code')},
                       'think_present': sum(cls[i][key]['tags']['think_present'] for i in ids),
                       'contains_question': sum(cls[i][key]['tags']['contains_question'] for i in ids),
                       'mean_tokens': sum(cls[i][key]['n_tokens'] for i in ids) / len(ids)}
        nat = {i: cls[i][f'T_nat|{d}']['Y_delivery'] for i in ids}
        trans = {a: K.transitions(nat, {i: cls[i][f'{a}|{d}']['Y_delivery'] for i in ids}) for a in ('T_noEOS1', 'T_q0', 'T_F')}
        pf = K.p_f_direction(c_ok, {i: cls[i][f'T_F|{d}']['Y_delivery'] for i in ids})
        out['directions'][d] = {'arms': arms, 'transitions_vs_T_nat': trans, 'P_F': {'status': pf[0], 'support_scenarios': pf[1], 'baseline_scenarios': pf[2]},
                                'samples': {i: {a: {'visible': cls[i][f'{a}|{d}']['visible'][:120], 'main': cls[i][f'{a}|{d}']['main']} for a in T_ARMS} for i in ids}}
    out['P_F_k_of_4'] = sum(out['directions'][d]['P_F']['status'] == 'support' for d in DIRECTIONS)
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
    print(json.dumps({'P_F_k_of_4': res['P_F_k_of_4'], 'C': res['C'],
                      'dirs': {d: {k: v for k, v in res['directions'][d].items() if k != 'samples'} for d in DIRECTIONS}}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
