"""Mechanical checks of trajectory boundaries, KL, and same-state local audit."""
from contextlib import contextmanager
import types
import unittest

import source_bridge as bridge

try:
    import torch
except ImportError:
    torch = None


class Boundaries(unittest.TestCase):
    def test_eos_is_included_and_later_turns_excluded(self):
        self.assertEqual(bridge.trim_at_first_eos([3, 248046, 7, 248044]), [3, 248046])
        self.assertEqual(bridge.trim_at_first_eos([3, 248044, 7]), [3, 248044])
        self.assertEqual(bridge.trim_at_first_eos([3, 4]), [3, 4])

    def test_first_answer_prediction_belongs_to_last_prompt_token(self):
        self.assertEqual(bridge.segments(3, 6), {"prompt_next_token": [0, 1],
            "answer_next_token": [2, 3, 4], "after_final_token": [5]})
        indices = [i for positions in bridge.segments(3, 6).values() for i in positions]
        self.assertEqual(indices, list(range(6)))


@unittest.skipIf(torch is None, "PyTorch unavailable on this host; run in frozen remote environment")
class TensorChecks(unittest.TestCase):
    def test_chunked_kl_matches_direct(self):
        torch.manual_seed(12)
        a, b = torch.randn(17, 29), torch.randn(17, 29)
        result = bridge.compare_logits(a, b, 5, chunk_size=3)
        loga, logb = a.log_softmax(-1), b.log_softmax(-1)
        expected = (loga.exp() * (loga - logb)).sum(-1)
        torch.testing.assert_close(torch.tensor(result["per_position"]["kl_channel_to_vector"]), expected)
        identical = bridge.compare_logits(a, a, 5, chunk_size=4)
        self.assertTrue(all(identical["per_position"]["argmax_equal"]))
        self.assertEqual(identical["summary"]["all_positions"]["kl_channel_to_vector_mean"], 0.0)

    def test_same_state_channel_difference_and_l14_preceding_b(self):
        from transfer_engine import TransferEngine

        class Layer(torch.nn.Module):
            def __init__(self, up, down):
                super().__init__()
                self.up, self.down_proj = up, down

            def forward(self, hidden):
                return hidden + self.down_proj(self.up(hidden))

        class Model(torch.nn.Module):
            def __init__(self, layers):
                super().__init__()
                self.first, self.second = layers[13], layers[14]

            def forward(self, input_ids, attention_mask, **_):
                hidden = torch.nn.functional.one_hot(input_ids % 2, 2).float()
                hidden = self.second(self.first(hidden))
                return types.SimpleNamespace(logits=hidden)

        class Tiny:
            pass

        engine = Tiny()
        engine.torch, engine.device = torch, "cpu"
        engine.layers, engine.modules = {}, {}
        for layer in (13, 14):
            up = torch.nn.Linear(2, 3, bias=False)
            down = torch.nn.Linear(3, 2, bias=False)
            with torch.no_grad():
                up.weight.copy_(torch.tensor([[1., 2.], [3., 1.], [2., 4.]]))
                down.weight.copy_(torch.tensor([[.5, .2, .7], [.3, .4, .2]]))
            engine.layers[layer] = Layer(up, down)
            engine.modules[layer] = down
        engine.column_norms = {str(layer): module.weight.norm(dim=0).detach() for layer, module in engine.modules.items()}
        engine._inputs = lambda seqs: {"input_ids": torch.tensor(seqs), "attention_mask": torch.ones_like(torch.tensor(seqs))}
        engine._intervention = types.MethodType(TransferEngine._intervention, engine)
        engine.model = Model(engine.layers)
        indices = {13: 0, 14: 1}
        engine.conditions = {"S_channel": {}, "S_vector": {}}
        for layer in (13, 14):
            n, sign = indices[layer], bridge.SIGNS[layer]
            norm = float(engine.column_norms[str(layer)][n])
            engine.conditions["S_channel"][str(layer)] = {"kind": "channel", "index": n,
                "scale": "target", "coefficient": sign / norm}
            engine.conditions["S_vector"][str(layer)] = {"kind": "vector",
                "vector": sign * engine.modules[layer].weight[:, n].detach() / norm,
                "scale": "target", "coefficient": 1.0}
        original_indices = bridge.SOURCE_NEURONS
        bridge.SOURCE_NEURONS = indices
        try:
            calibration = {"residual_scales": {"13": 2.0, "14": 3.0}}
            a, local_a, _ = bridge.forward_with_local_audit(engine, [0, 1, 0], "S_channel", calibration)
            b, local_b, _ = bridge.forward_with_local_audit(engine, [0, 1, 0], "S_vector", calibration)
            torch.testing.assert_close(a, b)
            self.assertTrue(local_a["14"]["preceding_B_active"])
            for item in (local_a, local_b):
                for layer in ("13", "14"):
                    self.assertLess(max(item[layer]["relative_error"]), 1e-5)
            self.assertFalse(any(module._forward_pre_hooks for module in engine.modules.values()))
            self.assertFalse(any(layer._forward_hooks for layer in engine.layers.values()))
        finally:
            bridge.SOURCE_NEURONS = original_indices


if __name__ == "__main__":
    unittest.main()
