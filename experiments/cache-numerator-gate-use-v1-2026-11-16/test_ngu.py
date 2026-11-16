"""CPU regression tests: endpoint semantics, dynamic hooks, scoring and budgets."""
import copy
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
os.environ['CUDA_VISIBLE_DEVICES']=''
import ngu_hooks as H
import ngu_run as N
import ngu_analysis as A
import torch
import test_rcs_hooks as T
import test_rcs_analysis as S

class Tests(unittest.TestCase):
    def test_finite_endpoints_and_no_whole_gate(self):
        gen=torch.Generator().manual_seed(1611)
        for dtype in (torch.float32,torch.bfloat16):
            x0,x1,z,ref=[torch.randn(32,128,generator=gen).to(dtype) for _ in range(4)]
            w=torch.linspace(.7,1.2,128).to(dtype)
            out,cur,delta,inv=H.gate_patch(x0,x1,z,ref,w,1e-6)
            f=lambda x,g: (w*(x.float()*inv).to(dtype)*torch.nn.functional.silu(g.float())).to(dtype)
            expected=(f(x1,z).double()+f(x1,ref).double()-f(x0,ref).double()-f(x1,z).double()+f(x0,z).double()).to(dtype)
            self.assertTrue(torch.equal(out,expected))
            self.assertFalse(torch.equal(out,f(x1,ref)))
            self.assertTrue(torch.equal(H.gate_patch(x0,x1,z,z,w,1e-6)[0],f(x1,z)))
            self.assertTrue(torch.equal(H.gate_patch(x1,x1,z,ref,w,1e-6)[0],f(x1,z)))
            self.assertEqual(cur.dtype,torch.float64)

    def test_dynamic_hook_cache_and_cleanup(self):
        old_threads=torch.get_num_threads();torch.set_num_threads(1)
        try:
            world=T.World(torch.bfloat16,heads=32,dim=128)
            package={l:torch.full((1,32,128,128),.001,dtype=torch.float64) for l in H.H.K.G}
            cache=copy.deepcopy(world.initial);wh=world.write_hook(package);world.run(cache,wh)
            rh=world.read_hook(wh.states,'11');expected=world.run(copy.deepcopy(cache),rh)
            refs={l:t['z'].clone() for l,t in rh.tensors.items()}
            with patch.object(T.V.LVKR,'gdn_module',return_value=world.qm):own=H.GateUseHook(T.V,object(),wh.states,refs)
            observed=world.run(copy.deepcopy(cache),own)
            self.assertTrue(all(torch.equal(a,b) for a,b in zip(expected,observed)))
            refs={l:z+.5 for l,z in refs.items()}
            with patch.object(T.V.LVKR,'gdn_module',return_value=world.qm):swap=H.GateUseHook(T.V,object(),wh.states,refs)
            altered=world.run(copy.deepcopy(cache),swap)
            self.assertTrue(any(not torch.equal(a,b) for a,b in zip(expected,altered)))
            self.assertEqual(swap.shadow_calls,14)
            self.assertTrue(all(r['cache_S2_committed'] and r['zero_increment_exact'] and r['same_gate_exact'] for r in swap.records.values()))
            self.assertTrue(all(len(t)==9 for t in swap.tensors.values()))
            world.assert_clean(self)
            with patch.object(T.V.LVKR,'gdn_module',return_value=world.qm):bad=H.GateUseHook(T.V,object(),wh.states,refs)
            with self.assertRaisesRegex(RuntimeError,'injected failure'):world.run(copy.deepcopy(cache),bad,stop_at=16)
            world.assert_clean(self)
        finally:torch.set_num_threads(old_threads)

    def synthetic(self):
        rec,it,tb=S.world()
        for r in rec:
            for d in tb[r]:
                p=rec[r]['pairs'][d['id']];p['CX']=copy.deepcopy(p['C11']);p['HX']=copy.deepcopy(p['H11'])
                if d['type'] in ('AL','BD'):
                    p['CX']['t2']['candidate_logits'][d['row']]+=2
                    p['HX']['t2']['candidate_logits'][d['row']]-=3
        return rec,it,tb

    def test_scores_signs_and_shared_off(self):
        out=A.analyse(*self.synthetic(),n_boot=40)
        f=out['continuous']['family']['intervals']
        self.assertEqual(f['G_H']['mean'],3);self.assertEqual(f['G_C']['mean'],2)
        self.assertTrue(out['continuous_both_at_1'])
        self.assertEqual(out['D_tr']['contrasts']['G_C'],0)
        self.assertTrue(out['delivery']['passed'])
        self.assertEqual(len(f),2)
        self.assertTrue(all(abs(p['delta_native']-p['G_H']-p['G_C']-p['delta_both_exchanged'])<1e-9 for p in out['continuous']['pairs']))

    def test_invalid_answers_and_prefix_not_filtered(self):
        rec,it,tb=self.synthetic();r=next(iter(rec));d=tb[r][0]['id']
        rec[r]['pairs'][d]['CX']=S.trajectory(it[r],text='nonsense<|im_end|>')
        out=A.analyse(rec,it,tb,n_boot=40)
        bounds=out['D_tr']['invalid_fill_bounds']['G_C'];self.assertLess(bounds['lo'],bounds['hi'])
        rec[r]['pairs'][d]['CX']['t2']['prefix_ids']=[999]
        with self.assertRaises(ValueError):A.analyse(rec,it,tb,n_boot=40)
        self.assertEqual(A.label({'lo':-.1,'hi':1.2}),'indeterminate')
        self.assertEqual(A.label({'lo':.1,'hi':.8}),'positive_direction_magnitude_not_established')

    def test_authorization_and_failed_attempt_accounting(self):
        import test_rcs_run as B
        with patch.object(B, 'R', N):
            for name in ('test_no_default_authorization', 'test_killed_worker_is_charged_from_supervisor',
                         'test_authorization_is_single_output_and_cannot_hide_prior_attempt'):
                getattr(B.Tests(name), name)()
        with self.assertRaises(AssertionError):N.project_seconds({}, N.W.runtime())

    def test_counts_no_extra_baselines(self):
        f,e=N.limits('formal'),N.limits('engineering')
        self.assertEqual((f['trajectories'],e['trajectories']),(2088,252))
        self.assertEqual(f['t1']+2*e['t1'],864)
        self.assertEqual(f['t2_shadow']+2*e['t2_shadow'],36288)
        self.assertEqual(N.TOTAL_CAP,10800);self.assertEqual(N.STORAGE,16*2**30)
        rc={'counts':{'trajectories':2089},'arm_counts':{}}
        with self.assertRaises(AssertionError):N.check_counts(rc,'formal')

if __name__=='__main__':unittest.main()
