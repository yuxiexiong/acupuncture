"""CPU tests for C2 (no weights).  CUDA_VISIBLE_DEVICES= python test_c2.py [RECEIPT_JSON]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import c2_core as K  # noqa: E402
import c2_analysis as A  # noqa: E402

U = [0.5] * 4


def fx(F, X, U0=U, U1=U):
    return [{'F': F[0], 'FIX': X[0], 'H': X[0], 'U': U0}, {'F': F[1], 'FIX': X[1], 'H': X[1], 'U': U1}]


class Signed(unittest.TestCase):
    def test_stop_side(self):
        self.assertTrue(K.scenario_check(fx((4, 5), (3, 3)), 'FIX', 1.0)['pass'])
        self.assertFalse(K.scenario_check(fx((4, 5), (1, 1)), 'FIX', 1.0)['retain_ok'])
        self.assertFalse(K.scenario_check(fx((0.5, 0.6), (0.5, 0.6)), 'FIX', 1.0)['F_ok'])

    def test_answer_side_uses_negative_direction(self):
        neg = [-0.5] * 4
        ok = K.scenario_check(fx((-8, -9), (-5, -5), neg, neg), 'FIX', -1.0)
        self.assertTrue(ok['pass'])                                        # the case C1-P could not evaluate
        self.assertFalse(K.scenario_check(fx((-8, -9), (-5, -5), neg, neg), 'FIX', 1.0)['F_ok'])
        self.assertFalse(K.scenario_check(fx((-8, -9), (-2, -2), neg, neg), 'FIX', -1.0)['retain_ok'])   # < half
        self.assertFalse(K.scenario_check(fx((-8, -9), (-5, -5), [-4.9] * 4, [-4.9] * 4), 'FIX', -1.0)['E_ok'])

    def test_judge_and_prediction(self):
        p = {'pass': True, 'F_ok': True, 'retain_ok': True}
        f = {'pass': False, 'F_ok': False, 'retain_ok': False}
        self.assertEqual(K.judge({i: p for i in range(6)})['decision'], 'support')
        self.assertEqual(K.judge({**{i: f for i in range(2)}, **{i: p for i in range(2, 6)}})['decision'], 'insufficient_F')
        dec = {d: 'support' for d in K.DIRECTIONS}
        self.assertTrue(K.prediction(dec))
        dec['R1_L00_D-1'] = 'list_not_realized'
        self.assertFalse(K.prediction(dec))


def synth(r_effect):
    recs = []
    for s in ['P01', 'P02', 'P03', 'P04', 'P05', 'P06']:
        for k in (0, 1):
            cells = {}
            for d in K.DIRECTIONS:
                fixv = 3.5 if d.startswith('N_') else r_effect
                for c, z in {'N:CC': 0.0, 'N:CT': 4.0, 'N:CFIX': fixv, 'N:CH': 3.5, 'N:CUF1': 0.5, 'N:CUF2': 0.6, 'N:CUF3': 0.4, 'N:CUF4': 0.7}.items():
                    cells[f'{c}|{d}'] = {'readout': {'primary': {'cz_s46': z, 'cz_a': -2 * z}, 'eos': False}}
            recs.append({'item': {'id': f'{s}-f{k}', 'base_id': s}, 'cells': cells,
                         'selections': {d: {'overlap_H_FIX': 30} for d in K.DIRECTIONS}, 'write_audits': {d: {} for d in K.DIRECTIONS}})
    return recs


class Consumer(unittest.TestCase):
    def test_transfer_and_failure(self):
        res = A.analyse(synth(3.5))
        self.assertTrue(res['prediction_random_directions_transfer'])
        self.assertEqual(res['directions']['R0_L00_D-1']['answer']['arms']['FIX']['decision'], 'support')
        res = A.analyse(synth(0.6))
        self.assertFalse(res['prediction_random_directions_transfer'])
        self.assertEqual(res['primary']['N_L00_C4146_D-1'], 'support')
        self.assertEqual(res['primary']['R0_L00_D-1'], 'list_not_realized')


class Wiring(unittest.TestCase):
    def test_plan_conditions_lists(self):
        import c2_run as V
        self.assertEqual([u['item_id'] for u in V.plan('preflight', 0, 1)], list(V.PREFLIGHT_ITEMS))
        self.assertEqual(len(V.plan('formal', 0, 2)) + len(V.plan('formal', 1, 2)), 12)
        conds = V.conditions()
        self.assertEqual(list(conds), list(K.DIRECTIONS))
        self.assertEqual(conds['N_L00_C1210_D-1']['channel'], 1210)
        self.assertEqual(len(conds['R0_L00_D-1']['vector']), 2560)
        fu = json.loads(V.FIXU.read_text())
        fix = json.loads(V.P.FIXED.read_text())['heads']
        per = sorted(x[0] for x in fix)
        for sets in fu['subsets'].values():
            self.assertEqual(len(sets), 4)
            for s in sets:
                self.assertEqual(sorted(x[0] for x in s), per)
        self.assertEqual(V.LIMITS['formal'], {'formations': 60, 'scores': 492})


def main():
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    receipt = sys.argv[1] if len(sys.argv) > 1 else None
    res = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    if receipt:
        import hashlib
        repo = HERE.parent.parent
        src = {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.glob('*.py'))}
        import torch
        with open(receipt, 'x') as f:
            json.dump({'status': 'passed' if res.wasSuccessful() else 'failed', 'tests_run': res.testsRun,
                       'failures': len(res.failures), 'errors': len(res.errors), 'skipped': len(res.skipped),
                       'source_hashes': src, 'torch': torch.__version__}, f, indent=2)
            f.write('\n')
    sys.exit(0 if res.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
