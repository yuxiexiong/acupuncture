"""Aggregate real-source CPU engineering tests, preserving command output and identity."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import time
import tg_run as R


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', required=True)
    p.add_argument('--upstream', action='store_true')
    args = p.parse_args()
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    output = Path(args.output)
    assert not output.exists()
    records = []
    source_hashes = {p.name: R.W.sha(p) for p in R.HERE.glob('*.py')}
    start = time.monotonic()
    for name in ('test_tg.py', 'test_rcs_hooks.py'):
        command = [sys.executable, str((R.HERE if name == 'test_tg.py' else R.N.RCS)/name)]
        if args.upstream: command.append('--upstream')
        proc = subprocess.run(command, cwd=R.HERE, capture_output=True, text=True)
        records.append(dict(command=command, returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr))
    import torch
    external = {}
    if args.upstream:
        import transformers.cache_utils as cache_utils
        for module in (R.W.runtime().gdn_module(), cache_utils):
            external[str(Path(module.__file__))] = R.W.sha(module.__file__)
    source_stable = source_hashes == {p.name: R.W.sha(p) for p in R.HERE.glob('*.py')}
    report = dict(status='passed' if source_stable and all(x['returncode'] == 0 for x in records) else 'failed',
                  model_forwards=0, cuda_initialized=torch.cuda.is_initialized(),
                  upstream_kernel_tested=args.upstream, torch_version=torch.__version__, tests=records,
                  source_hashes=source_hashes, source_stable=source_stable, external_sources=external,
                  wall_seconds=time.monotonic()-start)
    assert not report['cuda_initialized']
    R.W.write(output, report, immutable=True)
    print(report['status'], str(output))
    if report['status'] != 'passed':
        for r in records:
            if r['returncode']: print(r['stderr'])
        sys.exit(1)


if __name__ == '__main__':
    main()
