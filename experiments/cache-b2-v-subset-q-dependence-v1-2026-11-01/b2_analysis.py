"""CFM-B2 analysis (plan §4-§5). Records only.

python b2_analysis.py RUN_DIR OUT_JSON
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import b2_core as K  # noqa: E402

SIDES = {'stop': 'cz_s46', 'answer': 'cz_a'}
B_KEYS = ('B_H1', 'B_H0', 'B_R0', 'B_R1')


def analyse(records):
    by = {r['item']['id']: r for r in records}
    assert len(by) == 12
    scen_of = {i: r['item']['base_id'] for i, r in by.items()}
    out = {'rule': K.RULE, 'primary': 'stop|B_H1', 'sides': {}}
    for side, m in SIDES.items():
        est = {i: K.estimands({c: r['cells'][c]['readout']['primary'][m] for c in K.CELLS}) for i, r in by.items()}
        judged = {b: K.judge(K.scen_pairs(est, scen_of, lambda e, b=b: e[b])) for b in B_KEYS}
        pairs = lambda f: K.scen_pairs(est, scen_of, f)   # noqa: E731
        ratios = {}
        for name, num, den in (('B_H1/L', 'B_H1', 'L'), ('B_H0/L', 'B_H0', 'L'), ('B_R0/L', 'B_R0', 'L'), ('B_R1/L', 'B_R1', 'L')):
            pn, pd = pairs(lambda e, k=num: e[k]), pairs(lambda e, k=den: e[k])
            ratios[name] = {s: K.ratio(pn[s], pd[s]) for s in pn}
        for name, num, den in (('B_H1/A_H(0,1)', 'B_H1', ('A_H', '01')), ('B_H0/A_H(0,0)', 'B_H0', ('A_H', '00')),
                               ('B_R0/A_R(0,0)', 'B_R0', ('A_R', '00')), ('B_R1/A_R(0,1)', 'B_R1', ('A_R', '01'))):
            pn, pd = pairs(lambda e, k=num: e[k]), pairs(lambda e, d=den: e[d[0]][d[1]])
            ratios[name] = {s: K.ratio(pn[s], pd[s]) for s in pn}
        scen_vals = {k: {s: K.mean_pair(v) for s, v in pairs(lambda e, k=k: e[k]).items()} for k in ('L', 'J') + B_KEYS}
        for grp in ('A_H', 'A_R', 'E'):
            for sub in est[next(iter(est))][grp]:
                scen_vals[f'{grp}({sub})'] = {s: K.mean_pair(v) for s, v in pairs(lambda e, g=grp, u=sub: e[g][u]).items()}
        out['sides'][side] = {'judged': judged, 'scenario_means': scen_vals, 'ratios': ratios, 'per_item': est}
    out['primary_decision'] = out['sides']['stop']['judged']['B_H1']['decision']
    out['eos'] = {c: sum(by[i]['cells'][c]['readout']['eos'] for i in by) for c in K.CELLS}
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
    print(json.dumps({side: {b: v['judged'][b]['decision'] for b in B_KEYS} for side, v in res['sides'].items()}
                     | {'primary': res['primary_decision']}, indent=2))


if __name__ == '__main__':
    main()
