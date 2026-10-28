"""Append missing traces using the unchanged, GPU-validated collection engine."""
import argparse
from collections import Counter
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
BASE = ROOT.parent / 'early-layer-mechanism-v1-2026-10-28'
STAGES = (('six-layer', ('4b', '2b')), ('4b-full', ('4b',)))
TOTAL = 4560


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


original = load('extension_original_runner', BASE / 'trace_run.py')
queue_utils = load('extension_queue_utils', BASE / 'queue_run.py')
read, write, sha, utc = original.read, original.write, original.sha, original.utc


def build_inventory():
    contract = read(ROOT / 'contract.json')
    old_ids = {item['trace_id'] for item in original.load_sources()}
    unique = {}
    for source in contract['sources']:
        path = REPO / source['path']
        assert sha(path) == source['sha256']
        with path.open() as stream:
            for line, text in enumerate(stream, 1):
                row = json.loads(text)
                key = original.identity(row)
                reference = {'jsonl': source['path'], 'line': line, 'sha256': source['sha256']}
                if key in unique:
                    item = unique[key]
                    assert item['record']['output']['token_ids'] == row['output']['token_ids']
                    assert item['record']['context'] == row['context'] and item['record']['calibration'] == row['calibration']
                    item['references'].append(reference)
                else:
                    unique[key] = {'record': row, 'references': [reference]}
    assert len(unique) == 13400
    selected = []
    for (model, layer, channel, dose, qid), item in unique.items():
        if model not in ('2b', '4b'):
            continue
        stage = '' if layer is None else 'six-layer' if layer in (4, 5) else '4b-full' if model == '4b' and layer >= 6 else None
        if stage is None:
            continue
        row = item['record']
        provenance, metadata = original.source_provenance(item)
        historical_shard = int(provenance['run'].rsplit('-', 1)[-1])
        selected.append({**item, 'trace_id': original.trace_id(row), 'model': model, 'stage': stage,
                         'shard': -1, 'historical_shard': historical_shard, 'provenance': provenance})
    selected.sort(key=lambda item: item['trace_id'])
    for stage, models in STAGES:
        for model in models:
            rows = [item for item in selected if (item['stage'], item['model']) == (stage, model)]
            keys = sorted({original.identity(item['record'])[1:4] for item in rows})
            for item in rows:
                item['shard'] = keys.index(original.identity(item['record'])[1:4]) % 2
            assert len(rows) == (304 if stage == 'six-layer' else 3952)
            for key in keys:
                assert sorted(i['record']['question_id'] for i in rows if original.identity(i['record'])[1:4] == key) == [f'Q{q:02}' for q in range(1, 9)]
    new_ids = {item['trace_id'] for item in selected if item['stage']}
    assert len(new_ids) == TOTAL and not new_ids & old_ids
    combined = Counter(item['model'] for item in original.load_sources())
    combined.update(item['model'] for item in selected if item['stage'])
    assert combined == {'2b': 920, '4b': 4872, '9b': 920}
    assert len(selected) == 4576  # Sixteen source baselines are calibration-only, never generated again.
    return selected


def sources():
    with (ROOT / 'sources.jsonl').open() as stream:
        return [json.loads(line) for line in stream]


def cases(stage, model, shard):
    assert (stage, model) in {(s, m) for s, models in STAGES for m in models} and shard in (0, 1)
    return [{'name': item['trace_id'], 'record': item, 'arm_override': None}
            for item in sources() if (item['stage'], item['model'], item['shard']) == (stage, model, shard)]


def prepare():
    assert not (ROOT / 'freeze.json').exists(), 'Do not overwrite a frozen extension'
    original.validate_freeze()
    rows = build_inventory()
    (ROOT / 'sources.jsonl').write_text(''.join(json.dumps(item, ensure_ascii=False, allow_nan=False) + '\n' for item in rows))
    metadata = {item['provenance']['run']: read(REPO / item['provenance']['run'] / 'metadata.json') for item in rows}
    write(ROOT / 'source-metadata.json', metadata)
    manifest = {'additional_records': TOTAL, 'baseline_generation_count': 0, 'calibration_only_source_baselines': 16,
                'existing_records_reused': 2152, 'combined_unique_records': 6712,
                'combined_counts': {'2b': 920, '4b': 4872, '9b': 920},
                'stages': {stage: {model: {str(s): len(cases(stage, model, s)) for s in (0, 1)} for model in models} for stage, models in STAGES},
                'no_overlap_with_existing_collection': True, 'created_utc': utc()}
    write(ROOT / 'source-manifest.json', manifest)
    paths = list(ROOT.glob('*.py')) + [ROOT / name for name in ('contract.json', 'CONTRACT.zh-CN.md', 'sources.jsonl', 'source-metadata.json', 'source-manifest.json')]
    paths += [REPO / name for name in read(BASE / 'freeze.json')['files']] + [BASE / 'freeze.json']
    write(ROOT / 'freeze.json', {'experiment': ROOT.name, 'created_utc': utc(), 'files': {str(p.relative_to(REPO)): sha(p) for p in sorted(set(paths))}})
    return manifest


def validate_freeze():
    frozen = read(ROOT / 'freeze.json')
    assert frozen['experiment'] == ROOT.name
    for name, digest in frozen['files'].items():
        assert sha(REPO / name) == digest, f'Frozen file changed: {name}'
    return sha(ROOT / 'freeze.json')


def validate_authorization(path):
    auth = read(path)
    assert auth['status'] == 'authorized' and auth['purpose'] == 'trace_extension_queue'
    assert auth['experiment'] == ROOT.name and auth['user_instruction']
    assert auth['freeze_sha256'] == validate_freeze()
    assert auth['maximum_records'] == TOTAL and auth['maximum_generation_streams'] == TOTAL * 2
    assert auth['stages'] == [{'id': stage, 'models': list(models)} for stage, models in STAGES]
    assert auth['predecessor']['freeze_sha256'] == sha(BASE / 'freeze.json')
    cpu = auth['cpu_test_receipt']
    assert sha(ROOT / cpu['path']) == cpu['sha256']
    result = read(ROOT / cpu['path'])
    assert result['status'] == 'passed' and result['failures'] == result['errors'] == result['skipped'] == 0
    assert result['freeze_sha256'] == auth['freeze_sha256']
    return auth


def predecessor_ready(auth):
    source = auth['predecessor']
    path = Path(source['run'])
    assert sha(path / 'execution.json') == source['execution_sha256']
    state = read(path / 'queue-state.json')
    assert state['freeze_sha256'] == source['freeze_sha256']
    assert state['pid'] == source['process']['pid']
    assert state['status'] in ('waiting', 'running_preflight', 'running_survey', 'completed'), 'Predecessor failed or stopped'
    if state['status'] != 'completed':
        return False, 'predecessor_running'
    assert state['completed_records'] == state['expected_records'] == 2152
    expected = {f'{m}-shard-{s}' for m in original.MODELS for s in (0, 1)}
    assert set(state['stages']['survey']) == expected
    for key, worker in state['stages']['survey'].items():
        assert worker['status'] == 'completed' and worker['exit_code'] == 0
        assert (path / 'survey' / f'{key}.exit').read_text().strip() == '0'
        assert sha(path / 'survey' / key / 'receipt.json') == worker['receipt_sha256']
    if queue_utils.process_alive(source['process']):
        return False, 'predecessor_exiting'
    return True, 'predecessor_completed'


def verify_predecessor(auth):
    assert predecessor_ready(auth)[0]
    source = auth['predecessor']; path = Path(source['run'])
    assert sha(path / 'preflight-accepted.json') == source['preflight_accepted_sha256']
    original.require_preflight_acceptance(path / 'survey' / 'unused', {'freeze_sha256': source['freeze_sha256']})
    for model in original.MODELS:
        for shard in (0, 1):
            original.verify_worker(path / 'survey' / f'{model}-shard-{shard}', 'survey', model, shard)
    return {'status': 'passed', 'source_execution_sha256': source['execution_sha256'],
            'source_freeze_sha256': source['freeze_sha256'], 'gpu_preflight_accepted_sha256': source['preflight_accepted_sha256'],
            'reused_records': 2152, 'verified_utc': utc()}


def acceptance(auth):
    result = read(Path(auth['remote_output']) / 'predecessor-accepted.json')
    assert result['status'] == 'passed'
    assert result['source_execution_sha256'] == auth['predecessor']['execution_sha256']
    assert result['source_freeze_sha256'] == auth['predecessor']['freeze_sha256']
    assert result['gpu_preflight_accepted_sha256'] == auth['predecessor']['preflight_accepted_sha256']
    assert predecessor_ready(auth)[0]


def adapted_runner(stage):
    # ponytail: reuse the validated worker in an isolated module; never edit live predecessor code.
    runner = load('extension_worker_runner', BASE / 'trace_run.py')
    runner.ROOT = ROOT
    runner.cases_for = lambda mode, model, shard: cases(stage, model, shard) if mode == 'survey' else []
    def authorize(path):
        auth = validate_authorization(path)
        return {**auth, 'remote_output': str(Path(auth['remote_output']) / stage)}
    runner.validate_authorization = authorize
    runner.require_preflight_acceptance = lambda output, auth: acceptance({**auth, 'remote_output': str(Path(auth['remote_output']).parent)})
    return runner


def verify_worker(stage, model, shard, output):
    return adapted_runner(stage).verify_worker(output, 'survey', model, shard)


def worker(args):
    auth = validate_authorization(args.authorization)
    assert args.stage in dict(STAGES) and args.model in dict(STAGES)[args.stage]
    assert args.output.resolve() == Path(auth['remote_output']) / args.stage / 'survey' / f'{args.model}-shard-{args.shard}'
    acceptance(auth)
    if args.stage == '4b-full':
        state = read(Path(auth['remote_output']) / 'queue-state.json')
        assert all(state['stages']['six-layer'][f'{m}-shard-{s}']['status'] == 'completed' and
                   state['stages']['six-layer'][f'{m}-shard-{s}']['exit_code'] == 0 for m in ('4b', '2b') for s in (0, 1))
    sys.path.insert(0, str(BASE))
    args.mode = 'survey'
    adapted_runner(args.stage).worker(args)


def save_state(output, state):
    workers = {}
    for path in output.glob('*/survey/*/receipt.json'):
        row = read(path)
        workers[f'{path.parents[2].name}/{path.parent.name}'] = {k: row.get(k) for k in ('status', 'completed_records', 'expected_records')}
    state['workers'] = workers
    state['completed_records'] = sum(r['completed_records'] for r in workers.values())
    state['updated_utc'] = utc()
    write(output / 'queue-state.json', state)


def wait_ready(authorization, digest, output, state):
    while True:
        assert sha(authorization) == digest, 'Authorization changed'
        auth = validate_authorization(authorization)
        ready, reason = predecessor_ready(auth)
        apps = queue_utils.gpu_processes() if ready else []
        state.update(wait_reason='gpu_compute_processes' if apps else reason, gpu_compute_processes=apps)
        save_state(output, state)
        if ready and not apps:
            return auth
        time.sleep(10)


def run_pair(stage, model, authorization, digest, output, state):
    processes, logs = {}, []
    folder = output / stage / 'survey'
    folder.mkdir(parents=True, exist_ok=True)
    wait_ready(authorization, digest, output, state)
    try:
        for shard in (0, 1):
            key = f'{model}-shard-{shard}'
            log = (folder / f'{key}.log').open('x');logs.append(log)
            command = [sys.executable, '-B', str(ROOT / 'supplement.py'), 'worker', '--stage', stage,
                       '--model', model, '--shard', str(shard), '--gpu', str(shard), '--authorization', str(authorization),
                       '--output', str(folder / key), '--execute']
            child = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            processes[key] = child
            state['stages'].setdefault(stage, {})[key] = {'pid': child.pid, 'status': 'running', 'started_utc': utc()}
            save_state(output, state)
        while True:
            assert sha(authorization) == digest
            validate_authorization(authorization)
            codes = {key: child.poll() for key, child in processes.items()}
            if any(code is not None and code != 0 for code in codes.values()):
                raise RuntimeError(f'Extension worker failed: {codes}')
            save_state(output, state)
            if all(code == 0 for code in codes.values()):
                break
            time.sleep(10)
        for shard in (0, 1):
            key = f'{model}-shard-{shard}'
            verify_worker(stage, model, shard, folder / key)
            state['stages'][stage][key].update(status='completed', receipt_sha256=sha(folder / key / 'receipt.json'))
    finally:
        for key, child in processes.items():
            if child.poll() is None:
                child.terminate()
            try:
                code = child.wait(timeout=30)
            except subprocess.TimeoutExpired:
                child.kill();code = child.wait()
            (folder / f'{key}.exit').write_text(str(code) + '\n')
            state['stages'][stage][key].update(exit_code=code, ended_utc=utc())
        for log in logs:
            log.close()
        save_state(output, state)


def main_queue(args):
    assert args.execute
    authorization, output = args.authorization.resolve(), args.output.resolve()
    auth = validate_authorization(authorization)
    assert str(output) == auth['remote_output'] and not output.exists(), 'Never overwrite or rerun existing output'
    with (ROOT / '.queue.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        output.mkdir(parents=True)
        digest = sha(authorization)
        state = {'status': 'waiting', 'pid': os.getpid(), 'experiment': ROOT.name, 'freeze_sha256': auth['freeze_sha256'],
                 'authorization_sha256': digest, 'started_utc': utc(), 'expected_records': TOTAL, 'completed_records': 0, 'stages': {}}
        write(output / 'execution.json', state)
        save_state(output, state)
        try:
            wait_ready(authorization, digest, output, state)
            write(output / 'predecessor-accepted.json', verify_predecessor(auth))
            for stage, models in STAGES:
                for model in models:
                    state.update(status='running_survey', stage=stage, model=model)
                    run_pair(stage, model, authorization, digest, output, state)
            save_state(output, state)
            assert state['completed_records'] == TOTAL
            state['status'] = 'completed'
        except BaseException as error:
            state.update(status='failed', error=repr(error))
            raise
        finally:
            state['ended_utc'] = utc()
            save_state(output, state)
        return state


def stop(_signum, _frame):
    raise KeyboardInterrupt('Stop this extension only; preserve partial evidence')


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, stop)
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('prepare')
    for name in ('queue', 'worker'):
        task = sub.add_parser(name)
        task.add_argument('--authorization', type=Path, required=True)
        task.add_argument('--output', type=Path, required=True)
        task.add_argument('--execute', action='store_true')
        if name == 'worker':
            task.add_argument('--stage', choices=dict(STAGES), required=True)
            task.add_argument('--model', choices=('2b', '4b'), required=True)
            task.add_argument('--shard', type=int, choices=(0, 1), required=True)
            task.add_argument('--gpu', type=int, choices=(0, 1), required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        print(json.dumps(prepare(), ensure_ascii=False))
    elif args.command == 'worker':
        worker(args)
    else:
        print(json.dumps(main_queue(args)))
