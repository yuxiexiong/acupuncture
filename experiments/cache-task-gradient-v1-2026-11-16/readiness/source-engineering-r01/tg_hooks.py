"""Frozen additive norm controls; preserve the native t2 graph and forward dtype."""
from contextlib import nullcontext
import torch


def control_add(native, control):
    assert control.dtype == torch.float64 and control.shape == native.shape
    assert control.device == native.device
    return (native.double()+control).to(native.dtype)


class TaskControls:
    def __init__(self, modules, expected, patches=None):
        self.modules, self.expected, self.patches = modules, expected, patches
        self.handles, self.calls, self.controls, self.tensors, self.flow = [], [], {}, {}, {}
        self.logits, self.score, self.gradients = None, None, None

    def __enter__(self):
        assert not self.handles
        for layer, module in self.modules.items():
            self.handles.append(module.register_forward_hook(self._hook(layer)))
        return self

    def _hook(self, layer):
        def hook(module, args, native):
            assert layer not in self.calls
            self.calls.append(layer)
            assert native.shape == self.expected[layer].shape
            if self.patches is None:
                control = torch.zeros_like(native, dtype=torch.float64, requires_grad=True)
                assert torch.is_grad_enabled() and not torch.is_inference_mode_enabled()
                if len(self.calls) > 1:
                    assert native.requires_grad, ('earlier controls detached', layer)
            else:
                control = self.patches[layer].to(device=native.device)
            patch = control_add(native, control)
            self.controls[layer] = control
            self.flow[layer] = dict(native_requires_grad=native.requires_grad,
                                   control_leaf=control.is_leaf, patch_requires_grad=patch.requires_grad,
                                   control_dtype=str(control.dtype), output_dtype=str(patch.dtype))
            # Capture before bridge assertions so a mismatch retains the actual failed endpoint.
            self.tensors[layer] = {'native':native.detach().cpu().clone(), 'patch':patch.detach().cpu().clone()}
            assert torch.equal(self.tensors[layer]['native'], self.expected[layer]), ('native bridge',layer)
            if self.patches is None:
                assert torch.equal(patch, native), ('zero-control bridge',layer)
            return patch
        return hook

    def check(self):
        assert self.calls == list(self.modules)
        assert not self.handles

    def __exit__(self, *exc):
        for h in self.handles: h.remove()
        self.handles.clear()


def task_forward(V, model, cache, token, position, hook, target, donor, backward_started):
    """One unchanged native forward; autograd only records the t2 computation."""
    grad = hook.patches is None
    # Cache updates copy in-place. Snapshot saved values on mutation, without changing
    # the forward kernel/cache updates or detaching the earlier-control graph.
    graph = torch.autograd.graph.allow_mutation_on_saved_tensors() if grad else nullcontext()
    with torch.inference_mode(False), torch.set_grad_enabled(grad), graph:
        with hook:
            out = V.L.forward(model, [token], position, cache)
        hook.check()
        logits = out.logits[0,-1].float()
        hook.logits = logits.detach().cpu().clone()
        assert torch.isfinite(logits).all()
        loss = logits[donor]-logits[target]
        hook.score = float(loss.detach())
        gradients = None
        if grad:
            backward_started()
            gs = torch.autograd.grad(loss, tuple(hook.controls.values()), allow_unused=False)
            gradients = {l:g.detach().cpu().clone() for l,g in zip(hook.controls,gs)}
            hook.gradients = gradients
            assert all(g.dtype == torch.float64 and torch.isfinite(g).all() for g in gs)
    return out.past_key_values, logits.detach(), gradients
