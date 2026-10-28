"""Read selected archived 4B cases. No model loading or new inference."""
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).with_suffix('.json')
RUNS = [ROOT / 'experiments' / name for name in (
    'early-layer-mechanism-v1-2026-10-28',
    'layer-trace-extension-v1-2026-10-28',
)]
IDS = [
    '4b-L00-N004146-D+0.25__Q04',
    '4b-L00-N004146-D+0.5__Q04',
    '4b-L00-N004146-D+1__Q04',
    '4b-L02-N005063-D+1__Q04',
    '4b-L02-N005251-D+0.5__Q05',
    '4b-L02-N005251-D+1__Q05',
    '4b-L04-N005428-D+1__Q04',
    '4b-L03-N007666-D+1__Q04',
]
sources = {}
paths = {}
for run in RUNS:
    for line in (run / 'sources.jsonl').read_text().splitlines():
        s = json.loads(line)
        if 'layer-trace-extension' in run.name and not s.get('stage'):
            continue
        sources[s['trace_id']] = s
    for path in (run / 'archive-r01' / 'execution-r01').rglob('*.json.gz'):
        if '/survey/' in str(path):
            paths[path.name.split('-', 1)[1][:-8]] = path

cases = []
for trace_id in IDS:
    source = sources[trace_id]
    record = source['record']
    trace = json.load(gzip.open(paths[trace_id], 'rt'))
    steps = trace['logits']['steps']
    first_strict = None
    step_rows = []
    for step in steps:
        candidates = {c['token_id']: c for c in step['candidates']}
        actual = candidates[step['generated_token_id']]
        best_clean = max(c['clean_logit'] for c in candidates.values())
        gap = actual['clean_logit'] - best_clean
        if first_strict is None and gap < -1e-6:
            first_strict = step['step']
        step_rows.append({
            'step': step['step'], 'actual': actual['token_text'],
            'clean_top': candidates[step['clean_top_token_ids'][0]]['token_text'],
            'actual_clean_gap_to_best': gap,
            'clean_logprob': actual['clean_logprob'],
            'steer_logprob': actual['steer_logprob'],
            'kl_steer_to_clean': step['kl_steer_to_clean'],
            'clean_entropy': step['clean_entropy'], 'steer_entropy': step['steer_entropy'],
            'clean_stop_advantage': step['clean_stop_advantage'],
            'steer_stop_advantage': step['steer_stop_advantage'],
        })
    positions = sorted(set([0, first_strict or 0, min(5, len(steps)-1), len(steps)-1]))
    sites_by_step = {}
    for step in positions:
        pos = trace['prompt_token_count'] - 1 + step
        sites_by_step[str(step)] = [
            {'name': site['name'], 'module_type': site['module_type'],
             **{key: site[key][pos] for key in ('clean_norm', 'steer_norm', 'delta_norm', 'relative_delta', 'cosine')}}
            for site in trace['sites']
        ]
    cases.append({
        'trace_id': trace_id,
        'trace_path': str(paths[trace_id].relative_to(ROOT)),
        'record_path': str(paths[trace_id].with_name(paths[trace_id].name[:-3]).relative_to(ROOT)).replace('/traces/', '/records/'),
        'source_provenance': source['provenance'],
        'prompt': record['prompt'],
        'intervention': record['intervention'],
        'baseline_output': sources['4b-baseline__' + record['question_id']]['record']['output'],
        'intervened_output': trace['output'],
        'source_token_ids_match': trace['source_token_ids_match'],
        'first_strict_clean_disfavored_step': first_strict,
        'first_prediction_divergence_reported': trace['logits']['first_prediction_divergence'],
        'steps': step_rows, 'sites_by_step': sites_by_step,
    })
OUT.write_text(json.dumps(cases, ensure_ascii=False, indent=2) + '\n')
for c in cases:
    print(c['trace_id'], 'strict step', c['first_strict_clean_disfavored_step'])
    print('BASE', c['baseline_output']['raw_text'])
    print('STEER', c['intervened_output']['raw_text'])
    print('STEPS', json.dumps(c['steps'][:8], ensure_ascii=False))
    names = {'L0.attention','L0.mlp','L0.residual','L1.attention','L1.mlp','L1.residual','L2.attention','L2.mlp','L2.residual','L3.attention','L3.mlp','L3.residual','L4.attention','L4.mlp','L4.residual','L5.attention','L5.mlp','L5.residual','L7.residual','L15.residual','L23.residual','L31.residual'}
    print('SITES STEP0', json.dumps([x for x in c['sites_by_step']['0'] if x['name'] in names], ensure_ascii=False))
