"""Offline tests for the frozen follow-up rules and sign convention (no data).  python test_fu.py"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'cache-b2-v-subset-q-dependence-v1-2026-11-01'))
import fu_core as K  # noqa: E402
import b2_core as B2  # noqa: E402
import torch  # noqa: E402


class Sign(unittest.TestCase):
    def test_K_equals_BH1(self):
        g = torch.Generator().manual_seed(0)
        Z = {c: float(torch.randn(1, generator=g)) for c in B2.CELLS}
        self.assertAlmostEqual(K.K(Z), B2.estimands(Z)['B_H1'])

    def test_local_sign_matches_output_interaction_in_linear_world(self):
        """If the readout is linear in core and the only Q x V_H interaction is the local write interaction I, then
        P_local == K(output) (removing I restores exactly the observed saturation)."""
        g = torch.Generator().manual_seed(1)
        W, u = torch.randn(6, 4, generator=g, dtype=torch.float64), torch.randn(6, generator=g, dtype=torch.float64)
        out = lambda c: W @ c   # noqa: E731
        base, aq, av, I = (torch.randn(4, generator=g, dtype=torch.float64) for _ in range(4))
        core = {'001': base, '101': base + aq, '011': base + av, '111': base + aq + av + I}   # q, h (R=T)
        z = {c: float(u @ out(v)) for c, v in core.items()}
        self.assertAlmostEqual(K.local_projection(core['111'], I, out, u), K.K(z), places=10)


class Rules(unittest.TestCase):
    def test_screen(self):
        s = {f'S{i}': (0.3, 0.25) for i in range(6)}
        self.assertEqual(K.screen(s)['decision'], 'candidate')
        s['S0'] = s['S1'] = (0.3, -0.1)
        self.assertEqual(K.screen(s)['decision'], 'no_candidate')
        self.assertEqual(K.screen({f'S{i}': (-0.3, -0.4) for i in range(6)})['decision'], 'reverse')
        self.assertEqual(K.screen({f'S{i}': (0.15, 0.15) for i in range(6)})['decision'], 'no_candidate')

    def test_decide(self):
        c, n = {'decision': 'candidate'}, {'decision': 'no_candidate'}
        self.assertEqual(K.decide(c, c), 'both_candidates')
        self.assertEqual(K.decide(c, n), 'local_write_candidate')
        self.assertEqual(K.decide(n, c), 'tail_27_31_candidate')
        self.assertEqual(K.decide(n, {'decision': 'reverse'}), 'no_qualified_candidate')

    def test_closure(self):
        self.assertTrue(K.closure_ok([1.0, 2.0, -0.5], 2.5)[0])
        self.assertFalse(K.closure_ok([1.0, 2.0, -0.5], 2.51)[0])


if __name__ == '__main__':
    unittest.main(verbosity=2)
