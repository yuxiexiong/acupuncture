"""CPU tests for SK-01.  CUDA_VISIBLE_DEVICES= python test_sk.py [RECEIPT_JSON]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sk_core as K  # noqa: E402
import sk_analysis as A  # noqa: E402

NAT = {'N': 14.0, 'R_S': 6.0, 'R_K': 0.5, 'R_SK': 7.0, 'J_native': 0.5}


def m(D00=-11.0, D10=-5.0, D01=-10.8, D11=-4.5):
    return K.main_effects(D00, D10, D01, D11)


class Categories(unittest.TestCase):
    def test_s_concentrated_and_boundary(self):
        e = m()                                                   # H 6.5, S0 6, K0 0.2, K1 0.5 ; eps = 1.3
        self.assertEqual(K.main_category(e, NAT), 'S_concentrated')
        e2 = m(D10=-6.31)                                          # S0 = 4.69 -> |S0-H| = 1.81 > 1.3
        self.assertNotEqual(K.main_category(e2, NAT), 'S_concentrated')
        e3 = m(D10=-5.0, D01=-9.69)                               # K0 = 1.31 > eps
        self.assertNotEqual(K.main_category(e3, NAT), 'S_concentrated')
        e4 = m(D10=-4.0, D01=-9.5, D11=-3.5)                      # H 7.5, eps 1.5 (exact); K0 = 1.5 == eps, K1 0.5, |S0-H| 0.5
        self.assertEqual(K.eps(e4['H']), 1.5)
        self.assertEqual(K.main_category(e4, NAT), 'S_concentrated')
        e5 = m(D10=-4.0, D01=-9.375, D11=-3.5)                    # K0 = 1.625 > eps
        self.assertNotEqual(K.main_category(e5, NAT), 'S_concentrated')

    def test_other_categories(self):
        self.assertEqual(K.main_category(m(D10=-10.8, D01=-5.0, D11=-4.5), NAT), 'KV_concentrated')
        self.assertEqual(K.main_category(m(D10=-4.6, D01=-4.6, D11=-4.5), NAT), 'redundant')
        self.assertEqual(K.main_category(m(D10=-9.0, D01=-9.0, D11=-4.5), NAT), 'joint_distributed')
        self.assertEqual(K.main_category(m(D10=-2.0, D01=-13.0, D11=-4.5), NAT), 'opposing')
        self.assertEqual(K.main_category(m(D11=-10.5), NAT), 'native_strong_mixed_weak')
        self.assertEqual(K.main_category(m(), dict(NAT, N=0.5)), 'not_applicable')
        self.assertEqual(K.main_category(m(D11=-13.0), NAT), 'reverse_effect')
        tiny = K.main_effects(-11.0, -10.5, -10.5, -10.0)          # H = 1, eps 0.5; S0 = K0 = S1 = K1 = 0.5: both patterns
        self.assertEqual(K.main_category(tiny, NAT), 'resolution_insufficient')

    def test_p_native(self):
        self.assertEqual(K.p_native(NAT), 'support')                           # thr 2.8
        self.assertEqual(K.p_native(dict(NAT, R_S=2.79)), 'violate')
        self.assertEqual(K.p_native(dict(NAT, N=15.0, R_S=3.0, R_K=2.5)), 'support')      # thr 3.0, gap 0.5 exactly
        self.assertEqual(K.p_native(dict(NAT, N=15.0, R_S=3.0, R_K=2.625)), 'violate')
        self.assertEqual(K.p_native(dict(NAT, N=15.0, R_S=2.875, R_K=0.0)), 'violate')
        self.assertEqual(K.p_native(dict(NAT, N=0.9)), 'not_applicable')

    def test_native_patterns(self):
        self.assertEqual(K.native_pattern(dict(NAT, R_S=1.0, R_K=1.0, R_SK=5.0)), 'redundant_or_substitutive')
        self.assertEqual(K.native_pattern(dict(NAT, R_S=1.0, R_K=1.0, R_SK=1.0)), 'recovery_ops_weak')
        self.assertEqual(K.native_pattern(NAT), 'S_recovery')
        self.assertEqual(K.native_pattern(dict(NAT, R_S=0.5, R_K=5.0)), 'KV_recovery')
        self.assertEqual(K.native_pattern(dict(NAT, R_S=5.0, R_K=5.0)), 'both_recover')
        nt = K.native_effects(-12.0, 2.0, -4.0, 1.5, -6.0)
        self.assertAlmostEqual(nt['J_native'], nt['R_S'] + nt['R_K'] - nt['R_SK'])

    def test_direction_label_and_near(self):
        ok, _ = K.direction_label({f'P0{s}': ('S_concentrated',) * 2 if s <= 5 else ('S_concentrated', 'other') for s in range(1, 7)}, 'S_concentrated')
        self.assertTrue(ok)
        ok, _ = K.direction_label({f'P0{s}': ('S_concentrated',) * 2 if s <= 4 else ('other', 'other') for s in range(1, 7)}, 'S_concentrated')
        self.assertFalse(ok)
        self.assertIn('K0', K.near_boundaries(m(D01=-9.7), NAT))


def synth(world):
    recs = {}
    for s in range(1, 7):
        for f in (0, 1):
            iid = f'P0{s}-f{f}'
            vals = {'S': {'SK00': -11.0, 'SK10': -5.0, 'SK01': -10.8, 'SK11': -4.5, 'T_native': 1.0, 'P_S0': -6.0, 'P_K0': 0.5, 'P_SK0': -7.0},
                    'KV': {'SK00': -11.0, 'SK10': -10.8, 'SK01': -5.0, 'SK11': -4.5, 'T_native': 1.0, 'P_S0': 0.5, 'P_K0': -6.0, 'P_SK0': -7.0},
                    'red': {'SK00': -11.0, 'SK10': -4.6, 'SK01': -4.6, 'SK11': -4.5, 'T_native': 1.0, 'P_S0': 0.6, 'P_K0': 0.6, 'P_SK0': -6.0}}[world]

            def cell(D):
                return {'readout': {'D': D, 'raw': {'s44': -9.0, 's46': 10.0 + D, 'a': 10.0}},
                        'score': {'first_step_eos': D > 0, 'stop_winner': 248046}}
            cells = {'C_native': cell(-13.0)}
            for d in A.DIRECTIONS:
                for c, D in vals.items():
                    cells[f'{c}|{d}'] = cell(D)
            recs[iid] = {'item': {'id': iid}, 'cells': cells}
    return recs


class Consumer(unittest.TestCase):
    def test_worlds(self):
        res = A.analyse(synth('S'))
        self.assertEqual((res['P_S_k_of_4'], res['P_native_k_of_4']), (4, 4))
        self.assertEqual(res['directions'][A.DIRECTIONS[0]]['cross_table_facts'], {'S_concentrated|support': 12})
        res = A.analyse(synth('KV'))
        self.assertEqual((res['P_S_k_of_4'], res['P_native_k_of_4']), (0, 0))
        self.assertEqual(res['directions'][A.DIRECTIONS[0]]['category_label'], 'KV_concentrated')
        res = A.analyse(synth('red'))
        d = res['directions'][A.DIRECTIONS[0]]
        self.assertEqual(d['category_label'], 'redundant')
        self.assertEqual(d['native_pattern_label'], 'redundant_or_substitutive')


class Wiring(unittest.TestCase):
    def test_budget(self):
        import sk_run as R
        per_input = 1 + len(R.DIRECTIONS) * (1 + len(R.ARMS))
        self.assertEqual(per_input, 33)
        self.assertEqual(R.LIMITS['formal'], {'formations': 60, 'scores': 396, 'calibrations': 6})
        self.assertEqual(R.LIMITS['preflight'], {'formations': 12, 'scores': 2 * per_input + 2, 'calibrations': 1})
        self.assertEqual(R.DIRECTIONS, A.DIRECTIONS)
        self.assertEqual(R.OFF_DIR, 'N_L00_C4146_D-1')


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
