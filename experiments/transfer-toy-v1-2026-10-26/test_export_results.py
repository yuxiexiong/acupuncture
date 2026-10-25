"""Exporter guards: complete Cartesian records, blind separation, and literal raw text."""
import json
from pathlib import Path
import tempfile
import unittest

from export_results import (SOURCE_CONDITIONS, TARGET_CONDITIONS, LABELS, blind_pack,
    digest_text, paired_html, validate_generation, verified_toy)
from run_io import write, sha


def generated(text='a <script> is literal'):
    return {'token_ids': [10, 248046], 'generated_token_count': 2, 'max_new_tokens': 512,
            'end_reason': 'eos_token', 'raw_text': text, 'answer_text': text}


def record(condition, role='source', item=None):
    item = item or {'id': 'Q1', 'prompt': 'A normal question?'}
    return {'model_role': role, 'item': item, 'condition': condition, 'output': generated(),
            'source_file': 'private/source.jsonl', 'source_file_sha256': 'ab' * 32}


class ExportTests(unittest.TestCase):
    def test_blind_forms_preserve_all_answers_and_hide_condition_metadata(self):
        raw = [record(c) for c in SOURCE_CONDITIONS] + [record(c, 'target') for c in TARGET_CONDITIONS]
        first, first_keys = blind_pack(raw, 'A', 'target9b', 20261026)
        second, second_keys = blind_pack(raw, 'B', 'target9b', 20261027)
        self.assertEqual(len(first), 22)
        self.assertEqual(len({r['anonymous_id'] for r in first}), 22)
        self.assertNotEqual([r['condition'] for r in first_keys], [r['condition'] for r in second_keys])
        for row in first + second:
            self.assertEqual(set(row), {'anonymous_id', 'question', 'answer', 'labels', 'evidence', 'uncertain_reason'})
            self.assertEqual(row['labels'], {label: None for label in LABELS})
            self.assertEqual(row['answer'], raw[0]['output']['raw_text'])
        self.assertEqual({r['condition'] for r in first_keys}, set(SOURCE_CONDITIONS + TARGET_CONDITIONS))

    def test_html_keeps_all_conditions_and_escapes_model_markup(self):
        source = [record(c) for c in SOURCE_CONDITIONS]
        target = [record(c, 'target') for c in TARGET_CONDITIONS]
        rendered = paired_html(source, target, [source[0]['item']])
        self.assertEqual(rendered.count('<article class="card">'), 22)
        self.assertNotIn('<script>', rendered)
        self.assertEqual(rendered.count('&lt;script&gt;'), 22)

    def test_token_integrity_guard(self):
        result = validate_generation(generated())
        self.assertEqual(result['raw_text_sha256'], digest_text(generated()['raw_text']))
        broken = generated()
        broken['generated_token_count'] = 3
        with self.assertRaises(AssertionError):
            validate_generation(broken)
        broken = generated()
        broken['token_ids'][-1] = 8
        with self.assertRaises(AssertionError):
            validate_generation(broken)

    def test_missing_source_record_is_not_exported_as_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            data = base / 'data'
            data.mkdir()
            items = {split: [{'id': f'{split}-{i:03d}', 'prompt': f'question {i}'} for i in range(64)]
                     for split in ('confirm', 'ability_diag')}
            for name, values in items.items():
                (data / f'{name}.jsonl').write_text(''.join(json.dumps(value) + '\n' for value in values))
            model_hash = {'13': 'a', '14': 'b'}
            for shard in (0, 1):
                root = base / 'source' / f'shard{shard}'
                write(root / 'receipt.json', {'status': 'completed', 'kind': 'source',
                    'completed_behavior': 96, 'expected_behavior': 96, 'completed_diagnostic': 0,
                    'expected_diagnostic': 0, 'completed_calibrations': 64, 'hooks_removed': True,
                    'target_weight_sha256_after': model_hash,
                    'engine': {'target_weight_sha256_before': model_hash}, 'source_sha256': {'runner': 'c'},
                    'data_sha256': {name: sha(data / f'{name}.jsonl') for name in items}})
                for split, dataset in (('behavior', 'confirm'), ('ability', 'ability_diag')):
                    for index in range(shard, 64, 2):
                        item = items[dataset][index]
                        context = 'prompt' + str(index)
                        cal = {'item_id': item['id'], 'context_sha256': digest_text(context)}
                        write(root / 'calibrations' / f'{split}-{index:03d}.json', cal)
                        if split == 'behavior':
                            for condition in SOURCE_CONDITIONS:
                                row = {'status': 'completed', 'item': item, 'condition': condition,
                                       'calibration': cal, 'context': context, 'output': generated()}
                                path = root / 'records' / split / f'{index:03d}-{condition}.jsonl'
                                path.parent.mkdir(parents=True, exist_ok=True)
                                path.write_text(json.dumps(row) + '\n')
            complete = verified_toy(base / 'source', 'source', data, {})
            self.assertEqual(len(complete['behavior']), 192)
            (base / 'source/shard0/records/behavior/000-S_0.jsonl').unlink()
            with self.assertRaises(AssertionError):
                verified_toy(base / 'source', 'source', data, {})


if __name__ == '__main__':
    unittest.main()
