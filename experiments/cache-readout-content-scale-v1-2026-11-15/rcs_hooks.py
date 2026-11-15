"""RCS-01 t1 capture and t2 numerator/denominator use; no model loading."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cache-write-signal-background-v1-2026-11-11'))
import wsb_core as K
import wsb_run as W


def mixed_norm(x0, x1, gate, weight, epsilon, cell):
    """Native rsqrt/cast/weight/gate order, with binary endpoint selection."""
    import torch
    assert cell in ('00', '10', '01', '11')
    assert x0.shape == x1.shape == gate.shape and x0.dtype == x1.dtype
    numerator = x1 if cell[0] == '1' else x0
    denominator = x1 if cell[1] == '1' else x0
    inv = torch.rsqrt(denominator.float().pow(2).mean(-1, keepdim=True) + epsilon)
    out = weight * (numerator.float() * inv).to(numerator.dtype)
    out = out * torch.nn.functional.silu(gate.float())
    return out.to(numerator.dtype), inv


def _kernel_kwargs(kw):
    assert kw.pop('cu_seqlens', None) is None, 'packed sequences are outside RCS-01'
    assert kw.pop('use_cache', True) is True, 'persistent cache is required'
    assert not kw, ('unexpected kernel kwargs', kw)


def _cpu(t):
    return t.detach().cpu().clone()


def request_actual_error(actual, requested):
    """Compare saved/requested FP64 deltas on CPU, independent of runtime device."""
    import torch
    assert actual.dtype == requested.dtype == torch.float64 and actual.shape == requested.shape
    return (actual.detach().cpu() - requested.detach().cpu()).abs().max()


def _cache_metadata(cache):
    def scalars(obj):
        return {k: v for k, v in vars(obj).items() if v is None or isinstance(v, (str, bool, int, float))}
    return {'cache': scalars(cache), 'layers': [scalars(layer) for layer in cache.layers]}


class CapturingWriteHook(W.WriteHook):
    """The frozen WSB t1 operation, additionally retaining actual J/native_s."""
    def __init__(self, V, model, package=None, zero=False):
        super().__init__(V, model, package=package, zero=zero)
        self.states = {}

    def __enter__(self):
        import torch
        self.base.__enter__()

        def kern(query, key, value, g=None, beta=None, initial_state=None,
                 output_final_state=False, use_qk_l2norm_in_kernel=False, **kw):
            b = self.base
            if b.layer not in K.G:
                return b.orig_k(query, key, value, g=g, beta=beta, initial_state=initial_state,
                                output_final_state=output_final_state,
                                use_qk_l2norm_in_kernel=use_qk_l2norm_in_kernel, **kw)
            _kernel_kwargs(kw)
            assert b.layer not in self.calls
            self.calls.append(b.layer)
            captured = []

            def native(*args, **kwargs):
                out, state, error = self.V.LVKR.custom_update(*args, **kwargs)
                captured.append(state)
                return out, state, error

            delta = self.package[b.layer] if self.package is not None else None
            out, state, delta, rec = K.update(native, b.QM.l2norm, query, key, value, g, beta,
                initial_state, output_final_state, use_qk_l2norm_in_kernel, delta=delta)
            assert len(captured) == 1
            native_s = captured[0]
            J = state.double() - native_s.double()
            reconstructed = (state.double() - J).to(native_s.dtype)
            assert torch.equal(reconstructed, native_s), 'actual J does not recover native t1 state'
            self.states[b.layer] = {'J': _cpu(J), 'native_s': _cpu(native_s)}
            rec.update(state_sha256=self.V.F.th(state), native_state_sha256=self.V.F.th(native_s),
                       reconstructed_sha256=self.V.F.th(reconstructed), J_sha256=self.V.F.th(J),
                       delta_sha256=self.V.F.th(delta), delta_norm=float(delta.norm()),
                       J_norm=float(J.norm()),
                       request_actual_max_error=float(request_actual_error(self.states[b.layer]['J'], delta)),
                       reconstruction_exact=True)
            self.records[b.layer] = rec
            return out, state

        self.base.QM.torch_recurrent_gated_delta_rule = kern
        return self


class ReadoutHook:
    """One t2 forward. states=None is a no-shadow baseline/zero-J acceptance."""
    def __init__(self, V, model, states, cell):
        assert cell in ('00', '10', '01', '11') and (states is not None or cell == '11')
        if states is not None:
            assert set(states) == set(K.G)
        self.V, self.model, self.states, self.cell = V, model, states, cell
        self.base = V.LVKR.LHook(model, K.G, 'cell')
        self.records, self.tensors = {}, {}
        self.calls, self.norm_calls, self.norm_handles = [], [], []
        self.shadow_calls = 0
        self._pending = {}
        self._caches = {}

    def __enter__(self):
        import torch
        self.base.__enter__()
        try:
            for layer in K.G:
                attn = self.V.L.model_layers(self.model)[layer].linear_attn
                def capture_cache(_module, args, kwargs, layer=layer):
                    cache = kwargs.get('cache_params', args[1] if len(args) > 1 else None)
                    assert cache is not None, 't2 requires the actual persistent cache'
                    self._caches[layer] = cache
                self.norm_handles.append(attn.register_forward_pre_hook(capture_cache, with_kwargs=True))
                norm = attn.norm
                self.norm_handles.append(norm.register_forward_hook(self._norm_hook(layer)))

            def kern(query, key, value, g=None, beta=None, initial_state=None,
                     output_final_state=False, use_qk_l2norm_in_kernel=False, **kw):
                b = self.base
                args = dict(g=g, beta=beta, initial_state=initial_state, output_final_state=output_final_state,
                            use_qk_l2norm_in_kernel=use_qk_l2norm_in_kernel)
                if b.layer not in K.G:
                    return b.orig_k(query, key, value, **args, **kw)
                _kernel_kwargs(kw)
                assert query.shape[1] == 1 and output_final_state and initial_state is not None
                assert use_qk_l2norm_in_kernel and initial_state.dtype == torch.float32
                assert b.layer not in self.calls
                self.calls.append(b.layer)
                before = initial_state.clone()
                drivers = [t.clone() for t in (query, key, value, g, beta)]
                cache = self._caches[b.layer]
                metadata = _cache_metadata(cache)
                conv_before = self.V.L._get(cache.layers[b.layer], 'conv_states').clone()
                x1, state2 = b.orig_k(query, key, value, **args)
                assert torch.equal(initial_state, before), 'real kernel mutated S1'
                if self.states is None:
                    x0, shadow_s = x1, state2
                    J = None
                else:
                    saved = self.states[b.layer]
                    J = saved['J'].to(device=initial_state.device)
                    native_s = saved['native_s'].to(device=initial_state.device)
                    assert J.dtype == torch.float64 and J.shape == initial_state.shape
                    assert native_s.dtype == initial_state.dtype and native_s.shape == initial_state.shape
                    reconstructed = (initial_state.double() - J).to(initial_state.dtype)
                    assert torch.equal(reconstructed, native_s), 't2 S1-J != captured t1 native_s'
                    assert torch.equal((native_s.double()+J).float(), initial_state), 't2 start changed after t1'
                    shadow_before = reconstructed.clone()
                    x0, shadow_s = b.orig_k(query, key, value, **{**args, 'initial_state': reconstructed})
                    self.shadow_calls += 1
                    assert torch.equal(reconstructed, shadow_before), 'shadow kernel mutated its state input'
                assert torch.equal(initial_state, before), 'shadow kernel mutated real S1'
                assert all(torch.equal(a, z) for a, z in zip((query, key, value, g, beta), drivers)), 'kernel mutated driver'
                assert _cache_metadata(cache) == metadata, 'kernel changed cache management fields'
                assert torch.equal(self.V.L._get(cache.layers[b.layer], 'conv_states'), conv_before), 'kernel changed convolution cache'
                qn = b.QM.l2norm(query.transpose(1, 2).float().contiguous(), dim=-1, eps=1e-6)
                qn = qn / (qn.shape[-1] ** .5)
                raw = lambda s: (s * qn[:, :, 0].unsqueeze(-1)).sum(-2).unsqueeze(2).transpose(1, 2).contiguous()
                raw1, raw0 = raw(state2), raw(shadow_s)
                assert torch.equal(raw1.to(x1.dtype), x1) and torch.equal(raw0.to(x0.dtype), x0), 'kernel raw readback mismatch'
                rec = dict(S1_sha256=self.V.F.th(initial_state), S2_sha256=self.V.F.th(state2),
                           input_state_unchanged=True, drivers_unchanged=True, returned_real_S2=True,
                           cache_management_unchanged=True, conv_state_unchanged=True,
                           use_qk_l2norm_in_kernel=True, query_scale=1/(query.shape[-1] ** .5),
                           cell=self.cell, zero_J=self.states is None, shadow_calls=int(self.states is not None))
                if J is not None:
                    kn = b.QM.l2norm(key.transpose(1, 2).float().contiguous(), dim=-1, eps=1e-6)[:, :, 0].double()
                    qd = qn[:, :, 0].double()
                    ad = g[:, 0].double().exp()
                    bd = beta[:, 0].double()
                    w = ad.unsqueeze(-1) * (qd - bd.unsqueeze(-1)*kn*(kn*qd).sum(-1, keepdim=True))
                    expected = (J*w.unsqueeze(-1)).sum(-2).unsqueeze(1)
                    actual = raw1.double() - raw0.double()
                    error = float((actual-expected).abs().max()/max(1., float(expected.abs().max())))
                    assert error <= 1e-5, ('net D+E oracle', error)
                    rec['net_readout_oracle_error'] = error
                    rec['native_state_sha256'] = self.V.F.th(reconstructed)
                    self.tensors[b.layer] = {name: _cpu(t) for name, t in {
                        'x0': x0, 'x1': x1, 'raw0': raw0, 'raw1': raw1, 'q': query, 'k': key,
                        'v': value, 'log_decay': g, 'alpha': g.float().exp(), 'beta': beta}.items()}
                self.records[b.layer] = rec
                self._pending[b.layer] = (x0, x1, state2, state2.clone())
                return x1, state2

            self.base.QM.torch_recurrent_gated_delta_rule = kern
            return self
        except BaseException:
            self.__exit__(*sys.exc_info())
            raise

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
            rebuilt, inv1 = mixed_norm(x0, x1, gate, weight, eps, '11')
            assert torch.equal(rebuilt, original), 'native norm/cast-order mismatch'
            candidate, inv = mixed_norm(x0, x1, gate, weight, eps, self.cell)
            if self.states is None:
                for cell in ('00', '10', '01', '11'):
                    assert torch.equal(mixed_norm(x1, x1, gate, weight, eps, cell)[0], original), 'zero J factorial mismatch'
            result = original if self.cell == '11' else candidate
            assert torch.isfinite(result).all() and torch.equal(state2, state_before_norm), 'norm modified state or produced nonfinite output'
            assert torch.equal(self.V.L._get(self._caches[layer].layers[layer], 'recurrent_states'), state2), 'model did not commit real S2'
            self.norm_calls.append(layer)
            self.records[layer].update(norm_native_exact=True, norm_state_unchanged=True,
                cache_S2_committed=True,
                norm_input_dtype=str(x1.dtype), weight_dtype=str(weight.dtype), epsilon=float(eps),
                norm_shape=list(x1.shape), patch_sha256=self.V.F.th(result),
                native_norm_sha256=self.V.F.th(original), norm_weight_sha256=self.V.F.th(weight))
            if self.states is not None:
                tensors = self.tensors[layer]
                tensors.update({name: _cpu(t) for name, t in {
                    'z': gate, 'weight': weight, 'patch': result, 'native_norm': original,
                    'inv_r0': torch.rsqrt(x0.float().pow(2).mean(-1, keepdim=True)+eps),
                    'inv_r1': inv1, 'inv_used': inv}.items()})
                if self.cell == '11':
                    u, d = x0.double(), x1.double()-x0.double()
                    r0 = (u.square().mean(-1, keepdim=True)+eps).sqrt()
                    r1 = (x1.double().square().mean(-1, keepdim=True)+eps).sqrt()
                    a = weight.double() * torch.nn.functional.silu(gate.float()).double()
                    direct, scale = a*d/r1, a*u*(1/r1-1/r0)
                    change = a*x1.double()/r1 - a*u/r0
                    error = float((direct+scale-change).abs().max()/max(1., float(change.abs().max())))
                    assert error <= 1e-5
                    self.records[layer]['finite_difference_oracle_error'] = error
                    tensors.update({name: _cpu(t) for name, t in {
                        'direct_term': direct, 'scale_term': scale,
                        'relative_energy': (2*(u*d).sum(-1)+d.square().sum(-1))/(u.square().sum(-1)+u.shape[-1]*eps),
                        'r_ratio': r1/r0}.items()})
            return result
        return hook

    def __exit__(self, *exc):
        for handle in self.norm_handles:
            handle.remove()
        self.norm_handles = []
        self._pending.clear()
        self._caches.clear()
        return self.base.__exit__(*exc)

    def check(self):
        assert tuple(self.calls) == tuple(self.norm_calls) == tuple(self.base.conv_calls) == K.G
        assert self.shadow_calls == (len(K.G) if self.states is not None else 0)
        assert not self.norm_handles and not self.base.handles and not self._pending and not self._caches
        assert self.base.QM.torch_recurrent_gated_delta_rule is self.base.orig_k
        assert self.base.QM.causal_conv1d_update is self.base.orig_c
