"""Run the authorized two-worker stage after bounded GPU validation."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import experiment as exp


def launch(stage, authorization, output, delivery):
    auth = exp.authorize(authorization, stage, 'formal', True)
    exp.check()
    for name, expected in auth['readiness_hashes'].items():
        assert exp.sha(exp.HERE / name) == expected
    cpu = exp.read(exp.HERE / auth['cpu_receipt'])
    assert cpu['status'] == 'passed' and cpu['skipped'] == 0
    assert cpu['freeze_sha256'] == auth['freeze_sha256']
    output = Path(output).resolve()
    assert output.is_relative_to((exp.HERE / 'runs').resolve())
    assert str(output.relative_to(exp.HERE)) == auth['formal_runs'][stage]
    output.mkdir(parents=True, exist_ok=False)
    execution = {'pid': os.getpid(), 'argv': sys.argv, 'python': sys.executable,
        'stage': stage, 'authorization_sha256': exp.sha(authorization),
        'freeze_sha256': auth['freeze_sha256'], 'started_at': exp.utc(),
        'output': str(output), 'delivery': str(delivery), 'maximum_model_workers': 2}
    exp.write(output / 'execution.json', execution, immutable=True)
    state = {'status': 'running', **execution, 'workers': []}
    start = time.monotonic()
    def save():
        state['updated_at'] = exp.utc()
        exp.write(output / 'controller.json', state)
    def run_workers(mode, root):
        state.update(phase=mode, workers=[])
        processes = []
        for gpu in (0, 1):
            argv = [sys.executable, str(exp.HERE / 'experiment.py'), 'run', '--stage', stage,
                    '--mode', mode, '--gpu', str(gpu), '--output', str(root / f'worker-{gpu}'),
                    '--authorization', str(authorization), '--execute']
            log = open(output / f'{mode}-worker-{gpu}.log', 'x')
            process = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, cwd=exp.REPO)
            log.close()
            processes.append(process)
            state['workers'].append({'gpu': gpu, 'pid': process.pid, 'argv': argv,
                                     'status': 'running', 'exit_code': None})
        save()
        while any(p.poll() is None for p in processes):
            time.sleep(5)
            for process, row in zip(processes, state['workers']):
                if process.poll() is not None:
                    row.update(status='exited', exit_code=process.returncode)
            save()
        for process, row in zip(processes, state['workers']):
            row.update(status='exited', exit_code=process.returncode)
            exp.write(output / f"{mode}-worker-{row['gpu']}-exit.json",
                      {**row, 'finished_at': exp.utc()}, immutable=True)
        save()
        assert all(p.returncode == 0 for p in processes), f'{mode} worker failed; keep partial evidence'
    try:
        preflight = exp.HERE / auth['preflight_run']
        if stage == 'stage1':
            assert not preflight.exists(), 'Never restart an existing preflight'
            preflight.mkdir(parents=True)
            run_workers('preflight', preflight)
        preflight_checks = [exp.verify_worker(preflight / f'worker-{gpu}', 'preflight', 'stage1') for gpu in (0, 1)]
        exp.write(output / 'preflight-verification.json', preflight_checks, immutable=True)
        run_workers('formal', output)
        state['verification'] = exp.verify_stage(output, stage)
        state['phase'] = 'export'
        save()
        from delivery import export
        previous = exp.HERE / exp.read(exp.HERE / 'readiness/stage2-gate.json')['stage1_run'] if stage == 'stage2' else None
        state['delivery'] = export(output, stage, delivery, previous)
        state.update(status='completed', phase='awaiting_measurement_review' if stage == 'stage1' else 'awaiting_reading',
                     scientific_reading_complete=False, finished_at=exp.utc())
    except BaseException:
        state.update(status='failed', error=traceback.format_exc(), finished_at=exp.utc())
        raise
    finally:
        state['wall_seconds'] = time.monotonic() - start
        save()
    return state


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=('stage1', 'stage2'), required=True)
    parser.add_argument('--authorization', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--delivery', type=Path, required=True)
    args = parser.parse_args()
    launch(**vars(args))
