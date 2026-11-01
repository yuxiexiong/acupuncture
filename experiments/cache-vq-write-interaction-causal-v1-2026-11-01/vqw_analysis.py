"""CFM-VQ-WRITE-L13-v1 analysis (plan r2 §5-§6). Records only (old corners are carried in each record from CONV).

python vqw_analysis.py RUN_DIR OUT_JSON
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import vqw_core as K  # noqa: E402

READS = ('cz_s46', 'cz_a')
DERIVED = ('D', 's46_minus_a')
BGS = ('M_T', 'N')
PRIMARY = ('N', 'cz_s46')


def val(ro, m):
    return ro['primary'][m] if m in ro['primary'] else ro['derived'][m]


def per_item(rec, bg, m):
    c, k = rec['corners_from_conv'][bg], rec['cells']
    z = {x: val(k[f'{bg}:{x}']['readout'], m) for x in ('R', 'DEL', 'RAND0', 'RAND1')}
    assert z['R'] == val(c['TT'], m), ('R readout differs from CONV TT', rec['item']['id'], bg, m)
    e = K.estimands(z['R'], z['DEL'], val(c['TC'], m), val(c['CT'], m), val(c['CC'], m))
    e['d_rand0'] = z['R'] - z['RAND0']
    e['d_rand1'] = z['R'] - z['RAND1']
    e['label'] = K.label(e['rho'], e['delta'])
    return e


def analyse(records):
    by = {r['item']['id']: r for r in records}
    assert len(by) == 12
    out = {'rule': K.RULE, 'primary': '|'.join(PRIMARY), 'groups': {}}
    for bg in BGS:
        for m in READS + DERIVED:
            items = {i: per_item(r, bg, m) for i, r in by.items()}
            scen = {}
            for i, e in items.items():
                scen.setdefault(by[i]['item']['base_id'], []).append(e)
            sc = {s: K.scenario_rule(v) for s, v in sorted(scen.items())}
            out['groups'][f'{bg}|{m}'] = {'per_item': items, 'scenario': sc, **K.combine(sc),
                                          'max_identity_residual': max(abs(e['identity_residual']) for e in items.values())}
    out['primary_result'] = out['groups']['|'.join(PRIMARY)]['label']
    out['eos'] = {f'{bg}:{c}': sum(by[i]['cells'][f'{bg}:{c}']['readout']['eos'] for i in by) for bg in BGS for c in ('R', 'DEL', 'RAND0', 'RAND1')}
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
    print(json.dumps({k: {'label': v['label'], 'n_support': v['n_support'], 'n_evaluable': v['n_evaluable']}
                      for k, v in res['groups'].items() if k.split('|')[1] in READS} | {'primary': res['primary_result']}, indent=2))


if __name__ == '__main__':
    main()
