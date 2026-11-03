"""CPU tests for NMT-01 (guideline 6.2: every reading shown satisfiable and not satisfiable on synthetic data).
Scaling: block norms matched, direction kept, zero rules (incl. Unmatchable).  RND: norm matched, exactly rank-1 along k_hat, rho shared by
b.  build_arms on synthetic rank-1 increments with identical layer 13; apply_X on a cache-shaped object (only G-layer S changes, one cast).
Read-outs: sum-then-divide ratio, denominator guard, bad-draw guard, shared bootstrap.  Readings: near_reference / insufficient / one_sided /
overcompensation / partial / unscaled and the background label, each both ways; I_S annotation.  End to end: analysis entry point on
records with the real key structure.  Budget arithmetic.
CUDA_VISIBLE_DEVICES= python test_nmt.py [RECEIPT]"""
import json
import os
import sys
import types as TY
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import nmt_core as NC  # noqa: E402

SCN = [f'NQ0{k}' for k in range(1, 7)]
IDS = [f'{s}-{j}' for s in SCN for j in range(8)]
SCEN = {i: i.split('-')[0] for i in IDS}


def rs(phi, lo=None, hi=None, den=1.0):
    iv = None if lo is None else [lo, hi]
    return {'num': phi * den if phi is not None else None, 'den': den, 'phi': phi, 'interval': iv, 'interval_available': iv is not None}


class Scaling(unittest.TestCase):
    def test_scale_blocks(self):
        import torch
        g = torch.Generator().manual_seed(1)
        src = torch.randn(1, 4, 6, 5, generator=g, dtype=torch.float64)
        ns = NC.head_norms(src)
        nt = torch.tensor([2.0, 0.5, 0.0, 3.0], dtype=torch.float64)
        x, c = NC.scale_blocks(src, ns, nt)
        got = NC.head_norms(x)
        self.assertTrue(torch.allclose(got, nt, rtol=1e-12, atol=0))
        cos = (x[0, 0].flatten() @ src[0, 0].flatten()) / (x[0, 0].norm() * src[0, 0].norm())
        self.assertAlmostEqual(float(cos), 1.0, places=12)
        self.assertEqual(float(x[0, 2].abs().max()), 0.0)          # src > 0, tgt = 0 -> 0
        src2 = src.clone()
        src2[0, 1] = 0
        x2, _ = NC.scale_blocks(src2, NC.head_norms(src2), torch.tensor([2.0, 0.0, 0.0, 3.0], dtype=torch.float64))
        self.assertEqual(float(x2[0, 1].abs().max()), 0.0)         # both zero -> 0
        with self.assertRaises(NC.Unmatchable):                     # src = 0, tgt > 0 -> engineering stop
            NC.scale_blocks(src2, NC.head_norms(src2), torch.tensor([2.0, 1.0, 0.0, 3.0], dtype=torch.float64))

    def test_rnd_block_and_rank1(self):
        import torch
        g = torch.Generator().manual_seed(2)
        k = torch.randn(1, 3, 6, generator=g, dtype=torch.float64)
        k = k / k.norm(dim=-1, keepdim=True)
        rho = torch.randn(3, 5, generator=g, dtype=torch.float64)
        n = torch.tensor([1.5, 0.2, 4.0], dtype=torch.float64)
        x = NC.rnd_block(n, k, rho)
        self.assertTrue(torch.allclose(NC.head_norms(x), n, rtol=1e-12, atol=0))
        self.assertLess(NC.rank1_residual(x, k), 1e-12)
        k_eps = k * (1 - 3.5e-4)                                    # kernel l2norm with eps inside rsqrt: norm slightly < 1
        x2 = NC.rnd_block(n, k_eps, rho)
        self.assertTrue(torch.allclose(NC.head_norms(x2), n, rtol=1e-12, atol=0))
        self.assertLess(NC.rank1_residual(x2, k_eps), 1e-12)
        other = torch.randn(1, 3, 6, generator=g, dtype=torch.float64)
        self.assertGreater(NC.rank1_residual(x, other / other.norm(dim=-1, keepdim=True)), 0.1)   # wrong axis is detected

    def test_is_descriptor(self):
        import torch
        T0 = {13: torch.ones(1, 1, 2, 2, dtype=torch.float64)}
        T1 = {13: 3 * torch.ones(1, 1, 2, 2, dtype=torch.float64)}
        X0 = {13: torch.zeros(1, 1, 2, 2, dtype=torch.float64)}
        X1 = {13: torch.ones(1, 1, 2, 2, dtype=torch.float64)}
        d = NC.is_descriptor(X0, X1, T0, T1)
        self.assertAlmostEqual(d['ratio_all'], 0.5)
        self.assertAlmostEqual(d['cos_all'], 1.0)


class Arms(unittest.TestCase):
    def synth(self, ratio_deep=2.0):
        """S[cell][layer] with rank-1 increments dS(s,b) = beta k_b (v1 - v0)^T; layer 13 identical across sources."""
        import torch
        G = (13, 14, 16)
        g = torch.Generator().manual_seed(3)
        H, dk, dv = 2, 4, 3
        khat = {b: {l: None for l in G} for b in '01'}
        S = {c: {} for c in ('000', '001', '010', '011', '100', '101', '110', '111')}
        for l in G:
            base = {c: torch.randn(1, H, dk, dv, generator=g).float() for c in ('0', '1')}
            dv0 = torch.randn(H, dv, generator=g, dtype=torch.float64)
            for b in '01':
                k = torch.randn(1, H, dk, generator=g, dtype=torch.float64)
                k = k / k.norm(dim=-1, keepdim=True)
                khat[b][l] = k.float()
                for s in '01':
                    scale = 1.0 if (l == 13 or s == '0') else ratio_deep
                    inc = (0.3 * scale) * k[0][:, :, None] * dv0[:, None, :]
                    S[f'{s}0{b}'][l] = base['0' if l == 13 else s].clone()
                    S[f'{s}1{b}'][l] = (S[f'{s}0{b}'][l].double() + inc[None]).float()
        return S, khat, G

    def test_build_arms(self):
        import nmt_run as R
        S, khat, G = self.synth()
        X, st, isd = R.build_arms(S, khat, G, 'ITEM', 'DIR')
        self.assertLessEqual(st['scale_err'], 1e-6)
        self.assertLessEqual(st['cos_err'], 1e-6)
        self.assertLessEqual(st['upg_err'], 1e-6)
        self.assertLessEqual(st['rnd_err'], 1e-6)
        self.assertLessEqual(st['rank1'], 1e-4)
        self.assertEqual(st['rho_sha']['RND0|0'], st['rho_sha']['RND0|1'])
        self.assertNotEqual(st['rho_sha']['RND0|0'], st['rho_sha']['RND1|0'])
        self.assertTrue(set(X) >= {'UP|0', 'UP|1', 'DN|0', 'DN|1', 'UPG|0', 'UPG|1', 'RND4|1'})
        self.assertAlmostEqual(st['coef']['UP|0']['median'], 2.0, places=5)
        self.assertGreater(isd['UP']['ratio_all'], 0)

    def test_apply_X_cache_like(self):
        import torch
        import nmt_run as R
        L = R.L
        S, khat, G = self.synth()
        kinds = ['linear_attention' if (i + 1) % 4 else 'full_attention' for i in range(17)]
        lay = []
        for i, k in enumerate(kinds):
            if k == 'linear_attention':
                rec = S['000'][i] if i in G else torch.zeros(1, 2, 4, 3)
                lay.append(TY.SimpleNamespace(recurrent_states=rec.clone(), conv_states=torch.ones(1, 3, 2)))
            else:
                lay.append(TY.SimpleNamespace(keys=torch.ones(1, 1, 2, 2), values=torch.ones(1, 1, 2, 2)))
        cache = TY.SimpleNamespace(layers=lay)
        X, _, _ = R.build_arms(S, khat, G, 'ITEM', 'DIR')
        Y, err = R.apply_X(cache, S, '0', '0', X['UP|0'], G, kinds)
        self.assertLessEqual(err, 1e-6)
        self.assertTrue(torch.equal(L._get(Y.layers[13], 'recurrent_states'), S['010'][13]))    # layer 13 == B(0,1,0)
        for i in G:
            self.assertTrue(torch.equal(L._get(cache.layers[i], 'recurrent_states'), S['000'][i]))   # receiver untouched
            self.assertTrue(torch.equal(L._get(Y.layers[i], 'conv_states'), L._get(cache.layers[i], 'conv_states')))


class Readouts(unittest.TestCase):
    def M_for(self, h0, h1, hup, hdn, noise=0.0):
        M = {}
        for r in '01':
            for b in '01':
                M[(r, 'Z', b)] = {i: 0.0 for i in IDS}
                for arm, h in (('0', h0), ('1', h1), ('UP', hup), ('DN', hdn), ('UPG', hup)):
                    M[(r, arm, b)] = {i: (h + noise * ((k % 3) - 1) if b == '1' else 0.0) for k, i in enumerate(IDS)}
        return M

    def test_sum_then_divide_and_guard(self):
        draws = NC.boot_draws(IDS, SCEN, n=200)
        rb = NC.receiver_block(self.M_for(0.5, 1.5, 1.4, 0.6, noise=0.1), '0', SCEN, IDS, draws, ('UPG',))
        self.assertAlmostEqual(rb['phi_up']['phi'], 0.9)
        self.assertAlmostEqual(rb['phi_dn']['phi'], 0.9)
        self.assertTrue(rb['phi_up']['interval_available'])
        rb2 = NC.receiver_block(self.M_for(0.5, 0.8, 0.7, 0.6), '0', SCEN, IDS, draws)       # D_src 0.3 < 0.5
        self.assertIsNone(rb2['phi_up']['phi'])
        self.assertEqual(NC.reading(rb2['phi_up'], rb2['phi_dn'])['label'], 'unscaled')

    def test_shared_draws_deterministic(self):
        self.assertEqual(NC.boot_draws(IDS, SCEN, n=5), NC.boot_draws(IDS, SCEN, n=5))

    def test_readings_both_ways(self):
        near = NC.reading(rs(0.9, 0.7, 1.1), rs(1.0, 0.8, 1.2))
        self.assertEqual(near['label'], 'near_reference')
        self.assertNotEqual(NC.reading(rs(0.9, 0.4, 1.1), rs(1.0, 0.8, 1.2))['label'], 'near_reference')      # lower bound < 0.5
        self.assertEqual(NC.reading(rs(0.3, 0.1, 0.6), rs(0.6, 0.4, 0.9))['label'], 'insufficient')
        self.assertNotEqual(NC.reading(rs(0.3, 0.1, 0.8), rs(0.6, 0.4, 0.9))['label'], 'insufficient')        # upper bound >= 0.75
        self.assertEqual(NC.reading(rs(0.9, 0.7, 1.1), rs(0.2, 0.0, 0.4))['label'], 'one_sided')
        self.assertNotEqual(NC.reading(rs(0.7, 0.5, 0.9), rs(0.2, 0.0, 0.4))['label'], 'one_sided')
        over = NC.reading(rs(1.6, 1.3, 1.9), rs(1.0, 0.8, 1.2))
        self.assertEqual(over['label'], 'overcompensation')
        self.assertIn('overcompensation', over['flags'])
        self.assertNotIn('overcompensation', NC.reading(rs(1.2, 1.0, 1.4), rs(1.0, 0.8, 1.2))['flags'])
        self.assertEqual(NC.reading(rs(0.6, 0.4, 0.8), rs(0.7, 0.5, 0.9))['label'], 'partial')
        self.assertIn('reversed', NC.reading(rs(-0.2, -0.5, 0.1), rs(0.6, 0.4, 0.9))['flags'])
        a = NC.reading(rs(0.3, 0.1, 0.6), rs(0.9, 0.7, 1.1), is_up=0.5, is_dn=1.0)
        self.assertIn('IS_unmatched_UP', a['flags'])
        self.assertNotIn('IS_unmatched_UP', NC.reading(rs(0.3, 0.1, 0.6), rs(0.9, 0.7, 1.1), is_up=1.0, is_dn=1.0)['flags'])

    def test_background_both_ways(self):
        draws = NC.boot_draws(IDS, SCEN, n=200)
        r0 = NC.receiver_block(self.M_for(0.5, 1.5, 1.4, 0.6, noise=0.05), '0', SCEN, IDS, draws)
        r1a = NC.receiver_block(self.M_for(0.5, 1.5, 0.9, 0.6, noise=0.05), '1', SCEN, IDS, draws)
        r1b = NC.receiver_block(self.M_for(0.5, 1.5, 1.35, 0.6, noise=0.05), '1', SCEN, IDS, draws)
        self.assertTrue(NC.background(r0, r1a, SCEN, IDS, draws, 'phi_up')['label'])
        self.assertFalse(NC.background(r0, r1b, SCEN, IDS, draws, 'phi_up')['label'])

    def test_y_block(self):
        Y = {}
        for r in '01':
            for b in '01':
                for a in ('Z', '0', '1', 'UP', 'DN'):
                    Y[(r, a, b)] = {i: int(b == '1' and a in ('1', 'UP') and i.endswith(('-0', '-1'))) for i in IDS}
        y = NC.y_block(Y, '1', IDS, SCEN, {('1', '0'): set(), ('1', '1'): set()})
        self.assertEqual(y['fixed_b_count_diff']['UP-1|b1']['net'], 0)
        self.assertEqual(y['H_Y']['UP'], 12)
        self.assertEqual(y['n_live'], 48)


class EndToEnd(unittest.TestCase):
    def fake(self):
        import nmt_run as R
        recs, nvb, sit = {}, {}, {}
        Hs = {'0': 0.5, '1': 1.5, 'UP': 1.4, 'DN': 0.6, 'UPG': 1.0}
        for k, i in enumerate(IDS):
            item = {'target': 'B' if k % 3 else 'A', 'first_listed': 'A', 'listed_codes': ['A', 'B'], 'question': 'q'}
            dirs, nd, sd = {}, {}, {}
            for d in R.DIRECTIONS:
                old = {c: {'M': (Hs['0'] if c[0] == '0' else Hs['1']) if (c[1] == '1' and c[2] == '1') else 0.0, 'x': 5} for c in R.MAIN}
                cross = {c: {'M': (Hs['1'] if c[0] == '0' else Hs['0']) if c[2] == '1' else 0.0} for c in R.SIT_CELLS}
                new = {}
                for c in R.MAIN_NEW + R.SEC_NEW:
                    arm, r, b = c.split('|')
                    a = 'UPG' if arm.startswith('RND') else arm
                    new[c] = {'C': {'M': Hs[a] if b == '1' else 0.0}}
                    if c in R.MAIN_NEW:
                        new[c]['N'] = {'text': 'ok' if r == '1' else '', 'termination': 'stop', 'reached_t2': r == '1'}
                isd = {a: {'ratio_all': 1.0, 'cos_all': 0.9} for a in ('UP', 'DN', 'UPG') + tuple(f'RND{j}' for j in range(5))}
                coef = {'UP|0': {'median': 2.0}, 'UPG|0': 1.8}
                dirs[d] = {'old': old, 'cross': cross, 'new': new, 'IS': isd, 'coef': coef, 'nvb_record_sha256': f'n{k}', 'sit_record_sha256': f's{k}'}
                nd[d] = {'cells': {c: {'N': {'text': 'ok' if c[0] == '1' else '', 'termination': 'stop', 'reached_t2': c[0] == '1'}} for c in R.MAIN}}
                sd[d] = {'new': {c: {'N': {'text': 'ok' if c[0] == '1' else '', 'termination': 'stop', 'reached_t2': c[0] == '1'}} for c in R.SIT_CELLS}}
            recs[i] = {'scenario': SCEN[i], 'item': item, 'directions': dirs, 'eng': {'cast': 0.0}}
            nvb[i] = {'directions': nd, '_sha': f'n{k}'}
            sit[i] = {'directions': sd, '_sha': f's{k}'}
        return recs, nvb, sit

    def test_analyse_entry_point(self):
        import nmt_analysis as A
        recs, nvb, sit = self.fake()
        out = A.analyse(recs, nvb, sit, yfun=lambda t, it: int(t['text'] == 'ok'), fo={'values': {}})
        x = out['directions']['N_L00_C4146_D-1']['main_tnf']
        self.assertEqual(out['n_target_not_first'], 32)
        for r in '01':
            self.assertAlmostEqual(x['receivers'][r]['phi_up']['phi'], 0.9)
            self.assertAlmostEqual(x['receivers'][r]['phi_dn']['phi'], 0.9)
            self.assertEqual(x['readings'][r]['label'], 'near_reference')
        self.assertAlmostEqual(x['receivers']['0']['phi_UPG']['phi'], 0.5)
        self.assertEqual(out['summary']['0']['near_reference'], 3)

    def test_provenance_mismatch_is_caught(self):
        import nmt_analysis as A
        recs, nvb, sit = self.fake()
        sit[IDS[0]]['_sha'] = 'other'
        with self.assertRaises(AssertionError):
            A.analyse(recs, nvb, sit, yfun=lambda t, it: 0, fo={'values': {}})


class Wiring(unittest.TestCase):
    def test_budget(self):
        import nmt_run as R
        f, p = R.LIMITS['formal'], R.LIMITS['preflight']
        self.assertEqual((f['t1'], f['c_t2'], f['sit_c_t2'], f['new_c_t2']), (1536, 1536, 768, 3840))
        self.assertEqual(f['c_t2'] + f['sit_c_t2'] + f['new_c_t2'], 6144)
        self.assertEqual((f['trajectories'], f['n_steps']), (1536, 47616))
        self.assertEqual(p['c_t2'] + p['sit_c_t2'] + p['new_c_t2'], 256)
        self.assertEqual(len(R.MAIN_NEW), 8)
        self.assertEqual(len(R.SEC_NEW), 12)
        self.assertAlmostEqual(R.GPU_CAP_S['formal'], 1.2 * 3600)
        self.assertEqual(len(R.plan('formal', 0, 2)) + len(R.plan('formal', 1, 2)), 48)


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
            json.dump({'status': 'passed' if res.wasSuccessful() and not res.skipped else 'failed', 'tests_run': res.testsRun, 'failures': len(res.failures),
                       'errors': len(res.errors), 'skipped': len(res.skipped), 'source_hashes': src, 'torch': torch.__version__}, f, indent=2)
            f.write('\n')
    sys.exit(0 if (res.wasSuccessful() and not res.skipped) else 1)


if __name__ == '__main__':
    main()
