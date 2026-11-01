"""C2 analysis (plan §4-5). Records only.  python c2_analysis.py RUN_DIR OUT_JSON"""
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import c2_core as K  # noqa: E402

READ = {'stop': 'cz_s46', 'answer': 'cz_a'}


def per_item(rec, d, m):
    z = lambda c: rec['cells'][f'{c}|{d}']['readout']['primary'][m]   # noqa: E731
    cc = z('N:CC')
    return {'F': z('N:CT') - cc, 'FIX': z('N:CFIX') - cc, 'H': z('N:CH') - cc, 'U': [z(f'N:CUF{j}') - cc for j in range(1, 5)]}


def analyse(records):
    by = {r['item']['id']: r for r in records}
    assert len(by) == 12
    scen_of = {i: r['item']['base_id'] for i, r in by.items()}
    out = {'rule': K.RULE, 'directions': {}}
    for d in K.DIRECTIONS:
        out['directions'][d] = {}
        for side, m in READ.items():
            rows = {i: per_item(r, d, m) for i, r in by.items()}
            groups = {}
            for i, v in sorted(rows.items()):
                groups.setdefault(scen_of[i], []).append(v)
            arms = {}
            for arm in ('FIX', 'H'):
                scen = {s: K.scenario_check(v, arm, K.SIGN[side]) for s, v in sorted(groups.items())}
                arms[arm] = {'scenarios': scen, **K.judge(scen)}
            out['directions'][d][side] = {'arms': arms, 'per_item': rows,
                                          'U_scen_mean': {s: statistics.mean(statistics.mean(f['U']) for f in v) for s, v in sorted(groups.items())}}
        out['directions'][d]['overlap_H_FIX'] = {i: r['selections'][d]['overlap_H_FIX'] for i, r in by.items()}
        out['directions'][d]['write_audit'] = {i: r['write_audits'][d] for i, r in by.items()}
    primary = {d: out['directions'][d]['stop']['arms']['FIX']['decision'] for d in K.DIRECTIONS}
    out['primary'] = primary
    out['prediction_random_directions_transfer'] = K.prediction(primary)
    first = next(iter(by.values()))
    out['eos'] = {k: sum(by[i]['cells'][k]['readout']['eos'] for i in by) for k in first['cells']}
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
    print(json.dumps({d: {side: {arm: v[side]['arms'][arm]['decision'] for arm in ('FIX', 'H')} for side in READ}
                      for d, v in res['directions'].items()} | {'prediction': res['prediction_random_directions_transfer']}, indent=1))


if __name__ == '__main__':
    main()
