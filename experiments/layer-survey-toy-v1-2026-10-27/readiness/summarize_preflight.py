"""Technical timings only; never reads response text for semantic evaluation."""
import json
from pathlib import Path
import statistics
import sys

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
import survey

result = {'status': 'gpu_ready_pending_formal_authorization', 'formal_started': False,
          'freeze_sha256': survey.check_freeze(), 'models': {}, 'eta': {}}
point, capped, bytes_expected = 0., 0., 0.
for mid, conditions in [('2b',240),('4b',320),('9b',320)]:
    run = root / 'preflight-r02' / mid
    receipt = survey.verify(run)
    assert (run.parent / f'{mid}.exit').read_text().strip() == '0'
    records = [json.loads(p.read_text()) for p in (run/'records').glob('*.json')]
    positive = [r for r in records if r['intervention'] and r['intervention']['dose'] == 1]
    baseline = [r for r in records if r['condition_id'] == 'baseline']
    lengths = [r['output']['generated_token_count'] for r in positive]
    times = [r['output']['batch_seconds'] for r in positive]
    # Fit the local timing model only; the answers themselves are not evaluated.
    x = [r['output']['generated_token_count'] for r in records]
    y = [r['output']['batch_seconds'] for r in records]
    mx, my = statistics.mean(x), statistics.mean(y)
    slope = sum((a-mx)*(b-my) for a,b in zip(x,y))/sum((a-mx)**2 for a in x)
    intercept = max(0., my-slope*mx)
    fixed = max(0., receipt['wall_seconds']-sum(y))
    baseline_seconds = sum(r['output']['batch_seconds'] for r in baseline)
    count = conditions*8
    # Both GPUs run one shard/model, with stage barriers. Baselines belong to shard 0 only.
    predicted = fixed + count/2 * statistics.mean(times) + baseline_seconds
    cap = fixed + count/2 * (intercept+slope*128) + baseline_seconds
    result['models'][mid] = dict(preflight_records=len(records), positive_records=len(positive),
        positive_mean_tokens=statistics.mean(lengths), positive_cap_count=sum(n==128 for n in lengths),
        positive_mean_seconds=statistics.mean(times), positive_tokens_per_second=sum(lengths)/sum(times),
        observed_wall_seconds=receipt['wall_seconds'], observed_fixed_overhead_seconds=fixed,
        fitted_seconds_per_token=slope, fitted_intercept_seconds=intercept,
        formal_dual_gpu_point_seconds=predicted, formal_dual_gpu_128_scenario_seconds=cap,
        record_bytes=sum(p.stat().st_size for p in (run/'records').glob('*.json')))
    point += predicted
    capped += cap
    bytes_expected += result['models'][mid]['record_bytes']/22*(count+8)
result['eta'] = dict(dual_gpu_point_seconds=point, dual_gpu_all_modified_128_seconds=capped,
    raw_record_bytes_estimate=bytes_expected,
    assumptions=['Two idle H20 GPUs; one model worker per GPU; fixed BF16 eager batch1 code.',
    'Model stages 2B then 4B then 9B, both shards in parallel at each stage; no queue time.',
    'Point estimate extrapolates eight preflight positive answers/model across all sampled channels.',
    '128-token scenario uses timing regression, not a guaranteed worst-case time.',
    'Small timing sample does not establish the survey-wide response-length distribution.',
    'Observed fixed overhead includes asset hashing, loading, calibration and final weight verification.',
    'Final verification, export and copying are recorded separately; no arbitrary safety multiplier.'])
(root/'readiness/gpu-readiness.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
