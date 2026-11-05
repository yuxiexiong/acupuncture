"""Export saved B/C results and full answer text; read-only, no model imports."""
import gzip
import hashlib
import json
from pathlib import Path
import sys
import time

root = Path('external/wsp-vlm-open-repair-v8-2026-11-05')
out = dict(exported_unix=time.time(), model_calls=0, independent_confirmation=False, runs={})
for task in 'BC':
    p = root / task
    hashes = {}
    def read(path):
        raw = path.read_bytes()
        hashes[str(path)] = hashlib.sha256(raw).hexdigest()
        return json.loads(raw)
    state = read(p / 'state.json')
    assert state['research_done'] and state['repair_rounds_completed'] == 50
    rounds = [read(f) for f in sorted(p.glob('artifacts/repair-round-*.json'))]
    assert len(rounds) == 50 and len({r['signature'] for r in rounds}) == 50
    evaluations = []
    for ref in state['evaluations'].values():
        e = read(p / ref['path'])
        assert hashes[str(p / ref['path'])] == ref['sha256']
        # Keep every natural-language answer, no truncation of response text.
        e['predictions'] = [{k: r[k] for k in ('request_id', 'text', 'truncated', 'status') if k in r}
                            for r in e['predictions']]
        evaluations.append(e)
    manifests = [read(p / 'candidates' / r['candidate'] / 'manifest.json') for r in rounds]
    requests = [read(f) for f in sorted(p.glob('inbox/*.json'))]
    receipts = {name: read(p / name) for name in ('config.json', 'identity.json',
                'round-limit-amendment.json', 'broker-50-ready.json', 'frozen-candidate.json')}
    out['runs'][task] = dict(state=state, rounds=rounds, evaluations=evaluations,
                            manifests=manifests, requests=requests, receipts=receipts,
                            source_sha256=hashes)
sys.stdout.buffer.write(gzip.compress(json.dumps(out, ensure_ascii=False).encode(), mtime=0))
