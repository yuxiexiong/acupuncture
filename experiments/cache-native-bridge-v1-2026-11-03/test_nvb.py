"""CPU tests for NVB-01.
Local computation: diagonal split_update == original kernel bit for bit; off-diagonal output == the v_c candidate and returned state == the v_a
candidate bit for bit; S_a - S_c identity <= 1e-5; matched random rho is deterministic, per-head norm matched, b-independent.
Frozen read-outs: every primary label and reading is demonstrated both satisfiable and not satisfiable on synthetic data (guideline 6.2);
rank p arithmetic; ratio guard; budget.
CUDA_VISIBLE_DEVICES= python test_nvb.py [RECEIPT]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import nvb_core as K  # noqa: E402

SC = [f'NQ0{k}' for k in range(1, 7)]
IDS = [f'{s}-{j}' for s in SC for j in range(8)]
SCEN = {i: i.split('-')[0] for i in IDS}
ALL = set(IDS)


def const(v):
    return {i: (v(i) if callable(v) else v) for i in IDS}


def synth(e00=0.3, e01=0.3, e10=0.3, e11=2.0, rand=None, k=K.K_DRAWS, scen_flip=0, y=None):
    """Synthetic M with the given k effects e(c, a) (b = 0 margins 0, b = 1 margins e); random draws with k effects rand[j] (default e00 + small
    spread).  scen_flip: number of scenarios whose e01 is replaced by -e01 (to break the scenario rule)."""
    flip = set(SC[:scen_flip])
    e = {'00': e00, '01': e01, '10': e10, '11': e11}
    M = {}
    for ca, val in e.items():
        M[ca + '0'] = const(0.0)
        M[ca + '1'] = const(lambda i, val=val, ca=ca: (-val if (ca == '01' and SCEN[i] in flip) else val))
    if rand is None:
        rand = [e00 + 0.01 * (j - k / 2) / k for j in range(k)]
    MR = [{'0': const(0.0), '1': const(r)} for r in rand]
    Y = None
    if y is not None:
        Y = {c: const(lambda i, c=c: int(int(i.split('-')[1]) < y.get(c, 0))) for c in K.MAIN}
    return K.direction(M, MR, Y, SCEN, ALL)


class Rules(unittest.TestCase):
    def test_primary_labels_both_sides(self):
        self.assertEqual(synth(e01=1.8)['P'], 'beyond_random_substantial')                       # rho 1.5/1.7 >= 0.5
        self.assertEqual(synth(e01=0.8)['P'], 'beyond_random_partial')                           # rho 0.5/1.7 < 0.5
        self.assertEqual(synth(e01=1.0, e11=0.6)['P'], 'beyond_random_unscaled')                 # DF 0.3 < 0.5 -> no ratio
        self.assertEqual(synth(e01=1.8, rand=[0.3] * 18 + [2.5])['P'], 'not_beyond_random')       # one draw above -> p = 2/20
        self.assertEqual(synth(e01=0.4)['P'], 'not_supported')                                   # DS0 0.1 < 0.25
        self.assertEqual(synth(e01=1.8, scen_flip=3)['P'], 'not_supported')                       # only 3/6 scenarios positive
        self.assertEqual(synth(e01=-0.3)['P'], 'opposite')

    def test_readings_both_sides(self):
        self.assertEqual(synth(e01=1.8)['R'], 'storage_main')
        self.assertEqual(synth(e01=0.8)['R'], 'storage_partial')
        self.assertEqual(synth(e01=1.8, rand=[0.3] * 18 + [2.5])['R'], 'generic_not_excluded')
        self.assertEqual(synth(e01=-0.3)['R'], 'storage_opposite')
        self.assertEqual(synth(e01=0.3, e10=1.6)['R'], 'output_main')                            # DO0 1.3 / DF 1.7 >= 0.5
        self.assertEqual(synth(e01=0.3, e10=0.6)['R'], 'storage_needs_output')                   # DO0 ratio 0.18; DS1 1.4 supported
        self.assertEqual(synth(e01=0.3, e10=1.9, e11=2.0)['R'], 'output_main')
        self.assertEqual(synth(e01=0.4, e10=0.4, e11=2.0)['R'], 'storage_needs_output')
        r = synth(e01=0.4, e10=0.5, e11=0.85)                                                    # singles below support, DS1 0.35 supported
        self.assertEqual(r['R'], 'storage_needs_output')
        r = synth(e01=0.45, e10=0.45, e11=0.6)                                                   # DF 0.3 supported, singles not
        self.assertEqual(r['R'], 'joint_effective_singles_uncertain')
        self.assertEqual(synth(e01=0.35, e10=0.35, e11=0.4)['R'], 'weak')

    def test_rank_p_and_ratio(self):
        self.assertAlmostEqual(K.rank_p(1.0, [0.0] * 19), 1 / 20)
        self.assertAlmostEqual(K.rank_p(1.0, [0.0] * 18 + [1.0]), 2 / 20)                      # ties count against
        self.assertAlmostEqual(K.rank_p(1.0, [2.0] * 19), 1.0)
        r = synth(e01=1.8)
        self.assertAlmostEqual(r['rho_DS0_DF'], 1.5 / 1.7)
        self.assertAlmostEqual(r['p_rank'], 1 / 20)
        self.assertEqual(r['scen_above_all_draws'], 6)
        self.assertIsNone(synth(e01=1.0, e11=0.6)['rho_DS0_DF'])
        self.assertEqual(len(r['random_DS0_draws']), K.K_DRAWS)

    def test_multi_direction_and_y(self):
        good, bad = synth(e01=1.8), synth(e01=0.4)
        s = K.summary({'a': good, 'b': good, 'c': bad, 'd': good}, ('a', 'b', 'c'))
        self.assertTrue(s['multi_direction_storage_main'])
        self.assertFalse(K.summary({'a': good, 'b': bad, 'c': bad}, ('a', 'b', 'c'))['multi_direction_storage_main'])
        r = synth(e01=1.8, y={'100': 1, '110': 2, '101': 2, '111': 6})
        self.assertTrue(r['Y']['S1_b1']['support'])                                              # 6 scen x (6 - 2) = 24
        self.assertTrue(r['Y']['S1_b0']['support'])
        self.assertEqual(r['Y']['JS_c1'], 6 * (4 - 1))
        self.assertFalse(synth(e01=1.8, y={'101': 2, '111': 2})['Y']['S1_b1']['support'])


class Local(unittest.TestCase):
    def setUp(self):
        import torch
        import nvb_run as R
        self.R, self.torch = R, torch
        self.QM = R.gdn_module()
        g = torch.Generator().manual_seed(7)
        rnd = lambda *s: torch.randn(*s, generator=g)   # noqa: E731
        self.q, self.k, self.kb, self.v0, self.v1 = [rnd(1, 1, 32, 128).to(torch.bfloat16) for _ in range(5)]
        self.g, self.beta = -torch.rand(1, 1, 32, generator=g), torch.rand(1, 1, 32, generator=g).to(torch.bfloat16)
        self.S0 = rnd(1, 32, 128, 128) * 0.1

    def cu(self, kb, v):
        return self.R.custom_update(self.q, self.k, kb, v, self.g, self.beta, self.S0.clone(), True, True, self.QM.l2norm)

    def test_diagonal_equals_original(self):
        R = self.R
        orig = self.QM.torch_recurrent_gated_delta_rule
        o0, S0n = orig(self.q, self.k, self.v0, g=self.g, beta=self.beta, initial_state=self.S0.clone(), output_final_state=True, use_qk_l2norm_in_kernel=True)
        o, S, err, dse = R.split_update(self.q, self.k, self.k, self.v0, self.v0, self.g, self.beta, self.S0.clone(), self.QM.l2norm)
        self.assertTrue(R.bit_equal(o, o0)[0] and R.bit_equal(S, S0n)[0])
        self.assertIsNone(dse)
        self.assertLessEqual(err, R.ORACLE_TOL)

    def test_offdiagonal_selects_output_and_state(self):
        R = self.R
        for kb in (self.k, self.kb):
            for vc, va in ((self.v1, self.v0), (self.v0, self.v1)):
                o, S, err, dse = R.split_update(self.q, self.k, kb, vc, va, self.g, self.beta, self.S0.clone(), self.QM.l2norm)
                oc, Sc, _ = self.cu(kb, vc)
                oa, Sa, _ = self.cu(kb, va)
                self.assertTrue(R.bit_equal(o, oc)[0])            # output from the v_c candidate
                self.assertTrue(R.bit_equal(S, Sa)[0])            # returned state from the v_a candidate
                self.assertFalse(R.bit_equal(S, Sc)[0])
                self.assertFalse(R.bit_equal(o, oa)[0])
                self.assertLessEqual(dse, R.ORACLE_TOL)
                self.assertLessEqual(err, R.ORACLE_TOL)
        # the identity check detects a wrong state
        _, Sc, _ = self.cu(self.kb, self.v0)
        _, Sa, _ = self.cu(self.kb, self.v1)
        self.assertGreater(R.ds_error(Sa * 1.01, Sc, self.kb, self.v1, self.v0, self.beta, self.QM.l2norm), R.ORACLE_TOL)
        self.assertLessEqual(R.ds_error(Sa, Sc, self.kb, self.v1, self.v0, self.beta, self.QM.l2norm), R.ORACLE_TOL)

    def test_initial_state_untouched(self):
        S0 = self.S0.clone()
        self.R.split_update(self.q, self.k, self.kb, self.v1, self.v0, self.g, self.beta, S0, self.QM.l2norm)
        self.assertTrue(self.torch.equal(S0, self.S0))

    def test_random_arm(self):
        torch, R = self.torch, self.R
        v1 = self.v1.clone()
        v1[0, 0, 3] = self.v0[0, 0, 3]                         # one head without change -> zero rho
        rho, nrm, z = R.make_rho(('X', 'd', 0), 13, self.v0, v1)
        rho2, _, _ = R.make_rho(('X', 'd', 0), 13, self.v0, v1)
        self.assertTrue(torch.equal(rho, rho2))
        self.assertFalse(torch.equal(rho, R.make_rho(('X', 'd', 1), 13, self.v0, v1)[0]))
        self.assertFalse(torch.equal(rho, R.make_rho(('X', 'd', 0), 14, self.v0, v1)[0]))
        self.assertEqual(rho.dtype, torch.float32)
        self.assertTrue(torch.allclose(rho.norm(dim=-1, keepdim=True), nrm, rtol=1e-5, atol=1e-7))
        self.assertEqual(float(rho[0, 0, 3].abs().max()), 0.0)
        # another forward (different v0 / v1, as in deeper layers under b = 1): same unit direction, its own norm
        rho3, nrm3, z3 = R.make_rho(('X', 'd', 0), 13, self.v0 * 0.5, self.v1)
        self.assertTrue(torch.equal(z, z3))
        self.assertFalse(torch.equal(rho, rho3))
        self.assertTrue(torch.allclose(rho3.norm(dim=-1, keepdim=True), nrm3, rtol=1e-5, atol=1e-7))
        dvec = (v1.float() - self.v0.float())
        cos = torch.nn.functional.cosine_similarity(rho.reshape(-1, 128), dvec.reshape(-1, 128), dim=-1)
        self.assertLess(float(cos.abs().max()), 0.5)           # random, not the v1 direction
        va = self.v0.float() + rho
        o, S, err, dse = R.split_update(self.q, self.k, self.kb, self.v0, va, self.g, self.beta, self.S0.clone(), self.QM.l2norm)
        self.assertTrue(R.bit_equal(o, self.cu(self.kb, self.v0)[0])[0])
        self.assertLessEqual(dse, R.ORACLE_TOL)


class Wiring(unittest.TestCase):
    def test_budget(self):
        import nvb_run as R
        f, p = R.LIMITS['formal'], R.LIMITS['preflight']
        self.assertEqual((f['t1'], f['refs'], f['r_t1'], f['c_t2'], f['r_c_t2'], f['trajectories']), (1536, 768, 7296, 1536, 7296, 1536))
        self.assertEqual(f['n_steps'], 1536 * 31)
        self.assertEqual(f['decode_forwards'], 66048)
        self.assertEqual(p['decode_forwards'], 2752)
        self.assertEqual(f['shadow'], (14 + 57) * 14 * 4 * 48)
        self.assertEqual((f['formations'], f['prefix_prefills'], f['formation_token_forwards']), (240, 48, 6390))
        self.assertAlmostEqual(R.GPU_CAP_S['formal'] + 2 * R.GPU_CAP_S['preflight'], 1.5 * 3600)
        self.assertEqual(len(R.plan('formal', 0, 2)) + len(R.plan('formal', 1, 2)), 48)
        self.assertEqual(sorted(u['item_id'] for u in R.plan('preflight', 0, 1)), sorted(R.PREFLIGHT_ITEMS))
        self.assertEqual(R.K_DRAWS, 19)
        self.assertEqual(set(R.DIAG), {'000', '001', '110', '111'})


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
