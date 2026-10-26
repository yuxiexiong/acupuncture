"""One-time recovery of the verified 9B exporter network-retry stall."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from datetime import datetime, timezone

root = Path('/workspace/acupuncture/experiments/transfer-toy-v1-2026-10-26')
run = root / 'runs/transfer-9b-2b-r01'
queue_pid, export_pid = 1408445, 1458925
read = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
utc = lambda: datetime.now(timezone.utc).isoformat()

for name in ('freeze.json', 'freeze_parallel.json'):
    for path, digest in read(root / name)['files'].items():
        assert sha(root / path) == digest, path
for pid, script in ((queue_pid, 'run_queue_parallel.py'), (export_pid, 'export_results_parallel.py')):
    cmd = Path(f'/proc/{pid}/cmdline').read_bytes().decode().split('\0')
    assert str(root / script) in cmd and str(run) in cmd, (pid, cmd)
state = read(run / 'queue_receipt.json')
assert state['pid'] == queue_pid and state['current_stage'] == 'target9b-export'
job = state['stages'][-1]['jobs'][0]
assert job['pid'] == export_pid and job['status'] == 'running'
assert 'Network is unreachable' in Path(job['log']).read_text()
evidence = run / 'offline-export-recovery-r01'
evidence.mkdir(exist_ok=False)
record = {'status': 'starting', 'started_utc': utc(), 'old_queue_pid': queue_pid,
          'old_export_pid': export_pid, 'reason': 'Cached pinned datasets repeatedly queried offline network',
          'frozen_code_changed': False, 'inference_restarted': False,
          'script_sha256': sha(Path(__file__)), 'old_queue': state,
          'environment': {'HF_HOME': '/workspace/acupuncture/.cache/hf',
                          'HF_HUB_OFFLINE': '1', 'HF_DATASETS_OFFLINE': '1'}}
save = lambda: (evidence / 'receipt.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
save()
os.kill(queue_pid, signal.SIGSTOP)
try:
    assert read(run / 'queue_receipt.json')['current_stage'] == 'target9b-export'
    assert read(run / 'target9b/export-r01/receipt.json')['status'] == 'running'
    os.kill(export_pid, signal.SIGTERM)
    for _ in range(100):
        p = Path(f'/proc/{export_pid}/stat')
        if not p.exists() or p.read_text().split()[2] == 'Z':
            break
        time.sleep(.1)
    else:
        raise RuntimeError('Exporter did not stop; no retry started')
    os.kill(queue_pid, signal.SIGTERM)
finally:
    os.kill(queue_pid, signal.SIGCONT)
for _ in range(100):
    p = Path(f'/proc/{queue_pid}/stat')
    if not p.exists() or p.read_text().split()[2] == 'Z':
        break
    time.sleep(.1)
else:
    raise RuntimeError('Queue did not stop; no retry started')
archive = run / 'target9b/export-network-retry-r01'
assert not archive.exists()
(run / 'target9b/export-r01').rename(archive)
record.update(archived_export=str(archive), stopped_utc=utc())
save()
cmd = ['/workspace/acupuncture/.venv-bench/bin/python', str(root / 'run_queue_parallel.py'),
       '--run', str(run), '--resume', '--workers', '6', '--validation',
       str(root / 'optimization-check-r01/runtime-three-r01/receipt.json')]
with (evidence / 'queue.log').open('x') as stream:
    child = subprocess.Popen(cmd, cwd=root, env={**os.environ, **record['environment']},
                             stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
record.update(status='resumed_pending_verification', new_queue_pid=child.pid, command=cmd,
              resumed_utc=utc())
save()
print(json.dumps({k: record[k] for k in ('status', 'new_queue_pid', 'archived_export', 'resumed_utc')}))
