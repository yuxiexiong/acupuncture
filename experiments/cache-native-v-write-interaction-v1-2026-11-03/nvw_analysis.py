"""NVW-01 consumer (CPU).  python nvw_analysis.py RUN_DIR OUT_JSON"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'cache-query-state-transfer-v1-2026-11-02'))
import nvw_core as K  # noqa: E402
import qst_core as QK  # noqa: E402

DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'N_L00_C1343_D-1')
GAP = DIRECTIONS[:3]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(run_dir, stage='formal'):
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


def yf(t, it):
    return int(QK.y_full(t['text'], t['termination'], it['target'], it['listed_codes'], it['question']))


def analyse(recs):
    scen = {i: r['scenario'] for i, r in recs.items()}
    tnf = {i for i, r in recs.items() if r['item']['target'] != r['item']['first_listed']}
    allids = set(recs)
    out = {'n': len(recs), 'signed_zero_exceptions': sum(r['signed_zero_exceptions'] for r in recs.values()),
           'oracle_max': max(r['oracle_max'] for r in recs.values()), 'directions': {}}
    labs = {f: {} for f in ('R', 'A', 'Z')}
    for d in DIRECTIONS:
        A = {i: recs[i]['directions'][d]['arms'] for i in recs}
        arms = list(next(iter(A.values())))
        Z = {'G': {a: {i: A[i][a]['first']['G'] for i in recs} for a in arms},
             'M': {a: {i: A[i][a]['C']['M'] for i in recs} for a in arms},
             'Y': {a: {i: yf(A[i][a]['N'], recs[i]['item']) for i in recs} for a in arms}}
        dres = {'arm_summary': {a: {'Y': sum(Z['Y'][a].values()), 'stop_first': sum(1 for i in recs if A[i][a]['N']['ids'][0] in (248044, 248046)),
                                    'G_mean': sum(Z['G'][a].values()) / len(recs), 'M_tnf_mean': sum(Z['M'][a][i] for i in tnf) / len(tnf)} for a in arms},
                'families': {}}
        for fam in ('R', 'A', 'Z'):
            res = K.family(Z, scen, fam, tnf, allids)
            res['first16'] = K.family(Z, scen, fam, allids - tnf, allids)['labels']
            dres['families'][fam] = res
            if d in GAP:
                labs[fam][d] = res['labels']
        out['directions'][d] = dres
    out['multi_direction'] = {fam: {k: K.multi_direction(labs[fam], k, 'expected' if not k.startswith('delivery') else 'multi_scenario')
                                    for k in next(iter(labs[fam].values()))} for fam in labs}
    return out


def main(run_dir, out_path):
    ver, recs = load(run_dir)
    assert len(recs) == 48
    res = analyse(recs)
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256']}
    with open(out_path, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    r2 = lambda v: round(v, 3) if isinstance(v, float) else v   # noqa: E731
    print('signed-zero', res['signed_zero_exceptions'], 'oracle', res['oracle_max'])
    print('multi', json.dumps(res['multi_direction']))
    for d, x in res['directions'].items():
        print(d, {a: (s['Y'], s['stop_first'], r2(s['G_mean']), r2(s['M_tnf_mean'])) for a, s in x['arm_summary'].items()})
        for fam, p in x['families'].items():
            b0, b1 = p['backgrounds']
            e = p['effects']
            print('  ', fam, p['labels'])
            for bg in (b0, b1):
                print('      ', bg, 'G W/K', r2(e[f'G|{bg}|W']['eq']), r2(e[f'G|{bg}|K']['eq']), 'M W/K', r2(e[f'M|{bg}|W']['eq']), r2(e[f'M|{bg}|K']['eq']),
                      'Y W/K', p['delivery'][f'{bg}|W']['net'], p['delivery'][f'{bg}|K']['net'], 'ratioM', {k: r2(v) for k, v in p['ratios'][f'M|{bg}'].items()},
                      'ratioG', {k: r2(v) for k, v in p['ratios'][f'G|{bg}'].items()})
            print('       I', {k: (r2(v['eq']), v['label']) if isinstance(v, dict) else v for k, v in p['interaction'].items()})


if __name__ == '__main__':
    main(*sys.argv[1:3])
