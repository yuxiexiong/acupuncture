"""CPU tests for QKF-01 (synthetic worlds that must pass AND fail each rule; r_post scaling; masks; wiring).
CUDA_VISIBLE_DEVICES= python test_qkf.py [RECEIPT]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import qkf_core as K  # noqa: E402

SC = [f'NQ0{k}' for k in range(1, 7)]
IDS = [f'{s}-{j}' for s in SC for j in range(8)]
SCEN = {i: i.split('-')[0] for i in IDS}
ARMS = ['V', 'F'] + [f'{s}_{u}_{h}' for s in ('R', 'A') for u in ('mu', 'pre', 'post') for h in ('q', 'k', 'qk')]


def world(fix=None, rep=None, rand_fix=False):
    """damaged = j < 4.  fix[h] / rep[h]: does the mu half h repair (R) / reproduce exactly (A)."""
    fix = fix or {'q': True, 'k': True, 'qk': True}
    rep = rep or {'q': True, 'k': True, 'qk': True}
    Y = {a: {} for a in ARMS}
    match = {a: {} for a in ARMS}
    for i in IDS:
        dmg = int(i.split('-')[1]) < 4
        Y['V'][i], Y['F'][i] = int(not dmg), 1
        match['F'][i] = not dmg
        for u in ('mu', 'pre', 'post'):
            for h in ('q', 'k', 'qk'):
                good = (fix[h] if u == 'mu' else rand_fix) or not dmg
                Y[f'R_{u}_{h}'][i] = int(good)
                m = rep[h] if u == 'mu' else rand_fix
                Y[f'A_{u}_{h}'][i] = Y['V'][i] if m else 1
                match[f'A_{u}_{h}'][i] = bool(m)
                match[f'R_{u}_{h}'][i] = False
        match['V'][i] = True
    return Y, match


class Rules(unittest.TestCase):
    def test_single_and_advantage(self):
        Y, m = world()
        q = K.quantities(Y, m, SCEN)
        s = K.single(q, 'k')
        self.assertTrue(s['R_ok'] and s['A_ok'])
        self.assertEqual(K.advantage(q, 'k', 'pre', {'R': True, 'A': True})['R'], True)
        self.assertEqual(K.advantage(q, 'k', 'post', {'R': False, 'A': True})['R'], 'engineering_not_judgeable')
        Y, m = world(rand_fix=True)
        q = K.quantities(Y, m, SCEN)
        self.assertFalse(K.advantage(q, 'k', 'pre', {'R': True, 'A': True})['R'])     # random as good -> no advantage
        Y, m = world(fix={'q': False, 'k': False, 'qk': True}, rep={'q': False, 'k': False, 'qk': True})
        q = K.quantities(Y, m, SCEN)
        self.assertFalse(K.single(q, 'q')['R_ok'])
        self.assertFalse(K.single(q, 'q')['A_ok'])

    def test_k_vs_q(self):
        Y, m = world(fix={'q': False, 'k': True, 'qk': True}, rep={'q': False, 'k': True, 'qk': True})
        self.assertEqual(K.k_vs_q(Y, m, K.quantities(Y, m, SCEN), SCEN)['verdict'], 'k_stronger')
        Y, m = world(fix={'q': True, 'k': False, 'qk': True}, rep={'q': True, 'k': False, 'qk': True})
        self.assertEqual(K.k_vs_q(Y, m, K.quantities(Y, m, SCEN), SCEN)['verdict'], 'q_stronger')
        Y, m = world(fix={'q': False, 'k': True, 'qk': True}, rep={'q': True, 'k': True, 'qk': True})
        self.assertEqual(K.k_vs_q(Y, m, K.quantities(Y, m, SCEN), SCEN)['verdict'], 'asymmetric')
        Y, m = world()
        self.assertEqual(K.k_vs_q(Y, m, K.quantities(Y, m, SCEN), SCEN)['verdict'], 'no_order')

    def test_interaction(self):
        base = {i: 0 for i in IDS}
        joint_only = K.interaction({'q': base, 'k': base, 'qk': {i: 1 for i in IDS}}, base, SCEN)
        self.assertTrue(joint_only['visible'] and joint_only['I'] == 1.0)
        sat = K.interaction({'q': {i: 1 for i in IDS}, 'k': {i: 1 for i in IDS}, 'qk': {i: 1 for i in IDS}}, base, SCEN)
        self.assertEqual(sat['I'], -1.0)                                  # saturation gives a negative I (not antagonism)
        add = K.interaction({'q': {i: 1 for i in IDS}, 'k': base, 'qk': {i: 1 for i in IDS}}, base, SCEN)
        self.assertFalse(add['visible'])


class Vectors(unittest.TestCase):
    def test_masks_and_rpost(self):
        import torch
        import qkf_run as R
        import qkf_rpost as RP
        u = torch.randn(14, 4096, 3)
        q, k, qk = R.mask_vec(u, 'q'), R.mask_vec(u, 'k'), R.mask_vec(u, 'qk')
        self.assertTrue(torch.equal(q + k, qk) and torch.equal(qk, u))
        self.assertEqual(float(q[:, 2048:].abs().sum()), 0.0)
        W = [torch.rand(4096, 3).double() for _ in range(14)]
        mu, rp = torch.randn(14, 4096, 3), torch.randn(14, 4096, 3)
        mu[0, :128] = 0                                                   # head (0, q, 0): mu contribution 0 -> a = 0
        rpost, a = RP.scale(mu, rp, W)
        hm, hp = RP.heads(RP.Lmap(mu, W)), RP.heads(RP.Lmap(rpost, W))
        self.assertTrue(torch.allclose(hm, hp, rtol=1e-5, atol=1e-6))
        self.assertEqual(float(a[0, 0, 0]), 0.0)
        rp2 = rp.clone()
        rp2[1, :128] = 0                                                  # random contribution 0 where mu is not -> failure
        with self.assertRaises(AssertionError):
            RP.scale(mu, rp2, W)

    def test_wiring(self):
        import qkf_run as R
        self.assertEqual(len(R.SCI_ARMS), 20)
        self.assertEqual(R.LIMITS['formal']['trajectories'], 48 * (1 + 3 * (1 + 20)))
        self.assertEqual(R.LIMITS['preflight']['trajectories'], 2 * (1 + 3 + 3 * 20 + 3 * 2))
        self.assertEqual(R.LIMITS['formal']['formations'], 48 * 4)
        self.assertEqual(set(R.QCO_REF.values()), {'V', 'F', 'R', 'A', 'R_rand', 'A_rand'})


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
