"""Launch the authorized 3520-answer survey using the unchanged frozen runner."""
import argparse
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import dose_survey as survey

ROOT = Path(__file__).resolve().parent


def launch(authorization, output, execute=False):
    authorization, output = Path(authorization).resolve(), Path(output).resolve()
    for model in ('2b', '4b', '9b'):
        for gpu in (0, 1):
            identity, auth = survey.check_authorization(authorization, 'survey', model, gpu, execute)
    assert auth['controller_sha256'] == survey.io.sha(Path(__file__))
    assert str(output) == auth['remote_output']
    assert auth['maximum_generations'] == 3520
    assert auth['formal_launch_confirmed'] is True
    assert not output.exists(), 'Never overwrite or resume a partial formal run'
    assert not (output.parent / 'delivery-r01').exists(), 'Keep existing delivery evidence'
    output.mkdir(parents=True)
    started = time.monotonic()
    state = dict(status='running', experiment=ROOT.name, freeze_sha256=identity,
                 controller_sha256=survey.io.sha(Path(__file__)), authorization_sha256=survey.io.sha(authorization),
                 controller_pid=os.getpid(), started_utc=survey.io.utc(), models=['2b','4b','9b'],
                 worker_pids={}, worker_exit_codes={}, expected_records=3520)
    survey.io.immutable(output/'execution.json', state.copy())
    processes, logs = {}, []
    try:
        for model in state['models']:
            state['current_model'] = model
            processes = {}
            for gpu in (0, 1):
                key = f'{model}-shard-{gpu}'
                log = (output/f'{key}.log').open('x')
                logs.append(log)
                command = [sys.executable, str(ROOT/'dose_survey.py'), 'run', '--mode', 'survey',
                           '--model', model, '--gpu', str(gpu), '--shard', str(gpu), '--shards', '2',
                           '--authorization', str(authorization), '--output', str(output/key), '--execute']
                processes[key] = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
                state['worker_pids'][key] = processes[key].pid
                survey.io.write(output/'controller.json', state)
            while True:
                codes = {key: proc.poll() for key, proc in processes.items()}
                if any(code is not None and code != 0 for code in codes.values()):
                    raise RuntimeError(f'Worker failed: {codes}')
                if all(code == 0 for code in codes.values()):
                    break
                time.sleep(1)
            for key, proc in processes.items():
                code = proc.wait()
                (output/f'{key}.exit').write_text(str(code)+'\n')
                state['worker_exit_codes'][key] = code
                survey.verify(output/key)
            survey.io.write(output/'controller.json', state)
        state['generation_ended_utc'] = survey.io.utc()
        state['generation_wall_seconds'] = time.monotonic() - started
        from export_dose_survey import export
        delivery = export([output / f'{model}-shard-{gpu}' for model in state['models'] for gpu in (0, 1)], output.parent / 'delivery-r01')
        assert delivery['whole_survey_complete'] and delivery['counts']['unique_records'] == 7064
        assert delivery['counts']['new_records'] == 3520 and delivery['counts']['reused_sources'] == 3544
        assert delivery['counts']['comparison_groups'] == 704
        state['delivery'] = str(output.parent / 'delivery-r01')
        state['status'] = 'completed'
    except BaseException as exc:
        state.update(status='failed', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        # Only children created by this controller may be stopped; retain every partial file.
        for key, proc in processes.items():
            if proc.poll() is None:
                proc.terminate()
            try:
                code = proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                proc.kill()
                code = proc.wait()
            state['worker_exit_codes'][key] = code
            (output/f'{key}.exit').write_text(str(code)+'\n')
        for log in logs:
            log.close()
        state.update(ended_utc=survey.io.utc(), wall_seconds=time.monotonic()-started)
        survey.io.write(output/'controller.json', state)
    return state


def stop(_signum, _frame):
    raise KeyboardInterrupt('Controller stop requested')


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, stop)
    parser = argparse.ArgumentParser()
    parser.add_argument('--authorization', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    launch(args.authorization, args.output, args.execute)
