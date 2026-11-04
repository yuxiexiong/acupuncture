"""Read-only cost and duplicate-output audit; run on gqa-h20 via stdin."""
from pathlib import Path
import json, hashlib, time

root = Path('/workspace/acupuncture/external/wsp/fleet-v1/math-0p8b')
rows, duplicates, seen = [], [], {}
for action in sorted((root / 'actions').glob('turn-*')):
    if not (action / 'response.json').exists() or not (action / 'request.json').exists():
        continue
    response = json.loads((action / 'response.json').read_text())
    request = json.loads((action / 'request.json').read_text())
    row = dict(turn=action.name, type=request['type'], model=request['model'],
               success=not response.get('failed'), state=response.get('state'))
    results = list(action.glob('pass_*.result.json'))
    if results:
        result = json.loads(results[0].read_text())
        row['seconds'] = result.get('seconds')
        row['arms'] = {k: {p: v.get(p) for p in ('engine', 'mean_length', 'cut_share')}
                       for k, v in result.get('arms', {}).items()}
    if request['type'] == 'generate':
        row.update(items=len(request['problems']) + len(request['prompts']), n=request['n'],
                   max_tokens=request['max_tokens'], activations=request['activations'])
        for inputs in action.glob('*original.raw.jsonl.items.json'):
            key = hashlib.sha256(inputs.read_bytes()).hexdigest()
            raw = Path(str(inputs).replace('.items.json', ''))
            tokens = [hashlib.sha256(json.dumps(json.loads(line)['token_ids']).encode()).hexdigest()
                      for line in raw.open()] if raw.exists() else []
            row['original_items_sha256'] = key
            if key in seen and tokens:
                previous, before = seen[key]
                duplicates.append(dict(turn=action.name, previous=previous, rows=len(tokens),
                    identical_rows=sum(a == b for a, b in zip(before, tokens)), all_equal=before == tokens))
            elif tokens:
                seen[key] = (action.name, tokens)
    rows.append(row)
print(json.dumps(dict(observed_unix=time.time(), state=json.loads((root / 'state.json').read_text()),
    cap_seconds=json.loads((root / 'config.json').read_text())['gpu_seconds_limit'],
    calls=rows, duplicate_original_requests=duplicates), indent=2))
