"""CPU integration checks of real parallel dispatch and completeness rejection."""
import ast
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import run_benchmark as old_benchmark
import run_benchmark_parallel as benchmark
import run_toy as old_toy
import run_toy_parallel as toy
import run_queue_parallel as queue
import transfer_engine
from export_results_parallel import verified_target
from finish_benchmark_parallel import verified_records
from run_io import read, rows, sha, write

ROOT = Path(__file__).resolve().parent


class FakeTokenizer:
    def apply_chat_template(self, messages, **kwargs):
        assert kwargs == dict(tokenize=False, add_generation_prompt=True, enable_thinking=False)
        return 'synthetic chat: ' + messages[0]['content']


class FakeEngine:
    def __init__(self, model_path, device='cuda:0', batch_size=1, bundle=None):
        assert batch_size == 1 and device == 'cuda:0'
        self.batch_size, self.stop_ids = 1, [248044, 248046]
        self.tokenizer = FakeTokenizer()
        self.metadata = {'batch_size': 1, 'dtype': 'bfloat16', 'attention_backend': 'eager',
                         'model_path': str(model_path), 'target_weight_sha256_before': {'13': 'a', '14': 'b'}}

    def calibrate(self, contexts):
        return [{'context_sha256': transfer_engine.text_hash(text),
                 'input_token_sha256': transfer_engine.token_hash(list(text.encode())),
                 'input_token_count': len(text.encode()), 'residual_scales': {'13': 3., '14': 4.}}
                for text in contexts]

    def score(self, contexts, continuations, arm, calibrations):
        assert len(contexts) == len(continuations) == len(calibrations)
        return [{'loglikelihood': -float(i + 1), 'continuation_token_ids': [i],
                 'context_token_count': len(context.encode()),
                 'input_token_sha256': transfer_engine.token_hash(list(context.encode()))}
                for i, context in enumerate(contexts)]

    def generate(self, contexts, arm, calibrations, max_new_tokens, stops):
        assert len(contexts) == len(calibrations) == 1
        return [{'token_ids': [10, 248046], 'generated_token_count': 2,
                 'max_new_tokens': max_new_tokens, 'end_reason': 'eos_token',
                 'raw_text': 'synthetic', 'answer_text': 'synthetic',
                 'input_token_sha256': calibrations[0]['input_token_sha256']}]

    def verify_unchanged(self):
        return {'hooks_removed': True, 'target_weight_sha256_after': self.metadata['target_weight_sha256_before']}


def ast_node(path, name):
    tree = ast.parse(path.read_text())
    return ast.dump(next(node for node in tree.body if getattr(node, 'name', None) == name), include_attributes=False)


class ParallelExecutionTests(unittest.TestCase):
    def test_queue_adopts_source_and_keeps_target_pipeline_in_order(self):
        for count in (4, 6):
            with TemporaryDirectory() as temporary:
                base = Path(temporary)
                root, run = base/'code', base/'run'
                root.mkdir(); run.mkdir()
                write(root/'freeze.json', {'files': {}})
                write(root/'freeze_parallel.json', {'files': {}})
                probe_script = root/'optimization-check-r01/runtime_worker.py'
                probe_script.parent.mkdir()
                probe_script.write_text('synthetic probe')
                completed = ('collection-source4b', 'collection-target9b', 'bridge',
                             'target9b/mapping', 'decode-source4b', 'decode-target9b')
                for name in completed:
                    write(run/name/'receipt.json', {'status': 'completed'})
                bundle = run/'target9b/mapping/bundle.pt'
                bundle.write_text('synthetic bundle')
                for shard in (0, 1):
                    write(run/f'source/shard{shard}/receipt.json', {'status': 'running'})
                workers = []
                for index in range(count//2):
                    output = base/f'validation/worker{index}'
                    write(output/'receipt.json', {'status': 'completed', 'hooks_removed': True,
                        'generated_tokens': 8, 'cases': [{'seconds': 1.}], 'probe_sha256': sha(probe_script),
                        'freeze_sha256': sha(root/'freeze.json'), 'bundle_sha256': sha(bundle),
                        'engine': {'model_path': queue.MODELS['target9b']}})
                    workers.append({'output': str(output)})
                validation = base/'validation/receipt.json'
                write(validation, {'status': 'completed', 'all_cross_process_outputs_exact': True,
                    'worker_count': count//2, 'workers': workers})
                launches = []

                def finish_source(_seconds):
                    for shard in (0, 1):
                        write(run/f'source/shard{shard}/receipt.json', {'status': 'completed'})

                def fake_popen(command, **kwargs):
                    self.assertTrue(all(queue.complete(run/f'source/shard{i}/receipt.json') for i in (0, 1)))
                    script = Path(command[1]).name
                    options = dict(zip(command[2::2], command[3::2]))
                    launches.append((script, options, kwargs['env'].get('CUDA_VISIBLE_DEVICES')))
                    if script == 'export_results_parallel.py':
                        output = Path(options['--run'])/options['--target']/'export-r01'
                    else:
                        output = Path(options['--output'])
                        if script == 'run_toy_parallel.py':
                            output /= 'shard'+options['--shard-index']
                        elif script == 'run_benchmark_parallel.py':
                            output /= 'shard-'+options['--shard-index']
                        elif script == 'finish_benchmark_parallel.py':
                            output /= 'finish-r01'
                    write(output/'receipt.json', {'status': 'completed', 'all_cross_process_outputs_exact': True})
                    return SimpleNamespace(pid=100+len(launches), returncode=0, poll=lambda: 0)

                with patch.object(queue, 'ROOT', root), patch.object(queue.subprocess, 'Popen', fake_popen), \
                     patch.object(queue.time, 'sleep', finish_source):
                    queue.run(SimpleNamespace(run=str(run), workers=count, validation=str(validation), resume=False))
                self.assertEqual(read(run/'queue_receipt.json')['status'], 'machine_completed_blind_review_pending')
                self.assertFalse(any(script in ('run_toy.py', 'run_decode_check.py') and
                                     options.get('--model') == queue.MODELS['source4b'] for script, options, _ in launches))
                for target in ('target9b', 'target2b'):
                    for script in ('run_toy_parallel.py', 'run_benchmark_parallel.py'):
                        selected = [(options, gpu) for name, options, gpu in launches
                                    if name == script and options['--model'] == queue.MODELS[target]]
                        self.assertEqual(len(selected), count)
                        self.assertEqual([int(options['--shard-index']) for options, _ in selected], list(range(count)))
                        self.assertTrue(all(options['--shard-count'] == str(count) and gpu == str(i % 2)
                                            for i, (options, gpu) in enumerate(selected)))
                for script, options, _ in launches:
                    if script == 'finish_benchmark_parallel.py':
                        self.assertEqual(options['--shard-count'], str(count))
                    if script == 'export_results_parallel.py':
                        self.assertEqual(options['--toy-shards'], str(count))
                        self.assertEqual(options['--benchmark-shards'], str(count))
                names = [name for name, _, _ in launches]
                self.assertEqual(names.count('finish_benchmark_parallel.py'), 2)
                self.assertEqual(names.count('export_results_parallel.py'), 2)
                first_export = names.index('export_results_parallel.py')
                self.assertLess(first_export, names.index('run_preflight.py'))
                self.assertLess(names.index('runtime_concurrency_target.py'),
                                next(i for i, (name, options, _) in enumerate(launches)
                                     if name == 'run_toy_parallel.py' and options['--model'] == queue.MODELS['target2b']))

    def test_partitions_and_frozen_scientific_helpers(self):
        self.assertIs(toy.condition_order, old_toy.condition_order)
        self.assertIs(toy.prompt, old_toy.prompt)
        self.assertIs(toy.calibration_path, old_toy.calibration_path)
        self.assertEqual(benchmark.ARM_NAMES, old_benchmark.ARM_NAMES)
        for helper in ('BenchmarkEngine', 'frozen_panel', 'load_v3', 'validate_pair'):
            self.assertEqual(ast_node(ROOT/'run_benchmark.py', helper), ast_node(ROOT/'run_benchmark_parallel.py', helper))
        for helper in ('sandbox_command', 'score_records'):
            self.assertEqual(ast_node(ROOT/'finish_benchmark.py', helper), ast_node(ROOT/'finish_benchmark_parallel.py', helper))
        frozen = read(ROOT/'freeze.json')
        self.assertTrue(all(sha(ROOT/name) == digest for name, digest in frozen['files'].items()))
        for count in (2, 4, 6):
            assignments = [index for shard in range(count) for index in toy.assigned_indices(shard, count)]
            self.assertEqual(sorted(assignments), list(range(64)))
            self.assertTrue(all(index % 2 == shard % 2 for shard in range(count)
                                for index in toy.assigned_indices(shard, count)))
            for total in benchmark.COUNTS.values():
                assignments = [index for shard in range(count) for index in benchmark.assigned_indices(total, shard, count)]
                self.assertEqual(sorted(assignments), list(range(total)))
                self.assertTrue(all(index % 2 == shard % 2 for shard in range(count)
                                    for index in benchmark.assigned_indices(total, shard, count)))

    def test_actual_toy_dispatch_export_and_rejection(self):
        data = ROOT/'data'
        with TemporaryDirectory() as temporary, patch.object(toy, 'TransferEngine', FakeEngine), redirect_stdout(io.StringIO()):
            base = Path(temporary)
            bundle = base/'bundle.pt'
            bundle.write_text('synthetic bundle')
            source = base/'source'
            hashes = {name: sha(data/f'{name}.jsonl') for name in ('confirm', 'ability_diag')}
            for shard in (0, 1):
                write(source/f'shard{shard}/receipt.json', {'status': 'completed', 'data_sha256': hashes})
            for split, name in (('behavior', 'confirm'), ('ability', 'ability_diag')):
                for index, item in enumerate(rows(data/f'{name}.jsonl')):
                    write(old_toy.calibration_path(source, split, index), {'item_id': item['id'],
                        'context_sha256': f'source-{split}-{index}', 'residual_scales': {'13': 100. + index, '14': 200. + index}})
            for count in (2, 4, 6):
                output = base/f'toy-{count}'
                for shard in range(count):
                    args = SimpleNamespace(kind='target', model='synthetic', data=str(data), output=str(output),
                        conditions=str(bundle), source_output=str(source), shard_index=shard, shard_count=count)
                    with patch.dict(os.environ, CUDA_VISIBLE_DEVICES=str(shard % 2)):
                        toy.run(args)
                result = verified_target(output, data, {}, count)
                for split in ('behavior', 'ability'):
                    self.assertEqual(len(result[split]), 1216)
                    self.assertEqual(len({(row['item']['id'], row['condition']) for row in result[split]}), 1216)
                    for row in result[split]:
                        index = int(Path(row['source_file']).name.split('-')[0])
                        source_path = old_toy.calibration_path(source, split, index)
                        self.assertEqual(row['calibration']['source_calibration_file_sha256'], sha(source_path))
                        self.assertEqual(row['calibration']['source_residual_scales'], {'13': 100. + index, '14': 200. + index})
                path = output/'shard0/records/behavior/000-T_0.jsonl'
                original = path.read_bytes()
                path.unlink()
                with self.assertRaises(AssertionError):
                    verified_target(output, data, {}, count)
                path.write_bytes(original)
                extra = path.with_name('duplicate.jsonl')
                extra.write_bytes(original)
                with self.assertRaises(AssertionError):
                    verified_target(output, data, {}, count)

    def test_actual_benchmark_dispatch_and_incomplete_or_reordered_rejection(self):
        _, _, items = benchmark.frozen_panel()
        with TemporaryDirectory() as temporary, patch.object(transfer_engine, 'TransferEngine', FakeEngine), redirect_stdout(io.StringIO()):
            base = Path(temporary)
            model = base/'model'
            model.mkdir()
            (model/'config.json').write_text('{}')
            bundle = base/'bundle.pt'
            bundle.write_text('synthetic bundle')
            for count in (2, 4, 6):
                output = base/f'benchmark-{count}'
                for shard in range(count):
                    with patch.dict(os.environ, CUDA_VISIBLE_DEVICES=str(shard % 2)):
                        benchmark.run(SimpleNamespace(model=model, conditions=bundle, output=output,
                                                      shard_index=shard, shard_count=count))
                result, paths, receipts = verified_records(output, items, count)
                self.assertEqual(len(result), 1400)
                self.assertEqual([row['id'] for row in result],
                    [item['id'] for shard in (0, 1) for task in benchmark.COUNTS for item in items[task][shard::2]])
                self.assertEqual(sum(row['completed_pairs'] for row in receipts), 1400)
                path = paths[0]
                original = path.read_bytes()
                path.unlink()
                with self.assertRaises(AssertionError):
                    verified_records(output, items, count)
                path.write_bytes(original)
                row = json.loads(original)
                row['arm_order'].reverse()
                path.write_text(json.dumps(row)+'\n')
                receipt_path = path.parent.parent/'receipt.json'
                receipt = read(receipt_path)
                receipt['records_sha256'][str(path.relative_to(receipt_path.parent))] = sha(path)
                write(receipt_path, receipt)
                with self.assertRaises(AssertionError):
                    verified_records(output, items, count)


if __name__ == '__main__':
    unittest.main()
