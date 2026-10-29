"""CPU tests on a tiny randomly initialised Qwen3.5 (2 groups of 3 linear + 1 full attention layers); no checkpoint is loaded."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'early-input-control-v1-2026-10-29'))
import stage2 as S  # noqa: E402

L = S.L
import torch  # noqa: E402
from transformers import Qwen3_5TextConfig  # noqa: E402
from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5ForCausalLM  # noqa: E402
from control_engine import ControlEngine  # noqa: E402

STOP = [5]
REAL_TYPES = (['linear_attention'] * 3 + ['full_attention']) * 8  # Qwen3.5-4B config.json, read 2026-10-29


def tiny():
    torch.manual_seed(0)
    cfg = Qwen3_5TextConfig(vocab_size=64, hidden_size=32, intermediate_size=48, num_hidden_layers=8,
        layer_types=(['linear_attention'] * 3 + ['full_attention']) * 2, num_attention_heads=2, num_key_value_heads=1,
        head_dim=16, linear_num_key_heads=2, linear_num_value_heads=2, linear_key_head_dim=8, linear_value_head_dim=8,
        linear_conv_kernel_dim=4, max_position_embeddings=256, tie_word_embeddings=True)
    cfg._attn_implementation = 'eager'
    model = Qwen3_5ForCausalLM(cfg).eval()
    for p in model.parameters():
        p.requires_grad_(False)
    return model


def fake_engine(model):
    e = ControlEngine.__new__(ControlEngine)
    e.model, e.torch, e.device = model, torch, torch.device('cpu')
    e.layers = model.model.layers
    e.modules = {i: b.mlp.down_proj for i, b in enumerate(e.layers)}
    e.column_norms = {str(i): m.weight.float().norm(dim=0) for i, m in e.modules.items()}
    e.stop_ids = STOP
    return e


REF = {'residual_scales': {str(i): 2.0 for i in range(8)}, 'context_sha256': 'x', 'input_token_sha256': 'y'}
PROMPT = [9, 12, 20, 33, 41, 8, 17, 26, 30, 11]


def native(layer, channel=7, dose=1.0):
    return {'id': f'n{layer}', 'kind': 'native', 'layer': layer, 'channel': channel, 'dose': dose}


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = tiny()
        cls.engine = fake_engine(cls.model)
        cls.types = L.layer_types(cls.model)
        cls.groups = S.derive_groups(cls.types)
        cls.prefix, cls.last = PROMPT[:-1], PROMPT[-1]
        cls.T, _, _ = L._build_T(cls.engine, native(1), REF, cls.prefix)
        cls.C, _ = L._clean_cache(cls.engine, cls.prefix)

    def first_logits(self, cache):
        return L.decode(self.model, cache, self.last, len(PROMPT), STOP, max_new_tokens=1, attentions=False)['readouts'][0]['logits_sha256']


class GroupTests(Base):
    def test_contract_table_matches_real_layout(self):
        self.assertEqual(S.check_contract_groups(REAL_TYPES), S.CONTRACT_GROUPS)
        self.assertEqual(S.CONTRACT_GROUPS[7], {'linear': (28, 29, 30), 'full': (31,)})
        self.assertEqual(len(self.groups), 2)
        with self.assertRaises(AssertionError):
            S.check_contract_groups(self.types)
        with self.assertRaises(AssertionError):
            S.check_contract_groups(REAL_TYPES[:-1] + ['linear_attention'])

    def test_swap_sets(self):
        g = S.CONTRACT_GROUPS
        self.assertEqual(S.swaps_for(g, 3, ('kv',)), {(15, 'kv')})
        self.assertEqual(S.swaps_for(g, 3, ('recurrent', 'conv')), {(i, c) for i in (12, 13, 14) for c in ('recurrent', 'conv')})
        self.assertEqual(len(S.swaps_for(g, None, ('kv',))), 8)
        self.assertEqual(len(S.swaps_for(g, None, ('recurrent',))), 24)
        self.assertEqual(S.code_cleaned('CTC'), ('kv', 'conv'))
        self.assertEqual({S.code_cleaned(c) for c in S.G_CODES}, {(), ('kv', 'recurrent', 'conv'), ('kv',), ('recurrent',),
            ('conv',), ('recurrent', 'conv'), ('kv', 'conv'), ('kv', 'recurrent')})
        self.assertEqual(len(set(S.SUBSETS)), 7)


class CacheTests(Base):
    def test_provenance_every_group_subset_direction(self):
        for g in range(len(self.groups)):
            for s in S.SUBSETS:
                for d, bg in S.BACKGROUND.items():
                    swaps = S.swaps_for(self.groups, g, S.components_of(s))
                    rows = L.audit(S.compose_swaps(self.T, self.C, self.types, bg, swaps), self.T, self.C, self.types)
                    S.check_sources(rows, bg, swaps)
                    self.assertEqual({(r['layer'], r['component']) for r in rows if not r['equals_' + bg]} - swaps, set())

    def test_check_sources_rejects_wrong_design(self):
        swaps = S.swaps_for(self.groups, 1, ('recurrent',))
        rows = L.audit(S.compose_swaps(self.T, self.C, self.types, 'T', swaps), self.T, self.C, self.types)
        with self.assertRaises(AssertionError):
            S.check_sources(rows, 'T', S.swaps_for(self.groups, 1, ('conv',)))
        with self.assertRaises(AssertionError):
            S.check_sources(rows, 'C', swaps)

    def test_upstream_T_equals_C_rows_are_kept(self):
        swaps = S.swaps_for(self.groups, 0, S.COMPONENTS)
        rows = L.audit(S.compose_swaps(self.T, self.C, self.types, 'T', swaps), self.T, self.C, self.types)
        self.assertGreater(S.check_sources(rows, 'T', swaps)['t_equals_c_rows'], 0)  # layers 0-1 precede the L1 write
        self.assertEqual(len(rows), 2 * 8)

    def test_deepcopy_no_crosstalk(self):
        before = (S.cache_manifest(self.T, self.types), S.cache_manifest(self.C, self.types))
        mixed = S.compose_swaps(self.T, self.C, self.types, 'C', S.swaps_for(self.groups, 1, S.COMPONENTS))
        for i, _, field in L.component_tensors(mixed, self.types):
            L._get(mixed.layers[i], field).add_(1.0)
        L.decode(self.model, mixed, self.last, len(PROMPT), STOP, max_new_tokens=3)
        L.score(self.model, mixed, self.last, len(PROMPT), [1, 2])
        self.assertEqual(before, (S.cache_manifest(self.T, self.types), S.cache_manifest(self.C, self.types)))

    def test_eight_codes_replay_stage1_compose(self):
        for code in S.G_CODES:
            cleaned = S.code_cleaned(code)
            mine = S.compose_swaps(self.T, self.C, self.types, 'T', S.swaps_for(self.groups, None, cleaned))
            ref = L.compose(self.T, self.C, self.types, cleaned)
            self.assertEqual(S.cache_manifest(mine, self.types), S.cache_manifest(ref, self.types), code)
            self.assertEqual(self.first_logits(mine), self.first_logits(ref), code)

    def test_same_path_identity(self):
        none = S.compose_swaps(self.T, self.C, self.types, 'T', frozenset())
        a = L.decode(self.model, self.T, self.last, len(PROMPT), STOP, max_new_tokens=6, hash_all=True)
        b = L.decode(self.model, none, self.last, len(PROMPT), STOP, max_new_tokens=6, hash_all=True)
        self.assertEqual([r['logits_sha256'] for r in a['readouts']], [r['logits_sha256'] for r in b['readouts']])
        full = S.compose_swaps(self.T, self.C, self.types, 'T', S.swaps_for(self.groups, None, S.COMPONENTS))
        self.assertEqual(self.first_logits(full), self.first_logits(self.C))
        back = S.compose_swaps(self.T, self.C, self.types, 'C', S.swaps_for(self.groups, None, S.COMPONENTS))
        self.assertEqual(self.first_logits(back), self.first_logits(self.T))
        self.assertNotEqual(self.first_logits(self.T), self.first_logits(self.C))

    def test_swap_gates_pass_on_tiny_model(self):
        out = S.swap_gates(self.model, self.T, self.C, self.types, self.groups, self.last, len(PROMPT), STOP)
        self.assertEqual(set(out['global_replay']), set(S.G_CODES))
        self.assertEqual(len(out['provenance']), 2 * 7 * 2)
        self.assertTrue(all(out['readability'].values()))
        self.assertTrue(all(not m._forward_hooks and not m._forward_pre_hooks for m in self.model.modules()))


class StructureTests(Base):
    def test_downstream_only(self):
        s = S.structure(self.T, self.C, self.types, 1)
        self.assertEqual(s['downstream_layers']['kv'], [3, 7])
        self.assertTrue(all(i > 1 for c in S.COMPONENTS for i in s['differing_layers'][c]))
        self.assertTrue(any(s['differing_layers'].values()))

    def test_last_layer_is_structural_boundary(self):
        t_last, _, _ = L._build_T(self.engine, native(7), REF, self.prefix)
        s = S.structure(t_last, self.C, self.types, 7)
        self.assertEqual(s['differing_layers'], {c: [] for c in S.COMPONENTS})
        self.assertEqual(s['downstream_layers'], {c: [] for c in S.COMPONENTS})

    def test_upstream_difference_is_refused(self):
        with self.assertRaises(AssertionError):
            S.structure(self.T, self.C, self.types, 7)  # T was written at L1; claiming L7 must fail

    def test_fast_audit_and_other_state_equal_reference(self):
        from control_engine import state_fingerprint
        mt, mc = S.cache_manifest(self.T, self.types), S.cache_manifest(self.C, self.types)
        for bg in ('T', 'C'):
            mixed = S.compose_swaps(self.T, self.C, self.types, bg, S.swaps_for(self.groups, 1, ('kv', 'conv')))
            self.assertEqual(S.audit_against(mixed, mt, mc, self.types), L.audit(mixed, self.T, self.C, self.types))

        def strip(node):
            if isinstance(node, dict):
                return {k: strip(v) for k, v in node.items() if k not in S.CONTENT_FIELDS}
            return [strip(v) for v in node] if isinstance(node, list) else node
        for cache in (self.T, self.C):
            self.assertEqual(S.other_state(cache)['state'], strip(state_fingerprint(cache)['state']))

    def test_other_state_matches_and_detects_change(self):
        a, b = S.other_state(self.T), S.other_state(self.C)
        self.assertEqual(a['sha256'], b['sha256'])
        mixed = S.compose_swaps(self.T, self.C, self.types, 'T', S.swaps_for(self.groups, 1, ('kv', 'recurrent')))
        self.assertEqual(S.other_state(mixed)['sha256'], a['sha256'])
        changed = copy.deepcopy(self.T)
        changed.layers[0].extra_marker = 1  # any non-content field difference must be visible
        self.assertNotEqual(S.other_state(changed)['sha256'], a['sha256'])
        content_only = copy.deepcopy(self.T)
        L._set(content_only.layers[3], 'keys', L._get(content_only.layers[3], 'keys') + 1)
        self.assertEqual(S.other_state(content_only)['sha256'], a['sha256'])


class PlanTests(unittest.TestCase):
    SEL = {'early:stop': 'N_L00_C4146_D+1', 'early:fact': 'N_L02_C5251_D-1', 'mid:stop': 'N_L13_C248_D-1',
           'mid:fact': 'N_L15_C7988_D+1', 'late:stop': 'N_L25_C2747_D+1', 'late:fact': 'N_L27_C5398_D-1'}

    def cands(self, groups):
        return {r: {'condition_id': c, 'group': g} for (r, c), g in zip(sorted(self.SEL.items()), groups)}

    def total(self, stage, selection=None, candidates=None):
        return sum(len(S.plan(stage, g, selection, candidates)) for g in (0, 1))

    def test_conditions(self):
        conds = S.g_conditions()
        ids = {c['id'] for c in conds}
        self.assertEqual(len(conds), 64)
        self.assertTrue({'N_L00_C4146_D+1', 'N_L02_C5251_D-1', 'N_L25_C2747_D+1', 'N_L31_C8750_D+1'} <= ids)
        self.assertEqual(sorted({c['layer'] for c in conds}), list(range(32)))
        self.assertTrue(set(S.G_PREFLIGHT_CONDITIONS) <= ids)

    def test_g_counts(self):
        self.assertEqual(self.total('g_development'), 10776)
        self.assertEqual(self.total('g_history'), 10776)
        self.assertEqual(self.total('audit'), 24)
        specs = S.plan('g_development', 0)
        self.assertEqual(sum(s['code'] == 'CCC' for s in specs), 12)

    def test_a_counts_and_merge(self):
        self.assertEqual(self.total('a_scan', self.SEL), 8064)
        merged = dict(self.SEL, **{'early:fact': 'N_L00_C4146_D+1'})
        specs = S.plan('a_scan', 0, merged)
        self.assertEqual(self.total('a_scan', merged), 5 * 8 * 7 * 24)
        self.assertTrue(any(s['roles'] == ['early:fact', 'early:stop'] for s in specs))
        self.assertTrue(all(s['background'] == 'T' and s['direction'] == 'clean' for s in specs))

    def test_b_counts_and_dedupe(self):
        self.assertEqual(self.total('b_validate', self.SEL, self.cands(range(6))), 3048)
        shared = dict(self.SEL, **{'early:fact': 'N_L00_C4146_D+1'})
        c = {r: {'condition_id': shared[r], 'group': 2 if r.startswith('early') else i} for i, r in enumerate(sorted(shared))}
        self.assertEqual(self.total('b_validate', shared, c), 24 * (1 + 5 * 7 + 5 * 14))
        specs = S.plan('b_validate', 0, shared, c)
        self.assertEqual({s['background'] for s in specs if s['direction'] == 'pollute'}, {'C'})

    def test_preflight_budgets(self):
        cases = {'g_preflight': (None, None), 'a_preflight': (self.SEL, None), 'b_preflight': (self.SEL, self.cands(range(6)))}
        for stage, (sel, cand) in cases.items():
            n = self.total(stage, sel, cand)
            self.assertLessEqual(n, S.PREFLIGHT_LIMITS['generations'], stage)
            self.assertLessEqual(2 * n, S.PREFLIGHT_LIMITS['candidate_reads'], stage)
        self.assertEqual({s['code'] for s in S.plan('a_preflight', 0, self.SEL) if s['group'] is None}, {'TTT', 'CCC'})

    def test_selection_checks(self):
        with self.assertRaises(AssertionError):
            S.check_g_selection({'early:stop': 'N_L13_C248_D-1'})
        with self.assertRaises(AssertionError):
            S.check_candidates({'early:stop': {'condition_id': 'N_L00_C4146_D+1', 'group': 8}})

    def test_contract_groups_drive_every_swap(self):
        for spec in S.plan('b_validate', 1, self.SEL, self.cands(range(6))):
            swaps = S.swaps_of_spec(S.CONTRACT_GROUPS, spec)
            if spec['code'] == 'CCC':
                self.assertEqual(swaps, frozenset())
            elif spec['group'] is not None:
                layers = {l for l, _ in swaps}
                g = S.CONTRACT_GROUPS[spec['group']]
                self.assertTrue(layers <= set(g['linear']) | set(g['full']))

    def test_authorization_required(self):
        with self.assertRaises(Exception):
            S.authorize(str(HERE / 'no-such-authorization.json'), 'g_development')


class ReuseTests(unittest.TestCase):
    def test_reuse_replay_detects_any_difference(self):
        rec = {'reference_sha256': 'r', 'prompt_token_sha256': 'p', 'swaps': [],
               'generation': {'token_ids': [1, 2], 'readouts': [{'logits_sha256': 'h'}]}, 'candidates': [{'loglikelihood': -1.5}]}
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            name = 'X-f0__N_L00_C4146_D+1__all-TTT.json'
            for d in (tmp / 'new/records', tmp / 'g/worker-0/records'):
                d.mkdir(parents=True)
            (tmp / 'new/records' / name).write_text(json.dumps(rec))
            (tmp / 'g/worker-0/records' / name).write_text(json.dumps(rec))
            auth = {'g_development_run': str(tmp / 'g')}
            self.assertEqual(S.reuse_replay(tmp / 'new', {'id': 'X-f0'}, auth), {name: 'identical'})
            bad = json.loads(json.dumps(rec))
            bad['candidates'][0]['loglikelihood'] = -1.25
            (tmp / 'g/worker-0/records' / name).write_text(json.dumps(bad))
            with self.assertRaises(AssertionError):
                S.reuse_replay(tmp / 'new', {'id': 'X-f0'}, auth)


class DataTests(unittest.TestCase):
    def test_validation_panel(self):
        rows = S.exp.read(S.VALIDATION_DATA)
        self.assertEqual(len(rows), 24)
        bases = {}
        for r in rows:
            bases.setdefault(r['base_id'], []).append(r)
        self.assertEqual(len(bases), 12)
        self.assertEqual(sorted({r['family'] for r in rows}), ['arithmetic', 'reading', 'relation'])
        for fam in ('arithmetic', 'reading', 'relation'):
            self.assertEqual(sum(v[0]['family'] == fam for v in bases.values()), 4)
        old = {r['prompt'] for split in ('development', 'confirmation') for r in S.exp.items(split)}
        for b, (f0, f1) in bases.items():
            self.assertEqual(f0['choices'], f1['choices'])
            self.assertEqual(f0['target_index'] + f1['target_index'], 1)
            self.assertEqual(f0['reference_id'], f1['reference_id'])
            self.assertNotIn(f0['prompt'], old)
            self.assertIn('model-drafted', f0['source']['author'])


if __name__ == '__main__':
    unittest.main()
