import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import experiment as exp


class DesignTests(unittest.TestCase):
    def test_whole_base_partition_and_stage_disjointness(self):
        items = exp.inputs()
        left, right = exp.assigned(items, 0), exp.assigned(items, 1)
        self.assertFalse({x['base_id'] for x in left} & {x['base_id'] for x in right})
        self.assertEqual({x['id'] for x in items}, {x['id'] for x in left + right})
        c1, c2 = exp.conditions('stage1'), exp.conditions('stage2')
        self.assertEqual((len(c1), len(c2)), (13, 18))
        self.assertFalse({c['id'] for c in c1} & {c['id'] for c in c2})
        for stage in ('stage1', 'stage2'):
            self.assertEqual(exp.conditions(stage)[-1]['channels'], {'13': 6626, '14': 5810})

    def test_authorization_stops_before_runtime_import(self):
        with self.assertRaises(ValueError):
            exp.authorize(None, 'stage1', 'formal', False)

    def test_immutable_evidence_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'record.json'
            exp.write(path, {'a': 1}, immutable=True)
            with self.assertRaises(FileExistsError):
                exp.write(path, {'a': 2}, immutable=True)
            self.assertEqual(exp.read(path), {'a': 1})

    def test_contract_matches_executable_schedule(self):
        contract = exp.read(exp.HERE / 'contract.json')
        for stage in ('stage1', 'stage2'):
            rows = exp.conditions(stage)
            self.assertEqual(len(rows), contract['stages'][stage]['condition_count'])
            self.assertEqual(len(rows) * 120, contract['stages'][stage]['generation_count'])
            self.assertEqual(len(rows) * 96, contract['stages'][stage]['candidate_readout_count'])
            for row in rows:
                if row['recipe'] != 'clean':
                    self.assertEqual(row['channels'], contract['recipes'][row['recipe']]['layer_channels'])

    def test_empty_stage2_review_cannot_authorize(self):
        auth = {'experiment': exp.HERE.name, 'status': 'authorized', 'freeze_sha256': 'freeze',
                'stages': ['stage1', 'stage2'], 'maximum_model_workers': 2, 'user_instruction': 'run'}
        gate = {'status': 'passed', 'measurement_usable': True, 'freeze_sha256': 'freeze',
                'basis': 'measurement_validity_not_AB_effect', 'reviewer': 'reviewer',
                'review_evidence': 'done', 'evidence_hashes': {}}
        with patch.object(exp, 'sha', return_value='freeze'), patch.object(exp, 'read', side_effect=[auth, gate]):
            with self.assertRaises((AssertionError, KeyError)):
                exp.authorize('auth.json', 'stage2', 'formal', True)


if __name__ == '__main__':
    unittest.main()
