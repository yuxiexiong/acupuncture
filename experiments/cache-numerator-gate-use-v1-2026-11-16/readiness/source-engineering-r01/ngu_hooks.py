"""NGU: reuse RCS true/shadow kernels; exchange only the numerator-use gate."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'cache-readout-content-scale-v1-2026-11-15'))
import rcs_hooks as H


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
    rebuilt = (native.double()+ref-cur).to(native.dtype)
    same = torch.equal(gate, reference)
    zero = torch.equal(x0, x1)
    if same or zero:
        assert torch.equal(rebuilt, native), 'identity endpoint failed'
        result = native
    else:
        result = rebuilt
    assert torch.isfinite(result).all()
    return result, cur, ref, inv


class GateUseHook(H.ReadoutHook):
    def __init__(self, V, model, states, references):
        assert set(references) == set(H.K.G)
        self.references = references
        super().__init__(V, model, states, '11')

    def _norm_hook(self, layer):
        original_hook = super()._norm_hook(layer)
        def hook(module, args, original):
            import torch
            x1, gate = args
            x0 = self._pending[layer][0].reshape_as(x1)
            baseline = original_hook(module, args, original)
            reference = self.references[layer].to(device=gate.device)
            assert reference.dtype == gate.dtype and reference.shape == gate.shape
            result, cur, ref, inv = gate_patch(x0, x1, gate, reference,
                                             module.weight, module.variance_epsilon, baseline)
            # Local endpoint identities incur no extra model forwards.
            same = gate_patch(x0, x1, gate, gate, module.weight, module.variance_epsilon, baseline)[0]
            zero = gate_patch(x1, x1, gate, reference, module.weight, module.variance_epsilon, baseline)[0]
            assert torch.equal(same, baseline) and torch.equal(zero, baseline)
            self.records[layer].update(cell='gate_exchange', same_gate_exact=True, zero_increment_exact=True,
                reference_gate_sha256=self.V.F.th(reference), current_gate_sha256=self.V.F.th(gate),
                finite_endpoint_oracle_exact=torch.equal(result, (baseline.double()+ref-cur).to(result.dtype)),
                patch_sha256=self.V.F.th(result), numerator_current_norm=float(cur.norm()),
                numerator_reference_norm=float(ref.norm()))
            self.tensors[layer] = {k:H._cpu(v) for k,v in {
                'x0':x0, 'x1':x1, 'z_cur':gate, 'z_ref':reference, 'inv_r1':inv,
                'delta_cur':cur, 'delta_ref':ref, 'native':baseline, 'patch':result}.items()}
            return result
        return hook
