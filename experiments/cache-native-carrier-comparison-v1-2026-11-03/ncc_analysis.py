"""NCC-01 consumer (CPU).  python ncc_analysis.py RUN_DIR OUT_JSON [--stage formal|preflight]
Primary: natural full-correct Y over all 48 inputs per needle x arm (counts, changes vs T, gap to C).  Descriptive: first-step B and its
components, first-token categories, first-step stop.  Cross-needle: same-input paired differences of the arm effects.  No ratios, no labels."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ncc_core as NC  # noqa: E402

NEEDLES = ('N_L00_C4146_D-1', 'N_L12_C3621_D-1')
ARMS = ('T', 'TV', 'TS', 'TK', 'TJ')


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


def strip(x):
    return {k: v for k, v in x.items() if not k.startswith('_')}


def analyse(recs):
    ids = sorted(recs)
    scen = {i: recs[i]['scenario'] for i in ids}
    draws = NC.boot_draws(ids, scen)
    R = {('C', 'C'): {i: recs[i]['results']['C'] for i in ids}}
    for d in NEEDLES:
        for a in ARMS:
            R[(d, a)] = {i: recs[i]['results'][d][a] for i in ids}
    blocks = {d: NC.needle_block(R, d, ARMS, ids, scen, draws) for d in NEEDLES}
    out = {'n': len(ids), 'Y_C': sum(R[('C', 'C')][i]['Y'] for i in ids),
           'C_categories': {c: sum(1 for i in ids if R[('C', 'C')][i]['cat'] == c) for c in ('code', 'preamble', 'stop', 'other')},
           'needles': {d: strip(b) for d, b in blocks.items()},
           'cross_needle': NC.cross_needle(blocks[NEEDLES[0]], blocks[NEEDLES[1]], ARMS, ids, scen, draws)}
    c_ok = [i for i in ids if R[('C', 'C')][i]['Y'] == 1]
    out['C_correct_subset'] = {'n': len(c_ok), 'Y': {d: {a: sum(R[(d, a)][i]['Y'] for i in c_ok) for a in ARMS} for d in NEEDLES}}
    return out


def main(run_dir, out_path, stage='formal'):
    ver, recs = load_run(run_dir, stage)
    assert len(recs) == (48 if stage == 'formal' else 2)
    res = analyse(recs)
    res['source'] = {'run_dir': str(run_dir), 'freeze_sha256': ver['freeze_sha256'], 'stage': stage}
    with open(out_path, 'x') as fh:
        fh.write(json.dumps(res, ensure_ascii=False, indent=1) + '\n')
    r3 = lambda v: round(v, 3) if isinstance(v, float) else v   # noqa: E731
    print('Y_C', res['Y_C'], 'C categories', res['C_categories'])
    for d, b in res['needles'].items():
        print('==', d)
        print('  Y', b['Y_counts'], 'gap to C', b['gap_to_C'], 'first stop', b['first_stop'])
        print('  changes vs T', {a: (v['toward'], v['away'], v['net']) for a, v in b['changes_vs_T'].items()})
        print('  dB vs T', {a: (r3(v['eq']), [r3(x) for x in v['interval']], v['scen_pos']) for a, v in b['dB_vs_T'].items()})
        print('  categories', b['categories'])
    print('cross', {a: (r3(v['dY_L0_minus_L12']['eq']), r3(v['dB_L0_minus_L12']['eq'])) for a, v in res['cross_needle'].items()})


if __name__ == '__main__':
    stage = sys.argv[sys.argv.index('--stage') + 1] if '--stage' in sys.argv else 'formal'
    main(sys.argv[1], sys.argv[2], stage)
