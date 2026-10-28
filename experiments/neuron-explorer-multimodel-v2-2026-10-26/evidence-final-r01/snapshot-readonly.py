"""Run over SSH stdin: read existing files only and emit a one-time snapshot."""
import base64
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import zipfile

import numpy as np

root = Path('/workspace/acupuncture/experiments/neuron-explorer-multimodel-v2-2026-10-26')
models = json.loads((root / 'models.json').read_text())
snapshot = {'captured_at': datetime.now(timezone.utc).isoformat(), 'host': 'gqa-h20',
            'remote_root': str(root), 'read_only': True, 'cache_files': [],
            'coverage': {}, 'small_files': [],
            'boundary': 'Point-in-time snapshot; no new model execution. Missing 9B outputs remain pending.'}
for model in models:
    profile = model['id']
    expected = [root / 'data' / profile / 'cache' / name for name in
                ('steer_index.npz', 'lens_index.npz', 'layout_writes.npz', 'act_scale.npz', 'connections.npz')]
    expected += sorted((root / 'data' / profile / 'cache').glob('*.json'))
    if profile != '4b':
        expected += [root / 'data' / profile / 'stats' / f'steer-full-r01_L{i}.npz'
                     for i in range(model['layers'])]
    completed = []
    for path in expected:
        record = {'path': str(path.relative_to(root)), 'model': profile}
        if not path.is_file():
            record.update(status='pending', bytes=None, sha256=None, arrays=None)
            snapshot['cache_files'].append(record)
            continue
        before = path.stat()
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(block)
        record.update(bytes=before.st_size, sha256=digest.hexdigest(), resolved_path=str(path.resolve()), arrays={})
        if path.suffix == '.json':
            value = json.loads(path.read_text())
            record.update(status='available', arrays=None, json_type=type(value).__name__, json_length=len(value))
            snapshot['cache_files'].append(record)
            continue
        try:
            with zipfile.ZipFile(path) as archive:
                for name in archive.namelist():
                    if not name.endswith('.npy'):
                        continue
                    with archive.open(name) as stream:
                        version = np.lib.format.read_magic(stream)
                        reader = np.lib.format.read_array_header_1_0 if version == (1, 0) else np.lib.format.read_array_header_2_0
                        shape, order, dtype = reader(stream)
                        record['arrays'][name[:-4]] = {'shape': list(shape), 'dtype': str(dtype), 'fortran_order': order}
            if '/stats/steer-full-r01_' in str(path):
                with np.load(path, allow_pickle=False) as arrays:
                    record['layer_metadata'] = {key: arrays[key].tolist() for key in
                        ('complete_layer', 'layer', 'model', 'total_neurons', 'dose', 'calibration_norms', 'residual_norm', 'contexts')}
                    if bool(arrays['complete_layer']):
                        completed.append(int(arrays['layer']))
            record['status'] = 'available'
        except (OSError, ValueError, zipfile.BadZipFile, EOFError) as error:
            record.update(status='pending_write_or_unreadable', error=repr(error))
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            record.update(status='changed_during_snapshot', sha256=None)
        snapshot['cache_files'].append(record)
    snapshot['coverage'][profile] = {
        'model': model, 'merged_index_exists': expected[0].is_file(),
        'completed_layer_files': sorted(completed) if profile != '4b' else None,
        'pending_layer_files': [i for i in range(model['layers']) if i not in completed] if profile != '4b' else None,
        'note': '4B existing upstream/reused cache; this snapshot does not claim freshly computed layer files.' if profile == '4b' else 'Pending is not a completed full map.'}

paths = [root / 'models.json'] + [root / f'live-{p}-r01.json' for p in ('2b', '4b', '9b')]
paths += [root / 'data' / p / 'cache/model.json' for p in ('2b', '4b', '9b')]
for profile in ('2b', '9b'):
    paths += [root / 'data' / profile / name for name in
              ('steer-cache-receipt.json', 'calibration-receipt.json', 'calibration-token-ids.json')]
for pattern in ('layout-*-r01.log', 'full-cache-queue-*.log', 'steer-full-*-r01.log',
                'postbuild-receipt-r01.json', 'start-and-verify-r01.log', 'queue-update-r02.json', 'server-*-r01.log'):
    paths += sorted((root / 'runtime').glob(pattern))
for path in paths:
    record = {'path': str(path.relative_to(root))}
    if path.is_file():
        raw = path.read_bytes()
        record.update(status='available', bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                      content_base64=base64.b64encode(raw).decode())
    else:
        record.update(status='pending', bytes=None, sha256=None)
    snapshot['small_files'].append(record)
snapshot['finished_at'] = datetime.now(timezone.utc).isoformat()
print(json.dumps(snapshot))
