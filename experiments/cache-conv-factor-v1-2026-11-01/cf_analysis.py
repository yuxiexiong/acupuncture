"""CFM-CONV-FACTOR v1 analysis (plan r2 §5.2, §6.1, §6.2). Records only.

python cf_analysis.py RUN_DIR OUT_JSON
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cf_core as K  # noqa: E402

PRIMARY = ('cz_a', 'cz_s46')
DERIVED = ('s46_minus_a', 'think_minus_a', 's44_minus_a', 's46_minus_think', 'D')
BGS = ('M_T', 'M_C', 'N')
RANDOM_BASE = {'M_T': ('M', 'M:TTT'), 'N': ('N', 'N:TT')}
PART_CELL = {('M_T', 'Q'): 'M:TCT', ('M_T', 'V'): 'M:TTC', ('N', 'Q'): 'N:CT', ('N', 'V'): 'N:TC'}


def per_item_values(rec, m):
    return {cid: K.value(c['readout'], m) for cid, c in rec['cells'].items() if 'readout' in c}


def analyse(records):
    by = {r['item']['id']: r for r in records}
    assert len(by) == 12
    scen_of = {i: r['item']['base_id'] for i, r in by.items()}
    out = {'readouts': {}, 'hypotheses': {}, 'random': {}, 'calibration': {}, 'rule': K.RULE}
    for m in PRIMARY + DERIVED:
        Z = {i: per_item_values(r, m) for i, r in by.items()}
        fx = {bg: {i: K.factorial(Z[i], bg) for i in by} for bg in BGS}
        sc = {bg: {k: K.scen_mean({i: fx[bg][i][k] for i in by}, scen_of) for k in ('G', 'A_V', 'R_V', 'A_Q', 'R_Q', 'I')}
              for bg in BGS}
        eff = {bg: {s: {k: sc[bg][k][s] for k in sc[bg]} for s in sc[bg]['G']} for bg in BGS}
        out['readouts'][m] = {'per_item': fx, 'scenario': eff,
                              'cells_scenario': {cid: K.scen_mean({i: Z[i][cid] for i in by}, scen_of) for cid in Z[next(iter(by))]}}
        if m in PRIMARY:
            out['hypotheses'][m] = {bg: {'H_V': K.material_dominance(eff[bg], 'V'), 'H_Q': K.material_dominance(eff[bg], 'Q'),
                                         'H_add': K.additivity(eff[bg])} for bg in BGS}
            for bg, (_, base) in RANDOM_BASE.items():
                pfx = 'M' if bg == 'M_T' else 'N'
                for part in ('Q', 'V'):
                    per = {}
                    for i in by:
                        z = Z[i]
                        per[i] = {'G': fx[bg][i]['G'], 'R': z[base] - z[PART_CELL[bg, part]],
                                  'R0': z[base] - z[f'{pfx}:R{part}0'], 'R1': z[base] - z[f'{pfx}:R{part}1']}
                    out['random'][f'{bg}|{part}|{m}'] = {**K.random_rule(per, scen_of), 'per_item': per}
        if m == 'D':
            out['hypotheses']['H_transfer_D'] = K.transfer(sc['N']['G'], sc['M_T']['G'])
            cal = {}
            for i in by:
                z = Z[i]
                tot = z['N:TT'] - z['C']
                cal[i] = {'d_share': (z['D_step'] - z['C']) / tot, 'interaction_share': (z['N:TT'] - z['M:TTT'] - z['D_step'] + z['C']) / tot}
            sd = K.scen_mean({i: z['D_step'] - Z[i]['C'] for i, z in Z.items()}, scen_of)
            st = K.scen_mean({i: z['N:TT'] - Z[i]['C'] for i, z in Z.items()}, scen_of)
            si = K.scen_mean({i: z['N:TT'] - z['M:TTT'] - z['D_step'] + z['C'] for i, z in Z.items()}, scen_of)
            scen = {s: {'d_share': sd[s] / st[s], 'interaction_share': si[s] / st[s]} for s in sd}
            out['calibration'] = {'per_item': cal, 'scenario': scen, 'expected': {'d_share': [0.05, 0.25], 'abs_interaction_share_max': 0.2},
                                  'within_expected': {s: 0.05 <= v['d_share'] <= 0.25 and abs(v['interaction_share']) <= 0.2 for s, v in scen.items()}}
    labels = [v['label'] for v in out['random'].values()]
    out['random_stop'] = {'all_eight_fail': all(x != 'stable_exceed' for x in labels), 'labels': {k: v['label'] for k, v in out['random'].items()}}
    eos = {cid: sum(by[i]['cells'][cid]['readout']['eos'] for i in by) for cid in by[next(iter(by))]['cells'] if 'readout' in by[next(iter(by))]['cells'][cid]}
    out['eos_counts'] = eos
    return out


def load(run_dir):
    run_dir = Path(run_dir)
    recs = []
    for w in sorted(run_dir.glob('worker-*')):
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
    summary = {m: {bg: {h: v[h]['label'] for h in v} for bg, v in res['hypotheses'][m].items()} for m in PRIMARY}
    summary['H_transfer_D'] = res['hypotheses']['H_transfer_D']['label']
    summary['random'] = res['random_stop']
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
