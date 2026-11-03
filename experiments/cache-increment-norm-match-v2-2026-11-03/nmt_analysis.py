"""NMT-01 consumer (CPU).  python nmt_analysis.py RUN_DIR OUT_JSON [--stage formal|preflight]
M of old cells / SIT cross cells: this run's bit-equal replays; Y of old cells: NVB formal records; Y of SIT cross cells: SIT formal records;
M and Y of new cells: this run.  Frozen readings: nmt_core.reading (CONTRACT §5)."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'cache-query-state-transfer-v1-2026-11-02'))
import nmt_core as NC  # noqa: E402

DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'N_L00_C1343_D-1')
GAP = DIRECTIONS[:3]
K_RND = 5
NVB_FORMAL = HERE.parent / 'cache-native-bridge-v1-2026-11-03/runs/formal-r01'
SIT_FORMAL = HERE.parent / 'cache-state-increment-transfer-v1-2026-11-03/runs/formal-r01'
FO_REF = HERE / 'readiness/first-order-ref-r01.json'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_run(run_dir, stage=None):
    ver = json.load(open(Path(run_dir) / 'verification.json'))
    assert ver['status'] == 'passed' and (stage is None or ver['stage'] == stage)
    recs = {}
    for w in sorted(Path(run_dir).glob('worker-*')):
        if not w.is_dir():
            continue
        rc = json.load(open(w / 'receipt.json'))
        for rel, dg in rc['record_hashes'].items():
            assert sha(w / rel) == dg, rel
            r = json.load(open(w / rel))
            r['_sha'] = dg
            recs[r['text']] = r
    return ver, recs


def yf(t, it):
    import qst_core as QK
    return int(QK.y_full(t['text'], t['termination'], it['target'], it['listed_codes'], it['question']))


def assemble(recs, nvb, sit, d, ids, yfun=yf):
    """M[(r, arm, b)][i], Y[(r, arm, b)][i]; arm 'Z' = B(r,0,b); '0' / '1' = increment from source 0 / 1 unscaled; 'UP', 'DN', 'UPG', 'RNDj'."""
    D = {i: recs[i]['directions'][d] for i in ids}
    assert all(D[i]['nvb_record_sha256'] == nvb[i]['_sha'] and D[i]['sit_record_sha256'] == sit[i]['_sha'] for i in ids), 'provenance'
    NV = {i: nvb[i]['directions'][d]['cells'] for i in ids}
    SV = {i: sit[i]['directions'][d]['new'] for i in ids}
    M, Y = {}, {}
    for r in '01':
        s = '1' if r == '0' else '0'
        for b in '01':
            M[(r, 'Z', b)] = {i: D[i]['old'][f'{r}0{b}']['M'] for i in ids}
            M[(r, r, b)] = {i: D[i]['old'][f'{r}1{b}']['M'] for i in ids}
            M[(r, s, b)] = {i: D[i]['cross'][f'{r}{s}{b}']['M'] for i in ids}
            Y[(r, 'Z', b)] = {i: yfun(NV[i][f'{r}0{b}']['N'], recs[i]['item']) for i in ids}
            Y[(r, r, b)] = {i: yfun(NV[i][f'{r}1{b}']['N'], recs[i]['item']) for i in ids}
            Y[(r, s, b)] = {i: yfun(SV[i][f'{r}{s}{b}']['N'], recs[i]['item']) for i in ids}
            for arm in ('UP', 'DN'):
                M[(r, arm, b)] = {i: D[i]['new'][f'{arm}|{r}|{b}']['C']['M'] for i in ids}
                Y[(r, arm, b)] = {i: yfun(D[i]['new'][f'{arm}|{r}|{b}']['N'], recs[i]['item']) for i in ids}
    for b in '01':
        M[('0', 'UPG', b)] = {i: D[i]['new'][f'UPG|0|{b}']['C']['M'] for i in ids}
        for j in range(K_RND):
            M[('0', f'RND{j}', b)] = {i: D[i]['new'][f'RND{j}|0|{b}']['C']['M'] for i in ids}
    stopped = {(r, b): {i for i in ids if not NV[i][f'{r}0{b}']['N']['reached_t2']} for r in '01' for b in '01'}
    for r in '01':
        for b in '01':
            for arm in ('UP', 'DN'):
                assert all((not D[i]['new'][f'{arm}|{r}|{b}']['N']['reached_t2']) == (i in stopped[(r, b)]) for i in ids), 'stop != receiver'
    return D, M, Y, stopped


def is_median(D, ids, arm):
    xs = sorted(D[i]['IS'][arm]['ratio_all'] for i in ids if D[i]['IS'][arm]['ratio_all'] is not None)
    cs = sorted(D[i]['IS'][arm]['cos_all'] for i in ids if D[i]['IS'][arm]['cos_all'] is not None)
    return {'ratio_median': xs[len(xs) // 2] if xs else None, 'cos_median': cs[len(cs) // 2] if cs else None}


def strip(x):
    return {k: v for k, v in x.items() if not k.startswith('_')}


def analyse(recs, nvb, sit, yfun=yf, fo=None):
    ids = sorted(recs)
    scen = {i: recs[i]['scenario'] for i in ids}
    tnf = sorted(i for i in ids if recs[i]['item']['target'] != recs[i]['item']['first_listed'])
    draws = {'main_tnf': NC.boot_draws(tnf, scen), 'all48': NC.boot_draws(ids, scen)}
    out = {'n': len(ids), 'n_target_not_first': len(tnf), 'eng_max': {k: max(recs[i]['eng'][k] for i in ids) for k in recs[ids[0]]['eng']},
           'first_order_reference': fo, 'directions': {}}
    extra = ('UPG',) + tuple(f'RND{j}' for j in range(K_RND))
    for d in DIRECTIONS:
        D, M, Y, stopped = assemble(recs, nvb, sit, d, ids, yfun)
        res = {}
        for sub, sids in (('main_tnf', tnf), ('all48', ids)):
            if not sids:
                continue
            dr = draws[sub]
            rb = {'0': NC.receiver_block(M, '0', scen, sids, dr, extra), '1': NC.receiver_block(M, '1', scen, sids, dr)}
            isd = {r: {arm: is_median(D, sids, arm) for arm in ('UP', 'DN')} for r in '01'}
            readings = {r: NC.reading(rb[r]['phi_up'], rb[r]['phi_dn'], isd[r]['UP']['ratio_median'], isd[r]['DN']['ratio_median']) for r in '01'}
            bg = {w: NC.background(rb['0'], rb['1'], scen, sids, dr, w) for w in ('phi_up', 'phi_dn')}
            res[sub] = {'receivers': {r: strip(rb[r]) for r in '01'}, 'readings': readings, 'background': bg, 'IS': isd,
                        'IS_secondary': {arm: is_median(D, sids, arm) for arm in extra}}
        res['Y'] = {r: NC.y_block(Y, r, ids, scen, stopped) for r in '01'}
        res['coef_median'] = {k: sorted(D[i]['coef'][k]['median'] if isinstance(D[i]['coef'][k], dict) else D[i]['coef'][k] for i in ids)[len(ids) // 2]
                              for k in D[ids[0]]['coef']}
        if fo and d in fo.get('values', {}):
            res['vs_first_order'] = {'actual': {r: {'phi_up': res['main_tnf']['receivers'][r]['phi_up']['phi'],
                                                    'phi_dn': res['main_tnf']['receivers'][r]['phi_dn']['phi']} for r in '01'},
                                     'reference': fo['values'][d]}
        out['directions'][d] = res
    out['summary'] = {r: {lab: sum(1 for d in GAP if out['directions'][d]['main_tnf']['readings'][r]['label'] == lab)
                          for lab in ('near_reference', 'insufficient', 'one_sided', 'overcompensation', 'partial', 'unscaled')} for r in '01'}
    out['summary']['background'] = {w: sum(1 for d in GAP if out['directions'][d]['main_tnf']['background'][w].get('label')) for w in ('phi_up', 'phi_dn')}
    return out


def main(run_dir, out_path, stage='formal'):
    ver, recs = load_run(run_dir, stage)
    assert len(recs) == (48 if stage == 'formal' else 2)
    _, nvb = load_run(NVB_FORMAL)
    _, sit = load_run(SIT_FORMAL)
    fo = json.load(open(FO_REF))
    fo['source_sha256'] = sha(FO_REF)
    res = analyse(recs, nvb, sit, fo=fo)
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256'], 'stage': stage}
    with open(out_path, 'x') as fh:
        fh.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    r3 = lambda v: round(v, 3) if isinstance(v, float) else v   # noqa: E731
    print('eng', {k: r3(v) for k, v in res['eng_max'].items()}, 'summary', res['summary'])
    for d, x in res['directions'].items():
        m = x.get('main_tnf')
        print('==', d)
        if not m:
            continue
        for r in '01':
            rb = m['receivers'][r]
            print(f'  r={r} D_src', r3(rb['D_src']['eq']), 'phi_up', r3(rb['phi_up']['phi']), [r3(v) for v in (rb['phi_up']['interval'] or [])],
                  'phi_dn', r3(rb['phi_dn']['phi']), [r3(v) for v in (rb['phi_dn']['interval'] or [])], '->', m['readings'][r], 'IS', m['IS'][r])
        print('  secondary r=0', {k: r3(v['phi']) for k, v in m['receivers']['0'].items() if k.startswith('phi_') and k not in ('phi_up', 'phi_dn')})
        print('  background', {w: (r3(v.get('diff')), v.get('label')) for w, v in m['background'].items()})
        print('  Y r=1', x['Y']['1']['fixed_b_count_diff'], 'H_Y', x['Y']['1']['H_Y'])


if __name__ == '__main__':
    stage = sys.argv[sys.argv.index('--stage') + 1] if '--stage' in sys.argv else 'formal'
    main(sys.argv[1], sys.argv[2], stage)
