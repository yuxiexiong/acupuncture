"""KHC-01 consumer (CPU).  python khc_analysis.py RUN_DIR OUT_JSON"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'cache-query-state-transfer-v1-2026-11-02'))
import khc_core as K  # noqa: E402
import qst_core as QK  # noqa: E402

DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'N_L00_C1343_D-1')
GAP = DIRECTIONS[:3]
ORDERED = ('Rk<-V', 'V<-Rk', 'Ak<-F', 'F<-Ak', 'Ark<-F', 'F<-Ark')
CELLS = ('00', '10', '01', '11')
KRD_READ = HERE.parent / 'cache-k-repair-dependence-v1-2026-11-03/analysis/krd-readouts-r02.json'


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
    krd = json.load(open(KRD_READ))
    out = {'n': len(recs), 'n_target_not_first': len(tnf), 'krd_readouts_sha256': sha(KRD_READ), 'directions': {}}
    for d in DIRECTIONS:
        R = {i: recs[i]['directions'][d] for i in recs}
        dres = {'pairs': {}}
        labels = {}
        for pk in ORDERED:
            M = {c: {i: R[i]['cells'][f'{pk}|{c}']['C']['M'] for i in recs} for c in CELLS}
            Y = {c: {i: yf(R[i]['cells'][f'{pk}|{c}']['N'], recs[i]['item']) for i in recs} for c in CELLS}
            res = K.classify(M, Y, scen, tnf)
            res['first16'] = K.classify(M, Y, scen, set(recs) - tnf)['label']
            res['Y_totals'] = {c: sum(Y[c].values()) for c in CELLS}
            res['unreached'] = sum(1 for i in recs if not R[i]['cells'][f'{pk}|11']['N']['reached_t2'])
            kc = krd['directions'][d]['pairs'][pk]['cells']
            res['krd_Qr_H_only_ratio'] = kc['10']['M_tnf'].get('ratio')
            res['krd_g'] = kc['11']['M_tnf']['g']
            res['h_over_g'] = res['h'] / res['krd_g'] if res['krd_g'] else None
            labels[pk] = res['label']
            dres['pairs'][pk] = res
        if d in GAP:
            dres['P1'] = K.p1(labels)
        dres['handover'] = K.handover(labels)
        dres['common_vs_random'] = {}
        for c_, r_ in (('Ak<-F', 'Ark<-F'), ('F<-Ak', 'F<-Ark')):
            a, b = dres['pairs'][c_], dres['pairs'][r_]
            ok = abs(a['h']) >= K.TH['h'] and abs(b['h']) >= K.TH['h']
            dres['common_vs_random'][f'{c_}|{r_}'] = {'comparable': ok, 'common': {'h': a['h'], 'pS': a['pS'], 'pKV': a['pKV'], 'label': a['label']},
                                                     'random': {'h': b['h'], 'pS': b['pS'], 'pKV': b['pKV'], 'label': b['label']}}
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
        print(d, 'P1', x.get('P1'), 'handover', x['handover'])
        for pk, p in x['pairs'].items():
            e = p['effects']
            print('  ', pk, p['label'], 'h', r2(p['h']), 'h/g', r2(p['h_over_g']), 'pS', r2(p['pS']), 'pKV', r2(p['pKV']),
                  'okS/KV/H', e['10']['ok'], e['01']['ok'], e['11']['ok'], 'Ynet S/KV/H', p['y']['10']['net'], p['y']['01']['net'], p['y']['11']['net'],
                  'Y', p['Y_totals'], 'IntM', r2(p['interaction']['M_mean']), p['interaction']['M_practical'], 'IntY', p['interaction']['Y_sum'],
                  'first16', p['first16'], 'KRD10', r2(p['krd_Qr_H_only_ratio']))


if __name__ == '__main__':
    main(*sys.argv[1:3])
