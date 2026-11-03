"""Read-only verification of the imported snapshot and cache record receipts; no model imports."""
from pathlib import Path
import collections
import hashlib
import json
import sys

root = Path(__file__).resolve().parents[2]
base = Path(__file__).resolve().parent

def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

imp = json.loads((base / 'local-import.json').read_text())
errors = []
for row in imp['entries']:
    if row['action'] in ('manifest_only', 'already_identical'):
        continue
    p = root / row['destination']
    if not p.is_file() or digest(p) != row['sha256']:
        errors.append({'path': row['destination'], 'error': 'import hash mismatch'})

checks, missing, mismatches, tensor_refs, verifications = [], [], [], [], []
for d in sorted((root / 'experiments').glob('cache-*')):
    for p in sorted((d / 'runs').glob('*/verification.json')):
        obj = json.loads(p.read_text())
        verifications.append({'path': str(p.relative_to(root)), 'status': obj.get('status'),
                              'stage': obj.get('stage'), 'units': obj.get('units')})
    for p in sorted((d / 'runs').glob('*/worker-*/receipt.json')):
        obj = json.loads(p.read_text())
        for key, target in [('record_hashes', checks), ('tensor_hashes', tensor_refs)]:
            for name, expected in obj.get(key, {}).items():
                if not isinstance(expected, str):
                    continue
                q = p.parent / name
                row = {'receipt': str(p.relative_to(root)), 'path': str(q.relative_to(root)), 'sha256': expected}
                if key == 'tensor_hashes':
                    row['local_present'] = q.is_file()
                    target.append(row)
                elif not q.is_file():
                    missing.append(row)
                elif digest(q) != expected:
                    mismatches.append(row)
                else:
                    target.append(row)

# Independent arithmetic over saved record labels, not a rerun or a new semantic assessment.
y_counts = {}
for stem in ('cache-native-carrier-comparison', 'cache-native-s-reverse', 'cache-native-qk-history', 'cache-native-pair-combination'):
    d = next((root / 'experiments').glob(stem + '-v1-*'))
    records = [json.loads(p.read_text()) for p in sorted(d.glob('runs/formal-r01/worker-*/records/*.json'))]
    assert len(records) == 48, (d, len(records))
    sums = collections.Counter()
    def walk(value, keys=()):
        if not isinstance(value, dict):
            return
        if 'Y' in value and isinstance(value['Y'], (int, float)):
            sums['/'.join(keys)] += value['Y']
        for k, v in value.items():
            if isinstance(v, dict):
                walk(v, keys + (k,))
    for record in records:
        walk(record['results'])
    y_counts[d.name] = dict(sorted(sums.items()))
expected = {
 'cache-native-carrier-comparison': {'N_L00_C4146_D-1/TS':48, 'N_L00_C4146_D-1/TV':16, 'N_L00_C4146_D-1/TK':3},
 'cache-native-s-reverse': {'N_L00_C4146_D-1/CS':48, 'N_L00_C4146_D-1/CJ':2},
 'cache-native-qk-history': {'N_L00_C4146_D-1/CQK':48, 'N_L00_C4146_D-1/CVSK':2},
 'cache-native-pair-combination': {'N_L00_C4146_D-1/CSV':45, 'N_L00_C4146_D-1/CSK':32, 'N_L00_C4146_D-1/CVK':48},
}
for stem, values in expected.items():
    actual = next(v for k,v in y_counts.items() if k.startswith(stem+'-v1-'))
    for key, value in values.items():
        assert actual[key] == value, (stem, key, actual[key], value)

result = {'verification_status': 'ANALYZED_NO_MODEL_RERUN',
          'import_counts': imp['counts'], 'import_hash_errors': errors,
          'cache_record_hashes_matched': len(checks), 'missing_record_paths': missing,
          'record_hash_mismatches': mismatches, 'run_verifications': verifications,
          'tensor_references': tensor_refs, 'raw_Y_recount': y_counts,
          'limits': ['Tensor references inventoried, remote tensor bytes not reread.',
                     'Y recount reuses recorded labels; not independent semantic scoring.',
                     'Historical passed receipts are not new execution acceptance.',
                     'All missing paths and mismatches remain visible.']}
(base / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({k:result[k] for k in ('import_counts','import_hash_errors','cache_record_hashes_matched','missing_record_paths','record_hash_mismatches','raw_Y_recount')},ensure_ascii=False,indent=2))
assert not errors and not mismatches
