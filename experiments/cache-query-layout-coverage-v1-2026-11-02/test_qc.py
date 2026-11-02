"""CPU tests for QC-01 (synthetic statuses that must pass AND fail the coverage prediction; panel structure; wiring).
CUDA_VISIBLE_DEVICES= python test_qc.py [RECEIPT]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import qc_core as K  # noqa: E402
import qc_make_inputs as MI  # noqa: E402

D = ('a', 'b', 'c', 'd')


def st(*xs):
    return dict(zip(D, xs))


S, U, NA, NB_ = 'support', 'unsupported', 'not_applicable_damage', 'not_applicable_baseline'


class Prediction(unittest.TestCase):
    def test_support(self):
        self.assertEqual(K.p_cov_spec(st(U, U, U, U), st(S, S, S, U))['status'], 'support')
        self.assertEqual(K.p_cov_spec(st(S, S, U, U), st(S, S, S, S))['status'], 'support')

    def test_no_room(self):
        self.assertEqual(K.p_cov_spec(st(S, S, S, U), st(S, S, S, S))['status'], 'no_room')

    def test_unsupported(self):
        self.assertEqual(K.p_cov_spec(st(U, U, U, U), st(S, S, U, U))['status'], 'unsupported')

    def test_indeterminate(self):
        self.assertEqual(K.p_cov_spec(st(S, S, NA, U), st(S, S, S, U))['status'], 'indeterminate')   # broad could reach 3 via n/a
        self.assertEqual(K.p_cov_spec(st(U, U, U, U), st(S, S, NA, U))['status'], 'indeterminate')   # tail short only via n/a
        self.assertEqual(K.p_cov_spec(st(U, U, U, U), st(S, NB_, NB_, NB_))['status'], 'indeterminate')

    def test_overall_needs_both(self):
        ok = {'NA': st(U, U, U, U), 'NA-tail': st(S, S, S, S), 'LA': st(U, U, U, U), 'LA-tail': st(S, S, S, U)}
        self.assertTrue(K.p_cov(ok)['met'])
        ok['LA'] = st(S, S, S, U)
        self.assertFalse(K.p_cov(ok)['met'])
        self.assertEqual(K.p_cov(ok)['L']['status'], 'no_room')

    def test_paired(self):
        self.assertEqual(K.paired({'x': True, 'y': False, 'z': True}, {'x': True, 'y': True, 'z': False}),
                         {'a_only': 1, 'b_only': 1, 'both': 1, 'neither': 0})


class Panel(unittest.TestCase):
    def test_inputs(self):
        nq = json.load(open(MI.NQ_INPUTS))['items']
        rows = MI.build(nq)
        self.assertTrue(MI.check(rows, nq))
        import qc_run as R
        self.assertEqual(R.items(), json.loads(json.dumps(rows, ensure_ascii=False)))
        self.assertEqual(len(R.plan('formal', 0, 2)), 135 + 3)
        self.assertEqual(len(R.plan('formal', 1, 2)), 135 + 3)
        self.assertEqual(len(R.plan('preflight', 0, 1)), 6)
        self.assertEqual(R.LIMITS['formal']['trajectories'], 270 * 13 + 6 * 13)
        self.assertEqual(R.LIMITS['preflight']['trajectories'], 5 * 13 + 2 + 13)
        for s in ('NQ01', 'NQ02', 'NQ03', 'NQ04', 'NQ05', 'NQ06'):
            cal, _ = R.nq_calibration(f'{s}-ABC-A')
            self.assertTrue(cal['residual_scales'])
        with self.assertRaises(KeyError):
            R.nq_calibration('NQ07-ABC-A')


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
