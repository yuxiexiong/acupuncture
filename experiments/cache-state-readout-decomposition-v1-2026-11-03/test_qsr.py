"""CPU tests for QSR-01: frozen label / card rules both pass and fail; FP64 midpoint split (identity, endpoint reversal, single-variable
equal, zero difference, cancellation, failing identity gate); split vs real torch kernel D; budget arithmetic.
CUDA_VISIBLE_DEVICES= python test_qsr.py [RECEIPT]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import qsr_core as K  # noqa: E402

SC = [f'NQ0{k}' for k in range(1, 7)]
IDS = [f'{s}-{j}' for s in SC for j in range(8)]
SCEN = {i: i.split('-')[0] for i in IDS}


def ex(sS, sq, sa, sI=0.0, absI=0.05, cov=1.0, ids=IDS):
    f = lambda v, i: v(i) if callable(v) else v   # noqa: E731
    return {i: {'coverage': f(cov, i), 'sS': f(sS, i), 'sq': f(sq, i), 'sa': f(sa, i), 'sI': f(sI, i), 'absI': f(absI, i)} for i in ids}


class Labels(unittest.TestCase):
    def test_pass(self):
        self.assertEqual(K.label(ex(0.8, 0.1, 0.1), SCEN)['label'], 'S')
        self.assertEqual(K.label(ex(0.1, 0.7, 0.2), SCEN)['label'], 'q')
        self.assertEqual(K.label(ex(0.0, 0.2, 0.75), SCEN)['label'], 'a')

    def test_fail(self):
        self.assertEqual(K.label(ex(0.55, 0.2, 0.2), SCEN)['label'], 'mixed')                     # below 0.60
        self.assertEqual(K.label(ex(0.65, 0.55, -0.2), SCEN)['label'], 'mixed')                   # margin 0.10 < 0.15
        self.assertEqual(K.label(ex(0.8, 0.1, 0.1, absI=0.3), SCEN)['label'], 'mixed')            # |I| too large
        three = lambda i: 1.4 if SCEN[i] in SC[:3] else 0.2                                       # noqa: E731  eq 0.8, wins 3/6
        r = K.label(ex(three, lambda i: 0.1 if SCEN[i] in SC[:3] else 0.5, 0.0), SCEN)
        self.assertEqual((r['label'], r['scen_wins']['S']), ('mixed', 3))
        neg = K.label(ex(-0.8, -0.9, -1.0), SCEN)                                                 # highest but negative
        self.assertEqual(neg['label'], 'mixed')
        self.assertEqual(neg['scen_wins']['S'], 0)

    def test_judgeable(self):
        r = K.label(ex(0.8, 0.1, 0.1, cov=0.89), SCEN)
        self.assertEqual(r['label'], 'not_judgeable')
        cov = lambda i: 0.5 if i.endswith(('-0', '-1')) and SCEN[i] == 'NQ01' else 1.0           # noqa: E731  NQ01 6/8 = 0.75 < 0.80
        self.assertEqual(K.label(ex(0.8, 0.1, 0.1, cov=cov), SCEN)['label'], 'not_judgeable')
        cov = lambda i: 0.5 if i.endswith('-0') and SCEN[i] == 'NQ01' else 1.0                    # noqa: E731  7/8 = 0.875
        self.assertEqual(K.label(ex(0.8, 0.1, 0.1, cov=cov), SCEN)['label'], 'S')
        five = [i for i in IDS if SCEN[i] != 'NQ06']
        self.assertEqual(K.label(ex(0.8, 0.1, 0.1, ids=five), {i: SCEN[i] for i in five})['label'], 'not_judgeable')

    def test_card(self):
        gap = ('d1', 'd2', 'd3')
        S_ = {'label': 'S'}
        labels = {(p, d): S_ for p in ('Rk-V', 'Ak-F') for d in gap}
        dms = {(p, d): {i: (1.0 if p == 'Rk-V' else -1.0) for i in IDS} for p in ('Rk-V', 'Ak-F') for d in gap}
        self.assertEqual(K.card(labels, dms, SCEN, set(IDS), gap)['candidate'], 'S')
        l2 = dict(labels)
        l2[('Ak-F', 'd2')] = {'label': 'q'}
        self.assertIsNone(K.card(l2, dms, SCEN, set(IDS), gap)['candidate'])
        d2 = dict(dms)
        d2[('Ak-F', 'd3')] = {i: (-1.0 if SCEN[i] in SC[:3] else 1.0) for i in IDS}                # 3/6 negative
        self.assertIsNone(K.card(labels, d2, SCEN, set(IDS), gap)['candidate'])
        l3 = {(p, d): {'label': 'mixed'} for p in ('Rk-V', 'Ak-F') for d in gap}
        self.assertIsNone(K.card(l3, dms, SCEN, set(IDS), gap)['candidate'])


def ends(torch, seed, same=()):
    g = torch.Generator().manual_seed(seed)
    mk = lambda: {'qn': torch.randn(32, 128, generator=g, dtype=torch.float64) / 128 ** 0.5,                       # noqa: E731
                  'S': torch.randn(32, 128, 128, generator=g, dtype=torch.float64) * 0.1,
                  'a': torch.rand(32, generator=g, dtype=torch.float64), 'abs_err': torch.zeros(32, dtype=torch.float64)}
    d0, d1 = mk(), mk()
    for f in same:
        d1[f] = d0[f].clone()
    return d1, d0


class Split(unittest.TestCase):
    def rel(self, torch, t):
        return float(((sum(t['X'].values()) - t['dD']).norm(dim=-1) / t['dD'].norm(dim=-1)).max())

    def test_identity_and_reversal(self):
        import torch
        import qsr_run as R
        d1, d0 = ends(torch, 0)
        t = R.split_terms(d1, d0)
        self.assertLess(self.rel(torch, t), 1e-10)
        D1, D0 = d1['a'][:, None] * torch.einsum('hkv,hk->hv', d1['S'], d1['qn']), d0['a'][:, None] * torch.einsum('hkv,hk->hv', d0['S'], d0['qn'])
        self.assertLess(float(((t['dD'] - (D1 - D0)).norm(dim=-1) / (D1 - D0).norm(dim=-1)).max()), 1e-12)
        r = R.split_terms(d0, d1)
        for j in t['X']:
            self.assertLess(float((t['X'][j] + r['X'][j]).abs().max()), 1e-12)
        st = R.split_stats(t, d1['abs_err'], d0['abs_err'])
        self.assertTrue(R.identity_ok(st))
        F_ = R.SPLIT_FIELDS
        s = st[:, F_.index('sS')] + st[:, F_.index('sq')] + st[:, F_.index('sa')] + st[:, F_.index('sI')]
        self.assertLess(float((s - 1).abs().max()), 1e-10)

    def test_single_variable_equal(self):
        import torch
        import qsr_run as R
        for same, zero in ((('S',), ('S', 'I')), (('qn',), ('q', 'I')), (('a',), ('a', 'I')), (('qn', 'a'), ('q', 'a', 'I'))):
            t = R.split_terms(*ends(torch, 1, same))
            for j in zero:
                self.assertEqual(float(t['X'][j].abs().max()), 0.0, (same, j))
            self.assertLess(self.rel(torch, t), 1e-10)
        t = R.split_terms(*ends(torch, 2, ('qn', 'a')))                         # only S differs -> s_S = 1
        st = R.split_stats(t, torch.zeros(32, dtype=torch.float64), torch.zeros(32, dtype=torch.float64))
        self.assertLess(float((st[:, R.SPLIT_FIELDS.index('sS')] - 1).abs().max()), 1e-12)

    def test_zero_and_cancellation(self):
        import torch
        import qsr_run as R
        d1, d0 = ends(torch, 3, ('qn', 'S', 'a'))
        t = R.split_terms(d1, d0)
        self.assertEqual(float(t['dD'].abs().max()), 0.0)
        st = R.split_stats(t, d1['abs_err'], d0['abs_err'])
        self.assertTrue(R.identity_ok(st))
        self.assertTrue(bool(st[:, R.SPLIT_FIELDS.index('sS')].isnan().all()))
        self.assertEqual(float(st[:, R.SPLIT_FIELDS.index('resolvable')].max()), 0.0)
        d1, d0 = ends(torch, 4, ('qn',))                                         # S doubled, alpha halved: dD = 0, X_S and X_a cancel
        d1['S'], d1['a'] = d0['S'] * 2, d0['a'] / 2
        t = R.split_terms(d1, d0)
        self.assertLess(float(t['dD'].abs().max()), 1e-12)
        self.assertGreater(float(t['X']['S'].abs().max()), 1e-3)
        self.assertLess(float((sum(t['X'].values()) - t['dD']).abs().max()), 1e-12)
        self.assertTrue(R.identity_ok(R.split_stats(t, d1['abs_err'], d0['abs_err'])))

    def test_identity_gate_can_fail(self):
        import torch
        import qsr_run as R
        t = R.split_terms(*ends(torch, 5))
        t['X']['q'] = t['X']['q'] * (1 + 1e-6)
        self.assertFalse(R.identity_ok(R.split_stats(t, torch.zeros(32, dtype=torch.float64), torch.zeros(32, dtype=torch.float64))))

    def test_resolvable(self):
        import torch
        import qsr_run as R
        d1, d0 = ends(torch, 6)
        t = R.split_terms(d1, d0)
        nd = t['dD'].norm(dim=-1)
        d1['abs_err'] = nd / 10 * 1.01                                          # 5 x (2 x 0.101 nd) > nd -> not resolvable
        d0['abs_err'] = nd / 10 * 1.01
        self.assertEqual(float(R.split_stats(t, d1['abs_err'], d0['abs_err'])[:, R.SPLIT_FIELDS.index('resolvable')].max()), 0.0)
        d1['abs_err'] = d0['abs_err'] = nd / 10 * 0.99
        self.assertEqual(float(R.split_stats(t, d1['abs_err'], d0['abs_err'])[:, R.SPLIT_FIELDS.index('resolvable')].min()), 1.0)

    def test_vs_kernel(self):
        """Two real kernel calls (different q, S, g; same k, v, beta): split of decompose()'s D difference is exact; D from decompose
        matches the kernel output's D part (D + E + W reconstruction within 1e-5)."""
        import torch
        import qsr_run as R
        orig = R.gdn_module().torch_recurrent_gated_delta_rule
        g = torch.Generator().manual_seed(7)
        k = torch.randn(1, 1, 32, 128, generator=g)
        v = torch.randn(1, 1, 32, 128, generator=g)
        b = torch.rand(1, 1, 32, generator=g)
        decs = []
        for _ in range(2):
            q = torch.randn(1, 1, 32, 128, generator=g)
            gg = -torch.rand(1, 1, 32, generator=g)
            S = torch.randn(1, 32, 128, 128, generator=g) * 0.1
            o, _ = orig(q, k, v, g=gg, beta=b, initial_state=S.clone(), output_final_state=True, use_qk_l2norm_in_kernel=True)
            d = R.decompose({'q': q, 'k': k, 'v': v, 'g': gg, 'beta': b, 'S': S, 'o': o, 'l2': True}, orig)
            self.assertTrue(d['wired'])
            self.assertLess(float(d['err'].max()), 1e-5)
            decs.append(d)
        t = R.split_terms(decs[1], decs[0])
        self.assertLess(float(((t['dD'] - (decs[1]['D'] - decs[0]['D'])).norm(dim=-1) / t['dD'].norm(dim=-1)).max()), 1e-12)
        self.assertLess(self.rel(torch, t), 1e-10)
        self.assertTrue(R.identity_ok(R.split_stats(t, decs[1]['abs_err'], decs[0]['abs_err'])))


class Wiring(unittest.TestCase):
    def test_budget(self):
        import qsr_run as R
        ki = R.kernel_identity()
        self.assertFalse(ki['fla'] or ki['kernels'] or ki['causal_conv1d'])
        self.assertEqual(R.LIMITS['formal']['decode_forwards'], 48 * 4 * 6 * 2)
        self.assertEqual(R.LIMITS['preflight']['decode_forwards'], 2 * 4 * 6 * 2 * 2)
        self.assertEqual(R.LIMITS['formal']['formations'], 48 * 5)
        self.assertEqual(R.LIMITS['preflight']['formations'], 2 * 5)
        self.assertEqual(len(R.PAIRS) * 2 * 4 * 48, 1920)
        self.assertEqual(len(R.PAIRS) * 2 * 4 * 2, 80)
        self.assertEqual(R.GPU_CAP_S['formal'] + R.GPU_CAP_S['preflight'], 0.80 * 3600)
        self.assertEqual(tuple(R.PREFLIGHT_ITEMS), ('NA-NQ01-ABC-A', 'NA-NQ02-ABC-B'))
        self.assertEqual(R.ARMS.keys(), {'V', 'F', 'Rk', 'Ak', 'Rrk', 'Ark'})


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
