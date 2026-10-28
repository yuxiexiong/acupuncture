"""Run the authorized independent dose experiment after the broad survey passes."""
import argparse
import fcntl
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import survey


def prerequisites(path):
    auth = survey.io.read(path)
    assert auth['status'] == 'authorized' and auth['purpose'] == 'after_broad_acceptance'
    assert auth['experiment'] == ROOT.name and auth['user_instruction']
    assert auth['queue_sha256'] == survey.io.sha(Path(__file__))
    assert auth['freeze_sha256'] == survey.check_freeze()
    assert auth['source_freeze_sha256'] == survey.io.sha(survey.SOURCE/'freeze.json')
    assert auth['maximum_generations'] == {'preflight': 88, 'survey': 2304}
    for name, digest in auth['acceptance_evidence_sha256'].items():
        assert survey.io.sha(survey.REPO/name) == digest
    run = survey.SOURCE/'survey-r01'
    assert survey.io.sha(run/'execution.json') == auth['source_execution_sha256']
    state = survey.io.read(run/'controller.json')
    assert state['freeze_sha256'] == auth['source_freeze_sha256']
    assert state['status'] in ('running', 'completed'), 'Broad source failed or stopped'
    return auth, state


def stage_authorization(parent, mode):
    source = survey.SOURCE/'survey-r01'
    count = parent['maximum_generations'][mode]
    auth = dict(experiment=ROOT.name, status='authorized', purpose=mode,
        recorded_utc=survey.io.utc(), user_instruction=parent['user_instruction'],
        freeze_sha256=parent['freeze_sha256'], models=[survey.MODEL], gpus=[0, 1],
        maximum_workers=2, maximum_new_tokens_per_record=128,
        maximum_generations=count, maximum_generated_tokens=count*128,
        formal_launch_confirmed=mode == 'survey',
        controller_sha256=survey.io.sha(ROOT/'launch_survey.py'),
        remote_output=str(ROOT/('preflight-r01' if mode == 'preflight' else 'survey-r01')),
        remote_delivery=str(ROOT/'delivery-r01'),
        source_controller_sha256=survey.io.sha(source/'controller.json'),
        source_receipt_sha256={f'{survey.MODEL}-shard-{i}':survey.io.sha(source/f'{survey.MODEL}-shard-{i}'/'receipt.json') for i in (0,1)},
        acceptance_evidence_sha256=parent['acceptance_evidence_sha256'])
    survey.source_evidence(auth)
    if mode == 'survey':
        run = ROOT/'preflight-r01'
        paths = [run/f'{survey.MODEL}-shard-{i}' for i in (0,1)]
        survey.check_pair(paths, 'preflight')
        controller = survey.io.read(run/'controller.json')
        assert controller['status'] == 'completed'
        assert controller['worker_exit_codes'] == {p.name:0 for p in paths}
        assert all((run/f'{p.name}.exit').read_text().strip() == '0' for p in paths)
        auth.update(preflight_runs=[str(p.relative_to(survey.REPO)) for p in paths],
            preflight_controller_sha256=survey.io.sha(run/'controller.json'),
            preflight_exit_sha256={p.name:survey.io.sha(run/f'{p.name}.exit') for p in paths})
    return auth


def main(path, execute=False):
    parent, source_state = prerequisites(path)
    if not execute:
        return dict(status='ready', source_status=source_state['status'])
    lock = open('/tmp/acupuncture-llama31-split-successor.lock', 'w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    state_path = ROOT/'readiness/queue-state-r01.json'
    assert not state_path.exists(), 'Do not duplicate or resume a partial successor'
    state = dict(status='waiting_for_broad', pid=os.getpid(), started_utc=survey.io.utc(),
        authorization_sha256=survey.io.sha(path), queue_sha256=parent['queue_sha256'], stages={})
    survey.io.write(state_path, state)
    child = None
    try:
        while source_state['status'] != 'completed':
            time.sleep(10)
            _, source_state = prerequisites(path)
        for mode in ('preflight', 'survey'):
            prerequisites(path)
            auth = stage_authorization(parent, mode)
            if mode == 'survey':
                subprocess.run([sys.executable, '-B', str(ROOT/'readiness/estimate_timing.py')], cwd=ROOT, check=True)
            auth['parent_authorization_sha256'] = survey.io.sha(path)
            name = 'preflight' if mode == 'preflight' else 'formal'
            auth_path = ROOT/f'readiness/{name}-authorization-r01.json'
            survey.io.immutable(auth_path, auth)
            state['status'] = f'running_{mode}'
            command = [sys.executable, '-B', str(ROOT/'launch_survey.py'), '--mode', mode,
                '--authorization', str(auth_path), '--output', auth['remote_output'], '--execute']
            with (ROOT/f'readiness/{name}-controller-r01.log').open('x') as log:
                child = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
                launch = dict(status='dispatched', pid=child.pid, command=command,
                    started_utc=survey.io.utc(), freeze_sha256=parent['freeze_sha256'],
                    authorization_sha256=survey.io.sha(auth_path))
                survey.io.immutable(ROOT/f'readiness/{name}-launch-r01.json', launch)
                state['stages'][mode] = launch
                survey.io.write(state_path, state)
                code = child.wait()
            assert code == 0, f'{mode} controller exited {code}; retain partial evidence'
            completed = survey.io.read(Path(auth['remote_output'])/'controller.json')
            assert completed['status'] == 'completed'
            state['stages'][mode].update(exit_code=code, ended_utc=survey.io.utc(),
                controller_sha256=survey.io.sha(Path(auth['remote_output'])/'controller.json'))
            survey.io.write(state_path, state)
        state['status'] = 'completed'
    except BaseException as exc:
        state.update(status='failed', error=f'{type(exc).__name__}: {exc}')
        raise
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=45)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
        state['ended_utc'] = survey.io.utc()
        survey.io.write(state_path, state)
        lock.close()
    return state


if __name__ == '__main__':
    def stop(_signum, _frame):
        raise KeyboardInterrupt('Successor stopped')
    signal.signal(signal.SIGTERM, stop)
    parser = argparse.ArgumentParser()
    parser.add_argument('--authorization', required=True)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    print(survey.json.dumps(main(args.authorization, args.execute)))
