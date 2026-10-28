"""CPU-only checks against archived evidence; never imports a model runtime."""
import unittest
import all_experiments as history


class CatalogTest(unittest.TestCase):
    def test_catalog_and_all_reader_counts(self):
        for dataset in history.load_catalog()['datasets']:
            with self.subTest(dataset=dataset['id']):
                for view in dataset['views']:
                    if view['path'].startswith('/?'):
                        continue
                    self.assertTrue(history.allowed_file(view['path']).is_file())
                if 'expected_rows' in dataset:
                    page = history.history_rows(dataset['id'], limit=2)
                    self.assertEqual(page['total'], dataset['expected_rows'])
                    self.assertLessEqual(len(page['items']), 2)
                    for row in page['items']:
                        self.assertTrue(row['id'])
                        self.assertIsInstance(row['prompt'], str)
                        self.assertIsInstance(row['conditions'], list)
                        self.assertTrue(row['raw'])
                        for path in row['raw']:
                            self.assertTrue(history.allowed_file(path).is_file())

    def test_boundary_and_pagination(self):
        for path in ('../README.md', '/etc/passwd', 'AGENTS.md',
                     'experiments/../AGENTS.md', '%2e%2e/README.md'):
            with self.assertRaises(ValueError):
                history.allowed_file(path)
        for args in [('unknown', 0, 20), ('initial24', -1, 20), ('initial24', 0, 101)]:
            with self.assertRaises(ValueError):
                history.history_rows(*args)
        self.assertEqual(history.history_rows('initial24', 24, 2)['items'], [])

    def test_actual_conditions_not_planned(self):
        row = history.history_rows('llama-transfer', limit=1)['items'][0]
        self.assertEqual(len(row['conditions']), 10)
        self.assertFalse(any('S_recipe' in c['name'] for c in row['conditions']))
        row = history.history_rows('diagnostic-2b', limit=1)['items'][0]
        self.assertEqual(len(row['conditions']), 19)
        self.assertTrue(all('text' not in c and 'scores' in c for c in row['conditions']))
        rows = history.history_rows('transfer-q3', limit=20)['items']
        self.assertEqual(sum(r['provenance']['model'] == '4b-historical' for r in rows), 3)
        rows = history.history_rows('stopped-serial-math', limit=20)['items']
        self.assertEqual(len(rows), 9)
        self.assertEqual(sum(len(r['conditions']) == 2 for r in rows), 8)
        self.assertEqual([c['name'] for c in rows[-1]['conditions']], ['baseline'])


if __name__ == '__main__':
    unittest.main()
