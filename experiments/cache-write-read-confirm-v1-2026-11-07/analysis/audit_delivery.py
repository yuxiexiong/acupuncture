"""CPU delivery audit; uses frozen parser and statistics, never calls a model."""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
import dwc_analysis as A

def read(p):
    return json.loads(p.read_text())

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

run = HERE / 'runs/formal-r01'
freeze = read(HERE / 'freeze-r02.json')
assert all(sha(REPO / p) == h for p, h in freeze['files'].items())
ver, recs = A.A.load(run)
saved = read(HERE / 'analysis/dwc-readouts-formal-r01.json')
recomputed = A.analyse(recs)
assert recomputed == {k: v for k, v in saved.items() if k != 'source'}
assert saved['source']['verification_sha256'] == sha(run / 'verification.json')
assert saved['source']['freeze_sha256'] == sha(HERE / 'freeze-r02.json')
receipts = [read(run / f'worker-{w}/receipt.json') for w in (0, 1)]
assert all(r['status'] == 'completed' for r in receipts)
assert all(read(run / f'worker-{w}/exit.json')['returncode'] == 0 for w in (0, 1))
assert sum(r['summary']['units'] for r in receipts) == 96
assert sum(r['model_calls']['trajectories'] for r in receipts) == 81648
primary = [r for r in recs.values() if not r.get('diagnostic_donor')]
assert len(primary) == 864 and len(recs) == 1296
budget = read(HERE / 'readiness/budget-extension-authorization-r01.json')
formal = sum(r['wall_seconds'] for r in receipts)
preflight = sum(x['wall_seconds'] for x in read(HERE / 'runs/preflight-r01/verification.json')['workers'])
assert formal <= budget['new_formal_gpu_process_seconds']
assert all(r['wall_seconds'] <= budget['per_worker_seconds'] for r in receipts)
assert formal + preflight <= budget['all_in_ceiling_seconds']
recovery = read(HERE / 'readiness/final-verification-recovery-r01.json')
assert sha(run / 'controller.json') == recovery['original_controller_sha256']
assert sha(REPO / recovery['relocation']['new']) == recovery['relocation']['sha256']
conflicts = {}
for d in A.K.DIRS:
    out = {a: 0 for a in ('L11d', 'withdrawD', 'withdrawE')}
    n = 0
    for r in primary:
        for donor in r['donors']:
            if donor['type'] not in ('AL', 'BD'):
                continue
            n += 1
            for arm in out:
                nr = r['directions'][d][arm + '|' + donor['id']]['N']
                out[arm] += A.A.row_out(nr, r['item']) == r['self_row']
    assert n == 3456
    for j in ('D', 'E'):
        assert abs((out['withdraw'+j]-out['L11d'])/n-saved['directions'][d]['uses'][j]['R']['mean']) < 1e-12
    conflicts[d] = dict(n=n, self_correct=out)
out = dict(status='passed',scope='Author CPU delivery self-check; not independent review',
    frozen_files=len(freeze['files']),freeze_sha256=sha(HERE/'freeze-r02.json'),
    verification_sha256=sha(run/'verification.json'),analysis_sha256=sha(HERE/'analysis/dwc-readouts-formal-r01.json'),
    raw_hashed_files=sum(len(r['record_hashes']) for r in receipts),scenes=96,receivers=864,diagnostic_donors=432,
    trajectories=81648,conflict_counts=conflicts,
    zero_t2=sum(r['gates']['zero_t2'] for r in primary),read_hooks=sum(r['gates']['read_hooks'] for r in primary),
    oracle_max={k:max(r['gates'][k] for r in primary) for k in ('write_oracle_max','read_oracle_max','de_reference_max')},
    formal_gpu_process_hours=formal/3600,preflight_gpu_process_hours=preflight/3600,all_in_gpu_process_hours=(formal+preflight)/3600,
    exact_frozen_analysis_recomputation=True,original_controller_failure_preserved=True)
target=HERE/'analysis/delivery-audit.json'
with target.open('x') as f:
    json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(out,ensure_ascii=False,indent=2))
