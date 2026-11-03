"""NVB-01 consumer (CPU).  python nvb_analysis.py RUN_DIR OUT_JSON [--stage formal|preflight]"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'cache-query-state-transfer-v1-2026-11-02'))
import nvb_core as K  # noqa: E402
import qst_core as QK  # noqa: E402

DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'N_L00_C1343_D-1')
GAP = DIRECTIONS[:3]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(run_dir, stage):
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
    out = {'n': len(recs), 'n_target_not_first': len(tnf),
           'signed_zero_exceptions': sum(r['signed_zero_exceptions'] for r in recs.values()),
           'oracle_max': max(r['oracle_max'] for r in recs.values()), 'dserr_max': max(r['dserr_max'] for r in recs.values()),
           'rhoerr_max': max(r['rhoerr_max'] for r in recs.values()), 'directions': {}}
    for d in DIRECTIONS:
        D = {i: recs[i]['directions'][d] for i in recs}
        M = {c: {i: D[i]['cells'][c]['C']['M'] for i in recs} for c in K.MAIN}
        MR = [{b: {i: D[i]['random'][str(j)][b]['M'] for i in recs} for b in '01'} for j in range(K.K_DRAWS)]
        Y = {c: {i: yf(D[i]['cells'][c]['N'], recs[i]['item']) for i in recs} for c in K.MAIN}
        res = K.direction(M, MR, Y, scen, tnf)
        res['first16'] = K.direction(M, MR, Y, scen, set(recs) - tnf)['P'] if len(set(recs) - tnf) else None
        res['t1_stop'] = {c: sum(1 for i in recs if not D[i]['cells'][c]['N']['reached_t2']) for c in K.MAIN}
        res['x_ne_fF'] = {c: sum(1 for i in recs if D[i]['cells'][c]['x'] != D[i]['fF']) for c in K.MAIN}
        qc = [v for i in recs for v in D[i]['qk_cos_t2'].values()]
        res['qk_cos_t2_median'] = {k: sorted(x[k] for x in qc)[len(qc) // 2] for k in qc[0]}
        out['directions'][d] = res
    out['summary'] = K.summary(out['directions'], GAP)
    return out


def main(run_dir, out_path, stage='formal'):
    ver, recs = load(run_dir, stage)
    assert len(recs) == (48 if stage == 'formal' else 2)
    res = analyse(recs)
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256'], 'stage': stage}
    with open(out_path, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    r2 = lambda v: round(v, 3) if isinstance(v, float) else v   # noqa: E731
    print('signed-zero', res['signed_zero_exceptions'], 'oracle', res['oracle_max'], 'dserr', res['dserr_max'], 'rho', res['rhoerr_max'], res['summary'])
    for d, x in res['directions'].items():
        print(d, 'P', x['P'], 'R', x['R'], 'p', r2(x['p_rank']), 'rho', r2(x['rho_DS0_DF']), 'e', {k: r2(v) for k, v in x['e'].items()})
        print('    diffs', {k: (r2(v['eq']), v['label'], v['n_pos']) for k, v in x['diffs'].items()}, 'scen>all', x['scen_above_all_draws'])
        print('    random DS0 max/median', r2(max(x['random_DS0_draws'])), r2(sorted(x['random_DS0_draws'])[len(x['random_DS0_draws']) // 2]))
        print('    main', {k: (r2(v) if not isinstance(v, list) else (r2(min(v)), r2(max(v)))) for k, v in x['main_effects'].items()})
        print('    Y', x['Y'].get('totals'), {k: (v['net'], v['support']) for k, v in x['Y'].items() if isinstance(v, dict) and 'net' in v}, 'JS_c1', x['Y'].get('JS_c1'))
        print('    t1 stop', x['t1_stop'], 'qkcos', {k: r2(v) for k, v in x['qk_cos_t2_median'].items()}, 'first16', x['first16'])


if __name__ == '__main__':
    stage = sys.argv[sys.argv.index('--stage') + 1] if '--stage' in sys.argv else 'formal'
    main(sys.argv[1], sys.argv[2], stage)
