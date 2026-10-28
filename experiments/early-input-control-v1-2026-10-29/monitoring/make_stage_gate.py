"""Generic stage gate + formal authorization writer (through experiment.write), then dry validation.

python make_stage_gate.py STAGE PANEL REV OUT_ROOT SELECTION_OR_- EXTRA_EVIDENCE_JSON FLAGS_JSON [CONFIRMATION_LOCK_OR_-] [SOURCE_MANIFEST_OR_-]
"""
import json
import sys
sys.path.insert(0, '/workspace/acupuncture/experiments/early-input-control-v1-2026-10-29')
import experiment as ex
from execution import validate_formal_authorization

stage, panel, rev, out_root, selection, extra, flags = sys.argv[1:8]
lock = sys.argv[8] if len(sys.argv) > 8 and sys.argv[8] != '-' else None
manifest = sys.argv[9] if len(sys.argv) > 9 and sys.argv[9] != '-' else None
H = ex.HERE
freeze = 'freeze-r03.json'
base = {'preflight_evidence_path': 'runs/preflight-r04/verification.json',
        'data_review_path': 'readiness/independent-data-review-r01.json',
        'cpu_evidence_path': 'readiness/cpu-receipt-r05.json'}
paths = list(base.values()) + json.loads(extra)
if selection != '-':
    paths.append(selection)
if lock:
    paths.append(lock)
if manifest:
    paths.append(manifest)
evidence = {p: ex.sha(H / p) for p in dict.fromkeys(paths)}
tag = f'{stage}-{panel}' if stage in ('mechanism', 'patch') else stage
gate_path = f'readiness/stage-gate-{tag}-{rev}.json'
gate = {'status': 'passed', 'stage': stage, 'panel': panel, 'experiment': H.name, 'freeze_path': freeze,
        'freeze_sha256': ex.sha(H / freeze), 'created_at': ex.utc(), 'evidence_hashes': evidence, **json.loads(flags)}
ex.write(H / gate_path, gate, immutable=True)
auth_path = f'readiness/formal-authorization-{tag}-{rev}.json'
auth = {'status': 'authorized', 'experiment': H.name, 'created_at': ex.utc(),
        'user_instruction': '你按照handoff指令一直跑到实验结束，如果有bug和问题，按照实验设计文档中的内容修复，然后续跑。半小时更新一次eta和实验运行情况',
        'allowed_stages': [stage], 'formal_execution_authorized': True, 'maximum_workers': 2, 'panel': panel,
        'freeze_path': freeze, 'freeze_sha256': ex.sha(H / freeze), 'output_root': out_root, **base,
        'stage_gate_path': gate_path}
required = {p: evidence[p] for p in base.values()}
if selection != '-':
    auth['selection_path'] = selection; required[selection] = evidence[selection]
if lock:
    auth['confirmation_lock_path'] = lock; required[lock] = evidence[lock]
if manifest:
    auth['source_manifest_path'] = manifest; required[manifest] = evidence[manifest]
required[gate_path] = ex.sha(H / gate_path)
auth['required_evidence'] = required
ex.write(H / auth_path, auth, immutable=True)
a = ex.authorize(str(H / auth_path), stage, True)
validate_formal_authorization(a, stage)
for s in ('development', 'confirmation', 'mechanism', 'patch', 'preflight'):
    if s == stage:
        continue
    try:
        ex.authorize(str(H / auth_path), s, True); print('UNEXPECTED accept', s)
    except (AssertionError, KeyError):
        print('rejected', s)
print('gate', gate_path, ex.sha(H / gate_path)); print('auth', auth_path, ex.sha(H / auth_path))
