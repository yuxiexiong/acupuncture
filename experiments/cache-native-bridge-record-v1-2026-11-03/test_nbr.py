"""CPU tests for NBR-01: D + E + W == replicated original read (pre-cast) and the cast output == original kernel; endpoint differences and
interaction from synthetic states; local formula exact when the four cells share inputs; same-q read == manual; zero-leaf gradient is the total
derivative; budget.  CUDA_VISIBLE_DEVICES= python test_nbr.py [RECEIPT]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import nbr_core as NB  # noqa: E402


class Core(unittest.TestCase):
    def setUp(self):
        import torch
        import nbr_run as R
        self.R, self.torch = R, torch
        self.QM = R.gdn_module()
        g = torch.Generator().manual_seed(11)
        self.rnd = lambda *s: torch.randn(*s, generator=g)   # noqa: E731
        self.q, self.k, self.v = [self.rnd(1, 1, 32, 128).to(torch.bfloat16) for _ in range(3)]
        self.g, self.beta = -torch.rand(1, 1, 32, generator=g), torch.rand(1, 1, 32, generator=g).to(torch.bfloat16)
        self.S = self.rnd(1, 32, 128, 128) * 0.1

    def test_dew_matches_original(self):
        R, torch = self.R, self.torch
        orig = self.QM.torch_recurrent_gated_delta_rule
        o0, _ = orig(self.q, self.k, self.v, g=self.g, beta=self.beta, initial_state=self.S.clone(), output_final_state=True, use_qk_l2norm_in_kernel=True)
        o_ru, _, pre, _, _ = R.SRUR.read_use(self.q, self.k, self.v, self.g, self.beta, self.S, self.S, 0, 0, self.QM.l2norm)
        self.assertTrue(R.bit_equal(o_ru, o0)[0])
        qn, kn, vv, al, bt, kq = NB.reader(self.q, self.k, self.v, self.g, self.beta, self.QM.l2norm)
        D, E, W = NB.dew(self.S, qn, kn, vv, al, bt, kq)
        ref = pre[:, :, 0].double()
        self.assertLessEqual(float(((D + E + W) - ref).abs().max() / max(1.0, float(ref.abs().max()))), R.DEW_TOL)
        self.assertGreater(float(((D + W) - ref).abs().max()), 1e-4)          # E is not negligible -> the check can fail

    def test_state_diffs_and_local(self):
        torch = self.torch
        base = self.rnd(1, 4, 8, 8)
        k0, k1 = [torch.nn.functional.normalize(self.rnd(1, 4, 8), dim=-1) for _ in range(2)]
        v0, v1 = self.rnd(1, 4, 8), self.rnd(1, 4, 8)
        bt = torch.rand(1, 4)
        def st(k, v):
            return base + bt[..., None, None] * k.unsqueeze(-1) * v.unsqueeze(-2)
        S = {}
        for c in '01':
            for a in '01':
                for b in '01':
                    S[c + a + b] = {13: st(k1 if b == '1' else k0, v1 if a == '1' else v0)}
        L = NB.local_I(bt, k0, k1, v0, v1)
        row, dd = NB.state_stats(S, 13, L, L)
        f = {n: i for i, n in enumerate(NB.FIELDS)}
        self.assertLess(float(row[:, f['res0']].max()), 1e-5)                 # local formula exact when inputs coincide
        self.assertGreater(float(row[:, f['cosI']].min()), 0.9999)
        self.assertLess(float(row[:, f['nI1mI0']].max()), 1e-6)
        S['111'] = {13: S['111'][13] + 0.5 * self.rnd(1, 4, 8, 8)}            # background 1 differs -> residual and difference appear
        row2, _ = NB.state_stats(S, 13, L, L)
        self.assertGreater(float(row2[:, f['res1']].min()), 1e-3)
        self.assertGreater(float(row2[:, f['nI1mI0']].min()), 1e-3)
        self.assertLess(float(row2[:, f['res0']].max()), 1e-5)

    def test_read(self):
        torch = self.torch
        X, q, al = self.rnd(1, 4, 8, 6), self.rnd(1, 4, 8), torch.rand(1, 4)
        r = NB.read(X, q, al)
        man = torch.stack([al[0, h].double() * (X[0, h].double().T @ q[0, h].double()) for h in range(4)])
        self.assertTrue(torch.allclose(r[0], man))
        self.assertAlmostEqual(NB.proj(torch.ones(4, 6), r[0]), float(man.sum()), places=6)

    def test_zero_leaf_total_derivative(self):
        torch = self.torch
        x = torch.tensor(1.5)
        e1 = torch.zeros((), requires_grad=True)
        e2 = torch.zeros((), requires_grad=True)
        h1 = torch.sin(x) + e1                 # layer-1 output with leaf
        h2 = h1 * h1 + e2                      # layer-2 output depends on layer 1
        M = 3 * h2 + h1
        g1, g2 = torch.autograd.grad(M, [e1, e2])
        self.assertAlmostEqual(float(g1), 3 * 2 * float(torch.sin(x)) + 1, places=5)    # total: through h2 and directly
        self.assertAlmostEqual(float(g2), 3.0, places=6)
        self.assertEqual(float(h1.detach()), float(torch.sin(x)))           # values unchanged by zero leaves


class GradPath(unittest.TestCase):
    def test_inplace_cache_write_after_read(self):
        """Real torch kernel with the CapHook private-copy rule: backward works after the cache is overwritten in place and the output value
        is unchanged.  (The failure itself only appears on the model path; it is reproduced by readiness/grad_smoke.py, not here.)"""
        import torch
        import nbr_run as R
        QM = R.gdn_module()
        orig = QM.torch_recurrent_gated_delta_rule
        g = torch.Generator().manual_seed(3)
        q, k, v = [torch.randn(1, 1, 4, 16, generator=g) for _ in range(3)]
        gg, b = -torch.rand(1, 1, 4, generator=g), torch.rand(1, 1, 4, generator=g)
        def run(private):
            cache = torch.randn(1, 4, 16, 16, generator=torch.Generator().manual_seed(5))
            qq = q.clone().requires_grad_(True)
            st = cache.detach().clone() if private else cache
            o, S = orig(qq, k, v, g=gg, beta=b, initial_state=st, output_final_state=True, use_qk_l2norm_in_kernel=True)
            cache.copy_(S.detach())                                        # cache update in place
            (gq,) = torch.autograd.grad(o.sum(), [qq])
            return o.detach(), gq
        cache0 = torch.randn(1, 4, 16, 16, generator=torch.Generator().manual_seed(5))
        o1, g1 = run(True)
        o2, _ = orig(q, k, v, g=gg, beta=b, initial_state=cache0.clone(), output_final_state=True, use_qk_l2norm_in_kernel=True)
        self.assertTrue(torch.equal(o1, o2))
        self.assertTrue(torch.isfinite(g1).all())


class Wiring(unittest.TestCase):
    def test_budget(self):
        import nbr_run as R
        f, p = R.LIMITS['formal'], R.LIMITS['preflight']
        self.assertEqual((f['t1'], f['c_t2'], f['grad'], f['decode_forwards']), (1536, 1536, 1536, 4608))
        self.assertEqual(p['decode_forwards'], 192)
        self.assertEqual(f['shadow'], 140 * 4 * 48)
        self.assertAlmostEqual(R.GPU_CAP_S['formal'] + 2 * R.GPU_CAP_S['preflight'], 0.8 * 3600)
        self.assertEqual(len(R.plan('formal', 0, 2)) + len(R.plan('formal', 1, 2)), 48)
        self.assertEqual(len(NB.FIELDS), 18)


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
