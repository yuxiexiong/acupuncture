"""CPU numerical/cleanup acceptance, optionally against installed upstream code."""
import argparse
import copy
import json
import io
import os
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

os.environ['CUDA_VISIBLE_DEVICES'] = ''
import torch
import rcs_hooks as H

V = H.W.runtime()


def l2(x, dim=-1, eps=1e-6):
    return x * torch.rsqrt((x*x).sum(dim=dim, keepdim=True)+eps)


def native(q, k, v, **kw):
    return V.LVKR.custom_update(q, k, k, v, kw['g'], kw['beta'], kw['initial_state'],
        kw['output_final_state'], kw['use_qk_l2norm_in_kernel'], l2)[:2]


class Norm(torch.nn.Module):
    def __init__(self, dtype, dim=2):
        super().__init__()
        self.weight = torch.nn.Parameter(torch.linspace(.7, 1.1, dim, dtype=dtype))
        self.variance_epsilon, self.activation = 1e-6, 'silu'

    def forward(self, x, gate):
        dtype = x.dtype
        t = x.float()
        t = t * torch.rsqrt(t.pow(2).mean(-1, keepdim=True)+self.variance_epsilon)
        t = self.weight * t.to(dtype)
        return (t*torch.nn.functional.silu(gate.float())).to(dtype)


class World:
    def __init__(self, dtype=torch.bfloat16, kernel=native, heads=2, dim=2):
        def conv(x, state, weight, bias=None, activation=None):
            state.copy_(torch.cat([state[..., 1:], x], -1))
            return state.sum(-1, keepdim=True)
        self.qm = NS(torch_recurrent_gated_delta_rule=kernel, causal_conv1d_update=conv, l2norm=l2)
        self.kernel, self.conv = kernel, conv
        qm = self.qm
        class Layer(torch.nn.Module):
            key_dim = value_dim = heads*dim
            head_k_dim = head_v_dim = dim
            num_v_heads = num_k_heads = heads

            def __init__(self, index):
                super().__init__()
                self.layer_idx, self.norm = index, Norm(dtype, dim)

            def forward(self, drive, cache_params=None):
                state = cache_params.layers[self.layer_idx]
                projected = (torch.arange(3*heads*dim, dtype=torch.float32).reshape(1, 3*heads*dim, 1)/max(50, 3*heads*dim) + drive*.1).to(dtype)
                mixed = qm.causal_conv1d_update(projected, state.conv_states, None).transpose(1, 2)
                q, k, v = [x.reshape(1, 1, heads, dim) for x in mixed.split(heads*dim, -1)]
                o, s = qm.torch_recurrent_gated_delta_rule(q, k, v,
                    g=-torch.ones(1, 1, heads)*.3, beta=torch.ones(1, 1, heads)*.4,
                    initial_state=state.recurrent_states, output_final_state=True,
                    use_qk_l2norm_in_kernel=True, cu_seqlens=None, use_cache=True)
                state.recurrent_states = s
                gate = torch.full((heads, dim), .6+float(drive)*.05, dtype=dtype)
                return self.norm(o.reshape(heads, dim), gate).reshape(1, 1, heads*dim)

        self.layers = [NS(linear_attn=Layer(i)) for i in range(32)]
        gen = torch.Generator().manual_seed(1511)
        self.initial = NS(step=0, layers=[NS(record_past=False, recurrent_states=torch.randn(1, heads, dim, dim, generator=gen)*.1,
            conv_states=(torch.randn(1, 3*heads*dim, 4, generator=gen)*.02).to(dtype)) for _ in self.layers])

    def run(self, cache, hook=None, stop_at=None):
        def compute():
            drive = .25
            outputs = []
            with torch.inference_mode():
                for i, layer in enumerate(self.layers):
                    out = layer.linear_attn(drive, cache_params=cache)
                    outputs.append(out.clone())
                    drive = float(out.mean())
                    if i == stop_at:
                        raise RuntimeError('injected failure')
            return outputs
        with patch.object(V.LVKR, 'gdn_module', return_value=self.qm), patch.object(V.L, 'model_layers', return_value=self.layers), \
             patch.object(V.L, '_get', side_effect=lambda obj, field: getattr(obj, field)):
            # Hooks constructed outside the patched scope still use this synthetic runtime.
            if hook is not None:
                with hook:
                    out = compute()
                hook.check()
            else:
                out = compute()
        return out

    def write_hook(self, package=None, zero=False):
        with patch.object(V.LVKR, 'gdn_module', return_value=self.qm):
            return H.CapturingWriteHook(V, object(), package, zero)

    def read_hook(self, states, cell):
        with patch.object(V.LVKR, 'gdn_module', return_value=self.qm):
            return H.ReadoutHook(V, object(), states, cell)

    def assert_clean(self, test):
        test.assertIs(self.qm.torch_recurrent_gated_delta_rule, self.kernel)
        test.assertIs(self.qm.causal_conv1d_update, self.conv)
        for layer in self.layers:
            test.assertFalse(layer.linear_attn._forward_pre_hooks)
            test.assertFalse(layer.linear_attn.norm._forward_hooks)


class Tests(unittest.TestCase):
    def test_norm_dtype_order_and_zero_boundaries(self):
        gen = torch.Generator().manual_seed(1512)
        for dtype in (torch.float32, torch.bfloat16):
            x, z = [torch.randn(7, 2, generator=gen).to(dtype) for _ in range(2)]
            norm = Norm(dtype)
            actual = norm(x, z)
            for cell in ('00', '10', '01', '11'):
                self.assertTrue(torch.equal(H.mixed_norm(x, x, z, norm.weight, 1e-6, cell)[0], actual))
            zero = torch.zeros_like(x)
            self.assertTrue(torch.equal(H.mixed_norm(zero, x, z, norm.weight, 1e-6, '01')[0], zero))
            with self.assertRaises(AssertionError): H.mixed_norm(x, x, z, norm.weight, 1e-6, '12')

    def test_write_actual_j_and_zero_replay(self):
        for dtype in (torch.float32, torch.bfloat16):
            world = World(dtype)
            plain, zero = copy.deepcopy(world.initial), copy.deepcopy(world.initial)
            expected = world.run(plain)
            h = world.write_hook(zero=True)
            observed = world.run(zero, h)
            self.assertTrue(all(torch.equal(a, b) for a, b in zip(expected, observed)))
            self.assertTrue(all(torch.equal(plain.layers[i].recurrent_states, zero.layers[i].recurrent_states) for i in range(32)))
            package = {i: torch.full((1, 2, 2, 2), 2**-28, dtype=torch.float64) for i in H.K.G}
            saved = copy.deepcopy(package)
            h = world.write_hook(package=package)
            cache = copy.deepcopy(world.initial)
            world.run(cache, h)
            self.assertTrue(any(not torch.equal(data['J'], package[layer]) for layer, data in h.states.items()))
            for layer, data in h.states.items():
                self.assertEqual(data['J'].dtype, torch.float64)
                state = cache.layers[layer].recurrent_states
                self.assertTrue(torch.equal((state.double()-data['J']).float(), data['native_s']))
                self.assertTrue(torch.equal(package[layer], saved[layer]))
            world.assert_clean(self)

    def test_all_cells_native_state_and_dynamic_scope(self):
        world = World()
        package = {i: torch.tensor([[[[.03, -.02], [.01, .04]], [[-.03, .02], [.05, -.01]]]], dtype=torch.float64) for i in H.K.G}
        t1 = copy.deepcopy(world.initial)
        wh = world.write_hook(package)
        world.run(t1, wh)
        frozen = copy.deepcopy(t1)
        native_cache = copy.deepcopy(t1)
        expected = world.run(native_cache)
        all_outputs = {}
        for cell in ('00', '10', '01', '11'):
            cache = copy.deepcopy(t1)
            rh = world.read_hook(wh.states, cell)
            all_outputs[cell] = world.run(cache, rh)
            self.assertEqual(rh.shadow_calls, 14)
            self.assertEqual(set(rh.tensors), set(H.K.G))
            self.assertTrue(all(r['cache_S2_committed'] and r['cache_management_unchanged'] and r['conv_state_unchanged'] for r in rh.records.values()))
            self.assertTrue(all(r['net_readout_oracle_error'] <= 1e-5 for r in rh.records.values()))
            json.dumps(rh.records, allow_nan=False)
            if cell == '11':
                self.assertTrue(all(torch.equal(a, b) for a, b in zip(all_outputs[cell], expected)))
                self.assertTrue(all(torch.equal(cache.layers[i].recurrent_states, native_cache.layers[i].recurrent_states) for i in range(32)))
                self.assertTrue(all('direct_term' in x and 'scale_term' in x for x in rh.tensors.values()))
            else:
                self.assertTrue(all('direct_term' not in x for x in rh.tensors.values()))
            self.assertTrue(all(torch.equal(t1.layers[i].recurrent_states, frozen.layers[i].recurrent_states) for i in range(32)))
            world.assert_clean(self)
            # A subsequent t3 receives no hook; reusing the same completed hook must fail.
            world.run(cache)
            self.assertEqual(rh.shadow_calls, 14)
        self.assertTrue(any(not torch.equal(a, b) for a, b in zip(all_outputs['00'], all_outputs['11'])))

    def test_baseline_no_shadow_and_exception_cleanup(self):
        world = World()
        baseline = world.read_hook(None, '11')
        world.run(copy.deepcopy(world.initial), baseline)
        self.assertEqual(baseline.shadow_calls, 0)
        self.assertFalse(baseline.tensors)
        world.assert_clean(self)
        for hook in (world.write_hook(zero=True), world.read_hook(None, '11')):
            with self.assertRaisesRegex(RuntimeError, 'injected failure'):
                world.run(copy.deepcopy(world.initial), hook, stop_at=16)
            world.assert_clean(self)
            with self.assertRaises(AssertionError): hook.check()

    def test_saved_package_device_boundary(self):
        from torch._subclasses.fake_tensor import FakeTensor, FakeTensorMode
        # FakeTensor's constructor may initialize a real CUDA context on CUDA builds.
        # This is a metadata-only device regression; suppress that initialization explicitly.
        with patch('torch._subclasses.fake_tensor.init_gpu_context'):
            mode = FakeTensorMode()
            gpu = FakeTensor(mode, torch.empty(2, 3, device='meta', dtype=torch.float64), torch.device('cuda:1'))
            cpu = FakeTensor(mode, torch.empty(2, 3, device='meta', dtype=torch.float64), torch.device('cpu'))
            with mode:
                with self.assertRaisesRegex(RuntimeError, 'two different devices'):
                    gpu-cpu  # Regression: the original diagnostic mixed the two devices.
                fixed = H.request_actual_error(gpu, cpu)
                self.assertEqual(fixed.device.type, 'cpu')
                self.assertEqual(fixed.dtype, torch.float64)
        requested = torch.tensor([1., 2**-28], dtype=torch.float64)
        actual = requested + torch.tensor([2**-24, -2**-29], dtype=torch.float64)
        buf = io.BytesIO()
        torch.save({'J': actual, 'delta': requested}, buf)
        buf.seek(0)
        saved = torch.load(buf, map_location='cpu', weights_only=True)
        self.assertEqual(float(H.request_actual_error(saved['J'], saved['delta'])), 2**-24)
        self.assertTrue(torch.equal(saved['delta'], requested))
        self.assertFalse(torch.cuda.is_initialized())

    def test_real_head_dimensions_and_package_roundtrip(self):
        old_threads = torch.get_num_threads()
        torch.set_num_threads(1)
        try:
            world = World(torch.bfloat16, heads=32, dim=128)
            package = {i: torch.full((1, 32, 128, 128), .001, dtype=torch.float64) for i in H.K.G}
            cache = copy.deepcopy(world.initial)
            wh = world.write_hook(package)
            world.run(cache, wh)
            buf = io.BytesIO()
            torch.save(wh.states, buf)
            buf.seek(0)
            saved = torch.load(buf, map_location='cpu', weights_only=True)
            plain = world.run(copy.deepcopy(cache))
            for cell in ('00', '10', '01', '11'):
                rh = world.read_hook(saved, cell)
                observed = world.run(copy.deepcopy(cache), rh)
                self.assertTrue(all(r['net_readout_oracle_error'] <= 1e-5 for r in rh.records.values()))
                self.assertTrue(all(t['x0'].shape == (1, 1, 32, 128) for t in rh.tensors.values()))
                self.assertTrue(all(t['J'].device.type == t['native_s'].device.type == 'cpu' for t in saved.values()))
                if cell == '11':
                    self.assertTrue(all(torch.equal(a, b) for a, b in zip(plain, observed)))
                world.assert_clean(self)
        finally:
            torch.set_num_threads(old_threads)

    def test_corrupt_actual_state_rejected_and_cleaned(self):
        world = World()
        cache = copy.deepcopy(world.initial)
        wh = world.write_hook(zero=True)
        world.run(cache, wh)
        wh.states[13]['J'] = wh.states[13]['J'].clone()
        wh.states[13]['J'][0, 0, 0, 0] += 1
        bad = world.read_hook(wh.states, '01')
        with self.assertRaisesRegex(AssertionError, 'S1-J'):
            world.run(copy.deepcopy(cache), bad)
        world.assert_clean(self)


def upstream_check():
    qm = V.gdn_module()
    gen = torch.Generator().manual_seed(1513)
    old_threads = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        for dtype in (torch.float32, torch.bfloat16):
            # Real installed norm/kernel at actual head dimensions; never load a model.
            norm = qm.Qwen3_5RMSNormGated(128).to(dtype=dtype)
            x0, x1, z = [torch.randn(32, 128, generator=gen).to(dtype) for _ in range(3)]
            for cell, x in (('00', x0), ('11', x1)):
                actual = H.mixed_norm(x0, x1, z, norm.weight, norm.variance_epsilon, cell)[0]
                assert torch.equal(actual, norm(x, z)), 'upstream norm mismatch'
            world = World(dtype, kernel=qm.torch_recurrent_gated_delta_rule, heads=32, dim=128)
            package = {i: torch.randn(1, 32, 128, 128, generator=gen).double()*.02 for i in H.K.G}
            cache = copy.deepcopy(world.initial)
            wh = world.write_hook(package)
            world.run(cache, wh)
            expected = world.run(copy.deepcopy(cache))
            for cell in ('00', '10', '01', '11'):
                rh = world.read_hook(wh.states, cell)
                observed = world.run(copy.deepcopy(cache), rh)
                assert all(r['net_readout_oracle_error'] <= 1e-5 for r in rh.records.values())
                if cell == '11':
                    assert all(torch.equal(a, b) for a, b in zip(expected, observed))
    finally:
        torch.set_num_threads(old_threads)
    assert not torch.cuda.is_initialized()


def failure_state_check(path):
    package = torch.load(path, map_location='cpu', weights_only=True)
    for state in package['states'].values():
        j, native_s = state['J'], state['native_s']
        assert j.device.type == native_s.device.type == 'cpu'
        assert j.shape == (1, 32, 128, 128)
        actual = (native_s.double()+j).float()
        reproduced_j = actual.double()-native_s.double()
        assert torch.equal(j, reproduced_j)
        assert torch.equal((actual.double()-j).float(), native_s)
        assert float(H.request_actual_error(j, reproduced_j)) == 0
    assert package['states'], 'empty failed-state package'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--upstream', action='store_true')
    parser.add_argument('--failure-state', help='CPU-only reconstruction of a preserved engineering failure package')
    args = parser.parse_args()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    if args.upstream:
        upstream_check()
    if args.failure_state:
        failure_state_check(args.failure_state)
    assert not torch.cuda.is_initialized()
    print(json.dumps({'status': 'passed', 'model_forwards': 0, 'cuda_initialized': False,
                      'upstream_kernel_tested': args.upstream, 'failure_state_tested': bool(args.failure_state), 'torch_version': torch.__version__,
                      'tests_run': result.testsRun, 'skipped': len(result.skipped)}))
