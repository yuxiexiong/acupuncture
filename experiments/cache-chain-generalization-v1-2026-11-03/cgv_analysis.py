"""CGV-01 consumer (CPU).  python cgv_analysis.py RUN_DIR OUT_JSON"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'cache-query-state-transfer-v1-2026-11-02'))
import cgv_core as K  # noqa: E402
import qst_core as QK  # noqa: E402

L12 = 'N_L12_C3621_D-1'
L0_DIRS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1')
STOPS = (248044, 248046)


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
            recs[(r['kind'], r['text'])] = r
    return ver, recs


def yf(t, it):
    return int(QK.y_full(t['text'], t['termination'], it['target'], it['listed_codes'], it['question']))


def endpoint_tables(R, names, get):
    Z = {'G': {}, 'M': {}, 'Y': {}}
    for nm in names:
        Z['G'][nm] = {i: get(i, nm)['first']['G'] for i in R}
        Z['M'][nm] = {i: get(i, nm)['C']['M'] for i in R}
        Z['Y'][nm] = {i: yf(get(i, nm)['N'], R[i]['item']) for i in R}
    return Z


def reach(R, names, get):
    return {nm: {'stop_t1': sum(1 for i in R if get(i, nm)['N']['ids'][0] in STOPS), 'first_eq_f': sum(1 for i in R if get(i, nm)['x'] == R[i]['fF'])} for nm in names}


def reads_table(R, d, chain, pair, Z, recv, donor, sign, scen, tnf):
    Mc = {c: {i: R[i]['directions'][d]['reads'][chain][pair][c]['C']['M'] for i in R} for c in ('10', '01', '11')}
    Yc = {c: {i: yf(R[i]['directions'][d]['reads'][chain][pair][c]['N'], R[i]['item']) for i in R} for c in ('10', '01', '11')}
    res = K.read_pair(Mc, Yc, Z['M'][recv], Z['Y'][recv], Z['M'][donor], scen, tnf, sign)
    res['Y_totals'] = {'00': sum(Z['Y'][recv].values()), **{c: sum(Yc[c].values()) for c in Yc}}
    return res


def l_group(R, d, has_C, rand):
    scen = {i: R[i]['scenario'] for i in R}
    tnf = {i for i in R if R[i]['item']['target'] != R[i]['item']['first_listed']}
    allids = set(R)
    names = ['L00', 'L01', 'L10', 'L11'] + (['R01', 'R11'] if rand else [])
    get = lambda i, nm: R[i]['directions'][d]['endpoints'][nm]   # noqa: E731
    Z = endpoint_tables(R, names, get)
    if has_C:
        for k, v in endpoint_tables(R, ['C'], lambda i, nm: R[i]['directions']['C']).items():
            Z[k].update(v)
    out = {'n': len(R), 'n_tnf': len(tnf), 'Y_totals': {nm: sum(Z['Y'][nm].values()) for nm in Z['Y']}, 'reach': reach(R, names, get)}
    if has_C:
        out['needle_effect_C_to_L00'] = {'M': K.contrast(Z['M'], 'C', 'L00', scen, sorted(tnf), -1), 'G': K.contrast(Z['G'], 'C', 'L00', scen, sorted(allids), -1),
                                         'Y': K.ydiff(Z['Y']['C'], Z['Y']['L00'], scen, -1)}
    for r_, ids in (('M', sorted(tnf)), ('G', sorted(allids))):
        e0 = {i: Z[r_]['L01'][i] - Z[r_]['L00'][i] for i in ids}
        e1 = {i: Z[r_]['L11'][i] - Z[r_]['L10'][i] for i in ids}
        out[f'{r_}_write'] = {'e0': K.desc(e0, scen), 'e1': K.desc(e1, scen), 'vmain0': K.contrast(Z[r_], 'L00', 'L10', scen, ids),
                              'vmain1': K.contrast(Z[r_], 'L01', 'L11', scen, ids), 'I_local': K.desc({i: e1[i] - e0[i] for i in ids}, scen)}
    out['Y_write'] = {'e0': K.ydiff(Z['Y']['L00'], Z['Y']['L01'], scen), 'e1': K.ydiff(Z['Y']['L10'], Z['Y']['L11'], scen),
                      'vmain0': K.ydiff(Z['Y']['L00'], Z['Y']['L10'], scen)}
    out['triage_mu'] = K.triage(Z['M'], Z['Y'], 'L10', 'L11', scen, sorted(tnf))
    out['reads_mu'] = {'gain': reads_table(R, d, 'mu', 'gain', Z, 'L10', 'L11', 1, scen, tnf),
                       'withdraw': reads_table(R, d, 'mu', 'withdraw', Z, 'L11', 'L10', -1, scen, tnf)}
    if rand:
        out['triage_rand'] = K.triage(Z['M'], Z['Y'], 'L10', 'R11', scen, sorted(tnf))
        out['rand_write'] = {'M_e0': K.contrast(Z['M'], 'L00', 'R01', scen, sorted(tnf)), 'M_e1': K.contrast(Z['M'], 'L10', 'R11', scen, sorted(tnf)),
                             'Y_e1': K.ydiff(Z['Y']['L10'], Z['Y']['R11'], scen)}
        out['reads_rand'] = {'gain': reads_table(R, d, 'rand', 'gain', Z, 'L10', 'R11', 1, scen, tnf),
                             'withdraw': reads_table(R, d, 'rand', 'withdraw', Z, 'R11', 'L10', -1, scen, tnf)}
    if has_C:
        csub = {i for i in R if Z['Y']['C'][i] == 1}
        out['C_correct_subset'] = {'n': len(csub), 'I_local_M': K.desc({i: (Z['M']['L11'][i] - Z['M']['L10'][i]) - (Z['M']['L01'][i] - Z['M']['L00'][i]) for i in csub & tnf}, scen) if csub & tnf else None}
    return out


def g3c_group(R, d):
    scen = {i: R[i]['scenario'] for i in R}
    tnf = {i for i in R if R[i]['item']['target'] != R[i]['item']['first_listed']}
    names = ['A0', 'Amu', 'AR']
    Rw = {i: {**R[i], 'A0': R[i]['directions']['A0']} for i in R}
    get = lambda i, nm: Rw[i]['A0'] if nm == 'A0' else Rw[i]['directions'][d]['endpoints'][nm]   # noqa: E731
    Z = endpoint_tables(Rw, names, get)
    out = {'n': len(R), 'Y_totals': {nm: sum(Z['Y'][nm].values()) for nm in names}, 'reach': reach(Rw, names, get)}
    for nm in ('Amu', 'AR'):
        out[f'challenge_{nm}'] = {'M': K.contrast(Z['M'], 'A0', nm, scen, sorted(tnf), -1), 'G': K.contrast(Z['G'], 'A0', nm, scen, sorted(R), -1),
                                  'Y': K.ydiff(Z['Y']['A0'], Z['Y'][nm], scen, -1), 'triage': K.triage(Z['M'], Z['Y'], 'A0', nm, scen, sorted(tnf))}
    for chain, nm in (('mu', 'Amu'), ('rand', 'AR')):
        out[f'reads_{chain}'] = {'apply': reads_table(Rw, d, chain, 'apply', Z, 'A0', nm, -1, scen, tnf),
                                 'undo': reads_table(Rw, d, chain, 'undo', Z, nm, 'A0', 1, scen, tnf)}
    return out


def analyse(recs):
    out = {'acc': {k: max(r['acc'][k] for r in recs.values() if 'acc' in r) for k in ('oracle', 'ref11', 'rot_cos_err', 'rot_norm_err')}, 'groups': {}}
    g1 = {t: r for (k, t), r in recs.items() if k == 'g1'}
    g2 = {t: r for (k, t), r in recs.items() if k == 'g2'}
    g3 = {t: r for (k, t), r in recs.items() if k == 'g3c'}
    out['groups']['G1'] = {L12: l_group(g1, L12, True, False)}
    out['groups']['G2'] = {}
    for d in L0_DIRS:
        out['groups']['G2'][d] = l_group(g2, d, True, False)
        out['groups']['G2'][d]['by_scenario'] = {s: l_group({t: r for t, r in g2.items() if r['scenario'] == s}, d, True, s == 'GS01' and d == L0_DIRS[0])
                                                for s in ('GS01', 'GS02', 'GS03')}
    out['groups']['G3C'] = {d: g3c_group(g3, d) for d in L0_DIRS}
    return out


def main(run_dir, out_path):
    ver, recs = load(run_dir)
    res = analyse(recs)
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256']}
    with open(out_path, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    r2 = lambda v: round(v, 3) if isinstance(v, float) else v   # noqa: E731
    print('acc', res['acc'])
    def show_l(tag, g):
        ne = g.get('needle_effect_C_to_L00')
        print(tag, 'n', g['n'], 'Y', g['Y_totals'], 'reach', g['reach'])
        if ne:
            print('   needle C->L00: M', r2(ne['M']['eq']), ne['M']['descriptor'], 'G', r2(ne['G']['eq']), 'Y', ne['Y']['net'])
        w = g['M_write']
        print('   write M: e0', r2(w['e0']['eq']), 'e1', r2(w['e1']['eq']), 'vmain0', r2(w['vmain0']['eq']), 'I_local', r2(w['I_local']['eq']), w['I_local']['descriptor'],
              '| Y e1', g['Y_write']['e1']['net'], 'vmain0', g['Y_write']['vmain0']['net'], '| triage', g['triage_mu']['continue'])
        for pn, p in g['reads_mu'].items():
            e = p['effects']
            print('   read', pn, p['old_label_descriptor'], 'g', r2(p['g']), 'dM D/E/DE', r2(e['10']['eq']), r2(e['01']['eq']), r2(e['11']['eq']),
                  'D/DE', r2(p['D_over_DE']), 'DE/g', r2(p['DE_over_g']), 'Y', p['Y_totals'], 'net', {c: p['y'][c]['net'] for c in p['y']})
        if 'reads_rand' in g:
            rw = g['rand_write']
            print('   RAND write M e0', r2(rw['M_e0']['eq']), 'e1', r2(rw['M_e1']['eq']), 'Y e1', rw['Y_e1']['net'], 'triage', g['triage_rand']['continue'])
            for pn, p in g['reads_rand'].items():
                e = p['effects']
                print('   RAND read', pn, p['old_label_descriptor'], 'g', r2(p['g']), 'dM D/E/DE', r2(e['10']['eq']), r2(e['01']['eq']), r2(e['11']['eq']), 'Y', p['Y_totals'])
    show_l('G1 ' + L12, res['groups']['G1'][L12])
    for d, g in res['groups']['G2'].items():
        show_l('G2 ' + d, g)
        for s, gs in g['by_scenario'].items():
            show_l(f'   G2 {d} {s}', gs)
    for d, g in res['groups']['G3C'].items():
        print('G3C', d, 'Y', g['Y_totals'], 'reach', g['reach'])
        for nm in ('Amu', 'AR'):
            c = g[f'challenge_{nm}']
            print('   challenge', nm, 'M', r2(c['M']['eq']), c['M']['descriptor'], 'G', r2(c['G']['eq']), 'Y', c['Y']['net'], 'triage', c['triage']['continue'])
        for chain in ('mu', 'rand'):
            for pn, p in g[f'reads_{chain}'].items():
                e = p['effects']
                print('   read', chain, pn, p['old_label_descriptor'], 'g', r2(p['g']), 'dM D/E/DE', r2(e['10']['eq']), r2(e['01']['eq']), r2(e['11']['eq']),
                      'D/DE', r2(p['D_over_DE']), 'DE/g', r2(p['DE_over_g']), 'Y', p['Y_totals'])


if __name__ == '__main__':
    main(*sys.argv[1:3])
