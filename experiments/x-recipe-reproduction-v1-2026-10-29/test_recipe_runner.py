"""Small CPU checks of the new multi-point hook and shared-baseline schedule."""
import importlib.util
import unittest
from unittest.mock import patch

from recipe_engine import RecipeEngine, survey
from run_recipes import schedule, effective_generation, baseline_id, preflight_jobs, normalization_modes


class ScheduleChecks(unittest.TestCase):
    def test_real_preflight_covers_all_decoder_and_hook_modes(self):
        import json
        from pathlib import Path
        recipes = json.loads((Path(__file__).parent / "recipes.json").read_text())
        jobs = preflight_jobs(recipes)
        self.assertEqual(len(jobs), len({(r, q) for r, _, q, _ in jobs}))
        self.assertEqual({baseline_id(g) for _, _, _, g in jobs},
                         {baseline_id(effective_generation(r)) for r in recipes})
        selected = [r for r in recipes if r["id"] in {j[0] for j in jobs}]
        self.assertTrue(any(r["normalization"] == "per_prompt_median" for r in selected))
        self.assertTrue(any(len({p["layer"] for p in r["interventions"]}) < len(r["interventions"]) for r in selected))

    def test_formal_run_without_approval_never_locks_gpu(self):
        from argparse import Namespace
        import run_recipes
        with patch.object(run_recipes, "check_freeze", return_value="frozen"), \
             patch.object(run_recipes, "design", return_value=({}, [], [], {})), \
             patch.object(run_recipes.io, "read", side_effect=FileNotFoundError("formal_approval.json")), \
             patch.object(run_recipes, "lock_gpu") as lock:
            with self.assertRaises(FileNotFoundError):
                run_recipes.run(Namespace(execute=True, mode="run"))
            lock.assert_not_called()

    def test_unique_shared_baselines_and_five_answers_per_recipe(self):
        questions = [{"id": f"Q{i}"} for i in range(5)]
        recipes = [{"id": name, "interventions": [{"layer": 1, "neuron": 2, "dose": 0.3}],
                    "question_ids": [q["id"] for q in questions]} for name in ("A", "B", "C")]
        one = schedule(recipes, questions)
        two = schedule(recipes, questions, 0, 2) + schedule(recipes, questions, 1, 2)
        self.assertEqual(len(one), 20)
        self.assertEqual({(r, q) for r, _, q, _ in one}, {(r, q) for r, _, q, _ in two})
        self.assertEqual(len(two), len(one))

    def test_different_decoders_have_separate_paired_baselines(self):
        questions = [{"id": f"Q{i}"} for i in range(5)]
        recipes = [{"id": name, "interventions": [{"layer": 1, "neuron": 2, "dose": 0.3}],
                    "question_ids": [q["id"] for q in questions], "generation": {"repetition_penalty": penalty}}
                   for name, penalty in (("A", 1.), ("B", 1.1))]
        jobs = schedule(recipes, questions)
        self.assertEqual(len(jobs), 20)
        self.assertEqual(len({r for r, points, _, _ in jobs if not points}), 2)

    def test_decoder_validation(self):
        for invalid in ({"top_p": 0.8}, {"temperature": 0}, {"seed": -1}, {"do_sample": 1},
                        {"repetition_penalty": float("nan")}, {"max_new_tokens": 256}, {"min_p": 0.05},
                        {"do_sample": True, "min_p": -0.1}, {"do_sample": True, "min_p": 1.1}):
            with self.assertRaises(AssertionError):
                effective_generation({"generation": invalid})
        value = effective_generation({"generation": {"do_sample": True, "temperature": 0.7, "top_p": 0.9}})
        self.assertEqual(value["temperature"], 0.7)
        self.assertEqual(baseline_id(effective_generation({})), baseline_id(effective_generation({"generation": {"repetition_penalty": 1}})))

    def test_min_p_splits_sampling_baselines(self):
        recipes = [{"id": f"R{i}", "interventions": [{"layer": 1, "neuron": 2, "dose": 0.3}],
                    "question_ids": [f"Q{i}" for i in range(5)],
                    "generation": {"do_sample": True, "temperature": 0.7, "min_p": min_p}}
                   for i, min_p in enumerate((0.0, 0.05))]
        jobs = schedule(recipes, [])
        self.assertEqual(len(jobs), 20)
        self.assertEqual(len({r for r, points, _, _ in jobs if not points}), 2)
        self.assertEqual(effective_generation({})["min_p"], 0.0)

    def test_normalizations_do_not_split_untreated_baselines(self):
        recipes = [{"id": name, "interventions": [{"layer": 1, "neuron": 2, "dose": 0.3}],
                    "question_ids": [f"Q{i}" for i in range(5)], "normalization": mode}
                   for name, mode in (("A", "per_prompt_median"), ("B", "fixed_reference"))]
        self.assertEqual(len(schedule(recipes, [])), 15)
        self.assertEqual(normalization_modes(recipes)["zero"], "per_prompt_median")
        self.assertEqual(preflight_jobs(recipes)[0][2], "Q0")


@unittest.skipUnless(importlib.util.find_spec("torch"), "Torch required for CPU hook checks")
class HookChecks(unittest.TestCase):
    def setUp(self):
        import torch
        self.torch = torch
        self.engine = RecipeEngine.__new__(RecipeEngine)
        self.engine.torch = torch
        self.engine.modules = {i: torch.nn.Linear(4, 3, bias=False, dtype=torch.bfloat16) for i in range(2)}
        self.engine.column_norms = {str(i): torch.tensor([1., 2., 3., 4.]) for i in range(2)}
        self.cal = [{"residual_scales": {"0": 7.03125, "1": 10.01953125}}]
        self.mask = torch.tensor([[0, 1, 1]])
        self.x = torch.tensor([[[1., 2., 3., 4.], [2., 3., 4., 5.], [3., 4., 5., 6.]]], dtype=torch.bfloat16)
        self.points = [{"layer": 1, "neuron": 1, "dose": 0.42}, {"layer": 1, "neuron": 3, "dose": -0.28}]

    def test_same_layer_two_points_prefill_decode_padding_and_untouched(self):
        observed, original = [], self.x.clone()
        with self.engine._intervention(self.points, self.cal, self.mask):
            h = self.engine.modules[1].register_forward_pre_hook(lambda _m, a: observed.append(a[0].clone()))
            try:
                self.engine.modules[1](self.x)
                self.engine.modules[1](self.x[:, :1])
            finally:
                h.remove()
        expected, decode = self.x.clone(), self.x[:, :1].clone()
        for point in self.points:
            n = point["neuron"]
            amount = self.torch.tensor(point["dose"] * self.cal[0]["residual_scales"]["1"] / float(self.engine.column_norms["1"][n]), dtype=self.torch.bfloat16)
            expected[0, 1:, n] += amount
            decode[..., n] += amount
        self.assertTrue(self.torch.equal(observed[0], expected))
        self.assertTrue(self.torch.equal(observed[1], decode))
        self.assertTrue(self.torch.equal(self.x, original))
        self.assertTrue(all(not m._forward_pre_hooks for m in self.engine.modules.values()))

    def test_zero_restored_and_weight_immutability(self):
        module, torch = self.engine.modules[1], self.torch
        weights = module.weight.clone()
        baseline = module(self.x).detach().clone()
        with self.engine._intervention([dict(p, dose=0.) for p in self.points], self.cal, self.mask):
            self.assertTrue(torch.equal(module(self.x), baseline))
        with self.engine._intervention(self.points, self.cal, self.mask):
            module(self.x)
        self.assertTrue(torch.equal(module(self.x), baseline))
        self.assertTrue(torch.equal(module.weight, weights))

    def test_exception_removes_all_layer_hooks(self):
        points = self.points + [{"layer": 0, "neuron": 0, "dose": 1.0}]
        with self.assertRaisesRegex(RuntimeError, "synthetic"):
            with self.engine._intervention(points, self.cal, self.mask):
                raise RuntimeError("synthetic")
        self.assertTrue(all(not m._forward_pre_hooks for m in self.engine.modules.values()))

    def test_prompt_scale_is_clean_lower_median_and_hooks_are_removed(self):
        torch = self.torch
        self.engine.layers = [torch.nn.Identity() for _ in range(32)]
        self.engine.tokenizer = None
        residual = torch.tensor([[[100.], [2.], [4.], [9.], [11.]]], dtype=torch.bfloat16)
        self.engine._inputs = lambda _tokens: {}
        def forward(**_kwargs):
            for layer in self.engine.layers:
                layer(residual)
        self.engine.model = forward
        with patch.object(survey.transfer, "encode_text", return_value=[10, 20, 30, 40, 50]):
            result = self.engine.prompt_calibration("example")
        self.assertEqual(result["residual_scales"], {str(i): 4.0 for i in range(32)})
        self.assertEqual(result["input_token_count"], 5)
        self.assertEqual(result["normalization"], "per_prompt_median")
        self.assertTrue(all(not layer._forward_hooks for layer in self.engine.layers))

    def test_invalid_and_duplicate_points_never_install_hooks(self):
        for points in ([self.points[0], self.points[0]], [{"layer": 2, "neuron": 0, "dose": 1.}],
                       [{"layer": 1, "neuron": 4, "dose": 1.}], [{"layer": 1, "neuron": 0, "dose": float("nan")}]):
            with self.assertRaises(AssertionError):
                with self.engine._intervention(points, self.cal, self.mask):
                    self.fail("Invalid point reached forward")
            self.assertTrue(all(not m._forward_pre_hooks for m in self.engine.modules.values()))


if __name__ == "__main__":
    unittest.main()
