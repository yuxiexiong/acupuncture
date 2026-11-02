"""CPU tests for CT-01.  python test_ct.py [RECEIPT_JSON]"""
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ct_core as K  # noqa: E402


class Rules(unittest.TestCase):
    def test_answer_extraction(self):
        a, o = K.answer_and_distractors('档案记录：松塔编号为A17，目标条目海桥编号为B26，麦田编号为C38。')
        self.assertEqual((a, o), ('B26', ['A17', 'C38']))
        a, o = K.answer_and_distractors('站点登记：目标条目北亭编号为N48，东湾编号为P61，西岭编号为Q79。')
        self.assertEqual((a, o), ('N48', ['P61', 'Q79']))

    def test_category_priority(self):
        sp, ans, dis = {9}, {1, 2}, {2, 3}
        self.assertEqual(K.categorize(9, 'x', sp, 1, ans, dis), 'special')
        self.assertEqual(K.categorize(1, 'B', sp, 1, ans, dis), 'clean_first_token')
        self.assertEqual(K.categorize(2, '2', sp, 1, ans, dis), 'answer_overlap')          # answer before distractor
        self.assertEqual(K.categorize(3, '3', sp, 1, ans, dis), 'distractor_overlap')
        self.assertEqual(K.categorize(4, '\n', sp, 1, ans, dis), 'whitespace_punct')
        self.assertEqual(K.categorize(5, '，', sp, 1, ans, dis), 'whitespace_punct')
        self.assertEqual(K.categorize(6, '目标', sp, 1, ans, dis), 'lexical')
        self.assertEqual(K.categorize(7, '�', sp, 1, ans, dis), 'uncertain')

    def test_interaction_closure(self):
        import random
        random.seed(0)
        cells = {}
        for c in ('000', '100', '010', '001', '110', '101', '011', '111'):
            z44, z46, za, D = random.uniform(-5, 5), random.uniform(5, 20), random.uniform(5, 20), random.uniform(-15, 2)
            cells[c] = K.cell_terms(z44, z46, za, D, 248046)
            self.assertAlmostEqual(cells[c]['D'], cells[c]['Q'] + cells[c]['A'] - cells[c]['B'])
        dec, err = K.decompose_interactions(cells)
        self.assertLess(err, 1e-9)

    def test_edge_aux_does_not_imply_rise(self):
        zu = {0: 10.0, 1: 8.0, 2: 6.0}       # s0 = 0, old winner 1, new winner 2
        zv = {0: 10.0, 1: 3.0, 2: 5.0}       # new winner fell (6 -> 5) but old fell more
        a = K.edge_aux(zu, zv, 0, 1, 2)
        self.assertTrue(a['switched'])
        self.assertEqual(a['new_over_old_advantage'], 2.0)
        self.assertGreater(a['d_s0_minus_new'], 0)          # new winner lost ground vs s0
        self.assertEqual(K.edge_aux(zu, zu, 0, 1, 1)['new_over_old_advantage'], 0.0)

    def test_prediction(self):
        ids = [f'P0{s}-f{f}' for s in range(1, 7) for f in (0, 1)]
        self.assertEqual(K.prediction_direction({i: 'whitespace_punct' for i in ids}), (True, 6))
        mix = {i: ('lexical' if i.startswith(('P01', 'P02')) and i.endswith('f1') else 'special') for i in ids}
        self.assertEqual(K.prediction_direction(mix), (False, 4))


def main():
    receipt = sys.argv[1] if len(sys.argv) > 1 else None
    res = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    if receipt:
        import hashlib
        repo = HERE.parent.parent
        src = {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.glob('*.py'))}
        with open(receipt, 'x') as f:
            json.dump({'status': 'passed' if res.wasSuccessful() else 'failed', 'tests_run': res.testsRun, 'failures': len(res.failures),
                       'errors': len(res.errors), 'source_hashes': src}, f, indent=2)
            f.write('\n')
    sys.exit(0 if res.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
