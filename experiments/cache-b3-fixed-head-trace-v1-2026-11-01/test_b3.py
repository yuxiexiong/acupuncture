"""CPU tests for B3 (no weights): every criterion demonstrated both satisfiable and not, consumer on synthetic units,
runner wiring and budget arithmetic.  CUDA_VISIBLE_DEVICES= python test_b3.py [RECEIPT_JSON]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import b3_core as K  # noqa: E402
import b3_analysis as A  # noqa: E402


class Composition(unittest.TestCase):
    def test_categories(self):
        n = 12
        self.assertEqual(K.composition([-0.9] * n, [-0.1] * n, [-1.0] * n)['category'], 'self')
        c = K.composition([0.3] * n, [-1.3] * n, [-1.0] * n)
        self.assertEqual(c['category'], 'interaction')
        self.assertTrue(c['opposing'])
        c = K.composition([-0.5] * n, [-0.5] * n, [-1.0] * n)
        self.assertEqual(c['category'], 'both')
        self.assertFalse(c['opposing'])
        self.assertEqual(K.composition([0.1] * n, [0.0] * n, [0.1] * n)['category'], 'D_small')
        self.assertAlmostEqual(c['share_R'] + c['share_I'], 1.0)

    def test_contrast_identity(self):
        z = {'CC': 0.2, 'FIX': 4.1, 'REST': 0.7, 'CT': 3.3}
        c = K.contrasts(z)
        self.assertAlmostEqual(c['D'], c['R'] + c['I'])


class Band(unittest.TestCase):
    def test_specific_and_within(self):
        nulls = [[-0.1 + 0.01 * i, 0.05 - 0.01 * i] for i in range(12)]
        self.assertEqual(K.band([-1.3] * 12, nulls)['label'], 'specific')
        self.assertEqual(K.band([-1.3] * 12, nulls)['side'], 'below')
        self.assertEqual(K.band([0.0] * 12, nulls)['label'], 'within')
        mixed = [-1.3] * 6 + [1.3] * 6                      # beyond the band but split across sides
        self.assertEqual(K.band(mixed, nulls)['label'], 'within')
        self.assertEqual(K.band([-1.3] * 9 + [0.0] * 3, nulls)['label'], 'specific')
        self.assertEqual(K.band([-1.3] * 8 + [0.0] * 4, nulls)['label'], 'within')


class Scale(unittest.TestCase):
    def test_terms_sum(self):
        t = K.scale_terms(3.0, 70.0, 5.0, 90.0)
        self.assertAlmostEqual(t['num'] + t['den'], t['total'])

    def test_constant_r_is_numerator(self):
        p = {'CC': 0.0, 'FIX': 400.0, 'REST': 30.0, 'CT': 300.0}
        r = {k: 100.0 for k in p}
        si = K.scale_interaction(p, r)
        self.assertAlmostEqual(si['I_scale'], 0.0)
        self.assertEqual(K.scale_label([si['I_z']] * 12, [si['I_scale']] * 12)['label'], 'numerator_dominant')

    def test_additive_p_varying_r_is_scale(self):
        p = {'CC': 0.0, 'FIX': 400.0, 'REST': 30.0, 'CT': 430.0}    # numerator exactly additive
        r = {'CC': 100.0, 'FIX': 110.0, 'REST': 101.0, 'CT': 140.0}
        si = K.scale_interaction(p, r)
        self.assertAlmostEqual(si['I_num_common_r'], 0.0)
        self.assertEqual(K.scale_label([si['I_z']] * 12, [si['I_scale']] * 12)['label'], 'scale_involved')


class Layerwise(unittest.TestCase):
    def test_first_detectable(self):
        layers = [13, 14, 15]
        nulls = {l: [[-0.1, 0.1]] * 12 for l in layers}
        vals = {13: [0.0] * 12, 14: [-1.0] * 12, 15: [-2.0] * 12}
        self.assertEqual(K.first_detectable(layers, vals, nulls)['first']['layer'], 14)
        self.assertIsNone(K.first_detectable(layers, {l: [0.0] * 12 for l in layers}, nulls)['first'])


def synth_units(kind):
    import torch
    G = [13]
    units = []
    for i in range(12):
        j = 0.02 * (i - 6)
        dirs = {}
        for d in K.DIRECTIONS:
            if d == K.ANCHOR:
                z = {'N:CC': 0.0, 'N:CFIX': 3.5, 'N:CREST': 0.2, 'N:CT': 3.6}
            elif kind == 'interaction':
                z = {'N:CC': 0.0, 'N:CFIX': 4.0, 'N:CREST': 0.3, 'N:CT': 3.0 + j}
            else:
                z = {'N:CC': 0.0, 'N:CFIX': 4.0, 'N:CREST': -0.9, 'N:CT': 3.0 + j}
            z.update({'N:CUF1': 0.5, 'N:CUF1c': z['N:CT'] - 0.5 + 0.05 + j, 'N:CUF2': 0.6, 'N:CUF2c': z['N:CT'] - 0.6 - 0.05 - j})
            cells = {}
            for c, v in z.items():
                lp = {l: (v if l == A.LAST else 0.0) for l in range(A.FIRST, A.LAST + 1)}
                cells[c] = {'z': {'stop': v, 'answer': -2 * v}, 'p': {'stop': v * 50.0, 'answer': -2 * v * 50.0}, 'r': 50.0,
                            'layer_p': {'stop': lp, 'answer': {l: -2 * x for l, x in lp.items()}},
                            'mix_p': {'stop': dict(lp), 'answer': dict(lp)}, 'mlp_p': {'stop': dict(lp), 'answer': dict(lp)},
                            'core': {13: torch.full((32, 128), v, dtype=torch.float64)}}
            dirs[d] = cells
        units.append({'id': f'P{i}', 'base': f'P{i // 2}', 'dirs': dirs, 'G': G, 'fix': {(13, h) for h in range(5)}})
    return units


class Consumer(unittest.TestCase):
    def test_interaction_world(self):
        res = A.analyse(synth_units('interaction'))
        self.assertTrue(res['prediction']['P1_interaction_dominates'])
        self.assertTrue(res['prediction']['P2_fix_specific_interaction'])
        self.assertEqual(res['summary'][K.ANCHOR]['composition'], 'D_small')
        self.assertTrue(res['numerics']['recon_ok'])
        self.assertEqual(res['summary']['R0_L00_D-1']['first_detectable']['layer'], A.LAST)

    def test_self_world(self):
        res = A.analyse(synth_units('self'))
        self.assertFalse(res['prediction']['P1_interaction_dominates'])
        self.assertEqual(res['summary']['R1_L00_D-1']['composition'], 'self')
        self.assertFalse(res['prediction']['P2_fix_specific_interaction'])   # I = -0.1 +- jitter sits in the null band

    def test_recon_check_can_fail(self):
        u = synth_units('interaction')
        u[0]['dirs'][K.ANCHOR]['N:CC']['p']['stop'] = 30.0                      # z_rec 0.6 vs logits 0.0
        self.assertFalse(A.analyse(u)['numerics']['recon_ok'])


class Wiring(unittest.TestCase):
    def test_budget_and_sets(self):
        import b3_run as V
        per_input = 1 + len(K.DIRECTIONS) * len(V.PER_DIR)
        self.assertEqual(per_input, 41)
        self.assertEqual(V.LIMITS['formal']['scores'], 12 * per_input)
        self.assertEqual(V.LIMITS['preflight']['scores'], 2 * per_input + len(V.TWO_BY_TWO))
        self.assertEqual(V.LIMITS['formal']['formations'], 12 * (1 + len(K.DIRECTIONS)))
        self.assertEqual(V.LIMITS['preflight']['formations'], 2 * (1 + len(K.DIRECTIONS)))
        G = list(V.PK.G)
        fix = json.loads(V.P.FIXED.read_text())['heads']
        rest = V.complement(G, fix)
        self.assertEqual(len(rest) + len(fix), 448)
        self.assertFalse({tuple(x) for x in rest} & {tuple(x) for x in fix})
        self.assertEqual(len(V.plan('formal', 0, 2)) + len(V.plan('formal', 1, 2)), 12)
        self.assertEqual(set(V.REPLAY) & set(V.NEW), set())


def main():
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    receipt = sys.argv[1] if len(sys.argv) > 1 else None
    res = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    if receipt:
        import hashlib
        repo = HERE.parent.parent
        src = {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py'))}
        import torch
        with open(receipt, 'x') as f:
            json.dump({'status': 'passed' if res.wasSuccessful() else 'failed', 'tests_run': res.testsRun,
                       'failures': len(res.failures), 'errors': len(res.errors), 'skipped': len(res.skipped),
                       'source_hashes': src, 'torch': torch.__version__}, f, indent=2)
            f.write('\n')
    sys.exit(0 if res.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
