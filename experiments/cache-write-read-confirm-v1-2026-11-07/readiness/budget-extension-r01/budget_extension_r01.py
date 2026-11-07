"""One-shot, user-authorized DWC live budget change; no model operations."""
import hashlib
import json
import marshal
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def extend(module, new_seconds):
    before = dict(module.GPU_CAP_S)
    assert before == {'preflight': 5400, 'formal': 57600}, before
    assert new_seconds == 172800
    identities = {k: id(v) for k, v in vars(module).items()}
    functions = {k: hashlib.sha256(marshal.dumps(v.__code__)).hexdigest()
                 for k, v in vars(module).items()
                 if callable(v) and hasattr(v, '__code__')}
    module.GPU_CAP_S['formal'] = new_seconds
    assert identities == {k: id(v) for k, v in vars(module).items()}
    assert functions == {k: hashlib.sha256(marshal.dumps(v.__code__)).hexdigest()
                         for k, v in vars(module).items()
                         if callable(v) and hasattr(v, '__code__')}
    return {'before': before, 'after': dict(module.GPU_CAP_S),
            'global_object_identities_unchanged': True,
            'function_code_hashes_unchanged': functions}


def apply():
    module = sys.modules['__main__']
    root = Path('/workspace/acupuncture/experiments/cache-write-read-confirm-v1-2026-11-07')
    assert Path(module.__file__).resolve() == root / 'dwc_run.py'
    auth_path = root / 'readiness/budget-extension-authorization-r01.json'
    auth_bytes = auth_path.read_bytes()
    auth = json.loads(auth_bytes)
    pid = os.getpid()
    assert str(pid) in auth['process_start_ticks']
    ticks = Path('/proc/self/stat').read_text().split(') ', 1)[1].split()[19]
    assert ticks == auth['process_start_ticks'][str(pid)]
    assert '--stage' in sys.argv and sys.argv[sys.argv.index('--stage') + 1] == 'formal'
    assert hashlib.sha256((root / 'freeze-r02.json').read_bytes()).hexdigest() == auth['freeze_sha256']
    for name in ('execute', 'launch'):
        assert getattr(module, name).__globals__['GPU_CAP_S'] is module.GPU_CAP_S
    proof = root / f'readiness/budget-extension-applied-{pid}-r01.json'
    with proof.open('x') as stream:
        result = extend(module, auth['new_formal_gpu_process_seconds'])
        result.update(pid=pid, at=datetime.now(timezone.utc).isoformat(),
                      authorization_sha256=hashlib.sha256(auth_bytes).hexdigest(),
                      process_start_ticks=ticks, argv=sys.argv,
                      execute_and_launch_share_updated_budget=True)
        json.dump(result, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())


def self_test():
    from types import SimpleNamespace
    sample = SimpleNamespace(GPU_CAP_S={'preflight': 5400, 'formal': 57600},
                             scientific_setting=(96, 81648, 32), fn=lambda x: x + 1)
    result = extend(sample, 172800)
    assert result['after'] == {'preflight': 5400, 'formal': 172800}
    assert sample.scientific_setting == (96, 81648, 32) and sample.fn(2) == 3
    try:
        extend(sample, 172800)
    except AssertionError:
        pass
    else:
        raise AssertionError('must reject repeat application')
    print('PASS: exact budget mutation, preserved settings/code, repeat rejected')


if __name__ == '__main__':
    self_test()
