"""SIT-01 consumer (CPU).  python sit_analysis.py RUN_DIR OUT_JSON [--stage formal|preflight]
Continuous read-outs only (CONTRACT §4).  M of the 8 old cells: this run's replay (bit-equal to NVB formal by gate); Y of the 8 old cells: the
NVB formal natural records (hash-verified; not re-run); M and Y of the 4 new cells: this run.  First-order references: NBR re-projection
(conditions in CONTRACT §4.3), recomputed here from the frozen JSON."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'cache-query-state-transfer-v1-2026-11-02'))
import sit_core as SC  # noqa: E402

DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'N_L00_C1343_D-1')
GAP = DIRECTIONS[:3]
NVB_FORMAL = HERE.parent / 'cache-native-bridge-v1-2026-11-03/runs/formal-r01'
NBR_REPROJECT = HERE.parent / 'cache-native-bridge-record-v1-2026-11-03/analysis/nbr-reproject-r01.json'


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


def nvb_records():
    out = {}
    for w in sorted(NVB_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        rc = json.load(open(w / 'receipt.json'))
        for rel, dg in rc['record_hashes'].items():
            assert sha(w / rel) == dg, rel
            r = json.load(open(w / rel))
            r['_sha'] = dg
            out[r['text']] = r
    return out


def first_order(path=NBR_REPROJECT):
    """NBR single-point first-order references g . (XI_s1 - XI_s0), layer totals; A0 with the receiver-0 reader at gradient cells 000 / 011,
    A1 with the receiver-1 reader at gradient cells 100 / 111.  Same construction for DS0 / DS1 (calibration rows)."""
    d = json.load(open(path))['directions']
    out = {}
    for dn, res in d.items():
        t = lambda k: sum(res[k])   # noqa: E731
        out[dn] = {'A0': {g: t(f'XI_s1_q0|{g}') - t(f'XI_s0_q0|{g}') for g in ('g000', 'g011')},
                   'A1': {g: t(f'XI_s1_q1|{g}') - t(f'XI_s0_q1|{g}') for g in ('g100', 'g111')},
                   'DS0': {g: t(f'XI_s0_q0|{g}') for g in ('g000', 'g011')},
                   'DS1': {g: t(f'XI_s1_q1|{g}') for g in ('g100', 'g111')}}
    return {'source_sha256': sha(path), 'values': out}


def yf(t, it):
    import qst_core as QK
    return int(QK.y_full(t['text'], t['termination'], it['target'], it['listed_codes'], it['question']))


def assemble(recs, nvb, d, ids, yfun=yf):
    """M[(r, s, b)][i], Y[(r, s, b)][i] with (r, '-', b) = B(r,0,b), (r, r, b) = B(r,1,b), (r, s != r, b) = new; stopped[(r, b)]."""
    D = {i: recs[i]['directions'][d] for i in ids}
    assert all(D[i]['nvb_record_sha256'] == nvb[i]['_sha'] for i in ids), 'NVB record provenance'
    NV = {i: nvb[i]['directions'][d]['cells'] for i in ids}
    M, Y = {}, {}
    for r in '01':
        s = '1' if r == '0' else '0'
        for b in '01':
            M[(r, '-', b)] = {i: D[i]['old'][f'{r}0{b}']['M'] for i in ids}
            M[(r, r, b)] = {i: D[i]['old'][f'{r}1{b}']['M'] for i in ids}
            M[(r, s, b)] = {i: D[i]['new'][f'{r}{s}{b}']['C']['M'] for i in ids}
            Y[(r, '-', b)] = {i: yfun(NV[i][f'{r}0{b}']['N'], recs[i]['item']) for i in ids}
            Y[(r, r, b)] = {i: yfun(NV[i][f'{r}1{b}']['N'], recs[i]['item']) for i in ids}
            Y[(r, s, b)] = {i: yfun(D[i]['new'][f'{r}{s}{b}']['N'], recs[i]['item']) for i in ids}
    stopped = {(r, b): {i for i in ids if not NV[i][f'{r}0{b}']['N']['reached_t2']} for r in '01' for b in '01'}
    for r in '01':
        s = '1' if r == '0' else '0'
        for b in '01':
            assert all((not D[i]['new'][f'{r}{s}{b}']['N']['reached_t2']) == (i in stopped[(r, b)]) for i in ids), 'stop status != receiver'
    return D, M, Y, stopped


def analyse(recs, nvb, yfun=yf, fo=None):
    ids = sorted(recs)
    scen = {i: recs[i]['scenario'] for i in ids}
    tnf = {i for i in ids if recs[i]['item']['target'] != recs[i]['item']['first_listed']}
    fo = first_order() if fo is None else fo
    out = {'n': len(ids), 'n_target_not_first': len(tnf), 'cast_err_max': max(recs[i]['cast_err_max'] for i in ids),
           'signed_zero_exceptions': sum(recs[i]['signed_zero_exceptions'] for i in ids), 'first_order_reference': fo, 'directions': {}}
    for d in DIRECTIONS:
        D, M, Y, stopped = assemble(recs, nvb, d, ids, yfun)
        res = {'main_tnf': SC.margins_block(M, scen, tnf), 'all48': SC.margins_block(M, scen, set(ids)),
               'first16': SC.margins_block(M, scen, set(ids) - tnf), 'Y': SC.y_block(Y, scen, ids, stopped)}
        for k in ('all48', 'first16'):
            if res[k]:
                res[k].pop('per_input', None)
        mt = res['main_tnf']
        f = fo['values'].get(d)
        if f and mt:
            res['vs_first_order'] = {'A0_actual': mt['A0']['eq'], 'A0_reference': f['A0'], 'A1_actual': mt['A1']['eq'], 'A1_reference': f['A1'],
                                     'DS0_actual': mt['H']['00']['eq'], 'DS0_reference': f['DS0'], 'DS1_actual': mt['H']['11']['eq'], 'DS1_reference': f['DS1']}
        first = D[ids[0]]['increment_stats']
        med = lambda xs: sorted(xs)[len(xs) // 2]   # noqa: E731
        res['increment_stats_median'] = {l: {k: med([D[i]['increment_stats'][l][k] for i in ids]) for k in first[l]} for l in first}
        res['first_token_ne_fF'] = {c: sum(1 for i in ids if D[i]['new'][c]['x'] != D[i]['fF']) for c in D[ids[0]]['new']}
        out['directions'][d] = res
    return out


def main(run_dir, out_path, stage='formal'):
    ver, recs = load(run_dir, stage)
    assert len(recs) == (48 if stage == 'formal' else 2)
    nvb = nvb_records()
    res = analyse(recs, nvb)
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256'], 'stage': stage}
    with open(out_path, 'x') as fh:
        fh.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    r2 = lambda v: (round(v, 3) if isinstance(v, float) else v)   # noqa: E731
    print('cast', res['cast_err_max'], 'signed-zero', res['signed_zero_exceptions'])
    for d, x in res['directions'].items():
        m = x['main_tnf']
        print('==', d)
        if m is None:
            continue
        print('  H', {k: (r2(v['eq']), v['scen_pos']) for k, v in m['H'].items()})
        for k in ('A0', 'A1', 'G'):
            print(f'  {k}', r2(m[k]['eq']), 'scen+', m[k]['scen_pos'], 'scen-', m[k]['scen_neg'], 'inp+/-', m[k]['inp_pos'], m[k]['inp_neg'],
                  'boot', [r2(v) for v in m[k]['boot95']])
        print('  ratios A0/G', r2(m['ratio_A0_G']), 'A1/G', r2(m['ratio_A1_G']))
        print('  per-b effects', {k: r2(v['eq']) for k, v in m['effects'].items()})
        if 'vs_first_order' in x:
            print('  first-order', {k: (r2(v) if not isinstance(v, dict) else {g: r2(w) for g, w in v.items()}) for k, v in x['vs_first_order'].items()})
        y = x['Y']
        print('  Y totals', y['totals'], 'H_Y', y['H_Y'], 'A0_Y', y['A0_Y'], 'A1_Y', y['A1_Y'])
        print('  Y live', {r: (v['n'], v['H_Y']) for r, v in y['receiver_live'].items()})


if __name__ == '__main__':
    stage = sys.argv[sys.argv.index('--stage') + 1] if '--stage' in sys.argv else 'formal'
    main(sys.argv[1], sys.argv[2], stage)
