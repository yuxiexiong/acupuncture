"""One-time byte-preserving import; run from the delivery worktree, never the source."""
import collections
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

source = Path(sys.argv[1]).resolve()
root = Path.cwd().resolve()
assert source != root
archive = Path('migration/2026-11-04-evidence-archive-r01')
runtime = Path('experiments/wsp-process-reproduction-v1-2026-11-03/local-runtime-archive-r01')
assert not (archive / 'local-import.json').exists(), 'Import snapshot already exists'
def git(*args):
    return subprocess.check_output(['git', *args], cwd=source).decode()
def sha(data):
    return hashlib.sha256(data).hexdigest()
paths = set(filter(None, git('ls-files', '--others', '--exclude-standard', '-z').split('\0')))
paths.update(filter(None, git('diff', '--name-only', '-z').split('\0')))
entries = []
for name in sorted(paths):
    src = source / name
    if not src.is_file():
        continue
    data = src.read_bytes()
    row = {'source': name, 'bytes': len(data), 'sha256': sha(data),
           'captured_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    dst = Path(name)
    if name.endswith('/private-key.json'):
        row.update(action='manifest_only', reason='Private blinding map; preserved locally')
    elif name == 'external/wcp01-observer/mbpp.jsonl':
        row.update(action='manifest_only', reason='Upstream benchmark copy; committed WCP source manifest supplies origin')
    elif name.endswith('.lock'):
        row.update(action='manifest_only', reason='Transient process lock, not a result')
    elif dst.exists() and dst.read_bytes() == data:
        row.update(action='already_identical', destination=name)
    else:
        if dst.exists():
            dst = archive / 'local-variants' / name
            row.update(action='historical_variant', current_sha256=sha(Path(name).read_bytes()))
        elif name.startswith('external/'):
            dst = runtime / name
            row.update(action='runtime_snapshot')
        else:
            row.update(action='import_missing')
        assert not dst.exists(), dst
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
        assert sha(dst.read_bytes()) == row['sha256']
        row['destination'] = str(dst)
    entries.append(row)
result = {'source_root': str(source), 'source_head': git('rev-parse', 'HEAD').strip(),
          'delivery_base': subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip(),
          'scope': 'Local untracked and modified tracked files; runtime is a non-atomic per-file snapshot',
          'counts': dict(collections.Counter(x['action'] for x in entries)), 'entries': entries}
(archive / 'local-import.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print(result['counts'])
print('copied bytes', sum(x['bytes'] for x in entries if x['action'] in ('import_missing','runtime_snapshot','historical_variant')))
