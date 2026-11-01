"""CFM-LOCAL-READOUT v1 analysis (plan r3 §7-§8.1). Reads records only; no model, no tensors required.

python lr_analysis.py RUN_DIR OUT_JSON
"""
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lr_core as K  # noqa: E402

BGS = ('M', 'N')
DELS = ('mI', 'mJ', 'Q0', 'Q1')


def item_deltas(rec):
    """delta_X = D(R) - D(X) (positive: removing X lowers the stop advantage); same for fixed-pair L and fixed-scale L."""
    ro = rec['readout']
    out = {}
    for bg in BGS:
        r = ro[f'{bg}:R']
        d = {'gap': ro[f'{bg}:gap_to_C'], 'D_R': r['D'], 'eos_R': r['eos']}
        for x in DELS:
            c = ro[f'{bg}:{x}']
            d[x] = {'dD': r['D'] - c['D'], 'dL': r['L'] - c['L'], 'dL_fixscale': r['L'] - c['L_fixscale'],
                    'eos': c['eos'], 'eos_flip': c['eos'] != r['eos'], 'D': c['D'],
                    'D_L_sign_disagree': (r['D'] - c['D']) * (r['L'] - c['L']) < 0,
                    'decidable': rec['numerics'][f'{bg}:{x}']['decidable']}
        out[bg] = d
    return out


def analyse(records):
    by_item = {rec['item']['id']: rec for rec in records}
    assert len(by_item) == 12, len(by_item)
    scen_of = {i: r['item']['base_id'] for i, r in by_item.items()}
    deltas = {i: item_deltas(r) for i, r in by_item.items()}
    result = {'n_items': 12, 'n_scenarios': len(set(scen_of.values())), 'null_tail_e5': K.null_tail(), 'tier_rule': K.TIER,
              'per_item': deltas, 'backgrounds': {}}
    for bg in BGS:
        und = sorted(f'{i}:{x}' for i, d in deltas.items() for x in DELS if not d[bg][x]['decidable'])
        sm = {x: K.scenario_means({i: d[bg][x]['dD'] for i, d in deltas.items()}, scen_of) for x in DELS}
        gap = K.scenario_means({i: d[bg]['gap'] for i, d in deltas.items()}, scen_of)
        smL = {x: K.scenario_means({i: d[bg][x]['dL'] for i, d in deltas.items()}, scen_of) for x in DELS}
        smLf = {x: K.scenario_means({i: d[bg][x]['dL_fixscale'] for i, d in deltas.items()}, scen_of) for x in DELS}
        if any(u.split(':')[1] in ('mI', 'Q0', 'Q1') for u in und):
            ti = {'label': 'numerically_undecidable', 'cells': und}
        else:
            ti = K.tier_I(sm['mI'], sm['Q0'], sm['Q1'], gap)
        tj = {'label': 'numerically_undecidable', 'cells': und} if any(u.endswith(':mJ') for u in und) else K.tier_J(sm['mJ'], gap)
        loc = {i: r['local_components'][bg] for i, r in by_item.items()}
        cos = [v['cos_I_vs_AS_plus_AF'] for v in loc.values() if v['cos_I_vs_AS_plus_AF'] is not None]
        result['backgrounds'][bg] = {
            'tier_I': ti, 'tier_J': tj, 'undecidable_cells': und,
            'scenario_dD': sm, 'scenario_gap_to_C': gap, 'scenario_dL': smL, 'scenario_dL_fixscale': smLf,
            'eos_R': sum(d[bg]['eos_R'] for d in deltas.values()),
            'eos_flips': {x: sum(d[bg][x]['eos_flip'] for d in deltas.values()) for x in DELS},
            'D_L_sign_disagree': {x: sum(d[bg][x]['D_L_sign_disagree'] for d in deltas.values()) for x in DELS},
            'abs_dD_range': {x: [min(abs(v) for v in sm[x].values()), max(abs(v) for v in sm[x].values())] for x in DELS},
            'local': {'I_norm_range': [min(v['norms']['I'] for v in loc.values()), max(v['norms']['I'] for v in loc.values())],
                      'J_norm_range': [min(v['norms']['J'] for v in loc.values()), max(v['norms']['J'] for v in loc.values())],
                      'cos_I_vs_AS_plus_AF_range': [min(cos), max(cos)] if cos else None,
                      'cos_negative_items': sum(c < 0 for c in cos),
                      'cos_median': statistics.median(cos) if cos else None}}
    result['background_contrast'] = K.background_contrast(result['backgrounds']['M']['tier_I']['label'],
                                                           result['backgrounds']['N']['tier_I']['label'])
    return result


def load(run_dir):
    run_dir = Path(run_dir)
    out = []
    for w in sorted(run_dir.glob('worker-*')):
        if w.is_dir():
            r = json.loads((w / 'receipt.json').read_text())
            assert r['status'] == 'completed'
            for rel in sorted(r['record_hashes']):
                out.append(json.loads((w / rel).read_text()))
    return out


def main():
    run_dir, out = sys.argv[1], Path(sys.argv[2])
    ver = json.loads((Path(run_dir) / 'verification.json').read_text())
    assert ver['status'] == 'passed' and ver['stage'] == 'formal'
    res = analyse(load(run_dir))
    res['verification'] = ver
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('x') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({bg: {'tier_I': res['backgrounds'][bg]['tier_I']['label'], 'tier_J': res['backgrounds'][bg]['tier_J']['label']}
                      for bg in BGS} | {'contrast': res['background_contrast']}, indent=2))


if __name__ == '__main__':
    main()
