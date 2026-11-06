"""NWC-01 r03 consumer (CPU).  python nwc_analysis.py RUN_DIR OUT_JSON [STAGE]"""
import hashlib
import json
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'cache-native-write-readout-v1-2026-11-05'))
import nwc_core as K  # noqa: E402
import nwr_core as NK  # noqa: E402  (frozen output categories)

DIRS3 = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1')
MAIN_DIRS = DIRS3[:2]
BASE = ('C', 'L00', 'L10', 'L11', 'D00', 'E00', 'D10') + K.RAND
EXTRA = ('DV', 'DX', 'D00h', 'DXh', 'D10h') + K.QNAT


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
            if r['panel'] == 'new':
                r['_tensor_path'] = str(w / r['tensor_file'])
                recs[r['text']] = r
    return ver, recs


def t2_class(nr, rec):
    if not nr.get('reached_t2', True):
        return 'unreached'
    t, ct, it = nr['ids'][1], rec['code_tokens'], rec['item']
    if t == ct[it['target']]:
        return 'target'
    if it['first_listed'] != it['target'] and t == ct[it['first_listed']]:
        return 'first_listed'
    if t in [ct[c] for c in it['listed_codes'] if c != it['target']]:
        return 'other_listed'
    return 'stop' if (nr['termination'] == 'stop' and len(nr['ids']) == 2) else 'other'


def patch_cosine(recs, d):
    """Cosine between the D00 patch vectors (all layers and heads concatenated) of stratum-N inputs: same situation, same family, other family."""
    try:
        import torch
        V = {i: torch.load(r['_tensor_path'], map_location='cpu')[f'patch|D00|{d}'].float().flatten() for i, r in recs.items() if r['stratum'] == 'N'}
    except Exception as e:                                         # tensors not available (e.g. records copied without tensors)
        return {'unavailable': repr(e)[:80]}
    out = {'same_situation': [], 'same_family': [], 'other_family': []}
    ids = sorted(V)
    for a in range(len(ids)):
        for b in range(a + 1, len(ids)):
            ra, rb = recs[ids[a]], recs[ids[b]]
            c = float(torch.dot(V[ids[a]], V[ids[b]]) / (V[ids[a]].norm() * V[ids[b]].norm()))
            k = 'same_situation' if ra['situation'] == rb['situation'] else ('same_family' if ra['scenario'] == rb['scenario'] else 'other_family')
            out[k].append(c)
    return {k: {'n': len(v), 'mean': st.mean(v), 'min': min(v), 'max': max(v)} for k, v in out.items() if v}


def analyse_dir(recs, d):
    meta = {i: (r['scenario'], r['situation'], r['stratum']) for i, r in recs.items()}
    nin = [i for i, r in recs.items() if r['stratum'] == 'N']
    D = {i: recs[i]['directions'][d] for i in recs}
    cat, sub = {}, {}
    for a in BASE + EXTRA:
        ids = nin if a in EXTRA else list(recs)
        cat[a], sub[a] = {}, {}
        for i in ids:
            nr = D[i]['arms'][a]['N']
            cat[a][i], sub[a][i] = NK.category(nr['text'], nr['termination'], recs[i]['item'], nr.get('reached_t2', True))
    Y = {a: {i: float(c == 'correct') for i, c in cs.items()} for a, cs in cat.items()}
    E = {a: {i: float(c == 'wrong_num') for i, c in cs.items()} for a, cs in cat.items()}
    M11 = {i: D[i]['arms']['L11']['C']['M'] for i in nin}
    dM = {a: K.fam_eq({i: D[i]['arms'][a]['C']['M'] - M11[i] for i in nin}, meta, 'N') for a in ('D00', 'E00', 'D10', 'DV', 'DX', 'D00h', 'DXh', 'D10h')}
    nq = len(D[nin[0]]['M_Qk'])
    dMk = [K.fam_eq({i: D[i]['M_Qk'][j] - M11[i] for i in nin}, meta, 'N') for j in range(nq)]
    dMn = [K.fam_eq({i: D[i]['M_Qn'][j] - M11[i] for i in nin}, meta, 'N') for j in range(nq)]
    ratio = st.median(D[i]['patch_norm']['DV'] / D[i]['patch_norm']['D10'] for i in nin)
    unreached = sum(1 for i in nin if not D[i]['reached_t2']) / len(nin)
    dec = K.decide(Y, E, meta, dM, dMk, ratio, unreached)
    counts = {a: {s: {k: sum(1 for i, c in cat[a].items() if c == k and meta[i][2] == s) for k in NK.CATS} for s in ('N', 'F')} for a in cat}
    subs = {a: {} for a in cat}
    for a in cat:
        for i, c in cat[a].items():
            if c == 'wrong_num':
                subs[a][sub[a][i]] = subs[a].get(sub[a][i], 0) + 1
    allmeta = {i: (m[0], m[1], 'A') for i, m in meta.items()}
    ya = {a: K.fam_eq(Y[a], allmeta, 'A') for a in ('L00', 'L11', 'D00', 'E00') + K.RAND}
    pooled = {'b': ya['L11'] - ya['L00'], 'l_D': ya['L11'] - ya['D00'], 'l_E': ya['L11'] - ya['E00'],
              'l_R': sum(ya['L11'] - ya[r] for r in K.RAND) / len(K.RAND)}
    sd = st.pstdev(dMk)
    desc = {'D10_among_Qk': {'rank_from_most_negative': 1 + sum(1 for x in dMk if x < dM['D10']), 'z': (dM['D10'] - st.mean(dMk)) / sd if sd > 0 else None,
                             'mean': st.mean(dMk), 'sd': sd, 'min': min(dMk), 'max': max(dMk)},
            'Qn': {'mean': st.mean(dMn), 'sd': st.pstdev(dMn), 'min': min(dMn), 'max': max(dMn), 'count_le_half_dM_D00': sum(1 for x in dMn if x <= 0.5 * dM['D00'])},
            'norms_median': {k: st.median(D[i]['patch_norm'][k] for i in nin) for k in ('D00', 'D10', 'DV', 'DX')},
            'pooled_abc': pooled, 'patch_cosine_D00': patch_cosine(recs, d),
            't2_class': {a: {k: sum(1 for i in nin if t2_class(D[i]['arms'][a]['N'], recs[i]) == k) for k in ('target', 'first_listed', 'other_listed', 'stop', 'other', 'unreached')}
                         for a in ('L11', 'D00', 'E00', 'D10', 'DV', 'DX', 'D00h', 'DXh', 'D10h')},
            'first_G_structure_ok': sum(1 for i in recs if all(D[i]['structure_t1'][next(iter(D[i]['structure_t1']))][k] for k in ('q', 'k', 'g', 'beta', 'S0')))}
    return {'decision': dec, 'counts': counts, 'wrong_num_sub': subs, 'dM_Qk': dMk, 'dM_Qn': dMn, 'descriptive': desc, 'unreached_frac': unreached}


def analyse(recs):
    out = {'n': len(recs), 'strata': {s: sum(1 for r in recs.values() if r['stratum'] == s) for s in ('N', 'F')}, 'directions': {d: analyse_dir(recs, d) for d in DIRS3}}
    lab = {d: {k: out['directions'][d]['decision'][k] for k in ('P12', 'P3', 'P4M', 'P4Y', 'P5', 'P6')} for d in DIRS3}
    out['labels'] = lab
    out['confirmation'] = 'confirmed_both_main_directions' if all(lab[d]['P12'] == 'holds' for d in MAIN_DIRS) else (
        'one_main_direction' if any(lab[d]['P12'] == 'holds' for d in MAIN_DIRS) else 'not_confirmed')
    out['err_max'] = max(r['err_max'] for r in recs.values())
    out['signed_zero_exceptions'] = sum(r['signed_zero_exceptions'] for r in recs.values())
    return out


def main(run_dir, out_path, stage='formal'):
    ver, recs = load(run_dir, stage)
    res = analyse(recs)
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256'], 'stage': stage}
    with open(out_path, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    r3 = lambda v: round(v, 3) if isinstance(v, float) else v   # noqa: E731
    print('n', res['n'], res['strata'], 'confirmation:', res['confirmation'])
    for d in DIRS3:
        x = res['directions'][d]
        q, dc = x['decision']['q'], x['decision']
        print(d, res['labels'][d])
        print('   b', r3(q['b']), 'l_D', r3(q['l_D']), 'l_E', r3(q['l_E']), 'l_R', r3(q['l_R']), 'e_D', r3(q['e_D']), 'e_R', r3(q['e_R']), '| l_D10', r3(q['l_D10']), 'l_DV', r3(q['l_DV']),
              'l_DX', r3(q['l_DX']), 'l_D00h', r3(q['l_D00h']), 'l_DXh', r3(q['l_DXh']), '| F:', r3(q['YF_L11']), '->', r3(q['YF_D00']))
        print('   dM', {k: r3(v) for k, v in dc['dM'].items()}, 'rho', r3(dc['rho']), '| P4M', dc['p4m_count'], '/40 upper', r3(dc['p4m_upper']), '| P4Y', dc['p4y_count'], '/20 upper', r3(dc['p4y_upper']), '| R>=half', dc['r_half_count'], '/10 upper', r3(dc['r_half_upper']),
              '| norm DV/D10', r3(dc['norm_ratio_DV']))
        print('   boot lo', {k: r3(v['lo']) for k, v in dc['boot'].items()})
        print('   Qk', {k: r3(v) for k, v in x['descriptive']['D10_among_Qk'].items()}, '| cos', x['descriptive']['patch_cosine_D00'])


if __name__ == '__main__':
    main(*sys.argv[1:4])
