"""CPU tests for QCD-01 (synthetic worlds that must pass AND fail each rule; frozen plan; wiring).  CUDA_VISIBLE_DEVICES= python test_qcd.py [RECEIPT]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import qcd_core as K  # noqa: E402
import qcd_make_plan as MP  # noqa: E402

SCEN = [f'NQ0{s}' for s in range(1, 7)]
IDS = [f'{s}-{k}' for s in SCEN for k in range(9)]
SC = {i: i.split('-')[0] for i in IDS}


def world(right_wins_per_scen, left_wins_per_scen=None):
    """Per scenario: r right-only cells, then l left-only cells, the rest both right."""
    left_wins_per_scen = left_wins_per_scen or [0] * 6
    L_, R_ = {}, {}
    for s, r, l in zip(SCEN, right_wins_per_scen, left_wins_per_scen):
        for k in range(9):
            i = f'{s}-{k}'
            if r <= k < r + l:
                L_[i], R_[i] = True, False
            elif k < r:
                L_[i], R_[i] = False, True
            else:
                L_[i], R_[i] = True, True
    return L_, R_


class Stable(unittest.TestCase):
    def test_pass(self):
        L_, R_ = world([2, 2, 1, 1, 1, 0])                                     # 5/6 scenarios positive, total 7
        self.assertEqual(K.stable_class(L_, R_, SC)[0], 'right_better')
        L_, R_ = world([0] * 6, [2, 2, 1, 1, 1, 0])
        self.assertEqual(K.stable_class(L_, R_, SC)[0], 'left_better')

    def test_fail(self):
        L_, R_ = world([3, 2, 1, 1, 0, 0])                                     # 4/6 scenarios positive
        self.assertEqual(K.stable_class(L_, R_, SC)[0], 'none')
        L_, R_ = world([1, 1, 1, 1, 1, 0])                                     # 5/6 but total 5 < 6
        self.assertEqual(K.stable_class(L_, R_, SC)[0], 'none')
        L_, R_ = world([3, 3, 3, 1, 1, 0], [0, 0, 0, 0, 0, 2])                 # net cancels in one scenario only
        c, net, tot = K.stable_class(L_, R_, SC)
        self.assertEqual((c, tot), ('right_better', 9))

    def test_cancellation_visible_in_paired(self):
        L_, R_ = world([2] * 6, [2] * 6)                                        # 12 right-only, 12 left-only, net 0
        self.assertEqual(K.stable_class(L_, R_, SC)[0], 'none')
        p = K.paired(L_, R_)
        self.assertEqual((p['left_only'], p['right_only']), (12, 12))


class Gate(unittest.TestCase):
    def test_gate(self):
        ok = {('NA', 'd'): {k: 'right_better' for k in K.G_COMBOS}, ('LA', 'd'): {k: 'none' for k in K.G_COMBOS}}
        self.assertEqual(K.gate(ok)['status'], 'passed')
        bad = dict(ok)
        bad[('NA', 'd')] = dict(ok[('NA', 'd')], K4='none')
        r = K.gate(bad)
        self.assertEqual(r['status'], 'failed')
        self.assertIn('NA|d', r['disagreements'])


class Dose(unittest.TestCase):
    def test_dose_ok(self):
        a = {'x': {'A': 100.0, 'Q': 500.0, 'P': 5.0}}
        self.assertTrue(K.dose_ok(a, {'x': {'A': 100.9, 'Q': 520.0, 'P': 7.0}}, ('A',))['ok'])
        self.assertFalse(K.dose_ok(a, {'x': {'A': 101.2, 'Q': 500.0, 'P': 5.0}}, ('A',))['ok'])
        self.assertFalse(K.dose_ok(a, {'x': {'A': 100.0, 'Q': 520.0, 'P': 5.0}}, ('A', 'Q'))['ok'])

    def test_dose_rule(self):
        cls = {'E1|N1': 'none'}
        Y = {'B1': 20, 'N1': 50, 'N-A': 22, 'N-Q': 24, 'B-A': 48, 'B-Q': 46, 'E1': 49}
        self.assertEqual(K.dose_preferred(Y, cls, True), 'dose_preferred')
        self.assertEqual(K.dose_preferred(Y, {'E1|N1': 'right_better'}, True), 'position_and_dose')
        Y2 = dict(Y, **{'N-A': 45})                                             # N-A barely moves: |50-45|... moves, but not shrunk enough
        self.assertEqual(K.dose_preferred(Y2, cls, True), 'not_dose')
        self.assertEqual(K.dose_preferred(Y, cls, False), 'not_applicable')

    def test_cross_direction(self):
        self.assertEqual(K.cross_direction({'a': 'right_better', 'b': 'right_better', 'c': 'right_better', 'd': 'none'}), 'right_better')
        self.assertEqual(K.cross_direction({'a': 'right_better', 'b': 'right_better', 'c': 'not_applicable', 'd': 'none'}), 'none')


class Wiring(unittest.TestCase):
    def test_plan_and_limits(self):
        rows = MP.build()
        self.assertTrue(MP.check(rows))
        import qcd_run as R
        self.assertEqual(R.texts(), json.loads(json.dumps(rows)))
        self.assertEqual(len(R.plan('gformal', 0, 2)) + len(R.plan('gformal', 1, 2)), 108)
        self.assertEqual(len(R.plan('gformal', 0, 2)), 54)
        self.assertEqual([u['key'] for u in R.plan('preflight', 0, 1)], ['NA-NQ01-ABC-A', 'LA-NQ01-ABC-A'])
        self.assertEqual(R.LIMITS['gformal']['trajectories'], 108 * 42)
        self.assertEqual(R.LIMITS['sformal']['trajectories'], 108 * 40)
        self.assertEqual(R.LIMITS['preflight']['trajectories'], 2 * (42 + 40) + 2)
        self.assertEqual(R.LIMITS['sformal']['formations'], 108 * 28)
        c = R.scaled({'id': 'x', 'kind': 'native', 'layer': 0, 'channel': 1, 'dose': -1.0}, 1.35)
        self.assertEqual(c['dose'], -1.35)
        self.assertEqual(set(R.NEW_POLICIES) | {'B1', 'N1'}, set(rows[0]['policies']))


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
