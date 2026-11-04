"""Offline acceptance only: fixtures contain no model output."""
import unittest
from prepare_c import selected_groups, requests, parse_answer, validate_predictions


class DataAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.groups = selected_groups()
        cls.pairs = list(requests(cls.groups))

    def test_counts_and_disjointness(self):
        self.assertEqual(len(self.groups), 160)
        self.assertEqual(sum(g['split']=='D' for g in self.groups), 64)
        self.assertEqual(len(self.pairs), 6400)
        self.assertEqual(len({x['request_id'] for x,_ in self.pairs}), 6400)
        self.assertEqual(len({g['exact_group_id'] for g in self.groups}), 160)
        self.assertEqual(sum(g['primary'] for _,g in self.pairs), 800)

    def test_conditional_labels_and_input_separation(self):
        for inp, gold in self.pairs:
            expected = gold['names'][1 if gold['condition']=='counterfact_visual' else 0]
            self.assertEqual(gold['answer'], expected)
            self.assertEqual(inp['image'] is None, gold['condition']=='no_image_usual')
            self.assertEqual(set(inp), {'request_id', 'text', 'image'})
            x,y = gold['names'][::1 if gold['order']==0 else -1]
            self.assertIn(f'{x} or {y}?', inp['text'])

    def test_strict_parser(self):
        names = ['cat', 'caterpillar']
        self.assertEqual(parse_answer(' Caterpillar. ', names), 'caterpillar')
        for text in ['cat or caterpillar', 'The cat is larger', 'dog', '', 'cat\ncaterpillar']:
            self.assertIsNone(parse_answer(text, names))

    def test_complete_fixture_and_fail_closed(self):
        gold = [g for _,g in self.pairs]
        fake = [dict(request_id=g['request_id'], text=g['answer']) for g in gold]
        self.assertEqual(sum(s['correct'] for s in validate_predictions(fake, gold)), 6400)
        fake[0]['truncated'] = True
        self.assertFalse(validate_predictions(fake, gold)[0]['correct'])
        for bad in [fake[:-1], fake+[fake[0]], [dict(request_id='unknown',text='cat')]+fake[1:]]:
            with self.assertRaises(ValueError): validate_predictions(bad, gold)


if __name__ == '__main__':
    unittest.main()
