"""CPU-only tests: synthetic algebra, held-scenario exclusion, hooks, accounting and launch denial.

--upstream uses the installed frozen Transformers kernel, never a model or weights.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

os.environ['CUDA_VISIBLE_DEVICES'] = ''
import torch
import ngc_core as K
import ngc_run as R


def l2(x, dim=-1, eps=1e-6):
    return x * torch.rsqrt((x*x).sum(dim=dim, keepdim=True)+eps)


def native(query, key, value, g, beta, initial_state, output_final_state=False, use_qk_l2norm_in_kernel=False, **kw):
    q,k,v = query,key,value
    dtype = q.dtype
    q,k,v,b,g = [x.transpose(1,2).float() for x in (q,k,v,beta,g)]
    if use_qk_l2norm_in_kernel:
        q,k = l2(q),l2(k)
    q = q/(q.shape[-1]**.5)
    s = initial_state.float()
    o = torch.zeros_like(v)
    for i in range(q.shape[2]):
        s = s*g[:,:,i].exp()[...,None,None]
        delta = (v[:,:,i]-(s*k[:,:,i].unsqueeze(-1)).sum(-2))*b[:,:,i].unsqueeze(-1)
        s = s+k[:,:,i].unsqueeze(-1)*delta.unsqueeze(-2)
        o[:,:,i] = (s*q[:,:,i].unsqueeze(-1)).sum(-2)
    return o.transpose(1,2).contiguous().to(dtype), s if output_final_state else None


UPSTREAM = False
ORIGINAL, NORMALIZE = native, l2


class Tests(unittest.TestCase):
    def sample(self, dtype=torch.float32):
        gen = torch.Generator().manual_seed(178)
        q,k,v = [torch.randn(1,1,4,5,generator=gen).to(dtype) for _ in range(3)]
        return dict(query=q,key=k,value=v,g=-torch.rand(1,1,4,generator=gen),
                    beta=torch.sigmoid(torch.randn(1,1,4,generator=gen)),
                    initial_state=torch.randn(1,4,5,5,generator=gen),output_final_state=True,
                    use_qk_l2norm_in_kernel=True)

    def test_identity_and_capture_match_native(self):
        for dtype in (torch.float32,torch.bfloat16):
            a = self.sample(dtype)
            before = {k:v.clone() for k,v in a.items() if isinstance(v,torch.Tensor)}
            o,s,r = K.update(ORIGINAL,NORMALIZE,**a)
            on,sn = ORIGINAL(**a)
            self.assertTrue(torch.equal(o,on) and torch.equal(s,sn))
            oi,si,_ = K.update(ORIGINAL,NORMALIZE,**a,target=r['gain_actual'])
            self.assertTrue(torch.equal(oi,on) and torch.equal(si,sn))
            self.assertTrue(all(torch.equal(v,a[k]) for k,v in before.items()))

    def test_write_only_change_and_output_same_state(self):
        a = self.sample(torch.bfloat16)
        _,s0,r0 = K.update(ORIGINAL,NORMALIZE,**a)
        target = r0['gain_actual']*torch.tensor([[.4,1.7,.8,2.]])
        o,s,r = K.update(ORIGINAL,NORMALIZE,**a,target=target)
        k,v = r['k'].double(),r['v'].double()
        expected = ((target.double()-r0['gain_actual'].double())/k.norm(dim=-1)).unsqueeze(-1).unsqueeze(-1)*k.unsqueeze(-1)*v.unsqueeze(-2)
        torch.testing.assert_close((s-s0).double(),expected,atol=2e-6,rtol=2e-5)
        self.assertTrue(torch.equal(r['E_read'],r0['E_read']))
        self.assertTrue(torch.equal(o[:,0],(s*r['q'].unsqueeze(-1)).sum(-2).to(o.dtype)))
        self.assertLess(r['oracle_error'],1e-5)

    def test_held_scenario_exclusion_and_equal_weight(self):
        scenarios = {'a':'A','b':'B','c':'B','d':'C'}
        gains = {i:{'C':torch.ones(2,3),**{d:torch.exp(torch.full((2,3),float(j))) for d in K.DIRECTIONS}}
                 for i,j in zip(scenarios,[1,2,2,6])}
        r,_ = K.profiles(gains,scenarios)
        torch.testing.assert_close(r['A',K.DIRECTIONS[0]],torch.full((2,3),-4.,dtype=torch.float64))
        changed = copy.deepcopy(gains); changed['a']['C'] *= 100
        r2,_ = K.profiles(changed,scenarios)
        self.assertTrue(torch.equal(r['A',K.DIRECTIONS[0]],r2['A',K.DIRECTIONS[0]]))
        self.assertFalse(torch.equal(r['B',K.DIRECTIONS[0]],r2['B',K.DIRECTIONS[0]]))

    def test_targets_norm_and_reverse(self):
        x = torch.tensor([[.2,.7],[.4,.9]])
        r = torch.tensor([[.5,-.2],[.1,-.8]])
        for bg,sign in [('T',1),('C',-1)]:
            p,u = K.targets(x,r,bg)
            torch.testing.assert_close(p,x*(sign*r).exp())
            torch.testing.assert_close(p.norm(),u.norm())
            torch.testing.assert_close(u/x,torch.full_like(x,float(u.flatten()[0]/x.flatten()[0])))
        with self.assertRaises(AssertionError):
            K.targets(torch.zeros(2,2),r,'T')

    def test_zero_and_overflow_do_not_silently_clip(self):
        a = self.sample(); a['key'].zero_()
        with self.assertRaises(AssertionError): K.update(ORIGINAL,NORMALIZE,**a)
        with self.assertRaises(AssertionError): K.targets(torch.ones(2,2),torch.full((2,2),1000.),'T')

    def test_hook_coverage_and_exception_cleanup(self):
        qm = SimpleNamespace(torch_recurrent_gated_delta_rule=ORIGINAL,l2norm=NORMALIZE)
        a = self.sample()
        class Layer(torch.nn.Module):
            def forward(self): return qm.torch_recurrent_gated_delta_rule(**a)
        layers = [SimpleNamespace(linear_attn=Layer()) for _ in range(32)]
        v = SimpleNamespace(gdn_module=lambda:qm,L=SimpleNamespace(model_layers=lambda model:layers))
        hook = R.GainHook(v,object())
        with hook:
            for layer in layers: layer.linear_attn()
        hook.check()
        self.assertEqual(set(hook.records),set(K.G))
        try:
            with R.GainHook(v,object()): raise RuntimeError('synthetic failure')
        except RuntimeError: pass
        self.assertIs(qm.torch_recurrent_gated_delta_rule,ORIGINAL)
        self.assertTrue(all(not l.linear_attn._forward_pre_hooks for l in layers))

    def test_counts_and_multiscenario_not_pseudoreplication(self):
        for stage,n in [('formal',48),('preflight',2)]:
            c = K.limits(stage)
            self.assertEqual(c['trajectories'],21*n)
            self.assertEqual(c['decode_forwards'],c['t1']+c['refs']+c['n_steps']+c['c_t2'])
            self.assertEqual(c['formations'],10*n)
        sc = {'a':'A','b':'A','c':'B'}
        base = dict.fromkeys(sc,0)
        self.assertFalse(K.difference({'a':1,'b':1,'c':0},base,sc,True)['multi_scenario'])
        self.assertTrue(K.difference({'a':1,'b':0,'c':1},base,sc,True)['multi_scenario'])

    def test_cancelled_authorization_blocks_before_runtime(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'cancelled.json'; p.write_text('{"gpu_authorized":false}')
            old = R.runtime
            def forbidden(): raise AssertionError('runtime must not be reached')
            R.runtime = forbidden
            try:
                with self.assertRaises(PermissionError): R.run('preflight',0,p,Path(d)/'run')
            finally: R.runtime = old
            self.assertFalse((Path(d)/'run').exists())

    def test_frozen_file_drift_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=R.HERE) as d:
            p = Path(d)/'source'; p.write_text('before')
            manifest = Path(d)/'freeze.json'
            manifest.write_text(json.dumps({'files':{str(p.relative_to(R.REPO)):R.sha(p)},'external_sources':{}}))
            R.check_manifest(manifest)
            p.write_text('after')
            with self.assertRaises(AssertionError): R.check_manifest(manifest)

    def test_complete_answer_and_proxy_analysis_separated(self):
        scenarios,items,results = {},{},{}
        for s in range(6):
            for j in range(2):
                i = f'{s}-{j}'
                scenarios[i] = str(s)
                items[i] = {'target':'B' if j else 'A','first_listed':'A','query':str(j),'order':str(j)}
                def arm(y, margin):
                    return {'Y':y,'N':{'ids':[7,248046],'termination':'stop'},'classification':{},
                            'first':{'G':1.},'C':{'M':margin}}
                results[i] = {'C':arm(1,2.)}
                for d in K.DIRECTIONS:
                    results[i][d] = arm(0,0.)
                    for bg in ('C','T'):
                        for mode in ('P','U'):
                            results[i][f'{bg}-{mode}|{d}'] = arm(0,1.)
        out = R.analyse(results,scenarios,items,{})
        self.assertFalse(out['multi_direction_recovery'])
        self.assertTrue(out['directions'][K.DIRECTIONS[0]]['recovery']['M']['stable_positive'])
        self.assertEqual(out['seen_inputs'],12)

    def test_reference_loader_ignores_worker_logs(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); w = root/'runs/formal-r01/worker-0'; w.mkdir(parents=True)
            (w.parent/'worker-0.log').write_text('historical launch log')
            hashes,ledger = {},{}
            for j in range(48):
                i = f'LVK-H-{j}'
                p = w/(i+'.json'); p.write_text(json.dumps({'text':i}))
                hashes[p.name] = R.sha(p); ledger[i] = {}
            (w/'receipt.json').write_text(json.dumps({'status':'completed','record_hashes':hashes}))
            old = R.LVK; R.LVK = root
            try:
                refs,_ = R.references(SimpleNamespace(ledger=lambda:ledger))
            finally: R.LVK = old
            self.assertEqual(set(refs),set(ledger))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--upstream',action='store_true'); parser.add_argument('--output',required=True)
    args = parser.parse_args()
    if args.upstream:
        V,_ = R.runtime()
        ORIGINAL,NORMALIZE = V.gdn_module().torch_recurrent_gated_delta_rule,V.gdn_module().l2norm
        UPSTREAM = True
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    assert not torch.cuda.is_initialized()
    receipt = {'status':'passed' if result.wasSuccessful() else 'failed','tests_run':result.testsRun,
               'failures':len(result.failures),'errors':len(result.errors), 'model_forwards':0,
               'synthetic_kernel_calls':True,'upstream_kernel_tested':UPSTREAM,'cuda_initialized':False,
               'torch_version':torch.__version__,
               'source_hashes':{p.name:R.sha(p) for p in sorted(R.HERE.glob('*.py'))}}
    R.write(args.output,receipt,immutable=True)
    raise SystemExit(0 if result.wasSuccessful() else 1)
