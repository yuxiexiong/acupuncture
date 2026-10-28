#!/usr/bin/env python3
"""Descriptive CPU-only audit of archived L0-L5 traces; no inference or new labels."""
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
import gzip
import json
from pathlib import Path
from statistics import median
import sys

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[2]
EPS = 1e-6  # BF16 ties are exact; require a strictly worse clean logit.


def ratio(a, b):
    return a / b if b else None


def extract(job):
    key, source, baseline, record_path, trace_path, dose_channel = job
    r = source['record']
    archived = json.loads(Path(record_path).read_text())
    with gzip.open(trace_path, 'rt') as fh:
        t = json.load(fh)
    tokens = t['generated_token_ids']
    assert archived['checks_passed'] and archived['source_token_ids_match']
    assert tokens == archived['output']['token_ids'] == r['output']['token_ids']
    p = t['prompt_token_count'] - 1
    assert t['observed_input_token_ids'] == t['input_token_ids'] + tokens[:-1]
    assert t['observed_position_count'] == p + len(tokens)
    assert len(t['logits']['steps']) == len(tokens) == len(t['forward_steps'])
    assert all(s['step'] == i and s['observed_start'] == (0 if i == 0 else p + i)
               for i, s in enumerate(t['forward_steps']))
    layer = r['layer']
    dose = r['intervention']['dose'] if r.get('intervention') else 0
    sites = sorted(t['sites'], key=lambda s: (s['layer'], ['attention', 'mlp', 'residual'].index(s['component'])))
    metrics = ['clean_norm', 'steer_norm', 'delta_norm', 'relative_delta', 'cosine']
    assert all(len(s[m]) == t['observed_position_count'] for s in sites for m in metrics)
    first = [dict(layer=s['layer'], component=s['component'], module_type=s['module_type'],
                  **{m: s[m][p] for m in metrics}) for s in sites]
    residuals = [s for s in sites if s['component'] == 'residual']
    mlps = [s for s in sites if s['component'] == 'mlp']
    pre_sites = sites if layer is None else [s for s in sites if s['layer'] < layer or (s['layer'] == layer and s['component'] == 'attention')]
    pre_max = max(max(s['delta_norm']) for s in pre_sites)
    changed = [s for s in first if s['delta_norm'] > EPS]
    final = residuals[-1]
    injected = residuals[layer] if layer is not None else None
    expected = abs(dose) * r['calibration']['residual_scales'][str(layer)] if layer is not None else 0
    downstream = [s['delta_norm'][p] for s in residuals if layer is not None and s['layer'] >= layer]
    peak = max(first, key=lambda s: s['delta_norm'])
    relative_peak = max(first, key=lambda s: s['relative_delta'] or 0)
    step_rows, seen4 = [], set()
    for i, s in enumerate(t['logits']['steps']):
        assert s['step'] == i and s['generated_token_id'] == tokens[i]
        actual = next(c for c in s['candidates'] if c['token_id'] == tokens[i])
        clean_max = max(c['clean_logit'] for c in s['candidates'])
        steer_max = max(c['steer_logit'] for c in s['candidates'])
        cg, sg = clean_max - actual['clean_logit'], steer_max - actual['steer_logit']
        assert sg < EPS, (key, i, sg)
        gram = tuple(tokens[i-3:i+1]) if i >= 3 else None
        repeat4 = gram in seen4 if gram else False
        if gram:
            seen4.add(gram)
        step_rows.append(dict(step=i, token_id=tokens[i], token_text=actual['token_text'],
            actual_is_eos=actual['is_eos'], clean_gap=cg, steer_gap=sg,
            actual_logprob_gain=actual['steer_logprob']-actual['clean_logprob'],
            kl=s['kl_steer_to_clean'], clean_entropy=s['clean_entropy'], steer_entropy=s['steer_entropy'],
            clean_stop_advantage=s['clean_stop_advantage'], steer_stop_advantage=s['steer_stop_advantage'],
            clean_argmax_is_eos=s['clean_argmax_is_eos'], repeat4=repeat4,
            injected_mlp_delta=mlps[layer]['delta_norm'][p+i] if layer is not None else None,
            injected_residual_delta=injected['delta_norm'][p+i] if injected else None,
            final_residual_delta=final['delta_norm'][p+i], final_residual_relative=final['relative_delta'][p+i],
            residual_delta_peak_layer=max(residuals, key=lambda x: x['delta_norm'][p+i])['layer']))
    strict = [s['step'] for s in step_rows if s['clean_gap'] > EPS]
    repeats = [s for s in step_rows if s['repeat4']]
    cohorts = ['baseline'] if layer is None else ['all_interventions']
    if dose == 1:
        cohorts.append('ten_point_positive1')
    if layer is not None and r['channel'] == dose_channel:
        cohorts.append('dose_channel')
    out = dict(trace_id=key, model=source['model'], layer=layer, channel=r['channel'], dose=dose,
        question_id=r['question_id'], prompt=r['prompt'], cohorts=cohorts,
        answer=r['output']['answer_text'], raw_text=r['output']['raw_text'],
        baseline_answer=baseline['output']['answer_text'], baseline_raw_text=baseline['output']['raw_text'],
        output_tokens=len(tokens), baseline_output_tokens=len(baseline['output']['token_ids']),
        empty_answer=not r['output']['answer_text'].strip(), stop_reason=r['output']['end_reason'],
        source_record=str(Path(record_path).relative_to(REPO)), source_trace=str(Path(trace_path).relative_to(REPO)),
        prompt_tokens=p+1, observed_positions=t['observed_position_count'],
        pre_injection_max_delta_all_positions=pre_max,
        first_changed_site=({k: changed[0][k] for k in ['layer', 'component']} if changed else None),
        direct_injection_expected=expected,
        injection_mlp_delta=mlps[layer]['delta_norm'][p] if layer is not None else 0,
        injection_mlp_over_expected=ratio(mlps[layer]['delta_norm'][p], expected) if layer is not None else None,
        injection_residual_delta=injected['delta_norm'][p] if injected else 0,
        injection_residual_relative=injected['relative_delta'][p] if injected else 0,
        final_residual_delta=final['delta_norm'][p], final_residual_relative=final['relative_delta'][p],
        final_residual_cosine=final['cosine'][p],
        final_over_injection_absolute_delta=ratio(final['delta_norm'][p], injected['delta_norm'][p]) if injected else None,
        residual_delta_monotonic_nondecreasing=all(b+EPS >= a for a,b in zip(downstream, downstream[1:])) if downstream else None,
        delta_peak={k:peak[k] for k in ['layer','component','delta_norm']},
        relative_peak={k:relative_peak[k] for k in ['layer','component','relative_delta']},
        first_strict_divergence_step=strict[0] if strict else None,
        reported_first_prediction_divergence=t['logits']['first_prediction_divergence'],
        strict_divergent_steps=len(strict), strict_divergent_fraction=ratio(len(strict), len(tokens)),
        first_kl=step_rows[0]['kl'], first_clean_gap=step_rows[0]['clean_gap'],
        first_clean_stop_advantage=step_rows[0]['clean_stop_advantage'],
        first_steer_stop_advantage=step_rows[0]['steer_stop_advantage'],
        first_eos_with_clean_non_eos=step_rows[0]['actual_is_eos'] and not step_rows[0]['clean_argmax_is_eos'],
        repeated4_steps=len(repeats), repeated4_fraction=ratio(len(repeats), max(1,len(tokens)-3)),
        repeated4_clean_supported_steps=sum(s['clean_gap'] <= EPS for s in repeats),
        repeated4_clean_supported_fraction=ratio(sum(s['clean_gap'] <= EPS for s in repeats), len(repeats)),
        first_sites=first, steps=step_rows)
    if layer is None:
        assert pre_max == 0 and not strict and all(s['kl'] == 0 for s in step_rows)
    return out


MEDIANS = ['output_tokens', 'baseline_output_tokens', 'direct_injection_expected', 'injection_mlp_delta',
    'injection_mlp_over_expected', 'injection_residual_delta', 'injection_residual_relative',
    'final_residual_delta', 'final_residual_relative', 'final_residual_cosine',
    'final_over_injection_absolute_delta', 'first_kl', 'first_clean_gap', 'first_clean_stop_advantage',
    'first_steer_stop_advantage', 'strict_divergent_fraction', 'repeated4_fraction', 'repeated4_clean_supported_fraction']


def aggregate(rows):
    medians = {k: median(v) if (v := [r[k] for r in rows if r[k] is not None]) else None for k in MEDIANS}
    return dict(n=len(rows), medians=medians,
        empty_answer_count=sum(r['empty_answer'] for r in rows),
        stop_reason_counts=dict(Counter(r['stop_reason'] for r in rows)),
        strict_first_step_count=sum(r['first_strict_divergence_step'] == 0 for r in rows),
        no_strict_divergence_count=sum(r['first_strict_divergence_step'] is None for r in rows),
        first_eos_with_clean_non_eos_count=sum(r['first_eos_with_clean_non_eos'] for r in rows),
        residual_monotonic_count=sum(r['residual_delta_monotonic_nondecreasing'] is True for r in rows),
        pre_injection_nonzero_count=sum(r['pre_injection_max_delta_all_positions'] != 0 for r in rows),
        max_absolute_delta_peak_layers=dict(Counter(str(r['delta_peak']['layer']) for r in rows)),
        relative_peak_layers=dict(Counter(str(r['relative_peak']['layer']) for r in rows)))


def main():
    sys.path.insert(0, str(REPO / 'experiments/neuron-explorer-multimodel-v2-2026-10-26'))
    from serve_trajectories import Evidence
    evidence = Evidence()
    selected = {k:s for k,s in evidence.sources.items() if s['record']['layer'] is None or s['record']['layer'] < 6}
    assert len(selected) == 3680 and set(Counter(s['model'] for s in selected.values()).values()) == {920}
    channels = defaultdict(set)
    for s in selected.values():
        r = s['record']
        if r['layer'] is not None and r['intervention']['dose'] != 1:
            channels[s['model'],r['layer']].add(r['channel'])
    assert len(channels) == 24 and all(len(v) == 1 for v in channels.values())
    jobs = [(k,s,evidence.baselines[s['model'],s['record']['question_id']]['record'],
             *map(str,evidence.files[k]),next(iter(channels[s['model'],s['record']['layer']])) if s['record']['layer'] is not None else None)
            for k,s in sorted(selected.items())]
    rows = []
    with ProcessPoolExecutor(max_workers=3) as pool, gzip.open(OUT / 'features.jsonl.gz', 'wt', encoding='utf-8') as fh:
        for i,r in enumerate(pool.map(extract,jobs,chunksize=8),1):
            fh.write(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')
            rows.append(r)
            if i % 400 == 0:
                print(f'{i}/3680',flush=True)
    groups = defaultdict(list)
    for r in rows:
        for cohort in r['cohorts']:
            groups[r['model'],cohort,None,None].append(r)
            if r['layer'] is not None:
                groups[r['model'],cohort,r['layer'],None].append(r)
                groups[r['model'],cohort,r['layer'],r['dose']].append(r)
    grouped = [dict(model=k[0],cohort=k[1],layer=k[2],dose=k[3],**aggregate(v)) for k,v in groups.items()]
    assert all(len(v) == {'baseline':8,'all_interventions':912,'ten_point_positive1':480,'dose_channel':480}[k[1]]
               for k,v in groups.items() if k[2] is None)
    profiles = []
    for model in sorted({r['model'] for r in rows}):
        for layer in range(6):
            sample = [r for r in rows if r['model'] == model and r['layer'] == layer]
            sites = [{**{k:s[k] for k in ['layer','component','module_type']},
                      **{k:median([r['first_sites'][i][k] for r in sample]) for k in ['clean_norm','steer_norm','delta_norm','relative_delta','cosine']}}
                     for i,s in enumerate(sample[0]['first_sites'])]
            profiles.append(dict(model=model,injection_layer=layer,n=len(sample),sites=sites))
    candidates = []
    for model in sorted({r['model'] for r in rows}):
        sample = [r for r in rows if r['model'] == model and r['layer'] is not None]
        for metric in ['first_kl','final_residual_relative','final_over_injection_absolute_delta','repeated4_fraction']:
            candidates.append(dict(model=model,ranking_metric=metric,
                records=[{k:r[k] for k in ['trace_id','layer','channel','dose','question_id','answer','baseline_answer',metric]}
                         for r in sorted(sample,key=lambda r:r[metric] or 0,reverse=True)[:4]]))
    summary = dict(schema='archived-early-trace-descriptive-v1',created_utc=datetime.now(timezone.utc).isoformat(),
        new_inference=False,formal_early_records=len(rows),counts=dict(Counter(r['model'] for r in rows)),
        method={'population':'Existing L0-L5 archived formal traces, eight fixed questions; descriptive not independent random samples.',
          'first_step':'Last prompt position, before first generated token.',
          'strict_divergence':f'Actual generated token clean_logit is below maximum clean candidate logit by >{EPS}. Top-k union includes clean argmax. Ties are not divergence.',
          'clean_shadow':'Unsteered entire branch with its own cache, forced to the same generated-token history; not current-step-only needle removal.',
          'amplification':'Final residual absolute delta / injected-layer residual absolute delta; scale growth can confound mechanism interpretation.',
          'dose':'Expected direct MLP perturbation norm = abs(dose) * original clean prompt residual calibration scale; +1 is a whole calibration residual scale, not necessarily a small intervention.',
          'cohorts':'ten_point_positive1=480/model; dose_channel=480/model; overlap48/model. all_interventions=912/model, baseline=8/model.',
          'outcomes':'Empty, EOS, limit and repeated token ngrams are mechanical indicators, not automatic semantic failure labels; no p-values.'},
        checks={'archive_status':evidence.verification['status'],'alignment_and_source_tokens':'passed for all selected traces',
          'baseline_count':sum(r['layer'] is None for r in rows),'baseline_all_sites_all_positions_exact_zero':True,
          'direct_injection_mlp_over_expected_range':[min(r['injection_mlp_over_expected'] for r in rows if r['layer'] is not None),
                                                     max(r['injection_mlp_over_expected'] for r in rows if r['layer'] is not None)],
          'pre_injection_nonzero_records':[r['trace_id'] for r in rows if r['pre_injection_max_delta_all_positions'] != 0],
          'first_changed_not_injected_mlp':[r['trace_id'] for r in rows if r['layer'] is not None and r['first_changed_site'] != {'layer':r['layer'],'component':'mlp'}]},
        groups=grouped,first_step_profiles=profiles,ranked_candidates=candidates)
    (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'counts':summary['counts'],'checks':summary['checks']},ensure_ascii=False),flush=True)


if __name__ == '__main__':
    main()
