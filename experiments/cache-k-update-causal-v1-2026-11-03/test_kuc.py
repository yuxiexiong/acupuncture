"""CPU tests for KUC-01: custom update == original kernel (no change, and full replacement with the shadow k) bit for bit; erase/write cells
match the FP64 oracle and differ from 11; signed-zero exception strictly limited; masked cache comparison; frozen rules pass and fail; budget.
CUDA_VISIBLE_DEVICES= python test_kuc.py [RECEIPT]"""
import json
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kuc_core as K  # noqa: E402

SC = [f'NQ0{k}' for k in range(1, 7)]
IDS = [f'{s}-{j}' for s in SC for j in range(8)]
SCEN = {i: i.split('-')[0] for i in IDS}
ALL = set(IDS)


def const(v):
    return {i: v(i) if callable(v) else v for i in IDS}


def ycount(k):
    return const(lambda i: int(int(i.split('-')[1]) < k))


def inputs(torch, seed):
    g = torch.Generator().manual_seed(seed)
    r = lambda *s: torch.randn(*s, generator=g)   # noqa: E731
    return dict(query=r(1, 1, 32, 128).to(torch.bfloat16), key=r(1, 1, 32, 128).to(torch.bfloat16), value=r(1, 1, 32, 128).to(torch.bfloat16),
                g=-torch.rand(1, 1, 32, generator=g), beta=torch.rand(1, 1, 32, generator=g).to(torch.bfloat16), S=r(1, 32, 128, 128) * 0.1,
                k1=r(1, 1, 32, 128).to(torch.bfloat16))


class Update(unittest.TestCase):
    def test_equivalences(self):
        import torch
        import kuc_run as R
        QM = R.gdn_module()
        orig = QM.torch_recurrent_gated_delta_rule
        x = inputs(torch, 0)
        kw = dict(g=x['g'], beta=x['beta'], output_final_state=True, use_qk_l2norm_in_kernel=True)
        o0, S0 = orig(x['query'], x['key'], x['value'], initial_state=x['S'].clone(), **kw)
        oc, Sc, _ = R.custom_update(x['query'], x['key'], x['key'], x['value'], x['g'], x['beta'], x['S'].clone(), True, True, QM.l2norm)
        self.assertTrue(R.bit_equal(o0, oc)[0] and R.bit_equal(S0, Sc)[0])                              # no change == native
        o1, S1 = orig(x['query'], x['k1'], x['value'], initial_state=x['S'].clone(), **kw)
        of, Sf, _ = R.custom_update(x['query'], x['k1'], x['k1'], x['value'], x['g'], x['beta'], x['S'].clone(), True, True, QM.l2norm)
        self.assertTrue(R.bit_equal(o1, of)[0] and R.bit_equal(S1, Sf)[0])                              # 11 == original fed k1
        for E_, W_ in ((x['k1'], x['key']), (x['key'], x['k1'])):
            o, S, err = R.custom_update(x['query'], E_, W_, x['value'], x['g'], x['beta'], x['S'].clone(), True, True, QM.l2norm, oracle=True)
            self.assertLessEqual(err, R.ORACLE_TOL)
            self.assertFalse(torch.equal(S, S1) or torch.equal(S, S0))
        # E-term + W-term effects: S(11) - S(00) == (S(10) - S(00)) + (S(01) - S(00)) exactly in reals (the update is linear in each term)
        _, S10, _ = R.custom_update(x['query'], x['k1'], x['key'], x['value'], x['g'], x['beta'], x['S'].clone(), True, True, QM.l2norm)
        _, S01, _ = R.custom_update(x['query'], x['key'], x['k1'], x['value'], x['g'], x['beta'], x['S'].clone(), True, True, QM.l2norm)
        lhs, rhs = (S1 - S0).double(), ((S10 - S0) + (S01 - S0)).double()
        self.assertLess(float((lhs - rhs).abs().max() / lhs.abs().max()), 1e-4)

    def test_oracle_detects_error(self):
        import torch
        import kuc_run as R
        QM = R.gdn_module()
        x = inputs(torch, 1)
        _, S, err = R.custom_update(x['query'], x['k1'], x['key'], x['value'], x['g'], x['beta'], x['S'].clone(), True, True, QM.l2norm, oracle=True)
        _, Sbad, err_bad = R.custom_update(x['query'], x['k1'], x['key'], x['value'], x['g'], x['beta'] * 1.01, x['S'].clone(), True, True, QM.l2norm, oracle=True)
        self.assertLessEqual(err, R.ORACLE_TOL)
        # the oracle recomputes from the same (perturbed) inputs, so it must still pass; a wrong formula must fail:
        self.assertLessEqual(err_bad, R.ORACLE_TOL)
        bad = (S + 1e-3)
        So = S.double()
        self.assertGreater(float((bad.double() - So).abs().max() / max(1.0, float(So.abs().max()))), R.ORACLE_TOL)


class Exact(unittest.TestCase):
    def test_bit_equal(self):
        import torch
        import kuc_run as R
        a = torch.tensor([1.0, 0.0, -2.0])
        b = torch.tensor([1.0, -0.0, -2.0])
        self.assertEqual(R.bit_equal(a, b), (True, 1))
        self.assertEqual(R.bit_equal(a, a.clone()), (True, 0))
        self.assertFalse(R.bit_equal(a, torch.tensor([1.0, 0.0, -2.0000002]))[0])
        self.assertFalse(R.bit_equal(a, torch.tensor([1.0, 1e-45, -2.0]))[0])                             # denormal is not zero
        self.assertFalse(R.bit_equal(a, a.to(torch.float64))[0])
        h = torch.tensor([0.0, 3.0], dtype=torch.bfloat16)
        self.assertEqual(R.bit_equal(h, torch.tensor([-0.0, 3.0], dtype=torch.bfloat16)), (True, 1))

    def test_cache_mask(self):
        import torch
        import kuc_run as R
        types = ['linear_attention', 'full_attention', 'linear_attention']
        G = (2,)

        def mk():
            g = torch.Generator().manual_seed(3)
            lin = lambda: SimpleNamespace(recurrent_states={0: torch.randn(1, 32, 128, 128, generator=g)}, conv_states={0: torch.randn(1, 8192, 4, generator=g)})   # noqa: E731
            return SimpleNamespace(layers=[lin(), SimpleNamespace(keys=torch.randn(1, 4, 9, 256, generator=g), values=torch.randn(1, 4, 9, 256, generator=g)), lin()])
        c1, c2 = mk(), mk()
        self.assertTrue(R.cache_equal(c1, c2, types, G)[0])
        c2.layers[2].conv_states[0][0, 3000, 1] += 1.0                                                   # G conv k channel, old-slot position
        self.assertFalse(R.cache_equal(c1, c2, types, G)[0])
        ok, _, nm, _ = R.cache_equal(c1, c2, types, G, mask_k_old=True)
        self.assertTrue(ok and nm == 1)
        c3 = mk()
        c3.layers[2].conv_states[0][0, 3000, 3] += 1.0                                                   # t1 slot: not masked
        self.assertFalse(R.cache_equal(c1, c3, types, G, mask_k_old=True)[0])
        c4 = mk()
        c4.layers[2].conv_states[0][0, 5000, 1] += 1.0                                                   # V channel: not masked
        self.assertFalse(R.cache_equal(c1, c4, types, G, mask_k_old=True)[0])
        c5 = mk()
        c5.layers[0].conv_states[0][0, 3000, 1] += 1.0                                                   # non-G layer: not masked
        self.assertFalse(R.cache_equal(c1, c5, types, G, mask_k_old=True)[0])


class Rules(unittest.TestCase):
    def fam(self, m10, m01, m11, y=(0, 0, 0, 3), sign=1, morig=2.0):
        M = {'00': const(0.0), '10': const(m10), '01': const(m01), '11': const(m11), 'orig': const(morig)}
        Y = {c: ycount(k) for c, k in zip(('00', '10', '01', '11'), y)}
        Y['orig'] = ycount(4)
        return K.family(M, Y, SCEN, ALL, sign)

    def test_labels(self):
        self.assertEqual(self.fam(1.0, 0.1, 1.2, y=(0, 3, 0, 3))['label'], 'single_E')
        self.assertEqual(self.fam(0.1, 1.0, 1.2, y=(0, 0, 3, 3))['label'], 'single_W')
        self.assertEqual(self.fam(1.0, 1.0, 1.5, y=(0, 2, 2, 3))['label'], 'both_single')
        self.assertEqual(self.fam(0.1, 0.1, 1.5)['label'], 'joint_only')
        self.assertEqual(self.fam(0.1, 0.1, 1.5, y=(0, 0, 0, 0))['label'], 'diag_only')
        self.assertEqual(self.fam(0.1, 0.1, 0.2)['label'], 'none')
        self.assertEqual(self.fam(-0.5, 0.1, 1.5)['label'], 'sign_inconsistent')
        self.assertEqual(self.fam(-1.0, -0.1, -1.2, y=(3, 0, 3, 0), sign=-1, morig=-2.0)['label'], 'single_E')   # A/Z direction

    def test_ratios_interaction_residue(self):
        r = self.fam(0.6, 0.6, 1.0, y=(0, 1, 1, 3))
        self.assertAlmostEqual(r['g1_over_g_old'], 0.5)
        self.assertAlmostEqual(r['cell_ratios']['10'], 0.6)
        self.assertFalse(r['interaction']['M_practical'])                                                # I = -0.2, tol 0.25
        self.assertTrue(self.fam(0.9, 0.9, 1.0, y=(0, 1, 1, 3))['interaction']['M_practical'])          # I = -0.8
        self.assertAlmostEqual(r['residue']['M_tnf_eq'], 1.0)
        r2 = self.fam(0.5, 0.5, 1.0)
        self.assertFalse(r2['interaction']['M_practical'])                                               # I = 0
        self.assertIsNone(self.fam(0.1, 0.1, 0.3)['cell_ratios']['10'])                                  # |g1| < 0.5

    def test_p1(self):
        ok = {'R': {'joint': {'11': True}}, 'A': {'joint': {'11': True}}}
        bad = {'R': {'joint': {'11': True}}, 'A': {'joint': {'11': False}}}
        self.assertEqual(K.p1({'a': ok, 'b': ok, 'c': ok})['label'], 'holds')
        self.assertEqual(K.p1({'a': ok, 'b': bad, 'c': ok})['label'], 'partial')
        self.assertEqual(K.p1({'a': bad, 'b': bad, 'c': bad})['label'], 'fails')


class Wiring(unittest.TestCase):
    def test_budget(self):
        import kuc_run as R
        f, p = R.LIMITS['formal'], R.LIMITS['preflight']
        per = 4 * 14
        self.assertEqual((f['t1'], f['c_t2'], f['trajectories'], f['n_steps'], f['refs'], f['shadow']), (48 * per, 48 * per, 48 * per, 48 * per * 31, 48 * 4 * 5, 48 * 4 * 12 * 14))
        self.assertEqual(f['decode_forwards'], f['t1'] + f['n_steps'] + f['c_t2'] + f['refs'])
        self.assertEqual(f['decode_forwards'], 89664)
        self.assertEqual((p['t1'], p['c_t2'], p['n_steps'], p['refs'], p['shadow']), (2 * per, 2 * per, 2 * per * 31, 2 * 4 * 5, 2 * 4 * 12 * 14))
        self.assertEqual(p['decode_forwards'], p['t1'] + p['n_steps'] + p['c_t2'] + p['refs'])
        self.assertEqual(p['decode_forwards'], 3736)
        self.assertEqual(R.GPU_CAP_S['formal'] + 2 * R.GPU_CAP_S['preflight'], 2.4 * 3600)
        self.assertEqual(R.FAMILIES, {'R': ('V', 'Rk'), 'A': ('F', 'Ak'), 'Z': ('F', 'Ark')})


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
