#!/usr/bin/env python3
"""Open the existing three-model Explorer in cache-only, read-only mode."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
SURVEY = REPO / 'experiments/neuron-explorer-analysis-v1-2026-10-26/survey-evidence.json'


def main():
    if not SURVEY.is_file() or not SURVEY.with_name('survey-manifest.json').is_file():
        raise SystemExit('Copy the verified survey export and manifest first.')
    runtime = ROOT / 'runtime'
    runtime.mkdir(exist_ok=True)
    stamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    started = []
    for model in json.loads((ROOT / 'models.json').read_text()):
        address = ('127.0.0.1', model['port'])
        url = f'http://{address[0]}:{address[1]}/api/index'
        with socket.socket() as sock:
            occupied = sock.connect_ex(address) == 0
        if occupied:
            with urlopen(url, timeout=3) as response:
                current = json.load(response)
            if current.get('profile') != model['id'] or current.get('live_model') is not False or not current.get('read_only'):
                raise SystemExit(f"Port {model['port']} is occupied by a different service; left unchanged.")
            started.append({'model': model['id'], 'status': 'already_cache_only'})
            continue
        env = dict(os.environ, EXPLORER_NO_MODEL='1', EXPLORER_READ_ONLY='1',
                   EXPLORER_SURVEY=str(SURVEY), EXPLORER_REPO=str(REPO))
        log_path = runtime / f'brainmap-{model["id"]}-{stamp}.log'
        with log_path.open('ab') as log:
            process = subprocess.Popen([sys.executable, str(ROOT / 'serve_model.py'), model['id']],
                                       cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                                       stdout=log, stderr=log, start_new_session=True)
        started.append({'model': model['id'], 'status': 'started_cache_only', 'pid': process.pid,
                        'log': str(log_path)})
    receipt = runtime / f'brainmap-start-{stamp}.json'
    receipt.write_text(json.dumps({'new_inference': False, 'read_only': True, 'services': started}, indent=2) + '\n')
    print(receipt)
    print(json.dumps(started))


if __name__ == '__main__':
    main()
