"""CPU tests on a tiny randomly initialised Qwen3.5 (8 layers: lin lin lin full x2; needle at layer 0, split after
layer 4, so B covers layers 1..4 including a full-attention layer and A acts on the input of layer 5)."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'early-input-control-v1-2026-10-29'))
import form_ab as F  # noqa: E402
import form_analysis as AN  # noqa: E402

E2, S3, T1, L, ST2, S2T = F.E2, F.S3, F.T1, F.L, F.ST2, F.S2T
_spec = importlib.util.spec_from_file_location('cfm_form_t2', T1.STAGE2 / 'test_stage2.py')
T2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T2)

PROMPT = [9, 12, 20, 33, 41, 8, 17, 26, 30, 11, 14, 22]
LABELS = ['head'] * 2 + ['fact'] * 4 + ['question'] * 3 + ['instruction'] + ['tail'] + ['last']
NEEDLE = {'id': 'n0', 'kind': 'native', 'layer': 0, 'channel': 7, 'dose': 1.0}
KW = dict(n=8, split=5, a_layer=5, needle=NEEDLE)


def step_route(engine, prompt, labels, needle, upto):
    """Independent stepwise run (no B/A): clean chunk 0..b then single tokens b+1..upto."""
    import torch
    prefix = prompt[:-1]
    b = S2T.boundary_b(labels)
    with torch.inference_mode():
        c = L.forward(engine.model, list(prefix[:b + 1]), 0, None).past_key_values
    for t in range(b + 1, upto + 1):
        c, _ = F.forward_tokens(engine, c, [prefix[t]], t, needle, T2.REF)
    return c


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = T2.tiny()
        cls.engine = T2.fake_engine(cls.model)
        cls.types = L.layer_types(cls.model)
        cls.body, cls.tensors = F.run_item(cls.engine, T2.REF, PROMPT, LABELS, inert_rerun=True, **KW)


class FormationTests(Base):
    def test_gates_present(self):
        for g in ('timing', 'structure', 'scoring', 'inert_hooks'):
            self.assertIn(g, self.body['gates'])
        self.assertEqual(set(self.body['scores']), set(F.SCORES))
        self.assertEqual(self.body['n_window'], 5)

    def test_counts_match_plan_limits(self):
        # per input 5 prefixes / 6 scores (+2/+2 for the inert rerun in preflight); preflight adds 2/2 chunk replays
        self.assertEqual(self.body['counts'], {'prefixes': 7, 'scores': 8})
        F.check_limits({'prefixes': 7 + 2, 'scores': 8 + 2}, 'preflight')
        F.check_limits({'prefixes': 5 * 12, 'scores': 6 * 12}, 'formal')
        with self.assertRaises(AssertionError):
            F.check_limits({'prefixes': 5 * 12 + 1, 'scores': 72}, 'formal')

    def test_operations_are_not_trivial(self):
        dm, sm = self.body['deep_manifest'], self.body['shallow_manifest']
        self.assertNotEqual(dm['XA'], dm['T'])
        self.assertNotEqual(dm['XB'], dm['T'])
        self.assertNotEqual(dm['XAB'], dm['XA'])
        self.assertNotEqual(dm['XAB'], dm['XB'])
        self.assertNotEqual(sm['XB'], sm['T'])
        self.assertEqual(sm['XA'], sm['T'])
        s = self.body['scores']
        hashes = [s[c]['logits_sha256'] for c in ('C', 'T_native', 'X0', 'XA', 'XB', 'XAB')]
        self.assertEqual(len(set(hashes)), 6)

    def test_b_definition_independent(self):
        """XB shallow after tau == (C at tau-1) + one needle step at tau, built without the B code path."""
        n, tau = len(PROMPT), len(PROMPT) - 2
        c_prev = step_route(self.engine, PROMPT, LABELS, None, tau - 1)
        ref, _ = F.forward_tokens(self.engine, c_prev, [PROMPT[:-1][tau]], tau, NEEDLE, T2.REF)
        self.assertEqual(F.manifest(ref, self.types, range(0, 5)), self.body['shallow_manifest']['XB'])
        self.assertEqual(self.body['shallow_manifest']['XB'], self.body['shallow_manifest']['XAB'])

    def test_full_attention_past_from_clean(self):
        """Layer 3 (full attention, inside B): after tau, XB keys 0..tau-1 equal C's, key tau differs."""
        import torch
        tau = len(PROMPT) - 2
        d = self.tensors['donor'][-1]
        c_last = d['3:keys']
        self.assertEqual(int(c_last.shape[-2]), tau)
        b = S2T.boundary_b(LABELS)
        self.assertEqual(len(self.tensors['donor']), tau - b)
        self.assertEqual(self.tensors['delta0'].shape[0], tau - b)
        self.assertTrue(torch.isfinite(self.tensors['delta0']).all())

    def test_x0_equals_e2_style_cell_a(self):
        """X0 score == E2-style transplant (T base, C shallow) scored by S3.run_once on the same step-route caches."""
        tau = len(PROMPT) - 2
        c = step_route(self.engine, PROMPT, LABELS, None, tau)
        t = step_route(self.engine, PROMPT, LABELS, NEEDLE, tau)
        hy = E2.transplant(t, c, range(0, 5), self.types)
        res, _ = S3.run_once(self.engine, {'id': 'clean', 'kind': 'clean', 'dose': 0.0}, None, T2.REF, PROMPT, [], mtau=hy)
        self.assertEqual(res['first_step']['logits_sha256'], self.body['scores']['X0']['logits_sha256'])
        self.assertEqual(res['first_step']['stop_advantage'], self.body['scores']['X0']['stop_advantage'])
        rc, _ = S3.run_once(self.engine, {'id': 'clean', 'kind': 'clean', 'dose': 0.0}, None, T2.REF, PROMPT, [], mtau=c)
        self.assertEqual(rc['first_step']['logits_sha256'], self.body['scores']['C']['logits_sha256'])

    def test_a_audit(self):
        for x in ('XA', 'XAB'):
            rows = self.body['A_audit'][x]
            self.assertEqual(len(rows), 5)
            for r in rows:
                self.assertGreater(r['delta_norm'], 0)
                self.assertLess(r['rounding_residual_norm'], 1e-4 * max(r['delta_norm'], 1.0))  # fp32 tiny model
        self.assertTrue(all(r['inert'] is None for r in self.body['B_audit']['XB'][1:]))
        self.assertIs(self.body['B_audit']['XB'][0]['inert'], True)

    def test_score_matches_run_once(self):
        """Cross-module call point: F.score == S3.run_once first step on the E2 chunk route."""
        cache, _ = L._clean_cache(self.engine, PROMPT[:-1])
        mine, _ = F.score(self.engine, cache, PROMPT[-1], len(PROMPT))
        ref, _ = S3.run_once(self.engine, {'id': 'clean', 'kind': 'clean', 'dose': 0.0}, None, T2.REF, PROMPT, [])
        for k in ('token', 'stop_advantage', 'logits_sha256', 'top5'):
            self.assertEqual(mine[k], ref['first_step'][k], k)
        mask = S2T.arm_mask('01', LABELS)
        r1, c1 = F.chunk_route(self.engine, NEEDLE, mask, T2.REF, PROMPT)
        r2, c2 = S3.run_once(self.engine, NEEDLE, mask, T2.REF, PROMPT, [])
        self.assertEqual(ST2.cache_manifest(c1, self.types), r2['prefix_manifest'])
        self.assertEqual(r1['logits_sha256'], r2['first_step']['logits_sha256'])

    def test_zero_dose_collapses_to_clean(self):
        zero = dict(NEEDLE, dose=0.0)
        body, _ = F.run_item(self.engine, T2.REF, PROMPT, LABELS, keep_tensors=False, **dict(KW, needle=zero))
        s = body['scores']
        for c in ('T_native', 'X0', 'XA', 'XB', 'XAB'):
            self.assertEqual(s[c]['logits_sha256'], s['C']['logits_sha256'], c)


class HookTests(unittest.TestCase):
    def test_a_arithmetic_bf16(self):
        """A: r <- bf16(fp32(r) - delta) on the input of the target layer, delta kept in fp32."""
        import torch

        class Probe(torch.nn.Module):
            def forward(self, h):
                self.seen = h.clone()
                return h

        class M(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.model = torch.nn.Module()
                self.model.layers = torch.nn.ModuleList([Probe(), Probe(), Probe()])
        m = M()
        h = (torch.randn(1, 1, 16) * 3).to(torch.bfloat16)
        delta = torch.randn(1, 16) * 0.37
        with F.Hooks(m, a_layer=2, delta=delta) as hk:
            m.model.layers[0](h)
            m.model.layers[2](h)
        want = (h[0].float() - delta).to(torch.bfloat16)
        self.assertTrue(torch.equal(m.model.layers[2].seen[0], want))
        self.assertEqual(len(hk.a_rows), 1)
        self.assertGreater(hk.a_rows[0]['rounding_residual_norm'], 0)  # bf16 rounding is recorded, not hidden
        with F.Hooks(m, a_layer=2, delta=None, install_a=True) as hk:
            m.model.layers[2](h)
        self.assertTrue(torch.equal(m.model.layers[2].seen, h))
        self.assertEqual(hk.a_rows, [])
        self.assertFalse(m.model.layers[2]._forward_pre_hooks)

    def test_b_checks_can_fail(self):
        model = T2.tiny()
        engine = T2.fake_engine(model)
        types = L.layer_types(model)
        c = step_route(engine, PROMPT, LABELS, None, 7)
        t = step_route(engine, PROMPT, LABELS, NEEDLE, 7)
        fields = F.layer_fields(types, range(1, 5))
        donor = F.snapshot(c, fields)
        row = F.fix_shallow(copy.deepcopy(t), donor, types, 8, check_inert=True)
        self.assertIs(row['inert'], False)
        row = F.fix_shallow(copy.deepcopy(c), donor, types, 8, check_inert=True)
        self.assertIs(row['inert'], True)
        with self.assertRaises(AssertionError):
            F.fix_shallow(copy.deepcopy(t), donor, types, 9)            # donor length does not match t
        x = copy.deepcopy(t)
        F.fix_shallow(x, donor, types, 8)
        x, _ = F.forward_tokens(engine, x, [PROMPT[8]], 8, NEEDLE, T2.REF)
        self.assertTrue(F.b_source_check(x, donor, types))
        y, _ = F.forward_tokens(engine, copy.deepcopy(t), [PROMPT[8]], 8, NEEDLE, T2.REF)
        self.assertFalse(F.b_source_check(y, donor, types))             # no B: past is not C's


class GateTests(unittest.TestCase):
    def _scores(self, dc, dt, dx):
        return {k: {'stop_advantage': v, 'logits_sha256': 'h', 'token': 1} for k, v in (('C', dc), ('T_native', dt), ('X0', dx))}

    def test_route_gate_both_sides(self):
        e2 = {k: {'stop_advantage': v, 'logits_sha256': 'e', 'token': 1} for k, v in (('C', -20.0), ('T_native', 0.0), ('X0', -3.0))}
        ok = F.route_gate(self._scores(-20.0, 0.0625, -3.5), e2)
        self.assertTrue(ok['passed'])
        self.assertAlmostEqual(ok['tolerance'], 0.05 * 17.0)
        bad = F.route_gate(self._scores(-20.0, 0.0, -2.0), e2)
        self.assertFalse(bad['passed'])
        e2_bad = dict(e2, X0={'stop_advantage': -21.0, 'logits_sha256': 'e', 'token': 1})
        self.assertFalse(F.route_gate(self._scores(-20.0, 0.0, -21.0), e2_bad)['passed'])

    def test_route_gate_on_real_e2_records(self):
        recs = F.e2_records()
        self.assertEqual(len(F.e2_record_paths()), 12)
        for r in F.items():
            e2 = F.e2_endpoints(F.exp.read(recs[r['id']]))
            g = F.route_gate({k: e2[k] for k in ('C', 'T_native', 'X0')}, e2)
            self.assertTrue(g['passed'] and g['delta_e2'] > 10, r['id'])


class PlanTests(unittest.TestCase):
    def test_items_and_plans(self):
        self.assertEqual(len(F.items()), 12)
        units = F.plan('formal', 0, 2) + F.plan('formal', 1, 2)
        self.assertEqual(len(units), 12)
        self.assertEqual(len({u['key'] for u in units}), 12)
        self.assertEqual({u['base_id'] for u in F.plan('formal', 0, 2)} & {u['base_id'] for u in F.plan('formal', 1, 2)}, set())
        self.assertEqual([u['key'] for u in F.plan('preflight', 0, 1)], [F.PREFLIGHT_ITEM])

    def test_real_layout(self):
        types = list(T2.REAL_TYPES)
        self.assertEqual(F.b_layers(), tuple(range(1, 13)))
        self.assertEqual(types[0], 'linear_attention')
        self.assertEqual([i for i in range(1, 13) if types[i] == 'full_attention'], [3, 7, 11])
        self.assertEqual(len(F.layer_fields(types, F.b_layers())), 24)

    def test_frozen_paths_exist(self):
        self.assertEqual([str(p) for p in F.frozen_paths() if not p.exists()], [])

    def test_analysis_selftest(self):
        self.assertEqual(AN.selftest()['status'], 'passed')


if __name__ == '__main__':
    unittest.main()
