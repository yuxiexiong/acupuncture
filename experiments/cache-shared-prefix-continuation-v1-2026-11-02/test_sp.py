"""CPU tests for SP-01.  CUDA_VISIBLE_DEVICES= python test_sp.py [RECEIPT_JSON]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'cache-first-token-continuation-v1-2026-11-02'))
sys.path.insert(0, str(HERE))
import fc_core as FK  # noqa: E402
import sp_core as K  # noqa: E402

IDS = [f'SP0{s}-f{f}' for s in range(1, 7) for f in (0, 1)]


class Panel(unittest.TestCase):
    def test_inputs_file(self):
        items = json.load(open(HERE / 'data/inputs-r01.json'))['items']
        self.assertEqual([r['id'] for r in items], IDS)
        by = {}
        for r in items:
            a, o = FK.answer_and_distractors(r['record'])
            self.assertEqual((a, sorted(o)), (r['target'], sorted(r['distractors'])))
            codes = [r['target']] + r['distractors']
            self.assertEqual(len({c[0] for c in codes}), 1)                       # same letter
            self.assertEqual(len({c[1] for c in codes}), 3)                       # distinct first digit
            by.setdefault(r['base_id'], []).append(r)
        for s, (f0, f1) in by.items():
            self.assertEqual(sorted([f0['target']] + f0['distractors']), sorted([f1['target']] + f1['distractors']))
            self.assertNotEqual(f0['target'], f1['target'])
            self.assertEqual(f0['target_position'], f1['target_position'])
        self.assertEqual(sorted(r['target_position'] for r in items[::2]), ['first', 'first', 'last', 'last', 'middle', 'middle'])

    def test_same_letter_classification(self):
        c = FK.classify('U17<|im_end|>', 'stop', 'U17', ['U43', 'U86'])
        self.assertEqual((c['main'], c['Y_delivery'], c['Y_strict']), ('correct', True, True))
        self.assertEqual(FK.classify('U43<|im_end|>', 'stop', 'U17', ['U43', 'U86'])['main'], 'distractor')
        self.assertEqual(FK.classify('U1<|im_end|>', 'stop', 'U17', ['U43', 'U86'])['main'], 'other_code')


class Rules(unittest.TestCase):
    def test_direction_status(self):
        t = {i: True for i in IDS}
        f = {i: False for i in IDS}
        self.assertEqual(K.direction_status(t, f, t)['status'], 'support')
        self.assertEqual(K.direction_status(t, f, f)['status'], 'unsupported')
        self.assertEqual(K.direction_status(f, f, t)['status'], 'baseline_insufficient')
        self.assertEqual(K.direction_status(t, t, t)['status'], 'effect_not_transferred')
        three = {i: i.startswith(('SP01', 'SP02', 'SP03')) for i in IDS}                 # T_nat delivered in 3/6 -> damage 3 < 4
        self.assertEqual(K.direction_status(t, three, t)['status'], 'effect_not_transferred')
        two = {i: i.startswith(('SP01', 'SP02')) for i in IDS}                           # damage 4 -> qualifies
        self.assertEqual(K.direction_status(t, two, t)['status'], 'support')

    def test_overall_and_margin(self):
        s = {'a': {'status': 'support'}, 'b': {'status': 'support'}, 'c': {'status': 'effect_not_transferred'}, 'd': {'status': 'support'}}
        self.assertTrue(K.overall(s)['met'])
        s['d'] = {'status': 'baseline_insufficient'}
        self.assertFalse(K.overall(s)['met'])
        self.assertEqual(K.margin({'10': 5.0, '20': 3.0, '30': 4.0}, 10, [20, 30]), 1.0)
        self.assertIsNone(K.margin({}, 10, [20]))


class Wiring(unittest.TestCase):
    def test_budget(self):
        import sp_run as R
        self.assertEqual(R.LIMITS['formal'], {'formations': 60, 'trajectories': 216, 'decode_forwards': 6912, 'calibrations': 6})
        self.assertEqual(R.LIMITS['preflight'], {'formations': 12, 'trajectories': 40, 'decode_forwards': 1280, 'calibrations': 1})
        self.assertEqual(R.PREFLIGHT_ITEMS, ('SP01-f0', 'SP01-f1'))
        self.assertEqual(len(R.plan('formal', 0, 2)) + len(R.plan('formal', 1, 2)), 12)
        self.assertEqual(sorted(u['item_id'] for w in (0, 1) for u in R.plan('formal', w, 2)), IDS)   # the SP panel, not P
        self.assertEqual([r['id'] for r in R.items()], IDS)
        self.assertEqual([u['item_id'] for u in R.plan('preflight', 0, 1)], ['SP01-f0', 'SP01-f1'])


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
