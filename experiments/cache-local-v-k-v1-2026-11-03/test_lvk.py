"""CPU tests for LVK-01: synthetic cases (only v main effect, interaction without delivery, opposite sign, small reference denominator, gap
algebra gap = d0 - d1); custom update with a substituted value == original kernel fed that value (L10) and FP64 oracle (L11); budget.
CUDA_VISIBLE_DEVICES= python test_lvk.py [RECEIPT]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lvk_core as K  # noqa: E402

SC = [f'NQ0{k}' for k in range(1, 7)]
IDS = [f'{s}-{j}' for s in SC for j in range(8)]
SCEN = {i: i.split('-')[0] for i in IDS}
ALL = set(IDS)
TNF = {i for i in IDS if int(i.split('-')[1]) < 5}


def const(v):
    return {i: v(i) if callable(v) else v for i in IDS}


def ycount(k):
    return const(lambda i: int(int(i.split('-')[1]) < k))


def world(M, Y=None, new=False):
    arms = ('L00', 'L01', 'L10', 'L11', 'V', 'VW') + (('VE', 'VK', 'F') if new else ())
    Mv = {a: const(M.get(a, 0.0)) for a in arms}
    Yv = {a: ycount((Y or {}).get(a, 0)) for a in arms}
    return {'M': Mv, 'G': {a: const(0.0) for a in arms}, 'Y': Yv}


class Rules(unittest.TestCase):
    def test_only_v_main(self):
        r = K.panel_direction(world({'L10': 3.0, 'L11': 3.3, 'L01': 0.3, 'V': 3.0, 'VW': 5.0}), SCEN, TNF, ALL, False)
        self.assertEqual(r['M']['vmain0']['label'], 'expected')
        self.assertEqual(r['M']['I_local']['label'], 'not_stable')                     # e1 = e0 = 0.3
        self.assertEqual(r['M']['I_block']['label'], 'expected')                        # 2.0 - 0.3
        self.assertAlmostEqual(r['M']['ratio_local_over_block'], 0.0)

    def test_interaction_without_delivery(self):
        r = K.panel_direction(world({'L01': 0.3, 'L10': 1.0, 'L11': 3.3, 'V': 1.0, 'VW': 3.3}), SCEN, TNF, ALL, False)
        self.assertEqual(r['M']['I_local']['label'], 'expected')                        # 2.3 - 0.3 = 2.0
        self.assertAlmostEqual(r['M']['gap']['eq'], 0.0)
        self.assertEqual(r['delivery']['k_increment_L11_vs_L10']['label'], 'none')

    def test_opposite_and_small_den(self):
        r = K.panel_direction(world({'L01': 0.5, 'L11': -0.5, 'V': 0.0, 'VW': 0.7}), SCEN, TNF, ALL, False)
        self.assertEqual(r['M']['I_local']['label'], 'opposite')                        # -0.5 - 0.5
        self.assertIsNone(r['M']['ratio_local_over_block'])                              # I_block = 0.2
        self.assertEqual(r['labels']['I_block_M'], 'not_stable')

    def test_gap_algebra_and_delivery(self):
        r = K.panel_direction(world({'L01': 0.3, 'L10': 1.0, 'L11': 2.0, 'V': 1.5, 'VW': 3.8}, Y={'L10': 1, 'L11': 4}), SCEN, TNF, ALL, False)
        self.assertAlmostEqual(r['M']['gap']['eq'], r['M']['d0']['eq'] - r['M']['d1']['eq'])
        self.assertAlmostEqual(r['M']['d0']['eq'], 0.5)
        self.assertAlmostEqual(r['M']['d1']['eq'], 1.8)
        self.assertEqual(r['delivery']['k_increment_L11_vs_L10']['label'], 'multi_scenario')
        one = world({}, Y={'L11': 0})
        one['Y']['L11'] = const(lambda i: int(i in ('NQ01-0', 'NQ01-1', 'NQ01-2')))
        self.assertEqual(K.panel_direction(one, SCEN, TNF, ALL, False)['delivery']['total_L11_vs_L00']['label'], 'none')   # one scenario

    def test_kuc_replication(self):
        r = K.panel_direction(world({'VW': -2.0, 'V': 0.0, 'VE': 0.0, 'VK': -2.0}, new=True), SCEN, TNF, ALL, True)
        self.assertEqual(r['kuc_replication']['label'], 'none')                          # wrong sign for R
        r = K.panel_direction(world({'VW': 2.0, 'VE': 0.1, 'VK': 2.0}, Y={'VW': 3}, new=True), SCEN, TNF, ALL, True)
        self.assertEqual(r['kuc_replication']['label'], 'single_W')
        self.assertAlmostEqual(r['kuc_replication']['W_over_K'], 1.0)


class Update(unittest.TestCase):
    def test_value_substitution(self):
        import torch
        import lvk_run as R
        QM = R.gdn_module()
        orig = QM.torch_recurrent_gated_delta_rule
        g = torch.Generator().manual_seed(2)
        r = lambda *s: torch.randn(*s, generator=g)   # noqa: E731
        q, k0, k1, v0, v1 = [r(1, 1, 32, 128).to(torch.bfloat16) for _ in range(5)]
        gg, b, S = -torch.rand(1, 1, 32, generator=g), torch.rand(1, 1, 32, generator=g).to(torch.bfloat16), r(1, 32, 128, 128) * 0.1
        kw = dict(g=gg, beta=b, output_final_state=True, use_qk_l2norm_in_kernel=True)
        o_ref, S_ref = orig(q, k0, v1, initial_state=S.clone(), **kw)
        o10, S10, _ = R.custom_update(q, k0, k0, v1, gg, b, S.clone(), True, True, QM.l2norm)
        self.assertTrue(R.bit_equal(o_ref, o10)[0] and R.bit_equal(S_ref, S10)[0])       # L10 == original kernel fed v1
        _, S11, err = R.custom_update(q, k0, k1, v1, gg, b, S.clone(), True, True, QM.l2norm, oracle=True)
        self.assertLessEqual(err, R.KUCR.ORACLE_TOL)
        _, S01, _ = R.custom_update(q, k0, k1, v0, gg, b, S.clone(), True, True, QM.l2norm)
        _, S00, _ = R.custom_update(q, k0, k0, v0, gg, b, S.clone(), True, True, QM.l2norm)
        I = ((S11 - S10) - (S01 - S00)).double()
        bt = b.float()[0, 0].double()
        k0n = QM.l2norm(k0.float().transpose(1, 2)[0, :, 0], dim=-1, eps=1e-6).double()
        k1n = QM.l2norm(k1.float().transpose(1, 2)[0, :, 0], dim=-1, eps=1e-6).double()
        dv = (v1.float() - v0.float()).transpose(1, 2)[0, :, 0].double()
        want = bt[:, None, None] * (k1n - k0n)[:, :, None] * dv[:, None, :]              # local interaction = beta (k1 - k0)(v1 - v0)^T
        self.assertLess(float((I[0] - want).abs().max() / want.abs().max()), 1e-4)


class Wiring(unittest.TestCase):
    def test_budget(self):
        import lvk_run as R
        f, p = R.LIMITS['formal'], R.LIMITS['preflight']
        traj_f = 48 * 4 * 4 + 48 * (4 * 9 + 1)
        traj_p = 2 * 4 * 4 + 2 * (4 * 9 + 1)
        self.assertEqual((f['t1'], f['c_t2'], f['trajectories'], f['refs']), (traj_f, traj_f, traj_f, 96 * 4 * 4))
        self.assertEqual(traj_f, 2544)
        self.assertEqual((p['t1'], p['trajectories'], p['refs']), (traj_p, traj_p, 4 * 4 * 4))
        self.assertEqual(f['decode_forwards'], f['t1'] + f['n_steps'] + f['c_t2'] + f['refs'])
        self.assertEqual(p['decode_forwards'], p['t1'] + p['n_steps'] + p['c_t2'] + p['refs'])
        self.assertEqual(f['shadow'], 48 * 4 * (84 + 126))
        self.assertEqual(p['shadow'], 2 * 4 * (84 + 126))
        self.assertEqual(f['formation_token_forwards'], 6375 + 6390)
        self.assertAlmostEqual(R.GPU_CAP_S['formal'] + 2 * R.GPU_CAP_S['preflight'], 1.8 * 3600)
        self.assertEqual(len(R.all_units()), 96)
        self.assertEqual([u['item_id'] for u in R.plan('preflight', 0, 1)].count('LVK-H-NA-NQ01-ABC-A'), 1)
        w0, w1 = R.plan('formal', 0, 2), R.plan('formal', 1, 2)
        self.assertEqual(len(w0) + len(w1), 96)


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
