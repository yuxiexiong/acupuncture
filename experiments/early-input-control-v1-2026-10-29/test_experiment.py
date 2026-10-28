import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import experiment as ex


class ProtocolTests(unittest.TestCase):
    def test_exact_matrix_and_signed_pairs(self):
        for stage, count, doses in [('development', 193, ex.DOSES), ('confirmation', 145, ex.CONFIRM_DOSES)]:
            conditions = ex.conditions(stage)
            self.assertEqual(len(conditions), count)
            self.assertEqual(sum(c['kind'] == 'direction' for c in conditions), 48)
            for layer in ex.LAYERS:
                for channel in next(r['channels'] for r in ex.read(ex.HERE/'selection.json')['selected'] if r['layer'] == layer):
                    observed = {c['dose'] for c in conditions if c['kind'] == 'native' and c['layer'] == layer and c['channel'] == channel}
                    self.assertEqual(observed, set(doses))
            self.assertEqual(len(conditions)*24, 4632 if stage == 'development' else 3480)

    def test_shared_direction_and_candidate_selection(self):
        for direction in ex.read(ex.HERE/'data/directions.json'):
            self.assertAlmostEqual(sum(v*v for v in direction['values']), 1., places=12)
            self.assertEqual(ex.digest(direction['values']), direction['sha256'])
        for row in ex.read(ex.HERE/'selection.json')['selected']:
            self.assertEqual(row['channels'][0], row['historical_first_channel'])
            self.assertEqual(len(set(row['channels'])), 2)
            self.assertTrue(set(row['channels']) <= set(row['candidate_channels']))

    def test_pairs_stay_on_same_worker(self):
        for stage in ('development', 'confirmation'):
            rows = ex.items(stage)
            left, right = ex.assigned(rows, 0), ex.assigned(rows, 1)
            self.assertEqual(len(left), 12); self.assertEqual(len(right), 12)
            self.assertFalse({r['base_id'] for r in left} & {r['base_id'] for r in right})
            for r in rows:
                self.assertIn(r['reference_id'], {x['id'] for x in rows})

    def test_preflight_is_bounded_and_uses_no_confirmation(self):
        manifest = ex.preflight_cases()
        dev_ids = {r['id'] for r in ex.items('development')}
        for worker in manifest['workers'].values():
            self.assertEqual(len(worker['benchmarks']), 60)
            self.assertTrue(all(c['item_id'] in dev_ids for c in worker['benchmarks']))
            self.assertEqual({c['condition']['dose'] for c in worker['benchmarks']}, set(ex.DOSES))

    def test_test_authorization_cannot_launch_formal(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/'auth.json'
            auth = {'status': 'authorized', 'experiment': ex.HERE.name, 'allowed_stages': ['preflight'],
                'user_instruction': 'tests only', 'freeze_path': 'freeze.json', 'freeze_sha256': 'fixed',
                'maximum_workers': 2, 'formal_execution_authorized': False}
            ex.write(path, auth)
            for stage in ('development', 'confirmation', 'mechanism', 'patch'):
                with self.assertRaises(AssertionError):
                    ex.authorize(path, stage, True)
            with self.assertRaises(ValueError):
                ex.authorize(path, 'preflight', False)
            # A correct freeze alone must not bypass CPU/data/tokenizer/code evidence gates.
            with patch.object(ex, 'sha', return_value='fixed'), patch.object(ex, 'check'):
                with self.assertRaises(KeyError):
                    ex.authorize(path, 'preflight', True)
            with patch.object(ex, 'sha', return_value='changed'):
                with self.assertRaises(AssertionError):
                    ex.authorize(path, 'preflight', True)

    def test_archive_writes_refuse_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/'receipt.json'
            ex.write(path, {'status': 'failed'}, immutable=True)
            with self.assertRaises(FileExistsError):
                ex.write(path, {'status': 'passed'}, immutable=True)
            with self.assertRaises(AssertionError):
                ex.save_prepared(path, {'status': 'passed'})
            self.assertEqual(ex.read(path)['status'], 'failed')


if __name__ == '__main__':
    unittest.main()
