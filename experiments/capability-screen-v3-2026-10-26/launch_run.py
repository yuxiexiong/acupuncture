"""Start the authorized two workers and one CPU finisher exactly once."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

from prepare_panel import read, sha, utc, write

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--dry-run', action='store_true')
args = parser.parse_args()
root = Path(__file__).resolve().parent
protocol = read(root / 'protocol.json')
assert protocol['status'] == 'frozen_before_formal_inference'
for name, digest in protocol['source_sha256'].items():
    assert sha(root / name) == digest, name
for name in ('panel_manifest', 'reuse_manifest'):
    assert sha(root / f'{name}.json') == protocol[f'{name}_sha256']
reuse = read(root / 'reuse_manifest.json')
stop_path = root / reuse['stop_receipt']['file']
assert sha(stop_path) == reuse['stop_receipt']['sha256']
stop = read(stop_path)
assert stop['status'] == 'stopped_by_user' and not stop['remaining_live_processes']
for old in stop['leaders']:
    proc = Path(f"/proc/{old['pid']}/cmdline")
    assert not proc.exists() or b'capability-damage-v2-2026-10-26' not in proc.read_bytes()
for name in ('launch.json', 'worker-0.json', 'worker-1.json', 'finish-r01'):
    assert not (root / name).exists(), f'Preserve existing attempt: {name}'
jobs = [(f'worker-{gpu}', [sys.executable, '-u', str(root / 'run_worker.py'), '--gpu', str(gpu)]) for gpu in range(2)]
jobs.append(('finish', [sys.executable, '-u', str(root / 'finish_run.py')]))
if args.dry_run:
    print({'status': 'checked_without_launch', 'jobs': jobs}, flush=True)
else:
    environment = dict(os.environ, HF_HOME='/workspace/acupuncture/.cache/hf',
        HF_HUB_OFFLINE='1', HF_DATASETS_OFFLINE='1', HF_ENDPOINT='https://hf-mirror.com',
        OMP_NUM_THREADS='4', MKL_NUM_THREADS='4', TOKENIZERS_PARALLELISM='false',
        PYTHONDONTWRITEBYTECODE='1')
    receipt = {'status': 'launching', 'started_utc': utc(), 'protocol_sha256': sha(root / 'protocol.json'),
        'counts': protocol['counts'], 'reused_pairs': reuse['counts'], 'processes': []}
    write(root / 'launch.json', receipt)
    for name, command in jobs:
        log = root / f'{name}-supervisor.log'
        with log.open('xb') as stream:
            process = subprocess.Popen(command, cwd=root, env=environment,
                stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        receipt['processes'].append({'name': name, 'pid': process.pid, 'command': command, 'log': str(log)})
        write(root / 'launch.json', receipt)
        if name == 'finish':
            write(root / 'finish-launch.json', receipt['processes'][-1])
    receipt.update(status='launched', ended_utc=utc())
    write(root / 'launch.json', receipt)
    print(receipt, flush=True)
