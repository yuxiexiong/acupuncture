"""Two-worker bounded launcher; authorization determines the only allowed stage."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import time

import experiment as ex


def launch(stage, authorization, output):
    auth = ex.authorize(authorization, stage, True)
    output = Path(output).resolve()
    assert output == (ex.HERE / auth['output_root']).resolve()
    assert output.is_relative_to((ex.HERE / 'runs').resolve())
    output.mkdir(parents=True, exist_ok=False)
    controller = {'status': 'starting', 'pid': os.getpid(), 'stage': stage, 'started_at': ex.utc(),
        'authorization_sha256': ex.sha(authorization), 'freeze_sha256': auth['freeze_sha256'], 'workers': {}}
    ex.write(output / 'execution.json', dict(controller), immutable=True)
    processes = []
    streams = []
    started = time.monotonic()
    try:
        for gpu in (0, 1):
            log = (output / f'worker-{gpu}.log').open('x')
            streams.append(log)
            command = [sys.executable, '-u', str(ex.HERE / 'experiment.py'), 'run', '--stage', stage,
                '--gpu', str(gpu), '--authorization', str(Path(authorization).resolve()),
                '--output', str(output / f'worker-{gpu}'), '--execute']
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
            processes.append((gpu, process))
            controller['workers'][str(gpu)] = {'pid': process.pid, 'command': command}
        controller['status'] = 'running'
        ex.write(output / 'controller.json', controller)
        pending = dict(processes)
        failure = False
        while pending:
            for gpu, process in list(pending.items()):
                code = process.poll()
                if code is None:
                    continue
                worker = output / f'worker-{gpu}'
                worker.mkdir(exist_ok=True)
                ex.write(worker / 'exit.json', {'returncode': code, 'finished_at': ex.utc()}, immutable=True)
                controller['workers'][str(gpu)]['returncode'] = code
                del pending[gpu]
                failure |= code != 0
            ex.write(output / 'controller.json', controller)
            if failure:
                # Only children started by this controller are stopped; all partial evidence remains.
                for process in pending.values():
                    process.terminate()
            if pending:
                time.sleep(1)
        assert not failure, 'A worker failed; see preserved logs and partial receipts'
        results = [ex.verify_worker(output / f'worker-{gpu}') for gpu in (0, 1)]
        ex.write(output / 'verification.json', {'status': 'passed', 'freeze_sha256': auth['freeze_sha256'],
            'workers': results, 'verified_at': ex.utc()}, immutable=True)
        controller['status'] = 'completed'
    except BaseException as error:
        controller.update(status='failed', error=repr(error))
        for gpu, process in processes:
            if process.poll() is None:
                process.terminate()
                code = process.wait()
                worker = output / f'worker-{gpu}'; worker.mkdir(exist_ok=True)
                if not (worker / 'exit.json').exists():
                    ex.write(worker / 'exit.json', {'returncode': code, 'finished_at': ex.utc()}, immutable=True)
        raise
    finally:
        for stream in streams:
            stream.close()
        controller.update(finished_at=ex.utc(), wall_seconds=time.monotonic()-started)
        ex.write(output / 'controller.json', controller)
    return controller


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--stage', required=True); p.add_argument('--authorization', required=True)
    p.add_argument('--output', required=True)
    a = p.parse_args()
    print(launch(a.stage, a.authorization, a.output))
