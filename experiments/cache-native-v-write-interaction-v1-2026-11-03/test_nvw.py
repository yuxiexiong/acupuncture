"""CPU tests for NVW-01: synthetic cases for the four required patterns (native continuous change but still stopping, effect only after V
restoration, reverse, all zero) plus delivery and ratio rules; term statistics vs the custom update; budget.
CUDA_VISIBLE_DEVICES= python test_nvw.py [RECEIPT]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import nvw_core as K  # noqa: E402

SC = [f'NQ0{k}' for k in range(1, 7)]
IDS = [f'{s}-{j}' for s in SC for j in range(8)]
SCEN = {i: i.split('-')[0] for i in IDS}
ALL = set(IDS)
TNF = {i for i in IDS if int(i.split('-')[1]) < 5}


def const(v):
    return {i: v(i) if callable(v) else v for i in IDS}


def ycount(k):
    return const(lambda i: int(int(i.split('-')[1]) < k))


def world(G=None, M=None, Y=None):
    """R family arms over backgrounds T (0) and V (1).  Defaults: zero effects."""
    base = {'T': 0.0, 'V': 0.0, 'Q': 0.0, 'F': 0.0, 'RTW': 0.0, 'RTK': 0.0, 'RVW': 0.0, 'RVK': 0.0}
    Gv, Mv = dict(base, **(G or {})), dict(base, **(M or {}))
    yb = {'T': 0, 'V': 0, 'Q': 0, 'F': 0, 'RTW': 0, 'RTK': 0, 'RVW': 0, 'RVK': 0}
    Yv = dict(yb, **(Y or {}))
    return {'G': {a: const(v) for a, v in Gv.items()}, 'M': {a: const(v) for a, v in Mv.items()}, 'Y': {a: ycount(k) for a, k in Yv.items()}}


class Patterns(unittest.TestCase):
    def fam(self, Z):
        return K.family(Z, SCEN, 'R', TNF, ALL)

    def test_native_continuous_still_stopping(self):
        r = self.fam(world(G={'RTW': 1.0, 'RTK': 1.2}, M={'RTW': 0.6, 'RTK': 0.7, 'RVW': 0.6, 'RVK': 0.7}))
        self.assertEqual(r['labels']['native_first_step_W'], 'expected')
        self.assertEqual(r['labels']['delivery_W_unrestored'], 'none')                  # still stopping: no Y change
        self.assertEqual(r['labels']['interaction_M_W'], 'not_stable')

    def test_only_after_v_restoration(self):
        r = self.fam(world(M={'RVW': 2.0, 'RVK': 2.1}, Y={'V': 2, 'RVW': 6, 'RVK': 6}))
        self.assertEqual(r['labels']['target_competition_W_unrestored'], 'not_stable')
        self.assertEqual(r['labels']['target_competition_W_restored'], 'expected')
        self.assertEqual(r['labels']['interaction_M_W'], 'expected')
        self.assertEqual(r['labels']['delivery_W_restored'], 'multi_scenario')

    def test_reverse_and_zero(self):
        r = self.fam(world(G={'RTW': -1.0}, M={'RTW': -1.0}))
        self.assertEqual(r['labels']['native_first_step_W'], 'opposite')
        self.assertEqual(r['labels']['target_competition_W_unrestored'], 'opposite')
        z = self.fam(world())
        self.assertTrue(all(v in ('not_stable', 'none') for v in z['labels'].values()))

    def test_w_boundary_and_ratios(self):
        r = self.fam(world(G={'RTK': 1.0, 'RTW': 0.1, 'Q': 2.0}, M={'RVW': 1.0, 'RVK': 2.0, 'F': 4.0}))
        self.assertTrue(r['W_boundary']['G|T'])
        self.assertAlmostEqual(r['ratios']['G|T']['K_over_ref'], 0.5)                     # 1.0 / (Q - T = 2.0)
        self.assertAlmostEqual(r['ratios']['M|V']['W_over_K'], 0.5)
        self.assertAlmostEqual(r['ratios']['M|V']['W_over_ref'], 0.25)                    # 1.0 / (F - V = 4.0)
        self.assertIsNone(self.fam(world(G={'RTW': 1.0, 'Q': 0.3}))['ratios']['G|T']['W_over_ref'])   # |ref| < 0.5

    def test_scenario_rule(self):
        three = lambda i: 2.0 if SCEN[i] in SC[:3] else -0.3   # noqa: E731  mean 0.85 but 3/6
        Z = world()
        Z['G']['RTW'] = const(three)
        self.assertEqual(self.fam(Z)['labels']['native_first_step_W'], 'not_stable')
        Y = world(Y={'RTW': 0})
        Y['Y']['RTW'] = const(lambda i: int(i in ('NQ01-0', 'NQ01-1', 'NQ01-2')))         # net 3 but one scenario
        self.assertEqual(self.fam(Y)['delivery']['T|W']['label'], 'none')

    def test_sign_for_addition(self):
        Z = {'G': {}, 'M': {}, 'Y': {}}
        for a in ('T', 'V', 'Q', 'F', 'AQW', 'AQK', 'AFW', 'AFK'):
            Z['G'][a] = const(0.0)
            Z['M'][a] = const(-2.0 if a in ('AFW', 'AFK') else 0.0)
            Z['Y'][a] = ycount(8 if a not in ('AFW', 'AFK') else 2)
        r = K.family(Z, SCEN, 'A', TNF, ALL)
        self.assertEqual(r['labels']['target_competition_W_restored'], 'expected')
        self.assertEqual(r['labels']['interaction_M_W'], 'expected')                       # negative interaction expected for A
        self.assertEqual(r['labels']['delivery_W_restored'], 'multi_scenario')


class Stats(unittest.TestCase):
    def test_term_stats_vs_update(self):
        import torch
        import nvw_run as R
        QM = R.gdn_module()
        g = torch.Generator().manual_seed(5)
        r = lambda *s: torch.randn(*s, generator=g)   # noqa: E731
        q, k0, k1, v = [r(1, 1, 32, 128).to(torch.bfloat16) for _ in range(4)]
        gg, b, S = -torch.rand(1, 1, 32, generator=g), torch.rand(1, 1, 32, generator=g).to(torch.bfloat16), r(1, 32, 128, 128) * 0.1
        st = R.term_stats(k0, k1, v, gg, b, S, QM.l2norm)
        _, S0, _ = R.custom_update(q, k0, k0, v, gg, b, S.clone(), True, True, QM.l2norm)
        _, SE, _ = R.custom_update(q, k1, k0, v, gg, b, S.clone(), True, True, QM.l2norm)
        _, SW, _ = R.custom_update(q, k0, k1, v, gg, b, S.clone(), True, True, QM.l2norm)
        F_ = R.STAT_FIELDS
        nE = (SE - S0)[0].double().flatten(1).norm(dim=-1)
        nW = (SW - S0)[0].double().flatten(1).norm(dim=-1)
        self.assertLess(float(((st[:, F_.index('dE')] - nE).abs() / nE).max()), 1e-4)
        self.assertLess(float(((st[:, F_.index('dW')] - nW).abs() / nW).max()), 1e-4)
        self.assertLess(float((st[:, F_.index('cos_k0k1')]).abs().max()), 1.0)
        self.assertEqual(tuple(st.shape), (32, len(F_)))


class Wiring(unittest.TestCase):
    def test_budget(self):
        import nvw_run as R
        f, p = R.LIMITS['formal'], R.LIMITS['preflight']
        per = 4 * 16
        self.assertEqual((f['t1'], f['c_t2'], f['trajectories'], f['n_steps'], f['refs'], f['shadow']), (48 * per, 48 * per, 48 * per, 48 * per * 31, 48 * 4 * 10, 48 * 4 * 18 * 14))
        self.assertEqual(f['decode_forwards'], f['t1'] + f['n_steps'] + f['c_t2'] + f['refs'])
        self.assertEqual(f['decode_forwards'], 103296)
        self.assertEqual((p['t1'], p['c_t2'], p['n_steps'], p['refs'], p['shadow']), (2 * per, 2 * per, 2 * per * 31, 2 * 4 * 10, 2 * 4 * 18 * 14))
        self.assertEqual(p['decode_forwards'], 4304)
        self.assertEqual(R.GPU_CAP_S['formal'] + 2 * R.GPU_CAP_S['preflight'], 2.4 * 3600)
        self.assertEqual(R.BACKGROUNDS, {'T': ('T', 'T'), 'V': ('T', 'C'), 'Q': ('C', 'T'), 'F': ('C', 'C')})
        self.assertEqual(tuple(R.STOP), (248044, 248046))


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
