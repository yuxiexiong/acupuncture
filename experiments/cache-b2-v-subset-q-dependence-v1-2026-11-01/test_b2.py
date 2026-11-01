"""CPU tests for CFM-B2 (no weights, no CUDA).  CUDA_VISIBLE_DEVICES= python test_b2.py [RECEIPT_JSON]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import b2_core as K  # noqa: E402
import b2_analysis as A  # noqa: E402
import torch  # noqa: E402

H_LIST = [[30, j] for j in range(20)] + [[14, j] for j in range(25)]


def rnd(seed):
    return torch.randn(1, 8192, 4, generator=torch.Generator().manual_seed(seed)).to(torch.bfloat16)


class Conv(unittest.TestCase):
    def test_partition(self):
        H, R = K.partition(H_LIST)
        self.assertEqual((len(H), len(R)), (45, 403))
        with self.assertRaises(AssertionError):
            K.partition(H_LIST[:-1] + [H_LIST[0]])                        # duplicate
        with self.assertRaises(AssertionError):
            K.partition(H_LIST[:-1] + [[15, 0]])                          # full-attention layer is not a G layer

    def test_cells(self):
        H, _ = K.partition(H_LIST)
        fT, fC = rnd(1), rnd(2)
        for cell, (q, v) in {'000': (fC, fC), '100': (fT, fC), '011': (fC, fT), '111': (fT, fT)}.items():
            o = K.conv_cell(fT, fC, 30, cell, H)
            self.assertTrue(torch.equal(o[:, :4096], q[:, :4096]) and torch.equal(o[:, 4096:], v[:, 4096:]), cell)
        o = K.conv_cell(fT, fC, 30, '010', H)                             # only H heads from T, Q clean
        self.assertTrue(torch.equal(o[:, :4096], fC[:, :4096]))
        for j in range(32):
            a = 4096 + 128 * j
            want = fT if j < 20 else fC
            self.assertTrue(torch.equal(o[:, a:a + 128], want[:, a:a + 128]), j)
        o = K.conv_cell(fT, fC, 13, '001', H)                             # layer 13 has no H head: all R -> T
        self.assertTrue(torch.equal(o[:, 4096:], fT[:, 4096:]))
        self.assertEqual(K.donor_of(30, 3, '110', H), 'T')
        self.assertEqual(K.donor_of(30, 25, '110', H), 'C')


class Estimands(unittest.TestCase):
    def test_identities(self):
        g = torch.Generator().manual_seed(3)
        Z = {c: float(torch.randn(1, generator=g)) for c in K.CELLS}
        e = K.estimands(Z)
        for r in '01':
            self.assertAlmostEqual(e[f'B_H{r}'], e['A_H'][f'0{r}'] - e['A_H'][f'1{r}'])
        for h in '01':
            self.assertAlmostEqual(e[f'B_R{h}'], e['A_R'][f'0{h}'] - e['A_R'][f'1{h}'])
        self.assertAlmostEqual(e['J'], e['B_R0'] - e['B_R1'])
        self.assertAlmostEqual(e['L'], e['B_H0'] + e['B_R1'])

    def test_classify_and_judge(self):
        self.assertEqual(K.classify(0.3, 0.25), 'positive')
        self.assertEqual(K.classify(0.5, -0.05), 'intermediate')           # mean 0.225 but one fact <= 0
        self.assertEqual(K.classify(-0.3, -0.2), 'negative')
        self.assertEqual(K.classify(0.05, -0.15), 'small')
        self.assertEqual(K.classify(0.15, 0.15), 'intermediate')            # gap between 0.1 and 0.2
        s = {f'S{i}': (0.3, 0.3) for i in range(6)}
        self.assertEqual(K.judge(s)['decision'], 'stable_positive')
        s['S0'] = s['S1'] = (0.0, 0.0)
        self.assertEqual(K.judge(s)['decision'], 'unstable_or_partial')
        self.assertEqual(K.judge({f'S{i}': (0.01, -0.02) for i in range(6)})['decision'], 'stable_small')

    def test_ratio_rule(self):
        self.assertAlmostEqual(K.ratio((0.5, 0.7), (1.2, 1.0)), 0.6 / 1.1)
        self.assertIsNone(K.ratio((0.5, 0.7), (0.9, 0.9)))                   # |mean den| < 1
        self.assertIsNone(K.ratio((0.5, 0.7), (2.0, -0.1)))                  # denominators disagree in sign
        self.assertAlmostEqual(K.ratio((0.5, 0.5), (-1.5, -1.5)), -1 / 3)    # signed, no clipping


def synth(bh1):
    """Z = base + Q*1.5*(1 - V_total) + V effects; bh1 controls how much H restores Q's effect when R is T."""
    recs = []
    for s in ['VAR03', 'VAR04', 'VRD03', 'VRD04', 'VRL03', 'VRL04']:
        for k in (0, 1):
            cells = {}
            for c in K.CELLS:
                q, h, r = (int(x) for x in c)
                qeff = 1.5 if (h, r) == (0, 0) else (0.2 + bh1 if (h, r) == (0, 1) else 0.2)
                zs = 2.0 * h + 3.0 * r + q * qeff
                cells[c] = {'readout': {'primary': {'cz_s46': zs, 'cz_a': -zs}, 'eos': False}}
            recs.append({'item': {'id': f'{s}-f{k}', 'base_id': s}, 'cells': cells})
    return recs


class Consumer(unittest.TestCase):
    def test_positive_and_small(self):
        self.assertEqual(A.analyse(synth(0.5))['primary_decision'], 'stable_positive')
        res = A.analyse(synth(0.0))
        self.assertEqual(res['primary_decision'], 'stable_small')
        self.assertEqual(res['sides']['stop']['judged']['B_H0']['decision'], 'stable_positive')   # adding H alone suppresses Q
        self.assertEqual(res['sides']['answer']['judged']['B_H1']['decision'], 'stable_small')


class Wiring(unittest.TestCase):
    def test_plan_selection(self):
        import b2_run as V
        self.assertEqual([u['item_id'] for u in V.plan('preflight', 0, 1)], list(V.PREFLIGHT_ITEMS))
        w0, w1 = V.plan('formal', 0, 2), V.plan('formal', 1, 2)
        self.assertEqual(len(w0) + len(w1), 12)
        sel = V.selection()
        self.assertEqual(len(sel), 12)
        for v in sel.values():
            H, R = K.partition(v['H'])
            self.assertEqual(len(H) + len(R), 448)
        self.assertEqual(V.LIMITS['formal']['scores'], 96)
        self.assertEqual(V.LIMITS['preflight']['scores'], 20)


def main():
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    receipt = sys.argv[1] if len(sys.argv) > 1 else None
    res = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    if receipt:
        import hashlib
        repo = HERE.parent.parent
        src = {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.glob('*.py'))}
        with open(receipt, 'x') as f:
            json.dump({'status': 'passed' if res.wasSuccessful() else 'failed', 'tests_run': res.testsRun,
                       'failures': len(res.failures), 'errors': len(res.errors), 'skipped': len(res.skipped),
                       'source_hashes': src, 'torch': torch.__version__}, f, indent=2)
            f.write('\n')
    sys.exit(0 if res.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
