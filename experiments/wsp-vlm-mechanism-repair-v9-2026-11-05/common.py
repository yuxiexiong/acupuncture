"""Small observer utilities. Importing this package never loads a model."""
import hashlib
import importlib.util
import json
import os
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPERIMENTS = HERE.parent
REVISION = 'ebb281ec70b05090aa6165b016eac8ec08e71b17'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def packed(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False).encode()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024**2), b''):
            h.update(block)
    return h.hexdigest()


def write_json(path, value):
    path = Path(path)
    fd, name = tempfile.mkstemp(prefix='.'+path.name+'-', dir=path.parent)
    temp = Path(name)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(packed(value) + b'\n')
            f.flush()
            os.fsync(f.fileno())
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def inside(root, relative):
    root = Path(root).resolve()
    path = root / relative
    if Path(relative).is_absolute() or '..' in Path(relative).parts or path.is_symlink():
        raise ValueError('Unsafe relative path')
    if not path.resolve().is_relative_to(root):
        raise ValueError('Path escapes allowed root')
    return path


def legacy(relative, module_name):
    """Import only explicitly pinned, import-safe legacy source (never old kernels)."""
    import sys
    provenance = json.loads((HERE / 'reuse.json').read_text())
    path = EXPERIMENTS / relative
    if file_hash(path) != provenance['imports'][relative]:
        raise ValueError('Legacy source changed: ' + relative)
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    old_path = list(sys.path)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = old_path
    return module


def require_live(config):
    """An intentionally incomplete template cannot load weights or call an editor."""
    required = ('authorization_record', 'researcher_model',
                'researcher_cli_sha256', 'contract_sha256')
    if config.get('mode') != 'live' or config.get('authorized') is not True:
        raise PermissionError('Live execution disabled; offline preparation only')
    if any(not config.get(k) for k in required):
        raise PermissionError('Unfrozen live execution contract')
    if config.get('phase') not in ('engineering', 'search', 'confirmation'):
        raise PermissionError('An explicit execution phase is required')
    if config['phase'] != 'engineering' and not config.get('engineering_acceptance_sha256'):
        raise PermissionError('Search/confirmation requires real engineering acceptance')
    contract = config['contract']
    if digest(packed(contract)) != config['contract_sha256']:
        raise ValueError('Contract hash mismatch')
    for k in ('actions', 'forwards', 'samples', 'target_tokens', 'wall_seconds',
              'python_seconds', 'max_input_tokens', 'max_measure_elements',
              'temporary_scalars', 'final_scalars', 'researcher_turns'):
        if k == 'wall_seconds' and contract.get(k) is None and contract.get('repair_rounds') == 30:
            continue
        if not isinstance(contract.get(k), (int, float)) or contract[k] <= 0:
            raise ValueError('Missing positive numeric budget: ' + k)
    if config.get('researcher_billing') == 'existing_chatgpt':
        if not config.get('researcher_account_record') or contract.get('researcher_tokens', 0) <= 0:
            raise ValueError('Subscription identity and token budget required')
    elif contract.get('researcher_usd', 0) <= 0 or contract.get('researcher_turn_reserve_usd', 0) <= 0:
        raise ValueError('Missing researcher monetary budget')
    if contract['final_scalars'] > contract['temporary_scalars']:
        raise ValueError('Final support exceeds temporary support')
    for k in ('max_format_rate', 'max_protection_drop'):
        if not isinstance(contract.get(k), (int, float)) or not 0 <= contract[k] <= 1:
            raise ValueError('Missing protection limit: '+k)
    if not contract.get('protection_conditions'):
        raise ValueError('Missing protection conditions')

