"""C1-P analysis (plan §5 + r2 fixed arm). Records only.  python c1p_analysis.py RUN_DIR OUT_JSON"""
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import c1p_core as K  # noqa: E402

SIDES = {'stop': 'cz_s46', 'answer': 'cz_a'}


def per_item(rec, m):
    z = {k: v['readout']['primary'][m] for k, v in rec['cells'].items()}
    cc = z['N:CC']
    return {'F': z['N:CT'] - cc, 'H': z['N:CH'] - cc, 'FIX': z['N:CFIX'] - cc, 'U': [z[f'N:CU{j}'] - cc for j in range(1, 5)]}


def analyse(records):
    by = {r['item']['id']: r for r in records}
    assert len(by) == 12
    scen_of = {i: r['item']['base_id'] for i, r in by.items()}
    out = {'rule': K.RULE, 'sides': {}}
    for side, m in SIDES.items():
        rows = {i: per_item(r, m) for i, r in by.items()}
        groups = {}
        for i, v in sorted(rows.items()):
            groups.setdefault(scen_of[i], []).append(v)
        res = {}
        for arm in ('H', 'FIX'):
            scen = {s: K.scenario_check(v, arm) for s, v in sorted(groups.items())}
            res[arm] = {'scenarios': scen, **K.judge(scen)}
        out['sides'][side] = {'per_item': rows, 'arms': res,
                              'U_scen_mean': {s: statistics.mean(statistics.mean(f['U']) for f in v) for s, v in sorted(groups.items())}}
    out['primary_decision'] = out['sides']['stop']['arms']['H']['decision']
    out['eos'] = {k: sum(by[i]['cells'][k]['readout']['eos'] for i in by) for k in by[next(iter(by))]['cells']}
    out['overlap_with_H'] = {i: r['overlap'] for i, r in by.items()}
    return out


def load(run_dir):
    recs = []
    for w in sorted(Path(run_dir).glob('worker-*')):
        if w.is_dir():
            r = json.loads((w / 'receipt.json').read_text())
            assert r['status'] == 'completed'
            recs += [json.loads((w / rel).read_text()) for rel in sorted(r['record_hashes'])]
    return recs


def main():
    run_dir, outp = sys.argv[1], Path(sys.argv[2])
    ver = json.loads((Path(run_dir) / 'verification.json').read_text())
    assert ver['status'] == 'passed' and ver['stage'] == 'formal'
    res = analyse(load(run_dir))
    res['verification'] = ver
    outp.parent.mkdir(parents=True, exist_ok=True)
    with outp.open('x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({side: {arm: v['arms'][arm]['decision'] for arm in ('H', 'FIX')} for side, v in res['sides'].items()}
                     | {'primary': res['primary_decision']}, indent=2))


if __name__ == '__main__':
    main()
