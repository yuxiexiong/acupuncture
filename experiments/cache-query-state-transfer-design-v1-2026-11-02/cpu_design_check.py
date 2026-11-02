"""QST-01 design inventory and adversarial rule checks. Stdlib only; no model.
Run from any directory: python cpu_design_check.py
Writes deterministic design-r01.json and cpu-check-r01.json beside this file.
"""
import hashlib
import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
QCD = ROOT / 'experiments/cache-coverage-dose-v1-2026-11-02'
AUDIT = ROOT / 'experiments/cache-query-state-direction-audit-v1-2026-11-02/pair-audit-r01.json'
SOURCE_COMMIT = '115dc2e9bd73ac4604fdbf1dce2de30fec32c2a2'
DIRECTIONS = ['N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'N_L00_C1343_D-1']
SCENARIOS = ['NQ01', 'NQ03', 'NQ05', 'NQ06']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def contrast(out_b, out_c, b, c):
    """Inputs are full-delivery code or None, not first token / raw substring."""
    j = ((out_b == b) - (out_c == b) + (out_c == c) - (out_b == c)) / 2
    return {'J': j, 'W': int(out_b == b and out_c == c),
            'W_reverse': int(out_b == c and out_c == b)}


def mean(rows, key):
    return sum(r[key] for r in rows) / len(rows)


def stable(rows, anti_first=False, reverse=False):
    subset = [r for r in rows if not anti_first or r['both_foreign_nonfirst']]
    by = {s: [r for r in subset if r['scenario'] == s] for s in SCENARIOS}
    sign, wk = (-1, 'W_reverse') if reverse else (1, 'W')
    js = [sign * mean(by[s], 'J') for s in SCENARIOS]
    ws = [mean(by[s], wk) for s in SCENARIOS]
    return (sum(x > 0 for x in js) >= 3 and sum(js) / 4 >= 1 / 3
            and sum(ws) / 4 >= 1 / 3)


def support(rows, reverse=False):
    return stable(rows, reverse=reverse) and stable(rows, anti_first=True, reverse=reverse)


def attenuation(clean, damaged):
    assert [r['receiver'] for r in clean] == [r['receiver'] for r in damaged]
    delta = [dict(c, J=c['J'] - t['J'], W=c['W'] - t['W']) for c, t in zip(clean, damaged)]
    by = {s: [r for r in delta if r['scenario'] == s] for s in SCENARIOS}
    js = [mean(by[s], 'J') for s in SCENARIOS]
    ws = [mean(by[s], 'W') for s in SCENARIOS]
    anti = [r for r in delta if r['both_foreign_nonfirst']]
    return (support(clean) and not support(damaged, reverse=True)
            and sum(x > 0 for x in js) >= 3 and sum(js) / 4 >= 1 / 3
            and sum(ws) / 4 >= 1 / 3 and mean(anti, 'J') > 0 and mean(anti, 'W') > 0)


def workload(texts, pair_count):
    n = len(texts)
    natural = pair_count * 9 + n * 4  # 8 mixed receiver arms + 1 clean receiver arm; T_nat.
    return {'formations': n * 5, 'prefix_prefills': n,
            'prefix_prefill_tokens': sum(x['plan']['b_b'] + 1 for x in texts),
            'formation_token_forwards': sum(x['plan']['L'] for x in texts) * 5,
            'natural_trajectories': natural, 'diagnostic_forwards': natural,
            'natural_decode_forward_cap': natural * 32, 'new_calibrations': 0}


def main():
    source = json.loads(AUDIT.read_text())
    pairs = source['pairs']
    ids = sorted({p['receiver'] for p in pairs})
    records, hashes = {}, {}
    for worker in sorted((QCD / 'runs/gformal-r01').glob('worker-*')):
        if not worker.is_dir():
            continue
        receipt = json.loads((worker / 'receipt.json').read_text())
        for iid in ids:
            path = worker / 'records' / (iid + '.json')
            if path.exists():
                digest = sha(path)
                assert digest == receipt['record_hashes']['records/' + iid + '.json']
                records[iid] = json.loads(path.read_text())
                hashes[str(path.relative_to(ROOT))] = digest
    assert len(records) == 48
    texts = [{'id': i, 'item': records[i]['item'], 'plan': records[i]['plan_text']} for i in ids]
    donors = defaultdict(list)
    for p in pairs:
        a, b = records[p['receiver']], records[p['donor']]
        for k in ['base_id', 'order', 'record', 'instruction']:
            assert a['item'][k] == b['item'][k]
        for k in ['n', 'b_b', 'p', 'e', 'L']:
            assert a['plan_text'][k] == b['plan_text'][k]
        assert p['same_query'] == (p['receiver'] == p['donor'])
        if not p['same_query']:
            assert a['answer'] != b['answer']
            donors[p['receiver']].append(p['donor'])
    contrasts = []
    for i in ids:
        if len(donors[i]) == 2:
            b, c = sorted(donors[i])
            assert len({records[x]['answer'] for x in [i, b, c]}) == 3
            contrasts.append({'receiver': i, 'b': b, 'c': c,
                              'scenario': records[i]['item']['base_id'],
                              'both_foreign_nonfirst': all(records[d]['item']['target_position'] != 'first' for d in (b, c))})
    assert len(contrasts) == 36 and sum(x['both_foreign_nonfirst'] for x in contrasts) == 12
    assert set(x['scenario'] for x in contrasts) == set(SCENARIOS)
    assert len(pairs) == 132 and sum(not x['same_query'] for x in pairs) == 84
    assert sum(len(donors[i]) == 1 for i in ids) == 12
    both_nonfirst = sum(not p['same_query'] and all(
        records[p[k]]['item']['target_position'] != 'first'
        for k in ['receiver', 'donor']) for p in pairs)
    assert both_nonfirst == 28
    formal = workload(texts, len(pairs))
    pre_ids = ['NA-NQ01-ABC-A', 'NA-NQ01-ABC-B', 'NA-NQ01-ABC-C', 'NA-NQ02-ABC-B', 'NA-NQ02-ABC-C']
    pre = workload([x for x in texts if x['id'] in pre_ids], 13)
    # Rebuild C and T4146 for two texts, with fresh prefill: 4 formations, 8 C/T/V/F trajectories.
    pre['formations'] += 4
    pre['prefix_prefills'] += 2
    rebuild = [x for x in texts if x['id'] in ['NA-NQ01-ABC-A', 'NA-NQ02-ABC-B']]
    assert len(rebuild) == 2
    pre['prefix_prefill_tokens'] += sum(x['plan']['b_b'] + 1 for x in rebuild)
    pre['formation_token_forwards'] += 2 * sum(x['plan']['L'] for x in rebuild)
    # 5 additional untouched C generations explicitly compare clean self-copy with no-op C.
    pre['natural_trajectories'] += 13
    pre['diagnostic_forwards'] += 13
    pre['natural_decode_forward_cap'] += 13 * 32
    for phase in (pre, formal):
        phase['total_model_forward_cap'] = (phase['prefix_prefills'] + phase['formation_token_forwards']
                                           + phase['natural_decode_forward_cap'] + phase['diagnostic_forwards'])
    normal = {k: pre[k] + formal[k] for k in formal}
    maximum = {k: pre[k] * 2 + formal[k] for k in formal}
    assert formal['natural_trajectories'] == 1380 and pre['natural_trajectories'] == 150
    assert maximum['formations'] == 298 and maximum['natural_trajectories'] == 1680
    checks = {}
    for name, outs, expected in [('follow', ('B', 'C'), 1), ('constant_B', ('B', 'B'), 0),
                                 ('constant_C', ('C', 'C'), 0), ('none', (None, None), 0),
                                 ('reverse', ('C', 'B'), -1), ('one_sided', ('B', None), .5)]:
        score = contrast(*outs, 'B', 'C')
        assert score['J'] == expected
        checks[name] = score
    def toy(kind):
        return [dict(r, **checks[kind]) for r in contrasts]
    assert support(toy('follow')) and support(toy('reverse'), reverse=True)
    for k in ['constant_B', 'constant_C', 'none', 'one_sided', 'reverse']:
        assert not support(toy(k))
    assert attenuation(toy('follow'), toy('constant_B'))
    assert not attenuation(toy('follow'), toy('follow'))
    assert not attenuation(toy('follow'), toy('reverse'))
    only_one = [dict(r, **checks['follow' if r['scenario'] == 'NQ01' else 'none']) for r in contrasts]
    assert not support(only_one)
    first_only = [dict(r, **checks['none' if r['both_foreign_nonfirst'] else 'follow']) for r in contrasts]
    assert not support(first_only)
    classifier = ROOT / 'experiments/cache-first-token-continuation-v1-2026-11-02/fc_core.py'
    spec = importlib.util.spec_from_file_location('frozen_fc', classifier)
    fc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fc)
    def complete(text, end='stop'):
        y = fc.classify(text, end, 'U17', ['U43', 'U86'])
        return y['Y_delivery'] and end == 'stop' and not y['tags']['think_unclosed']
    assert complete('编号是U17。<|im_end|>') and not complete('U17、U43<|im_end|>')
    assert not complete('U17', 'budget') and not complete('<think>U17')
    # Pure arithmetic illustration of length-4 valid convolution, not a model replay.
    def last_output(old):
        return sum(x * w for x, w in zip((old + [5])[-4:], [1, 2, 3, 4]))
    assert last_output([1, 2, 3, 4]) == last_output([999, 2, 3, 4])
    for f in [AUDIT, QCD / 'data/plan-r01.json', QCD / 'freeze-r01.json', classifier,
              ROOT / 'experiments/cache-conv-factor-design-audit-v1-2026-11-01/installed-conv-source.txt']:
        hashes[str(f.relative_to(ROOT))] = sha(f)
    design = {'id': 'QST-01-v1', 'source_commit': SOURCE_COMMIT, 'status': 'design_only_not_run',
              'directions': DIRECTIONS, 'texts': texts, 'pairs': pairs, 'primary_contrasts': contrasts,
              'primary_scenarios': SCENARIOS, 'preflight_ids': pre_ids,
              'thresholds': {'positive_scenarios_min': 3, 'scenario_count': 4,
                             'J_mean_min': 1 / 3, 'W_mean_min': 1 / 3,
                             'attenuation_delta_J_min': 1 / 3, 'attenuation_delta_W_min': 1 / 3},
              'budget': {'preflight_one_attempt': pre, 'formal': formal,
                         'normal_total': normal, 'maximum_one_preflight_retry': maximum,
                         'device_hours_caps': {'preflight_per_attempt': .25, 'formal': 2.5, 'total': 3},
                         'storage_cap_gib_all_attempts': 12}, 'source_sha256': hashes}
    (HERE / 'design-r01.json').write_text(json.dumps(design, ensure_ascii=False, indent=2) + '\n')
    report = {'status': 'passed_cpu_design_checks_only', 'independent_review': False, 'model_forwards': 0,
              'counts': {'texts': 48, 'pairs': 132, 'foreign_pairs': 84, 'primary_receivers': 36,
                         'primary_nonfirst_foreign_receivers': 12, 'both_nonfirst_foreign_pairs': 28},
              'preflight': pre, 'formal': formal, 'maximum': maximum, 'adversarial_scores': checks,
              'checks': ['source records match QCD receipts', 'matched record/order/positions',
                         'constant-answer bias cancels', 'one-sided failure does not pass',
                         'reverse distinguished from attenuation', 'one-scenario effect does not pass',
                         'anti-first check blocks first-dependent effects', 'complete-delivery parser cases',
                         'dead oldest-slot arithmetic illustration'],
              'design_sha256': sha(HERE / 'design-r01.json'), 'checker_sha256': sha(Path(__file__))}
    (HERE / 'cpu-check-r01.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ['status', 'counts', 'preflight', 'formal', 'maximum']}, indent=2))


if __name__ == '__main__':
    main()
