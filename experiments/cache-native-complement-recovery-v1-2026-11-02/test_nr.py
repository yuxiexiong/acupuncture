"""CPU tests for NR-01.  CUDA_VISIBLE_DEVICES= python test_nr.py [RECEIPT_JSON]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import nr_core as K  # noqa: E402
import nr_analysis as A  # noqa: E402


def cells_from_R(D_P, R):
    return {code: D_P - R[name] for name, code in K.CODES.items()}


class Algebra(unittest.TestCase):
    def test_reviewer_additive_counterexample(self):
        R = {'X': 4.0, 'F': 4.0, 'H': 4.0, 'XF': 8.0, 'XH': 8.0, 'FH': 8.0, 'XFH': 12.0}
        dec = K.decompose(R, 12.0)
        for kk in ('i_XF', 'i_XH', 'i_FH', 'i_XFH'):
            self.assertEqual(dec[kk], 0.0)
        self.assertEqual(dec['identity_err'], 0.0)
        self.assertTrue(K.descriptive(dec, 12.0)['additive_compatible'])
        self.assertEqual(K.fact_predictions(dec, 12.0)['P_X'], 'support')         # 4 < 6
        self.assertEqual(K.fact_predictions(dec, 12.0)['P_XH'], 'violate')         # i_XH = 0 < tau 1.2

    def test_pure_pairwise_and_threeway(self):
        R = {'X': 1.0, 'F': 1.0, 'H': 1.0, 'XF': 2.0, 'XH': 6.0, 'FH': 2.0, 'XFH': 10.0}
        dec = K.decompose(R, 10.0)
        self.assertEqual(dec['i_XH'], 4.0)
        self.assertEqual(dec['i_XFH'], 10.0 - 2.0 - 6.0 - 2.0 + 3.0)
        self.assertEqual(dec['identity_err'], 0.0)
        R3 = {'X': 1.0, 'F': 1.0, 'H': 1.0, 'XF': 2.0, 'XH': 2.0, 'FH': 2.0, 'XFH': 9.0}
        d3 = K.decompose(R3, 9.0)
        self.assertEqual((d3['i_XF'], d3['i_XH'], d3['i_FH'], d3['i_XFH']), (0.0, 0.0, 0.0, 6.0))
        self.assertEqual(K.descriptive(d3, 9.0)['interaction_signs']['i_XFH'], 'positive')
        self.assertFalse(K.descriptive(d3, 9.0)['additive_compatible'])

    def test_retention_uses_N_not_absolute_D(self):
        D_P, D_C = 1.0, -13.0
        N = D_P - D_C
        R = K.recoveries(D_P, {'100': 0.0, '010': -5.0, '001': -2.0, '110': -7.0, '101': -4.0, '011': -12.0, '111': -13.0})
        dec = K.decompose(R, N)
        self.assertEqual(dec['L_X'], N - R['FH'])
        self.assertEqual(dec['L_X'], 1.0)                                          # not D(011) = -12

    def test_prediction_boundaries(self):
        R = {'X': 7.0, 'F': 4.0, 'H': 3.0, 'XF': 11.0, 'XH': 10.0 + 1.5, 'FH': 7.0, 'XFH': 14.0}
        dec = K.decompose(R, 14.0)                                                 # 0.5N = 7, tau = 1.4 (inexact) -> use exact case below
        self.assertEqual(K.fact_predictions(dec, 14.0)['P_X'], 'violate')          # r_X == 0.5N is not < 0.5N
        R2 = dict(R, X=6.875, XH=6.875 + 3.0 + 2.5)
        d2 = K.decompose(R2, 20.0)                                                 # tau = 2.0 exact, 0.5N = 10
        self.assertEqual(K.fact_predictions(d2, 20.0)['P_X'], 'support')
        self.assertEqual(K.fact_predictions(d2, 20.0)['P_XH'], 'support')          # i_XH = 2.5 >= 2
        d3 = K.decompose(dict(R2, XH=6.875 + 3.0 + 1.875), 20.0)
        self.assertEqual(K.fact_predictions(d3, 20.0)['P_XH'], 'violate')
        self.assertEqual(K.fact_predictions(d2, 0.5)['P_X'], 'not_applicable')

    def test_direction_status(self):
        sup = {f'P0{s}': ('support', 'support') for s in range(1, 7)}
        self.assertEqual(K.direction_status(sup)[0], 'support')
        mixed = {f'P0{s}': ('support', 'support') if s <= 4 else ('violate', 'support') for s in range(1, 7)}
        self.assertEqual(K.direction_status(mixed)[0], 'unsupported')
        na = {f'P0{s}': ('support', 'support') if s <= 4 else ('not_applicable', 'support') for s in range(1, 7)}
        self.assertEqual(K.direction_status(na)[0], 'insufficient')


def synth(world):
    recs = {}
    for s in range(1, 7):
        for f in (0, 1):
            iid = f'P0{s}-f{f}'
            D_C, D_P = -13.0, 1.0
            R = {'additive': {'X': 4.0, 'F': 6.0, 'H': 4.0, 'XF': 10.0, 'XH': 8.0, 'FH': 10.0, 'XFH': 14.0},
                 'xh': {'X': 2.0, 'F': 5.0, 'H': 3.0, 'XF': 7.0, 'XH': 9.0, 'FH': 8.0, 'XFH': 14.0}}[world]

            def cell(D):
                return {'readout': {'D': D, 'raw': {'s44': -9.0, 's46': 10.0 + D, 'a': 10.0}}, 'score': {'first_step_eos': D > 0, 'stop_winner': 248046}}
            cells = {'C_native': cell(D_C)}
            for d in A.DIRECTIONS:
                cells[f'T_native|{d}'] = cell(D_P)
                for code, D in cells_from_R(D_P, R).items():
                    cells[f'R{code}|{d}'] = cell(D)
            recs[iid] = {'item': {'id': iid}, 'cells': cells}
    return recs


class Consumer(unittest.TestCase):
    def test_worlds(self):
        res = A.analyse(synth('additive'))
        d = res['directions'][A.DIRECTIONS[0]]
        self.assertEqual(res['P_X_k_of_4'], 4)
        self.assertEqual(res['P_XH_k_of_4'], 0)
        self.assertEqual(d['additive_compatible_count'], 12)
        self.assertEqual(d['max_identity_err'], 0.0)
        res = A.analyse(synth('xh'))
        self.assertEqual(res['P_XH_k_of_4'], 4)                                    # i_XH = 4 >= tau 1.4
        self.assertEqual(res['directions'][A.DIRECTIONS[0]]['interaction_sign_counts']['i_XH']['positive'], 12)


class Wiring(unittest.TestCase):
    def test_budget(self):
        import nr_run as R
        per_input = 1 + len(R.DIRECTIONS) * (1 + len(R.ARMS))
        self.assertEqual(per_input, 33)
        self.assertEqual(R.LIMITS['formal'], {'formations': 60, 'scores': 396, 'calibrations': 6})
        self.assertEqual(R.LIMITS['preflight'], {'formations': 12, 'scores': 68, 'calibrations': 1})
        self.assertEqual(R.DIRECTIONS, A.DIRECTIONS)
        self.assertEqual(set(R.CELLS), set(K.CODES.values()))


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
