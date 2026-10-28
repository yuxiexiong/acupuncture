"""Wait behind all Qwen extension stages, then validate and trace Llama L0-L5."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import signal

import trace_run as run

ROOT = Path(__file__).resolve().parent
MODEL, TOTAL = run.MODEL, run.TOTAL
read, write, sha, utc = run.read, run.write, run.sha, run.utc
queue = run.load('llama_trace_shared_queue', run.BASE / 'queue_run.py')
queue.ROOT, queue.MODELS, queue.TOTAL = ROOT, (MODEL,), TOTAL


def predecessor_ready(auth):
    source = auth['predecessor']; path = Path(source['run'])
    assert sha(path / 'execution.json') == source['execution_sha256'], 'Predecessor execution changed'
    assert sha(path.parent / 'freeze.json') == source['freeze_sha256'], 'Predecessor freeze changed'
    state = read(path / 'queue-state.json')
    assert state['freeze_sha256'] == source['freeze_sha256'] and state['pid'] == source['process']['pid']
    assert state['status'] in ('waiting', 'running_survey', 'completed'), 'Predecessor failed or stopped'
    if state['status'] != 'completed':
        assert queue.process_alive(source['process']), 'Predecessor stopped without a terminal receipt'
        return False, 'predecessor_running'
    assert state['completed_records'] == state['expected_records'] == 4560
    assert set(state['stages']) == {'six-layer', '4b-full'}
    for stage, models, count in (('six-layer', ('4b', '2b'), 152), ('4b-full', ('4b',), 1976)):
        expected = {f'{m}-shard-{s}' for m in models for s in (0, 1)}
        assert set(state['stages'][stage]) == expected
        for key, worker in state['stages'][stage].items():
            folder = path / stage / 'survey' / key
            receipt = read(folder / 'receipt.json')
            model, shard = key.rsplit('-shard-', 1)
            assert receipt['model_id'] == model
            assert receipt['shard'] == int(shard)
            assert worker['status'] == 'completed' and worker['exit_code'] == 0
            assert (folder.parent / f'{key}.exit').read_text().strip() == '0'
            assert sha(folder / 'receipt.json') == worker['receipt_sha256']
            assert receipt['status'] == 'completed' and receipt['checks_passed'] is True
            assert receipt['freeze_sha256'] == source['freeze_sha256']
            assert receipt['completed_records'] == receipt['expected_records'] == count
            assert receipt['integrity']['hooks_removed'] is True
    if queue.process_alive(source['process']):
        return False, 'predecessor_exiting'
    return True, 'predecessor_completed'


def prerequisites(path, expected_hash=None):
    if expected_hash is not None:
        assert sha(path) == expected_hash, 'Authorization changed while queued'
    return run.validate_authorization(path)


queue.prerequisites = prerequisites
queue.predecessor_ready = predecessor_ready


def main(authorization, output, execute=False):
    authorization, output = Path(authorization).resolve(), Path(output).resolve()
    auth = prerequisites(authorization)
    assert str(output) == auth['remote_output'] and not output.exists(), 'Never overwrite or resume partial evidence'
    if not execute:
        ready, reason = predecessor_ready(auth)
        return {'status': 'ready', 'predecessor_ready': ready, 'wait_reason': reason, 'expected_records': TOTAL}
    with (ROOT / '.queue.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        output.mkdir(parents=True)
        digest = sha(authorization)
        state = {'status': 'waiting', 'experiment': ROOT.name, 'pid': os.getpid(), 'started_utc': utc(),
            'authorization_sha256': digest, 'freeze_sha256': auth['freeze_sha256'],
            'expected_records': TOTAL, 'completed_records': 0, 'stages': {}}
        write(output / 'execution.json', state.copy())
        queue.save_state(output, state)
        try:
            queue.wait_ready(authorization, digest, output, state)
            write(output / 'predecessor-accepted.json', {'status': 'passed', 'predecessor': auth['predecessor'],
                'verified_utc': utc(), 'expected_records': 4560})
            for mode in ('preflight', 'survey'):
                state.update(status=f'running_{mode}', mode=mode, model=MODEL)
                queue.run_pair(mode, MODEL, authorization, digest, output, state)
                if mode == 'preflight':
                    workers = state['stages'][mode]
                    assert set(workers) == {f'{MODEL}-shard-{s}' for s in (0, 1)}
                    assert all(w['status'] == 'completed' and w['exit_code'] == 0 for w in workers.values())
                    write(output / 'preflight-accepted.json', {'status': 'passed', 'freeze_sha256': auth['freeze_sha256'],
                        'accepted_utc': utc(), 'workers': workers})
            queue.save_state(output, state)
            assert state['completed_records'] == TOTAL
            state['status'] = 'completed'
        except BaseException as error:
            state.update(status='failed', error=repr(error))
            raise
        finally:
            state['ended_utc'] = utc()
            queue.save_state(output, state)
        return state


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, queue.stop)
    parser = argparse.ArgumentParser()
    parser.add_argument('--authorization', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    print(json.dumps(main(args.authorization, args.output, args.execute)))
