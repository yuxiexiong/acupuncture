"""CPU tests on a tiny randomly initialised Qwen3.5 (8 layers lin lin lin full x2; needle at layer 0; split after
layer 4: B covers layers 1..4, deep linear set G = (5, 6), deep full attention = (7,))."""
import importlib.util
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'early-input-control-v1-2026-10-29'))
import bridge as B  # noqa: E402
import bridge_analysis as AN  # noqa: E402

F, L, T1, S2T, E2 = B.F, B.L, B.T1, B.S2T, B.E2
_spec = importlib.util.spec_from_file_location('cfm_bridge_t2', T1.STAGE2 / 'test_stage2.py')
T2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T2)

PROMPT = [9, 12, 20, 33, 41, 8, 17, 26, 30, 11, 14, 22]
LABELS = ['head'] * 2 + ['fact'] * 4 + ['question'] * 3 + ['instruction'] + ['tail'] + ['last']
NEEDLE = {'id': 'n0', 'kind': 'native', 'layer': 0, 'channel': 7, 'dose': 1.0}
TOKENS = [1, 2, 3, 5]


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = T2.tiny()
        cls.engine = T2.fake_engine(cls.model)
        cls.types = L.layer_types(cls.model)
        cls.body, cls.tensors = B.run_item(cls.engine, T2.REF, PROMPT, LABELS, 'tiny', TOKENS, n=8, split=5,
                                           needle=NEEDLE, preflight_extras=True)


class BridgeTests(Base):
    def test_layout(self):
        self.assertEqual(B.g_layers(self.types, 5), (5, 6))
        self.assertEqual(B.full_deep(self.types, 5), (7,))
        self.assertEqual(B.g_layers(list(T2.REAL_TYPES), 13), B.G_REAL)
        self.assertEqual(B.full_deep(list(T2.REAL_TYPES), 13), (15, 19, 23, 27, 31))

    def test_gates_and_counts(self):
        for g in ('formation', 'scoring', 'preflight_inert'):
            self.assertIn(g, self.body['gates'])
        self.assertEqual(self.body['counts'], {'prefixes': 14, 'scores': 22})
        B.check_limits(self.body['counts'], 'preflight')
        B.check_limits({'prefixes': 9 * 12, 'scores': 14 * 12}, 'formal')
        with self.assertRaises(AssertionError):
            B.check_limits({'prefixes': 109, 'scores': 168}, 'formal')

    def test_operations_not_trivial(self):
        dm = self.body['deep_manifest']
        for x, ref in (('U', 'T'), ('W', 'H'), ('TC', 'T'), ('CT', 'C'), ('TR0', 'T'), ('TR1', 'T'), ('H', 'T')):
            self.assertNotEqual(dm[x], dm[ref], x)
        self.assertNotEqual(dm['TR0'], dm['TR1'])
        hashes = [self.body['scores'][s]['logits_sha256'] for s in B.SCORES]
        self.assertEqual(len(set(hashes)), len(B.SCORES))

    def test_v_pinning_from_first_step(self):
        """At t=b+1 every needle formation without B starts from the same state, so its natural V equals T's;
        later the pinned V changes the natural V of the next positions."""
        import torch
        nat, app, bands = self.tensors['v_natural'], self.tensors['v_applied'], self.tensors['bands']
        # first G layer (5) at t=b+1: same state and same input -> natural V equals T's
        for x in ('U', 'TC', 'TR0'):
            self.assertTrue(torch.equal(nat[x][5][0], nat['T'][5][0]), x)
        self.assertTrue(torch.equal(nat['CT'][5][0], nat['C'][5][0]))
        # layer 6 at t=b+1: changed by the pinned V of layer 5 in the same step, except U (V_H == V_T at b+1, B inert)
        self.assertTrue(torch.equal(nat['U'][6][0], nat['T'][6][0]))
        self.assertFalse(torch.equal(nat['TC'][6][0], nat['T'][6][0]))
        for x, band in (('U', 'H'), ('W', 'T'), ('TC', 'C'), ('CT', 'T'), ('TR0', 'R0')):
            for i in (5, 6):
                self.assertTrue(torch.equal(app[x][i], bands[band][i]), (x, i))
        self.assertFalse(torch.equal(nat['U'][6][-1], nat['T'][6][-1]))

    def test_random_band_norms(self):
        for d in ('R0', 'R1'):
            for i, v in self.body['random_band_norms'][d].items():
                for a, b in zip(v['target'], v['xi']):
                    self.assertAlmostEqual(a, b, places=4)
        self.assertNotEqual(B.item_seed('VAR03-f0-required', 0), B.item_seed('VAR03-f1-required', 0))
        self.assertNotEqual(B.item_seed('VAR03-f0-required', 0), B.item_seed('VAR03-f0-required', 1))
        self.assertEqual(B.item_seed('VAR03-f0-required', 1), B.item_seed('VAR03-f0-required', 1))

    def test_reconstruction_and_terms(self):
        for x, r in self.body['reconstruction'].items():
            self.assertTrue(r['passed'], (x, r))
        for x, d in self.body['old_new_terms'].items():
            for i, rows in d.items():
                for row in rows:
                    self.assertLess(row['sum_vs_core_rel'], 1e-4, (x, i, row))

    def test_scores_records(self):
        for s in B.SCORES:
            sc = self.body['scores'][s]
            self.assertTrue(sc['final_norm']['normed_bitwise'])
            self.assertLess(sc['eta'], 1e-4)            # fp32 tiny model vs fp64 recompute
            self.assertIn('entropy_fix_scale', sc)
        self.assertAlmostEqual(self.body['scores']['C']['final_norm']['r_over_rC'], 1.0)
        self.assertEqual(set(self.body['pairs']), {f'{a}|{b}' for a, b in B.COMPARISONS})
        self.assertIn('final:h', self.tensors['score_extras']['Y_T'])
        self.assertIn('7:attn_out', self.tensors['score_extras']['Y_T'])
        self.assertEqual(set(self.tensors['score_drivers']['J_T_SU']), {5, 6})

    def test_j_definition_independent(self):
        """J(T<-S_U) == T's hybrid with the G recurrent states copied from U, scored by S3.run_once."""
        tensors = self.tensors
        container, _ = L._clean_cache(self.engine, PROMPT[:-1])          # same length; every field overwritten below

        def build(deep_src, rec_src=None):
            for i, _, f in L.component_tensors(container, self.types):
                if i < 5:
                    v = tensors['c_shallow'][f'{i}:{f}']
                elif rec_src is not None and i in (5, 6) and f == 'recurrent_states':
                    v = tensors['deep'][rec_src][f'{i}:{f}']
                else:
                    v = tensors['deep'][deep_src][f'{i}:{f}']
                L._set(container.layers[i], f, v.clone())
            res, _ = B.S3.run_once(self.engine, {'id': 'clean', 'kind': 'clean', 'dose': 0.0}, None, T2.REF, PROMPT, [],
                                   mtau=container)
            return res['first_step']['logits_sha256']
        self.assertEqual(build('T'), self.body['scores']['Y_T']['logits_sha256'])
        self.assertEqual(build('T', 'U'), self.body['scores']['J_T_SU']['logits_sha256'])
        self.assertEqual(build('H', 'W'), self.body['scores']['J_H_SW']['logits_sha256'])
        self.assertNotEqual(self.body['scores']['J_T_SU']['logits_sha256'], self.body['scores']['Y_T']['logits_sha256'])
        self.assertNotEqual(self.body['scores']['J_T_SU']['logits_sha256'], self.body['scores']['Y_U']['logits_sha256'])


class FailureTests(unittest.TestCase):
    def test_score_refuses_extra_hook(self):
        model = T2.tiny()
        engine = T2.fake_engine(model)
        F.hook_baseline(model)
        cache, _ = L._clean_cache(engine, PROMPT[:-1])
        rec = B.Recorder(model, (5, 6), 5)
        with rec:
            expected = F.hook_counts(model)
            B.score(engine, cache, PROMPT[-1], len(PROMPT), rec, 'ok', TOKENS, expected)
            h = L.model_layers(model)[2].register_forward_hook(lambda *a: None)
            with self.assertRaises(AssertionError):
                B.score(engine, cache, PROMPT[-1], len(PROMPT), rec, 'bad', TOKENS, expected)
            h.remove()

    def test_vhook_detects_layout(self):
        model = T2.tiny()
        engine = T2.fake_engine(model)
        cache, _ = L._clean_cache(engine, PROMPT[:-2])
        with B.VHook(model, (5,), 32, 40):     # wrong v1 -> shape assertion inside the forward
            with self.assertRaises(AssertionError):
                F.forward_tokens(engine, cache, [PROMPT[-2]], len(PROMPT) - 2)


class PlanTests(unittest.TestCase):
    def test_items_tokens_plans(self):
        self.assertEqual(len(B.items()), 12)
        tok = B.exp.read(B.TOKENS)
        recs = B.fab_records()
        self.assertEqual(set(tok['items']), {r['id'] for r in B.items()})
        for k, v in tok['items'].items():
            self.assertEqual(v['a5_record_sha256'], B.exp.sha(recs[k]))
            s = B.exp.read(recs[k])['scores']
            self.assertEqual(v['nonstop'], sorted({s[c]['nonstop_winner'] for c in ('C', 'X0', 'XB')}))
        self.assertEqual(tok['stop_ids'], [248044, 248046])
        units = B.plan('formal', 0, 2) + B.plan('formal', 1, 2)
        self.assertEqual(len(units), 12)
        self.assertEqual([u['key'] for u in B.plan('preflight', 0, 1)], [B.PREFLIGHT_ITEM])

    def test_frozen_paths_exist(self):
        self.assertEqual([str(p) for p in B.frozen_paths() if not p.exists()], [])

    def test_analysis_selftest(self):
        self.assertEqual(AN.selftest()['status'], 'passed')


if __name__ == '__main__':
    unittest.main()
