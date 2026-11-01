"""CPU tests for B3-P1 (no weights).  CUDA_VISIBLE_DEVICES= python test_p1.py [RECEIPT_JSON]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import torch  # noqa: E402
import p1_core as K  # noqa: E402

D = 16


def z(n=38):
    return torch.zeros(n, D, dtype=torch.float64)


def unit(i):
    v = torch.zeros(D, dtype=torch.float64)
    v[i] = 1.0
    return v


class Steps(unittest.TestCase):
    def test_same_step_alignment(self):
        al, be = z(), z()
        for j in range(12):
            al[j], be[j] = unit(j % D), unit(j % D)          # each step alpha_j == beta_j, orthogonal across steps
        rows, M, s = K.steps(al, be, K.WINDOW, 1e-9)
        sh = K.shares(rows, M, 1e-12)
        self.assertEqual(K.label_same(sh['same_abs_share']), 'same_step_concentrated')
        self.assertLess(s['err_steps'], 1e-12)
        self.assertLess(s['err_M'], 1e-12)

    def test_pure_cross_step(self):
        al, be = z(), z()
        al[0] = unit(0)                                       # A changes early
        for j in range(1, 12):
            be[j] = unit(0) * 0.5 + unit(j) * 0.1             # B later grows along A's earlier direction
        rows, M, s = K.steps(al, be, K.WINDOW, 1e-9)
        sh = K.shares(rows, M, 1e-12)
        self.assertEqual(K.label_same(sh['same_abs_share']), 'cross_step_concentrated')
        self.assertGreater(sum(r['newB_oldA'] for r in rows), 0)
        self.assertAlmostEqual(sum(r['same'] for r in rows), 0.0)

    def test_mlp_vs_mixer_and_cancellation(self):
        al, be = z(), z()
        for j in range(12):
            if j % 2 == 1:                                    # MLP steps carry the growth
                al[j], be[j] = unit(1), unit(1)
        al[2], be[2] = unit(2), -unit(2)                      # one negative mixer step
        rows, M, _ = K.steps(al, be, K.WINDOW, 1e-9)
        sh = K.shares(rows, M, 1e-12)
        self.assertEqual(K.label_mlp(sh['S_MLP']), 'mlp_dominant')
        self.assertLess(sh['negative_total'], 0)
        al2, be2 = z(), z()
        for j in range(0, 12, 2):
            al2[j], be2[j] = unit(1), unit(1)
        rows2, M2, _ = K.steps(al2, be2, K.WINDOW, 1e-9)
        self.assertEqual(K.label_mlp(K.shares(rows2, M2, 1e-12)['S_MLP']), 'mixer_dominant')

    def test_zero_vectors_na(self):
        rows, M, s = K.steps(z(), z(), K.WINDOW, 1e-9)
        self.assertIsNone(rows[-1]['cos_ab'])
        self.assertIsNone(K.shares(rows, M, 1e-12)['S_MLP'])
        self.assertEqual(K.label_same(None), 'not_resolvable')

    def test_fixed_projection_closes_rotating_does_not(self):
        torch.manual_seed(0)
        al, be = torch.randn(38, D, dtype=torch.float64), torch.randn(38, D, dtype=torch.float64)
        e = unit(0)
        rows, M, s = K.steps(K.project(al, e), K.project(be, e), K.FULL, 1e-9)
        self.assertLess(s['err_steps'], 1e-12)                # fixed axis: exact closure
        # rotating axis: project each step on its own axis and sum dC -> does not equal the end C in any fixed space
        a = torch.zeros(D, dtype=torch.float64)
        b = torch.zeros(D, dtype=torch.float64)
        tot = 0.0
        for j in range(38):
            ej = unit(j % D)
            x, y = al[j] - (al[j] @ ej) * ej, be[j] - (be[j] @ ej) * ej
            ap, bp = a - (a @ ej) * ej, b - (b @ ej) * ej
            tot += 2 * float(x @ y) + 2 * float(ap @ y) + 2 * float(x @ bp)
            a, b = a + al[j], b + be[j]
        self.assertGreater(abs(tot - 2 * float(K.project(a[None], e)[0] @ K.project(b[None], e)[0])), 1e-3)

    def test_radial(self):
        c = unit(0) * 10
        a = -unit(0) * 1 + unit(1) * 3
        b = -unit(0) * 1 + unit(1) * 2 + unit(2)
        r = K.radial(a, b, c)
        self.assertAlmostEqual(r['along_c'], 2.0)
        self.assertAlmostEqual(r['aligned'], 2 * (1 + 6))
        self.assertTrue(r['a_dot_e'] < 0 and r['b_dot_e'] < 0)


class Blocks(unittest.TestCase):
    def test_exact_sum_and_labels(self):
        torch.manual_seed(1)
        v = [torch.randn(D, dtype=torch.float64) for _ in range(8)]
        t = K.block_terms(*v)
        aA, aB, aR, bA, bB, bR, ab, bb = v
        al, be = aA + aB + aR, bA + bB + bR
        dC = 2 * float(al @ be) + 2 * float(ab @ be) + 2 * float(al @ bb)
        self.assertAlmostEqual(t['own'] + t['other'] + t['rem'], dC)
        zero = torch.zeros(D, dtype=torch.float64)
        own_only = K.block_terms(unit(0), zero, zero, zero, unit(0), zero, zero, zero)
        self.assertEqual(K.label_block(K.block_share([own_only], 1e-12)), 'own_block_dominant')
        other_only = K.block_terms(zero, unit(0), zero, unit(0), zero, zero, zero, zero)
        self.assertEqual(K.label_block(K.block_share([other_only], 1e-12)), 'other_block_dominant')


class Labels(unittest.TestCase):
    def test_across_and_joint(self):
        scen = {f'P0{i}': ('x', 'x') for i in range(1, 7)}
        self.assertEqual(K.across({d: scen for d in range(4)})[0], 'x')
        weak = {f'P0{i}': ('x', 'x') if i <= 4 else ('x', 'y') for i in range(1, 7)}
        self.assertEqual(K.across({d: weak for d in range(4)})[0], 'condition_dependent')
        self.assertEqual(K.joint('a', 'a'), 'a')
        self.assertEqual(K.joint('a', 'b'), 'projection_sensitive')

    def test_registered(self):
        self.assertTrue(K.registered('cross_step_concentrated', 'cross_step_concentrated', 'mixed')['P1_cross_step'])
        self.assertFalse(K.registered('mixed', 'cross_step_concentrated', 'mixed')['P1_cross_step'])
        self.assertTrue(K.registered('x', 'x', 'other_block_dominant')['P2_not_own_block'])
        self.assertFalse(K.registered('x', 'x', 'own_block_dominant')['P2_not_own_block'])
        self.assertFalse(K.registered('x', 'x', 'condition_dependent')['P2_not_own_block'])

    def test_scenario_pairs(self):
        self.assertEqual(K.scenario_pairs({'P01-f0': 1, 'P01-f1': 2}), {'P01': (1, 2)})


class Wiring(unittest.TestCase):
    def test_import_runner(self):
        import p1_run as R
        self.assertEqual(len(K.STEP_NAMES), 38)
        self.assertEqual(K.STEP_NAMES[:12][-1], '18:mlp')
        self.assertEqual(set(R.WINDOW_G) <= set(R.G_LAYERS), True)


class Consumer(unittest.TestCase):
    def test_end_to_end_synthetic(self):
        import zlib
        import p1_run as R
        Dm = 24
        g = torch.Generator().manual_seed(3)
        W = {l: torch.randn(Dm, 4096, generator=g, dtype=torch.float64) / 40 for l in R.G_LAYERS}
        fix = [[l, h] for l in R.G_LAYERS for h in range(0, 32, 10)]
        u1 = [[l, h] for l in R.G_LAYERS for h in range(1, 32, 10)]
        u2 = [[l, h] for l in R.G_LAYERS for h in range(2, 32, 10)]
        names = ['N:CC', 'N:CFIX', 'N:CREST', 'N:CT', 'N:CUF1', 'N:CUF1c', 'N:CUF2', 'N:CUF2c']
        sets = {'N:CC': [], 'N:CFIX': fix, 'N:CREST': [x for x in ([[l, h] for l in R.G_LAYERS for h in range(32)]) if x not in fix],
                'N:CT': [[l, h] for l in R.G_LAYERS for h in range(32)], 'N:CUF1': u1,
                'N:CUF1c': [x for x in ([[l, h] for l in R.G_LAYERS for h in range(32)]) if x not in u1], 'N:CUF2': u2,
                'N:CUF2c': [x for x in ([[l, h] for l in R.G_LAYERS for h in range(32)]) if x not in u2]}
        res, gates = {}, {}
        for sc in range(1, 7):
            for f in (0, 1):
                iid = f'P0{sc}-f{f}'
                gg = torch.Generator().manual_seed(zlib.crc32(iid.encode()))
                entry = (torch.randn(Dm, generator=gg) * 3).to(torch.bfloat16)
                off = torch.randn(4096, generator=gg, dtype=torch.float64) * 2
                base = {l: torch.randn(4096, generator=gg, dtype=torch.float64) for l in R.G_LAYERS}
                Wm = torch.randn(Dm, Dm, generator=gg, dtype=torch.float64) / 5
                ten = {'extras': {}, 'trace': {}, 'counter': {}}
                for d in R.DIRECTIONS:
                    for nm in names:
                        key = f'{nm}|{d}'
                        hs = {(x[0], x[1]) for x in sets[nm]}
                        h = entry
                        ex, tr, cn = {}, {}, {}
                        for l in range(13, 32):
                            if l in R.G_LAYERS:
                                gno = base[l].clone()
                                for hh in range(32):
                                    if (l, hh) in hs:
                                        gno[hh * 128:(hh + 1) * 128] += off[hh * 128:(hh + 1) * 128]
                                gno = gno.to(torch.bfloat16)
                                m = (W[l] @ gno.double()).to(torch.bfloat16)
                                cn[f'{l}:gated_norm_out'] = gno
                                cn[f'{l}:out_proj'] = m
                            else:
                                m = (0.1 * torch.tanh(h.double())).to(torch.bfloat16)
                            a = h + m
                            fo = (Wm @ torch.tanh(a.double())).to(torch.bfloat16)
                            o = a + fo
                            ex[f'{l}:in'], ex[f'{l}:out'], tr[f'{l}:mix'], tr[f'{l}:mlp'] = h, o, m, fo
                            h = o
                        ex['final:h'] = h
                        ten['extras'][key], ten['trace'][key], ten['counter'][key] = ex, tr, cn
                rec = {'item': {'id': iid}, 'FIX': fix, 'UFIX': [u1, u2]}
                res[iid] = {}
                for d in R.DIRECTIONS:
                    res[iid][d] = {}
                    for sp, (A, B, _) in R.splits(rec).items():
                        y = {c: ten['extras'][f'{n}|{d}']['final:h'].double() for c, n in (('00', 'N:CC'), ('10', A), ('01', B))}
                        p0u = {'final': {'aligned': 2 * float((y['10'] - y['00']) @ (y['01'] - y['00']))}}
                        res[iid][d][sp] = R.analyse_unit(ten, rec, d, sp, W, p0u, gates)
        S = R.aggregate(res)
        self.assertTrue(gates['layer13_other_heads_unchanged'])
        self.assertLess(gates['max_err_M'], 1e-9)
        self.assertLess(gates['max_outproj_rel'], R.OUTPROJ_REL)
        L = S['FIX']['labels']
        for k in ('S_MLP_window', 'same_abs_share_full'):
            self.assertIn('joint', L[k])
        b = res['P01-f0'][R.DIRECTIONS[0]]['FIX']['blocks'][13]
        self.assertAlmostEqual(b['norm_aB'], 0.0)              # layer 13: A's history cannot reach B heads


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
