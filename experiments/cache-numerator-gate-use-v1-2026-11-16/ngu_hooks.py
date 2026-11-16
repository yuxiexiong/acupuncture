"""NGU: reuse RCS true/shadow kernels; exchange only the numerator-use gate."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'cache-readout-content-scale-v1-2026-11-15'))
import rcs_hooks as H


def replace_increment(native, current, reference, identity=False):
    import torch
    rebuilt = (native.double()+reference-current).to(native.dtype)
    if identity:
        assert torch.equal(rebuilt, native), 'identity endpoint failed'
        return native
    return rebuilt


def gate_patch(x0, x1, gate, reference, weight, epsilon, native=None):
    import torch
    assert gate.shape == reference.shape == x1.shape == x0.shape
    assert gate.dtype == reference.dtype and gate.device == reference.device
    f11, inv = H.mixed_norm(x0, x1, gate, weight, epsilon, '11')
    f01 = H.mixed_norm(x0, x1, gate, weight, epsilon, '01')[0]
    ref11 = H.mixed_norm(x0, x1, reference, weight, epsilon, '11')[0]
    ref01 = H.mixed_norm(x0, x1, reference, weight, epsilon, '01')[0]
    if native is None: native = f11
    assert torch.equal(native, f11), 'native dtype/cast ordering changed'
    cur, ref = f11.double()-f01.double(), ref11.double()-ref01.double()
    # Exercise the same composition/identity branch with cached rounded endpoints.
    assert torch.equal(replace_increment(native, cur, cur, True), native)
    zero_cur, zero_ref = f11.double()-f11.double(), ref11.double()-ref11.double()
    assert torch.equal(replace_increment(native, zero_cur, zero_ref, True), native)
    result = replace_increment(native, cur, ref,
                               torch.equal(gate, reference) or torch.equal(x0, x1))
    assert torch.isfinite(result).all()
    return result, cur, ref, inv


class GateUseHook(H.ReadoutHook):
    def __init__(self, V, model, states, references):
        assert set(references) == set(H.K.G)
        self.references = references
        super().__init__(V, model, states, '11')

    def _norm_hook(self, layer):
        def hook(module, args, original):
            import torch
            assert layer in self._pending and layer not in self.norm_calls
            assert len(args) == 2, 'unexpected gated norm signature'
            x1, gate = args
            x0, kernel_x1, state2, state_before_norm = self._pending.pop(layer)
            assert x1.numel() == kernel_x1.numel() and x1.shape[-1] == kernel_x1.shape[-1]
            assert torch.equal(x1, kernel_x1.reshape_as(x1)), 'wrong norm/kernel pairing'
            x0 = x0.reshape_as(x1)
            eps, weight = module.variance_epsilon, module.weight
            assert module.activation == 'silu'
            reference = self.references[layer].to(device=gate.device)
            result, cur, ref, inv = gate_patch(x0, x1, gate, reference, weight, eps, original)
            assert torch.equal(state2, state_before_norm), 'norm modified state'
            assert torch.equal(self.V.L._get(self._caches[layer].layers[layer], 'recurrent_states'), state2), 'model did not commit real S2'
            self.norm_calls.append(layer)
            self.records[layer].update(norm_native_exact=True, norm_state_unchanged=True,
                cache_S2_committed=True, norm_input_dtype=str(x1.dtype), weight_dtype=str(weight.dtype),
                epsilon=float(eps), norm_shape=list(x1.shape), native_norm_sha256=self.V.F.th(original),
                norm_weight_sha256=self.V.F.th(weight),
                cell='gate_exchange', same_gate_exact=True, zero_increment_exact=True,
                reference_gate_sha256=self.V.F.th(reference), current_gate_sha256=self.V.F.th(gate),
                finite_endpoint_oracle_exact=torch.equal(result, (original.double()+ref-cur).to(result.dtype)),
                patch_sha256=self.V.F.th(result), numerator_current_norm=float(cur.norm()),
                numerator_reference_norm=float(ref.norm()))
            self.tensors[layer] = {k:H._cpu(v) for k,v in {
                'x0':x0, 'x1':x1, 'z_cur':gate, 'z_ref':reference, 'inv_r1':inv,
                'delta_cur':cur, 'delta_ref':ref, 'native':original, 'patch':result}.items()}
            return result
        return hook
