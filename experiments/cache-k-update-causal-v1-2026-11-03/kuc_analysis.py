"""KUC-01 consumer (CPU).  python kuc_analysis.py RUN_DIR OUT_JSON"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'cache-query-state-transfer-v1-2026-11-02'))
import kuc_core as K  # noqa: E402
import qst_core as QK  # noqa: E402

DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'N_L00_C1343_D-1')
GAP = DIRECTIONS[:3]
FAMILIES = {'R': ('V', 'Rk'), 'A': ('F', 'Ak'), 'Z': ('F', 'Ark')}


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
    out = {'n': len(recs), 'n_target_not_first': len(tnf), 'signed_zero_exceptions': sum(r['signed_zero_exceptions'] for r in recs.values()),
           'oracle_max': max(r['oracle_max'] for r in recs.values()), 'directions': {}}
    fams_gap = {}
    for d in DIRECTIONS:
        R = {i: recs[i]['directions'][d] for i in recs}
        dres = {'Y_orig': {a: sum(yf(R[i]['orig'][a]['N'], recs[i]['item']) for i in recs) for a in ('V', 'F', 'Rk', 'Ak', 'Ark')}, 'families': {}}
        for fam, (bg, src) in FAMILIES.items():
            pick = lambda cell, i: R[i]['orig'][bg] if cell == '00' else (R[i]['orig'][src] if cell == 'orig' else R[i]['new'][f'{fam}{cell}'])   # noqa: E731
            M = {c: {i: pick(c, i)['C']['M'] for i in recs} for c in ('00', '10', '01', '11', 'orig')}
            Y = {c: {i: yf(pick(c, i)['N'], recs[i]['item']) for i in recs} for c in ('00', '10', '01', '11', 'orig')}
            res = K.family(M, Y, scen, tnf, K.EXPECT[fam])
            res['first16'] = K.family(M, Y, scen, set(recs) - tnf, K.EXPECT[fam])['label']
            res['Y_totals'] = {c: sum(Y[c].values()) for c in Y}
            res['unreached'] = {c: sum(1 for i in recs if not pick(c, i)['N']['reached_t2']) for c in ('10', '01', '11')}
            dres['families'][fam] = res
        if d in GAP:
            fams_gap[d] = dres['families']
        out['directions'][d] = dres
    out['P1'] = K.p1(fams_gap)
    return out


def main(run_dir, out_path):
    ver, recs = load(run_dir)
    assert len(recs) == 48
    res = analyse(recs)
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256']}
    with open(out_path, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    r2 = lambda v: round(v, 3) if isinstance(v, float) else v   # noqa: E731
    print('P1', res['P1'], 'signed-zero', res['signed_zero_exceptions'], 'oracle', res['oracle_max'])
    for d, x in res['directions'].items():
        print(d, 'Y_orig', x['Y_orig'])
        for fam, p in x['families'].items():
            e, y = p['effects'], p['y']
            print('  ', fam, p['label'], 'g1', r2(p['g1']), 'g_old', r2(p['g_old']), 'g1/g_old', r2(p['g1_over_g_old']), 'ratios', {k: r2(v) for k, v in p['cell_ratios'].items()},
                  '| M10/01/11', r2(e['10']['eq']), r2(e['01']['eq']), r2(e['11']['eq']), 'sup', e['10']['support'], e['01']['support'], e['11']['support'],
                  '| Ynet', y['10']['net'], y['01']['net'], y['11']['net'], 'Y', p['Y_totals'], '| IntM', r2(p['interaction']['M']), p['interaction']['M_practical'],
                  'IntY', p['interaction']['Y'], '| residue M', r2(p['residue']['M_tnf_eq']), 'Y', p['residue']['Y_orig_minus_11'], '| first16', p['first16'])


if __name__ == '__main__':
    main(*sys.argv[1:3])
