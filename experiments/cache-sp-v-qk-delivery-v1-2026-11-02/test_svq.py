"""CPU tests for SVQ-01 (synthetic worlds that must pass AND fail each reading).  CUDA_VISIBLE_DEVICES= python test_svq.py [RECEIPT]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import svq_core as K  # noqa: E402

IDS = [f'SP0{s}-f{f}' for s in range(1, 7) for f in (0, 1)]
T = {i: True for i in IDS}
Fz = {i: False for i in IDS}


def only(scen):
    return {i: i.startswith(tuple(scen)) for i in IDS}


class Status(unittest.TestCase):
    def test_support_and_fail(self):
        self.assertEqual(K.rescue_status(T, Fz, T)['status'], 'support')
        self.assertEqual(K.rescue_status(T, Fz, only(['SP01', 'SP02', 'SP03', 'SP04']))['status'], 'unsupported')
        self.assertEqual(K.rescue_status(only(['SP01', 'SP02', 'SP03', 'SP04']), Fz, T)['status'], 'baseline_insufficient')
        self.assertEqual(K.rescue_status(T, only(['SP01', 'SP02', 'SP03']), T)['status'], 'effect_not_transferred')

    def test_naturally_right_is_not_rescued(self):
        tn = only(['SP01'])                                  # damage 5/6 holds; SP01 was never damaged
        r = K.rescue_status(T, tn, T)
        self.assertEqual((r['rescued'], r['status']), (5, 'support'))
        tn = only(['SP01', 'SP02'])                          # damage 4/6 holds, but only 4 scenarios can be rescued
        r = K.rescue_status(T, tn, T)
        self.assertEqual((r['rescued'], r['status']), (4, 'unsupported'))

    def test_overall_fixed_denominator(self):
        self.assertTrue(K.overall({d: {'status': 'support'} for d in 'abc'} | {'d': {'status': 'unsupported'}})['met'])
        self.assertFalse(K.overall({'a': {'status': 'support'}, 'b': {'status': 'support'},
                                    'c': {'status': 'baseline_insufficient'}, 'd': {'status': 'unsupported'}})['met'])

    def test_arm_better_than_reference_is_counted(self):
        # amendments v2 A2: F is a reference, not a ceiling; V can be supported where F is not
        f_ok = only(['SP01', 'SP02', 'SP04', 'SP05'])
        self.assertEqual(K.rescue_status(T, Fz, f_ok)['status'], 'unsupported')
        self.assertEqual(K.rescue_status(T, Fz, T)['status'], 'support')
        p = K.pairing(f_ok, T)
        self.assertEqual(p, {'a_only': 0, 'b_only': 4, 'both': 8, 'neither': 0})


class Pairing(unittest.TestCase):
    def test_cells(self):
        a = {'x': True, 'y': True, 'z': False, 'w': False}
        b = {'x': True, 'y': False, 'z': True, 'w': False}
        self.assertEqual(K.pairing(a, b), {'a_only': 1, 'b_only': 1, 'both': 1, 'neither': 1})


class Selection(unittest.TestCase):
    def item(self, target, order):
        rec = '名册：' + '，'.join(f'物{k}编号为{c}' for k, c in enumerate(order)) + '。'
        return {'record': rec, 'target': target, 'distractors': [c for c in order if c != target]}

    def test_first_listed_excluded_and_counted(self):
        items = {'a': self.item('V54', ['V28', 'V54', 'V91']), 'b': self.item('W19', ['W35', 'W62', 'W19']),
                 'c': self.item('U17', ['U17', 'U43', 'U86'])}
        cls = {'a': {'visible': 'V28'}, 'b': {'visible': 'W19'}, 'c': {'visible': 'U17'}}
        self.assertEqual(K.selection(cls, items), {'n': 2, 'target': 1, 'first_listed': 1, 'other': 0})
        cls = {'a': {'visible': 'V91'}, 'b': {'visible': 'W35 W19'}, 'c': {'visible': ''}}
        self.assertEqual(K.selection(cls, items), {'n': 2, 'target': 0, 'first_listed': 0, 'other': 2})

    def test_margin(self):
        self.assertAlmostEqual(K.margin({'1': 3.0, '2': 1.0, '3': 2.5}, 1, [2, 3]), 0.5)
        self.assertLess(K.margin({'1': 1.0, '2': 1.5, '3': 0.0}, 1, [2, 3]), 0)


class Wiring(unittest.TestCase):
    def test_budget_panel_positions(self):
        import svq_run as R
        self.assertEqual(R.LIMITS['formal'], {'formations': 60, 'trajectories': 204, 'decode_forwards': 6528, 'diagnostics': 204, 'calibrations': 6})
        self.assertEqual(R.LIMITS['preflight'], {'formations': 12, 'trajectories': 36, 'decode_forwards': 1152, 'diagnostics': 36, 'calibrations': 1})
        rows = R.items()
        self.assertEqual([r['id'] for r in rows], IDS)
        nonfirst = [r['id'] for r in rows if K.first_listed(r['record'], [r['target']] + r['distractors']) != r['target']]
        self.assertEqual(nonfirst, [i for i in IDS if not i.startswith(('SP01', 'SP04'))])
        for r in rows:
            pos = K.first_listed(r['record'], [r['target']] + r['distractors']) == r['target']
            self.assertEqual(pos, r['target_position'] == 'first')


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
