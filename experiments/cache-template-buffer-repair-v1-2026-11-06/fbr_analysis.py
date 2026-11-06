"""FBR-01 consumer (CPU).  python fbr_analysis.py RUN_DIR OUT_JSON [STAGE]"""
import hashlib
import json
import statistics as st
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'cache-native-write-readout-v1-2026-11-05'))
import fbr_core as K  # noqa: E402
import nwr_core as NK  # noqa: E402  (frozen output categories)


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


def cluster_meta(recs):
    """Stage A (LVK new panel): one family, cluster = scenario.  Stage B records carry 'situation': family = scenario, cluster = situation."""
    if all(r.get('situation') for r in recs.values()):
        return {i: (r['scenario'], r['situation']) for i, r in recs.items()}
    return {i: ('A', r['scenario']) for i, r in recs.items()}


def analyse(recs):
    meta = cluster_meta(recs)
    dirs = list(next(iter(recs.values()))['directions'])
    out = {'n': len(recs), 'clean_correct': sum(1 for r in recs.values() if NK.category(r['clean']['N']['text'], r['clean']['N']['termination'], r['item'])[0] == 'correct'),
           'directions': {}}
    for d in dirs:
        cat, opened = {}, {}
        for a in K.ARMS:
            cat[a], opened[a] = {}, 0
            for i, r in recs.items():
                nr = r['directions'][d]['arms'][a]['N']
                cat[a][i] = NK.category(nr['text'], nr['termination'], r['item'], nr.get('reached_t2', True))[0]
                opened[a] += int(nr.get('reached_t2', True))
        Y = {a: {i: float(c == 'correct') for i, c in cs.items()} for a, cs in cat.items()}
        dec = K.decide(Y, meta)
        counts = {a: {k: sum(1 for c in cat[a].values() if c == k) for k in NK.CATS} for a in K.ARMS}
        B = [r['directions'][d]['buffers'] for r in recs.values()]
        buf = {k: st.median(b[k] for b in B) for k in ('cos_clean_qk', 'cos_clean_v', 'cos_damage_qk', 'cos_damage_v', 'norm_mean_minus_T', 'norm_own_minus_T', 'norm_mean_minus_own')}
        out['directions'][d] = {'decision': dec, 'counts': counts, 'first_step_open': opened, 'buffers_median': buf,
                                'rand_correct': [counts[r]['correct'] for r in K.RAND],
                                'rand_norm_err_max': max(r['directions'][d]['rand_norm_err_max'] for r in recs.values())}
    out['outcomes'] = {d: out['directions'][d]['decision']['outcome'] for d in dirs}
    return out


def main(run_dir, out_path, stage='formal'):
    ver, recs = load(run_dir, stage)
    res = analyse(recs)
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256'], 'stage': stage}
    with open(out_path, 'x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    r3 = lambda v: round(v, 3) if isinstance(v, float) else v   # noqa: E731
    print('n', res['n'], 'clean correct', res['clean_correct'], 'outcomes', res['outcomes'])
    for d, x in res['directions'].items():
        dc = x['decision']
        print(d, dc['outcome'], dc['labels'])
        print('   correct:', {a: x['counts'][a]['correct'] for a in K.ARMS[:8]}, '| random:', x['rand_correct'])
        print('   gain lower bounds:', {k: r3(v['lo']) for k, v in dc['boot'].items()}, '| random reaching half:', dc['rand_half_count'], 'upper', r3(dc['rand_half_upper']))
        print('   buffers:', {k: r3(v) for k, v in x['buffers_median'].items()})


if __name__ == '__main__':
    main(*sys.argv[1:4])
