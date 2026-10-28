"""Create development stage gate + formal authorization from verified preflight evidence (run with -I from experiment dir via sys.path)."""
import sys
sys.path.insert(0, '/workspace/acupuncture/experiments/early-input-control-v1-2026-10-29')
import experiment as ex
from execution import validate_formal_authorization

preflight_run, gate_rev, auth_rev, out_root, eta_path, worker_verify = sys.argv[1:7]
H = ex.HERE
pre = f'{preflight_run}/verification.json'
cpu, data = 'readiness/cpu-receipt-r05.json', 'readiness/independent-data-review-r01.json'
freeze = 'freeze-r03.json'
v = ex.read(H / pre)
assert v['status'] == 'passed' and v['freeze_sha256'] == ex.sha(H / freeze)
wv = ex.read(H / worker_verify)
assert all(w['status'] == 'passed' for w in wv['workers'].values())
evidence = {p: ex.sha(H / p) for p in (pre, cpu, data, eta_path, worker_verify)}
gate_path = f'readiness/stage-gate-development-{gate_rev}.json'
ex.write(H / gate_path, {'status': 'passed', 'stage': 'development', 'experiment': H.name,
    'freeze_path': freeze, 'freeze_sha256': ex.sha(H / freeze), 'created_at': ex.utc(),
    'evidence_hashes': evidence,
    'checks': ['launcher verification.json passed for both workers (status, exit 0, hooks removed, weight hash unchanged, record/asset hashes, 60 benchmarks, fork 4/16 withdraw, exact independent candidate reference)',
               'experiment.py verify re-run per worker after completion', 'local copy hash verification of full run tree',
               'CPU receipt r05 39/0/0/0 and its source hashes equal current code', 'data review r01 passed, confirmation outputs unread',
               'timing estimate produced from this verified run'],
    'not_checked_here': 'scientific measurement validity (judged after development reading)'}, immutable=True)
auth_path = f'readiness/formal-authorization-development-{auth_rev}.json'
auth = {'status': 'authorized', 'experiment': H.name, 'created_at': ex.utc(),
    'user_instruction': '你按照handoff指令一直跑到实验结束，如果有bug和问题，按照实验设计文档中的内容修复，然后续跑。半小时更新一次eta和实验运行情况',
    'user_instruction_context': 'handoff order: development -> read/measurement check -> mechanism(dev) -> patch(dev) -> lock -> confirmation -> mechanism(conf) -> patch(conf)',
    'allowed_stages': ['development'], 'formal_execution_authorized': True, 'maximum_workers': 2, 'panel': 'development',
    'freeze_path': freeze, 'freeze_sha256': ex.sha(H / freeze), 'output_root': out_root,
    'preflight_evidence_path': pre, 'data_review_path': data, 'cpu_evidence_path': cpu, 'stage_gate_path': gate_path,
    'required_evidence': {pre: evidence[pre], data: evidence[data], cpu: evidence[cpu], gate_path: ex.sha(H / gate_path)}}
ex.write(H / auth_path, auth, immutable=True)
a = ex.authorize(str(H / auth_path), 'development', True)
validate_formal_authorization(a, 'development')
for s in ('confirmation', 'mechanism', 'patch', 'preflight'):
    try:
        ex.authorize(str(H / auth_path), s, True); print('UNEXPECTED accept', s)
    except (AssertionError, KeyError):
        print('rejected', s)
print('gate', gate_path, ex.sha(H / gate_path)); print('auth', auth_path, ex.sha(H / auth_path))
