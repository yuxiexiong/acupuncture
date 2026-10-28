"""CPU-only checks for exact Llama source scope, provenance and preflight."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import source_prepare as source


class Sources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = source.build_source_inventory()

    def test_six_layer_coverage_and_disjoint_shards(self):
        self.assertEqual(len(self.rows), 920)
        shards = [source.split_records(self.rows, source.MODEL, s) for s in (0, 1)]
        self.assertEqual(list(map(len, shards)), [464, 456])
        self.assertFalse({i['trace_id'] for i in shards[0]} & {i['trace_id'] for i in shards[1]})
        self.assertEqual(sum(i['record']['layer'] is None for i in self.rows), 8)
        self.assertEqual(sum(len(i['references']) > 1 for i in self.rows), 56)
        for layer in range(6):
            rows = [i['record'] for i in self.rows if i['record']['layer'] == layer]
            self.assertEqual(len(rows), 152)
            self.assertEqual(len({(r['channel'], r['dose']) for r in rows}), 19)
        self.assertTrue(all(i['record']['layer'] is None or i['record']['layer'] < 6 for i in self.rows))

    def test_preflight_bounded_distinct_same_as_existing_method(self):
        for shard in (0, 1):
            cases = source.select_preflight(self.rows, source.MODEL, shard)
            self.assertEqual(cases, source.select_preflight(list(reversed(self.rows)), source.MODEL, shard))
            self.assertEqual([c['name'] for c in cases], ['baseline', 'short_eos', 'long_positive', 'negative', 'low_positive', 'zero', 'restored'])
            self.assertEqual(len({c['record']['trace_id'] for c in cases[1:5]}), 4)
            self.assertTrue(all(c['record']['shard'] == shard for c in cases[1:5]))
            self.assertLess(source.identity(cases[3]['record']['record'])[3], 0)
            self.assertTrue(0 < source.identity(cases[4]['record']['record'])[3] < 1)
            self.assertEqual(cases[5]['arm_override'][2], 0)

    def test_duplicate_output_or_calibration_conflict_rejected(self):
        original = self.rows[0]['record']
        for field in ('output', 'calibration'):
            changed = copy.deepcopy(original)
            if field == 'output':
                changed['output']['token_ids'][0] += 1
            else:
                changed['calibration']['residual_scales']['0'] += 1
            with tempfile.TemporaryDirectory() as temporary:
                paths = [Path(temporary) / f'{s}.jsonl' for s in (0, 1)]
                for p, row in zip(paths, (original, changed)):
                    p.write_text(json.dumps(row) + '\n')
                contract = source.read(source.ROOT / 'contract.json')
                for entry, p in zip(contract['sources'], paths):
                    entry['sha256'] = source.sha(p)
                with self.assertRaisesRegex(AssertionError, 'Conflicting source'):
                    source.build_source_inventory(paths, contract)

    def test_changed_source_or_old_stopped_source_rejected(self):
        contract = source.read(source.ROOT / 'contract.json')
        contract['sources'][0]['sha256'] = 'wrong'
        with self.assertRaisesRegex(AssertionError, 'Source changed'):
            source.build_source_inventory(contract=contract)
        contract = source.read(source.ROOT / 'contract.json')
        contract['sources'][0]['path'] = 'experiments/llama31-layer-dose-survey-v1-2026-10-28/survey-r01/records.jsonl'
        with self.assertRaisesRegex(AssertionError, 'Only completed separate'):
            source.build_source_inventory(contract=contract)

    def test_raw_provenance_for_each_producing_worker(self):
        selected = {}
        for item in self.rows:
            key = item['record']['export_source']['run']
            selected.setdefault(key, item)
        self.assertEqual(len(selected), 4)
        for item in selected.values():
            provenance, metadata = source.source_provenance(item)
            self.assertEqual(metadata['revision'], source.REVISION)
            self.assertEqual(source.sha(source.REPO / provenance['record']), provenance['record_sha256'])
            wrong = copy.deepcopy(item)
            wrong['record']['export_source']['record_sha256'] = 'wrong'
            with self.assertRaises(AssertionError):
                source.source_provenance(wrong)

    def test_source_provenance_rejects_wrong_model_revision(self):
        item = self.rows[0]
        provenance, metadata = source.base.source_provenance(item)
        metadata['revision'] = 'wrong'
        with patch.object(source.base, 'source_provenance', return_value=(provenance, metadata)):
            with self.assertRaises(AssertionError):
                source.source_provenance(item)


if __name__ == '__main__':
    unittest.main()
