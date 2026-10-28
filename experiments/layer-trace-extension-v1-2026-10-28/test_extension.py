"""CPU checks for incremental coverage and successor-queue gates; no model runs."""
from collections import Counter, defaultdict
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

import supplement as run


class SourceChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = run.build_inventory()
        cls.added = [item for item in cls.rows if item['stage']]
        original = Path(__file__).resolve().parent.parent / 'early-layer-mechanism-v1-2026-10-28/sources.jsonl'
        with original.open() as stream:
            cls.original = [json.loads(line) for line in stream]

    def test_additions_are_exact_disjoint_and_complete(self):
        self.assertEqual(Counter(item['stage'] for item in self.added), {'six-layer': 608, '4b-full': 3952})
        added_ids = {item['trace_id'] for item in self.added}
        original_ids = {item['trace_id'] for item in self.original}
        self.assertEqual(len(self.added), len(added_ids))
        self.assertEqual(len(added_ids), 4560)
        self.assertFalse(added_ids & original_ids)
        self.assertEqual(len(added_ids | original_ids), 6712)
        self.assertEqual(Counter(item['model'] for item in self.original + self.added),
                         {'2b': 920, '4b': 4872, '9b': 920})
        for item in self.added:
            row = item['record']
            self.assertEqual(row['model_id'], item['model'])
            self.assertIn(item['shard'], (0, 1))
            self.assertIn(item['historical_shard'], (0, 1))
            self.assertTrue(item['references'])
            self.assertTrue(item['provenance']['record_sha256'])
            if item['stage'] == 'six-layer':
                self.assertIn(item['model'], ('2b', '4b'))
                self.assertIn(row['layer'], (4, 5))
            else:
                self.assertEqual(item['model'], '4b')
                self.assertIn(row['layer'], range(6, 32))

    def test_each_layer_keeps_original_nineteen_conditions_and_eight_questions(self):
        layers, conditions = defaultdict(list), defaultdict(list)
        for item in self.added:
            row = item['record']
            dose = row.get('dose', (row.get('intervention') or {}).get('dose'))
            layers[(item['model'], row['layer'])].append(row)
            conditions[(item['model'], row['layer'], row['channel'], dose)].append(item)
        self.assertEqual(len(layers), 30)
        for key, rows in layers.items():
            self.assertEqual(len(rows), 152)
            self.assertEqual(len({row['channel'] for row in rows}), 10)
            self.assertEqual(sum(row.get('dose', (row.get('intervention') or {}).get('dose')) == 1 for row in rows), 80)
            self.assertEqual(sum(condition[:2] == key for condition in conditions), 19)
        for items in conditions.values():
            self.assertEqual(sorted(item['record']['question_id'] for item in items), [f'Q{i:02}' for i in range(1, 9)])
            self.assertEqual(len({item['shard'] for item in items}), 1)

    def test_baselines_are_calibration_only_and_shards_partition_new_work(self):
        baselines = [item for item in self.rows if not item['stage']]
        self.assertEqual(Counter(item['model'] for item in baselines), {'2b': 8, '4b': 8})
        self.assertTrue(all(item['record']['layer'] is None and item['shard'] == -1 for item in baselines))
        self.assertEqual(Counter((item['stage'], item['model'], item['shard']) for item in self.added),
                         {('six-layer', '4b', 0): 152, ('six-layer', '4b', 1): 152,
                          ('six-layer', '2b', 0): 152, ('six-layer', '2b', 1): 152,
                          ('4b-full', '4b', 0): 1976, ('4b-full', '4b', 1): 1976})


class GateChecks(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.output = self.root / 'new-run'
        self.authorization = self.root / 'authorization.json'
        self.authorization.write_text('{}')
        self.auth = {'remote_output': str(self.output), 'freeze_sha256': 'extension-frozen'}

    def predecessor(self, status='completed'):
        path = self.root / 'old-run'
        path.mkdir()
        run.write(path / 'execution.json', {'immutable': True})
        run.write(path / 'preflight-accepted.json', {'status': 'passed'})
        workers = {}
        for model in ('4b', '2b', '9b'):
            for shard in (0, 1):
                key = f'{model}-shard-{shard}'
                run.write(path / 'survey' / key / 'receipt.json', {'status': 'completed'})
                (path / 'survey' / f'{key}.exit').write_text('0\n')
                workers[key] = {'status': 'completed', 'exit_code': 0,
                                'receipt_sha256': run.sha(path / 'survey' / key / 'receipt.json')}
        state = {'status': status, 'freeze_sha256': 'source-frozen', 'pid': 10,
                 'completed_records': 2152, 'expected_records': 2152, 'stages': {'survey': workers}}
        run.write(path / 'queue-state.json', state)
        auth = {'predecessor': {'run': str(path), 'execution_sha256': run.sha(path / 'execution.json'),
                'freeze_sha256': 'source-frozen', 'preflight_accepted_sha256': run.sha(path / 'preflight-accepted.json'),
                'process': {'pid': 10, 'start_ticks': 100}}}
        return auth, state

    def test_predecessor_must_finish_successfully_and_exit(self):
        auth, state = self.predecessor('running_survey')
        self.assertEqual(run.predecessor_ready(auth), (False, 'predecessor_running'))
        path = Path(auth['predecessor']['run'])
        with patch.object(run.queue_utils, 'process_alive', return_value=True):
            state['status'] = 'completed';run.write(path / 'queue-state.json', state)
            self.assertEqual(run.predecessor_ready(auth), (False, 'predecessor_exiting'))
        with patch.object(run.queue_utils, 'process_alive', return_value=False):
            self.assertTrue(run.predecessor_ready(auth)[0])
            state['stages']['survey']['4b-shard-0']['exit_code'] = 1
            run.write(path / 'queue-state.json', state)
            with self.assertRaises(AssertionError):
                run.predecessor_ready(auth)
            state['status'] = 'failed';run.write(path / 'queue-state.json', state)
            with self.assertRaisesRegex(AssertionError, 'failed or stopped'):
                run.predecessor_ready(auth)

    def test_reused_gpu_preflight_and_all_old_results_are_verified(self):
        auth, state = self.predecessor()
        path = Path(auth['predecessor']['run'])
        with patch.object(run.queue_utils, 'process_alive', return_value=False), \
             patch.object(run.original, 'require_preflight_acceptance') as gpu_check, \
             patch.object(run.original, 'verify_worker') as record_check:
            accepted = run.verify_predecessor(auth)
            self.assertEqual(accepted['reused_records'], 2152)
            gpu_check.assert_called_once_with(path / 'survey' / 'unused', {'freeze_sha256': 'source-frozen'})
            self.assertEqual(record_check.call_count, 6)
            self.assertEqual({tuple(call.args[1:]) for call in record_check.call_args_list},
                             {('survey', m, s) for m in ('4b', '2b', '9b') for s in (0, 1)})
            run.write(path / 'preflight-accepted.json', {'status': 'changed'})
            with self.assertRaises(AssertionError):
                run.verify_predecessor(auth)

    def test_gpu_must_be_empty_and_authorization_must_stay_frozen(self):
        self.output.mkdir()
        state = {}
        with patch.object(run, 'validate_authorization', return_value=self.auth), \
             patch.object(run, 'predecessor_ready', return_value=(True, 'predecessor_completed')), \
             patch.object(run.queue_utils, 'gpu_processes', side_effect=[['external GPU job'], []]), \
             patch.object(run.time, 'sleep') as sleep:
            run.wait_ready(self.authorization, run.sha(self.authorization), self.output, state)
            sleep.assert_called_once_with(10)
            self.assertEqual(state['gpu_compute_processes'], [])
            with self.assertRaisesRegex(AssertionError, 'Authorization changed'):
                run.wait_ready(self.authorization, 'wrong', self.output, state)

    def test_authorization_rejects_scope_changes_and_failed_cpu_receipt(self):
        base = self.root / 'base';base.mkdir();(base / 'freeze.json').write_text('source freeze')
        cpu = {'status': 'passed', 'failures': 0, 'errors': 0, 'skipped': 0, 'freeze_sha256': 'extension-frozen'}
        run.write(self.root / 'cpu.json', cpu)
        auth = dict(self.auth, status='authorized', purpose='trace_extension_queue', experiment=self.root.name,
                    user_instruction='Append only missing records after current queue.', maximum_records=4560,
                    maximum_generation_streams=9120, stages=[{'id': s, 'models': list(ms)} for s, ms in run.STAGES],
                    predecessor={'freeze_sha256': run.sha(base / 'freeze.json')},
                    cpu_test_receipt={'path': 'cpu.json', 'sha256': run.sha(self.root / 'cpu.json')})
        run.write(self.authorization, auth)
        with patch.object(run, 'ROOT', self.root), patch.object(run, 'BASE', base), \
             patch.object(run, 'validate_freeze', return_value='extension-frozen'):
            self.assertEqual(run.validate_authorization(self.authorization), auth)
            for field, bad in [('maximum_records', 4561), ('maximum_generation_streams', 9121),
                               ('stages', list(reversed(auth['stages']))), ('freeze_sha256', 'changed')]:
                run.write(self.authorization, dict(auth, **{field: bad}))
                with self.assertRaises(AssertionError):
                    run.validate_authorization(self.authorization)
            for field in ('failures', 'errors', 'skipped'):
                run.write(self.root / 'cpu.json', dict(cpu, **{field: 1}))
                auth['cpu_test_receipt']['sha256'] = run.sha(self.root / 'cpu.json')
                run.write(self.authorization, auth)
                with self.assertRaises(AssertionError):
                    run.validate_authorization(self.authorization)

    def fake_pair(self, stage, model, authorization, digest, output, state):
        state['stages'].setdefault(stage, {})
        for shard in (0, 1):
            key = f'{model}-shard-{shard}'
            state['stages'][stage][key] = {'status': 'completed', 'exit_code': 0}
            count = 152 if stage == 'six-layer' else 1976
            run.write(output / stage / 'survey' / key / 'receipt.json',
                      {'status': 'completed', 'completed_records': count, 'expected_records': count})

    def test_stage_order_and_existing_output_rejection(self):
        args = types.SimpleNamespace(authorization=self.authorization, output=self.output, execute=True)
        with patch.object(run, 'ROOT', self.root), \
             patch.object(run, 'validate_authorization', return_value=self.auth), \
             patch.object(run, 'wait_ready'), patch.object(run, 'verify_predecessor', return_value={'status': 'passed'}), \
             patch.object(run, 'run_pair', side_effect=self.fake_pair) as pair:
            state = run.main_queue(args)
            self.assertEqual([call.args[:2] for call in pair.call_args_list],
                             [('six-layer', '4b'), ('six-layer', '2b'), ('4b-full', '4b')])
            self.assertEqual(state['completed_records'], 4560)
            self.assertEqual(state['status'], 'completed')
            with self.assertRaisesRegex(AssertionError, 'Never overwrite'):
                run.main_queue(args)

    def test_failed_six_layer_stage_never_starts_full_stage(self):
        def fail(stage, model, *args):
            if model == '2b':
                raise RuntimeError('new source mismatch')
            self.fake_pair(stage, model, *args)
        args = types.SimpleNamespace(authorization=self.authorization, output=self.output, execute=True)
        with patch.object(run, 'ROOT', self.root), \
             patch.object(run, 'validate_authorization', return_value=self.auth), \
             patch.object(run, 'wait_ready'), patch.object(run, 'verify_predecessor', return_value={'status': 'passed'}), \
             patch.object(run, 'run_pair', side_effect=fail) as pair:
            with self.assertRaisesRegex(RuntimeError, 'source mismatch'):
                run.main_queue(args)
        self.assertEqual([call.args[:2] for call in pair.call_args_list], [('six-layer', '4b'), ('six-layer', '2b')])
        self.assertEqual(run.read(self.output / 'queue-state.json')['status'], 'failed')
        self.assertTrue((self.output / 'six-layer/survey/4b-shard-0/receipt.json').exists())

    def test_adapter_keeps_old_module_immutable_and_routes_extension_only(self):
        original_root, original_cases = run.original.ROOT, run.original.cases_for
        with patch.object(run, 'validate_authorization', return_value=self.auth), \
             patch.object(run, 'acceptance') as accept, \
             patch.object(run, 'cases', return_value=['only new case']) as cases:
            adapter = run.adapted_runner('six-layer')
            self.assertEqual(adapter.ROOT, run.ROOT)
            self.assertEqual(adapter.cases_for('survey', '4b', 0), ['only new case'])
            cases.assert_called_once_with('six-layer', '4b', 0)
            self.assertEqual(adapter.cases_for('preflight', '4b', 0), [])
            auth = adapter.validate_authorization(self.authorization)
            self.assertEqual(auth['remote_output'], str(self.output / 'six-layer'))
            adapter.require_preflight_acceptance(None, auth)
            accept.assert_called_once_with(self.auth)
        self.assertEqual(run.original.ROOT, original_root)
        self.assertIs(run.original.cases_for, original_cases)


if __name__ == '__main__':
    unittest.main()
