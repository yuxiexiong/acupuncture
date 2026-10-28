"""CPU tensor checks; never load a model or use CUDA."""
import importlib.util
import unittest

from dose_engine import DoseEngine


@unittest.skipUnless(importlib.util.find_spec("torch"), "Torch required for CPU hook acceptance")
class DoseHookChecks(unittest.TestCase):
    def setUp(self):
        import torch
        self.torch = torch
        self.engine = DoseEngine.__new__(DoseEngine)
        self.engine.torch = torch
        self.engine.modules = {i: torch.nn.Linear(4, 3, bias=False, dtype=torch.bfloat16) for i in range(2)}
        self.engine.column_norms = {str(i): torch.tensor([1., 2., 3., 4.]) for i in range(2)}
        self.calibrations = [{"residual_scales": {"0": 7.03125, "1": 10.01953125}}]
        self.mask = torch.tensor([[0, 1, 1]])
        self.x = torch.tensor([[[1., 2., 3., 4.], [2., 3., 4., 5.], [3., 4., 5., 6.]]], dtype=torch.bfloat16)

    def captured(self, arm, tensors):
        observed = []
        with self.engine._intervention(arm, self.calibrations, self.mask):
            self.assertFalse(self.engine.modules[0]._forward_pre_hooks)
            handle = self.engine.modules[1].register_forward_pre_hook(lambda _m, args: observed.append(args[0].clone()))
            try:
                for value in tensors:
                    self.engine.modules[1](value)
            finally:
                handle.remove()
        return observed

    def test_each_dose_uses_original_scale_then_bf16_and_one_channel(self):
        torch = self.torch
        weights = {i: module.weight.clone() for i, module in self.engine.modules.items()}
        original = self.x.clone()
        for dose in (0., -1 / 16, -1 / 8, -1 / 4, -1 / 2, -1., 1.):
            with self.subTest(dose=dose):
                observed = self.captured((1, 2, dose), [self.x, self.x[:, :1]])
                requested = dose * self.calibrations[0]["residual_scales"]["1"] / 3.
                amount = torch.tensor(requested, dtype=torch.bfloat16)
                self.assertEqual(self.engine.last_hook["requested_offset"], requested)
                self.assertEqual(self.engine.last_hook["bf16_offset"], float(amount))
                if dose < 0:
                    positive = torch.tensor(-requested, dtype=torch.bfloat16)
                    self.assertEqual(float(amount), -float(positive))
                if dose:
                    self.assertNotEqual(requested, dose * float(torch.tensor(self.calibrations[0]["residual_scales"]["1"] / 3., dtype=torch.bfloat16)))
                expected = self.x.clone()
                expected[0, 1:, 2] += amount
                self.assertTrue(torch.equal(observed[0], expected))
                decode = self.x[:, :1].clone()
                decode[..., 2] += amount
                self.assertTrue(torch.equal(observed[1], decode))
                self.assertTrue(torch.equal(self.x, original))
                self.assertEqual(self.engine.last_hook["calls"], 2)
                self.assertEqual(self.engine.last_hook["positions"], 4)
                self.assertTrue(all(not module._forward_pre_hooks for module in self.engine.modules.values()))
        self.assertTrue(all(torch.equal(weights[i], module.weight) for i, module in self.engine.modules.items()))

    def test_zero_hook_and_removed_hook_restore_exactly(self):
        torch, module = self.torch, self.engine.modules[1]
        baseline = module(self.x).detach().clone()
        with self.engine._intervention((1, 2, 0.), self.calibrations, self.mask):
            self.assertTrue(torch.equal(module(self.x), baseline))
        for dose in (-.0625, -.125, -.25, -.5, -1.):
            with self.engine._intervention((1, 2, dose), self.calibrations, self.mask):
                module(self.x)
            with self.engine._intervention("baseline", self.calibrations, self.mask):
                self.assertIsNone(self.engine.last_hook)
                self.assertTrue(torch.equal(module(self.x), baseline))

    def test_hook_removed_on_forward_failure(self):
        with self.assertRaisesRegex(RuntimeError, "intentional"):
            with self.engine._intervention((1, 2, -.5), self.calibrations, self.mask):
                self.engine.modules[1](self.x)
                raise RuntimeError("intentional")
        self.assertTrue(all(not module._forward_pre_hooks for module in self.engine.modules.values()))

    def test_invalid_doses_and_coordinates_never_install_hook(self):
        for arm in ((1, 2, .0625), (1, 2, -.75), (1, 2, .75), (1, 2, .3), (1, 2, 2.), (1, 2, float("nan")), (2, 2, -.5), (1, 4, -.5)):
            with self.subTest(arm=arm), self.assertRaises((AssertionError, ValueError)):
                with self.engine._intervention(arm, self.calibrations, self.mask):
                    self.fail("Invalid condition entered")
            self.assertTrue(all(not module._forward_pre_hooks for module in self.engine.modules.values()))


if __name__ == "__main__":
    unittest.main()
