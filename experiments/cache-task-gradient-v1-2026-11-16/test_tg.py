"""CPU gradient-flow, finite-endpoint, calibration and installed-kernel checks."""
import argparse
import copy
import os
from types import SimpleNamespace as NS
import unittest
os.environ['CUDA_VISIBLE_DEVICES']=''
import torch
import tg_hooks as H
import tg_analysis as A

UPSTREAM=False


class Tests(unittest.TestCase):
    def test_two_taps_keep_earlier_gradient_and_cleanup(self):
        mods={13:torch.nn.Identity(),14:torch.nn.Identity()}
        expected={13:torch.tensor([2.]),14:torch.tensor([6.])}
        hook=H.TaskControls(mods,expected)
        with hook:
            x=mods[13](torch.tensor([2.])); y=mods[14](3*x)
            gs=torch.autograd.grad((5*y).sum(),tuple(hook.controls.values()))
        hook.check()
        self.assertEqual([g.item() for g in gs],[15.,5.])
        self.assertFalse(hook.flow[13]['native_requires_grad'])
        self.assertTrue(hook.flow[14]['native_requires_grad'])
        self.assertTrue(all(not m._forward_hooks for m in mods.values()))

    def test_endpoint_recomposition_cast_and_failure_cleanup(self):
        for dtype in (torch.bfloat16,torch.float32):
            native=torch.tensor([.125,1.5,-4.],dtype=dtype)
            patch=torch.tensor([.25,1.625,-3.75],dtype=dtype)
            p=patch.double()-native.double()
            self.assertTrue(torch.equal(H.control_add(native,p),patch))
            self.assertTrue(torch.equal(H.control_add(native,torch.zeros_like(p)),native))
            m=torch.nn.Identity(); h=H.TaskControls({13:m},{13:native+1})
            with self.assertRaises(AssertionError):
                with h:m(native)
            self.assertFalse(m._forward_hooks)
            self.assertTrue(torch.equal(h.tensors[13]['native'],native))

    def test_inference_history_clone_and_saved_mutation(self):
        with torch.inference_mode():state=torch.tensor([2.])
        state=copy.deepcopy(state);self.assertFalse(state.is_inference())
        with torch.autograd.graph.allow_mutation_on_saved_tensors():
            x=torch.tensor([3.],requires_grad=True);out=x*state;state.copy_(torch.tensor([9.]))
            g=torch.autograd.grad(out.sum(),x)[0]
        self.assertEqual(g.item(),2.)
        self.assertEqual(state.item(),9.)

    def test_sign_and_cross_projection(self):
        grad={'C':{13:torch.tensor([2.,0.])},'H':{13:torch.tensor([3.,0.])}}
        p={'C':{13:torch.tensor([1.,0.])},'H':{13:torch.tensor([-2.,0.])}}
        r=A.projection(grad,p)
        self.assertEqual(r['totals']['raw'],{'C':{'C':2.,'H':4.},'H':{'C':3.,'H':6.}})
        self.assertEqual(r['totals']['equal_amplitude']['C']['C'],r['totals']['equal_amplitude']['C']['H'])
        p['H'][13].zero_();r=A.projection(grad,p)
        self.assertEqual(r['zero_direction_layers'],[13]);self.assertEqual(r['totals']['equal_amplitude']['C']['C'],0.)

    def test_calibration_is_per_receiver_and_both_backgrounds(self):
        rows=[dict(receiver='a',donor=str(i),scenario='s',prediction=1.,observed=1.) for i in range(5)]
        rows+=[dict(receiver='b',donor='x',scenario='t',prediction=0.,observed=1.)]
        r=A.summary(rows);self.assertEqual(r['mae'],.5);self.assertEqual(r['sign_agreement'],.5);self.assertFalse(r['passed'])
        for x in rows:x['prediction']=x['observed']
        self.assertTrue(A.summary(rows)['passed'])
        for x in rows:x['prediction']=0.;x['observed']=.05
        r=A.summary(rows);self.assertFalse(r['passed']);self.assertEqual(r['sign_pairs'],0)
        self.assertFalse(r['gates']['half_zero_mae'])
        for x in rows:x['prediction']=x['observed']=0.
        self.assertFalse(A.summary(rows)['passed'])

    def test_task_score_backward_and_failure_retains_logits(self):
        mods={13:torch.nn.Identity(),14:torch.nn.Identity()}
        def forward(model,tokens,position,cache):
            y=mods[14](3*mods[13](torch.tensor([2.])))
            return NS(logits=torch.stack([torch.ones_like(y),3*y,torch.zeros_like(y)],-1).reshape(1,1,3),past_key_values=cache)
        V=NS(L=NS(forward=forward))
        for fail in (False,True):
            h=H.TaskControls(mods,{13:torch.tensor([2.]),14:torch.tensor([6.])})
            calls=[]
            def backward():
                calls.append(1)
                if fail:raise RuntimeError('synthetic backward failure')
            if fail:
                with self.assertRaises(RuntimeError):H.task_forward(V,None,{},7,3,h,0,1,backward)
            else:
                _,z,g=H.task_forward(V,None,{},7,3,h,0,1,backward)
                self.assertEqual([g[l].item() for l in mods],[9.,3.])
                self.assertIs(h.gradients,g)
            self.assertEqual(calls,[1]);self.assertEqual(h.logits.tolist(),[1.,18.,0.]);self.assertEqual(h.score,17.)
            self.assertTrue(all(not m._forward_hooks for m in mods.values()))

    def test_panel_budget_is_upper_bound_not_completion_count(self):
        import tg_run as R
        V=R.W.runtime();led=V.LVKR.ledger()
        for stage,total in [('engineering',322),('formal',2556)]:
            items,tables=R.panel(stage);lim=R.limits(stage)
            actual=sum(2*(led[r]['plan']['e']-led[r]['plan']['p']+1) for r in items)
            self.assertEqual(actual,total);self.assertLess(actual,lim['formation_token_forwards'])
            self.assertLess(actual+len(items)+6*lim['pairs'],lim['model_forwards'])

    def test_original_kernel_backward_with_cache_copy(self):
        if not UPSTREAM:self.skipTest('installed frozen upstream required')
        import tg_run as R
        m=R.W.runtime().gdn_module()
        gen=torch.Generator().manual_seed(1611)
        def inputs():
            return [torch.randn(1,1,32,128,generator=gen).to(torch.bfloat16) for _ in range(3)]+[
                -torch.ones(1,1,32)*.3,torch.ones(1,1,32)*.4,torch.randn(1,32,128,128,generator=gen)*.1]
        orig=inputs()
        def run(mutate):
            q,k,v,g,b,s=[x.clone() for x in orig]
            q.requires_grad_();k.requires_grad_();v.requires_grad_()
            with torch.autograd.graph.allow_mutation_on_saved_tensors():
                o,new=m.torch_recurrent_gated_delta_rule(q,k,v,g=g,beta=b,initial_state=s,
                    output_final_state=True,use_qk_l2norm_in_kernel=True)
                if mutate:s.copy_(new)
                gs=torch.autograd.grad(o.float().sum(),(q,k,v))
            return o.detach(),[x.detach() for x in gs]
        a,b=run(False),run(True)
        self.assertTrue(torch.equal(a[0],b[0]))
        self.assertTrue(all(torch.equal(x,y) and torch.isfinite(y).all() for x,y in zip(a[1],b[1])))
        self.assertFalse(torch.cuda.is_initialized())


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--upstream',action='store_true');a=p.parse_args()
    UPSTREAM=a.upstream
    torch.set_num_threads(1)
    unittest.main(argv=['test_tg'])
