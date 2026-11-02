"""CPU tests for FC-01.  CUDA_VISIBLE_DEVICES= python test_fc.py [RECEIPT_JSON]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fc_core as K  # noqa: E402

T, DIS = 'B26', ['A17', 'C38']
Q = '请根据上面的记录，简短回答：目标条目的编号是什么？只需给出编号。'


class Classify(unittest.TestCase):
    def test_main_categories(self):
        c = K.classify('B26<|im_end|>', 'stop', T, DIS)
        self.assertEqual((c['main'], c['Y_delivery'], c['Y_strict']), ('correct', True, True))
        c = K.classify('B26。<|im_end|>', 'stop', T, DIS)
        self.assertEqual((c['main'], c['Y_delivery'], c['Y_strict']), ('correct', True, False))
        c = K.classify('B26，不对，B62', 'budget', T, DIS)
        self.assertEqual((c['main'], c['Y_delivery']), ('multi_code', False))
        self.assertEqual(K.classify('A17<|im_end|>', 'stop', T, DIS)['main'], 'distractor')
        self.assertEqual(K.classify('Z99', 'budget', T, DIS)['main'], 'other_code')
        self.assertEqual(K.classify('<|im_end|>', 'stop', T, DIS)['main'], 'stopped_no_code')
        self.assertEqual(K.classify('请请请', 'budget', T, DIS)['main'], 'budget_no_code')

    def test_boundaries_and_repeats(self):
        c = K.classify('B260', 'budget', T, DIS)
        self.assertEqual((c['main'], c['Y_delivery']), ('other_code', False))           # B260 is not B26
        c = K.classify('B26 B26', 'budget', T, DIS)
        self.assertTrue(c['Y_delivery'] and c['tags']['target_repeated'])
        self.assertFalse(c['Y_strict'])

    def test_think_handling(self):
        c = K.classify('<think>A17</think>B26<|im_end|>', 'stop', T, DIS)
        self.assertEqual((c['main'], c['Y_delivery']), ('correct', True))
        self.assertTrue(c['tags']['think_present'])
        c = K.classify('<think>B26 maybe', 'budget', T, DIS)
        self.assertEqual((c['main'], c['Y_delivery']), ('budget_no_code', False))
        self.assertTrue(c['tags']['think_unclosed'])

    def test_question_echo_tag(self):
        c = K.classify(Q + 'B26', 'budget', T, DIS, Q)
        self.assertTrue(c['tags']['contains_question'])
        self.assertEqual(c['main'], 'correct')
        self.assertFalse(K.classify('请', 'budget', T, DIS, Q)['tags']['contains_question'])


class Aggregation(unittest.TestCase):
    def test_p_f(self):
        ids = [f'P0{s}-f{f}' for s in range(1, 7) for f in (0, 1)]
        allT = {i: True for i in ids}
        self.assertEqual(K.p_f_direction(allT, allT)[0], 'support')
        tf = {i: not (i.startswith(('P01', 'P02')) and i.endswith('f1')) for i in ids}
        self.assertEqual(K.p_f_direction(allT, tf)[:2], ('unsupported', 4))
        c = {i: not i.startswith(('P01', 'P02')) for i in ids}
        self.assertEqual(K.p_f_direction(c, allT)[0], 'baseline_insufficient')
        tr = K.transitions({'a': False, 'b': True, 'c': True, 'd': False}, {'a': True, 'b': True, 'c': False, 'd': False})
        self.assertEqual(tr, {'wrong_to_right': 1, 'both_right': 1, 'right_to_wrong': 1, 'both_wrong': 1})

    def test_audit_and_answers(self):
        a, o = K.answer_and_distractors('档案记录：松塔编号为A17，目标条目海桥编号为B26，麦田编号为C38。')
        self.assertEqual((a, o), ('B26', ['A17', 'C38']))
        au = K.q0_audit('B', 'B26', ['A17', 'B62'])
        self.assertEqual(au['distractors_compatible'], ['B62'])
        self.assertTrue(au['target_compatible'] and not au['covers_full_answer'])


class Wiring(unittest.TestCase):
    def test_budget(self):
        import fc_run as R
        per_input = 2 + len(R.DIRECTIONS) * len(R.T_ARMS)
        self.assertEqual(per_input, 18)
        self.assertEqual(R.LIMITS['formal'], {'formations': 60, 'trajectories': 216, 'decode_forwards': 216 * 32, 'calibrations': 6})
        self.assertEqual(R.LIMITS['preflight'], {'formations': 12, 'trajectories': 2 * per_input + 2 + 2, 'decode_forwards': 40 * 32, 'calibrations': 1})
        self.assertEqual(R.MAX_NEW, 32)
        self.assertEqual(R.STOP, (248044, 248046))


def main():
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    receipt = sys.argv[1] if len(sys.argv) > 1 else None
    res = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    if receipt:
        import hashlib
        repo = HERE.parent.parent
        src = {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py'))}
        import torch
        with open(receipt, 'x') as f:
            json.dump({'status': 'passed' if res.wasSuccessful() else 'failed', 'tests_run': res.testsRun, 'failures': len(res.failures),
                       'errors': len(res.errors), 'source_hashes': src, 'torch': torch.__version__}, f, indent=2)
            f.write('\n')
    sys.exit(0 if res.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
