"""CPU tests for CGV-01: same-angle random rotation (angle and norm match to 1e-5, rotation toward the u component orthogonal to k0, raw-scale
equal to k0); unit counts and budget per group; descriptive rules (G2 3/3 scenarios, G1 4/6), read descriptor pass/fail, triage flag.
CUDA_VISIBLE_DEVICES= python test_cgv.py [RECEIPT]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cgv_core as K  # noqa: E402


def const(ids, v):
    return {i: v(i) if callable(v) else v for i in ids}


class Rotation(unittest.TestCase):
    def test_same_angle(self):
        import torch
        import cgv_run as R
        QM = R.gdn_module()
        g = torch.Generator().manual_seed(3)
        k0 = torch.randn(1, 1, 32, 128, generator=g).to(torch.bfloat16)
        km = (k0.float() + 0.8 * torch.randn(1, 1, 32, 128, generator=g)).to(torch.bfloat16)
        u = torch.load(R.RAND_U)['u'][0].repeat_interleave(2, dim=0)
        kr, st = R.rotate(k0, km, u, QM.l2norm)
        self.assertEqual(tuple(kr.shape), (1, 1, 32, 128))
        self.assertEqual(kr.dtype, torch.float32)
        self.assertLessEqual(st['cos_err_max'], R.ROT_TOL)
        self.assertLessEqual(st['norm_err_max'], R.ROT_TOL)
        f = lambda x: QM.l2norm(x.float()[0, 0], dim=-1, eps=1e-6).double()   # noqa: E731
        k0n, kmn, krn = f(k0), f(km), f(kr)
        self.assertTrue(torch.allclose((k0n * kmn).sum(-1), (k0n * krn).sum(-1), atol=1e-5))
        w = krn - (krn * k0n).sum(-1, keepdim=True) * k0n
        uu = u.double() - (u.double() * k0n).sum(-1, keepdim=True) * k0n
        cosw = (w * uu).sum(-1) / (w.norm(dim=-1) * uu.norm(dim=-1))
        self.assertTrue(bool((cosw > 1 - 1e-5).all()))                     # rotated toward u's orthogonal component
        self.assertTrue(torch.allclose(kr.float()[0, 0].norm(dim=-1), k0.float()[0, 0].norm(dim=-1), rtol=1e-5))
        self.assertTrue(torch.equal(R.rotate(k0, km, u, QM.l2norm)[0], kr))  # deterministic

    def test_u_frozen(self):
        import torch
        import cgv_run as R
        u = torch.load(R.RAND_U)['u']
        self.assertEqual(tuple(u.shape), (14, 16, 128))
        self.assertTrue(torch.allclose(u.norm(dim=-1), torch.ones(14, 16, dtype=torch.float64)))


class Rules(unittest.TestCase):
    def test_scenario_rule(self):
        ids2 = [f'GS0{s}-{j}' for s in (1, 2, 3) for j in range(6)]
        sc2 = {i: i.split('-')[0] for i in ids2}
        self.assertEqual(K.desc(const(ids2, 0.5), sc2)['descriptor'], 'stable_expected')
        two = const(ids2, lambda i: 1.0 if sc2[i] != 'GS03' else -0.1)        # 2/3 -> not stable under 3/3
        self.assertEqual(K.desc(two, sc2)['descriptor'], 'not_stable')
        ids6 = [f'NQ0{s}-{j}' for s in range(1, 7) for j in range(5)]
        sc6 = {i: i.split('-')[0] for i in ids6}
        four = const(ids6, lambda i: 1.0 if sc6[i] in ('NQ01', 'NQ02', 'NQ03', 'NQ04') else -0.2)
        self.assertEqual(K.desc(four, sc6)['descriptor'], 'stable_expected')    # 4/6 suffices on six scenarios
        self.assertEqual(K.desc(const(ids6, -0.5), sc6, sign=-1)['descriptor'], 'stable_expected')
        self.assertEqual(K.desc(const(ids6, 0.1), sc6)['descriptor'], 'not_stable')

    def test_read_descriptor_and_triage(self):
        ids = [f'NQ0{s}-{j}' for s in range(1, 7) for j in range(8)]
        sc = {i: i.split('-')[0] for i in ids}
        y = lambda k: const(ids, lambda i: int(int(i.split('-')[1]) < k))   # noqa: E731
        M00, Md = const(ids, 0.0), const(ids, 2.0)
        r = K.read_pair({'10': const(ids, 1.8), '01': const(ids, 0.0), '11': const(ids, 1.8)}, {'10': y(3), '01': y(0), '11': y(3)}, M00, y(0), Md, sc, set(ids), 1)
        self.assertEqual(r['old_label_descriptor'], 'direct_dominant')
        self.assertAlmostEqual(r['DE_over_g'], 0.9)
        r = K.read_pair({'10': const(ids, 0.1), '01': const(ids, 0.1), '11': const(ids, 0.2)}, {'10': y(0), '01': y(0), '11': y(0)}, M00, y(0), Md, sc, set(ids), 1)
        self.assertEqual(r['old_label_descriptor'], 'weak')
        self.assertIsNone(K.read_pair({'10': const(ids, 0.1), '01': const(ids, 0.0), '11': const(ids, 0.2)}, {c: y(0) for c in ('10', '01', '11')}, M00, y(0), Md, sc, set(ids), 1)['D_over_DE'])
        t = K.triage({'a': M00, 'b': const(ids, 0.1)}, {'a': y(0), 'b': y(0)}, 'a', 'b', sc, ids)
        self.assertFalse(t['continue'])
        t = K.triage({'a': M00, 'b': const(ids, 0.1)}, {'a': y(0), 'b': y(1)}, 'a', 'b', sc, ids)
        self.assertTrue(t['continue'])


class Wiring(unittest.TestCase):
    def test_units_and_budget(self):
        import cgv_run as R
        uf = R.units_for('formal')
        kinds = {}
        for u in uf:
            kinds[u['kind']] = kinds.get(u['kind'], 0) + 1
        self.assertEqual(kinds, {'g1': 48, 'g2': 27, 'g3c': 48})
        tr = {k: sum(R.unit_budget(u)['trajectories'] for u in uf if u['kind'] == k) for k in kinds}
        self.assertEqual(tr, {'g1': 528, 'g2': 639, 'g3c': 1392})
        lim = R.limits('formal')
        self.assertEqual(lim['decode_forwards'], lim['t1'] + lim['refs'] + lim['c_t2'] + lim['n_steps'])
        pre = R.units_for('preflight')
        self.assertEqual(sorted(u['kind'] for u in pre), sorted(['g1', 'g1', 'g2', 'g2', 'g2', 'g3c', 'g3c', 'bridge']))
        br = [u for u in pre if u['kind'] == 'bridge'][0]
        self.assertEqual({k: R.unit_budget(br)[k] for k in ('t1', 'trajectories', 'shadow', 'refs')}, {'t1': 4, 'trajectories': 10, 'shadow': 56, 'refs': 4})
        prep = R.units_for('prep')
        self.assertEqual(sum(u['kind'] == 'collect' for u in prep), 48)
        self.assertEqual(sum(u['kind'] == 'calib' for u in prep), 3)
        self.assertEqual(len(R.plan('formal', 0, 2)) + len(R.plan('formal', 1, 2)), len(uf))
        self.assertEqual(R.L12_COND, {'id': 'N_L12_C3621_D-1', 'kind': 'native', 'layer': 12, 'channel': 3621, 'dose': -1.0})


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
