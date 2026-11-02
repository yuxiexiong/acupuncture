"""KRD-01 consumer (CPU).  python krd_analysis.py RUN_DIR OUT_JSON"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'cache-query-state-transfer-v1-2026-11-02'))
import krd_core as K  # noqa: E402
import qst_core as QK  # noqa: E402

DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'N_L00_C1343_D-1')
GAP = DIRECTIONS[:3]
UNORDERED = (('Rk', 'V'), ('Ak', 'F'), ('Rrk', 'V'), ('Ark', 'F'))
ORDERED = tuple(x for a, b in UNORDERED for x in ((a, b), (b, a)))
CELLS = ('10', '01', '11')


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
    out = {'n': len(recs), 'n_target_not_first': len(tnf), 'directions': {}}
    for d in DIRECTIONS:
        R = {i: recs[i]['directions'][d] for i in recs}
        M00 = {a: {i: R[i]['C00'][a]['M'] for i in recs} for a in ('V', 'F', 'Rk', 'Ak', 'Rrk', 'Ark')}
        Y00 = {a: {i: yf(R[i]['N00'][a], recs[i]['item']) for i in recs} for a in M00}
        dres = {'Y00': {a: sum(v.values()) for a, v in Y00.items()}, 'pairs': {}}
        deltas = {}
        for r_, d_ in ORDERED:
            pk = f'{r_}<-{d_}'
            Mc = {c: {i: R[i]['cells'][f'{pk}|{c}']['C']['M'] for i in recs} for c in CELLS}
            Yc = {c: {i: yf(R[i]['cells'][f'{pk}|{c}']['N'], recs[i]['item']) for i in recs} for c in CELLS}
            unreached = sum(1 for i in recs if not R[i]['cells'][f'{pk}|11']['N']['reached_t2'])
            same_x = {i for i in recs if R[i]['x'][r_] == R[i]['x'][d_]}
            pres = {'unreached_N': unreached, 'n_same_first_token': len(same_x), 'cells': {}}
            for c in CELLS:
                tr = K.transfer(M00[r_], M00[d_], Mc[c], scen, tnf)
                tr_first = K.transfer(M00[r_], M00[d_], Mc[c], scen, allids - tnf)
                dl = K.delivery(Y00[r_], Y00[d_], Yc[c], tr)
                dl_same = K.delivery({i: Y00[r_][i] for i in same_x}, {i: Y00[d_][i] for i in same_x}, {i: Yc[c][i] for i in same_x}, tr)
                trans = {}
                for i in recs:
                    k_ = f'{Y00[r_][i]}->{Yc[c][i]}'
                    trans[k_] = trans.get(k_, 0) + 1
                pres['cells'][c] = {'M_tnf': tr, 'M_target_first': tr_first, 'Y': dl, 'Y_same_first_token': dl_same, 'Y_transitions': trans,
                                    'Y_total': sum(Yc[c].values())}
                deltas[(pk, c)] = {i: Mc[c][i] - M00[r_][i] for i in tnf}
            ym = {'00': Y00[r_], **Yc}
            mm = {'00': M00[r_], **Mc}
            g = pres['cells']['11']['M_tnf']['g']
            pres['interaction_M'] = K.interaction(mm, sorted(tnf), g=g)
            pres['interaction_Y'] = K.interaction(ym, sorted(allids), binary=True)
            dres['pairs'][pk] = pres
        for (r_, d_), (rr, rd) in K.RANDOM_OF.items():
            pk, pr = f'{r_}<-{d_}', f'{rr}<-{rd}'
            for c in CELLS:
                dres['pairs'][pk]['cells'][c]['specificity'] = K.specificity(dres['pairs'][pk]['cells'][c]['M_tnf'], deltas[(pk, c)], deltas[(pr, c)], scen)
        if d in GAP:
            p1 = {}
            for pk in ('Rk<-V', 'V<-Rk'):
                c11 = dres['pairs'][pk]['cells']['11']
                p1[pk] = bool(c11['M_tnf']['transfer'] and c11['Y']['support'])
            dres['P1'] = {'pairs': p1, 'holds': all(p1.values())}
            dres['P2_Rk_V'] = K.p2(dres['pairs']['Rk<-V']['cells']['11']['M_tnf'].get('ratio'), dres['pairs']['V<-Rk']['cells']['11']['M_tnf'].get('ratio'))
            dres['P2_Ak_F'] = K.p2(dres['pairs']['F<-Ak']['cells']['11']['M_tnf'].get('ratio'), dres['pairs']['Ak<-F']['cells']['11']['M_tnf'].get('ratio'))
        out['directions'][d] = dres
    return out


def main(run_dir, out_path):
    ver, recs = load(run_dir)
    assert len(recs) == 48
    res = analyse(recs)
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256']}
    with open(out_path, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    r2 = lambda v: round(v, 3) if isinstance(v, float) else v   # noqa: E731
    for d, x in res['directions'].items():
        print(d, 'Y00', x['Y00'], 'P1', x.get('P1'), 'P2', x.get('P2_Rk_V', {}).get('label'), x.get('P2_Ak_F', {}).get('label'))
        for pk, p in x['pairs'].items():
            print('  ', pk, 'unreached', p['unreached_N'], 'IntM', r2(p['interaction_M']['mean']), p['interaction_M']['practical'], 'IntY', p['interaction_Y']['sum'])
            for c, v in p['cells'].items():
                m = v['M_tnf']
                print('      ', c, m['label'], 'g', r2(m['g']), 'mean', r2(m['mean_delta']), 'ratio', r2(m.get('ratio')), 'scen', m.get('n_scen_same'),
                      '| Y', v['Y']['label'], 'net', v['Y']['net'], 'gap', v['Y']['gap_count'], '| spec', v.get('specificity', {}).get('label'))


if __name__ == '__main__':
    main(*sys.argv[1:3])
