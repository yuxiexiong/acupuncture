"""Versioned early-input-control experiment. Importing this file never loads a model."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import random
import subprocess
import time
import traceback

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
LAYERS = tuple(range(4)) + tuple(range(12, 16)) + tuple(range(24, 28))
VECTOR_LAYERS = (0, 3, 12, 15, 24, 27)
DOSES = (-1., -.5, -.25, .25, .5, 1.)
CONFIRM_DOSES = (-1., -.5, .5, 1.)
DEPENDENCIES = [
    'layer-survey-toy-v1-2026-10-27/survey_engine.py',
    'layer-survey-toy-v1-2026-10-27/questions.json',
    'layer-survey-toy-v1-2026-10-27/contract.json',
    'layer-dose-survey-toy-v1-2026-10-27/selection.json',
    'layer-dose-survey-toy-v1-2026-10-27/asset_manifest.json',
    'layer-dose-survey-toy-v1-2026-10-27/dose_engine.py',
    'layer-negative-dose-survey-toy-v1-2026-10-27/dose_engine.py',
    'transfer-toy-v1-2026-10-26/transfer_engine.py',
    'capability-damage-v2-2026-10-26/model_engine.py',
    'joint-behavior-capability-v1-2026-10-28/data/items.json',
    'joint-behavior-capability-v1-2026-10-28/joint_engine.py',
]


def utc():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    allow_nan=False).encode()).hexdigest()


def write(path, value, immutable=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    if immutable:
        with path.open('x') as f:
            f.write(data)
    else:
        temporary = path.with_suffix(path.suffix + '.tmp')
        temporary.write_text(data)
        temporary.replace(path)


def save_prepared(path, value):
    if Path(path).exists():
        assert read(path) == value, f'Prepared identity differs: {path}'
    else:
        write(path, value, immutable=True)


def prepare():
    source = read(REPO / 'experiments/layer-dose-survey-toy-v1-2026-10-27/selection.json')
    selected = []
    for row in source['selected_channels']:
        if row['model_id'] != '4b' or row['layer'] not in LAYERS:
            continue
        remaining = sorted(set(row['candidate_channels']) - {row['channel']})
        seed = f'acupuncture-early-input-control-v1:4b:{row["layer"]}'
        selected.append({'layer': row['layer'], 'channels': [row['channel'], random.Random(seed).choice(remaining)],
                         'candidate_channels': row['candidate_channels'], 'additional_seed': seed,
                         'historical_first_channel': row['channel']})
    selected.sort(key=lambda r: r['layer'])
    vectors = []
    for i in range(2):
        seed = f'acupuncture-early-input-control-v1:direction:{i}'
        rng = random.Random(seed)
        values = [rng.gauss(0, 1) for _ in range(2560)]
        norm = math.sqrt(sum(x*x for x in values))
        vector = [x/norm for x in values]
        vectors.append({'id': f'V{i}', 'seed': seed, 'values': vector, 'sha256': digest(vector)})
    save_prepared(HERE / 'selection.json', {'layers': list(LAYERS), 'selected': selected,
        'source_sha256': sha(REPO / 'experiments/layer-dose-survey-toy-v1-2026-10-27/selection.json')})
    save_prepared(HERE / 'data/directions.json', vectors)
    old = read(REPO / 'experiments/joint-behavior-capability-v1-2026-10-28/contract.json')['source']
    metadata = read(REPO / 'experiments/layer-survey-toy-v1-2026-10-27/survey-r01/4b-shard-0/metadata.json')
    source_model = dict(old)
    source_model['target_weight_sha256'] = metadata['target_weight_sha256_before']
    value = {'schema': 1, 'experiment': HERE.name, 'created_for': '2026-10-29',
        'status': 'prepared_not_formally_authorized', 'source': source_model,
        'user_instruction': '写合同，代码，做测试，然后报给我 ETA。',
        'current_authorization': 'cpu_tests_and_bounded_gpu_preflight_only',
        'generation': {'max_new_tokens': 128, 'greedy': True, 'batch_size': 1, 'dtype': 'bfloat16',
            'attention_backend': 'eager', 'thinking': False, 'eos': [248044, 248046],
            'branch_budget_includes_prefix': True},
        'layers': list(LAYERS), 'direction_layers': list(VECTOR_LAYERS),
        'development_doses': list(DOSES), 'confirmation_doses': list(CONFIRM_DOSES),
        'calibration': 'fact0 required clean prompt, all fact/mode/direction branches share reference; historical Q uses its own original clean prompt',
        'counts': {'development_inputs': 24, 'confirmation_inputs': 24, 'anchors': 8,
            'development_conditions': 193, 'development_generations': 4632,
            'confirmation_conditions': 145, 'confirmation_generations': 3480,
            'mechanism_max_conditions': 6, 'patch_max_symptoms': 2, 'patch_max_candidates_per_symptom': 2},
        'preflight_limits_per_worker': {'generations_or_branches': 128, 'candidate_continuations': 512,
            'donor_replays': 32, 'calibration_prompts': 20, 'maximum_tokens_per_generation': 128},
        'preflight_confirmation_model_outputs': False,
        'formal_gates': {'development': ['preflight', 'data_review', 'new_formal_authorization'],
            'mechanism': ['development_verified', 'measurement_review', 'selection_freeze'],
            'patch': ['mechanism_verified', 'candidate_selection_freeze'],
            'confirmation': ['development_and_mechanism_interpretation_locked', 'selection_freeze']},
        'fork_steps': [4, 16], 'formal_automatic_launch': False}
    save_prepared(HERE / 'contract.json', value)
    save_prepared(HERE / 'readiness/preflight-cases-r01.json', preflight_cases())
    return {'status': 'prepared', 'conditions': {s: len(conditions(s)) for s in ('development', 'confirmation')}}


def conditions(stage):
    assert stage in ('development', 'confirmation')
    result = [{'id': 'clean', 'kind': 'clean', 'dose': 0.0}]
    doses = DOSES if stage == 'development' else CONFIRM_DOSES
    for row in read(HERE / 'selection.json')['selected']:
        for channel in row['channels']:
            for dose in doses:
                result.append({'id': f'N_L{row["layer"]:02d}_C{channel}_D{dose:+g}', 'kind': 'native',
                    'layer': row['layer'], 'channel': channel, 'dose': dose})
    for layer in VECTOR_LAYERS:
        for i in range(2):
            for dose in CONFIRM_DOSES:
                result.append({'id': f'V{i}_L{layer:02d}_D{dose:+g}', 'kind': 'direction',
                    'layer': layer, 'direction_id': f'V{i}', 'dose': dose})
    assert len(result) == (193 if stage == 'development' else 145)
    assert len({r['id'] for r in result}) == len(result)
    return result


def engine_condition(condition):
    result = dict(condition)
    if result['kind'] == 'direction':
        vector = next(r for r in read(HERE / 'data/directions.json') if r['id'] == result['direction_id'])
        assert digest(vector['values']) == vector['sha256']
        result['vector'] = vector['values']
    return result


def preflight_cases():
    table = read(HERE / 'selection.json')['selected']
    plan = {'experiment': HERE.name, 'benchmarks_per_worker': 60, 'workers': {}}
    for gpu in (0, 1):
        bases = [f'{family}{gpu+1:02d}' for family in ('RD', 'AR', 'RL')]
        cases = []
        for n, layer in enumerate(VECTOR_LAYERS):
            channel = next(r['channels'][0] for r in table if r['layer'] == layer)
            for j, dose in enumerate(DOSES):
                cases.append({'item_id': f'{bases[(n+j)%3]}-f{j%2}-required',
                    'condition': {'id': f'N_L{layer:02d}_C{channel}_D{dose:+g}', 'kind': 'native',
                                  'layer': layer, 'channel': channel, 'dose': dose}})
        for n, layer in enumerate((0, 15, 24)):
            for i in range(2):
                for j, dose in enumerate(CONFIRM_DOSES):
                    cases.append({'item_id': f'{bases[(n+i+j)%3]}-f{j%2}-required',
                        'condition': {'id': f'V{i}_L{layer:02d}_D{dose:+g}', 'kind': 'direction',
                            'layer': layer, 'direction_id': f'V{i}', 'dose': dose}})
        assert len(cases) == 60
        plan['workers'][str(gpu)] = {'benchmarks': cases, 'technical_controls':
            ['clean/zero/restored', 'legacy_native_positive_negative', 'prefill/decode/last/except_last',
             'continue/withdraw/rebuild_at_4_and_16', 'six_patch_arms', 'full_logit_candidate_crosscheck']}
    return plan


def frozen_paths():
    return sorted(HERE.glob('*.py')) + [HERE / n for n in ('CONTRACT.zh-CN.md', 'contract.json', 'selection.json',
        'data/development.json', 'data/confirmation.json', 'data/anchors.json', 'data/directions.json',
        'readiness/preflight-cases-r01.json')] + [REPO / 'experiments' / n for n in DEPENDENCIES]


def freeze(path):
    value = {'experiment': HERE.name, 'created_at': utc(),
             'files': {str(p.relative_to(REPO)): sha(p) for p in frozen_paths()}}
    write(path, value, immutable=True)
    return {'path': str(path), 'sha256': sha(path), 'files': len(value['files'])}


def check(path):
    value = read(path)
    assert value['experiment'] == HERE.name
    actual = {str(p.relative_to(REPO)): sha(p) for p in frozen_paths()}
    assert value['files'] == actual, 'Frozen source changed; preserve old attempt and create a new freeze'
    return {'status': 'passed', 'freeze_sha256': sha(path), 'files': len(actual)}


def authorize(path, stage, execute):
    if not execute or not path:
        raise ValueError('Bound user authorization and --execute are required before model loading')
    auth = read(path)
    assert auth['status'] == 'authorized' and auth['experiment'] == HERE.name
    assert stage in auth['allowed_stages'] and auth['user_instruction']
    fp = HERE / auth['freeze_path']
    assert sha(fp) == auth['freeze_sha256']
    check(fp)
    assert auth['maximum_workers'] == 2
    if stage == 'preflight':
        required = auth['required_evidence']
        for role in ('cpu_evidence_path', 'data_review_path', 'tokenizer_evidence_path', 'code_review_path'):
            relative = auth[role]
            assert relative in required and sha(HERE / relative) == required[relative]
            evidence = read(HERE / relative)
            assert evidence['status'] == 'passed', role
            for name, expected in evidence.get('source_hashes', {}).items():
                assert sha(REPO / name) == expected, name
        cpu = read(HERE / auth['cpu_evidence_path'])
        assert cpu['tests_run'] > 0 and cpu['failures'] == cpu['errors'] == cpu['skipped'] == 0
        data_review = read(HERE / auth['data_review_path'])
        assert len(data_review['rows']) == 56 and all(r['status'] == 'reviewed' for r in data_review['rows'])
        data_hashes = {r['evidence_path']: r['evidence_file_sha256'] for r in data_review['rows']}
        for name, expected in data_hashes.items():
            assert sha(REPO / name) == expected
        assert auth['preflight_limits_per_worker'] == read(HERE / 'contract.json')['preflight_limits_per_worker']
    else:
        assert auth.get('formal_execution_authorized') is True
        for evidence, expected in auth['required_evidence'].items():
            assert sha(HERE / evidence) == expected
        assert auth['required_evidence'], 'Formal authorization must bind passed preflight and data review'
        from execution import validate_formal_authorization
        validate_formal_authorization(auth, stage)
    return auth


def items(split):
    assert split in ('development', 'confirmation', 'anchors')
    return read(HERE / 'data' / f'{split}.json')


def contexts_for(tokenizer, rows):
    return {r['id']: tokenizer.apply_chat_template([{'role': 'user',
        'content': r.get('user_message', r['prompt'])}], tokenize=False, add_generation_prompt=True,
        enable_thinking=False) for r in rows}


def assigned(rows, gpu):
    bases = list(dict.fromkeys(r['base_id'] for r in rows))
    return [r for r in rows if bases.index(r['base_id']) % 2 == gpu]


def model_spec():
    source = read(HERE / 'contract.json')['source']
    return {'id': '4b', 'layers': 32, 'hidden_size': 2560, 'intermediate_size': 9216,
            'revision': source['revision']}


def model_assets():
    manifest = REPO / 'experiments/layer-dose-survey-toy-v1-2026-10-27/asset_manifest.json'
    expected = read(manifest)['4b']
    source = read(HERE / 'contract.json')['source']
    assert expected['revision'] == source['revision']
    started = time.monotonic()
    for name, row in expected['files'].items():
        path = Path(source['model_path']) / name
        assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], name
    return {'status': 'passed', 'files': len(expected['files']), 'manifest_sha256': sha(manifest),
            'wall_seconds': time.monotonic() - started}


def metadata_check(engine):
    source = read(HERE / 'contract.json')['source']
    assert engine.weight_hashes == source['target_weight_sha256']
    for p in ('torch', 'transformers'):
        assert engine.metadata['versions'][p] == source[p + '_version']
    assert engine.stop_ids == [248044, 248046] and len(engine.layers) == 32


def run(stage, gpu, output, authorization, execute=False):
    auth = authorize(authorization, stage, execute)
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root'] / f'worker-{gpu}').resolve()
    assert output.is_relative_to((HERE / 'runs').resolve())
    import fcntl
    lock = open(f'/tmp/acupuncture-layer-survey-gpu{gpu}.lock', 'w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    processes = subprocess.check_output(['nvidia-smi', f'--id={gpu}', '--query-compute-apps=pid',
        '--format=csv,noheader,nounits'], text=True).strip()
    assert not processes, 'GPU has an existing compute process; do not disturb it'
    output.mkdir(parents=True, exist_ok=False)
    receipt = {'status': 'running', 'stage': stage, 'gpu': gpu, 'pid': os.getpid(),
        'started_at': utc(), 'freeze_path': auth['freeze_path'], 'freeze_sha256': auth['freeze_sha256'],
        'authorization_sha256': sha(authorization), 'record_hashes': {}, 'asset_hashes': {}}
    write(output / 'execution.json', dict(receipt), immutable=True)
    write(output / 'authorization.json', auth, immutable=True)
    write(output / 'receipt.json', receipt)
    started, engine = time.monotonic(), None
    try:
        from control_engine import ControlEngine
        source = read(HERE / 'contract.json')['source']
        receipt['asset_identity'] = model_assets()
        engine = ControlEngine(source['model_path'], model_spec(), f'cuda:{gpu}')
        metadata_check(engine)
        receipt['load_and_identity_seconds'] = time.monotonic() - started
        write(output / 'metadata.json', engine.metadata, immutable=True)
        receipt['asset_hashes']['metadata.json'] = sha(output / 'metadata.json')
        if stage == 'preflight':
            from preflight import run_preflight
            receipt['preflight'] = run_preflight(engine, gpu, output, receipt)
        else:
            from execution import run_formal
            run_formal(engine, stage, gpu, output, receipt, auth)
        receipt['integrity'] = engine.verify_unchanged()
        receipt['status'] = 'completed'
    except BaseException:
        receipt.update(status='failed', error=traceback.format_exc())
        if engine is not None:
            try:
                receipt['integrity_after_failure'] = engine.verify_unchanged()
            except BaseException:
                receipt['integrity_error'] = traceback.format_exc()
        raise
    finally:
        receipt.update(finished_at=utc(), wall_seconds=time.monotonic() - started)
        write(output / 'receipt.json', receipt)
    return receipt


def verify_worker(path):
    path = Path(path)
    r = read(path / 'receipt.json')
    assert r['status'] == 'completed'
    assert r['freeze_sha256'] == sha(HERE / r['freeze_path'])
    assert r['authorization_sha256'] == sha(path / 'authorization.json')
    execution = read(path / 'execution.json')
    for key in ('stage', 'gpu', 'pid', 'started_at', 'freeze_path', 'freeze_sha256', 'authorization_sha256'):
        assert execution[key] == r[key], f'Execution/receipt identity mismatch: {key}'
    check(HERE / r['freeze_path'])
    for name, expected in {**r['record_hashes'], **r['asset_hashes']}.items():
        assert sha(path / name) == expected, name
    assert r['integrity']['hooks_removed'] is True
    assert r['integrity']['target_weight_sha256_after'] == read(path / 'metadata.json')['target_weight_sha256_before']
    assert read(path / 'exit.json')['returncode'] == 0
    if r['stage'] == 'preflight':
        from preflight import verify_output
        p = read(path / 'preflight.json')
        assert p['status'] == 'passed' and p['confirmation_model_outputs'] == 0
        assert len(p['benchmark_records']) == 60 and len(set(p['benchmark_records'])) == 60
        benchmark_rows = read(HERE / 'readiness/preflight-cases-r01.json')['workers'][str(r['gpu'])]['benchmarks']
        assert p['benchmark_records'] == [f'records/benchmark-{i:03d}.json' for i in range(60)]
        for name, expected in zip(p['benchmark_records'], benchmark_rows):
            row = read(path / name)
            assert row['item']['id'] == expected['item_id']
            assert row['condition'] == engine_condition(expected['condition'])
        for k in (4, 16):
            assert any(c['check'] == f'fork_{k}_same_state_then_withdraw' and c['status'] == 'passed' for c in p['checks'])
        for name in p['benchmark_records']:
            assert name in r['record_hashes']
        for name in r['record_hashes']:
            row = read(path / name)
            if 'output' in row:
                assert row['item']['id'] not in {i['id'] for i in items('confirmation')}
                verify_output(row['output'], row['reference_calibration'], row['condition'], row['context'], row['mode'])
                for choice in row['choices']:
                    verify_output(choice, row['reference_calibration'], row['condition'], row['context'], row['mode'])
        for key, actual in p['counters'].items():
            if key in p['limits']:
                assert actual <= p['limits'][key]
    else:
        from execution import verify_formal_records
        verify_formal_records(path, r)
    return {'status': 'passed', 'stage': r['stage'], 'records': len(r['record_hashes']),
            'freeze_sha256': r['freeze_sha256']}


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('prepare')
    for name in ('freeze', 'check', 'verify'):
        q = sub.add_parser(name); q.add_argument('path')
    q = sub.add_parser('run')
    q.add_argument('--stage', required=True, choices=['preflight', 'development', 'confirmation', 'mechanism', 'patch'])
    q.add_argument('--gpu', required=True, type=int, choices=[0, 1])
    q.add_argument('--output', required=True); q.add_argument('--authorization', required=True)
    q.add_argument('--execute', action='store_true')
    args = p.parse_args()
    if args.command == 'prepare': value = prepare()
    elif args.command == 'freeze': value = freeze(args.path)
    elif args.command == 'check': value = check(args.path)
    elif args.command == 'verify': value = verify_worker(args.path)
    else: value = run(args.stage, args.gpu, args.output, args.authorization, args.execute)
    print(json.dumps(value, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
