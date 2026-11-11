"""CPU-only synthetic acceptance. --upstream additionally tests installed Qwen kernel, no weights."""
import argparse
import copy
import itertools
import json
import os
from pathlib import Path
import random
import tempfile
import subprocess
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

os.environ['CUDA_VISIBLE_DEVICES'] = ''
import torch
import wsb_core as K
import wsb_run as R

V = R.runtime()
UPSTREAM = False


def l2(x, dim=-1, eps=1e-6):
    return x*torch.rsqrt((x*x).sum(dim=dim, keepdim=True)+eps)


def sample(dtype=torch.float32):
    rng = torch.Generator().manual_seed(411)
    q, k, v = [torch.randn(1, 1, 2, 3, generator=rng).to(dtype) for _ in range(3)]
    return dict(query=q, key=k, value=v, g=-torch.rand(1, 1, 2, generator=rng),
                beta=torch.rand(1, 1, 2, generator=rng), initial_state=torch.randn(1, 2, 3, 3, generator=rng),
                output_final_state=True, use_qk_l2norm_in_kernel=True)


def local(**kw):
    return K.update(V.LVKR.custom_update, l2, **kw)


def world(rules):
    items, tables = K.panel()
    return {r: {c: {d['id']: (d['row'] if rules[c] == 'donor' else
                    items[r]['listed_codes'].index(items[r]['target']) if rules[c] == 'self' else rules[c])
                    for d in tables[r]} for c in K.CELLS} for r in items}


class Tests(unittest.TestCase):
    def test_counts_and_old_source_hashes(self):
        design = R.read(K.HERE/'design-audit.json')
        for p in design['sources']:
            self.assertEqual(R.sha(K.ROOT/p['path']), p['sha256'])
        self.assertEqual(K.limits('formal')['trajectories'], 2184)
        self.assertEqual(K.limits('preflight')['trajectories'], 192)
        self.assertEqual(K.limits('formal')['decode_forwards'], 69984)
        refs, _ = R.references()
        items, tables = K.panel()
        self.assertEqual(set(refs), set(items))
        self.assertEqual(sum('DO|'+d['id'] in refs[r]['directions'][K.MAIN] for r in items for d in tables[r]), 348)

    def test_source_diagonal_and_output_share_state(self):
        for dtype in (torch.float32, torch.bfloat16):
            a = sample(dtype)
            before = {k: x.clone() for k, x in a.items() if isinstance(x, torch.Tensor)}
            donor = a['value']*.7-1
            out, state, delta, rec = local(**a, shadow=donor)
            replay, replay_s, _, _ = local(**a, delta=delta)
            self.assertTrue(V.bit_equal(state, replay_s)[0])
            self.assertTrue(V.bit_equal(out, replay)[0])
            expected, es, _ = V.LVKR.custom_update(a['query'], a['key'], a['key'], donor,
                a['g'], a['beta'], a['initial_state'], True, True, l2, oracle=True)
            self.assertTrue(torch.equal(out, expected) and torch.equal(state, es))
            self.assertLessEqual(rec['delta_oracle'], 1e-5)
            self.assertTrue(all(torch.equal(a[k], x) for k, x in before.items()))
            self.assertEqual(delta.dtype, torch.float64)

    def test_fixed_package_cross_background_and_zero(self):
        a = sample()
        _, _, delta, _ = local(**a, shadow=a['value']+1)
        saved = delta.clone()
        b = {**a, 'initial_state': a['initial_state']*2, 'query': a['query']-.5}
        _, native, _, _ = local(**b)
        out, state, _, _ = local(**b, delta=delta)
        self.assertTrue(torch.equal(state, (native.double()+delta).float()))
        q = l2(b['query'].transpose(1, 2).float())/(b['query'].shape[-1]**.5)
        self.assertTrue(torch.equal(out[:, 0], (state*q[:, :, 0].unsqueeze(-1)).sum(-2)))
        self.assertTrue(torch.equal(delta, saved))
        zero_o, zero_s, _, _ = local(**a)
        original_o, original_s, _ = V.LVKR.custom_update(a['query'], a['key'], a['key'], a['value'],
            a['g'], a['beta'], a['initial_state'], True, True, l2, oracle=True)
        self.assertTrue(torch.equal(zero_o, original_o) and torch.equal(zero_s, original_s))
        if UPSTREAM:
            qm = V.gdn_module()
            actual, actual_s = qm.torch_recurrent_gated_delta_rule(**a, cu_seqlens=None, use_cache=True)
            self.assertTrue(V.bit_equal(zero_o, actual)[0] and V.bit_equal(zero_s, actual_s)[0])

    def test_tensor_rejects_bad_mode_shape_precision_and_nan(self):
        a = sample()
        bad = torch.zeros_like(a['initial_state'])
        with self.assertRaises(AssertionError): local(**a, delta=bad)
        with self.assertRaises(AssertionError): local(**a, delta=bad.double()[..., :1])
        with self.assertRaises(AssertionError): local(**a, delta=bad.double()+float('nan'))
        with self.assertRaises(AssertionError): local(**a, shadow=a['value'], delta=bad.double())
        with self.assertRaises(AssertionError): local(**{**a, 'output_final_state': False})

    def test_frozen_hook_conv_scope_coverage_cleanup_and_replay(self):
        def native(q, k, v, **kw):
            return V.LVKR.custom_update(q, k, k, v, kw['g'], kw['beta'], kw['initial_state'], True, True, l2)[:2]
        def conv(x, state, weight, bias=None, activation=None):
            state.copy_(torch.cat([state[..., 1:], x], -1))
            return state.sum(-1, keepdim=True)
        qm = NS(torch_recurrent_gated_delta_rule=native, causal_conv1d_update=conv, l2norm=l2)
        class Layer(torch.nn.Module):
            key_dim = value_dim = 4
            head_k_dim = head_v_dim = 2
            num_v_heads = num_k_heads = 2
            def forward(self, drive, **kernel_kwargs):
                b = torch.arange(48).reshape(1, 12, 4).float()/100
                y = qm.causal_conv1d_update(torch.ones(1, 12, 1)*drive, b, None)
                q, k, v = [x.reshape(1, 1, 2, 2) for x in y.transpose(1, 2).split(4, -1)]
                return qm.torch_recurrent_gated_delta_rule(q, k, v, g=-torch.ones(1, 1, 2),
                    beta=torch.ones(1, 1, 2)*.5, initial_state=torch.ones(1, 2, 2, 2),
                    output_final_state=True, use_qk_l2norm_in_kernel=True,
                    **({'cu_seqlens': None, 'use_cache': True} | kernel_kwargs))
        layers = [NS(linear_attn=Layer()) for _ in range(32)]
        donor = {i: torch.ones(1, 12, 4)*.9 for i in K.G}
        donor_before = copy.deepcopy(donor)
        def run(hook):
            drive, outputs = 1., []
            with hook:
                for layer in layers:
                    o, s = layer.linear_attn(drive)
                    outputs.append((o.clone(), s.clone()))
                    drive = float(o.mean())
            hook.check()
            return outputs
        with patch.object(V.LVKR, 'gdn_module', return_value=qm), patch.object(V.L, 'model_layers', return_value=layers), patch.object(V.LVKR, 'V_LO', 8):
            source = R.WriteHook(V, object(), donor=donor)
            a = run(source)
            replay = R.WriteHook(V, object(), package=source.deltas)
            b = run(replay)
            self.assertTrue(all(torch.equal(x, y) for xs, ys in zip(a, b) for x, y in zip(xs, ys)))
            self.assertEqual(source.base.n_shadow, 14)
            self.assertEqual(replay.base.n_shadow, 0)
            self.assertEqual(set(source.deltas), set(K.G))
            self.assertTrue(all(torch.equal(donor[i], donor_before[i]) for i in donor))
            for bad in ({'use_cache': False}, {'cu_seqlens': torch.tensor([0, 1])}, {'unknown': True}):
                with self.assertRaises(AssertionError):
                    with R.WriteHook(V, object(), zero=True):
                        layers[13].linear_attn(1., **bad)
            broken = R.WriteHook(V, object(), zero=True)
            with self.assertRaisesRegex(RuntimeError, 'injected'):
                with broken:
                    layers[13].linear_attn(1.)
                    raise RuntimeError('injected')
            self.assertIs(qm.torch_recurrent_gated_delta_rule, native)
            self.assertIs(qm.causal_conv1d_update, conv)
            self.assertTrue(all(not l.linear_attn._forward_pre_hooks for l in layers))
            with self.assertRaises(AssertionError): broken.check()

    def test_weights_equal_frozen_score_and_bounds_match_enumeration(self):
        _, tables = K.panel()
        rng = random.Random(13)
        for ds in tables.values():
            w = K.weights(ds)
            for _ in range(5):
                o = {d['id']: rng.choice([0, 1, 2, 'stop', 'other']) for d in ds}
                linear = sum(w[d][v] if v in (0, 1, 2) else 0 for d, v in o.items())
                self.assertAlmostEqual(linear, K.S.d_transfer(ds, o))
        ds = next(iter(tables.values()))
        out = {c: {d['id']: d['row'] for d in ds} for c in K.CELLS}
        missing = [('CC', ds[0]['id']), ('HH', ds[1]['id']), ('CH', ds[2]['id'])]
        for c, d in missing: out[c][d] = 'stop'
        for coef in K.COEF.values():
            got = K.bounds(ds, out, coef)
            vals = []
            for rows in itertools.product(range(3), repeat=len(missing)):
                one = copy.deepcopy(out)
                for (c, d), row in zip(missing, rows): one[c][d] = row
                vals.append(sum(a*K.S.d_transfer(ds, one[c]) for c, a in zip(K.CELLS, coef)))
            self.assertAlmostEqual(got[0], min(vals))
            self.assertAlmostEqual(got[1], max(vals))

    def test_all_result_worlds_and_delivery_guard(self):
        items, tables = K.panel()
        cases = [(['self','donor','self','donor'], {'S_C':'positive','S_H':'positive','B_C':'near_zero','B_H':'near_zero'}),
                 (['self','self','donor','donor'], {'S_C':'near_zero','S_H':'near_zero','B_C':'positive','B_H':'positive'}),
                 (['self','self','self','donor'], {'I':'positive'}),
                 (['donor']*4, {'G':'near_zero'}),
                 (['donor','self','donor','self'], {'S_C':'negative','S_H':'negative'})]
        for rules, labels in cases:
            result = K.analyse(world(dict(zip(K.CELLS, rules))), items, tables, n_boot=400)
            for name, want in labels.items(): self.assertEqual(result['contrasts'][name]['label'], want)
        out = world(dict(zip(K.CELLS, ['self','donor','self','donor'])))
        for r in out:
            out[r]['HH'] = {d: 'stop' for d in out[r]['HH']}
        result = K.analyse(out, items, tables, n_boot=400)
        self.assertEqual(result['contrasts']['S_H']['label'], 'delivery_degraded')
        self.assertEqual(K.label(.16, .6, -.01, .7, .95), 'indeterminate')
        self.assertEqual(K.label(-.03, .04, -.2, .2, 1), 'indeterminate')
        self.assertEqual(K.label(-.1, .11, -.1, .11, 1), 'indeterminate')
        del out[next(iter(out))]['CC'][next(iter(tables[next(iter(tables))]))['id']]
        with self.assertRaises(AssertionError): K.analyse(out, items, tables, n_boot=2)

    def test_scene_cluster_weighting_and_heterogeneous_uncertainty(self):
        items, tables = K.panel()
        out = world({c:'self' for c in K.CELLS})
        scenes = sorted({x['scenario'] for x in items.values()})
        for r in out:
            if items[r]['scenario'] in scenes[:3]:
                out[r]['HH'] = {d['id']:d['row'] for d in tables[r]}
        result = K.analyse(out, items, tables, n_boot=1000)
        expected = sum(K.S.d_transfer(tables[r], out[r]['HH']) for r in out)/48
        self.assertAlmostEqual(result['cells']['HH']['mean'], expected)
        self.assertEqual(result['clusters'], 6)
        self.assertEqual(result['contrasts']['G']['label'], 'indeterminate')
        self.assertEqual(result, K.analyse(out, items, tables, n_boot=1000))

    def test_counter_completion_and_immediate_stop(self):
        for stage in K.CAP:
            lim = K.limits(stage)
            rc = {'counts':{k:lim.get(k,0) for k in V.COUNT_KEYS},
                  'arm_counts':{k:lim[k] for k in ('baseline','source','replay','zero')}}
            R.check_counts(rc, stage, True)
            rc['counts']['trajectories'] -= 1
            with self.assertRaises(AssertionError): R.check_counts(rc, stage, True)
            rc['counts']['trajectories'] += 2
            with self.assertRaises(AssertionError): R.check_counts(rc, stage, False)
        counts = {k:0 for k in V.COUNT_KEYS}
        nr, _ = V.natural(None, None, V.STOP[0], 5, counts)
        self.assertFalse(nr['reached_t2'])
        self.assertEqual(counts['trajectories'], 0)  # regression documents why runner adds one
        refs, _ = R.references()
        it = next(iter(refs.values()))['item']
        engine = NS(tokenizer=NS(decode=lambda ids,**kw:'<|im_end|>'))
        z = torch.zeros(V.STOP[0]+1); z[V.STOP[0]] = 1
        ans = R.natural_answer(V, engine, None, z, {'counts':counts,'n':5,'item':it})
        self.assertEqual(counts['trajectories'], 1)
        self.assertEqual(ans['row'], 'stop')

    def test_snapshot_zero_exception_and_cache_change_rejection(self):
        fake = NS(F=V.F,L=NS(component_tensors=lambda c,t:[(0,'recurrent','state')], _get=lambda l,f:getattr(l,f)))
        a = NS(layers=[NS(state=torch.tensor([0., 2.]))])
        b = NS(layers=[NS(state=torch.tensor([-0., 2.]))])
        sa = R.snapshot(fake, a, torch.tensor([3.]), [])
        sb = R.snapshot(fake, b, torch.tensor([3.]), [])
        self.assertEqual(R.identical(sa, sb), 1)
        b.layers[0].state[1] += .01
        with self.assertRaises(AssertionError): R.identical(sa, R.snapshot(fake,b,torch.tensor([3.]),[]))
        b.layers[0].state[1] = 2
        b.layers[0].is_initialized = False
        with self.assertRaises(AssertionError): R.identical(sa, R.snapshot(fake,b,torch.tensor([3.]),[]))

    def test_budget_category_extrapolation_and_launch_denial(self):
        cats = ('load','prefix_token','formation_token','baseline','source','replay','zero','decode',
                'formation_overhead','receiver_overhead','pair_overhead','setup','integrity','finalize_per_pair')
        maxima = dict.fromkeys(cats, .01)
        self.assertGreater(K.project_seconds(maxima, 1467), 0)
        maxima['source'] = 100
        self.assertGreater(K.project_seconds(maxima, 1467), K.CAP['formal'])
        del maxima['decode']
        with self.assertRaises(AssertionError): K.project_seconds(maxima,1467)
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)/'never_created'
            with patch.object(R,'runtime',side_effect=AssertionError('runtime imported')), patch.object(R.subprocess,'check_output',side_effect=AssertionError('hardware queried')):
                for fn in (R.launch,R.worker):
                    with self.assertRaises(PermissionError): fn('preflight',0,K.HERE/'authorization.disabled.json',out)
            self.assertFalse(out.exists())

    def test_supervisor_timeout_preserves_failure_receipt(self):
        with tempfile.TemporaryDirectory(dir=K.HERE) as td:
            out = Path(td)/'runs'/'preflight'
            with patch.object(R,'HERE',Path(td)), patch.object(R,'authorize',return_value=({},0)), \
                 patch.object(R.subprocess,'check_output',side_effect=['','100000']), \
                 patch.object(R.shutil,'disk_usage',return_value=NS(free=K.STORAGE)), \
                 patch.object(R.subprocess,'run',side_effect=subprocess.TimeoutExpired('synthetic-worker',1440)) as proc:
                with self.assertRaisesRegex(RuntimeError,'timed out'):
                    R.launch('preflight',0,K.HERE/'authorization.disabled.json',out)
                self.assertEqual(proc.call_args.kwargs['timeout'],1440)
                self.assertEqual(proc.call_args.kwargs['env']['WSB_SUPERVISOR_PID'],str(os.getpid()))
                self.assertEqual(R.read(out/'receipt.json')['status'],'failed')
                self.assertEqual(R.read(out/'exit.json')['returncode'],-9)

    def test_timing_uses_selected_device_and_restores_forward(self):
        original = lambda *a,**kw: 'synthetic'
        fake = NS(L=NS(forward=original))
        meter = R.Meter(fake, 1)
        with patch.object(torch.cuda,'synchronize') as sync:
            with meter:
                meter.phase = 'formation'
                self.assertEqual(fake.L.forward(None,[1,2],0,None),'synthetic')
                fake.L.forward(None,[1],2,object())
                meter.phase = 'source'
                fake.L.forward(None,[1],3,object())
            self.assertEqual(sync.call_count,3)
            self.assertTrue(all(c.args == (1,) for c in sync.call_args_list))
        self.assertIs(fake.L.forward,original)
        self.assertEqual(set(meter.maxima),{'prefix_token','formation_token','source'})

    def test_asset_identity_ignores_elapsed_time_but_not_hash(self):
        expected = {'status':'passed','files':7,'manifest_sha256':'fixed','wall_seconds':5.}
        R.check_model_assets({**expected,'wall_seconds':9.},expected)
        for key,value in [('files',8),('manifest_sha256','changed'),('status','failed')]:
            with self.assertRaises(AssertionError): R.check_model_assets({**expected,key:value},expected)

    def test_stage_space_requirement_keeps_total_cap(self):
        self.assertEqual(K.required_free_bytes('preflight'),8*2**30)
        self.assertLess(K.required_free_bytes('preflight'),55*2**30)
        self.assertEqual(K.required_free_bytes('formal',48*2**30),48*2**30)
        with self.assertRaises(AssertionError): K.required_free_bytes('formal',65*2**30)
        with self.assertRaises(AssertionError): K.required_free_bytes('formal')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True)
    p.add_argument('--upstream', action='store_true')
    args = p.parse_args()
    UPSTREAM = args.upstream
    if UPSTREAM:
        qm = V.gdn_module()
        l2 = qm.l2norm
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    assert not torch.cuda.is_initialized()
    R.write(args.output, dict(status='passed' if result.wasSuccessful() else 'failed', tests_run=result.testsRun,
        failures=len(result.failures), errors=len(result.errors), model_forwards=0, cuda_initialized=False,
        upstream_kernel_tested=UPSTREAM, torch_version=torch.__version__, synthetic_kernel_calls=True,
        external_sources={str(Path(qm.__file__)):R.sha(qm.__file__)} if UPSTREAM else {},
        source_hashes={p.name:R.sha(p) for p in sorted(K.HERE.glob('*.py'))}), immutable=True)
    raise SystemExit(0 if result.wasSuccessful() else 1)
