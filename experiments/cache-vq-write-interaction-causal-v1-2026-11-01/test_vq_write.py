"""CPU tests for CFM-VQ-WRITE-L13-v1 (no weights, no CUDA).

CUDA_VISIBLE_DEVICES= python test_vq_write.py [RECEIPT_JSON]
"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import vqw_core as K  # noqa: E402
import vqw_analysis as A  # noqa: E402
import torch  # noqa: E402


def rnd(*shape, seed=0):
    return torch.randn(*shape, generator=torch.Generator().manual_seed(seed), dtype=torch.float64)


def corners(H=4, d=8, break_qk=False):
    g, beta, z = -rnd(H, seed=1).abs(), torch.sigmoid(rnd(H, seed=2)), rnd(H * d, seed=3)
    qC, kC, qT, kT = rnd(H, d, seed=4), rnd(H, d, seed=5), rnd(H, d, seed=6), rnd(H, d, seed=7)
    vC, vT = rnd(H, d, seed=8), rnd(H, d, seed=9)
    rows = {}
    for c in K.CORNERS:
        q, k = (qT, kT) if c[0] == 'T' else (qC, kC)
        v = vT if c[1] == 'T' else vC
        rows[c] = {'q': q.clone(), 'k': k.clone(), 'v': v.clone(), 'g': g, 'beta': beta, 'z': z}
    if break_qk:
        rows['CT']['q'] = rows['CT']['q'] + 0.1
    S = rnd(H, d, d, seed=10)
    for c in K.CORNERS:
        n = K.write_term(rows[c])
        r = torch.einsum('hiv,hi->hv', S, K.read_weights(rows[c]))
        rows[c]['new'] = n.float()
        rows[c]['core'] = (r + n).to(torch.bfloat16)
    return rows, S


class Algebra(unittest.TestCase):
    def test_identity_and_read_zero(self):
        rows, S = corners()
        I, chk = K.i13(rows, S)
        self.assertTrue(chk['g_beta_z_shared'] and chk['qk_depend_only_on_Q'] and chk['v_depends_only_on_V'])
        self.assertTrue(chk['product_identity_ok'])
        self.assertTrue(chk['read_interaction_ok'])
        self.assertTrue(chk['core_recon_ok'])
        self.assertGreater(float(I.norm()), 0)

    def test_dependence_violation_detected(self):
        rows, S = corners(break_qk=True)
        _, chk = K.i13(rows, S)
        self.assertFalse(chk['qk_depend_only_on_Q'])
        self.assertFalse(chk['read_interaction_ok'])


class Precision(unittest.TestCase):
    def test_pass_and_fail(self):
        core = (rnd(32, 128, seed=1) * 5.5e-4).to(torch.bfloat16)        # norm ~0.035 like the real layer-13 core
        d = rnd(32, 128, seed=2) * 1e-4                                  # norm ~0.011, every head resolvable
        self.assertTrue(K.precision(core, d)['ok'])
        tiny = d * 1e-3                                                  # below BF16 resolution in every head
        p = K.precision(core, tiny)
        self.assertFalse(p['ok'])
        self.assertGreater(p['unresolved_energy_share'], 0.02)
        d0 = d.clone()
        d0[3] = 0
        p0 = K.precision(core, d0)
        self.assertTrue(p0['zero_heads_untouched'] and p0['ok'])

    def test_addback_bitwise(self):
        core = (rnd(32, 128, seed=3) * 5.5e-4).to(torch.bfloat16)
        self.assertTrue(torch.equal(K.patch_core(core, rnd(32, 128, seed=4) * 1e-4, addback=True), core))
        self.assertTrue(torch.equal(K.patch_core(core, torch.zeros(32, 128, dtype=torch.float64)), core))


class Random(unittest.TestCase):
    def test_random_like(self):
        t = rnd(32, 128, seed=5)
        t[7] = 0
        a, b, c = K.random_like('X', 0, t), K.random_like('X', 0, t), K.random_like('X', 1, t)
        self.assertTrue(torch.equal(a, b))
        self.assertFalse(torch.equal(a, c))
        self.assertTrue(torch.allclose(a.norm(dim=-1), t.norm(dim=-1), rtol=1e-12, atol=1e-15))
        self.assertEqual(float(a[7].abs().max()), 0.0)


class Estimands(unittest.TestCase):
    def test_identity_and_ratio(self):
        e = K.estimands(z_tt=5.0, z_del=6.0, z_tc=3.0, z_ct=4.0, z_cc=0.0)       # I=-2, I'=-1, delta=-1
        self.assertAlmostEqual(e['I'], -2.0)
        self.assertAlmostEqual(e['I_prime'], -1.0)
        self.assertAlmostEqual(e['delta'], -1.0)
        self.assertAlmostEqual(e['rho'], 0.5)
        self.assertAlmostEqual(e['kappa'], 0.5)
        self.assertEqual(e['identity_residual'], 0.0)
        self.assertIsNone(K.estimands(1.0, 1.0, 0.6, 0.6, 0.0)['rho'])          # |I| = 0.2 < 1

    def test_labels(self):
        self.assertEqual(K.label(None, 0.0), 'ratio_undecidable')
        self.assertEqual(K.label(0.05, 0.05), 'small_change')
        self.assertEqual(K.label(0.05, 0.5), 'reduced')
        self.assertEqual(K.label(0.5, 1.0), 'reduced')
        self.assertEqual(K.label(1.5, 3.0), 'overshoot_smaller')
        self.assertEqual(K.label(2.0, 4.0), 'equal_and_opposite')
        self.assertEqual(K.label(2.5, 5.0), 'reversed_or_amplified')
        self.assertEqual(K.label(-0.5, -1.0), 'reversed_or_amplified')

    def test_scenario_rule(self):
        f = [{'I': -3.0, 'delta': -1.5, 'd_rand0': 0.2, 'd_rand1': -0.3}, {'I': -2.5, 'delta': -1.0, 'd_rand0': 0.1, 'd_rand1': 0.2}]
        self.assertTrue(K.scenario_rule(f)['support'])
        f2 = [dict(x, d_rand0=1.5) for x in f]                                   # random as large as the real deletion
        self.assertFalse(K.scenario_rule(f2)['support'])
        f3 = [f[0], dict(f[1], delta=0.5)]                                       # one fact moves the wrong way
        self.assertFalse(K.scenario_rule(f3)['support'])
        f4 = [f[0], dict(f[1], I=2.0)]                                           # facts disagree in sign -> not evaluable
        r4 = K.scenario_rule(f4)
        self.assertFalse(r4['evaluable'])
        self.assertIsNone(r4['rho'])
        f5 = [dict(x, delta=x['I'] * 0.1) for x in f]                            # rho 0.1 -> kappa 0.9 > 0.75
        self.assertFalse(K.scenario_rule(f5)['support'])


def ro(cz_s46, cz_a, D=0.0):
    return {'primary': {'cz_s46': cz_s46, 'cz_a': cz_a}, 'derived': {'D': D, 's46_minus_a': cz_s46 - cz_a}, 'eos': False}


def synth(rho_true=0.6, rand=0.2):
    recs = []
    for s in ['S1', 'S2', 'S3', 'S4', 'S5', 'S6']:
        for k in (0, 1):
            cc, ct, tc = ro(0.0, 0.0), ro(5.0, -4.0), ro(3.0, -1.0)
            I_s, I_a = -2.0, 2.0                                    # TT = TC + CT - CC + I
            tt = ro(8.0 + I_s, -5.0 + I_a)
            dele = ro(tt['primary']['cz_s46'] - rho_true * I_s, tt['primary']['cz_a'] - rho_true * I_a)
            cells = {}
            for bg in ('M_T', 'N'):
                cells[f'{bg}:R'] = {'readout': tt}
                cells[f'{bg}:DEL'] = {'readout': dele}
                cells[f'{bg}:RAND0'] = {'readout': ro(tt['primary']['cz_s46'] + rand, tt['primary']['cz_a'] - rand)}
                cells[f'{bg}:RAND1'] = {'readout': ro(tt['primary']['cz_s46'] - rand, tt['primary']['cz_a'] + rand)}
            corners_ = {bg: {'CC': cc, 'CT': ct, 'TC': tc, 'TT': tt} for bg in ('M_T', 'N')}
            recs.append({'item': {'id': f'{s}-f{k}', 'base_id': s}, 'cells': cells, 'corners_from_conv': corners_})
    return recs


class AnalysisConsumer(unittest.TestCase):
    def test_support_world(self):
        res = A.analyse(synth())
        self.assertEqual(res['primary_result'], 'stable_support')
        g = res['groups']['N|cz_s46']
        self.assertAlmostEqual(g['scenario']['S1']['rho'], 0.6)
        self.assertLess(g['max_identity_residual'], 1e-12)

    def test_null_world(self):
        res = A.analyse(synth(rho_true=0.02, rand=0.5))
        self.assertEqual(res['primary_result'], 'not_stable_support')
        self.assertEqual(res['groups']['N|cz_s46']['scenario']['S1']['label'], 'small_change')


class Wiring(unittest.TestCase):
    def test_plan_and_limits(self):
        import vq_write as V
        self.assertEqual([u['item_id'] for u in V.plan('preflight', 0, 1)], list(V.PREFLIGHT_ITEMS))
        w0, w1 = V.plan('formal', 0, 2), V.plan('formal', 1, 2)
        self.assertEqual(len(w0) + len(w1), 12)
        self.assertFalse({u['base_id'] for u in w0} & {u['base_id'] for u in w1})
        self.assertEqual(V.LIMITS['formal']['scores'], 12 * 2 * 4)
        self.assertEqual(V.LIMITS['preflight']['scores'], 2 * (2 * 6 + 2))
        ids = {c['id'] for c in V.CF.cells()}
        self.assertTrue(set(V.BASE.values()) <= ids)
        self.assertTrue({cid for bg in K.BG_CELLS.values() for cid in bg.values()} <= ids)


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
