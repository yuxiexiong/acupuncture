"""QCO-01 consumer (CPU): verified formal records.  python qco_analysis.py RUN_DIR OUT_JSON"""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'cache-query-state-transfer-v1-2026-11-02'))
import qco_core as K  # noqa: E402
import qst_core as QK  # noqa: E402

DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'N_L00_C1343_D-1')
ARMS = ('V', 'F', 'R', 'A', 'R_rand', 'A_rand')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(run_dir):
    ver = json.load(open(Path(run_dir) / 'verification.json'))
    assert ver['status'] == 'passed' and ver['stage'] == 'formal'
    recs = {}
    for w in sorted(Path(run_dir).glob('worker-*')):
        if not w.is_dir():
            continue
        rc = json.load(open(w / 'receipt.json'))
        for rel, dg in rc['record_hashes'].items():
            assert sha(w / rel) == dg, rel
            r = json.load(open(w / rel))
            recs[r['text']] = r
    assert len(recs) == 48
    return ver, recs


def label(t, it):
    listed = it['listed_codes']
    full = [c for c in listed if QK.y_full(t['text'], t['termination'], c, listed, it['question'])]
    if full:
        return 'own' if full[0] == it['target'] else ('first_listed' if full[0] == it['first_listed'] else 'other_single')
    return QK.FK.classify(t['text'], t['termination'], it['target'], it['distractors'], it['question'])['main']


def analyse(recs):
    scen_of = {i: r['scenario'] for i, r in recs.items()}
    out = {'directions': {}}
    for d in DIRECTIONS:
        Y = {a: {} for a in ARMS}
        lab = {a: Counter() for a in ARMS}
        mA, mAr = {}, {}
        nR = nA = True
        broken = {a: 0 for a in ARMS}
        for i, r in recs.items():
            it = r['item']
            for a in ARMS:
                t = r['trajectories'][f'{a}|{d}']
                Y[a][i] = int(QK.y_full(t['text'], t['termination'], it['target'], it['listed_codes'], it['question']))
                lab[a][label(t, it)] += 1
            mA[i] = r['trajectories'][f'A|{d}']['ids'] == r['trajectories'][f'V|{d}']['ids']
            mAr[i] = r['trajectories'][f'A_rand|{d}']['ids'] == r['trajectories'][f'V|{d}']['ids']
            ok = r['edit_norms'][f'norm_ok|{d}']
            nR &= ok['R']
            nA &= ok['A']
            for a in ('R', 'R_rand'):
                broken[a] += int(Y['V'][i] == 1 and Y[a][i] == 0)
            for a in ('A', 'A_rand'):
                broken[a] += int(Y['F'][i] == 1 and Y['V'][i] == 1 and Y[a][i] == 0)
        j = K.judge(Y, mA, mAr, scen_of, nR, nA)
        out['directions'][d] = {**j, 'Y_totals': {a: sum(v.values()) for a, v in Y.items()}, 'labels': {a: dict(c) for a, c in lab.items()},
                                'A_exact_V': sum(mA.values()), 'Arand_exact_V': sum(mAr.values()), 'broken': broken,
                                'edit_norm_mean': {a: sum(r['edit_norms'][f'{a}|{d}'] for r in recs.values()) / 48 for a in ('R', 'A', 'R_rand', 'A_rand')}}
    return out


def main(run_dir, out_path):
    ver, recs = load(run_dir)
    res = analyse(recs)
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256']}
    with open(out_path, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps({d: {k: v for k, v in x.items() if k not in ('gap_by_scenario',)} for d, x in res['directions'].items()}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
