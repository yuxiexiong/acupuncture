"""CPU tests for QKD-01 (label rule pass/fail; D/E/W decomposition vs the real torch kernel; J+H identity; wiring).
CUDA_VISIBLE_DEVICES= python test_qkd.py [RECEIPT]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import qkd_core as K  # noqa: E402

SC = [f'NQ0{k}' for k in range(1, 7)]
IDS = [f'{s}-{j}' for s in SC for j in range(4)]
SCEN = {i: i.split('-')[0] for i in IDS}


class Labels(unittest.TestCase):
    def test_label(self):
        self.assertEqual(K.label({i: 0.1 for i in IDS}, {i: 0.9 for i in IDS}, SCEN)['label'], 'H_dominant')
        self.assertEqual(K.label({i: 0.9 for i in IDS}, {i: 0.1 for i in IDS}, SCEN)['label'], 'J_dominant')
        self.assertEqual(K.label({i: 0.4 for i in IDS}, {i: 0.6 for i in IDS}, SCEN)['label'], 'neither')          # below 0.75
        mixed = {i: (0.9 if SCEN[i] in SC[:3] else 0.1) for i in IDS}
        self.assertEqual(K.label({i: 1 - mixed[i] for i in IDS}, mixed, SCEN)['label'], 'neither')               # 3/6 scenarios
        self.assertEqual(K.label({i: None for i in IDS}, {i: None for i in IDS}, SCEN)['label'], 'not_resolvable')

    def test_err_threshold(self):
        self.assertEqual(K.err_threshold(0.003), 0.006)
        self.assertEqual(K.err_threshold(0.5), 0.02)
        self.assertEqual(K.err_threshold(0.0), 1e-5)


def fake_call(torch, seed, k=None):
    g = torch.Generator().manual_seed(seed)
    q = torch.randn(1, 1, 32, 128, generator=g)
    kk = torch.randn(1, 1, 32, 128, generator=g) if k is None else k
    v = torch.randn(1, 1, 32, 128, generator=g)
    gg = -torch.rand(1, 1, 32, generator=g)
    b = torch.rand(1, 1, 32, generator=g)
    S = torch.randn(1, 32, 128, 128, generator=g) * 0.1
    return q, kk, v, gg, b, S


class Decomposition(unittest.TestCase):
    def test_vs_kernel_and_pair_identity(self):
        import torch
        import qkd_run as R
        orig = R.gdn_module().torch_recurrent_gated_delta_rule
        q, k, v, g, b, S = fake_call(torch, 0)
        o, _ = orig(q, k, v, g=g, beta=b, initial_state=S.clone(), output_final_state=True, use_qk_l2norm_in_kernel=True)
        c = {'q': q, 'k': k, 'v': v, 'g': g, 'beta': b, 'S': S, 'o': o, 'l2': True}
        d = R.decompose(c, orig)
        self.assertTrue(d['wired'])
        self.assertLess(float(d['err'].max()), 1e-5)
        # same q, S, v, a, b; different k -> actual difference equals J + H exactly (FP64 arithmetic identity)
        k2 = torch.randn(1, 1, 32, 128, generator=torch.Generator().manual_seed(9))
        o2, _ = orig(q, k2, v, g=g, beta=b, initial_state=S.clone(), output_final_state=True, use_qk_l2norm_in_kernel=True)
        d2 = R.decompose({'q': q, 'k': k2, 'v': v, 'g': g, 'beta': b, 'S': S, 'o': o2, 'l2': True}, orig)
        for x in (d, d2):                                   # replace o by the exact FP64 sum so the identity is tested alone
            x['o'] = x['D'] + x['E'] + x['W']
            x['abs_err'] = x['abs_err'] * 0
        st = R.pair_stats(d, d2)
        F_ = R.PAIR_FIELDS
        self.assertLess(float(st[:, F_.index('n_res')].max() / st[:, F_.index('n_dact')].max()), 1e-10)
        self.assertTrue(bool(((st[:, F_.index('sJ')] + st[:, F_.index('sH')]) - 1).abs().max() < 1e-9))
        self.assertTrue(bool((st[:, F_.index('sD')]).abs().max() < 1e-9))           # D does not depend on k
        # alpha = 0 (g -> -inf): E vanishes, H vanishes
        q3, k3, v3, g3, b3, S3 = fake_call(torch, 3)
        g3 = torch.full_like(g3, -1e4)
        o3, _ = orig(q3, k3, v3, g=g3, beta=b3, initial_state=S3.clone(), output_final_state=True, use_qk_l2norm_in_kernel=True)
        d3 = R.decompose({'q': q3, 'k': k3, 'v': v3, 'g': g3, 'beta': b3, 'S': S3, 'o': o3, 'l2': True}, orig)
        self.assertLess(float(d3['E'].abs().max()), 1e-12)

    def test_wiring(self):
        import qkd_run as R
        ki = R.kernel_identity()
        self.assertFalse(ki['fla'] or ki['kernels'] or ki['causal_conv1d'])
        self.assertEqual(R.LIMITS['formal']['decode_forwards'], 48 * 6 * 32 + 48 * 4 * 6 * 3 + 48 * 4 * 6 * 2)
        self.assertEqual(R.LIMITS['preflight']['decode_forwards'], 2 * 6 * 32 + 2 * 4 * 6 * (3 + 2 + 3))
        self.assertEqual(R.LIMITS['formal']['formations'], 48 * 5)


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
