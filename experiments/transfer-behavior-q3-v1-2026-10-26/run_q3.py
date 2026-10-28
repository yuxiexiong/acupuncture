"""Three original benign prompts, fixed target recipes, unchanged generation engine."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
TRANSFER = PROJECT / 'experiments/transfer-toy-v1-2026-10-26'


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_inputs():
    manifest = read(HERE / 'manifest.json')
    for name, digest in manifest['files'].items():
        assert sha(PROJECT / name) == digest, name
    questions = read(HERE / 'questions.json')
    assert [q['id'] for q in questions] == ['Q01', 'Q02', 'Q03']
    assert len({q['prompt'] for q in questions}) == 3
    assert set(manifest['targets']) == {'9b', '2b'}
    for spec in manifest['targets'].values():
        prior = read(PROJECT / spec['reference'])
        assert prior['status'] == 'completed' and prior['hooks_removed']
        assert {'long-T_0', 'long-true_S_recipe'} <= {c['id'] for c in prior['cases']}
    return manifest, questions


def run(args):
    manifest, questions = check_inputs()
    sys.path.insert(0, str(TRANSFER))
    from run_io import write, immutable, utc
    from transfer_engine import TransferEngine

    spec = manifest['targets'][args.target]
    args.output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    receipt = {'status': 'running', 'started_utc': utc(), 'pid': os.getpid(),
               'target': args.target, 'device': os.environ.get('CUDA_VISIBLE_DEVICES'),
               'manifest_sha256': sha(HERE / 'manifest.json'), 'completed_answers': 0,
               'expected_answers': 6, 'engineering_checks': []}
    write(args.output / 'receipt.json', receipt)
    try:
        engine = TransferEngine(spec['model'], bundle=PROJECT / spec['bundle'])
        reference = read(PROJECT / spec['reference'])
        assert engine.metadata['versions'] == reference['engine']['versions']
        assert engine.metadata['numerical_settings'] == reference['engine']['numerical_settings']
        assert engine.weight_hashes == reference['engine']['target_weight_sha256_before']
        receipt['engine'] = engine.metadata
        receipt['caller_applies_native_chat_template'] = True
        receipt['conditions'] = engine.conditions['true_S_recipe']
        prose = 'A public library records book titles, shelf locations, and return dates. Its catalogue helps readers locate material and staff maintain accurate records. '
        control = prose * 40 + '\nExplain in detail how a library can keep this catalogue accurate.'
        def render(text):
            return engine.tokenizer.apply_chat_template([{'role': 'user', 'content': text}],
                tokenize=False, add_generation_prompt=True, enable_thinking=False)
        context = render(control)
        calibration = engine.calibrate([context])[0]
        for arm in ('T_0', 'true_S_recipe'):
            prior = next(c for c in reference['cases'] if c['id'] == 'long-' + arm)
            check = {'condition': arm, 'prefix_tokens': 32, 'calibration': calibration,
                     'calibration_matches': calibration == prior['calibration']}
            receipt['engineering_checks'].append(check)
            write(args.output / 'receipt.json', receipt)
            assert calibration == prior['calibration'], 'Changed control calibration'
            result = engine.generate([context], arm, [calibration], 32, [])[0]
            check.update(output=result,
                exact_historical_match=result['token_ids'] == prior['output']['token_ids'][:32],
                input_matches=result['input_token_sha256'] == prior['output']['input_token_sha256'])
            write(args.output / 'receipt.json', receipt)
            assert result['token_ids'] == prior['output']['token_ids'][:32], 'Control prefix mismatch'
            assert result['input_token_sha256'] == prior['output']['input_token_sha256']
        for question in questions:
            context = render(question['prompt'])
            calibration = engine.calibrate([context])[0]
            for arm in ('T_0', 'true_S_recipe'):
                receipt.update(current_question=question['id'], current_condition=arm)
                write(args.output / 'receipt.json', receipt)
                begin = time.monotonic()
                result = engine.generate([context], arm, [calibration], 1024, [])[0]
                record = {'status': 'completed', 'model': args.target, 'question': question,
                    'condition': arm, 'context': context, 'calibration': calibration,
                    'output': result, 'elapsed_seconds': time.monotonic() - begin, 'ended_utc': utc()}
                immutable(args.output / 'records' / f"{question['id']}-{arm}.jsonl", record)
                receipt['completed_answers'] += 1
                receipt['elapsed_seconds'] = time.monotonic() - started
                write(args.output / 'receipt.json', receipt)
                print({'question': question['id'], 'arm': arm, 'completed': receipt['completed_answers'],
                       'tokens': result['generated_token_count']}, flush=True)
        assert receipt['completed_answers'] == 6
        check_inputs()
        receipt.update(status='completed', **engine.verify_unchanged())
    except Exception as error:
        receipt.update(status='failed', error=str(error), traceback=traceback.format_exc())
        raise
    finally:
        receipt.update(ended_utc=utc(), elapsed_seconds=time.monotonic() - started)
        write(args.output / 'receipt.json', receipt)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', choices=['9b', '2b'])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        check_inputs()
        print('PASS: fixed three prompts, frozen files, both historical control receipts')
    else:
        assert args.target and args.output
        run(args)
