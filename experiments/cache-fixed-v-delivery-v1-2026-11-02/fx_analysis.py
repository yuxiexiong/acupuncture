"""FX-01 consumer: verified formal records (CPU).  python fx_analysis.py RUN_DIR OUT_JSON"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'cache-first-token-continuation-v1-2026-11-02'))
sys.path.insert(0, str(HERE))
import fc_core as FK  # noqa: E402
import fx_core as K  # noqa: E402

DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'N_L00_C1343_D-1')
T_ARMS = ('T_nat', 'T_F', 'T_V', 'T_FIXV', 'T_RESTV', 'T_U')
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
    cls = {i: {name: FK.classify(t['text'], t['termination'], recs[i]['answer'], recs[i]['distractors'], recs[i]['item']['question'])
               for name, t in recs[i]['trajectories'].items()} for i in ids}
    c_ok = {i: cls[i]['C_nat']['Y_delivery'] for i in ids}
    out = {'C_nat': sum(c_ok.values()), 'directions': {}}
    sv, sf = {}, {}
    for d in DIRECTIONS:
        ok = {a: {i: cls[i][f'{a}|{d}']['Y_delivery'] for i in ids} for a in T_ARMS}
        st = {a: K.direction_status(c_ok, ok['T_nat'], ok[a]) for a in T_ARMS if a != 'T_nat'}
        sv[d], sf[d] = st['T_V'], st['T_FIXV']
        out['directions'][d] = {
            'arms': {a: {'Y_delivery': sum(ok[a].values()), 'Y_strict': sum(cls[i][f'{a}|{d}']['Y_strict'] for i in ids),
                         'main': {m: sum(cls[i][f'{a}|{d}']['main'] == m for i in ids) for m in MAINS}} for a in T_ARMS},
            'status': st, 'fix_vs_u': K.fix_vs_u(c_ok, ok['T_nat'], ok['T_FIXV'], ok['T_U']),
            'restored_v_norm_mean': {a: sum(recs[i]['restored_v_norm'][f'{a}|{d}'] for i in ids) / len(ids) for a in ('T_V', 'T_FIXV', 'T_RESTV', 'T_U')},
            'samples': {i: {a: (cls[i][f'{a}|{d}']['main'], cls[i][f'{a}|{d}']['visible'][:60]) for a in T_ARMS} for i in ids}}
    out['P_V'] = K.overall(sv)
    out['P_FIX'] = K.overall(sf)
    out['U_overlap_with_FIX'] = {i: recs[i]['U_overlap_with_FIX'] for i in ids}
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
    print(json.dumps({k: res[k] for k in ('C_nat', 'P_V', 'P_FIX')}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
