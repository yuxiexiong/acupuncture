"""CPU tests for CFM-LOCAL-READOUT v1 (no model weights, no CUDA).

CUDA_VISIBLE_DEVICES= python test_local_readout.py [RECEIPT_JSON]
"""
import json
import math
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lr_core as K  # noqa: E402
import lr_analysis as A  # noqa: E402

import torch  # noqa: E402


def rnd(*shape, seed=0, dtype=torch.float64):
    g = torch.Generator().manual_seed(seed)
    return torch.randn(*shape, generator=g, dtype=torch.float64).to(dtype)


class Algebra(unittest.TestCase):
    def test_matches_real_kernel(self):
        """o = S^T w + n reproduces the real transformers recurrent kernel for one token (plan §5)."""
        import transformers.models.qwen3_5.modeling_qwen3_5 as qm
        H, d = 4, 8
        q, k, v = rnd(1, 1, H, d, seed=1), rnd(1, 1, H, d, seed=2), rnd(1, 1, H, d, seed=3)
        g = -rnd(1, 1, H, seed=4).abs()
        beta = torch.sigmoid(rnd(1, 1, H, seed=5))
        S = rnd(1, H, d, d, seed=6)
        fn = getattr(qm.torch_recurrent_gated_delta_rule, '__wrapped__', qm.torch_recurrent_gated_delta_rule)
        core, _ = fn(q, k, v, g=g, beta=beta, initial_state=S.clone(), output_final_state=True, use_qk_l2norm_in_kernel=True)
        row = {'q': q[0, 0], 'k': k[0, 0], 'v': v[0, 0], 'g': g[0, 0], 'beta': beta[0, 0]}
        w, n = K.weights(row)
        o = K.read(S[0], w) + n
        self.assertLess(K.rel(o, core[0, 0].double()), 1e-5)

    def test_four_cells_identity(self):
        H, d = 4, 8
        sc, st = rnd(H, d, d, seed=1), rnd(H, d, d, seed=2)
        base = {'g': -rnd(H, seed=3).abs(), 'beta': torch.sigmoid(rnd(H, seed=4))}
        r0 = {**base, 'q': rnd(H, d, seed=5), 'k': rnd(H, d, seed=6), 'v': rnd(H, d, seed=7)}
        r1 = {**base, 'q': rnd(H, d, seed=8), 'k': rnd(H, d, seed=9), 'v': rnd(H, d, seed=10)}
        f = K.four_cells(sc, st, r0, r1)
        self.assertTrue(f['identity_ok'])
        self.assertLess(f['J_split_residual'], 1e-12)
        self.assertGreater(f['norms']['I'], 0)
        # same F on both sides -> I is exactly zero (no read change), J = A_S
        f0 = K.four_cells(sc, st, r0, r0)
        self.assertEqual(f0['norms']['I'], 0.0)
        self.assertTrue(f0['identity_ok'])
        # same S -> I zero
        self.assertLess(K.four_cells(sc, sc, r0, r1)['norms']['I'], 1e-15)   # four-corner FP64 roundoff only

    def test_entry_mismatch_rejected(self):
        H, d = 2, 4
        r0 = {'g': torch.zeros(H, dtype=torch.float64), 'beta': torch.ones(H, dtype=torch.float64) / 2,
              'q': rnd(H, d, seed=1), 'k': rnd(H, d, seed=2), 'v': rnd(H, d, seed=3)}
        r1 = dict(r0, g=r0['g'] - 0.1)
        with self.assertRaises(AssertionError):
            K.four_cells(rnd(H, d, d, seed=4), rnd(H, d, d, seed=5), r0, r1)


class PatchArithmetic(unittest.TestCase):
    def setUp(self):
        self.core = (rnd(32, 128, seed=11) * 5.5e-4).to(torch.bfloat16)   # norm ~0.035 like real layer-13 core

    def test_zero_and_addback_bitwise(self):
        z = K.patch_core(self.core, torch.zeros(32, 128, dtype=torch.float64))
        self.assertTrue(torch.equal(z, self.core))
        d = rnd(32, 128, seed=12) * 1.1e-4
        self.assertTrue(torch.equal(K.patch_core(self.core, d, addback=True), self.core))

    def test_deletion_gate_can_pass_and_fail(self):
        d = rnd(32, 128, seed=13) * 1.1e-4                    # norm ~0.007, ~20% of core, like I_M
        new = K.patch_core(self.core, d)
        self.assertLess(K.realized(self.core, new, d)['rel_err'], K.TOL['deletion_rel'])
        tiny = d * 1e-3                                        # below BF16 resolution -> undecidable
        new = K.patch_core(self.core, tiny)
        self.assertGreater(K.realized(self.core, new, tiny)['rel_err'], K.TOL['deletion_rel'])


class RandomRefs(unittest.TestCase):
    def test_deterministic_and_matched(self):
        u0, u0b, u1 = K.unit_dirs('X', 0), K.unit_dirs('X', 0), K.unit_dirs('X', 1)
        self.assertTrue(torch.equal(u0, u0b))
        self.assertFalse(torch.equal(u0, u1))
        target = rnd(32, 128, seed=3)
        target[5] = 0
        q = K.match_heads(u0, target)
        self.assertTrue(torch.allclose(q.norm(dim=-1), target.norm(dim=-1), rtol=1e-12, atol=1e-15))
        self.assertEqual(float(q[5].abs().max()), 0.0)
        self.assertEqual(K.seed_of('X', 0), int(__import__('hashlib').sha256(b'CFM-LOCAL-READOUT-v1|X|0').hexdigest()[:16], 16))


SC = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6']


def mk(vals):
    return dict(zip(SC, vals))


class Tiers(unittest.TestCase):
    gap = mk([16.0] * 6)

    def test_null_tail(self):
        self.assertAlmostEqual(K.null_tail(), 13 / 729, places=12)
        self.assertAlmostEqual(K.null_tail(4), 73 / 729, places=12)

    def test_clear_push_reachable_and_breakable(self):
        dI, q = mk([2.0] * 6), mk([0.5] * 6)
        self.assertEqual(K.tier_I(dI, q, q, self.gap)['label'], 'clear_push')
        # e = 4 only -> not clear
        q2 = mk([0.5, 0.5, 0.5, 0.5, 3.0, 3.0])
        self.assertEqual(K.tier_I(dI, q2, q, self.gap)['label'], 'nonspecific_or_unstable')
        # direction 4/6 -> not clear
        dI2 = mk([2.0, 2.0, 2.0, 2.0, -2.0, -2.0])
        self.assertEqual(K.tier_I(dI2, q, q, self.gap)['label'], 'nonspecific_or_unstable')
        # median ratio 0.04 -> weak
        dI3 = mk([0.64] * 6)
        self.assertEqual(K.tier_I(dI3, mk([0.1] * 6), mk([0.1] * 6), self.gap)['label'], 'weak')

    def test_clear_suppress(self):
        dI, q = mk([-2.0] * 6), mk([0.5] * 6)
        self.assertEqual(K.tier_I(dI, q, q, self.gap)['label'], 'clear_suppress')

    def test_small_gap_excluded_from_ratio(self):
        gap = mk([16.0] * 5 + [0.5])
        t = K.tier_I(mk([2.0] * 6), mk([0.5] * 6), mk([0.5] * 6), gap)
        self.assertIsNone(t['ratios']['S6'])
        self.assertEqual(t['n_ratio'], 5)

    def test_J(self):
        self.assertEqual(K.tier_J(mk([3.0] * 6), self.gap)['label'], 'magnitude_clear_uncalibrated')
        self.assertEqual(K.tier_J(mk([0.1] * 6), self.gap)['label'], 'weak')
        self.assertEqual(K.tier_J(mk([3.0, 3.0, 3.0, -3.0, -3.0, -3.0]), self.gap)['label'], 'unstable')

    def test_contrast(self):
        self.assertEqual(K.background_contrast('clear_push', 'weak'), 'only_M')
        self.assertEqual(K.background_contrast('weak', 'clear_push'), 'only_N')
        self.assertEqual(K.background_contrast('clear_push', 'clear_suppress'), 'both_clear_opposite')
        self.assertEqual(K.background_contrast('nonspecific_or_unstable', 'weak'), 'no_background_claim')


def synthetic_record(item_id, base, dI, dJ, dq0, dq1, gap=16.0, undecidable=()):
    """A record with exactly the fields lr_analysis consumes, produced through lr_core.cell_readout as the run does."""
    stop = [0, 1]
    readout = {}
    for bg in ('M', 'N'):
        base_logits = torch.zeros(10, dtype=torch.float32)
        base_logits[0], base_logits[1], base_logits[5] = 1.0, -100.0, 3.0   # D_R = -2; stop id 1 never wins
        ro_r = K.cell_readout(base_logits, stop, 0, 5, 1.0, 1.0)
        readout[f'{bg}:R'] = ro_r
        for x, dd in (('mI', dI), ('mJ', dJ), ('Q0', dq0), ('Q1', dq1)):
            z = base_logits.clone()
            z[0] -= dd
            readout[f'{bg}:{x}'] = K.cell_readout(z, stop, 0, 5, 1.0, 1.0)
        readout[f'{bg}:gap_to_C'] = gap
    numerics = {f'{bg}:{x}': {'decidable': f'{bg}:{x}' not in undecidable} for bg in ('M', 'N') for x in A.DELS}
    local = {bg: {'norms': {'I': 0.007, 'J': 0.017}, 'cos_I_vs_AS_plus_AF': -0.2} for bg in ('M', 'N')}
    return {'item': {'id': item_id, 'base_id': base}, 'readout': readout, 'numerics': numerics, 'local_components': local}


class AnalysisConsumer(unittest.TestCase):
    def records(self, dI, **kw):
        return [synthetic_record(f'{s}-f{k}', s, dI, 0.1, 0.2, 0.2, **kw) for s in SC for k in (0, 1)]

    def test_push_detected(self):
        res = A.analyse(self.records(2.0))
        self.assertEqual(res['backgrounds']['M']['tier_I']['label'], 'clear_push')
        self.assertEqual(res['background_contrast'], 'both_clear')
        self.assertAlmostEqual(res['backgrounds']['N']['scenario_dD']['mI']['S1'], 2.0, places=5)

    def test_weak_detected(self):
        res = A.analyse(self.records(0.01))
        self.assertEqual(res['backgrounds']['N']['tier_I']['label'], 'weak')
        self.assertEqual(res['background_contrast'], 'no_background_claim')

    def test_undecidable_propagates(self):
        res = A.analyse(self.records(2.0, undecidable=('M:mI',)))
        self.assertEqual(res['backgrounds']['M']['tier_I']['label'], 'numerically_undecidable')
        self.assertEqual(res['backgrounds']['N']['tier_I']['label'], 'clear_push')


class Wiring(unittest.TestCase):
    """Model-side pieces exercised on toy modules (imports the frozen bridge/combo chain; no weights)."""

    @classmethod
    def setUpClass(cls):
        import local_readout as LR
        cls.LR = LR

    def test_plan(self):
        pre = self.LR.plan('preflight', 0, 1)
        self.assertEqual([u['item_id'] for u in pre], list(self.LR.PREFLIGHT_ITEMS))
        w0, w1 = self.LR.plan('formal', 0, 2), self.LR.plan('formal', 1, 2)
        ids = [u['item_id'] for u in w0 + w1]
        self.assertEqual(len(ids), 12)
        self.assertEqual(len(set(ids)), 12)
        self.assertFalse({u['base_id'] for u in w0} & {u['base_id'] for u in w1})

    def test_patch_wrapper(self):
        p = self.LR.Patch(None)
        core = (rnd(1, 1, 32, 128, seed=1) * 0.003).to(torch.bfloat16)
        s_new = rnd(1, 32, 128, 128, seed=2).float()
        fake = lambda *a, **k: (core.clone(), s_new)   # noqa: E731
        inner = p._wrap(fake)
        q = torch.zeros(1, 1, 32, 128)
        d = rnd(32, 128, seed=3) * 6e-4
        p.set('a', d)
        out, s = inner(q)                                # outside layer 13: untouched, not counted
        self.assertTrue(torch.equal(out, core))
        self.assertEqual(p.info['a']['hits'], 0)
        p.inside = True
        out, s = inner(q)
        self.assertIs(s, s_new)
        self.assertEqual(p.info['a']['hits'], 1)
        self.assertLess(p.info['a']['rel_err'], 0.05)
        self.assertFalse(p.info['a']['bitwise_unchanged'])
        p.set('b', d, addback=True)
        out, _ = inner(q)
        self.assertTrue(torch.equal(out, core))
        self.assertTrue(p.info['b']['bitwise_unchanged'])
        p.set('c', None)
        out, _ = inner(q)
        self.assertTrue(torch.equal(out, core))
        with self.assertRaises(AssertionError):
            p.set('d', d)
            inner(torch.zeros(1, 2, 32, 128))

    def test_entry_hook(self):
        class Block(torch.nn.Module):
            def forward(self, h, *rest):
                return h * 1

        class Toy(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.model = torch.nn.Module()
                self.model.layers = torch.nn.ModuleList([Block() for _ in range(14)])
        m = Toy()
        x = torch.arange(6, dtype=torch.float32)
        h = torch.zeros(1, 1, 6)
        with self.LR.Entry(m, x) as e:
            out = m.model.layers[13](h, 'pos')
            other = m.model.layers[12](h)
        self.assertTrue(torch.equal(out[0, -1], x))
        self.assertTrue(torch.equal(other, h))
        self.assertEqual(e.hits, 1)
        self.assertTrue(torch.equal(m.model.layers[13](h), h))   # removed on exit


def main():
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    receipt = sys.argv[1] if len(sys.argv) > 1 else None
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    res = unittest.TextTestRunner(verbosity=2).run(suite)
    if receipt:
        import hashlib
        repo = HERE.parent.parent
        src = {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.glob('*.py'))}
        Path(receipt).parent.mkdir(parents=True, exist_ok=True)
        with open(receipt, 'x') as f:
            json.dump({'status': 'passed' if res.wasSuccessful() else 'failed', 'tests_run': res.testsRun,
                       'failures': len(res.failures), 'errors': len(res.errors), 'skipped': len(res.skipped),
                       'source_hashes': src, 'torch': torch.__version__}, f, indent=2)
            f.write('\n')
    sys.exit(0 if res.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
