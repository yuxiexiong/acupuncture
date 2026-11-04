"""NWR-01 r02 consumer (CPU).  python nwr_analysis.py RUN_DIR OUT_JSON"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import nwr_core as K  # noqa: E402

ARMS = ('C', 'L00', 'L10', 'L11', 'D00', 'E00', 'D10') + K.RAND
T2 = ('D00', 'E00', 'D10') + K.RAND


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


def t2_class(nr, rec):
    """Natural t2 output token: target / first_listed / other_listed second token, stop, other; 'unreached' if the receiver stopped at t1."""
    if not nr.get('reached_t2', True):
        return 'unreached'
    t = nr['ids'][1]
    ct, it = rec['code_tokens'], rec['item']
    if t == ct[it['target']]:
        return 'target'
    if it['first_listed'] != it['target'] and t == ct[it['first_listed']]:
        return 'first_listed'
    if t in [ct[c] for c in it['listed_codes'] if c != it['target']]:
        return 'other_listed'
    if nr['termination'] == 'stop' and len(nr['ids']) == 2:
        return 'stop'
    return 'other'


def analyse(recs):
    scen = {i: r['scenario'] for i, r in recs.items()}
    cat, sub, t2c = {a: {} for a in ARMS}, {a: {} for a in ARMS}, {a: {} for a in T2 + ('L11',)}
    for i, r in recs.items():
        for a in ARMS:
            nr = r['arms'][a]['N']
            cat[a][i], sub[a][i] = K.category(nr['text'], nr['termination'], r['item'], nr.get('reached_t2', True))
        for a in t2c:
            t2c[a][i] = t2_class(r['arms'][a]['N'], r)
    rates = K.rates(cat, scen)
    unreached = sum(1 for r in recs.values() if not r['reached_t2']) / len(recs)
    budget_D = sum(1 for r in recs.values() if r['arms']['D00']['N']['termination'] == 'budget') / len(recs)
    dec = K.decide(rates, unreached_frac=unreached, budget_frac_D=budget_D)
    tnf = [i for i, r in recs.items() if r['item']['target'] != r['item']['first_listed']]
    M = {a: {i: recs[i]['arms'][a]['C']['M'] for i in tnf} for a in T2 + ('L11',)}
    dM = {a: K.seq({i: M[a][i] - M['L11'][i] for i in tnf}, scen)[0] for a in T2}
    trans = {}
    for a in T2:
        tr = {}
        for i in recs:
            k = f"{cat['L11'][i]}->{cat[a][i]}"
            tr[k] = tr.get(k, 0) + 1
        trans[a] = dict(sorted(tr.items()))
    subs = {a: {} for a in ARMS}
    for a in ARMS:
        for i in recs:
            if cat[a][i] == 'wrong_num':
                subs[a][sub[a][i]] = subs[a].get(sub[a][i], 0) + 1
    st = {l: {k: sum(int(bool(r['structure_t1'][l][k])) for r in recs.values()) for k in ('q', 'k', 'g', 'beta', 'S0', 'v')} for l in next(iter(recs.values()))['structure_t1']}
    out = {'n': len(recs), 'direction': next(iter(recs.values()))['direction'], 'decision': dec, 'rates': rates, 'wrong_num_sub': subs,
           't2_class': {a: {k: sum(1 for v in t2c[a].values() if v == k) for k in ('target', 'first_listed', 'other_listed', 'stop', 'other', 'unreached')} for a in t2c},
           'transitions_from_L11': trans, 'dM_vs_L11_C_route_target_not_first': dM, 'scenario_bootstrap_descriptive': K.scen_boot(cat, scen),
           'first_token_ne_fF': {nm: sum(1 for r in recs.values() if r['x'][nm] != r['fF']) for nm in ('L10', 'L11')},
           'structure_t1_equal_counts': st, 'v_rel_diff_first_G': sorted(r['structure_t1'][next(iter(r['structure_t1']))]['v_rel_diff'] for r in recs.values())[len(recs) // 2],
           'signed_zero_exceptions': sum(r['signed_zero_exceptions'] for r in recs.values()), 'oracle_max': max(r['oracle_max'] for r in recs.values()),
           'rand_norm_err_max': max(r['rand_norm_err_max'] for r in recs.values()), 'categories': cat}
    return out


def main(run_dir, out_path, stage='formal'):
    ver, recs = load(run_dir, stage)
    res = analyse(recs)
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256'], 'stage': stage}
    with open(out_path, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    d = res['decision']
    r3 = lambda v: round(v, 3) if isinstance(v, float) else v   # noqa: E731
    print('n', res['n'], 'label', d['label'], {k: r3(d[k]) for k in ('b', 'l_D', 'l_E', 'l_R', 'e_D', 'e_E', 'e_R', 'l_D10', 'e_D10')})
    print('gates', d['gates'])
    for a in ARMS:
        print(f'  {a:4s}', 'Y', r3(res['rates'][a]['Y']), 'E', r3(res['rates'][a]['E']), res['rates'][a]['counts'], res['wrong_num_sub'][a])
    print('t2', res['t2_class'])
    print('dM', {k: r3(v) for k, v in res['dM_vs_L11_C_route_target_not_first'].items()})
    print('boot', {k: (r3(v['lo']), r3(v['hi'])) for k, v in res['scenario_bootstrap_descriptive'].items()})


if __name__ == '__main__':
    main(*sys.argv[1:4])
