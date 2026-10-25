"""One-time user-authorized stop; preserve the old run and identify exact groups."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import shutil
import signal
import time

root = Path('/workspace/acupuncture/experiments/capability-damage-v2-2026-10-26')
output = root / 'user-stop-20261026-r01'
output.mkdir(exist_ok=False)

def utc():
    return datetime.now(timezone.utc).isoformat()

def write(value):
    (output / 'receipt.json').write_text(json.dumps(value, indent=2) + '\n')

leaders = []
for name in ('finish-launch.json', 'worker-0.json', 'worker-1.json'):
    pid = json.loads((root / name).read_text())['pid']
    command = Path(f'/proc/{pid}/cmdline').read_bytes().replace(b'\0', b' ').decode()
    assert str(root) + '/' in command and os.getpgid(pid) == pid
    leaders.append({'pid': pid, 'pgid': pid, 'command': command})
paths = [root / 'worker-0.json', root / 'worker-1.json', root / 'finish-launch.json',
         root / 'finish-r01/receipt.json', *sorted((root / 'outputs').glob('*/receipt.json'))]
for path in paths:
    target = output / 'before' / path.relative_to(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
receipt = {'status': 'stopping', 'requested_by': 'user', 'started_utc': utc(), 'leaders': leaders,
           'reason': 'Replace full run with MMLU1000 ARC200 GSM100 HumanEval100 paired panel', 'signals': []}
write(receipt)
for leader in leaders:
    os.killpg(leader['pgid'], signal.SIGINT)
    receipt['signals'].append({'pgid': leader['pgid'], 'signal': 'SIGINT'})
time.sleep(5)
for leader in leaders:
    try:
        os.killpg(leader['pgid'], signal.SIGTERM)
        receipt['signals'].append({'pgid': leader['pgid'], 'signal': 'SIGTERM'})
    except ProcessLookupError:
        pass
time.sleep(2)
remaining = []
for path in Path('/proc').iterdir():
    if not path.name.isdigit():
        continue
    try:
        if os.getpgid(int(path.name)) in [row['pgid'] for row in leaders] and (path / 'stat').read_text().split()[2] != 'Z':
            remaining.append(int(path.name))
    except (FileNotFoundError, ProcessLookupError):
        pass
receipt['remaining_live_processes'] = remaining
receipt['tasks'] = {}
for folder in sorted((root / 'outputs').iterdir()):
    if not folder.is_dir():
        continue
    count = 0
    for path in folder.glob('*.jsonl'):
        for line in path.open():
            row = json.loads(line)
            assert row['status'] == 'completed' and set(row['outputs']) == {'baseline', 'evo'}
            count += 1
    receipt['tasks'][folder.name] = {'completed_pairs': count,
        'partial_files': [str(path.relative_to(root)) for path in sorted(folder.glob('*.partial.json'))]}
for path in paths:
    target = output / 'after' / path.relative_to(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
inventory = output / 'preserved-file-hashes.jsonl'
with inventory.open('x') as stream:
    for path in sorted((root / 'outputs').rglob('*')):
        if path.is_file():
            stream.write(json.dumps({'path': str(path.relative_to(root)), 'bytes': path.stat().st_size,
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}) + '\n')
receipt.update(status='stopped_by_user' if not remaining else 'stop_incomplete', ended_utc=utc(),
    protocol_sha256=hashlib.sha256((root / 'protocol.json').read_bytes()).hexdigest(),
    inventory_sha256=hashlib.sha256(inventory.read_bytes()).hexdigest(),
    note='All original files retained. Interrupted records are not scored as model errors.')
write(receipt)
print(json.dumps(receipt), flush=True)
assert not remaining
