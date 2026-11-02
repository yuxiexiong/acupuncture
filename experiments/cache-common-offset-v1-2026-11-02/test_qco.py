"""CPU tests for QCO-01 (synthetic worlds that must pass AND fail each rule; offset math; edit arithmetic; wiring).
CUDA_VISIBLE_DEVICES= python test_qco.py [RECEIPT]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import qco_core as K  # noqa: E402
import qco_offsets as O  # noqa: E402

SC = [f'NQ0{k}' for k in range(1, 7)]
IDS = [f'{s}-{j}' for s in SC for j in range(8)]
SCEN = {i: i.split('-')[0] for i in IDS}


def world(R_fix=True, A_rep=True, rand=False, gap_scen=6):
    Y = {a: {} for a in ('V', 'F', 'R', 'A', 'R_rand', 'A_rand')}
    mA, mAr = {}, {}
    for i in IDS:
        s, j = SCEN[i], int(i.split('-')[1])
        damaged = j < 4 and SC.index(s) < gap_scen
        Y['F'][i], Y['V'][i] = 1, 0 if damaged else 1
        Y['R'][i] = 1 if (R_fix or not damaged) else 0
        Y['R_rand'][i] = Y['R'][i] if rand else Y['V'][i]
        Y['A'][i] = Y['V'][i]
        Y['A_rand'][i] = Y['V'][i]
        mA[i] = A_rep
        mAr[i] = A_rep if rand else False
    return Y, mA, mAr


class Judge(unittest.TestCase):
    def test_two_way(self):
        self.assertEqual(K.judge(*world(), SCEN)['verdict'], 'two_way')

    def test_partial_and_random(self):
        self.assertEqual(K.judge(*world(R_fix=False), SCEN)['verdict'], 'A_only')
        self.assertEqual(K.judge(*world(A_rep=False), SCEN)['verdict'], 'R_only')
        self.assertEqual(K.judge(*world(rand=True), SCEN)['verdict'], 'neither')       # random reference as good
        self.assertEqual(K.judge(*world(gap_scen=3), SCEN)['verdict'], 'not_applicable')  # gap in only 3 scenarios
        Y, m, mr = world()
        self.assertEqual(K.judge(Y, m, mr, SCEN, norm_ok_R=False)['verdict'], 'engineering_not_judgeable')

    def test_breakage_counts_against_P(self):
        Y, m, mr = world()
        for i in IDS:                                       # R fixes damaged cells but breaks every intact cell
            if Y['V'][i] == 1:
                Y['R'][i] = 0
        r = K.judge(Y, m, mr, SCEN)
        self.assertLess(r['P'], 0.5)


class Offsets(unittest.TestCase):
    def test_leave_one_out(self):
        import torch
        dirs = ('d',)
        delta = {}
        for k, s in enumerate(SC):
            for j in range(2 if s in ('NQ02', 'NQ04') else 3):
                delta[(f'{s}-{j}', 'd')] = torch.full((14, 4096, 3), float(k))
        scen = {i: i.split('-')[0] for i, _ in delta}
        mu = O.leave_one_out(delta, scen, dirs)
        for k, s in enumerate(SC):                          # mean over the other five scenario means, unequal sizes do not weight
            want = (sum(range(6)) - k) / 5
            self.assertAlmostEqual(float(mu[(s, 'd')][0, 0, 0]), want, places=5)

    def test_random_scaling_and_seed(self):
        import torch
        mu = torch.zeros(14, 4096, 3)
        mu[0, :2048, 0] = 2.0
        r1, r2 = O.random_like(mu, 'NQ01', 'd'), O.random_like(mu, 'NQ01', 'd')
        self.assertTrue(torch.equal(r1, r2))
        self.assertAlmostEqual(float(r1[0, :2048, 0].norm()), float(mu[0, :2048, 0].norm()), places=3)
        self.assertEqual(float(r1[0, 2048:, 0].abs().sum()), 0.0)                 # zero mu block -> zero r block
        self.assertFalse(torch.equal(O.random_like(mu, 'NQ02', 'd'), r1))


class Edit(unittest.TestCase):
    def test_edit_block(self):
        import torch
        import qco_run as R
        q = torch.randn(1, 4096, 4).to(torch.bfloat16)
        v = torch.randn(4096, 3)
        new, sq = R.edit_block(q, v, -1)
        self.assertTrue(torch.equal(new[0, :, 0], q[0, :, 0]))
        self.assertTrue(torch.equal(new[0, :, 1:], (q[0, :, 1:].float() - v).to(torch.bfloat16)))
        self.assertAlmostEqual(sq, float((new[0, :, 1:].float() - q[0, :, 1:].float()).pow(2).sum()), places=3)
        z, sz = R.edit_block(q, torch.zeros(4096, 3), 1)
        self.assertTrue(torch.equal(z, q))
        self.assertEqual(sz, 0.0)

    def test_wiring(self):
        import qco_run as R
        p0, p1 = R.plan('formal', 0, 2), R.plan('formal', 1, 2)
        self.assertEqual(len(p0) + len(p1), 48)
        self.assertEqual(R.LIMITS['formal']['trajectories'], 48 * 4 * 6 + 48 + 192)
        self.assertEqual(R.LIMITS['preflight']['trajectories'], 2 * (1 + 4 * 3 + 8))
        self.assertEqual(R.LIMITS['collect']['formations'], 48 * 5)


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
