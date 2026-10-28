"""CPU-only checks of the Llama successor boundary; no models or GPU calls."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import queue_run as run


class QueueChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.output = self.root / 'new-run'
        self.authorization = self.root / 'authorization.json'
        self.authorization.write_text('{}')
        self.auth = {'remote_output': str(self.output), 'freeze_sha256': 'new-frozen', 'predecessor': {}}

    def predecessor(self, status='completed'):
        path = self.root / 'old-experiment' / 'execution-r01'
        run.write(path / 'execution.json', {'immutable': True})
        run.write(path.parent / 'freeze.json', {'files': {}})
        digest = run.sha(path.parent / 'freeze.json')
        state = {'status': status, 'pid': 10, 'freeze_sha256': digest,
                 'completed_records': 4560, 'expected_records': 4560, 'stages': {}}
        for stage, models, count in (('six-layer', ('4b', '2b'), 152), ('4b-full', ('4b',), 1976)):
            state['stages'][stage] = {}
            for model in models:
                for shard in (0, 1):
                    key = f'{model}-shard-{shard}'
                    folder = path / stage / 'survey' / key
                    run.write(folder / 'receipt.json', {'status': 'completed', 'checks_passed': True,
                        'model_id': model, 'shard': shard,
                        'freeze_sha256': digest, 'completed_records': count, 'expected_records': count,
                        'integrity': {'hooks_removed': True}})
                    (folder.parent / f'{key}.exit').write_text('0\n')
                    state['stages'][stage][key] = {'status': 'completed', 'exit_code': 0,
                        'receipt_sha256': run.sha(folder / 'receipt.json')}
        run.write(path / 'queue-state.json', state)
        return {'predecessor': {'run': str(path), 'execution_sha256': run.sha(path / 'execution.json'),
            'freeze_sha256': digest, 'process': {'pid': 10, 'start_ticks': 100}}}, state

    def test_requires_all_stages_counts_and_six_successful_workers(self):
        auth, original = self.predecessor()
        state_path = Path(auth['predecessor']['run']) / 'queue-state.json'
        mutations = [lambda s: s['stages'].pop('4b-full'),
            lambda s: s['stages']['six-layer'].pop('2b-shard-1'),
            lambda s: s.update(completed_records=4559),
            lambda s: s.update(expected_records=4561),
            lambda s: s['stages']['4b-full']['4b-shard-1'].update(exit_code=1),
            lambda s: s['stages']['4b-full']['4b-shard-1'].update(status='running')]
        with patch.object(run.queue, 'process_alive', return_value=False):
            self.assertEqual(run.predecessor_ready(auth), (True, 'predecessor_completed'))
            for index, mutate in enumerate(mutations):
                with self.subTest(index=index):
                    state = deepcopy(original); mutate(state); run.write(state_path, state)
                    with self.assertRaises(AssertionError):
                        run.predecessor_ready(auth)

    def test_running_failed_dead_or_exiting_predecessor_never_starts(self):
        auth, state = self.predecessor('running_survey')
        state_path = Path(auth['predecessor']['run']) / 'queue-state.json'
        with patch.object(run.queue, 'process_alive', return_value=True):
            self.assertEqual(run.predecessor_ready(auth), (False, 'predecessor_running'))
        with patch.object(run.queue, 'process_alive', return_value=False):
            with self.assertRaisesRegex(AssertionError, 'without a terminal receipt'):
                run.predecessor_ready(auth)
        for status in ('failed', 'stopped'):
            state['status'] = status; run.write(state_path, state)
            with self.assertRaisesRegex(AssertionError, 'failed or stopped'):
                run.predecessor_ready(auth)
        state['status'] = 'completed'; run.write(state_path, state)
        with patch.object(run.queue, 'process_alive', return_value=True):
            self.assertEqual(run.predecessor_ready(auth), (False, 'predecessor_exiting'))

    def test_changed_execution_freeze_pid_or_receipt_blocks(self):
        auth, state = self.predecessor()
        path = Path(auth['predecessor']['run'])
        for field in ('execution_sha256', 'freeze_sha256'):
            changed = deepcopy(auth); changed['predecessor'][field] = 'wrong'
            with self.subTest(field=field), self.assertRaises(AssertionError):
                run.predecessor_ready(changed)
        changed = deepcopy(state); changed['pid'] = 11; run.write(path / 'queue-state.json', changed)
        with self.assertRaises(AssertionError):
            run.predecessor_ready(auth)
        run.write(path / 'queue-state.json', state)
        receipt = path / '4b-full/survey/4b-shard-0/receipt.json'
        original = run.read(receipt); changed = dict(original, completed_records=1975)
        run.write(receipt, changed)
        with self.assertRaises(AssertionError):
            run.predecessor_ready(auth)
        state['stages']['4b-full']['4b-shard-0']['receipt_sha256'] = run.sha(receipt)
        run.write(path / 'queue-state.json', state)
        with self.assertRaises(AssertionError):
            run.predecessor_ready(auth)
        for field, value in (('model_id', '2b'), ('shard', 1)):
            changed = dict(original, **{field: value}); run.write(receipt, changed)
            state['stages']['4b-full']['4b-shard-0']['receipt_sha256'] = run.sha(receipt)
            run.write(path / 'queue-state.json', state)
            with self.subTest(field=field), self.assertRaises(AssertionError):
                run.predecessor_ready(auth)

    def test_gpu_occupancy_waits_after_predecessor_success(self):
        self.output.mkdir()
        state = {'status': 'waiting'}
        with patch.object(run.queue, 'prerequisites', return_value=self.auth), \
             patch.object(run.queue, 'predecessor_ready', return_value=(True, 'predecessor_completed')), \
             patch.object(run.queue, 'gpu_processes', side_effect=[['77, other experiment'], []]), \
             patch.object(run.queue.time, 'sleep') as sleep:
            result = run.queue.wait_ready(self.authorization, 'digest', self.output, state)
        sleep.assert_called_once_with(10)
        self.assertEqual(result, self.auth)
        self.assertEqual(state['gpu_compute_processes'], [])

    def fake_pair(self, mode, model, authorization, digest, output, state):
        state['stages'][mode] = {}
        for shard, count in ((0, 464), (1, 456)):
            key = f'{model}-shard-{shard}'
            state['stages'][mode][key] = {'status': 'completed', 'exit_code': 0}
            if mode == 'survey':
                run.write(output / mode / key / 'receipt.json', {'status': 'completed',
                    'completed_records': count, 'expected_records': count})

    def test_both_llama_preflights_precede_formal_work(self):
        with patch.object(run, 'ROOT', self.root), \
             patch.object(run, 'prerequisites', return_value=self.auth), \
             patch.object(run.queue, 'wait_ready'), \
             patch.object(run.queue, 'run_pair', side_effect=self.fake_pair) as pair:
            state = run.main(self.authorization, self.output, True)
        self.assertEqual([c.args[:2] for c in pair.call_args_list],
                         [('preflight', run.MODEL), ('survey', run.MODEL)])
        accepted = run.read(self.output / 'preflight-accepted.json')
        self.assertEqual(len(accepted['workers']), 2)
        self.assertEqual((state['status'], state['completed_records']), ('completed', 920))

    def test_failed_preflight_preserves_evidence_and_blocks_survey(self):
        def fail(mode, model, authorization, digest, output, state):
            (output / 'partial-evidence.txt').write_text('preserve me')
            self.fake_pair(mode, model, authorization, digest, output, state)
            state['stages'][mode][f'{model}-shard-1']['exit_code'] = 1
        with patch.object(run, 'ROOT', self.root), \
             patch.object(run, 'prerequisites', return_value=self.auth), \
             patch.object(run.queue, 'wait_ready'), \
             patch.object(run.queue, 'run_pair', side_effect=fail) as pair:
            with self.assertRaises(AssertionError):
                run.main(self.authorization, self.output, True)
        self.assertEqual([c.args[0] for c in pair.call_args_list], ['preflight'])
        self.assertFalse((self.output / 'preflight-accepted.json').exists())
        self.assertEqual(run.read(self.output / 'queue-state.json')['status'], 'failed')
        self.assertEqual((self.output / 'partial-evidence.txt').read_text(), 'preserve me')

    def test_existing_output_and_duplicate_queue_are_rejected(self):
        self.output.mkdir()
        with patch.object(run, 'prerequisites', return_value=self.auth):
            with self.assertRaisesRegex(AssertionError, 'overwrite or resume'):
                run.main(self.authorization, self.output, True)
        other = self.root / 'other-run'; auth = dict(self.auth, remote_output=str(other))
        with (self.root / '.queue.lock').open('a') as lock:
            run.fcntl.flock(lock, run.fcntl.LOCK_EX | run.fcntl.LOCK_NB)
            with patch.object(run, 'ROOT', self.root), patch.object(run, 'prerequisites', return_value=auth):
                with self.assertRaises(BlockingIOError):
                    run.main(self.authorization, other, True)
        self.assertFalse(other.exists())


if __name__ == '__main__':
    unittest.main()
