"""Read-only export of completed B receipts; run from the remote repository root."""
import hashlib
import json
from pathlib import Path

p = Path('external/wsp-vlm-open-repair-v8-2026-11-05/B')
sources = {}


def read(path):
    raw = path.read_bytes()
    sources[str(path)] = hashlib.sha256(raw).hexdigest()
    return json.loads(raw)


s = read(p / 'state.json')
evaluations = []
for v in s['evaluations'].values():
    e = read(p / v['path'])
    assert sources[str(p / v['path'])] == v['sha256']
    evaluations.append({k: e[k] for k in ('candidate', 'full_development', 'summary', 'scored')})
rounds = []
for f in sorted(p.glob('artifacts/repair-round-*.json')):
    r = read(f)
    r['manifest'] = read(p / 'candidates' / r['candidate'] / 'manifest.json')
    rounds.append(r)
requests = [read(f) for f in sorted(p.glob('inbox/*.json'))]
print(json.dumps(dict(state=s, rounds=rounds, evaluations=evaluations,
                     requests=requests, source_sha256=sources), ensure_ascii=False))
