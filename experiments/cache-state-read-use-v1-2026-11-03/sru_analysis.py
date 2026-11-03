"""SRU-01 consumer (CPU).  python sru_analysis.py RUN_DIR OUT_JSON"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'cache-query-state-transfer-v1-2026-11-02'))
import sru_core as K  # noqa: E402
import qst_core as QK  # noqa: E402

DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'N_L00_C1343_D-1')
GAP = DIRECTIONS[:3]
CELLS = ('00', '10', '01', '11')


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
    out = {'n': len(recs), 'signed_zero_exceptions': sum(r['signed_zero_exceptions'] for r in recs.values()),
           'oracle_max': max(r['oracle_max'] for r in recs.values()), 'ref11_max': max(r['ref11_max'] for r in recs.values()), 'directions': {}}
    nbi = 0
    for d in DIRECTIONS:
        D = {i: recs[i]['directions'][d] for i in recs}
        dres = {'pairs': {}, 'first_token_ne_fF': {nm: sum(1 for i in recs if D[i]['x'][nm] != D[i]['fF']) for nm in ('L10', 'L11')}}
        Mrec = {}
        for pn in ('gain', 'withdraw'):
            Mrec[pn] = {c: {i: D[i]['pairs'][pn][c]['C']['M'] for i in recs} for c in CELLS}
        for pn in ('gain', 'withdraw'):
            M = Mrec[pn]
            Y = {c: {i: yf(D[i]['pairs'][pn][c]['N'], recs[i]['item']) for i in recs} for c in CELLS}
            sel = {c: sum(1 for i in recs if D[i]['pairs'][pn][c]['N'].get('t2_token') == D[i]['target_second_token']) for c in CELLS}
            other = 'withdraw' if pn == 'gain' else 'gain'
            res = K.pair(M, Y, scen, tnf, pn, Mdonor00=Mrec[other]['00'])
            res['first16'] = K.pair(M, Y, scen, set(recs) - tnf, pn, Mdonor00=Mrec[other]['00'])['label']
            res['Y_totals'] = {c: sum(Y[c].values()) for c in CELLS}
            res['t2_selection_correct'] = sel
            dres['pairs'][pn] = res
        dres.update(K.direction(dres['pairs']))
        qk = [v for i in recs for v in D[i]['qk_cos_t2'].values()]
        dres['qk_cos_t2_median'] = {'q': sorted(x['q'] for x in qk)[len(qk) // 2], 'k': sorted(x['k'] for x in qk)[len(qk) // 2]}
        if d in GAP and dres['bidirectional_direct']:
            nbi += 1
        out['directions'][d] = dres
    out['multi_direction_bidirectional_direct'] = {'n': nbi, 'multi': nbi >= 2}
    return out


def main(run_dir, out_path):
    ver, recs = load(run_dir)
    assert len(recs) == 48
    res = analyse(recs)
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256']}
    with open(out_path, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    r2 = lambda v: round(v, 3) if isinstance(v, float) else v   # noqa: E731
    print('signed-zero', res['signed_zero_exceptions'], 'oracle', res['oracle_max'], 'ref11', res['ref11_max'], 'multi', res['multi_direction_bidirectional_direct'])
    for d, x in res['directions'].items():
        print(d, 'bidir', x['bidirectional_direct'], 'x!=fF', x['first_token_ne_fF'], 'qkcos', {k: r2(v) for k, v in x['qk_cos_t2_median'].items()})
        for pn, p in x['pairs'].items():
            e = p['effects']
            print('   ', pn, p['label'], 'g', r2(p['g']), 'dM10/01/11', r2(e['10']['eq']), r2(e['01']['eq']), r2(e['11']['eq']), 'r10', r2(p['r10']), 'r01', r2(p['r01']),
                  'd11/g', r2(p['d11_over_g']), '| Y', p['Y_totals'], 'net', {c: p['y'][c]['net'] for c in ('10', '01', '11')}, 'sel', p['t2_selection_correct'],
                  '| I_M', r2(p['I_M']), 'I_Y', p['I_Y'], 'first16', p['first16'])


if __name__ == '__main__':
    main(*sys.argv[1:3])
