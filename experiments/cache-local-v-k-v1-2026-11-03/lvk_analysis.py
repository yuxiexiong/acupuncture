"""LVK-01 consumer (CPU).  python lvk_analysis.py RUN_DIR OUT_JSON"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'cache-query-state-transfer-v1-2026-11-02'))
import lvk_core as K  # noqa: E402
import qst_core as QK  # noqa: E402

DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'N_L00_C1343_D-1')
GAP = DIRECTIONS[:3]
NVW_FORMAL = HERE.parent / 'cache-native-v-write-interaction-v1-2026-11-03/runs/formal-r01'


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


def nvw():
    out = {}
    for w in sorted(NVW_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        rc = json.load(open(w / 'receipt.json'))
        for rel, dg in rc['record_hashes'].items():
            assert sha(w / rel) == dg, rel
            r = json.load(open(w / rel))
            out[r['text']] = r
    return out


def yf(t, it):
    return int(QK.y_full(t['text'], t['termination'], it['target'], it['listed_codes'], it['question']))


def analyse(recs):
    nv = nvw()
    out = {'signed_zero_exceptions': sum(r['signed_zero_exceptions'] for r in recs.values()), 'oracle_max': max(r['oracle_max'] for r in recs.values()),
           'vmask_elements_differing': sum(r['vmask_elements_differing'] for r in recs.values()), 'panels': {}}
    for pn in ('old', 'new'):
        P = {i: r for i, r in recs.items() if r['panel'] == pn}
        assert len(P) == 48
        scen = {i: r['scenario'] for i, r in P.items()}
        tnf = {i for i, r in P.items() if r['item']['target'] != r['item']['first_listed']}
        allids = set(P)
        pres = {'n': 48, 'n_target_not_first': len(tnf), 'directions': {}}
        if pn == 'new':
            pres['C_clean_Y'] = sum(yf(r['directions']['C_clean']['N'], r['item']) for r in P.values())
        labs = {}
        for d in DIRECTIONS:
            arms = {i: dict(P[i]['directions'][d]['arms']) for i in P}
            if pn == 'old':
                for i in P:
                    na = nv[i]['directions'][d]['arms']
                    arms[i]['V'], arms[i]['VW'] = na['V'], na['RVW']
            names = list(next(iter(arms.values())))
            Z = {'G': {a: {i: arms[i][a]['first']['G'] for i in P} for a in names},
                 'M': {a: {i: arms[i][a]['C']['M'] for i in P} for a in names},
                 'Y': {a: {i: yf(arms[i][a]['N'], P[i]['item']) for i in P} for a in names}}
            res = K.panel_direction(Z, scen, tnf, allids, pn == 'new')
            res['first16'] = K.panel_direction(Z, scen, allids - tnf, allids, pn == 'new')['labels']
            res['stop_first'] = {a: sum(1 for i in P if arms[i][a]['N']['ids'][0] in (248044, 248046)) for a in names}
            pres['directions'][d] = res
            if d in GAP:
                labs[d] = res['labels']
        pres['multi_direction'] = {k: K.multi(labs, k, 'expected') for k in ('I_local_M', 'I_block_M')}
        if pn == 'new':
            pres['multi_direction']['kuc_replication'] = K.multi(labs, 'kuc_replication', 'single_W')
        out['panels'][pn] = pres
    return out


def main(run_dir, out_path):
    ver, recs = load(run_dir)
    assert len(recs) == 96
    res = analyse(recs)
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256']}
    with open(out_path, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    r2 = lambda v: round(v, 3) if isinstance(v, float) else v   # noqa: E731
    print('signed-zero', res['signed_zero_exceptions'], 'oracle', res['oracle_max'], 'vmask', res['vmask_elements_differing'])
    for pn, p in res['panels'].items():
        print('==', pn, 'multi', json.dumps(p['multi_direction']), 'C_clean_Y', p.get('C_clean_Y'))
        for d, x in p['directions'].items():
            M = x['M']
            print('  ', d, x['labels'], 'Gid', x['G_identity_max_abs'], 'Ytot', x['Y_totals'])
            print('      M e0/e1', r2(M['e0']['eq']), r2(M['e1']['eq']), 'vmain0/1', r2(M['vmain0']['eq']), r2(M['vmain1']['eq']), 'I_local', r2(M['I_local']['eq']),
                  'I_block', r2(M['I_block']['eq']), 'ratio', r2(M['ratio_local_over_block']), 'gap', r2(M['gap']['eq']), 'd0/d1', r2(M['d0']['eq']), r2(M['d1']['eq']))
            print('      Y', x['Y'], 'deliv', {k: (v['net'], v['label']) for k, v in x['delivery'].items()})
            if 'kuc_replication' in x:
                k = x['kuc_replication']
                print('      KUC rep', k['label'], 'W', r2(k['W']['eq']), 'E', r2(k['E']['eq']), 'K', r2(k['K']['eq']), 'W/K', r2(k['W_over_K']), 'YW', k['Y_W']['net'], 'F-V', r2(x['F_minus_V_M']['eq']))


if __name__ == '__main__':
    main(*sys.argv[1:3])
