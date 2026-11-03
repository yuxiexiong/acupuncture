"""NQK-01 consumer (CPU).  python nqk_analysis.py RUN_DIR OUT_JSON [--stage formal|preflight]
Per needle: CQK and CVSK (this run) against the receiver C, with error types and per-input pairing against the same input's native T
(this run, bridged) and CJ / CS / CV / CK (NSR-01 formal records).  No ratios, no labels."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import nqk_core as NQ  # noqa: E402

NS, NCC = NQ.NS, NQ.NCC
NEEDLES = ('N_L00_C4146_D-1', 'N_L12_C3621_D-1')
NSR_FORMAL = HERE.parent / 'cache-native-s-reverse-v1-2026-11-03/runs/formal-r01'


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


def flat(x):
    return {**x, 'text': x['N']['text']}


def analyse(recs, nsr):
    ids = sorted(recs)
    scen = {i: recs[i]['scenario'] for i in ids}
    draws = NCC.boot_draws(ids, scen)
    assert all(recs[i]['nsr_record_sha256'] == nsr[i]['_sha'] for i in ids), 'NSR provenance'
    R = {'C': {i: flat(recs[i]['results']['C']) for i in ids}}
    out = {'n': len(ids), 'C': NS.arm_block(R, 'C', 'C', ids, scen, draws), 'needles': {}}
    for d in NEEDLES:
        for a in ('T', 'CQK', 'CVSK'):
            R[(d, a)] = {i: flat(recs[i]['results'][d][a]) for i in ids}
        for a in ('CS', 'CV', 'CK', 'CJ'):
            R[(d, a)] = {i: flat(nsr[i]['results'][d][a]) for i in ids}
        assert all(R[(d, 'T')][i]['N']['ids'] == nsr[i]['results'][d]['T']['N']['ids'] for i in ids), ('T != NSR-01', d)
        blk = {a: NS.arm_block(R, (d, a), 'C', ids, scen, draws) for a in ('T', 'CQK', 'CVSK', 'CS', 'CV', 'CK', 'CJ')}
        blk['pairing'] = {a: NQ.pairing(R, (d, a), {'T': (d, 'T'), 'CJ': (d, 'CJ')}, ids) for a in ('CQK', 'CVSK')}
        blk['type_overlap'] = {a: {'T': NS.type_overlap(blk[a]['types'], blk['T']['types']), 'CJ': NS.type_overlap(blk[a]['types'], blk['CJ']['types'])}
                               for a in ('CQK', 'CVSK')}
        blk['CJ_broken_explained'] = {'by_CQK': sum(1 for i in ids if R[(d, 'CJ')][i]['Y'] == 0 and R[(d, 'CQK')][i]['Y'] == 0),
                                      'by_CVSK': sum(1 for i in ids if R[(d, 'CJ')][i]['Y'] == 0 and R[(d, 'CVSK')][i]['Y'] == 0),
                                      'by_either': sum(1 for i in ids if R[(d, 'CJ')][i]['Y'] == 0 and (R[(d, 'CQK')][i]['Y'] == 0 or R[(d, 'CVSK')][i]['Y'] == 0)),
                                      'by_neither': sum(1 for i in ids if R[(d, 'CJ')][i]['Y'] == 0 and R[(d, 'CQK')][i]['Y'] == 1 and R[(d, 'CVSK')][i]['Y'] == 1),
                                      'n_CJ_broken': sum(1 for i in ids if R[(d, 'CJ')][i]['Y'] == 0)}
        out['needles'][d] = blk
    return out


def main(run_dir, out_path, stage='formal'):
    ver, recs = load_run(run_dir, stage)
    assert len(recs) == (48 if stage == 'formal' else 2)
    _, nsr = load_run(NSR_FORMAL)
    nsr = {i: nsr[i] for i in recs}
    res = analyse(recs, nsr)
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256'], 'stage': stage}
    with open(out_path, 'x') as fh:
        fh.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    r2 = lambda v: round(v, 2) if isinstance(v, float) else v   # noqa: E731
    print('C', res['C']['Y'])
    for d, b in res['needles'].items():
        print('==', d)
        for a in ('T', 'CQK', 'CVSK', 'CJ'):
            print(f'  {a}: Y', b[a]['Y'], 'types', b[a]['types'], 'broken scen', b[a]['vs_C']['n_scen_broken'], 'dB', r2(b[a]['dB_vs_C']['eq']), 'cat', b[a]['categories'])
        for a in ('CQK', 'CVSK'):
            p = b['pairing'][a]
            print(f'  pair {a}: broken', p['n_broken'], 'T', {k: v for k, v in p['T'].items()}, 'CJ', {k: v for k, v in p['CJ'].items()})
        print('  CJ broken explained', b['CJ_broken_explained'], 'overlap', {a: {k: r2(v) for k, v in x.items()} for a, x in b['type_overlap'].items()})


if __name__ == '__main__':
    stage = sys.argv[sys.argv.index('--stage') + 1] if '--stage' in sys.argv else 'formal'
    main(sys.argv[1], sys.argv[2], stage)
