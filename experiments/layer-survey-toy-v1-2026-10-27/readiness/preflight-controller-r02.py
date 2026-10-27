"""Bounded technical preflight only; never starts the formal survey."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parent.parent
out = root / 'preflight-r02'


def worker(gpu, models):
    result = {}
    for model in models:
        with (out / f'{model}.log').open('x') as log:
            cmd = [sys.executable, str(root / 'survey.py'), 'run', '--mode', 'preflight',
                   '--model', model, '--gpu', str(gpu), '--authorization',
                   str(root / 'readiness/preflight-authorization.json'), '--output', str(out / model), '--execute']
            proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, cwd=root)
            (out / f'{model}.pid').write_text(str(proc.pid))
            code = proc.wait()
            (out / f'{model}.exit').write_text(str(code) + '\n')
            result[model] = code
            if code:
                break
    return result


if __name__ == '__main__':
    started = time.time()
    out.mkdir(exist_ok=False)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(worker, 0, ['2b', '4b']), pool.submit(worker, 1, ['9b'])]
        results = [f.result() for f in futures]
    (out / 'controller.json').write_text(json.dumps({
        'completed_at': time.time(), 'wall_seconds': time.time() - started,
        'worker_exit_codes': results}, indent=2) + '\n')
