"""Verify parallel target dispatch, then preserve the frozen raw/blind/scoring export."""
import argparse
import json
from pathlib import Path
import shutil
import time
import traceback

from run_io import read, rows, sha, utc, write
from run_toy_parallel import assigned_indices
from export_results import (ROOT, TARGET_CONDITIONS, blind_pack, diagnostic_scores, digest_text,
                            dump_rows, paired_html, validate_generation, verified_toy)


def verified_target(directory, data, inputs, shard_count):
    directory = Path(directory)
    assert shard_count in (2, 4, 6)
    assert {p.name for p in directory.glob('shard*') if p.is_dir()} == {f'shard{i}' for i in range(shard_count)}
    frozen = {'behavior': rows(data / 'confirm.jsonl'), 'ability': rows(data / 'ability_diag.jsonl')}
    assert all(len(items) == 64 and len({item['id'] for item in items}) == 64 for items in frozen.values())
    records = {'behavior': [], 'ability': []}
    observed = {'behavior': set(), 'ability': set()}
    identities = []
    source_hashes = {name: sha(ROOT / name) for name in
                     ('run_toy_parallel.py', 'run_toy.py', 'transfer_engine.py', 'run_io.py')}
    for shard in range(shard_count):
        indices = assigned_indices(shard, shard_count)
        shard_root = directory / f'shard{shard}'
        receipt_path = shard_root / 'receipt.json'
        receipt = read(receipt_path)
        inputs[str(receipt_path)] = sha(receipt_path)
        assert receipt['status'] == 'completed' and receipt['kind'] == 'target'
        assert receipt['shard_index'] == shard
        assert receipt['shard_count'] == receipt['actual_worker_count'] == shard_count
        assert receipt['cuda_visible_devices'] == str(shard % 2)
        assert receipt['worker_topology'] == {'processes_per_gpu': shard_count // 2,
            'gpu_slot_by_worker': {str(i): i % 2 for i in range(shard_count)},
            'independent_model_processes': True, 'actual_forward_batch_size': 1,
            'assignment': 'item_index modulo shard_count'}
        assert receipt['completed_behavior'] == receipt['expected_behavior'] == len(indices) * 19
        assert receipt['completed_diagnostic'] == receipt['expected_diagnostic'] == len(indices) * 19
        assert receipt['completed_calibrations'] == receipt['expected_calibrations'] == len(indices) * 2
        assert receipt['hooks_removed'] and receipt['target_weight_sha256_after'] == receipt['engine']['target_weight_sha256_before']
        assert receipt['engine']['batch_size'] == 1 and receipt['engine']['dtype'] == 'bfloat16'
        assert receipt['engine']['attention_backend'] == 'eager'
        assert receipt['source_sha256'] == source_hashes
        assert receipt['original_freeze_sha256'] == sha(ROOT / 'freeze.json')
        assert receipt['data_sha256'] == {name: sha(data / f'{name}.jsonl') for name in ('confirm', 'ability_diag')}
        expected_paths = {f'records/{split}/{index:03d}-{condition}.jsonl'
                          for split in frozen for index in indices for condition in TARGET_CONDITIONS}
        expected_calibrations = {f'calibrations/{split}-{index:03d}.json' for split in frozen for index in indices}
        assert set(receipt['records_sha256']) == expected_paths
        assert {str(p.relative_to(shard_root)) for p in (shard_root / 'records').rglob('*.jsonl')} == expected_paths
        assert set(receipt['calibrations_sha256']) == expected_calibrations
        assert {str(p.relative_to(shard_root)) for p in (shard_root / 'calibrations').glob('*.json')} == expected_calibrations
        identities.append(receipt)
        for split, items in frozen.items():
            for index in indices:
                calibration_path = shard_root / 'calibrations' / f'{split}-{index:03d}.json'
                calibration = read(calibration_path)
                calibration_digest = sha(calibration_path)
                assert receipt['calibrations_sha256'][str(calibration_path.relative_to(shard_root))] == calibration_digest
                inputs[str(calibration_path)] = calibration_digest
                assert calibration['item_id'] == items[index]['id']
                for condition in TARGET_CONDITIONS:
                    path = shard_root / 'records' / split / f'{index:03d}-{condition}.jsonl'
                    digest = sha(path)
                    assert receipt['records_sha256'][str(path.relative_to(shard_root))] == digest
                    content = rows(path)
                    assert len(content) == 1
                    row = content[0]
                    assert row['status'] == 'completed' and row['item'] == items[index] and row['condition'] == condition
                    assert row['calibration'] == calibration and digest_text(row['context']) == calibration['context_sha256']
                    key = (row['item']['id'], condition)
                    assert key not in observed[split]
                    observed[split].add(key)
                    entry = {'model_role': 'target', **row, 'source_file': str(path), 'source_file_sha256': digest}
                    inputs[str(path)] = digest
                    if split == 'behavior':
                        integrity = validate_generation(row['output'])
                        assert row['output_integrity'] == integrity
                        assert row['output']['input_token_sha256'] == calibration['input_token_sha256']
                        entry['export_integrity'] = integrity
                    else:
                        assert len(row['output']['choice_loglikelihoods']) == len(row['item']['continuations'])
                        assert len(row['output']['choice_details']) == len(row['item']['continuations'])
                        assert row['output']['choice_loglikelihoods'] == [detail['loglikelihood'] for detail in row['output']['choice_details']]
                    records[split].append(entry)
    for receipt in identities[1:]:
        for field in ('data_sha256', 'source_sha256', 'conditions_sha256', 'original_freeze_sha256'):
            assert receipt[field] == identities[0][field]
        assert receipt['engine'] == identities[0]['engine']
    for split, items in frozen.items():
        assert observed[split] == {(item['id'], condition) for item in items for condition in TARGET_CONDITIONS}
        order = {item['id']: i for i, item in enumerate(items)}
        records[split].sort(key=lambda row: (order[row['item']['id']], TARGET_CONDITIONS.index(row['condition'])))
    return records


def verify_benchmark(directory, inputs, shard_count):
    from finish_benchmark_parallel import verified_records
    from run_benchmark import frozen_panel
    _, _, items = frozen_panel()
    records, paths, _ = verified_records(directory, items, shard_count)
    assert len(records) == 1400
    finish = directory / 'finish-r01'
    receipt = read(finish / 'receipt.json')
    assert receipt['status'] == 'completed' and receipt['inference_pairs'] == 1400 and receipt['condition_units'] == 2800
    assert receipt['shard_count'] == shard_count
    assert receipt['original_freeze_sha256'] == sha(ROOT / 'freeze.json')
    inputs[str(finish / 'receipt.json')] = sha(finish / 'receipt.json')
    for index in range(shard_count):
        path = directory / f'shard-{index}' / 'receipt.json'
        assert sha(path) == receipt['worker_receipts_sha256'][str(index)]
        inputs[str(path)] = sha(path)
    for name, digest in receipt['artifacts_sha256'].items():
        assert sha(finish / name) == digest
        inputs[str(finish / name)] = digest
    for path in paths:
        inputs[str(path)] = sha(path)
    summary = read(finish / 'summary.json')
    assert summary['status'] == 'completed' and summary['technical_failures'] == 0
    assert {task: row['n'] for task, row in summary['benchmarks'].items()} == {
        'mmlu': 1000, 'arc_challenge': 200, 'gsm8k': 100, 'humaneval': 100}
    return summary


def self_check():
    """CPU-only partition and incomplete/corrupt export guards; no model loading."""
    import tempfile
    from run_toy import condition_order
    for count in (2, 4, 6):
        assigned = [i for shard in range(count) for i in assigned_indices(shard, count)]
        assert sorted(assigned) == list(range(64)) and len(set(assigned)) == 64
        assert sum(len(assigned_indices(shard, count)) * 19 for shard in range(count)) == 1216
        assert all(set(condition_order('target', i)) == set(TARGET_CONDITIONS) for i in assigned)
    with tempfile.TemporaryDirectory() as temporary:
        directory, data, count = Path(temporary), ROOT / 'data', 6
        frozen = {'behavior': rows(data / 'confirm.jsonl'), 'ability': rows(data / 'ability_diag.jsonl')}
        model_hash = {'13': 'synthetic-a', '14': 'synthetic-b'}
        for shard in range(count):
            root, indices = directory / f'shard{shard}', assigned_indices(shard, count)
            for split, items in frozen.items():
                for index in indices:
                    context = 'synthetic-context'
                    cal = {'item_id': items[index]['id'], 'context_sha256': digest_text(context),
                           'input_token_sha256': digest_text('[1]')}
                    write(root / 'calibrations' / f'{split}-{index:03d}.json', cal)
                    for condition in TARGET_CONDITIONS:
                        record = {'status': 'completed', 'item': items[index], 'condition': condition,
                                  'context': context, 'calibration': cal}
                        if split == 'behavior':
                            record['output'] = {'token_ids': [10, 248046], 'generated_token_count': 2,
                                'max_new_tokens': 512, 'end_reason': 'eos_token', 'raw_text': 'synthetic',
                                'answer_text': 'synthetic', 'input_token_sha256': cal['input_token_sha256']}
                            record['output_integrity'] = validate_generation(record['output'])
                        else:
                            details = [{'loglikelihood': -1.0} for _ in items[index]['continuations']]
                            record['output'] = {'choice_details': details, 'choice_loglikelihoods': [-1.0] * len(details)}
                        path = root / 'records' / split / f'{index:03d}-{condition}.jsonl'
                        path.parent.mkdir(parents=True, exist_ok=True)
                        dump_rows(path, [record])
            write(root / 'receipt.json', {'status': 'completed', 'kind': 'target', 'shard_index': shard,
                'shard_count': count, 'actual_worker_count': count,
                'cuda_visible_devices': str(shard % 2),
                'worker_topology': {'processes_per_gpu': count // 2,
                    'gpu_slot_by_worker': {str(i): i % 2 for i in range(count)},
                    'independent_model_processes': True, 'actual_forward_batch_size': 1,
                    'assignment': 'item_index modulo shard_count'},
                'completed_behavior': len(indices) * 19, 'expected_behavior': len(indices) * 19,
                'completed_diagnostic': len(indices) * 19, 'expected_diagnostic': len(indices) * 19,
                'completed_calibrations': len(indices) * 2, 'expected_calibrations': len(indices) * 2,
                'hooks_removed': True, 'target_weight_sha256_after': model_hash,
                'engine': {'target_weight_sha256_before': model_hash, 'batch_size': 1,
                    'dtype': 'bfloat16', 'attention_backend': 'eager', 'model_path': 'synthetic'},
                'source_sha256': {name: sha(ROOT / name) for name in
                    ('run_toy_parallel.py', 'run_toy.py', 'transfer_engine.py', 'run_io.py')},
                'original_freeze_sha256': sha(ROOT / 'freeze.json'), 'conditions_sha256': 'synthetic',
                'data_sha256': {name: sha(data / f'{name}.jsonl') for name in ('confirm', 'ability_diag')},
                'records_sha256': {str(p.relative_to(root)): sha(p) for p in (root / 'records').rglob('*.jsonl')},
                'calibrations_sha256': {str(p.relative_to(root)): sha(p) for p in (root / 'calibrations').glob('*.json')}})
        verified = verified_target(directory, data, {}, count)
        assert len(verified['behavior']) == len(verified['ability']) == 1216
        path = directory / 'shard0/records/behavior/000-T_0.jsonl'
        original = path.read_bytes()
        path.unlink()
        try:
            verified_target(directory, data, {}, count)
        except AssertionError:
            pass
        else:
            raise AssertionError('Missing record passed export')
        path.write_bytes(original + b' ')
        try:
            verified_target(directory, data, {}, count)
        except AssertionError:
            pass
        else:
            raise AssertionError('Changed record hash passed export')
    print('PASS: 2/4/6 disjoint partitions, complete six-worker export, missing/corrupt record rejection')


def run(args):
    started = time.monotonic()
    destination = args.run / args.target / 'export-r01'
    destination.mkdir(parents=True, exist_ok=False)
    receipt_path = destination / 'receipt.json'
    receipt = {'status': 'running', 'started_utc': utc(), 'target': args.target,
               'toy_shards': args.toy_shards, 'benchmark_shards': args.benchmark_shards,
               'original_freeze_sha256': sha(ROOT / 'freeze.json'),
               'source_sha256': {name: sha(ROOT / name) for name in
                   ('export_results_parallel.py', 'export_results.py', 'run_toy_parallel.py', 'RATING_MANUAL.zh-CN.md')},
               'behavior_ratings': 'not_started', 'behavior_semantic_analysis_performed': False}
    write(receipt_path, receipt)
    inputs = {}
    try:
        for name in ('confirm', 'ability_diag'):
            inputs[str(args.data / (name + '.jsonl'))] = sha(args.data / (name + '.jsonl'))
        source = verified_toy(args.run / 'source', 'source', args.data, inputs)
        target = verified_target(args.run / args.target / 'toy', args.data, inputs, args.toy_shards)
        assert len(source['behavior']) == 192 and not source['ability']
        assert len(target['behavior']) == len(target['ability']) == 1216
        benchmark = verify_benchmark(args.run / args.target / 'benchmark', inputs, args.benchmark_shards)
        toy_identity = read(args.run / args.target / 'toy/shard0/receipt.json')
        benchmark_identity = read(args.run / args.target / 'benchmark/shard-0/receipt.json')
        assert toy_identity['conditions_sha256'] == benchmark['conditions_sha256'] == benchmark_identity['conditions_sha256']
        assert toy_identity['engine'] == benchmark_identity['engine']
        for split, name in [('behavior', 'confirm'), ('ability', 'ability_diag')]:
            frozen_items = rows(args.data / f'{name}.jsonl')
            calibration_by_id = {}
            for index, item in enumerate(frozen_items):
                path = args.run / 'source' / f'shard{index % 2}' / 'calibrations' / f'{split}-{index:03d}.json'
                calibration_by_id[item['id']] = (read(path), inputs[str(path)])
            for row in target[split]:
                original, digest = calibration_by_id[row['item']['id']]
                assert row['calibration']['source_calibration_file_sha256'] == digest
                assert row['calibration']['source_residual_scales'] == original['residual_scales']
                assert row['calibration']['source_calibration_context_sha256'] == original['context_sha256']
        dump_rows(destination / 'source.raw.jsonl', source['behavior'])
        dump_rows(destination / 'original.raw.jsonl', [row for row in target['behavior'] if row['condition'] == 'T_0'])
        dump_rows(destination / 'modified.raw.jsonl', [row for row in target['behavior'] if row['condition'] != 'T_0'])
        dump_rows(destination / 'diagnostic.raw.jsonl', target['ability'])
        behavior = source['behavior'] + target['behavior']
        (destination / 'paired_raw.html').write_text(paired_html(source['behavior'], target['behavior'], rows(args.data / 'confirm.jsonl')))
        private = []
        for reviewer, seed in (('A', 20261026), ('B', 20261027)):
            packet, keys = blind_pack(behavior, reviewer, args.target, seed)
            directory = destination / f'blind_{reviewer}'
            directory.mkdir()
            dump_rows(directory / 'ratings.blank.jsonl', packet)
            shutil.copyfile(ROOT / 'RATING_MANUAL.zh-CN.md', directory / 'RATING_MANUAL.zh-CN.md')
            private.extend(keys)
        dump_rows(destination / 'rating_keys.private.jsonl', private)
        scored, diagnostic = diagnostic_scores(target['ability'], args.project)
        dump_rows(destination / 'diagnostic.scores.jsonl', scored)
        write(destination / 'diagnostic.summary.json', diagnostic)
        write(destination / 'benchmark.summary.json', benchmark)
        for path, digest in inputs.items():
            assert sha(path) == digest, f'Input changed during export: {path}'
        receipt.update(status='machine_completed_blind_review_pending', counts={
            'questions': 64, 'source_behavior_records': 192, 'target_behavior_records': 1216,
            'target_original_records': 64, 'target_modified_records': 1152,
            'target_diagnostic_records': 1216, 'benchmark_pairs': 1400,
            'blind_records_per_reviewer': 1408, 'independent_reviewers': 2},
            input_sha256=inputs, behavior_ratings='blank_independent_forms_exported',
            claims='Machine inference, integrity, raw export, diagnostic scoring and official capability benchmark complete; behavioral transfer remains unjudged.')
    except Exception as error:
        receipt.update(status='failed', error=str(error), traceback=traceback.format_exc())
        raise
    finally:
        receipt.update(ended_utc=utc(), elapsed_seconds=time.monotonic() - started,
            artifacts_sha256={str(p.relative_to(destination)): sha(p) for p in sorted(destination.rglob('*'))
                              if p.is_file() and p != receipt_path})
        write(receipt_path, receipt)
        print(json.dumps({'status': receipt['status'], 'target': args.target, 'receipt': str(receipt_path)}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--target', choices=['target9b', 'target2b'], required=True)
    parser.add_argument('--data', type=Path, default=ROOT / 'data')
    parser.add_argument('--project', type=Path, default=ROOT.parents[1])
    parser.add_argument('--toy-shards', type=int, choices=[2, 4, 6], required=True)
    parser.add_argument('--benchmark-shards', type=int, choices=[2, 4, 6])
    args = parser.parse_args()
    args.benchmark_shards = args.benchmark_shards or args.toy_shards
    run(args)
