"""Relate archived search targets to previously defined stable failures."""
import ast
import csv
import gzip
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
OLD = P.parent / 'wsp-c-failure-structure-audit-2026-11-06'
STABLE = P.parent / 'wsp-c-stable-failure-audit-2026-11-06'

def read(p):
    return json.loads(gzip.decompress(p.read_bytes()) if p.suffix == '.gz' else p.read_bytes())

def main():
    trace = read(P / 'trace-extract.json.gz')
    previous_check = read(STABLE / 'verification.json')
    assert hashlib.sha256((OLD / 'saved-C-results.json.gz').read_bytes()).hexdigest() == previous_check['inputs'][str((OLD / 'saved-C-results.json.gz').relative_to(P.parents[1]))]
    for name in ('analysis.json', 'source-details.json'):
        assert hashlib.sha256((STABLE / name).read_bytes()).hexdigest() == previous_check['isolated_repeat']['output_sha256'][name]
    saved = read(OLD / 'saved-C-results.json.gz')
    stable = read(STABLE / 'analysis.json')['models']['Gemma']['tier_sources']['T0_control_pass_stable']
    details = {r['group']: r for r in read(STABLE / 'source-details.json') if r['model'] == 'Gemma'}
    assert len(stable) == 16
    run = saved['runs']['Gemma_v9']
    w0 = next(e for k, e in run['evaluations'].items() if k.startswith('w0-'))
    scores0 = {r['request_id']: r for r in w0['scored']}
    failures = {rid for rid, r in scores0.items() if r['group_id'] in stable and r['template'] == 'T0'
                and r['arm'] == 'B0' and r['condition'].startswith('counterfact_') and not r['correct']}
    output = {'scope': 'Post hoc saved-development search-target audit', 'calls': {'gpu': 0, 'model': 0},
              'stable_sources': stable, 'exact_stable_failed_ids': sorted(failures), 'runs': {}}
    table = []
    for version, records in trace['runs'].items():
        run = saved['runs']['Gemma_' + version]
        rounds = {r['candidate']: r['round'] for r in run['rounds']}
        ops, commits = [], []
        for r in records:
            q = r['request'].get('request', {})
            op = q.get('op')
            if op in ('measure', 'diagnose', 'image'):
                ids = q.get('ids', [])
                if 'id' in q:
                    ids = [q['id']]
                if 'request_id' in q:
                    ids = [q['request_id']]
                groups = sorted({x.split(':')[0] for x in ids})
                ops.append({'turn': r['turn'], 'op': op, 'ids': ids, 'groups': groups,
                            'stable_groups': sorted(set(groups) & set(stable)),
                            'stable_failed_id_matches': sorted(set(ids) & failures),
                            'text_overrides': bool(q.get('text_overrides') or q.get('spec', {}).get('text_overrides')),
                            'prose': r['reply'].split('```')[0].strip()})
            if op == 'commit' and not r['response'].get('failed'):
                cid = r['response'].get('value', {}).get('id')
                if cid not in rounds:
                    continue
                ids = q.get('evidence', {}).get('contrast_ids', [])
                after = {x['request_id']: x for x in run['evaluations'][cid]['scored']}
                tested_errors = [x for x in ids if x in scores0 and not scores0[x]['correct']]
                commits.append({'turn': r['turn'], 'round': rounds[cid], 'candidate': cid,
                                'evidence': q.get('evidence'), 'rationale': q.get('rationale'),
                                'contrast_ids': ids, 'stable_group_ids': [x for x in ids if x.split(':')[0] in stable],
                                'exact_stable_failed_ids': sorted(set(ids) & failures),
                                'baseline_failed_contrast_ids': tested_errors,
                                'formal_repaired_contrast_ids': [x for x in tested_errors if after[x]['correct']]})
        assert sorted(c['round'] for c in commits) == list(range(1, 31)), version
        output['runs'][version] = {'ops': ops, 'commits': commits,
                                  'measure_groups': sorted({g for x in ops if x['op'] == 'measure' for g in x['groups']}),
                                  'diagnose_stable_groups': sorted({g for x in ops if x['op'] == 'diagnose' for g in x['stable_groups']}),
                                  'committed_stable_failed_ids': sorted({x for c in commits for x in c['exact_stable_failed_ids']})}
    # Reconstruct the source selection in researcher turn 12 using saved formal W0.
    meaning_pairs = []
    for g in output['runs']['v9']['measure_groups']:
        candidates = [[f'{g}:counterfact_visual:{t}:O{o}:B0' for o in (0, 1)] for t in ('T0', 'T1')]
        candidates += [[f'{g}:counterfact_visual:{t}:O{o}:B0' for t in ('T0', 'T1')] for o in (0, 1)]
        for a, b in candidates:
            if scores0[a]['correct'] != scores0[b]['correct']:
                meaning_pairs.append([a, b] if scores0[a]['correct'] else [b, a])
    output['direction_construction'] = {'code_source': 'v9 turn-0012 and turn-0014',
        'meaning_preserving_success_failure_pairs': meaning_pairs,
        'source_groups': sorted({x[0].split(':')[0] for x in meaning_pairs}),
        'stable_sources_in_direction': sorted({x[0].split(':')[0] for x in meaning_pairs} & set(stable))}
    reply12 = next(r for r in trace['runs']['v9'] if r['turn'] == 'turn-0012')['response']['value']['output']
    printed = next(line.removeprefix('SUCCESS_FAILURE_PAIRS ') for line in reply12.splitlines() if line.startswith('SUCCESS_FAILURE_PAIRS '))
    assert sorted(map(tuple, meaning_pairs)) == sorted(ast.literal_eval(printed))
    for g in stable:
        d = details[g]
        row = {'source': g, 'direction': d['T0_failure_direction'], 'full_repair_count': len(d['repair_candidates']),
               'eligible_partial_rounds': ';'.join(x['run'] + ':R' + str(x['round']) for x in d['partial_candidates'] if x['protection_pass'])}
        for version, r in output['runs'].items():
            row[version + '_measure_turns'] = ';'.join(x['turn'] for x in r['ops'] if x['op'] == 'measure' and g in x['groups'])
            row[version + '_diagnose_turns'] = ';'.join(x['turn'] for x in r['ops'] if x['op'] == 'diagnose' and g in x['groups'])
            row[version + '_contrast_rounds_same_source'] = ';'.join(str(x['round']) for x in r['commits'] if any(z.startswith(g + ':') for z in x['contrast_ids']))
            row[version + '_contrast_rounds_exact_failure'] = ';'.join(str(x['round']) for x in r['commits'] if any(z.startswith(g + ':') for z in x['exact_stable_failed_ids']))
        assert row['full_repair_count'] == 0
        table.append(row)
    (P / 'analysis.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    with (P / 'source-targets.csv').open('w') as f:
        w = csv.DictWriter(f, fieldnames=list(table[0]), lineterminator='\n')
        w.writeheader(); w.writerows(table)
    inputs = [P / 'trace-extract.json.gz', OLD / 'saved-C-results.json.gz', STABLE / 'analysis.json', STABLE / 'source-details.json']
    verification = {'inputs': {str(p.relative_to(P.parent)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
                    'archived_trace_identity': trace['provenance'], 'rounds_checked': 60, 'sources_checked': 16,
                    'all_stable_sources_fully_repaired': 0, 'direction_pairs_match_original_printed_output': True,
                    'new_model_or_gpu_calls': 0}
    (P / 'verification.json').write_text(json.dumps(verification, indent=2) + '\n')
    print(json.dumps({v: {k: val for k, val in r.items() if k not in ('ops', 'commits')} for v, r in output['runs'].items()}, indent=2))

if __name__ == '__main__':
    main()
