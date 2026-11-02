"""QCD-01 stage S verification addendum (DEVIATIONS X4).  The launch controller's aggregate check failed only on 'formations'
(3132 > 3024): the contract budget table omitted the 108 C_b recomputations that contract §0 item 4 requires (29 formations per
text, not 28).  This addendum re-runs the frozen verify_worker on both workers, checks the unit count, and checks every aggregate
limit with 'formations' corrected to 108 x 29 = 3132; all other limits are the frozen ones.  The controller.json failure is kept.
python analysis/verify_addendum_r01.py runs/sformal-r01"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import qcd_run as R  # noqa: E402

out = (HERE / sys.argv[1]).resolve()
auth = R.exp.read(out / 'worker-0' / 'authorization.json')
results = [R.verify_worker(out / f'worker-{w}') for w in range(2)]
units = sum(x['units'] for x in results)
assert units == 108, units
calls = {k: sum(x['model_calls'][k] for x in results) for k in results[0]['model_calls']}
declared = dict(R.LIMITS['sformal'])
corrected = dict(declared, formations=108 * 29)
assert calls['formations'] == corrected['formations'], calls['formations']
assert all(calls[k] <= corrected[k] for k in corrected), (calls, corrected)
gpu_s = sum(x['wall_seconds'] for x in results)
assert gpu_s <= 5 * 3600, gpu_s
R.exp.write(out / 'verification.json', {
    'status': 'passed', 'stage': 'sformal', 'freeze_sha256': auth['freeze_sha256'], 'workers': results, 'units': units,
    'model_calls': calls, 'verified_at': R.exp.utc(), 'verified_by': 'analysis/verify_addendum_r01.py (controller aggregate check failed; see DEVIATIONS X4)',
    'deviation': {'formations_declared_limit': declared['formations'], 'formations_actual': calls['formations'],
                  'reason': 'contract budget table omitted the per-text C_b recomputation required by contract §0 item 4',
                  'other_limits': 'all within the frozen limits', 'gpu_device_seconds': gpu_s, 'gpu_cap_seconds': 5 * 3600}}, immutable=True)
print('verification written', calls, round(gpu_s))
