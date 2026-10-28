"""Pure checks run without torch; the full suite requires torch and never skips."""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("control_under_test", Path(__file__).with_name("control_engine.py"))
control = importlib.util.module_from_spec(spec)
spec.loader.exec_module(control)


class Tokenizer:
    bos_token_id, eos_token_id = None, 7

    def encode(self, text, **kwargs):
        return [ord(c) % 6 for c in text]

    def decode(self, tokens, skip_special_tokens=False, **kwargs):
        if isinstance(tokens, int):
            return "<stop>" if tokens == 7 else str(tokens)
        return " ".join(str(t) for t in tokens if not (skip_special_tokens and t == 7))


class PureTests(unittest.TestCase):
    def test_masks_define_first_prediction_and_modes(self):
        self.assertEqual(control.selection_mask("prefill", 0, 4, 4), [True]*4)
        self.assertEqual(control.selection_mask("prefill", 1, 1, 4), [False])
        self.assertEqual(control.selection_mask("decode", 0, 4, 4), [False]*4)
        self.assertEqual(control.selection_mask("decode", 1, 1, 4), [True])
        self.assertEqual(control.selection_mask("prompt_last", 0, 4, 4), [False]*3+[True])
        self.assertEqual(control.selection_mask("prompt_except_last", 0, 4, 4), [True]*3+[False])
        self.assertEqual(control.selection_mask("full", 0, 4, 4, False), [False]*4)
        with self.assertRaises(AssertionError):
            control.selection_mask("full", 2, 4, 4)

    def test_reference_identity_is_not_current_fact_identity(self):
        ref = {"context_sha256": "fact0", "input_token_sha256": "tokens0", "residual_scales": {"0": 2.}}
        bound = control.bind_reference("other fact", ref, Tokenizer())
        self.assertEqual(bound["reference_context_sha256"], "fact0")
        self.assertEqual(bound["context_sha256"], control.text_hash("other fact"))
        self.assertEqual(bound["residual_scales"], ref["residual_scales"])
        self.assertIsNot(bound["residual_scales"], ref["residual_scales"])

    def test_candidate_preserves_prompt_boundary(self):
        prefix, suffix = control.exact_pair(Tokenizer(), "ab ", "cd")
        self.assertEqual(prefix, Tokenizer().encode("ab "))
        self.assertEqual(suffix, Tokenizer().encode("cd"))
        class BadTokenizer(Tokenizer):
            def encode(self, text, **kwargs):
                return [0] if len(text) < 4 else [1, 2]
        with self.assertRaises(AssertionError):
            control.exact_pair(BadTokenizer(), "ab", "cd")

    def test_cache_scalar_fingerprint(self):
        a, b = SimpleNamespace(seen=3), SimpleNamespace(seen=3)
        self.assertEqual(control.state_fingerprint(a), control.state_fingerprint(b))
        b.seen = 4
        self.assertNotEqual(control.state_fingerprint(a), control.state_fingerprint(b))


def synthetic_engine(torch):
    class Attention(torch.nn.Module):
        def forward(self, values, memory):
            return values * .125 + memory[:, None, :] * .0625

    class MLP(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.down_proj = torch.nn.Linear(4, 4, bias=False, dtype=torch.bfloat16)
            self.down_proj.weight.data.copy_(torch.eye(4, dtype=torch.bfloat16) * .25)

        def forward(self, values):
            return self.down_proj(values)

    class Block(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.self_attn, self.mlp = Attention(), MLP()

        def forward(self, values, memory):
            values = values + self.self_attn(values, memory)
            return values + self.mlp(values)

    class Model(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.layers = torch.nn.ModuleList([Block(), Block()])
            self.embedding = torch.nn.Embedding(8, 4, dtype=torch.bfloat16)
            self.head = torch.nn.Linear(4, 8, dtype=torch.bfloat16)
            self.force_eos = False
            with torch.no_grad():
                self.embedding.weight.copy_(torch.arange(32).reshape(8, 4).to(torch.bfloat16) / 32)
                self.head.weight.copy_(torch.tensor([[1,0,0,0], [0,1,0,0], [0,0,1,0], [0,0,0,1],
                    [-1,0,0,0], [0,-1,0,0], [0,0,-1,0], [0,0,0,-1]], dtype=torch.bfloat16))
                self.head.bias.zero_()
                self.head.bias[7] = -8

        def forward(self, input_ids, past_key_values, **kwargs):
            if past_key_values is None:
                past_key_values = {"memory": torch.zeros((1, 4), dtype=torch.bfloat16), "seen": 0}
            values = self.embedding(input_ids)
            for layer in self.layers:
                values = layer(values, past_key_values["memory"])
            past_key_values["memory"] = values[:, -1].detach().clone()
            past_key_values["seen"] += input_ids.shape[1]
            logits = self.head(values)
            if self.force_eos:
                logits[..., 7] = 100
            if kwargs.get("logits_to_keep"):
                logits = logits[:, -kwargs["logits_to_keep"]:]
            return SimpleNamespace(logits=logits, past_key_values=past_key_values)

        def generate(self, input_ids, attention_mask, max_new_tokens, eos_token_id,
                     pad_token_id, logits_processor, **kwargs):
            history = input_ids.clone()
            cache = {"memory": torch.zeros((1, 4), dtype=torch.bfloat16), "seen": 0}
            for step in range(max_new_tokens):
                value = input_ids if step == 0 else history[:, -1:]
                out = self(input_ids=value, past_key_values=cache)
                scores = logits_processor(history, out.logits[:, -1].float())
                next_token = scores.argmax(-1).reshape(1, 1)
                history = torch.cat((history, next_token), dim=1)
                if int(next_token) in eos_token_id:
                    break
            return history

    engine = control.ControlEngine.__new__(control.ControlEngine)
    engine.torch, engine.device, engine.batch_size = torch, "cpu", 1
    engine.model, engine.tokenizer = Model().eval(), Tokenizer()
    engine.layers = engine.model.layers
    engine.modules = {i: block.mlp.down_proj for i, block in enumerate(engine.layers)}
    engine.column_norms = {str(i): module.weight.float().norm(dim=0) for i, module in engine.modules.items()}
    engine.stop_ids, engine.pad_id, engine.max_length = [7], 0, 512
    return engine


class TorchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import torch  # Required dependency: absence is an error, not a skipped check.
        cls.torch = torch
        class ProcessorList(list):
            def __call__(self, ids, scores):
                for processor in self:
                    scores = processor(ids, scores)
                return scores
        cls.transformers = SimpleNamespace(LogitsProcessor=object, LogitsProcessorList=ProcessorList)

    def setUp(self):
        self.engine = synthetic_engine(self.torch)
        self.reference = {"context_sha256": control.text_hash("abcd"),
            "input_token_sha256": control.token_hash(Tokenizer().encode("abcd")),
            "residual_scales": {"0": 1., "1": 1.5}}
        self.clean = {"id": "clean", "kind": "clean", "dose": 0}
        self.native = {"id": "native", "kind": "native", "layer": 0, "channel": 1, "dose": .5}
        self.stub = patch.dict(sys.modules, {"transformers": self.transformers})
        self.stub.start()
        self.addCleanup(self.stub.stop)

    def run_one(self, condition=None, **kwargs):
        return self.engine.generate_one("abcd", self.reference, condition or self.native,
                                        max_new_tokens=8, **kwargs)

    def test_masks_zero_and_readouts(self):
        clean = self.run_one(self.clean)
        for condition in ({**self.native, "dose": 0},
                          {"id": "zero_dir", "kind": "direction", "layer": 0, "dose": 0,
                           "vector": [1., 0., 0., 0.]}):
            zero = self.run_one(condition)
            self.assertEqual(clean["token_ids"], zero["token_ids"])
            self.assertEqual(clean["step_readouts"], zero["step_readouts"])
        for mode, total in (("full", 11), ("prefill", 4), ("decode", 7),
                            ("prompt_last", 1), ("prompt_except_last", 3)):
            result = self.run_one(mode=mode)
            self.assertEqual(sum(r["positions"] for r in result["write_audit"]), total)
            self.assertTrue(all(r["non_target_values_unchanged"] and r["masked_positions_unchanged"]
                                for r in result["write_audit"]))
        self.assertIsNone(clean["step_readouts"][1]["logits_sha256"])
        self.assertIsNotNone(clean["step_readouts"][4]["logits_sha256"])

    def test_fork_state_and_continuation_replay(self):
        self.assertEqual(control.state_fingerprint({"seen": self.torch.tensor(4)}),
                         control.state_fingerprint({"seen": self.torch.tensor(4)}))
        original = self.run_one()
        prefix = original["token_ids"][:4]
        branches = {kind: self.engine.branch("abcd", self.reference, self.native, prefix,
                    kind=kind, max_new_tokens=8) for kind in ("continue", "withdraw", "rebuild")}
        self.assertEqual(original["token_ids"], branches["continue"]["token_ids"])
        self.assertEqual(original["step_readouts"], branches["continue"]["step_readouts"])
        self.assertEqual(branches["continue"]["cache_fingerprints"]["4"],
                         branches["withdraw"]["cache_fingerprints"]["4"])
        self.assertNotEqual(branches["continue"]["cache_fingerprints"]["4"]["sha256"],
                            branches["rebuild"]["cache_fingerprints"]["4"]["sha256"])
        self.assertTrue(all(r["positions"] == 0 for r in branches["withdraw"]["write_audit"][4:]))
        self.assertTrue(all(r["positions"] == 0 for r in branches["rebuild"]["write_audit"]))
        self.assertEqual(original["step_readouts"], self.run_one()["step_readouts"])

    def test_zero_rebuild_is_numerically_clean(self):
        clean = self.run_one(self.clean)
        rebuilt = self.engine.branch("abcd", self.reference, {**self.native, "dose": 0},
            clean["token_ids"][:4], kind="rebuild", max_new_tokens=8)
        self.assertEqual(clean["token_ids"], rebuilt["token_ids"])
        self.assertEqual(clean["step_readouts"], rebuilt["step_readouts"])
        self.assertEqual(clean["cache_fingerprints"], rebuilt["cache_fingerprints"])

    def test_fork_cross_scores_use_full_single_step_logits(self):
        source = self.run_one()
        branches = {kind: self.engine.branch("abcd", self.reference, self.native,
            source["token_ids"][:4], kind=kind, max_new_tokens=8, retain_fork_logits=True)
            for kind in ("continue", "withdraw", "rebuild")}
        union = {row["token_ids"][4] for row in branches.values()}
        for row in branches.values():
            logits = row.pop("_fork_logits")
            self.assertEqual(logits.ndim, 1)
            recorded = {entry["token_id"]: entry["logit"] for entry in row["step_readouts"][4]["top32"]}
            self.assertTrue(all(float(logits[token]) == recorded[token] for token in union))
            self.assertNotIn("_fork_logits", row)

    def test_eos_and_total_budget_are_not_extended(self):
        self.engine.model.force_eos = True
        result = self.run_one(self.clean)
        self.assertEqual(result["token_ids"], [7])
        self.assertEqual(result["end_reason"], "eos_token")
        na = self.engine.branch("abcd", self.reference, self.native, [7], max_new_tokens=8)
        self.assertEqual(na["status"], "not_applicable")
        self.engine.model.force_eos = False
        source = self.run_one()
        na = self.engine.branch("abcd", self.reference, self.native, source["token_ids"], max_new_tokens=8)
        self.assertEqual(na["status"], "not_applicable")
        with self.assertRaises(AssertionError):
            self.engine.branch("abcd", self.reference, self.native, [6,6,6,6], max_new_tokens=8)

    def test_candidate_scores_match_independent_incremental_forward(self):
        result = self.engine.score_one("abcd", "ef", self.reference, self.clean)
        prompt, suffix = control.exact_pair(self.engine.tokenizer, "abcd", "ef")
        cache = {"memory": self.torch.zeros((1,4), dtype=self.torch.bfloat16), "seen": 0}
        scores = []
        with self.torch.inference_mode():
            for step, target in enumerate(suffix):
                ids = prompt if step == 0 else [suffix[step-1]]
                out = self.engine.model(input_ids=self.torch.tensor([ids]), past_key_values=cache)
                scores.append(float(self.torch.log_softmax(out.logits[0,-1].float(), -1)[target]))
        self.assertEqual(result["token_logprobs"], scores)
        self.assertEqual(result["loglikelihood"], sum(scores))

    def test_manual_candidate_reference_matches_all_logits_without_generate(self):
        for condition in (self.clean, self.native):
            for mode in control.MODES:
                generated = self.engine.score_one("abcd", "efab", self.reference, condition,
                                                   mode=mode, verify_logits=True)
                with patch.object(self.engine.model, "generate", side_effect=AssertionError("generate forbidden")):
                    manual = self.engine.manual_score_one("abcd", "efab", self.reference, condition, mode=mode)
                self.assertEqual(manual["continuation_token_ids"], generated["continuation_token_ids"])
                self.assertEqual(manual["token_logprobs"], generated["token_logprobs"])
                self.assertEqual(manual["loglikelihood"], generated["loglikelihood"])
                self.assertEqual(manual["logits_sha256"],
                                 [r["logits_sha256"] for r in generated["step_readouts"]])
                self.assertEqual(manual["forward_input_widths"], [4, 1, 1, 1])
                self.assertEqual(manual["write_audit"], generated["write_audit"])
        self.assertTrue(all(not m._forward_hooks and not m._forward_pre_hooks
                            for m in self.engine.model.modules()))

    def test_patch_self_identity_otherfact_and_rejection(self):
        donor = self.engine.prepare_donor("abcd", self.reference, self.native,
            layer=0, component="mlp", prediction_step=0)
        patch_spec = {"layer": 0, "component": "mlp", "prediction_step": 0, "donor": donor}
        original = self.run_one()
        restored = self.run_one(patch=patch_spec)
        self.assertEqual(original["step_readouts"], restored["step_readouts"])
        self.assertEqual(restored["patch_audit"][0]["delta_norm"], 0.)
        other = self.engine.prepare_donor("abce", self.reference, self.clean,
            layer=0, component="mlp", prediction_step=0, donor_id="other_fact")
        changed = self.run_one(patch={**patch_spec, "donor": other})
        self.assertGreater(changed["patch_audit"][0]["delta_norm"], 0.)
        self.assertEqual(changed["patch_audit"][0]["donor_id"], "other_fact")
        for bad in ({**patch_spec, "component": "attention"},
                    {**patch_spec, "donor": {**donor, "reference_calibration_sha256": "wrong"}},
                    {**patch_spec, "donor": {**donor, "prefix_token_sha256": "wrong"}}):
            with self.assertRaises(AssertionError):
                self.run_one(patch=bad)
        self.assertTrue(all(not m._forward_hooks and not m._forward_pre_hooks
                            for m in self.engine.model.modules()))


if __name__ == "__main__":
    unittest.main()
