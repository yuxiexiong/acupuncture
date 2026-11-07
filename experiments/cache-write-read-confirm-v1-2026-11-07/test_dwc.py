"""CPU acceptance of material assignment, estimator, stopping and numerical operators."""
import copy
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import dwc_run as R
import dwc_core as K
import dwc_analysis as A
import materials as M
from test_sru import ReadUse
from test_lvk import Update

class Design(unittest.TestCase):
    def test_matrix_partition_and_budget(self):
        data=M.load()
        self.assertEqual(len(data['items']),1458)
        for stage,want in [('formal',(81648,3024,21168,18144)),('preflight',(7260,414,2094,1860))]:
            lim,_=R.limits(stage)
            # The preflight totals include old six receivers; exact values are calculated independently below.
            if stage=='formal':self.assertEqual(tuple(lim[k] for k in ('trajectories','formations','t1','c_t2')),want)
            self.assertEqual(lim['trajectories'],want[0])
        one=R.plan('formal',0,1);two=R.plan('formal',0,2)+R.plan('formal',1,2)
        self.assertEqual({u['key'] for u in one},{u['key'] for u in two});self.assertEqual(len(two),96)
        for w in range(2):
            units=R.plan('formal',w,2)
            for f in M.FAMILIES:
                self.assertEqual(sum(u['base_id']==f for u in units),8)
                self.assertEqual(sum(u['base_id']==f and u['diagnostic'] for u in units),2)
        self.assertEqual(R.GPU_CAP_S['formal']+2*R.GPU_CAP_S['preflight'],19*3600)
        self.assertEqual(M.sha(HERE/'data/materials-r01.json'),R.exp.read(HERE/'data/token-ledger-r01.json')['materials_sha256'])

    def test_balanced_text_predictions_and_zero_null(self):
        data=M.load();items=data['items']
        for r,ds in data['primary_donors'].items():
            for fixed in (0,1,2,'stop','other'):
                self.assertEqual(K.S.d_transfer(ds,{d['id']:fixed for d in ds}),0)
            self.assertEqual(K.S.d_transfer(ds,{d['id']:d['row'] for d in ds}),1)
            rr=items[r]
            for d in ds:
                dd=items[d['id']]
                self.assertEqual(d['row'],dd['listed_codes'].index(dd['target']))
                self.assertEqual(d['key'],rr['listed_codes'].index(dd['target']))
            dx=data['diagnostic_donors'][r]
            for d in dx:
                dd=items[d['id']];pred=d['predicted_rows']
                self.assertEqual(pred,[dd['listed_codes'].index(dd['target']),rr['order'].index(dd['query']),rr['listed_codes'].index(dd['target'])])
                self.assertEqual(len(set(pred)),3)
            for fixed in range(3):
                if dx:self.assertEqual([sum(d['predicted_rows'][k]==fixed for d in dx) for k in range(3)],[2,2,2])

    def test_natural_unreachable_is_counted_no_hook(self):
        for hook in (None,object()):
            c={k:0 for k in R.COUNT_KEYS}
            with patch.object(R.OLD,'natural',side_effect=AssertionError('must not forward')):
                nr,z=R.natural(None,None,R.STOP[0],61,c,hook)
            self.assertEqual(c['trajectories'],1);self.assertEqual(c['n_steps'],0)
            self.assertFalse(nr['reached_t2']);self.assertEqual(nr['unreachable_noop'],hook is not None);self.assertIsNone(z)

    def test_margin_and_scientific_failure(self):
        b=lambda l,h:dict(lo=l,hi=h)
        yes,positive,zero,neg=b(.4,.8),b(.1,.4),b(0,0),b(-.5,-.1)
        self.assertEqual(K.level(b(.25,.25)),'indeterminate')
        self.assertEqual(K.level(b(.25,.6)),'holds')
        self.assertEqual(K.level(b(.01,.24)),'below')
        self.assertEqual(K.decision(yes,yes,yes,yes,{'all':True}),'independent_magnitude_confirmation')
        self.assertEqual(K.decision(yes,positive,yes,yes,{'all':True}),'positive_relation_magnitude_unconfirmed')
        self.assertEqual(K.decision(zero,yes,yes,yes,{'all':True}),'write_endpoint_below_margin')
        self.assertEqual(K.decision(yes,neg,yes,yes,{'all':True}),'opposite_direction_evidence')
        self.assertEqual(K.decision(yes,yes,yes,yes,{'all':False}),'premise_or_delivery_indeterminate')

    def test_paired_stratified_bootstrap(self):
        scenes={f'{f}-{j}':f for f in M.FAMILIES for j in range(16)};boot=K.Bootstrap(scenes,80)
        vals={s:i/100 for i,s in enumerate(sorted(scenes))}
        a=boot.interval(vals);b=K.Bootstrap(scenes,80).interval(vals)
        self.assertEqual(a,b);self.assertEqual(a['scenes'],96)
        zero=boot.interval({s:vals[s]-vals[s] for s in scenes})
        self.assertEqual((zero['mean'],zero['lo'],zero['hi']),(0,0,0))
        for g,idx in zip(boot.groups,boot.indices):self.assertTrue(set(idx.flat)<=set(g))
        with self.assertRaises(AssertionError):boot.interval({})

    def test_full_consumer_missing_truncation_and_directions(self):
        data=M.load();records={}
        for u in data['units']:
            if u['stage']!='preflight':continue
            for r in u['item_ids']:
                it=data['items'][r];selfrow=it['listed_codes'].index(it['target'])
                def ans(row):return dict(x=5,N=dict(ids=[5,6,2],text=it['listed_codes'][row]+'<|im_end|>',termination='stop',reached_t2=True))
                rec=dict(text=r,scenario=u['key'],family=u['base_id'],item=it,self_row=selfrow,once={'C0':ans(selfrow)})
                if r not in u['receivers']:
                    rec['diagnostic_donor']=True;records[r]=rec;continue
                ds=data['primary_donors'][r];dx=data['diagnostic_donors'][r]
                rec.update(donors=ds,diagnostic_donors=dx,directions={})
                for direction in K.DIRS:
                    arms={'L00':ans(selfrow),'L11o':ans(selfrow)}
                    for donor in ds+dx:
                        row=donor.get('row',donor.get('predicted_rows',[None])[0])
                        for a in K.DONOR_ARMS:
                            if donor in dx and a.endswith('E'):continue
                            follow=a=='L11d' or (a=='gainD' and direction==K.MAIN)
                            arms[a+'|'+donor['id']]=ans(row if follow else selfrow)
                    rec['directions'][direction]=arms
                records[r]=rec
        out=A.analyse(records,'preflight',n_boot=40)
        self.assertEqual(out['directions'][K.MAIN]['uses']['D']['decision'],'independent_magnitude_confirmation')
        self.assertNotEqual(out['directions'][K.SECOND]['uses']['D']['decision'],'independent_magnitude_confirmation')
        self.assertEqual(out['directions'][K.MAIN]['uses']['D']['R_pairs'],216)
        rec=next(x for x in records.values() if 'directions' in x)
        nr={'text':rec['item']['target'],'termination':'budget','reached_t2':True}
        self.assertNotIn(A.A.row_out(nr,rec['item']),(0,1,2))
        rec['directions'][K.MAIN].pop('gainD|'+rec['donors'][0]['id'])
        with self.assertRaises(KeyError):A.analyse(records,'preflight',n_boot=10)
        records.pop(next(iter(records)))
        with self.assertRaises(AssertionError):A.analyse(records,'preflight',n_boot=10)

if __name__=='__main__':
    assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
    res=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    if len(sys.argv)>1:
        own=list(HERE.glob('*.py'))+list((HERE/'readiness').glob('*.py'))
        M.write(sys.argv[1],dict(status='passed' if res.wasSuccessful() else 'failed',tests_run=res.testsRun,
                failures=len(res.failures),errors=len(res.errors),source_hashes={str(p.relative_to(R.REPO)):M.sha(p) for p in own}))
    sys.exit(0 if res.wasSuccessful() else 1)
