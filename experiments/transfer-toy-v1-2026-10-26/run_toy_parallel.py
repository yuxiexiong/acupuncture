"""Versioned target-only dispatch across independent batch-one model processes."""
import argparse
import os
from pathlib import Path
import time
import traceback

from run_io import read, rows, write, immutable, sha, utc
from run_toy import condition_order, prompt, calibration_path
from transfer_engine import TransferEngine, text_hash, token_hash

ROOT = Path(__file__).resolve().parent


def assigned_indices(shard_index, shard_count):
    assert shard_count in (2, 4, 6) and 0 <= shard_index < shard_count
    return range(shard_index, 64, shard_count)


def run(args):
    indices = assigned_indices(args.shard_index, args.shard_count)
    assert args.kind == 'target' and args.source_output and args.conditions
    out = Path(args.output) / f'shard{args.shard_index}'
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    frozen = read(ROOT / 'freeze.json')
    execution_files = {name: sha(ROOT / name) for name in
                       ('run_toy_parallel.py', 'run_toy.py', 'transfer_engine.py', 'run_io.py')}
    rec = {'status': 'running', 'started_utc': utc(), 'kind': 'target', 'arguments': vars(args),
           'pid': os.getpid(), 'shard_index': args.shard_index, 'shard_count': args.shard_count,
           'actual_worker_count': args.shard_count,
           'worker_topology': {'processes_per_gpu': args.shard_count // 2,
               'gpu_slot_by_worker': {str(i): i % 2 for i in range(args.shard_count)},
               'independent_model_processes': True, 'actual_forward_batch_size': 1,
               'assignment': 'item_index modulo shard_count'},
           'cuda_visible_devices': os.environ.get('CUDA_VISIBLE_DEVICES'),
           'completed_behavior': 0, 'completed_diagnostic': 0, 'completed_calibrations': 0,
           'expected_behavior': len(indices) * 19, 'expected_diagnostic': len(indices) * 19,
           'expected_calibrations': len(indices) * 2,
           'source_sha256': execution_files, 'original_freeze_sha256': sha(ROOT / 'freeze.json'),
           'conditions_sha256': sha(args.conditions),
           'data_sha256': {name: sha(Path(args.data) / f'{name}.jsonl') for name in ('confirm', 'ability_diag')}}
    write(out / 'receipt.json', rec)
    try:
        assert rec['cuda_visible_devices'] == str(args.shard_index % 2), 'Worker assigned to wrong declared GPU slot'
        for name, digest in frozen['files'].items():
            assert sha(ROOT / name) == digest, f'Frozen input changed: {name}'
        for shard in (0, 1):
            prior = read(Path(args.source_output) / f'shard{shard}' / 'receipt.json')
            assert prior['status'] == 'completed'
            assert prior['data_sha256'] == rec['data_sha256']
        engine = TransferEngine(args.model, bundle=args.conditions)
        rec['engine'] = engine.metadata
        for split, items in [('behavior', rows(Path(args.data) / 'confirm.jsonl')),
                             ('ability', rows(Path(args.data) / 'ability_diag.jsonl'))]:
            assert len(items) == 64
            for index in indices:
                item = items[index]
                context = prompt(engine, item) if split == 'behavior' else item['context']
                scale_start = time.monotonic()
                cal = engine.calibrate([context])[0]
                cal['item_id'] = item['id']
                cal['calibration_seconds'] = time.monotonic() - scale_start
                source_path = calibration_path(args.source_output, split, index)
                source = read(source_path)
                assert source['item_id'] == item['id']
                cal['source_residual_scales'] = source['residual_scales']
                cal['source_calibration_context_sha256'] = source['context_sha256']
                cal['source_calibration_file_sha256'] = sha(source_path)
                write(out / 'calibrations' / f'{split}-{index:03d}.json', cal)
                rec['completed_calibrations'] += 1
                for condition in condition_order('target', index):
                    begin = time.monotonic()
                    rec.update(current_split=split, current_item=item['id'], current_condition=condition,
                               elapsed_seconds=begin - started)
                    write(out / 'receipt.json', rec)
                    if split == 'behavior':
                        result = engine.generate([context], condition, [cal], 512, [])[0]
                    else:
                        details = engine.score([context] * len(item['continuations']), item['continuations'],
                                               condition, [cal] * len(item['continuations']))
                        result = {'choice_loglikelihoods': [d['loglikelihood'] for d in details],
                                  'choice_details': details}
                    record = {'status': 'completed', 'item': item, 'condition': condition, 'context': context,
                              'prompt_format': 'native_chat_thinking_false' if split == 'behavior' else 'frozen_benchmark_raw',
                              'calibration': cal, 'output': result, 'ended_utc': utc(),
                              'elapsed_seconds': time.monotonic() - begin}
                    if split == 'behavior':
                        record['output_integrity'] = {'generated_token_sha256': token_hash(result['token_ids']),
                                                      'raw_text_sha256': text_hash(result['raw_text'])}
                    target = out / 'records' / split / f'{index:03d}-{condition}.jsonl'
                    immutable(target, record)
                    key = 'completed_behavior' if split == 'behavior' else 'completed_diagnostic'
                    rec[key] += 1
                    rec.setdefault('condition_seconds', {}).setdefault(split, {}).setdefault(condition, []).append(record['elapsed_seconds'])
                    rec['elapsed_seconds'] = time.monotonic() - started
                    write(out / 'receipt.json', rec)
                    print({'split': split, 'item': item['id'], 'condition': condition, 'completed': rec[key],
                           'seconds': record['elapsed_seconds'], 'tokens': result.get('generated_token_count')}, flush=True)
        assert rec['completed_behavior'] == rec['expected_behavior']
        assert rec['completed_diagnostic'] == rec['expected_diagnostic']
        assert rec['completed_calibrations'] == rec['expected_calibrations']
        rec.update(engine.verify_unchanged())
        for name, digest in execution_files.items():
            assert sha(ROOT / name) == digest, f'Execution source changed: {name}'
        assert sha(ROOT / 'freeze.json') == rec['original_freeze_sha256']
        assert sha(args.conditions) == rec['conditions_sha256']
        rec.update(status='completed',
            records_sha256={str(p.relative_to(out)): sha(p) for p in sorted((out / 'records').rglob('*.jsonl'))},
            calibrations_sha256={str(p.relative_to(out)): sha(p) for p in sorted((out / 'calibrations').glob('*.json'))})
    except Exception as exc:
        rec.update(status='failed', error=str(exc), traceback=traceback.format_exc())
        raise
    finally:
        rec.update(ended_utc=utc(), elapsed_seconds=time.monotonic() - started)
        write(out / 'receipt.json', rec)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model', required=True)
    p.add_argument('--kind', choices=['target'], default='target')
    p.add_argument('--data', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--conditions', required=True)
    p.add_argument('--source-output', required=True)
    p.add_argument('--shard-index', type=int, required=True)
    p.add_argument('--shard-count', type=int, choices=[2, 4, 6], required=True)
    run(p.parse_args())
