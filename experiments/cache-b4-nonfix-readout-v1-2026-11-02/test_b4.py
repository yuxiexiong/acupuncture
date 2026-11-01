"""CPU tests for B4 (no weights).  CUDA_VISIBLE_DEVICES= python test_b4.py [RECEIPT_JSON]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import torch  # noqa: E402
import b4_core as K  # noqa: E402
import b4_hooks as H  # noqa: E402
import b4_analysis as A  # noqa: E402


class Axes(unittest.TestCase):
    def test_axis_a_boundaries(self):
        self.assertEqual(K.axis_a(0.5), 'strong_reduction')
        self.assertEqual(K.axis_a(0.5001), 'moderate_reduction')
        self.assertEqual(K.axis_a(0.8), 'moderate_reduction')
        self.assertEqual(K.axis_a(0.8001), 'below_change_threshold')
        self.assertEqual(K.axis_a(1.1999), 'below_change_threshold')
        self.assertEqual(K.axis_a(1.2), 'reverse_enhancement')
        self.assertEqual(K.axis_a(None), 'denominator_insufficient')
        self.assertEqual(K.axis_a_main(0.8), 'reduced')
        self.assertEqual(K.axis_a_main(0.81), 'not_reduced')
        self.assertIsNone(K.rho(0.5, 0.99))
        self.assertAlmostEqual(K.rho(0.5, 1.0), 0.5)

    def test_axis_b(self):
        self.assertEqual(K.axis_b(0.3, 0.5, 0.5), 'exceeds_both')               # d = +0.2 exactly counts as exceeding
        self.assertEqual(K.axis_b(0.3, 0.5, 0.4), 'exceeds_one')
        self.assertEqual(K.axis_b(0.3, 0.4, 0.35), 'close_to_both')
        self.assertEqual(K.axis_b(0.5, 0.3, 0.45), 'other')                     # d = -0.2 -> other
        self.assertEqual(K.axis_b(0.3, None, 0.9), 'comparison_insufficient')
        self.assertEqual(K.axis_b(None, 0.9, 0.9), 'denominator_insufficient')

    def test_labels_and_joint(self):
        strong = {f'P0{s}': ('strong_reduction', 'strong_reduction') for s in range(1, 7)}
        exc = {f'P0{s}': ('exceeds_both', 'exceeds_both') for s in range(1, 7)}
        self.assertEqual(len(K.joint_scenarios(strong, exc)), 6)
        # axis A passes in scenarios 1-3 only, axis B in 4-6 only: joint must not stitch them
        a = {f'P0{s}': ('strong_reduction',) * 2 if s <= 3 else ('moderate_reduction',) * 2 for s in range(1, 7)}
        b = {f'P0{s}': ('exceeds_both',) * 2 if s >= 4 else ('close_to_both',) * 2 for s in range(1, 7)}
        self.assertEqual(K.joint_scenarios(a, b), [])
        self.assertFalse(K.joint_label({d: 0 for d in range(4)}))
        self.assertTrue(K.joint_label({0: 6, 1: 5, 2: 5, 3: 0}))
        lab, _ = K.direction_label({f'P0{s}': ('x', 'x') if s <= 5 else ('x', 'y') for s in range(1, 7)})
        self.assertEqual(lab, 'x')
        lab, _ = K.direction_label({f'P0{s}': ('x', 'x') if s <= 4 else ('x', 'y') for s in range(1, 7)})
        self.assertIsNone(lab)
        self.assertEqual(K.cross_label({0: 'a', 1: 'a', 2: 'a', 3: None}), 'a')
        self.assertEqual(K.cross_label({0: 'a', 1: 'a', 2: 'b', 3: None}), 'condition_dependent')

    def test_predictions(self):
        ids = [f'P0{s}-f{f}' for s in range(1, 7) for f in (0, 1)]
        rk = {d: {i: 0.4 for i in ids} for d in range(4)}
        rs = {d: {i: 0.5 for i in ids} for d in range(4)}
        p = K.predictions(rk, rs)
        self.assertTrue(p['P1'] and p['P2'])
        rk = {d: {i: 0.95 for i in ids} for d in range(4)}
        p = K.predictions(rk, rs)
        self.assertFalse(p['P1'] or p['P2'])


class Matching(unittest.TestCase):
    def test_template_and_scale(self):
        torch.manual_seed(0)
        W = torch.randn(16, K.NV * K.HD)
        mask = torch.tensor([h % 3 != 0 for h in range(K.NV)])
        target = torch.rand(K.NV) * mask
        raw = torch.randn(K.NV, K.HD)
        v, ok = K.build_template(raw, target, mask)
        self.assertTrue(ok)
        self.assertTrue(torch.allclose(v.norm(dim=1), target, atol=1e-5))
        self.assertTrue(torch.equal(v[~mask], torch.zeros_like(v[~mask])))
        A_ = float((W @ v.reshape(-1)).norm()) * 1.7
        g_cc = torch.randn(K.NV, K.HD)
        sc = K.scale_layer(W, v, A_, g_cc)
        self.assertTrue(sc['ok'])
        self.assertAlmostEqual(float((W @ (sc['lambda'] * v).reshape(-1)).norm()) / A_, 1.0, places=4)
        raw0 = raw.clone()
        raw0[1] = 0
        _, ok = K.build_template(raw0, target, mask)
        self.assertFalse(ok)                                                    # zero direction for a target>0 head
        self.assertTrue(K.scale_layer(W, v, 0.0, g_cc)['near_zero'])
        bad = K.scale_layer(W, v, float((W @ v.reshape(-1)).norm()) * 50, g_cc)
        self.assertFalse(bad['ok'])
        self.assertEqual(bad['reason'], 'lambda_out_of_range')

    def test_seeded(self):
        self.assertTrue(torch.equal(K.seeded_gaussian('a|b|14|3', (4,)), K.seeded_gaussian('a|b|14|3', (4,))))
        self.assertFalse(torch.equal(K.seeded_gaussian('a|b|14|3', (4,)), K.seeded_gaussian('a|b|14|4', (4,))))


class ToyNorm(torch.nn.Module):
    def __init__(self, val):
        super().__init__()
        self.val = val

    def forward(self, x):
        return self.val.clone()


class Hook(unittest.TestCase):
    def test_clamp_add_and_records(self):
        torch.manual_seed(1)
        val = torch.randn(K.NV, K.HD).to(torch.bfloat16)
        norm = ToyNorm(val)
        W = torch.randn(8, K.NV * K.HD).to(torch.bfloat16)
        mask = torch.tensor([h >= 2 for h in range(K.NV)])
        hook = H.ReadoutHook({14: (norm, W)}, {14: mask})
        donor = torch.zeros(K.NV, K.HD, dtype=torch.bfloat16)
        with hook:
            hook.arm('k', 'clamp', {14: donor})
            out = norm(torch.zeros(1))
            hook.disarm()
            self.assertTrue(torch.equal(out[mask], donor[mask]))
            self.assertTrue(torch.equal(out[~mask], val[~mask]))
            self.assertEqual(hook.hits['k'], {14: 1})
            hook.arm('m', 'add', {14: torch.ones(K.NV, K.HD)})
            out2 = norm(torch.zeros(1))
            hook.disarm()
            self.assertTrue(torch.equal(out2[~mask], val[~mask]))
            self.assertTrue(torch.equal(out2[mask], (val[mask].float() + 1).to(torch.bfloat16)))
            hook.arm('r')
            out3 = norm(torch.zeros(1))
            hook.disarm()
            self.assertTrue(torch.equal(out3, val))
            self.assertNotIn('post', hook.rec['r'][14])
            self.assertEqual(hook.rec['r'][14]['outproj_pre'].shape[0], 8)
            out4 = norm(torch.zeros(1))                                          # disarmed: no record
        self.assertTrue(torch.equal(out4, val))
        self.assertEqual(len(hook.handles), 0)


def synth_records(world, unmatched=False):
    ids = [f'P0{s}-f{f}' for s in range(1, 7) for f in (0, 1)]
    recs, shadow = {}, {'per_direction': {d: {} for d in K.DIRECTIONS}}
    for i in ids:
        cells, match = {}, {}
        for d in K.DIRECTIONS:
            zs = {'CC': 10.0, 'CFIX': 13.0, 'K0': 10.0, 'K_early': 12.0, 'K_late': 11.5}
            if world == 'dependence':
                zs.update(K=10.9, M_nat=12.8, M_rand=12.9)
            elif world == 'general':
                zs.update(K=10.9, M_nat=11.0, M_rand=11.1)
            else:                                                                # none
                zs.update(K=12.9, M_nat=12.95, M_rand=12.8)
            for a, z in zs.items():
                cells[f'{a}|{d}'] = {'readout': {'primary': {'cz_s46': z, 'cz_a': -z}}, 'score': {'first_step_eos': z > 12}}
            match[d] = {'M_nat': {'matched': not unmatched}, 'M_rand': {'matched': True}}
            shadow['per_direction'][d][i] = {'rho_shadow': 0.4}
        recs[i] = {'cells': cells, 'matching': match, 'item': {'id': i}}
    return recs, shadow


class Consumer(unittest.TestCase):
    def test_dependence_world(self):
        res = A.analyse(*synth_records('dependence'))
        self.assertEqual(res['cross']['axis_b'], 'exceeds_both')
        self.assertTrue(res['cross']['joint_strong_and_exceeds_both'])
        self.assertTrue(res['predictions']['P1'] and res['predictions']['P2'])
        self.assertTrue(res['K0_exact_zero'])

    def test_general_world(self):
        res = A.analyse(*synth_records('general'))
        self.assertEqual(res['cross']['axis_b'], 'close_to_both')
        self.assertFalse(res['cross']['joint_strong_and_exceeds_both'])
        self.assertEqual(res['cross']['axis_a_main'], 'reduced')

    def test_no_dependence_and_unmatched(self):
        res = A.analyse(*synth_records('none'))
        self.assertEqual(res['cross']['axis_a_main'], 'not_reduced')
        self.assertFalse(res['predictions']['P1'])
        res = A.analyse(*synth_records('dependence', unmatched=True))
        self.assertEqual(res['cross']['axis_b'], 'comparison_insufficient')
        self.assertFalse(res['cross']['joint_strong_and_exceeds_both'])


class Wiring(unittest.TestCase):
    def test_runner_constants(self):
        import b4_run as R
        per_input = 1 + len(K.DIRECTIONS) * (1 + len(R.N_ARMS))
        self.assertEqual(per_input, 37)
        self.assertEqual(R.LIMITS['formal']['scores'], 12 * per_input)
        self.assertEqual(R.LIMITS['preflight']['scores'], 2 * per_input)
        self.assertEqual(R.next_scenario('P06-f1'), 'P01-f1')
        self.assertEqual(R.next_scenario('P02-f0'), 'P03-f0')
        self.assertEqual(set(K.EARLY) | set(K.LATE), set(K.G_LAYERS))
        self.assertFalse(set(K.EARLY) & set(K.LATE))


def main():
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    receipt = sys.argv[1] if len(sys.argv) > 1 else None
    res = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    if receipt:
        import hashlib
        repo = HERE.parent.parent
        src = {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py'))}
        with open(receipt, 'x') as f:
            json.dump({'status': 'passed' if res.wasSuccessful() else 'failed', 'tests_run': res.testsRun, 'failures': len(res.failures),
                       'errors': len(res.errors), 'source_hashes': src, 'torch': torch.__version__}, f, indent=2)
            f.write('\n')
    sys.exit(0 if res.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
