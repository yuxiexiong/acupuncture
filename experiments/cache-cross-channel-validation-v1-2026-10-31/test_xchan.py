"""CPU tests on the tiny randomly initialised Qwen3.5 of the bridge tests (8 layers; needle at layer 0; split after
layer 4; G = (5, 6)). The anchor gate is exercised end to end against a tiny run of the frozen bridge code."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'early-input-control-v1-2026-10-29'))
import xchan as X  # noqa: E402
import xchan_analysis as AN  # noqa: E402

B, F, L, T1 = X.B, X.F, X.L, X.T1
_spec = importlib.util.spec_from_file_location('xchan_t2', T1.STAGE2 / 'test_stage2.py')
T2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T2)

PROMPT = [9, 12, 20, 33, 41, 8, 17, 26, 30, 11, 14, 22]
LABELS = ['head'] * 2 + ['fact'] * 4 + ['question'] * 3 + ['instruction'] + ['tail'] + ['last']
TOKENS = [1, 2, 3, 5]
NATIVES, DOSES, N_RANDOM = (7, 11), (-1.0, 1.0, -0.5), 2
ANCHOR = X.native_id(7, -1.0)


def tiny_needles():
    return X.needles(NATIVES, DOSES, N_RANDOM)


def tiny_directions():
    return {r['id']: r for r in X.make_directions(32, N_RANDOM)}


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = T2.tiny()
        cls.engine = T2.fake_engine(cls.model)
        cls.types = L.layer_types(cls.model)
        needle = {'id': ANCHOR, 'kind': 'native', 'layer': 0, 'channel': 7, 'dose': -1.0}
        cls.bridge, _ = B.run_item(cls.engine, T2.REF, PROMPT, LABELS, 'tiny', TOKENS, n=8, split=5, needle=needle,
                                   keep_tensors=False)
        cls.body, cls.tensors = X.run_item(cls.engine, T2.REF, PROMPT, LABELS, 'tiny', TOKENS, tiny_needles(),
                                           tiny_directions(), bridge_rec=cls.bridge, n=8, split=5,
                                           preflight_extras=True, anchor=ANCHOR)


class RunItemTests(Base):
    def test_gates_and_counts(self):
        for g in ('formation', 'scoring', 'anchor', 'preflight_inert'):
            self.assertIn(g, self.body['gates'])
        n_needles, n_mech = 2 * 3 + 2, 2 + 2
        self.assertEqual(self.body['mech'], [X.native_id(7, -1.0), X.native_id(11, -1.0), 'R0_L00_D-1', 'R1_L00_D-1'])
        self.assertEqual(self.body['counts'], {'prefixes': 1 + n_needles + 4 * n_mech + 2,
                                               'scores': 1 + 2 * n_needles + 4 * n_mech + 5})
        self.assertEqual(len(self.body['scores']), 1 + 2 * n_needles + 4 * n_mech)

    def test_anchor_detects_mismatch(self):
        for field in ('Y_TC', 'Y_TR1'):
            bad = copy.deepcopy(self.bridge)
            bad['scores'][field]['logits_sha256'] = '0' * 64
            with self.assertRaises(AssertionError):
                X.run_item(self.engine, T2.REF, PROMPT, LABELS, 'tiny', TOKENS, tiny_needles()[:1] + tiny_needles()[-1:],
                           tiny_directions(), bridge_rec=bad, n=8, split=5, anchor=ANCHOR, keep_tensors=False)
        bad = copy.deepcopy(self.bridge)
        bad['donor_band_hashes']['R0'] = {k: '0' for k in bad['donor_band_hashes']['R0']}
        with self.assertRaises(AssertionError):
            X.run_item(self.engine, T2.REF, PROMPT, LABELS, 'tiny', TOKENS, tiny_needles()[:1], tiny_directions(),
                       bridge_rec=bad, n=8, split=5, anchor=ANCHOR, keep_tensors=False)

    def test_operations_not_trivial(self):
        m = self.body['manifest_digests']
        for x in self.body['mech']:
            self.assertNotEqual(m[f'TC|{x}']['deep'], m[x]['deep'], x)
            self.assertNotEqual(m[f'CT|{x}']['deep'], m['C']['deep'], x)
            self.assertNotEqual(m[f'TR0|{x}']['deep'], m[f'TR1|{x}']['deep'], x)
            self.assertNotEqual(m[x]['deep'], m['C']['deep'], x)
            self.assertEqual(m[f'CT|{x}']['shallow'], m['C']['shallow'])
            self.assertEqual(m[f'TC|{x}']['shallow'], m[x]['shallow'])
        # every needle changes its own formation; distinct needles give distinct formations
        deeps = [m[n['id']]['deep'] for n in tiny_needles()]
        self.assertEqual(len(set(deeps)), len(deeps))
        hashes = [s['logits_sha256'] for s in self.body['scores'].values()]
        self.assertEqual(len(set(hashes)), len(hashes))

    def test_random_band_seeds(self):
        mech = self.body['mech']
        self.assertEqual(self.body['random_band_norms'][ANCHOR]['seed_base'], X.SEED)
        bases = [self.body['random_band_norms'][x]['seed_base'] for x in mech]
        self.assertEqual(len(set(bases)), len(bases))
        for x in mech:
            for d in ('R0', 'R1'):
                for _i, v in self.body['random_band_norms'][x]['norms'][d].items():
                    for a, b in zip(v['target'], v['xi']):
                        self.assertAlmostEqual(a, b, places=4)

    def test_write_audit(self):
        for x, a in self.body['write_audit'].items():
            self.assertGreater(a['nominal_write_norm'], 0)
            self.assertAlmostEqual(a['nominal_write_norm'] / a['target_write_norm'], 1.0, places=4)
        a = self.body['write_audit'][X.native_id(7, -0.5)]
        self.assertAlmostEqual(a['target_write_norm'], 0.5 * T2.REF['residual_scales']['0'])

    def test_scores_and_tensors(self):
        sc = self.body['scores']
        self.assertEqual(sc['C']['tv_vs_C'], 0.0)
        for name, s in sc.items():
            self.assertTrue(s['final_norm']['normed_bitwise'])
            self.assertLess(s['eta'], 1e-4)
            self.assertGreaterEqual(s['tv_vs_C'], 0.0)
        self.assertEqual(set(self.tensors['v_natural']), {'C'} | {n['id'] for n in tiny_needles()})
        self.assertEqual(set(self.tensors['logits']), set(sc))
        self.assertEqual(tuple(self.tensors['v_natural']['C'][5].shape)[0], self.body['n_window'])
        for x in self.body['mech']:
            self.assertIn(f'Y|{x}||Y_TC|{x}', self.body['pairs'])

    def test_analysis_on_real_record_shape(self):
        """The readout code consumes a record produced by run_item (consumer-side check)."""
        rec = {'scores': self.body['scores']}
        cells = AN.cells_from_record(rec)
        mech = self.body['mech']
        table = {'b': {0: cells, 1: cells}}
        nonstop = {'b': {0: [1, 2], 1: [1, 2]}}
        ids = [n['id'] for n in tiny_needles()]
        res = AN.summarize(table, nonstop, ids, mech, [X.native_id(c, -1.0) for c in NATIVES], ['R0_L00_D-1', 'R1_L00_D-1'],
                           stop=tuple(T2.STOP))
        self.assertEqual(set(res['mechanism_summary']), set(mech))
        self.assertEqual(res['rank_vs_random']['deep']['n'], 2)
        g = AN.geometry_item(self.tensors['v_natural'], tiny_needles(), (5, 6))
        self.assertEqual(len(g['groups']['native_native']['5']), 1)
        self.assertEqual(len(g['groups']['native_random']['5']), 4)
        self.assertEqual(set(g['sign']), {'7', '11'})


class UnitTests(unittest.TestCase):
    def test_directions(self):
        rows = X.make_directions(32, 4)
        again = X.make_directions(32, 4)
        self.assertEqual([r['sha256'] for r in rows], [r['sha256'] for r in again])
        self.assertEqual(len({r['sha256'] for r in rows}), 4)
        for r in rows:
            self.assertAlmostEqual(sum(v * v for v in r['values']), 1.0, places=12)
        engine = T2.fake_engine(T2.tiny())
        cond = X.engine_condition({'id': 'R0', 'kind': 'direction', 'layer': 0, 'direction_id': 'R0', 'dose': -1.0},
                                  {r['id']: r for r in rows})
        engine._validate_condition(cond, T2.REF)

    def test_needle_lists_and_counts(self):
        nl = X.needles()
        self.assertEqual(len(nl), 34)
        mech = X.mech_ids(nl)
        self.assertEqual(len(mech), 14)
        self.assertIn(X.ANCHOR, mech)
        self.assertEqual(X.ANCHOR, B.E2.A0)
        self.assertEqual(sorted({n['channel'] for n in nl if n['kind'] == 'native'}), sorted(X.NATIVE))
        forms, scores = 1 + len(nl) + 4 * len(mech), 1 + 2 * len(nl) + 4 * len(mech)
        self.assertEqual((forms, scores), (91, 125))
        X.check_limits({'prefixes': forms + 2, 'scores': scores + 5}, 'preflight')
        X.check_limits({'prefixes': 12 * forms, 'scores': 12 * scores}, 'formal')
        with self.assertRaises(AssertionError):
            X.check_limits({'prefixes': 12 * forms + 1, 'scores': 12 * scores}, 'formal')

    def test_anchor_condition_matches_bridge(self):
        nd = next(n for n in X.needles() if n['id'] == X.ANCHOR)
        self.assertEqual(X.engine_condition(nd, {}), T1.engine_condition(B.F.A0))

    def test_tr_seed_base(self):
        mech = X.mech_ids(X.needles())
        bases = [X.tr_seed_base(x, mech) for x in mech]
        self.assertEqual(X.tr_seed_base(X.ANCHOR, mech), B.SEED)
        self.assertEqual(len(set(bases)), len(bases))

    def test_plans(self):
        self.assertEqual(len(X.items()), 12)
        units = [u for w in range(6) for u in X.plan('formal', w, 6)]
        self.assertEqual(len(units), 12)
        self.assertEqual(len({u['key'] for u in units}), 12)
        for w in range(6):
            self.assertEqual(len({u['base_id'] for u in X.plan('formal', w, 6)}), 1)
        self.assertEqual([u['key'] for u in X.plan('preflight', 0, 1)], [B.PREFLIGHT_ITEM])

    def test_frozen_paths_and_bridge_records(self):
        self.assertEqual([str(p) for p in X.frozen_paths() if not p.exists()], [])
        recs = X.bridge_records()
        self.assertEqual(set(recs), {r['id'] for r in X.items()})

    def test_analysis_selftests(self):
        self.assertEqual(AN.selftest()['status'], 'passed')
        self.assertEqual(AN.selftest_geometry()['status'], 'passed')


if __name__ == '__main__':
    unittest.main()
