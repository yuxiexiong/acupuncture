"""CPU tests for SIT-01.
Transplant arithmetic: same-source increment rebuilds S(r,1,b) bit for bit; cross-source equals the FP64 reference within CAST_TOL; inputs are
not modified; the cast gate passes on float32 and fails on bfloat16 (both sides shown).  build_transplant on a real HF-style cache object:
only the G-layer recurrent states change, everything else bit-equal.  Read-outs: H / A0 / A1 / G on synthetic margins with known values
(positive, negative and zero transfer reproduced), ratio guard, bootstrap determinism, Y block with receiver-stopped inputs; the analysis
entry point end to end on records with the real key structure; first-order references recomputed from the real NBR JSON equal the values
registered in CONTRACT §4.3; budget arithmetic.
CUDA_VISIBLE_DEVICES= python test_sit.py [RECEIPT]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import sit_core as SC  # noqa: E402

SCN = [f'NQ0{k}' for k in range(1, 7)]
IDS = [f'{s}-{j}' for s in SCN for j in range(8)]
SCEN = {i: i.split('-')[0] for i in IDS}
REGISTERED_FO = {   # CONTRACT §4.3 (rounded to 3 decimals)
    'N_L00_C4146_D-1': {'A0': (0.300, 0.363), 'A1': (0.306, 0.613)},
    'N_L00_C1210_D-1': {'A0': (0.286, 0.332), 'A1': (0.308, 0.330)},
    'R0_L00_D-1': {'A0': (0.321, 0.398), 'A1': (0.353, 0.461)},
    'N_L00_C1343_D-1': {'A0': (0.648, 0.498), 'A1': (0.746, 0.204)},
}


def synth_M(z=(0.0, 0.0, 0.0, 0.0), h00=0.3, h11=2.0, h01=0.3, h10=2.0, noise=0.0):
    """Z(r,b) = z; F(r,s,0) = Z(r,0); F(r,s,1) = Z(r,1) + H(r,s) (+ deterministic per-input noise on the b = 1 new cells only)."""
    z00, z01, z10, z11 = z
    Z = {('0', '0'): z00, ('0', '1'): z01, ('1', '0'): z10, ('1', '1'): z11}
    H = {'00': h00, '01': h01, '10': h10, '11': h11}
    M = {}
    for r in '01':
        for b in '01':
            M[(r, '-', b)] = {i: Z[(r, b)] for i in IDS}
            for s in '01':
                M[(r, s, b)] = {i: Z[(r, b)] + (H[r + s] if b == '1' else 0.0) + (noise * ((k % 3) - 1) if (r != s and b == '1') else 0.0)
                                for k, i in enumerate(IDS)}
    return M


class Transplant(unittest.TestCase):
    def setUp(self):
        import torch
        g = torch.Generator().manual_seed(7)
        self.S = {c: (torch.randn(1, 4, 8, 8, generator=g) * (1 + int(c[0]))).float() for c in ('00', '01', '10', '11')}

    def test_same_source_rebuilds_bitwise(self):
        import torch
        for r in '01':
            new, _, err = SC.transplant_state(self.S[f'{r}0'], self.S[f'{r}1'], self.S[f'{r}0'])
            self.assertTrue(torch.equal(new, self.S[f'{r}1']))
            self.assertLessEqual(err, 1e-7)

    def test_cross_source_value_and_inputs_untouched(self):
        import torch
        before = {k: v.clone() for k, v in self.S.items()}
        new, exact, err = SC.transplant_state(self.S['00'], self.S['11'], self.S['10'])
        ref = self.S['00'].double() + self.S['11'].double() - self.S['10'].double()
        self.assertEqual(new.dtype, torch.float32)
        self.assertTrue(torch.equal(exact, ref))
        self.assertLessEqual(float((new.double() - ref).abs().max() / ref.abs().max()), 1e-6)
        self.assertLessEqual(err, 1e-6)
        self.assertFalse(torch.equal(new, self.S['01']))
        self.assertTrue(all(torch.equal(before[k], self.S[k]) for k in self.S))

    def test_cast_gate_both_sides(self):
        import torch
        import sit_run as R
        _, _, e32 = SC.transplant_state(self.S['00'], self.S['11'], self.S['10'])
        bf = {k: v.to(torch.bfloat16) for k, v in self.S.items()}
        _, _, e16 = SC.transplant_state(bf['00'], bf['11'], bf['10'])
        self.assertLessEqual(e32, R.CAST_TOL)       # satisfiable
        self.assertGreater(e16, R.CAST_TOL)         # not satisfiable when the cast is lossy

    def test_increment_stats(self):
        import torch
        S = {c: {13: torch.ones(1, 2, 2, 2) * k} for k, c in enumerate(('000', '001', '010', '011', '100', '101', '110', '111'))}
        st = SC.increment_stats(S, [13])['13']
        self.assertAlmostEqual(st['norm_dS_s0_b0'], 2 * 8 ** 0.5)
        self.assertAlmostEqual(st['cos_dS_b0'], 1.0)
        self.assertAlmostEqual(st['norm_IS_s0'], 0.0)


class CacheWiring(unittest.TestCase):
    def test_build_transplant_on_cache_like_object(self):
        """Cache-shaped object (layers with recurrent_states / conv_states / keys / values attributes, as L._get reads them); the real
        transformers DynamicCache is exercised by readiness/gpu_smoke.py on the model.  Only the G-layer recurrent states change."""
        import types as TY
        import torch
        import sit_run as R
        L = R.L
        kinds = ['linear_attention' if (i + 1) % 4 else 'full_attention' for i in range(32)]
        G = [i for i, k in enumerate(kinds) if k == 'linear_attention' and i >= R.NVBR.SPLIT]
        self.assertEqual(tuple(G), R.G14)
        g = torch.Generator().manual_seed(3)
        lay = []
        for k in kinds:
            if k == 'linear_attention':
                lay.append(TY.SimpleNamespace(recurrent_states=torch.randn(1, 2, 4, 4, generator=g), conv_states=torch.randn(1, 6, 4, generator=g)))
            else:
                lay.append(TY.SimpleNamespace(keys=torch.randn(1, 2, 3, 4, generator=g), values=torch.randn(1, 2, 3, 4, generator=g)))
        cache = TY.SimpleNamespace(layers=lay)
        S = {cell: {l: torch.randn(1, 2, 4, 4, generator=g) for l in G} for cell in R.MAIN}
        for l in G:
            S['000'][l] = L._get(cache.layers[l], 'recurrent_states').clone()
        before = {(i, f): L._get(cache.layers[i], f).clone() for i, _k, f in L.component_tensors(cache, kinds)}
        X, err, changed = R.build_transplant(cache, S, '0', '1', '0', G, kinds)
        self.assertLessEqual(err, R.CAST_TOL)
        self.assertEqual(changed, G)
        for i, _k, f in L.component_tensors(cache, kinds):
            self.assertTrue(torch.equal(L._get(cache.layers[i], f), before[(i, f)]))       # receiver untouched
            got = L._get(X.layers[i], f)
            if f == 'recurrent_states' and i in G:
                # receiver r = 0, b = 0, source s = 1: S(0,0,0) + S(1,1,0) - S(1,0,0)
                ref = (S['000'][i].double() + S['110'][i].double() - S['100'][i].double()).float()
                self.assertTrue(torch.equal(got, ref))
            else:
                self.assertTrue(torch.equal(got, before[(i, f)]))
        with self.assertRaises(AssertionError):                                            # wrong receiver state is refused
            S2 = {c: dict(v) for c, v in S.items()}
            S2['000'][G[3]] = S2['000'][G[3]] + 1
            R.build_transplant(cache, S2, '0', '1', '0', G, kinds)


class Readouts(unittest.TestCase):
    def test_positive_negative_zero_transfer(self):
        m = SC.margins_block(synth_M(h01=1.5, h10=0.8), SCEN, set(IDS))       # transfer both ways
        self.assertAlmostEqual(m['A0']['eq'], 1.2)
        self.assertAlmostEqual(m['A1']['eq'], 1.2)
        self.assertAlmostEqual(m['G']['eq'], 1.7)
        self.assertAlmostEqual(m['ratio_A0_G'], 1.2 / 1.7)
        self.assertEqual(m['A0']['scen_pos'], 6)
        m = SC.margins_block(synth_M(h01=0.3, h10=2.0), SCEN, set(IDS))       # no transfer: source irrelevant
        self.assertAlmostEqual(m['A0']['eq'], 0.0)
        self.assertAlmostEqual(m['A1']['eq'], 0.0)
        self.assertEqual(m['A0']['scen_pos'] + m['A0']['scen_neg'], 0)
        m = SC.margins_block(synth_M(h01=-0.5, h10=2.6), SCEN, set(IDS))      # opposite sign
        self.assertAlmostEqual(m['A0']['eq'], -0.8)
        self.assertAlmostEqual(m['A1']['eq'], -0.6)
        self.assertEqual(m['A1']['scen_neg'], 6)

    def test_bridge_to_nvb_and_baselines(self):
        m = SC.margins_block(synth_M(z=(0.4, -0.2, 1.0, 0.7), h01=1.0, h10=1.1), SCEN, set(IDS))
        self.assertAlmostEqual(m['H']['00']['eq'], 0.3)     # = DS0
        self.assertAlmostEqual(m['H']['11']['eq'], 2.0)     # = DS1
        self.assertAlmostEqual(m['A0']['eq'], 0.7)
        self.assertAlmostEqual(m['A1']['eq'], 0.9)
        self.assertAlmostEqual(m['effects']['011']['eq'], 1.0)
        self.assertAlmostEqual(m['effects']['010']['eq'], 0.0)

    def test_ratio_guard_and_bootstrap(self):
        m = SC.margins_block(synth_M(h11=0.6, h01=0.5), SCEN, set(IDS))        # G = 0.3 < 0.5 -> no ratio
        self.assertIsNone(m['ratio_A0_G'])
        self.assertIsNone(m['ratio_A1_G'])
        a = SC.margins_block(synth_M(h01=1.0, noise=0.4), SCEN, set(IDS))
        b = SC.margins_block(synth_M(h01=1.0, noise=0.4), SCEN, set(IDS))
        self.assertEqual(a['A0']['boot95'], b['A0']['boot95'])
        lo, hi = a['A0']['boot95']
        self.assertLess(lo, a['A0']['eq'] + 1e-12)
        self.assertGreater(hi, a['A0']['eq'] - 1e-12)
        self.assertLess(lo, hi)

    def test_y_block(self):
        Y = {}
        for r in '01':
            for b in '01':
                Y[(r, '-', b)] = {i: 0 for i in IDS}
                for s in '01':
                    Y[(r, s, b)] = {i: int(b == '1' and r == '1' and s == '1' and i.endswith(('-0', '-1'))) for i in IDS}
        stopped = {('0', '0'): set(IDS[:40]), ('0', '1'): set(IDS[:40]), ('1', '0'): set(), ('1', '1'): set()}
        y = SC.y_block(Y, SCEN, IDS, stopped)
        self.assertEqual(y['totals']['111'], 12)
        self.assertEqual(y['H_Y']['11'], 12)
        self.assertEqual(y['A1_Y'], 12)
        self.assertEqual(y['A0_Y'], 0)
        self.assertEqual(y['changes']['111']['n_scen_toward'], 6)
        self.assertEqual(y['receiver_live']['0']['n'], 8)
        self.assertEqual(y['receiver_live']['1']['H_Y']['1'], 12)


class EndToEnd(unittest.TestCase):
    def fake(self):
        """Records with the real SIT / NVB key structure; M chosen so that A0 = 0.5, A1 = 0.25 exactly, G = 1.0."""
        import sit_run as R
        H = {'00': 0.5, '11': 1.5, '01': 1.0, '10': 1.25}
        recs, nvb = {}, {}
        for k, i in enumerate(IDS):
            item = {'target': 'B' if k % 3 else 'A', 'first_listed': 'A', 'listed_codes': ['A', 'B'], 'question': 'q'}
            dirs, ndirs = {}, {}
            for d in R.DIRECTIONS:
                old = {c: {'M': (H[c[0] * 2] if c[1] == '1' and c[2] == '1' else 0.0), 'x': 5} for c in R.MAIN}
                new = {}
                for c in R.NEW_CELLS:
                    r, s, b = c
                    new[c] = {'C': {'M': H[r + s] if b == '1' else 0.0}, 'N': {'text': 'ok' if r == '1' else '', 'termination': 'stop',
                              'reached_t2': r == '1'}, 'x': 5 if r == '1' else 9}
                inc = {'13': {'norm_dS_s0_b0': 1.0}}
                dirs[d] = {'old': old, 'new': new, 'fF': 5, 'increment_stats': inc, 'nvb_record_sha256': f'h{k}'}
                ndirs[d] = {'cells': {c: {'N': {'text': 'ok' if (c[0] == '1') else '', 'termination': 'stop', 'reached_t2': c[0] == '1'}}
                                      for c in R.MAIN}}
            recs[i] = {'scenario': SCEN[i], 'item': item, 'directions': dirs, 'cast_err_max': 0.0, 'signed_zero_exceptions': 0}
            nvb[i] = {'directions': ndirs, '_sha': f'h{k}'}
        return recs, nvb

    def test_analyse_entry_point(self):
        import sit_analysis as A
        recs, nvb = self.fake()
        yfun = lambda t, it: int(t['text'] == 'ok')   # noqa: E731
        fo = A.first_order()
        out = A.analyse(recs, nvb, yfun=yfun, fo=fo)
        x = out['directions']['N_L00_C4146_D-1']
        self.assertEqual(out['n_target_not_first'], 32)
        self.assertAlmostEqual(x['main_tnf']['A0']['eq'], 0.5)
        self.assertAlmostEqual(x['main_tnf']['A1']['eq'], 0.25)
        self.assertAlmostEqual(x['main_tnf']['G']['eq'], 1.0)
        self.assertAlmostEqual(x['main_tnf']['ratio_A0_G'], 0.5)
        self.assertEqual(x['Y']['receiver_live']['0']['n'], 0)
        self.assertEqual(x['Y']['receiver_live']['1']['n'], 48)
        self.assertEqual(x['first_token_ne_fF']['010'], 48)
        self.assertIn('vs_first_order', x)

    def test_provenance_mismatch_is_caught(self):
        import sit_analysis as A
        recs, nvb = self.fake()
        nvb[IDS[0]]['_sha'] = 'other'
        with self.assertRaises(AssertionError):
            A.analyse(recs, nvb, yfun=lambda t, it: 0, fo={'values': {}, 'source_sha256': ''})


class Registered(unittest.TestCase):
    def test_first_order_matches_contract(self):
        import sit_analysis as A
        fo = A.first_order()['values']
        for d, v in REGISTERED_FO.items():
            self.assertAlmostEqual(fo[d]['A0']['g000'], v['A0'][0], places=3)
            self.assertAlmostEqual(fo[d]['A0']['g011'], v['A0'][1], places=3)
            self.assertAlmostEqual(fo[d]['A1']['g100'], v['A1'][0], places=3)
            self.assertAlmostEqual(fo[d]['A1']['g111'], v['A1'][1], places=3)


class Wiring(unittest.TestCase):
    def test_budget(self):
        import sit_run as R
        f, p = R.LIMITS['formal'], R.LIMITS['preflight']
        self.assertEqual((f['t1'], f['c_t2'], f['sit_c_t2'], f['trajectories'], f['n_steps']), (1536, 1536, 768, 768, 23808))
        self.assertEqual(f['decode_forwards'], 1536 + 1536 + 768 + 23808)
        self.assertEqual((p['t1'], p['c_t2'], p['sit_c_t2'], p['n_steps']), (64, 64, 32, 992))
        self.assertEqual(f['shadow'], 140 * 4 * 48)
        self.assertAlmostEqual(R.GPU_CAP_S['formal'] + 2 * R.GPU_CAP_S['preflight'], 1.5 * 3600)
        self.assertEqual(len(R.plan('formal', 0, 2)) + len(R.plan('formal', 1, 2)), 48)
        self.assertEqual(R.NEW_CELLS, ('010', '011', '100', '101'))


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
