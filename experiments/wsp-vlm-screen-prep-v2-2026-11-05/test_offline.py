"""CPU acceptance on known synthetic answers, never model performance evidence."""
import copy
import json
import unittest
import tempfile
import subprocess
import sys
from pathlib import Path
from collections import Counter

from prepare_b import build
from statistics_c import (HERE, classify, holm, paired, report, score, wilson_lower)
from prepare_c import requests, selected_groups


def fixture(mode='perfect'):
    gold=[g for _,g in requests(selected_groups())]
    ids={s:sorted({g['group_id'] for g in gold if g['split']==s}) for s in ('D','H')}
    bad=set(ids['D'][:24]+ids['H'][:32])
    predictions=[]
    for g in gold:
        text=g['answer']
        if mode=='gap' and g['group_id'] in bad and g['condition']=='counterfact_usual' and g['arm']=='B0':
            text=g['names'][1]
        predictions.append(dict(request_id=g['request_id'],text=text,truncated=False))
    return predictions,gold


class OfflineTests(unittest.TestCase):
    def test_b_freeze(self):
        audit, rows=build()
        self.assertEqual(Counter(r['status'] for r in audit),
                         dict(pass_ai_visual=146,ambiguous=14,exclude_label=3,exclude_pairing=1))
        self.assertEqual(len(rows),146)
        self.assertEqual(len({r['source_id'] for r in rows}),146)
        self.assertEqual(Counter(r['split'] for r in rows),dict(D=58,H=88))
        self.assertEqual(Counter(r['stratum'] for r in rows),dict(distance=73,position=73))
        stored=[json.loads(x) for x in (HERE/'audit/B_selected_groups.jsonl').read_text().splitlines()]
        self.assertEqual(rows,stored)
        self.assertTrue(all(r['subset_answer']<=r['total_answer'] for r in rows))

    def test_development_cli_does_not_require_holdout(self):
        predictions,gold=fixture('gap')
        dids={g['request_id'] for g in gold if g['split']=='D'}
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp)
            for name,rows in [('gold',gold),('predictions',[p for p in predictions if p['request_id'] in dids])]:
                (tmp/name).write_text(''.join(json.dumps(r)+'\n' for r in rows))
            subprocess.run([sys.executable,str(HERE/'statistics_c.py'),'--gold',str(tmp/'gold'),
                            '--predictions',str(tmp/'predictions'),'--out',str(tmp/'out')],check=True)
            result=json.loads((tmp/'out').read_text())
            self.assertNotIn('H',result)
            self.assertEqual(result['D']['cells']['B0:T0:Oprimary']['n'],64)
            self.assertTrue(result['engineering_pass'])

    def test_exact_p_and_direction(self):
        x=[1,1,1,1,0,0]; y=[0,0,0,1,1,0]
        p=paired(x,y)
        self.assertEqual((p['n'],p['b'],p['c']),(6,3,1))
        self.assertEqual(p['p_one_sided'],5/16)
        self.assertAlmostEqual(p['delta'],1/3)
        self.assertEqual(p,paired(x,y))
        self.assertAlmostEqual(paired(y,x)['delta'],-1/3)
        self.assertEqual(paired([1,0],[1,0])['p_one_sided'],1)
        self.assertEqual(paired([1]*8,[0]*8)['ci95'],[1,1])
        with self.assertRaises(ValueError): paired([2],[0])

    def test_holm_and_wilson(self):
        self.assertEqual(holm({'C':.01}),dict(C=.03,A=1.,B=1.))
        self.assertEqual(holm({'A':.01,'B':.03,'C':.04}),dict(A=.03,B=.06,C=.06))
        with self.assertRaises(ValueError): holm({'C':float('nan')})
        self.assertGreater(wilson_lower(96,96),.9)
        self.assertAlmostEqual(wilson_lower(0,96),0)

    def test_missing_duplicate_unknown_and_infrastructure(self):
        p,g=fixture()
        for broken in (p[:-1],p+[p[0]],p+[dict(p[0],request_id='unknown')]):
            with self.assertRaises(ValueError): score(broken,g)
        for change in (dict(truncated=None),dict(status='error'),dict(text=None)):
            broken=copy.deepcopy(p); broken[0].update(change)
            with self.assertRaises(ValueError): score(broken,g)
        p[0]['truncated']=True
        self.assertFalse(score(p,g)[0]['correct'])

    def test_perfect_fixture_no_gap(self):
        p,g=fixture(); r=report(p,g,resamples=100)
        self.assertEqual(r['decision'],'not_priority_on_current_distribution')
        h=r['splits']['H']['cells']['B0:T0:Oprimary']
        self.assertEqual((h['n'],h['five_way_joint']),(96,1))
        self.assertEqual(r['engineering']['B0']['n'],3200)

    def test_gap_fixture_and_gates(self):
        p,g=fixture('gap'); r=report(p,g,resamples=100)
        d,h=r['splits']['D'],r['splits']['H']
        primary=h['cells']['B0:T0:Oprimary']
        self.assertEqual((primary['n'],primary['b'],primary['c'],primary['error_pattern_groups']),(96,32,0,32))
        self.assertAlmostEqual(primary['five_way_joint'],2/3)
        self.assertEqual(r['decision'],'behavior_gap_priority_not_WSP_repairability')
        self.assertEqual(h['B1_changes']['T0:O0']['counterfact_usual'],dict(n=96,repaired=32,worsened=0))
        self.assertEqual(classify(d,h,r['holm']['C'],False),'measurement_protocol_failed')
        h['cells']['B0:T1:O1']['delta']=0
        self.assertEqual(classify(d,h,r['holm']['C'],True),'unresolved')

    def test_registered_order_and_prompt_harm(self):
        p,g=fixture()
        # Flip only the H group's registered order. A fixed-order-zero implementation fails this.
        target=next(x for x in g if x['split']=='H' and x['primary'] and x['order']==1 and x['condition']=='counterfact_usual')
        index=next(i for i,x in enumerate(g) if x==target)
        p[index]['text']=target['names'][1]
        strong=next(i for i,x in enumerate(g) if x['group_id']==target['group_id'] and x['arm']=='B1' and
                    x['template']=='T1' and x['order']==0 and x['condition']=='original_usual')
        p[strong]['text']='invalid'
        r=report(p,g,resamples=100)
        self.assertEqual(r['splits']['H']['cells']['B0:T0:Oprimary']['b'],1)
        self.assertEqual(r['splits']['H']['B1_changes']['T1:O0']['original_usual']['worsened'],1)

    def test_format_failure_is_engineering(self):
        p,g=fixture('gap')
        for i,x in enumerate(g):
            if x['arm']=='B0' and x['condition']=='no_image_usual': p[i]['text']='invalid'
        r=report(p,g,resamples=100)
        self.assertFalse(r['engineering_pass'])
        self.assertEqual(r['decision'],'measurement_protocol_failed')


if __name__=='__main__': unittest.main()
