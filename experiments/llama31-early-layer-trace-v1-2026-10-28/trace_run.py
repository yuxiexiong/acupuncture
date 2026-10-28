"""Llama sources and native checks around the unchanged trace worker."""
import argparse
from functools import lru_cache
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
BASE = ROOT.parent / 'early-layer-mechanism-v1-2026-10-28'
LLAMA = ROOT.parent / 'llama31-single-point-dose-survey-v1-2026-10-28'
MODEL = 'llama31-8b-instruct'
MODELS = (MODEL,)
TOTAL = 920


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


original = load('llama_trace_original_runner', BASE / 'trace_run.py')
source_checks = load('llama_trace_native_checks', LLAMA / 'survey.py')
read, write, sha, utc = original.read, original.write, original.sha, original.utc


def check_output(output):
    tokens = output['token_ids']
    assert all(type(t) is int and 0 <= t < 128256 for t in tokens)
    assert output['token_sha256'] == source_checks.token_hash(tokens)
    assert output['generated_token_count'] == len(tokens) and 0 < len(tokens) <= 128
    assert output['max_new_tokens'] == 128 and output['returned_padding_count'] == 0
    assert output['batch_size'] == 1 and output['end_reason'] in ('eos_token', 'length_limit')
    assert (output['end_reason'] == 'eos_token') == (tokens[-1] in source_checks.STOP_IDS)
    assert not any(t in source_checks.STOP_IDS for t in tokens[:-1])
    assert output['end_reason'] != 'length_limit' or len(tokens) == 128


def compatible_metadata(current, source):
    assert {k: v for k, v in current.items() if k != 'device'} == {
        k: v for k, v in source.items() if k != 'device'}, 'Llama source runtime/model metadata mismatch'


def validate_freeze():
    frozen = read(ROOT / 'freeze.json')
    assert frozen['experiment'] == ROOT.name
    for name, digest in frozen['files'].items():
        assert sha(REPO / name) == digest, f'Frozen file changed: {name}'
    return sha(ROOT / 'freeze.json')


def validate_authorization(path):
    auth = read(path)
    assert auth['status'] == 'authorized' and auth['purpose'] == 'llama_early_trace_queue'
    assert auth['experiment'] == ROOT.name and auth['user_instruction']
    assert auth['freeze_sha256'] == validate_freeze()
    assert auth['models'] == list(MODELS)
    assert auth['maximum_records'] == {'preflight': 14, 'survey': TOTAL}
    assert auth['maximum_generations'] == {'preflight': 38, 'survey': TOTAL * 2}
    assert auth['queue_sha256'] == sha(ROOT / 'queue_run.py')
    assert auth['predecessor']['freeze_sha256'] == read(ROOT / 'contract.json')['queue']['predecessor_freeze_sha256']
    evidence = auth['cpu_test_receipt']
    assert sha(ROOT / evidence['path']) == evidence['sha256']
    cpu = read(ROOT / evidence['path'])
    assert cpu['status'] == 'passed' and cpu['failures'] == cpu['errors'] == cpu['skipped'] == 0
    assert cpu['freeze_sha256'] == auth['freeze_sha256']
    return auth


@lru_cache(maxsize=1)
def adapted_runner():
    # Reuse the complete worker/acceptance logic without editing a live dependency.
    runner = load('llama_trace_worker_runner', BASE / 'trace_run.py')
    runner.ROOT, runner.MODELS, runner.EXPECTED = ROOT, MODELS, {MODEL: TOTAL}
    runner.validate_authorization = validate_authorization
    native = SimpleNamespace(check_model_assets=source_checks.check_model_assets,
        compatible_metadata=compatible_metadata, token_hash=source_checks.token_hash, check_output=check_output)
    original_loader = runner.load_module
    runner.load_module = lambda name, path: native if name == 'trace_source_checks' else original_loader(name, path)
    return runner


def verify_worker(output, mode, model, shard):
    assert model == MODEL
    return adapted_runner().verify_worker(output, mode, model, shard)


def worker(args):
    auth = validate_authorization(args.authorization)
    from queue_run import predecessor_ready
    assert predecessor_ready(auth)[0]
    accepted = read(Path(auth['remote_output']) / 'predecessor-accepted.json')
    assert accepted['status'] == 'passed' and accepted['predecessor'] == auth['predecessor']
    assert args.model == MODEL and args.mode in ('preflight', 'survey')
    adapted_runner().worker(args)


def prepare():
    assert not (ROOT / 'freeze.json').exists(), 'Never overwrite a frozen run'
    from source_prepare import prepare_sources
    manifest = prepare_sources()
    # Source JSONL is frozen once; external weights remain out of this repository.
    paths = set(ROOT.glob('*.py')) | {ROOT / n for n in (
        'contract.json', 'CONTRACT.zh-CN.md', 'sources.jsonl', 'source-metadata.json', 'source-manifest.json')}
    for base in (BASE, LLAMA):
        frozen = read(base / 'freeze.json')
        paths.add(base / 'freeze.json')
        paths.update(REPO / name for name in frozen['files'] if name.endswith('.py') or base == LLAMA)
    paths.add(BASE / 'queue_run.py')
    write(ROOT / 'freeze.json', {'experiment': ROOT.name, 'created_utc': utc(),
        'files': {str(p.relative_to(REPO)): sha(p) for p in sorted(paths)}})
    return manifest


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('prepare')
    task = sub.add_parser('worker')
    task.add_argument('--mode', choices=('preflight', 'survey'), required=True)
    task.add_argument('--model', choices=MODELS, required=True)
    task.add_argument('--shard', type=int, choices=(0, 1), required=True)
    task.add_argument('--gpu', type=int, choices=(0, 1), required=True)
    task.add_argument('--output', type=Path, required=True)
    task.add_argument('--authorization', type=Path, required=True)
    task.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if args.command == 'prepare':
        print(json.dumps(prepare(), ensure_ascii=False))
    else:
        worker(args)


if __name__ == '__main__':
    main()
