"""Changed storage, restrictions and evidence plumbing; synthetic CPU only."""
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
from weights import save_sparse, load_sparse, quantize, check_targeted_edit, Candidates
from test_offline import OfflineTests, NAMES


class StorageTests(unittest.TestCase):
    def test_absolute_values_preserve_bits_and_storage(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'patch.npz'
            base = np.arange(100000,dtype=np.float32).reshape(100,1000)/7
            value = base.copy(); value[0,0] = -0.; value[99,999] = np.float32(1e-30)
            meta = save_sparse(p,base,value)
            restored = load_sparse(p,base)
            self.assertEqual(restored.tobytes(),value.tobytes())
            self.assertEqual(meta['stored_coordinates'],2)
            self.assertLess(p.stat().st_size,2000)
            wrong = base.copy(); wrong[1,1] = 0
            self.assertNotEqual(load_sparse(p,wrong).tobytes(),value.tobytes())

    def test_scalar_and_forbidden_edits_rejected_direction_allowed(self):
        base = quantize(np.random.default_rng(4).normal(size=(20,30)),'BF16')
        for name in ['model.language_model.embed_tokens.weight','lm_head.weight','model.language_model.norm.weight']:
            with self.assertRaises(ValueError):check_targeted_edit(name,base,base+1,'BF16')
        for scale in [0.,-.5,.9,1.075,2.]:
            with self.assertRaises(ValueError):
                check_targeted_edit('mlp.down_proj.weight',base,quantize(base*scale,'BF16'),'BF16')
        edited=base.copy(); edited[:,0]-=np.linspace(.1,.5,20)
        check_targeted_edit('mlp.down_proj.weight',base,edited,'BF16')


class EvidenceTests(OfflineTests):
    # Inherit the existing fixtures but run just these methods via load_tests.
    def test_targeted_candidate_requires_real_capture_and_prediction(self):
        s=self.service(); s.contract['targeted']=True
        x=self.source.load(NAMES[0]); x[0,0]=1
        from kernel import PythonNamespace
        ns=PythonNamespace(self.source,self.candidates,s.root/'work',s.root/'public/public.json',self.evidence.root,s.root/'artifacts')
        ns.save_edit(NAMES[0],x)
        rejected=self.action(s,'missing',op='commit',parent=self.candidates.base_id,rationale='test')
        self.assertTrue(rejected['failed'])
        measured=self.action(s,'measured',op='measure',ids=['g0:total','g0:subset'])
        self.assertFalse(measured['failed'])
        ev=dict(failure_behavior='wrong subset',component_hypothesis='synthetic target',expected_change='subset 2 to 1',dose='one',control_plan='other component',contrast_ids=['g0:total','g0:subset'],measurement_actions=['measured'],role='targeted')
        out=self.action(s,'commit',op='commit',parent=self.candidates.base_id,rationale='fixture',evidence=ev)
        self.assertFalse(out['failed'],out)
        self.assertTrue((s.root/'artifacts'/(out['value']['id']+'-evidence.json')).exists())

    def test_sparse_candidate_reload_and_proposal_archive(self):
        s=self.service()
        out=s.dispatch(dict(id='proposal',kind='python',code='x=load(NAMES[0]);x[0,0]=1;save_edit(NAMES[0],x)'))
        self.assertFalse(out['failed'],out)
        entry=next(iter(json.loads((s.root/'actions/proposal/proposal/manifest.json').read_text()).values()))
        self.assertEqual(entry['encoding'],'absolute-f32-sparse-v1')
        out=self.action(s,'save',op='commit',parent=self.candidates.base_id,rationale='fixture')
        ident=out['value']['id']
        fresh=Candidates(self.source,self.candidates.root,6,2)
        self.assertEqual(fresh.load(ident,NAMES[0]).tobytes(),self.candidates.load(ident,NAMES[0]).tobytes())


def load_tests(loader, tests, pattern):
    suite=loader.loadTestsFromTestCase(StorageTests)
    for name in ['test_targeted_candidate_requires_real_capture_and_prediction','test_sparse_candidate_reload_and_proposal_archive']:
        suite.addTest(EvidenceTests(name))
    return suite
