"""CPU tests for FXS-01 (synthetic worlds that must pass AND fail each reading).  CUDA_VISIBLE_DEVICES= python test_fxs.py [RECEIPT]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fxs_core as K  # noqa: E402

IDS = [f'P0{s}-f{f}' for s in range(1, 7) for f in (0, 1)]
SP = 2.0 ** -6     # a bf16 gap of 1/64 at |v| in [2, 4): half-gap 1/128 per logit


def arm(m, argmax=0, gap=SP):
    return {'q0': m, 's0': 0.0, 'argmax': argmax, 'spacing': {'q0': gap, 's0': gap}}


def world(dfix, drest, dv, du=None, dub=None, nat=-10.0, gap=SP):
    du = dfix if du is None else du
    dub = drest if dub is None else dub
    return {'T_nat': arm(nat, 1, gap), 'T_V': arm(nat + dv, 0, gap), 'T_FIXV': arm(nat + dfix, 1, gap), 'T_RESTV': arm(nat + drest, 1, gap),
            'T_U': arm(nat + du, 1, gap), 'T_Ubar': arm(nat + dub, 1, gap)}


class Labels(unittest.TestCase):
    def test_label_regions(self):
        r = K.input_reading(world(4.0, 6.0, 10.0))                 # additive: J = 0
        self.assertEqual(r['FIX']['label'], 'additive')
        self.assertAlmostEqual(r['FIX']['J'], 0.0)
        r = K.input_reading(world(1.0, 1.0, 10.0))                 # super: J = 8 > tau = 1
        self.assertEqual(r['FIX']['label'], 'super')
        r = K.input_reading(world(8.0, 8.0, 10.0))                 # sub: J = -6
        self.assertEqual(r['FIX']['label'], 'sub')
        r = K.input_reading(world(0.2, 0.3, 0.5))                  # |dV| < 1
        self.assertEqual(r['FIX']['label'], 'insufficient')
        self.assertIsNone(r['FIX']['share'])

    def test_tau_scales(self):
        self.assertEqual(K.label(1.9, 20.0), 'additive')           # tau = 2
        self.assertEqual(K.label(2.1, 20.0), 'super')
        self.assertEqual(K.label(0.5, 2.0), 'additive')            # tau = 0.5 (abs floor), boundary inclusive
        self.assertEqual(K.label(-0.5078125, 2.0), 'sub')

    def test_u_split_independent(self):
        r = K.input_reading(world(4.0, 6.0, 10.0, du=1.0, dub=1.0))
        self.assertEqual((r['FIX']['label'], r['U']['label']), ('additive', 'super'))
        self.assertAlmostEqual(r['J_FIX_minus_J_U'], -8.0)

    def test_precision_sensitive(self):
        # J exactly at tau = 1.0 with dV = 10: any error flips the corner labels
        r = K.input_reading(world(4.5, 4.5, 10.0))
        self.assertEqual(r['FIX']['label'], 'additive')
        self.assertTrue(r['FIX']['sensitive'])
        r = K.input_reading(world(4.0, 6.0, 10.0))
        self.assertFalse(r['FIX']['sensitive'])
        self.assertAlmostEqual(r['FIX']['err'], 6 * SP)


class Aggregation(unittest.TestCase):
    def reads(self, spec):
        return {i: K.input_reading(world(*spec(i))) for i in IDS}

    def test_direction_supported_and_mixed(self):
        s = K.summarise(self.reads(lambda i: (4.0, 6.0, 10.0)), 'FIX')
        self.assertEqual(s['direction'], 'additive')
        s = K.summarise(self.reads(lambda i: (1.0, 1.0, 10.0) if i.startswith(('P01', 'P02')) else (4.0, 6.0, 10.0)), 'FIX')
        self.assertEqual(s['direction'], 'mixed')                  # only 4/6 additive
        s = K.summarise(self.reads(lambda i: (1.0, 1.0, 10.0) if i == 'P01-f0' else (4.0, 6.0, 10.0)), 'FIX')
        self.assertEqual(s['scenarios']['P01'], 'mixed')
        self.assertEqual(s['direction'], 'additive')               # 5/6 additive

    def test_worst_case(self):
        sens = lambda i: (4.5, 4.5, 10.0) if i.startswith(('P01', 'P02')) else (4.0, 6.0, 10.0)   # noqa: E731
        s = K.summarise(self.reads(sens), 'FIX')
        self.assertEqual(s['direction'], 'additive')
        self.assertEqual(s['worst_direction'], 'mixed')
        self.assertEqual(s['n_sensitive'], 4)

    def test_k_of_4(self):
        self.assertEqual(K.k_of_4({'a': 'additive', 'b': 'super', 'c': 'mixed', 'd': 'additive'})['additive'], 2)

    def test_threshold_compatible(self):
        sc = world(4.0, 6.0, 10.0)
        r = K.input_reading(sc)
        self.assertTrue(K.threshold_compatible(r, sc, 0))
        sc['T_FIXV']['argmax'] = 0
        self.assertFalse(K.threshold_compatible(r, sc, 0))
        sc = world(1.0, 1.0, 10.0)
        self.assertFalse(K.threshold_compatible(K.input_reading(sc), sc, 0))


class Wiring(unittest.TestCase):
    def test_budget_sets_spacing(self):
        import fxs_run as R
        self.assertEqual(R.LIMITS['formal'], {'formations': 60, 'scores': 300, 'calibrations': 6})
        self.assertEqual(R.LIMITS['preflight'], {'formations': 12, 'scores': 52, 'calibrations': 1})
        self.assertEqual(R.exp.sha(R.FIXED), R.FIXED_SHA)
        self.assertEqual(R.exp.sha(R.URAND), R.URAND_SHA)
        G = (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
        fx = R.exp.read(R.FIXED)['heads']
        for iid in IDS:
            s = R.heads_sets(G, fx, R.exp.read(R.URAND)['subsets'][iid][0])
            self.assertEqual({tuple(x) for x in s['T_U']} | {tuple(x) for x in s['T_Ubar']}, {tuple(x) for x in s['T_V']})
            self.assertFalse({tuple(x) for x in s['T_U']} & {tuple(x) for x in s['T_Ubar']})
        with self.assertRaises(AssertionError):
            R.heads_sets(G, fx, fx[:44])                            # wrong size must be refused
        self.assertEqual(R.spacing(3.0, 'torch.bfloat16'), 2.0 ** -6)
        self.assertEqual(R.spacing(-17.5, 'torch.bfloat16'), 2.0 ** -3)
        self.assertEqual(R.spacing(1.0, 'torch.float32'), 2.0 ** -23)
        self.assertEqual([r['id'] for r in R.items()], IDS)
        self.assertEqual(R.T_ARMS[0], 'T_nat')


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
