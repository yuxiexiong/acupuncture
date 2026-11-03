"""CPU tests for NCC-01.  Replacement on a cache-shaped object for V (channels [V_LO:] only, q/k kept), S, K and J (full conv q/k/V + S + K):
only the targets change, the donor and receiver are untouched, check_arm accepts the correct arm and rejects a corrupted one.  First-step
read-outs and categories on synthetic logits.  Aggregation: changes vs T, shared bootstrap, cross-needle paired differences.  Analysis
entry point end to end on records with the real key structure.  Budget arithmetic.
CUDA_VISIBLE_DEVICES= python test_ncc.py [RECEIPT]"""
import copy
import json
import os
import sys
import types as TY
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ncc_core as NC  # noqa: E402

SCN = [f'NQ0{k}' for k in range(1, 7)]
IDS = [f'{s}-{j}' for s in SCN for j in range(8)]
SCEN = {i: i.split('-')[0] for i in IDS}
G = (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
KL = (15, 19, 23, 27, 31)
VLO = 4


def cache(seed):
    import torch
    g = torch.Generator().manual_seed(seed)
    lay = []
    for i in range(32):
        if (i + 1) % 4 == 0:
            lay.append(TY.SimpleNamespace(keys=torch.randn(1, 2, 5, 3, generator=g), values=torch.randn(1, 2, 5, 3, generator=g)))
        else:
            lay.append(TY.SimpleNamespace(recurrent_states=torch.randn(1, 2, 3, 3, generator=g), conv_states=torch.randn(1, 7, 3, generator=g)))
    return TY.SimpleNamespace(layers=lay)


def get(layer, f):
    return getattr(layer, f)


def set_(layer, f, t):
    setattr(layer, f, t)


class Replacement(unittest.TestCase):
    def setUp(self):
        self.T, self.C = cache(1), cache(2)
        self.kinds = ['full_attention' if (i + 1) % 4 == 0 else 'linear_attention' for i in range(32)]

    def check(self, grp):
        import torch
        tg = NC.targets(grp, G, KL, VLO)
        Tc, Cc = copy.deepcopy(self.T), copy.deepcopy(self.C)
        X = NC.replace(self.T, self.C, tg, get, set_, copy.deepcopy)
        tset = {(l, f) for l, f, _ in tg}
        for i, lay in enumerate(X.layers):
            for f in vars(lay):
                a, r, d = getattr(lay, f), getattr(self.T.layers[i], f), getattr(self.C.layers[i], f)
                self.assertTrue(torch.equal(r, getattr(Tc.layers[i], f)) and torch.equal(d, getattr(Cc.layers[i], f)))   # untouched
                if (i, f) not in tset:
                    self.assertTrue(torch.equal(a, r))
                elif grp == 'V':
                    self.assertTrue(torch.equal(a[:, VLO:], d[:, VLO:]) and torch.equal(a[:, :VLO], r[:, :VLO]))
                else:
                    self.assertTrue(torch.equal(a, d))
        return X, tg

    def test_groups(self):
        for grp in NC.GROUPS:
            self.check(grp)
        tgJ = NC.targets('J', G, KL, VLO)
        self.assertIn((13, 'conv_states', None), tgJ)          # J includes the full conv buffer (q/k/V)
        self.assertEqual(len(tgJ), 14 + 14 + 10)
        self.assertTrue(all(l >= 13 for l, _f, _s in tgJ))      # shallow 0-12 never replaced

    def test_check_arm_rejects_corruption(self):
        import torch

        def check_arm(X, R_, D, tg):     # same logic as ncc_run.check_arm on plain attributes
            tset = {(l, f) for l, f, _ in tg}
            for l, f, sl in tg:
                a, d, r = getattr(X.layers[l], f), getattr(D.layers[l], f), getattr(R_.layers[l], f)
                assert torch.equal(a, d) if sl is None else (torch.equal(a[:, sl[1]:], d[:, sl[1]:]) and torch.equal(a[:, :sl[1]], r[:, :sl[1]]))
            for i, lay in enumerate(X.layers):
                for f in vars(lay):
                    if (i, f) not in tset:
                        assert torch.equal(getattr(lay, f), getattr(R_.layers[i], f))
        X, tg = self.check('V')
        check_arm(X, self.T, self.C, tg)
        X.layers[2].conv_states = X.layers[2].conv_states + 1         # shallow change must be caught
        with self.assertRaises(AssertionError):
            check_arm(X, self.T, self.C, tg)
        X2, tg2 = self.check('V')
        X2.layers[13].conv_states[:, :VLO] = 0                          # q/k channels overwritten must be caught
        with self.assertRaises(AssertionError):
            check_arm(X2, self.T, self.C, tg2)


class FirstStep(unittest.TestCase):
    def test_first_step_and_category(self):
        import torch
        z = torch.tensor([0.0, 5.0, 3.0, 4.0, 1.0])
        r = NC.first_step(z, 1, {3})
        self.assertAlmostEqual(r['B'], 1.0)
        self.assertEqual(r['winner'], 1)
        self.assertTrue(r['first_is_f'] and not r['first_stop'])
        self.assertAlmostEqual(r['best_stop'], 4.0)
        self.assertAlmostEqual(r['best_nonstop_comp'], 3.0)
        r2 = NC.first_step(z, 2, {1})
        self.assertTrue(r2['first_stop'] and r2['B'] < 0)
        self.assertEqual(NC.category(True, False, 'x', ['A1']), 'code')
        self.assertEqual(NC.category(False, True, '', ['A1']), 'stop')
        self.assertEqual(NC.category(False, False, '答案是 A1', ['A1']), 'preamble')
        self.assertEqual(NC.category(False, False, '不知道', ['A1']), 'other')


def fake_R():
    R = {('C', 'C'): {i: {'Y': 1, 'B': 2.0, 'cat': 'code', 'first_stop': False, 'z_f': 5.0, 'best_stop': 0.0, 'best_nonstop_comp': 3.0} for i in IDS}}
    vals = {'N_L00_C4146_D-1': {'T': (0, -3.0, 'stop'), 'TV': (0, -1.0, 'stop'), 'TS': (0, -2.5, 'stop'), 'TK': (0, -3.0, 'stop'), 'TJ': (1, 1.0, 'code')},
            'N_L12_C3621_D-1': {'T': (0, -1.0, 'preamble'), 'TV': (1, 1.5, 'code'), 'TS': (0, -0.8, 'preamble'), 'TK': (0, -1.0, 'preamble'), 'TJ': (1, 1.8, 'code')}}
    for d, arms in vals.items():
        for a, (y, b, c) in arms.items():
            R[(d, a)] = {i: {'Y': y, 'B': b, 'cat': c, 'first_stop': c == 'stop', 'z_f': b, 'best_stop': 0.0, 'best_nonstop_comp': 0.0} for i in IDS}
    return R


class Aggregation(unittest.TestCase):
    def test_needle_and_cross(self):
        R = fake_R()
        draws = NC.boot_draws(IDS, SCEN, n=50)
        arms = ('T', 'TV', 'TS', 'TK', 'TJ')
        b0 = NC.needle_block(R, 'N_L00_C4146_D-1', arms, IDS, SCEN, draws)
        b1 = NC.needle_block(R, 'N_L12_C3621_D-1', arms, IDS, SCEN, draws)
        self.assertEqual(b0['Y_counts']['TJ'], 48)
        self.assertEqual(b0['changes_vs_T']['TJ'], {'net': 48, 'toward': 48, 'away': 0, 'n_scen_toward': 6})
        self.assertAlmostEqual(b0['dB_vs_T']['TV']['eq'], 2.0)
        self.assertEqual(b0['gap_to_C']['T'], 48)
        self.assertEqual(b1['categories']['TS']['preamble'], 48)
        cr = NC.cross_needle(b0, b1, arms, IDS, SCEN, draws)
        self.assertAlmostEqual(cr['TV']['dY_L0_minus_L12']['eq'], -1.0)
        self.assertAlmostEqual(cr['TJ']['dB_L0_minus_L12']['eq'], 4.0 - 2.8)
        self.assertEqual(NC.boot_draws(IDS, SCEN, n=3), NC.boot_draws(IDS, SCEN, n=3))


class EndToEnd(unittest.TestCase):
    def test_analyse(self):
        import ncc_analysis as A
        R = fake_R()
        recs = {}
        for i in IDS:
            res = {'C': R[('C', 'C')][i]}
            for d in A.NEEDLES:
                res[d] = {a: R[(d, a)][i] for a in A.ARMS}
            recs[i] = {'scenario': SCEN[i], 'results': res}
        out = A.analyse(recs)
        self.assertEqual(out['Y_C'], 48)
        self.assertEqual(out['needles']['N_L12_C3621_D-1']['Y_counts']['TV'], 48)
        self.assertEqual(out['C_correct_subset']['n'], 48)
        self.assertNotIn('_dY', out['needles']['N_L00_C4146_D-1'])


class Wiring(unittest.TestCase):
    def test_budget(self):
        import ncc_run as R
        f, p = R.LIMITS['formal'], R.LIMITS['preflight']
        self.assertEqual((f['t1'], f['trajectories'], f['n_steps']), (528, 528, 528 * 31))
        self.assertEqual((p['t1'], p['engineering']), (22, 8))
        self.assertEqual(f['t1'] + f['n_steps'] + p['t1'] + p['n_steps'], (528 + 22) * 32)      # plan: at most 17600 new tokens
        self.assertEqual((f['formations'], f['prefix_prefills']), (144, 48))
        self.assertEqual(R.ARMS, ('T', 'TV', 'TS', 'TK', 'TJ'))
        self.assertEqual(R.KL, (15, 19, 23, 27, 31))
        self.assertEqual(len(R.plan('formal', 0, 2)) + len(R.plan('formal', 1, 2)), 48)


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
            json.dump({'status': 'passed' if res.wasSuccessful() and not res.skipped else 'failed', 'tests_run': res.testsRun, 'failures': len(res.failures),
                       'errors': len(res.errors), 'skipped': len(res.skipped), 'source_hashes': src, 'torch': torch.__version__}, f, indent=2)
            f.write('\n')
    sys.exit(0 if (res.wasSuccessful() and not res.skipped) else 1)


if __name__ == '__main__':
    main()
