"""SP-01 consumer: verified formal records (CPU).  python sp_analysis.py RUN_DIR OUT_JSON"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'cache-first-token-continuation-v1-2026-11-02'))
sys.path.insert(0, str(HERE))
import fc_core as FK  # noqa: E402
import sp_core as K  # noqa: E402

DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'N_L00_C1343_D-1')
T_ARMS = ('T_nat', 'T_noEOS1', 'T_shared', 'T_F')
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
    cls = {i: {name: {**FK.classify(t['text'], t['termination'], recs[i]['answer'], recs[i]['distractors'], recs[i]['item']['question']),
                      'n_tokens': len(t['ids']), 'first_token': t['ids'][0],
                      'M': K.margin(t['first'].get('step2'), recs[i]['second_tokens']['target'], recs[i]['second_tokens']['distractors'])}
               for name, t in recs[i]['trajectories'].items()} for i in ids}
    c_ok = {i: cls[i]['C_nat']['Y_delivery'] for i in ids}
    out = {'C': {a: {'Y_delivery': sum(cls[i][a]['Y_delivery'] for i in ids), 'Y_strict': sum(cls[i][a]['Y_strict'] for i in ids),
                     'main': {m: sum(cls[i][a]['main'] == m for i in ids) for m in MAINS}} for a in ('C_nat', 'C_noEOS1')},
           'c_first_is_shared': {i: recs[i]['c_first_is_shared'] for i in ids}, 'directions': {}}
    stA1, stA2 = {}, {}
    for d in DIRECTIONS:
        tn = {i: cls[i][f'T_nat|{d}']['Y_delivery'] for i in ids}
        arms = {a: {'Y_delivery': sum(cls[i][f'{a}|{d}']['Y_delivery'] for i in ids), 'Y_strict': sum(cls[i][f'{a}|{d}']['Y_strict'] for i in ids),
                    'main': {m: sum(cls[i][f'{a}|{d}']['main'] == m for i in ids) for m in MAINS},
                    'think_present': sum(cls[i][f'{a}|{d}']['tags']['think_present'] for i in ids)} for a in T_ARMS}
        stA1[d] = K.direction_status(c_ok, tn, {i: cls[i][f'T_F|{d}']['Y_delivery'] for i in ids})
        stA2[d] = K.direction_status(c_ok, tn, {i: cls[i][f'T_shared|{d}']['Y_delivery'] for i in ids})
        Ms = [(cls[i]['C_nat']['M'], cls[i][f'T_shared|{d}']['M']) for i in ids if recs[i]['c_first_is_shared']]
        out['directions'][d] = {'arms': arms, 'P_A1': stA1[d], 'P_A2': stA2[d],
                                'transitions_vs_T_nat': {a: FK.transitions(tn, {i: cls[i][f'{a}|{d}']['Y_delivery'] for i in ids}) for a in ('T_noEOS1', 'T_shared', 'T_F')},
                                'M_pairs_C_vs_T_shared': Ms,
                                'samples': {i: {a: (cls[i][f'{a}|{d}']['main'], cls[i][f'{a}|{d}']['visible'][:80]) for a in T_ARMS} for i in ids}}
    out['P_A1_overall'] = K.overall(stA1)
    out['P_A2_overall'] = K.overall(stA2)
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
    print(json.dumps({k: res[k] for k in ('C', 'c_first_is_shared', 'P_A1_overall', 'P_A2_overall')}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
