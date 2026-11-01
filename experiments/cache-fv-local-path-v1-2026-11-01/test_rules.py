"""Offline pass/fail demos for PLAN §5 rules and helpers (no data).  CUDA_VISIBLE_DEVICES= python test_rules.py"""
import os
import sys
import unittest
from pathlib import Path
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '')
sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze as A  # noqa: E402
import torch  # noqa: E402


def summ(n_conc, n_g, m_conc=0, m_g=0):
    return {'N|s46': {'n_conc_pass': n_conc, 'n_gsupp_pass': n_g}, 'M_T|s46': {'n_conc_pass': m_conc, 'n_gsupp_pass': m_g}}


class Rules(unittest.TestCase):
    def test_decide(self):
        self.assertEqual(A.decide(summ(5, 0))['decision'], 'candidates')
        self.assertTrue(A.decide(summ(0, 6))['gating_candidate'])
        d = A.decide(summ(4, 4, 6, 6))
        self.assertEqual(d['decision'], 'no_head_or_gating_candidate')
        self.assertTrue(d['mixed_leads']['head_subset'] and d['mixed_leads']['gating'])

    def test_spearman(self):
        x = torch.arange(10, dtype=torch.float64)
        self.assertAlmostEqual(A.spearman(x, x * 3 + 1), 1.0)
        self.assertAlmostEqual(A.spearman(x, -x), -1.0)

    def test_gnorm_head_separable(self):
        c = torch.randn(4, 8, dtype=torch.float64, generator=torch.Generator().manual_seed(0))
        w, g = torch.ones(8, dtype=torch.float64), torch.rand(4, 8, dtype=torch.float64, generator=torch.Generator().manual_seed(1))
        c2 = c.clone(); c2[1] += 0.3
        y1, _ = A.gnorm(c, w, g, 1e-6); y2, _ = A.gnorm(c2, w, g, 1e-6)
        self.assertTrue(torch.equal(y1[[0, 2, 3]], y2[[0, 2, 3]]))        # changing one head leaves others untouched


if __name__ == '__main__':
    unittest.main(verbosity=2)
