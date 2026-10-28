"""Read selected archived cases only. No model loading or new inference."""
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).with_suffix('.json')
EXPERIMENTS = ['early-layer-mechanism-v1-2026-10-28',
               'layer-trace-extension-v1-2026-10-28',
               'llama31-early-layer-trace-v1-2026-10-28']
SELECT = [('2b', 5, 3522, [-1, -.5]),
          ('9b', 0, 978, [.125, .25, .5, 1, -1]),
          ('llama31-8b-instruct', 5, 1726, [-1, -.5, 1, .5])]
rows, baselines, paths = {}, {}, {}
for experiment in EXPERIMENTS:
    root = ROOT / 'experiments' / experiment
    for line in (root / 'sources.jsonl').open():
        row = json.loads(line)
        if experiment == EXPERIMENTS[1] and not row.get('stage'):
            continue
        r = row['record']
        if r['layer'] is None:
            baselines[row['model'], r['question_id']] = r['output']
        for model, layer, channel, doses in SELECT:
            if (row['model'], r['layer'], r['channel'], r['question_id']) == (model, layer, channel, 'Q04') and r['intervention']['dose'] in doses:
                rows[row['trace_id']] = row
    patterns = ['*/survey/*/traces/*.json.gz'] if experiment == EXPERIMENTS[1] else ['survey/*/traces/*.json.gz']
    for pattern in patterns:
        for p in (root / 'archive-r01/execution-r01').glob(pattern):
            key = p.name[:-8].split('-', 1)[1]
            if key in rows:
                paths[key] = p
assert len(rows) == len(paths) == sum(len(x[3]) for x in SELECT)

cases = []
for key, row in sorted(rows.items()):
    r = row['record']
    t = json.load(gzip.open(paths[key], 'rt'))
    record_path = paths[key].parent.parent / 'records' / paths[key].name[:-3]
    record = json.loads(record_path.read_text())
    assert record['checks_passed'] and record['source_token_ids_match']
    assert t['generated_token_ids'] == r['output']['token_ids'] == record['output']['token_ids']
    pos = t['prompt_token_count'] - 1
    profile = [{**{k: s[k] for k in ['name', 'layer', 'component', 'module_type']},
                **{k: s[k][pos] for k in ['clean_norm', 'steer_norm', 'delta_norm', 'relative_delta', 'cosine']}}
               for s in t['sites']]
    assert next(s['name'] for s in profile if s['delta_norm'] > 0) == f"L{r['layer']}.mlp"
    last_residual = max((s for s in t['sites'] if s['component'] == 'residual'), key=lambda s: s['layer'])
    steps = []
    for step, fwd in zip(t['logits']['steps'], t['forward_steps']):
        candidates = {c['token_id']: c for c in step['candidates']}
        actual = candidates[step['generated_token_id']]
        clean = candidates[step['clean_top_token_ids'][0]]
        steer = candidates[step['steer_top_token_ids'][0]]
        p = fwd['observed_start'] + fwd['observed_count'] - 1
        steps.append({**{k: step[k] for k in ['step', 'kl_steer_to_clean', 'clean_entropy', 'steer_entropy',
                                             'clean_stop_advantage', 'steer_stop_advantage']},
                      'actual': actual['token_text'], 'actual_is_eos': actual['is_eos'],
                      'clean_top': clean['token_text'], 'steer_top': steer['token_text'],
                      'clean_actual_gap': clean['clean_logit'] - actual['clean_logit'],
                      'steer_actual_gap': steer['steer_logit'] - actual['steer_logit'],
                      'final_residual_delta': last_residual['delta_norm'][p],
                      'final_residual_relative_delta': last_residual['relative_delta'][p],
                      'final_residual_cosine': last_residual['cosine'][p]})
    assert len(steps) == len(t['generated_token_ids'])
    assert all(s['steer_actual_gap'] == 0 for s in steps)
    half = steps[len(steps) // 2:]
    cases.append({'trace_id': key, 'model': row['model'], 'layer': r['layer'], 'channel': r['channel'],
                  'dose': r['intervention']['dose'], 'prompt': r['prompt'],
                  'baseline': baselines[row['model'], r['question_id']], 'intervened': r['output'],
                  'trace_path': str(paths[key].relative_to(ROOT)),
                  'record_path': str(record_path.relative_to(ROOT)),
                  'prompt_last_profile': profile, 'steps': steps,
                  'first_strict_clean_divergence': next((s['step'] for s in steps if s['clean_actual_gap'] > 0), None),
                  'last_half_steps': len(half),
                  'last_half_clean_also_maximizes_actual': sum(s['clean_actual_gap'] == 0 for s in half),
                  'last_half_clean_prefers_eos': sum(s['clean_stop_advantage'] > 0 for s in half),
                  'last_half_steer_prefers_eos': sum(s['steer_stop_advantage'] > 0 for s in half)})
OUT.write_text(json.dumps({'scope': '11 selected Q04 archived cases; descriptive, not prevalence estimates',
                           'new_inference': False, 'cases': cases}, ensure_ascii=False, indent=2) + '\n')
for c in cases:
    injection = next(s for s in c['prompt_last_profile'] if s['name'] == f"L{c['layer']}.mlp")
    final = c['steps'][0]
    print(c['trace_id'], 'n=',len(c['steps']), 'first_div=', c['first_strict_clean_divergence'],
          'MLPrel=',round(injection['relative_delta'],4),
          'finalrel=',round(final['final_residual_relative_delta'],4),
          'cos=',round(final['final_residual_cosine'],4),
          'KL=',round(final['kl_steer_to_clean'],4),
          'clean/actual=',repr(final['clean_top']),repr(final['actual']),
          'shadow_agree_last_half=',c['last_half_clean_also_maximizes_actual'],'/',c['last_half_steps'])
