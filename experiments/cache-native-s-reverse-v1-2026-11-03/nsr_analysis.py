"""NSR-01 consumer (CPU).  python nsr_analysis.py RUN_DIR OUT_JSON [--stage formal|preflight]
Primary: natural full-correct Y per arm (C receiver; CS/CV/CK/CJ per needle; CSx shared), changes relative to C, error types compared
type by type with the same needle's native T and with CSx (never by totals only).  Descriptive: first-step B change vs C, first-token
categories.  Cross-needle: same-input paired differences of the CS effect.  No ratios, no labels."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import nsr_core as NS  # noqa: E402

NCC = NS.NCC
NEEDLES = ('N_L00_C4146_D-1', 'N_L12_C3621_D-1')
ARMS = ('CS', 'CV', 'CK', 'CJ')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_run(run_dir, stage):
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


def analyse(recs):
    ids = sorted(recs)
    scen = {i: recs[i]['scenario'] for i in ids}
    draws = NCC.boot_draws(ids, scen)
    R = {'C': {i: recs[i]['results']['C'] for i in ids}, 'CSx': {i: recs[i]['results']['CSx'] for i in ids}}
    for d in NEEDLES:
        for a in ('T',) + ARMS:
            R[(d, a)] = {i: recs[i]['results'][d][a] for i in ids}
    out = {'n': len(ids), 'C': NS.arm_block(R, 'C', 'C', ids, scen, draws), 'CSx': NS.arm_block(R, 'CSx', 'C', ids, scen, draws), 'needles': {}}
    for d in NEEDLES:
        blk = {a: NS.arm_block(R, (d, a), 'C', ids, scen, draws) for a in ('T',) + ARMS}
        blk['type_overlap_with_T'] = {a: NS.type_overlap(blk[a]['types'], blk['T']['types']) for a in ARMS}
        blk['type_overlap_with_CSx'] = {a: NS.type_overlap(blk[a]['types'], out['CSx']['types']) for a in ARMS}
        blk['CS_minus_CSx_paired'] = NCC.describe({i: float(R[(d, 'CS')][i]['Y'] - R['CSx'][i]['Y']) for i in ids}, scen, ids, draws)
        out['needles'][d] = blk
    out['cross_needle_CS'] = NCC.describe({i: float(R[(NEEDLES[0], 'CS')][i]['Y'] - R[(NEEDLES[1], 'CS')][i]['Y']) for i in ids}, scen, ids, draws)
    return out


def main(run_dir, out_path, stage='formal'):
    ver, recs = load_run(run_dir, stage)
    assert len(recs) == (48 if stage == 'formal' else 2)
    res = analyse(recs)
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256'], 'stage': stage}
    with open(out_path, 'x') as fh:
        fh.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    r2 = lambda v: round(v, 2) if isinstance(v, float) else v   # noqa: E731
    for k in ('C', 'CSx'):
        print(k, 'Y', res[k]['Y'], 'types', res[k]['types'], 'vs C', res[k]['vs_C'])
    for d, b in res['needles'].items():
        print('==', d)
        for a in ('T',) + ARMS:
            print(f'  {a}: Y', b[a]['Y'], 'types', b[a]['types'], 'broken', b[a]['vs_C']['broken'], 'scen', b[a]['vs_C']['n_scen_broken'],
                  'dB', r2(b[a]['dB_vs_C']['eq']), 'cat', b[a]['categories'])
        print('  overlap T', {a: r2(v) for a, v in b['type_overlap_with_T'].items()}, 'overlap CSx', {a: r2(v) for a, v in b['type_overlap_with_CSx'].items()})
        print('  CS-CSx', r2(b['CS_minus_CSx_paired']['eq']), [r2(x) for x in b['CS_minus_CSx_paired']['interval']])
    print('cross CS', r2(res['cross_needle_CS']['eq']))


if __name__ == '__main__':
    stage = sys.argv[sys.argv.index('--stage') + 1] if '--stage' in sys.argv else 'formal'
    main(sys.argv[1], sys.argv[2], stage)
