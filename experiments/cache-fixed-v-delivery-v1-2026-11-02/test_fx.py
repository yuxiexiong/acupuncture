"""CPU tests for FX-01.  CUDA_VISIBLE_DEVICES= python test_fx.py [RECEIPT_JSON]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fx_core as K  # noqa: E402

IDS = [f'P0{s}-f{f}' for s in range(1, 7) for f in (0, 1)]
T = {i: True for i in IDS}
Fz = {i: False for i in IDS}


def only(scen):
    return {i: i.startswith(tuple(scen)) for i in IDS}


class Rules(unittest.TestCase):
    def test_rescue_and_status(self):
        self.assertEqual(K.direction_status(T, Fz, T)['status'], 'support')
        self.assertEqual(K.direction_status(T, T, T)['rescued'], 0)                       # naturally correct is not rescued
        self.assertEqual(K.direction_status(T, Fz, only(['P01', 'P02', 'P03', 'P04']))['status'], 'unsupported')
        self.assertEqual(K.direction_status(only(['P01', 'P02', 'P03', 'P04']), Fz, T)['status'], 'baseline_insufficient')
        half = {i: (i.endswith('f0') or not i.startswith('P06')) for i in IDS}            # P06 rescued in one fact only
        self.assertEqual(K.direction_status(T, Fz, half)['rescued'], 5)

    def test_overall(self):
        self.assertTrue(K.overall({d: {'status': 'support'} for d in 'abc'} | {'d': {'status': 'unsupported'}})['met'])
        self.assertFalse(K.overall({'a': {'status': 'support'}, 'b': {'status': 'support'}, 'c': {'status': 'baseline_insufficient'}, 'd': {'status': 'unsupported'}})['met'])

    def test_fix_vs_u(self):
        r = K.fix_vs_u(T, Fz, T, only(['P01', 'P02', 'P03', 'P04']))
        self.assertEqual((r['wins'], r['losses'], r['advantage']), (2, 0, True))
        r = K.fix_vs_u(T, Fz, only(['P01', 'P02', 'P03', 'P04', 'P05']), only(['P01', 'P02', 'P03', 'P06']))
        self.assertEqual((r['wins'], r['losses'], r['advantage']), (2, 1, False))
        r = K.fix_vs_u(T, Fz, T, T)
        self.assertFalse(r['advantage'])
        r = K.fix_vs_u(T, Fz, only(['P01', 'P02', 'P03', 'P04', 'P05']), only(['P01', 'P02', 'P03', 'P04']))
        self.assertEqual((r['wins'], r['advantage']), (1, False))


class Wiring(unittest.TestCase):
    def test_budget_and_lists(self):
        import fx_run as R
        self.assertEqual(R.LIMITS['formal'], {'formations': 60, 'trajectories': 300, 'decode_forwards': 9600, 'calibrations': 6})
        self.assertEqual(R.LIMITS['preflight'], {'formations': 12, 'trajectories': 52, 'decode_forwards': 1664, 'calibrations': 1})
        self.assertEqual(R.exp.sha(R.FIXED), R.FIXED_SHA)
        self.assertEqual(R.exp.sha(R.URAND), R.URAND_SHA)
        fx = R.exp.read(R.FIXED)['heads']
        u = R.exp.read(R.URAND)['subsets']
        self.assertEqual(len(fx), 45)
        for iid in IDS:
            self.assertEqual(sorted(x[0] for x in u[iid][0]), sorted(x[0] for x in fx))
        self.assertEqual([r['id'] for r in R.items()], [f'P0{s}-f{f}' for s in range(1, 7) for f in (0, 1)])


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
