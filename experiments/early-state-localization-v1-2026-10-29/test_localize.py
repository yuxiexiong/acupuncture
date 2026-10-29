"""CPU tests on a tiny randomly initialised Qwen3.5 (3 linear + 1 full attention layers); no checkpoint is loaded."""
import copy
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / 'early-input-control-v1-2026-10-29'))
import localize as L  # noqa: E402

import torch  # noqa: E402
from transformers import Qwen3_5TextConfig  # noqa: E402
from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5ForCausalLM  # noqa: E402
from control_engine import ControlEngine  # noqa: E402

STOP = [5]


def tiny():
    torch.manual_seed(0)
    cfg = Qwen3_5TextConfig(vocab_size=64, hidden_size=32, intermediate_size=48, num_hidden_layers=4,
        layer_types=['linear_attention'] * 3 + ['full_attention'], num_attention_heads=2, num_key_value_heads=1,
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


REF = {'residual_scales': {str(i): 2.0 for i in range(4)}, 'context_sha256': 'x', 'input_token_sha256': 'y'}
NATIVE = {'id': 'n', 'kind': 'native', 'layer': 0, 'channel': 7, 'dose': 1.0}
PROMPT = [9, 12, 20, 33, 41, 8, 17, 26, 30, 11]


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = tiny()
        cls.engine = fake_engine(cls.model)
        cls.types = L.layer_types(cls.model)
        cls.prefix, cls.last = PROMPT[:-1], PROMPT[-1]
        cls.T, _, _ = L._build_T(cls.engine, NATIVE, REF, cls.prefix)
        cls.C, _ = L._clean_cache(cls.engine, cls.prefix)

    def dec(self, cache, **kw):
        kw.setdefault('max_new_tokens', 6)
        return L.decode(self.model, cache, self.last, len(PROMPT), STOP, hash_all=True, **kw)


class CacheTests(Base):
    def test_compose_sources_for_every_arm(self):
        for arm, clean in L.ARMS.items():
            composed = L.compose(self.T, self.C, self.types, clean)
            rows = L.audit(composed, self.T, self.C, self.types)
            self.assertTrue(L.check_audit(rows, clean), arm)
            self.assertEqual({r['component'] for r in rows}, set(L.COMPONENTS))
        # Layer 0 caches are computed before the layer-0 MLP write, so T and C agree there.
        rows = L.audit(self.T, self.T, self.C, self.types)
        self.assertTrue(all(r['equals_C'] for r in rows if r['layer'] == 0))
        self.assertTrue(any(not r['equals_C'] for r in rows if r['layer'] > 0))

    def test_audit_rejects_wrong_source(self):
        composed = L.compose(self.T, self.C, self.types, ('kv',))
        rows = L.audit(composed, self.T, self.C, self.types)
        with self.assertRaises(AssertionError):
            L.check_audit(rows, ('recurrent',))

    def test_deepcopy_no_shared_storage(self):
        before = L.audit(self.T, self.T, self.C, self.types)
        composed = L.compose(self.T, self.C, self.types, ('recurrent',))
        for i, comp, field in L.component_tensors(composed, self.types):
            L._get(composed.layers[i], field).add_(1.0)
        after = L.audit(self.T, self.T, self.C, self.types)
        self.assertEqual([r['sha256'] for r in before], [r['sha256'] for r in after])

    def test_same_path_identity(self):
        a, b = self.dec(self.T), self.dec(L.compose(self.T, self.C, self.types, ()))
        self.assertEqual([r['logits_sha256'] for r in a['readouts']], [r['logits_sha256'] for r in b['readouts']])
        c, d = self.dec(self.C), self.dec(L.compose(self.T, self.C, self.types, L.COMPONENTS))
        self.assertEqual([r['logits_sha256'] for r in c['readouts']], [r['logits_sha256'] for r in d['readouts']])
        self.assertNotEqual(a['readouts'][0]['logits_sha256'], c['readouts'][0]['logits_sha256'])

    def test_readability_detects_and_can_fail(self):
        base = self.dec(self.T, max_new_tokens=1)['readouts'][0]['logits_sha256']
        for comp in L.COMPONENTS:
            rnd = self.dec(L.randomize(self.T, self.types, comp, 3), max_new_tokens=1)
            self.assertNotEqual(rnd['readouts'][0]['logits_sha256'], base, comp)
        # A silently dropped state (randomised then restored before reading) must look identical -> gate fails.
        dropped = L.randomize(self.T, self.types, 'recurrent', 3)
        for i, comp, field in L.component_tensors(dropped, self.types):
            if comp == 'recurrent':
                L._set(dropped.layers[i], field, L._get(self.T.layers[i], field).clone())
        self.assertEqual(self.dec(dropped, max_new_tokens=1)['readouts'][0]['logits_sha256'], base)

    def test_masked_hook_equals_control_hooks(self):
        full, _, _ = L._build_T(self.engine, NATIVE, REF, self.prefix, mask=[True] * len(self.prefix))
        self.assertTrue(all(r['equals_T'] for r in L.audit(full, self.T, self.C, self.types)))
        direction = {'id': 'v', 'kind': 'direction', 'layer': 1, 'dose': -1.0,
                     'vector': (torch.ones(32) / 32 ** .5).tolist(), 'direction_id': 'V'}
        ref_t, _, _ = L._build_T(self.engine, direction, REF, self.prefix)
        mask_t, _, _ = L._build_T(self.engine, direction, REF, self.prefix, mask=[True] * len(self.prefix))
        self.assertTrue(all(r['equals_T'] for r in L.audit(mask_t, ref_t, self.C, self.types)))
        half, _, _ = L._build_T(self.engine, NATIVE, REF, self.prefix, mask=[i < 4 for i in range(len(self.prefix))])
        self.assertFalse(all(r['equals_T'] for r in L.audit(half, self.T, self.C, self.types)))

    def test_attention_readout_present_and_inert(self):
        a = self.dec(self.T, max_new_tokens=1, attentions=True)
        b = self.dec(self.T, max_new_tokens=1, attentions=False)
        self.assertTrue(all(not m._forward_hooks and not m._forward_pre_hooks for m in self.model.modules()))
        self.assertEqual(a['readouts'][0]['logits_sha256'], b['readouts'][0]['logits_sha256'])
        self.assertEqual(set(a['first_token_attention']), {'3'})
        self.assertTrue(0 <= a['first_token_attention']['3'] <= 1)

    def test_score_shares_decode_path(self):
        g = self.dec(self.C, max_new_tokens=4)
        toks = g['token_ids'] if g['token_ids'][-1] not in STOP else g['token_ids'][:-1]
        s = L.score(self.model, self.C, self.last, len(PROMPT), toks[:3] or [1])
        if toks:
            self.assertEqual(s['logits_sha256'][:len(toks[:3])], [r['logits_sha256'] for r in g['readouts'][:len(toks[:3])]])
        self.assertAlmostEqual(sum(s['token_logprobs']), s['loglikelihood'])

    def test_gate_decay_range(self):
        _, decay = L._clean_cache(self.engine, self.prefix)
        self.assertEqual(set(decay), {'0', '1', '2'})
        for v in decay.values():
            self.assertTrue(v['log_survive_from_0'] <= v['log_survive_from_mid'] <= 0)

    def test_hooks_removed(self):
        L._build_T(self.engine, NATIVE, REF, self.prefix, mask=[True] * len(self.prefix))
        self.assertTrue(all(not m._forward_hooks and not m._forward_pre_hooks for m in self.model.modules()))


class PlanTests(unittest.TestCase):
    def test_conditions(self):
        rows = L.conditions()
        self.assertEqual(len(rows), 26)
        ids = {r['id'] for r in rows}
        self.assertTrue(set(L.ANCHORS) <= ids and L.CONTROL in ids)
        self.assertEqual(sum(r['kind'] == 'direction' for r in rows), 8)

    def test_plan_counts(self):
        for stage, n in (('development', 3288), ('confirmation', 3288)):
            total = sum(len(L.plan(stage, g)) for g in (0, 1))
            self.assertEqual(total, n, stage)
        pre = sum(len(L.plan('preflight', g)) for g in (0, 1))
        self.assertEqual(pre, 2 * 2 * (1 + 3 * 5 + 2 * 2))

    def test_preflight_summary(self):
        ok = {'item_id': 'a', 'status': 'passed', 'gates': {}}
        self.assertEqual(L.summarize_preflight([ok, dict(ok, item_id='b')], 2)['status'], 'passed')
        for bad in ([ok], [ok, dict(ok, status='failed')], list(ok)):
            with self.assertRaises((AssertionError, TypeError)):
                L.summarize_preflight(bad, 2)

    def test_confirmation_requires_lock(self):
        with self.assertRaises(Exception):
            L.authorize(str(HERE / 'no-such-authorization.json'), 'confirmation')


if __name__ == '__main__':
    unittest.main()
