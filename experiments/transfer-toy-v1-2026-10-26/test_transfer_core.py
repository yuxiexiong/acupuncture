"""CPU math controls: paired ridge, one-column projection, normalization, source sampling."""
import os
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
import unittest
import torch
from fit_mapping import ridge_statistics, solve_ridge, target_condition, random_sources
from collect_activations import evenly


class TransferMathTests(unittest.TestCase):
    def test_weighted_affine_mapping_and_increment(self):
        torch.manual_seed(7)
        x = torch.randn(120, 4)
        true_m = torch.tensor([[1., 2., 0., 0.], [0., -.5, 1., 0.], [0., 0., 0., 3.]])
        bias = torch.tensor([12., -5., 8.])
        y = x @ true_m.T + bias
        weights = torch.cat((torch.full((20,), .5 / 20), torch.full((100,), .5 / 100)))
        matrix, fitted_bias = solve_ridge(ridge_statistics(x, y, weights), 1e-8)
        self.assertTrue(torch.allclose(matrix, true_m, atol=2e-5))
        self.assertTrue(torch.allclose(fitted_bias, bias, atol=2e-5))
        delta = torch.tensor([.2, -.1, .3, 1.])
        self.assertTrue(torch.allclose((matrix @ (x[0] + delta) + fitted_bias) - (matrix @ x[0] + fitted_bias), matrix @ delta, atol=2e-6))

    def test_projection_sign_tie_and_norm(self):
        unit = torch.tensor([1., 0.])
        matrix = torch.tensor([[-3., 0.], [4., 1.]])
        columns = torch.tensor([[2., -2., 0.], [0., 0., 10.]])
        specs, audit, mapped = target_condition(unit, matrix, columns)
        self.assertEqual(audit["index"], 2)
        self.assertEqual(audit["sign"], 1)
        self.assertAlmostEqual(audit["reconstruction_fraction"], 16 / 25)
        projected = columns[:, audit["index"]] * specs["S_proj"]["coefficient"]
        self.assertTrue(torch.allclose(projected, torch.tensor([0., 4.])))
        self.assertAlmostEqual(float(specs["D_match"]["vector"].norm()), 1)
        self.assertAlmostEqual(float((columns[:, audit["index"]] * specs["S_recipe"]["coefficient"]).norm()), 1)
        _, tie, _ = target_condition(torch.tensor([1., 0.]), torch.eye(2), columns[:, :2])
        self.assertEqual(tie["index"], 0)

    def test_synthetic_channel_identity(self):
        torch.manual_seed(3)
        weight, a = torch.randn(13, 19), torch.randn(5, 19)
        n, offset = 7, -2.5
        changed = a.clone()
        changed[:, n] += offset
        self.assertTrue(torch.allclose(changed @ weight.T, a @ weight.T + offset * weight[:, n], atol=2e-6))

    def test_zero_mapping_fails(self):
        with self.assertRaises(AssertionError):
            target_condition(torch.ones(2), torch.zeros(3, 2), torch.ones(3, 4))

    def test_deterministic_random_source_strata(self):
        torch.manual_seed(4)
        columns = {str(l): torch.randn(3, 9216) for l in (13, 14)}
        rms = {str(l): torch.rand(9216) for l in (13, 14)}
        a, audit_a = random_sources(columns, rms)
        b, audit_b = random_sources(columns, rms)
        self.assertEqual(a, b)
        self.assertEqual(audit_a, audit_b)
        for layer, true_index in (("13", 7956), ("14", 8949)):
            indices = [a[f"random{i}"][layer] for i in (1, 2, 3)]
            self.assertEqual(len(set(indices)), 3)
            self.assertNotIn(true_index, indices)

    def test_position_sampling_unique(self):
        selected = evenly(list(range(512)), 128)
        self.assertEqual(len(set(selected)), 128)
        self.assertEqual((selected[0], selected[-1]), (0, 511))


if __name__ == "__main__":
    unittest.main()
