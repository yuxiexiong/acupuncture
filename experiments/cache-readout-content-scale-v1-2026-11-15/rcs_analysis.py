"""RCS-01 frozen eight-arm analysis. Pure Python; no model/tokenizer imports.

python rcs_analysis.py --run-dir RUN --output summary.json [--stage engineering]
Input: records/R/bases.json {'bases': {'C': trajectory, 'H': trajectory}};
records/R/D.json has the eight arm keys. A trajectory contains the old WSB
`answer` and `t2` prefix/mapping/logits fields described in validate_prefix().
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / 'cache-write-signal-background-v1-2026-11-11'))
sys.path.insert(0, str(HERE.parent / 'cache-selection-precedence-v1-2026-11-06'))
import wsb_core as W
import spf_analysis as A

ARMS = tuple(b + c for b in ('C', 'H') for c in ('00', '10', '01', '11'))
SEED, N_BOOT = 2026111101, 20000
WITHIN = {'S0': ('01', '00'), 'S1': ('11', '10'),
          'C0': ('10', '00'), 'C1': ('11', '01')}
COEF = {'B': {'H11': 1, 'C11': -1}}
for _b in ('C', 'H'):
    for _n, (_a, _z) in WITHIN.items():
        COEF[_b + '_' + _n] = {_b + _a: 1, _b + _z: -1}
for _n in ('S0', 'S1'):
    COEF['delta_' + _n] = {**COEF['H_' + _n],
                            **{a: -v for a, v in COEF['C_' + _n].items()}}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def avg(xs):
    return sum(xs) / len(xs) if xs else None


def finite_logits(xs):
    return (isinstance(xs, list) and len(xs) == 3 and
            all(type(x) in (int, float) and math.isfinite(x) for x in xs))


def classify(trajectory, item):
    """Re-use the original full-answer parser; do not trust a saved row label."""
    answer = trajectory['answer']
    nr = answer['N']
    require(nr['ids'] and nr['ids'][0] == answer['x'], 'answer first token mismatch')
    row = A.row_out(nr, item)
    cat = A.NK.FK.classify(nr['text'], nr['termination'], item['target'],
                         [x for x in item['listed_codes'] if x != item['target']],
                         item.get('question'))
    require(answer['row'] == row, 'saved row disagrees with frozen parser')
    require(answer['classification'] == cat, 'saved classification disagrees with frozen parser')
    category, sub = A.NK.category(nr['text'], nr['termination'], item,
                                nr.get('reached_t2', True))
    return {'row': row, 'category': category, 'sub': sub, 'classification': cat,
            'first_stop': not nr.get('reached_t2', True) and nr['termination'] == 'stop',
            'later_stop': category == 'stop_no_code' and nr.get('reached_t2', True),
            'truncated': nr['termination'] == 'budget'}


def validate_prefix(trajectory):
    """Eligibility uses ONLY t1 prefix + frozen candidate mapping, never logits."""
    t = trajectory['t2']
    ids = t['candidate_token_ids']
    require(type(t['mapping_valid']) is bool, 'mapping_valid must be a boolean')
    reasons = []
    if not t['mapping_valid']:
        reasons.append('mapping_invalid:' + t.get('reason', ''))
    if (not isinstance(ids, list) or len(ids) != 3 or
            any(type(x) is not int for x in ids) or len(set(ids)) != 3):
        reasons.append('three_distinct_candidate_tokens_required')
    if t['prefix_ids'] != [trajectory['answer']['x']]:
        reasons.append('prefix_first_token_mismatch')
    if not isinstance(t['prefix_text'], str) or not t['prefix_text']:
        reasons.append('uninterpretable_prefix')
    if not trajectory['answer']['N'].get('reached_t2', True):
        reasons.append('first_token_stop')
    return reasons


def eligibility(records, items, tables):
    eligible, missing = [], {}
    for r in sorted(items):
        trajectories = [('U_' + b, records[r]['bases'][b]) for b in ('C', 'H')]
        trajectories += [(d['id'] + '/' + a, records[r]['pairs'][d['id']][a])
                         for d in tables[r] for a in ARMS]
        ref = trajectories[0][1]['t2']
        failures = []
        for name, tr in trajectories:
            reasons = validate_prefix(tr)
            t = tr['t2']
            if any(t[k] != ref[k] for k in ('prefix_ids', 'prefix_text', 'candidate_token_ids')):
                reasons.append('not_receiver_common_prefix_and_mapping')
            if reasons:
                failures.append({'trajectory': name, 'reasons': reasons})
        if failures:
            missing[r] = failures
        else:
            eligible.append(r)
            # Missing measurements never become a result-dependent eligibility filter.
            for name, tr in trajectories:
                require(finite_logits(tr['t2'].get('candidate_logits')),
                        f'eligible receiver missing finite t2 logits: {r}/{name}')
                stops = tr['t2'].get('stop_logits')
                require(isinstance(stops, dict) and set(stops) == {'248044', '248046'} and
                        all(type(v) in (int, float) and math.isfinite(v) for v in stops.values()),
                        f'eligible receiver missing finite stop logits: {r}/{name}')
    total_pairs = sum(len(tables[r]) for r in items)
    pairs = sum(len(tables[r]) for r in eligible)
    by_scene = {}
    for scene in sorted({v['scenario'] for v in items.values()}):
        rs = [r for r in items if items[r]['scenario'] == scene]
        yes = [r for r in rs if r in eligible]
        by_scene[scene] = {'receivers': len(rs), 'eligible_receivers': len(yes),
                           'pairs': sum(len(tables[r]) for r in rs),
                           'eligible_pairs': sum(len(tables[r]) for r in yes)}
    coverage = len(eligible) / len(items)
    pair_coverage = pairs / total_pairs
    return {'receivers': eligible, 'excluded': missing, 'receiver_coverage': coverage,
            'pair_coverage': pair_coverage, 'pairs': pairs, 'total_pairs': total_pairs,
            'total_receivers': len(items), 'per_scenario': by_scene,
            'coverage_passed': coverage >= .90 and pair_coverage >= .90}


def draws_for(clusters, n_boot):
    require(type(n_boot) is int and n_boot > 0, 'positive bootstrap count required')
    rng = random.Random(SEED)
    return [tuple(rng.choice(clusters) for _ in clusters) for _ in range(n_boot)]


def family(rows, scenes, draws, names):
    """Receiver-equal means; same whole-scenario draws, simultaneous max-deviation CI.

    Empty R* draws are NOT dropped/replaced. They invalidate its intervals.
    """
    names = list(names)
    clusters = sorted(set(scenes.values()))
    groups = {s: [r for r in rows if scenes[r] == s] for s in clusters}
    per_scene = {s: {'receivers': len(rs), 'means': {
        k: avg([rows[r][k] for r in rs]) for k in names}} for s, rs in groups.items()}
    means = {k: avg([v[k] for v in rows.values()]) for k in names}
    result = {'receivers': len(rows), 'per_receiver': rows, 'per_scenario': per_scene,
              'names': names, 'intervals': {}, 'empty_draws': 0}
    if not rows:
        result['status'] = 'no_eligible_receivers'
        return result
    sums = {s: [sum(rows[r][k] for r in rs) for k in names] for s, rs in groups.items()}
    deviations = []
    for draw in draws:
        n = sum(len(groups[s]) for s in draw)
        if n == 0:
            result['empty_draws'] += 1
            continue
        deviations.append(max(abs(sum(sums[s][j] for s in draw) / n - means[k])
                              for j, k in enumerate(names)))
    width = None if result['empty_draws'] else sorted(deviations)[math.ceil(.95 * len(draws)) - 1]
    result.update(status='empty_cluster_draw' if width is None else 'ok', common_width=width)
    result['intervals'] = {k: {'mean': means[k],
                              'lo': None if width is None else means[k] - width,
                              'hi': None if width is None else means[k] + width} for k in names}
    return result


def fill_bounds(table, outputs, coef):
    """Exact extremes over arbitrary three-row filling of every invalid answer."""
    weights = W.weights(table)
    low = high = 0.
    for arm, factor in coef.items():
        for donor, ws in weights.items():
            row = outputs[arm][donor]
            vals = [factor * ws[row]] if type(row) is int and row in (0, 1, 2) else [factor * w for w in ws]
            low += min(vals)
            high += max(vals)
    return low, high


def dtr_analysis(ids, outputs, tables, scenes, draws):
    rows, bound_rows, cells, interaction = {}, {}, {}, {}
    for r in ids:
        f = {a: W.S.d_transfer(tables[r], outputs[r][a]) for a in ARMS}
        require(all(v is not None for v in f.values()), 'incomplete D_tr donor contrast table')
        cells[r] = f
        rows[r] = {name: sum(f[a] * w for a, w in coef.items()) for name, coef in COEF.items()}
        bound_rows[r] = {}
        for name, coef in COEF.items():
            low, high = fill_bounds(tables[r], outputs[r], coef)
            bound_rows[r][name + '_lo'], bound_rows[r][name + '_hi'] = low, high
        interaction[r] = {b: f[b+'11'] - f[b+'10'] - f[b+'01'] + f[b+'00'] for b in ('C', 'H')}
    result = family(rows, scenes, draws, COEF)
    bounds = family(bound_rows, scenes, draws, [n + suffix for n in COEF for suffix in ('_lo', '_hi')])
    result.update(sensitivity=bounds, cells_per_receiver=cells,
                  cells={a: avg([f[a] for f in cells.values()]) for a in ARMS},
                  interaction={'per_receiver': interaction,
                               'mean': {b: avg([v[b] for v in interaction.values()]) for b in ('C', 'H')},
                               'inferential_family': False})
    for name, interval in result['intervals'].items():
        interval['sensitivity_lo'] = bounds['intervals'][name+'_lo']['lo']
        interval['sensitivity_hi'] = bounds['intervals'][name+'_hi']['hi']
        interval['label'] = effect_label(interval)
    return result


def positive(interval, threshold=.10):
    return (interval.get('lo') is not None and interval['lo'] >= threshold and
            interval.get('sensitivity_lo', interval['lo']) is not None and
            interval.get('sensitivity_lo', interval['lo']) >= threshold)


def near_zero(interval, band=.05):
    return (interval.get('lo') is not None and interval['lo'] >= -band and interval['hi'] <= band and
            interval.get('sensitivity_lo', interval['lo']) is not None and
            interval.get('sensitivity_lo', interval['lo']) >= -band and
            interval.get('sensitivity_hi', interval['hi']) <= band)


def effect_label(interval):
    if positive(interval):
        return 'positive'
    if (interval.get('hi') is not None and interval['hi'] <= -.10 and
            interval['sensitivity_hi'] is not None and interval['sensitivity_hi'] <= -.10):
        return 'negative'
    return 'near_zero' if near_zero(interval) else 'indeterminate'


def continuous_analysis(ids, records, tables, self_rows, scenes, draws):
    pairs, per_l, per_q, per_other = [], {}, {}, {}
    q_names = ('C_S0', 'C_S1', 'H_S0', 'H_S1', 'delta_S0', 'delta_S1')
    l_names = ('delta_L_S0', 'delta_L_S1', 'delta_e')
    for r in ids:
        local = []
        for donor in tables[r]:
            if donor['type'] not in ('AL', 'BD'):
                continue
            d, y = donor['row'], self_rows[r]
            require(d != y, 'conflict donor unexpectedly agrees with self')
            o = next(k for k in (0, 1, 2) if k not in (d, y))
            rec = {'receiver': r, 'donor': donor['id'], 'scenario': scenes[r],
                   'type': donor['type'], 'self_row': y, 'donor_row': d, 'third_row': o,
                   'backgrounds': {}, 'L': {}, 'Q': {}}
            for b in ('C', 'H'):
                base = records[r]['bases'][b]['t2']
                zb = base['candidate_logits']
                arm_logits = {c: records[r]['pairs'][donor['id']][b+c]['t2']['candidate_logits']
                              for c in ('00', '10', '01', '11')}
                ls = {c: z[d] - z[y] for c, z in arm_logits.items()}
                qs = {c: z[d] - z[o] for c, z in arm_logits.items()}
                m, e = zb[y] - zb[d], ls['11'] - (zb[d] - zb[y])
                rec['backgrounds'][b] = {'baseline_logits': zb, 'arm_logits': arm_logits,
                    'baseline_stop_logits': base.get('stop_logits'),
                    'arm_stop_logits': {c: records[r]['pairs'][donor['id']][b+c]['t2'].get('stop_logits')
                                        for c in ('00', '10', '01', '11')},
                    'L': ls, 'Q': qs, 'm': m, 'e': e, 'remaining_self_advantage': m-e}
                for n in ('S0', 'S1'):
                    a, z = WITHIN[n]
                    rec['L'][b+'_'+n] = ls[a] - ls[z]
                    rec['Q'][b+'_'+n] = qs[a] - qs[z]
            for n in ('S0', 'S1'):
                rec['L']['delta_L_'+n] = rec['L']['H_'+n] - rec['L']['C_'+n]
                rec['Q']['delta_'+n] = rec['Q']['H_'+n] - rec['Q']['C_'+n]
            bc, bh = rec['backgrounds']['C'], rec['backgrounds']['H']
            rec['L']['delta_e'] = bh['e'] - bc['e']
            thresholds = {'midpoint': (bc['m']+bh['m'])/2, 'm_C': bc['m'], 'm_H': bh['m']}
            rec['common_thresholds'] = {n: {'threshold': m, 'C': bc['e']-m, 'H': bh['e']-m}
                                        for n, m in thresholds.items()}
            local.append(rec)
            pairs.append(rec)
        require(local, f'eligible receiver has no conflict pairs: {r}')
        per_l[r] = {n: avg([p['L'][n] for p in local]) for n in l_names}
        per_q[r] = {n: avg([p['Q'][n] for p in local]) for n in q_names}
        per_other[r] = {b+'_'+n: avg([p['backgrounds'][b][n] for p in local])
                        for b in ('C', 'H') for n in ('m', 'e')}
        per_other[r].update({b+'_Q00_positive': avg([float(p['backgrounds'][b]['Q']['00'] > 0) for p in local])
                             for b in ('C', 'H')})
    descriptive_names = [b+'_'+n for b in ('C', 'H') for n in ('m', 'e', 'Q00_positive')]
    # The raw pair distributions, including every Q00, are retained; no Q-based selection.
    return {'receivers': len(ids), 'conflict_pairs': len(pairs), 'pairs': pairs,
            'L_family': family(per_l, scenes, draws, l_names),
            'Q_family': family(per_q, scenes, draws, q_names),
            'descriptive_per_receiver': per_other,
            'descriptive_means': {n: avg([v[n] for v in per_other.values()]) for n in descriptive_names},
            'descriptive_per_scenario': {s: {n: avg([v[n] for r, v in per_other.items() if scenes[r] == s])
                                             for n in descriptive_names} for s in sorted(set(scenes.values()))},
            'conflict_pairs_per_receiver': dict(Counter(p['receiver'] for p in pairs))}


def analyse(records, items, tables, n_boot=N_BOOT):
    require(records and set(records) == set(items) == set(tables), 'receiver panel mismatch')
    outputs, classified, bases = {}, {}, {}
    scenes = {r: item['scenario'] for r, item in items.items()}
    self_rows = {r: item['listed_codes'].index(item['target']) for r, item in items.items()}
    for r, item in items.items():
        require(set(records[r]['bases']) == {'C', 'H'}, 'baseline backgrounds mismatch')
        require(set(records[r]['pairs']) == {d['id'] for d in tables[r]}, 'donor table mismatch')
        bases[r] = {b: classify(records[r]['bases'][b], item) for b in ('C', 'H')}
        classified[r] = {a: {} for a in ARMS}
        outputs[r] = {a: {} for a in ARMS}
        for d in tables[r]:
            pair = records[r]['pairs'][d['id']]
            require(set(ARMS) <= set(pair), 'missing eight-arm cell')
            for a in ARMS:
                c = classify(pair[a], item)
                classified[r][a][d['id']] = c
                outputs[r][a][d['id']] = c['row']
    rstar = eligibility(records, items, tables)
    draws = draws_for(sorted(set(scenes.values())), n_boot)
    full = dtr_analysis(sorted(items), outputs, tables, scenes, draws)
    subset = dtr_analysis(rstar['receivers'], outputs, tables, scenes, draws)
    continuous = continuous_analysis(rstar['receivers'], records, tables, self_rows, scenes, draws)
    total = sum(len(t) for t in tables.values())
    valid = {a: sum(type(v) is int and v in (0, 1, 2) for r in outputs for v in outputs[r][a].values())/total
             for a in ARMS}
    baseline_correct = {b: avg([float(v[b]['row'] == self_rows[r]) for r, v in bases.items()]) for b in ('C', 'H')}
    arm_ok = {a: valid[a] >= .90 and valid[a[0]+'11'] - valid[a] <= .05 + 1e-12 for a in ARMS}
    guards = {'valid_fraction': valid, 'baseline_self_correct': baseline_correct,
              'drop_from_11': {a: valid[a[0]+'11']-valid[a] for a in ARMS},
              'arm_passed': arm_ok, 'passed': all(arm_ok.values()) and min(baseline_correct.values()) >= .90}
    conflict_counts = {a: Counter() for a in ARMS}
    for r in items:
        for d in tables[r]:
            if d['type'] not in ('AL', 'BD'):
                continue
            for a in ARMS:
                c = classified[r][a][d['id']]
                row = c['row']
                label = ('self' if row == self_rows[r] else 'donor' if row == d['row'] else
                         'third' if type(row) is int else row)
                conflict_counts[a][label] += 1
                for flag in ('first_stop', 'later_stop', 'truncated'):
                    conflict_counts[a][flag] += int(c[flag])
                conflict_counts[a]['invalid'] += int(type(row) is not int)
                conflict_counts[a]['total'] += 1
    strong_checks = {scope+'_'+name: positive(d['intervals'].get(name, {}), .15 if name == 'B' else .10)
                     for scope, d in (('full', full), ('Rstar', subset)) for name in ('B', 'H_S1', 'delta_S1')}
    for name in ('delta_L_S1', 'delta_e'):
        strong_checks[name] = positive(continuous['L_family']['intervals'].get(name, {}))
    strong = guards['passed'] and rstar['coverage_passed'] and all(strong_checks.values())
    uses = {}
    for b in ('C', 'H'):
        f = full['intervals']
        uses[b] = {'denominator_advantage': guards['passed'] and
                       all(positive(f[b+'_'+n]) for n in ('S0', 'S1')) and
                       all(near_zero(f[b+'_'+n]) for n in ('C0', 'C1')),
                   'numerator_advantage': guards['passed'] and
                       all(positive(f[b+'_'+n]) for n in ('C0', 'C1')) and
                       all(near_zero(f[b+'_'+n]) for n in ('S0', 'S1'))}
    return {'kind': 'seen-panel exploratory RCS-01', 'seed': SEED, 'bootstrap_draws': n_boot,
            'independent_unit': 'scenario', 'receiver_weighting': 'equal',
            'receivers': len(items), 'pairs': total, 'scenarios': sorted(set(scenes.values())),
            'full_D_tr': full, 'Rstar': rstar, 'Rstar_D_tr': subset, 'continuous': continuous,
            'delivery': guards, 'conflict_counts': {a: dict(v) for a, v in conflict_counts.items()},
            'classifications': classified, 'baseline_classifications': bases,
            'conditional_use_advantage': uses,
            'strong_background_beyond_fixed_margin': {'holds': strong, 'checks': strong_checks,
                 'delivery_passed': guards['passed'], 'common_coverage_passed': rstar['coverage_passed']},
            'mechanism_status': ('delivery_degraded' if not guards['passed'] else
                                 'continuous_unjudgeable' if not rstar['coverage_passed'] or
                                 continuous['L_family']['status'] != 'ok' else 'report_separate_effects'),
            'effect_label_scope': 'Numerical interval labels require delivery guards for mechanism claims; B background gate is .15.',
            'limits': 'Conditional uses, not natural mediation shares; intervals are exploratory over seen scenarios.'}


def full_items(panel, root=None):
    """Restore the frozen parser's original question/first_listed, without runtime imports."""
    root = ROOT if root is None else Path(root)
    base = 'experiments/cache-local-v-k-v1-2026-11-03/'
    ledger_rel = base + 'data/heldout-tokens-r01.json'
    heldout_rel = 'experiments/cache-local-v-k-design-v1-2026-11-03/heldout-inputs-r01.json'
    freeze = json.loads((root/(base+'freeze-r01.json')).read_text())
    raw = {}
    for rel in (ledger_rel, heldout_rel):
        raw[rel] = (root/rel).read_bytes()
        require(hashlib.sha256(raw[rel]).hexdigest() == freeze['files'][rel],
                'frozen parser source hash mismatch: ' + rel)
    ledger = json.loads(raw[ledger_rel])
    require(ledger['status'] == 'passed' and
            ledger['heldout_sha256'] == hashlib.sha256(raw[heldout_rel]).hexdigest(),
            'frozen token ledger not accepted or heldout identity mismatch')
    out = {}
    for r, p in panel.items():
        it = ledger['items'][r]['item']
        normalized = {**it, 'scenario': it['base_id'],
                      'binding': {k: v[1] for k, v in it['binding'].items()}}
        require(all(normalized.get(k) == v for k, v in p.items()),
                'SPF panel disagrees with full frozen ledger: ' + r)
        require(isinstance(it.get('question'), str) and it['question'],
                'full frozen item missing question: ' + r)
        out[r] = {**it, 'scenario': p['scenario']}
    return out


def load(run_dir, stage='formal'):
    run_dir = Path(run_dir)
    receipt_raw, exit_raw = ((run_dir/name).read_bytes() for name in ('receipt.json', 'exit.json'))
    receipt, exited = json.loads(receipt_raw), json.loads(exit_raw)
    require(receipt['status'] == 'completed', 'analysis requires completed run receipt')
    require(receipt['stage'] == stage, 'run receipt stage mismatch')
    require(exited['returncode'] == 0, 'analysis requires zero worker exit code')
    items, tables = W.panel('formal')
    items = full_items(items)
    if stage == 'engineering':
        ids = {min(r for r, item in items.items() if item['scenario'] == s)
               for s in {item['scenario'] for item in items.values()}}
        items, tables = ({r: x for r, x in source.items() if r in ids} for source in (items, tables))
    root = Path(run_dir) / 'records'
    require({p.name for p in root.iterdir() if p.is_dir()} == set(items), 'run receiver directories mismatch')
    expected_records = {f'records/{r}/{name}.json' for r in items
                        for name in ['bases'] + [d['id'] for d in tables[r]]}
    require({rel for rel in receipt['files'] if rel.startswith('records/') and rel.endswith('.json')} == expected_records,
            'receipt record inventory mismatch')
    records, hashes = {}, {'receipt.json': hashlib.sha256(receipt_raw).hexdigest(),
                          'exit.json': hashlib.sha256(exit_raw).hexdigest()}
    def read(path):
        raw = path.read_bytes()
        rel = str(path.relative_to(run_dir))
        digest = hashlib.sha256(raw).hexdigest()
        require(receipt['files'].get(rel) == digest, 'record hash missing or mismatched: ' + rel)
        hashes[rel] = digest
        return json.loads(raw)
    for r in items:
        paths = {d['id']+'.json' for d in tables[r]} | {'bases.json'}
        require({p.name for p in (root/r).glob('*.json')} == paths, f'run donor files mismatch: {r}')
        baseline = read(root/r/'bases.json')
        if 'item' in baseline:
            require(all(baseline['item'].get(k) == v for k, v in items[r].items() if k != 'scenario'),
                    'saved full item disagrees with frozen ledger: ' + r)
        records[r] = {'bases': baseline['bases'],
                      'pairs': {d['id']: read(root/r/(d['id']+'.json')) for d in tables[r]}}
    return records, items, tables, hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--stage', choices=('formal', 'engineering'), default='formal')
    args = parser.parse_args()
    records, items, tables, hashes = load(args.run_dir, args.stage)
    result = analyse(records, items, tables)
    result['source'] = {'run_dir': str(args.run_dir), 'stage': args.stage, 'sha256': hashes}
    with args.output.open('x') as f:
        f.write(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    main()
