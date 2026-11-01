"""CPU tests for EH (no weights).  CUDA_VISIBLE_DEVICES= python test_eh.py [RECEIPT_JSON]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import eh_core as K  # noqa: E402
import eh_analysis as A  # noqa: E402


class Rules(unittest.TestCase):
    def test_two_by_two(self):
        t = K.two_by_two(-12.0, -11.0, -6.0, -4.0)
        self.assertAlmostEqual(t['e1'], 8.0)
        self.assertAlmostEqual(t['I'], -4.0 - (-11.0) - (-6.0) + (-12.0))
        self.assertAlmostEqual(t['hist_clean_entry'] + t['entry_T_hist'], t['e1'])
        self.assertAlmostEqual(t['entry_clean_hist'] + t['hist_T_entry'], t['e1'])
        self.assertIsNone(K.two_by_two(0.0, 0.1, 0.2, 0.5)['s_H'])

    def test_labels(self):
        self.assertEqual(K.label_2x2(0.75, 0.25), 'history_alone_suffices')
        self.assertEqual(K.label_2x2(0.74, 0.25), 'partial')
        self.assertEqual(K.label_2x2(0.25, 0.75), 'entry_alone_suffices')
        self.assertEqual(K.label_2x2(0.8, 0.8), 'both_alone_strong')
        self.assertEqual(K.label_2x2(0.25, 0.25), 'joint_needed')
        self.assertEqual(K.label_2x2(0.26, 0.1), 'partial')
        self.assertEqual(K.label_2x2(None, None), 'not_formable')
        self.assertEqual(K.label_order(5.0, 5.0)[0], 'order_independent')
        self.assertEqual(K.label_order(3.75, 5.0)[0], 'order_independent')
        self.assertEqual(K.label_order(2.5, 5.0)[0], 'needs_context')
        self.assertEqual(K.label_order(3.0, 5.0)[0], 'partial')
        self.assertEqual(K.label_order(7.5, 5.0)[0], 'larger_in_clean')
        self.assertEqual(K.label_order(1.0, 0.5)[0], 'not_formable')

    def test_predictions(self):
        ids = [f'P0{s}-f{f}' for s in range(1, 7) for f in (0, 1)]
        good = {d: {i: {'s_H': 0.8, 's_X': 0.1, 'order_ratio': 0.3} for i in ids} for d in range(4)}
        p = K.predictions(good)
        self.assertTrue(p['P1'] and p['P2'])
        bad = {d: {i: {'s_H': 0.2, 's_X': 0.7, 'order_ratio': 0.9} for i in ids} for d in range(4)}
        p = K.predictions(bad)
        self.assertFalse(p['P1'] or p['P2'])


def synth(world):
    eh, b3 = {}, {}
    vals = {'history': (-12.0, -11.5, -5.0, -4.0, -10.0), 'entry': (-12.0, -5.0, -11.5, -4.0, -7.0),
            'joint': (-12.0, -11.8, -11.5, -4.0, -11.0)}[world]
    for s in range(1, 7):
        for f in (0, 1):
            iid = f'P0{s}-f{f}'

            def c(Dv, sha):
                return {'readout': {'D': Dv}, 'score': {'first_step_eos': Dv > 0, 'logits_sha256': sha}}
            r = {'item': {'id': iid}, 'cells': {'C_native': c(vals[0], 'cn')}}
            r3 = {'item': {'id': iid}, 'cells': {'C_native': c(vals[0], 'cn')}}
            for d in A.DIRECTIONS:
                r['cells'][f'X10|{d}'] = c(vals[1], 'x')
                r['cells'][f'H01|{d}'] = c(vals[2], 'h')
                r['cells'][f'XH11|{d}'] = c(vals[3], f'cc{d}')
                r['cells'][f'FIX0|{d}'] = c(vals[4], 'f')
                r3['cells'][f'N:CC|{d}'] = c(vals[3], f'cc{d}')
                r3['cells'][f'N:CFIX|{d}'] = c(vals[3] + 5.0, 'cf')
            eh[iid], b3[iid] = r, r3
    return eh, b3


class Consumer(unittest.TestCase):
    def test_worlds(self):
        res = A.analyse(*synth('history'))
        self.assertEqual(res['cross']['label_2x2'], 'history_alone_suffices')
        self.assertEqual(res['cross']['label_order'], 'needs_context')           # e2_rev 2 vs e2_fwd 5
        self.assertTrue(res['predictions']['P1'] and res['predictions']['P2'])
        res = A.analyse(*synth('entry'))
        self.assertEqual(res['cross']['label_2x2'], 'entry_alone_suffices')
        self.assertFalse(res['predictions']['P1'])
        self.assertEqual(res['cross']['label_order'], 'order_independent')        # e2_rev 5 vs 5
        res = A.analyse(*synth('joint'))
        self.assertEqual(res['cross']['label_2x2'], 'joint_needed')

    def test_replay_mismatch_raises(self):
        eh, b3 = synth('history')
        b3['P02-f0']['cells'][f'N:CC|{A.DIRECTIONS[0]}']['score']['logits_sha256'] = 'other'
        with self.assertRaises(AssertionError):
            A.analyse(eh, b3)


class Wiring(unittest.TestCase):
    def test_constants(self):
        import eh_run as R
        per_input = 1 + len(R.DIRECTIONS) * (1 + len(R.ARMS))
        self.assertEqual(per_input, 21)
        self.assertEqual(R.LIMITS['formal']['scores'], 12 * per_input)
        self.assertEqual(R.LIMITS['preflight']['scores'], 2 * per_input)
        self.assertEqual(R.LIMITS['formal']['formations'], 60)


def main():
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    receipt = sys.argv[1] if len(sys.argv) > 1 else None
    res = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    if receipt:
        import hashlib
        repo = HERE.parent.parent
        src = {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py'))}
        import torch
        with open(receipt, 'x') as f:
            json.dump({'status': 'passed' if res.wasSuccessful() else 'failed', 'tests_run': res.testsRun, 'failures': len(res.failures),
                       'errors': len(res.errors), 'source_hashes': src, 'torch': torch.__version__}, f, indent=2)
            f.write('\n')
    sys.exit(0 if res.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
