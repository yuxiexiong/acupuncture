"""One small check: correct injection, exact zero, cleanup and saved patch roundtrip."""
from pathlib import Path
from tempfile import TemporaryDirectory

import torch
import probe


def main():
    torch.manual_seed(0)
    # Small neurons preserve both layer keys while avoiding a large test matrix.
    original_targets = probe.TARGETS
    probe.TARGETS = ((14, 2, 1.0), (13, 1, -1.0))
    modules = {layer: torch.nn.Linear(4, 3, bias=False).double() for layer in (14, 13)}
    original_weights = {layer: module.weight.detach().clone() for layer, module in modules.items()}
    inputs = torch.randn(1, 5, 4, dtype=torch.float64)
    offsets = {14: 0.75, 13: -0.25}
    try:
        baselines = {layer: module(inputs) for layer, module in modules.items()}
        with probe.activation_offsets(modules, {14: 0.0, 13: 0.0}):
            assert all(torch.equal(module(inputs), baselines[layer]) for layer, module in modules.items())
        with probe.activation_offsets(modules, offsets):
            dynamic = {layer: module(inputs) for layer, module in modules.items()}
        for layer, neuron, _ in probe.TARGETS:
            expected = baselines[layer] + offsets[layer] * modules[layer].weight[:, neuron]
            torch.testing.assert_close(dynamic[layer], expected, atol=1e-14, rtol=1e-14)
        exact_biases = {str(layer): offsets[layer] * modules[layer].weight[:, neuron] for layer, neuron, _ in probe.TARGETS}
        with probe.fixed_biases(modules, exact_biases):
            for layer, module in modules.items():
                torch.testing.assert_close(module(inputs), dynamic[layer], atol=1e-14, rtol=1e-14)
        # The first (large) token is excluded, and residuals are captured after each layer.
        layers = {layer: torch.nn.Identity() for layer in modules}
        fake_model = torch.nn.Module()
        fake_model.forward = lambda input_ids, **kwargs: (
            layers[13](input_ids * 2), layers[14](input_ids * 3)
        )
        scales = probe.residual_scales(fake_model, layers, {"input_ids": torch.tensor([[[100.0], [1.0], [2.0], [3.0]]])})
        assert scales == {14: 6.0, 13: 4.0}
        assert all(not layer._forward_hooks for layer in layers.values())
        with TemporaryDirectory() as directory:
            patch = Path(directory) / "patch.safetensors"
            loaded = probe.save_bias_patch(modules, offsets, patch)
            with probe.fixed_biases(modules, loaded):
                for layer, module in modules.items():
                    # The persistent patch intentionally stores bias values in float32.
                    torch.testing.assert_close(module(inputs), dynamic[layer], atol=1e-7, rtol=1e-7)
        try:
            with probe.activation_offsets(modules, offsets):
                raise RuntimeError("Exercise cleanup")
        except RuntimeError:
            pass
        assert all(module.bias is None and not module._forward_pre_hooks for module in modules.values())
        assert all(torch.equal(module.weight, original_weights[layer]) for layer, module in modules.items())
        print("PASS: zero, additive direction, fixed-bias equivalence, saved patch reload, cleanup, unchanged W")
    finally:
        probe.TARGETS = original_targets


if __name__ == "__main__":
    main()
