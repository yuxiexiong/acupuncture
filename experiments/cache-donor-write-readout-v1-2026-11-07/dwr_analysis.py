"""CPU consumer, frozen parser, all pairs and arms; no post-outcome threshold selection."""
import json
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import dwr_core as K
sys.path.insert(0, str(HERE.parent / 'cache-donor-write-bridge-v2-2026-11-07'))
import dwb_analysis as DA
A = DA.A


def analyse(recs, n_boot=10000, n_perm=2000):
    tables = {r: x['donors'] for r, x in recs.items()}
    clusters = {r: x['scenario'] for r, x in recs.items()}
    selfrow = {r: x['self_row'] for r, x in recs.items()}
    out = {'receivers': len(recs), 'scenarios': len(set(clusters.values())), 'directions': {}}
    for direction in K.DIRS:
        outputs, counts = {}, {}
        for arm in K.ARMS:
            outputs[arm] = {}
            counts[arm] = {'categories': {c: 0 for c in A.CATS}, 'truncated': 0, 'n': 0, 'by_donor_type': {}}
            for r, rec in recs.items():
                outputs[arm][r] = {}
                for d in tables[r]:
                    key = arm if arm == 'L11o' else arm + '|' + d['id']
                    nr = rec['directions'][direction][key]['N']
                    o = A.row_out(nr, rec['item'])
                    outputs[arm][r][d['id']] = o
                    c = counts[arm]
                    c['n'] += 1
                    c['categories'][A.bucket(o, selfrow[r])] += 1
                    c['truncated'] += int(nr['termination'] not in ('stop', 'first_step_stop'))
                    t = c['by_donor_type'].setdefault(d['type'], dict(n=0, self=0, row=0, key=0, first=0))
                    t['n'] += 1
                    for k, target in [('self', selfrow[r]), ('row', d['row']), ('key', d['key']), ('first', 0)]:
                        t[k] += int(o == target)
        result = K.evaluate(outputs, tables, clusters, selfrow, n_boot, n_perm)
        result['counts'] = counts
        result['identity_answers'] = {}
        for arm in ('C0', 'L00', 'L11o'):
            result['identity_answers'][arm] = sum(A.row_out((rec['once'] if arm == 'C0' else rec['directions'][direction])[arm]['N'], rec['item']) == selfrow[r] for r, rec in recs.items())
        out['directions'][direction] = result
    return out


def main(run_dir, target, stage='formal'):
    ver, recs = DA.load(run_dir, stage)
    assert len(recs) == (48 if stage == 'formal' else 6)
    res = analyse(recs)
    res['source'] = {'run_dir': str(run_dir), 'stage': stage, 'freeze_sha256': ver['freeze_sha256'],
                     'verification_sha256': DA.sha(Path(run_dir) / 'verification.json')}
    with open(target, 'x') as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
        f.write('\n')
    for d, v in res['directions'].items():
        print(d)
        for j, x in v['uses'].items():
            print(j, x['decision'], {k: x[k] for k in ('G','W','R')})


if __name__ == '__main__':
    main(*sys.argv[1:])
