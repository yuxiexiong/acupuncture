import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import runner
from prepare_inputs import HERE,all_pairs,b_groups,read_jsonl
from statistics_b import parse_integer,score,report


def fixture(kind='perfect'):
    gold=[g for i,g in all_pairs('B')]
    groups=b_groups()
    bad=set()
    for split,n in [('D',20),('H',24)]:
        ids=sorted(g['group_id'] for g in groups if g['split']==split and g['total_answer']!=g['subset_answer'])
        bad.update(ids[:n])
    preds=[]
    for g in gold:
        answer=g['answer']
        if kind=='gap' and g['group_id'] in bad and g['arm']=='B0' and g['condition']=='subset':answer=g['total_answer']
        preds.append(dict(request_id=g['request_id'],text=str(answer),truncated=False))
    return preds,gold


class ReadyTests(unittest.TestCase):
    def test_rewrite_and_request_coverage(self):
        pairs=all_pairs('B');self.assertEqual(len(pairs),1168)
        self.assertEqual(len({i['request_id'] for i,g in pairs}),1168)
        self.assertEqual(sum(g['split']=='D' for i,g in pairs),464)
        r=read_jsonl(HERE/'audit/B_rewrites.jsonl')
        self.assertEqual(len(r),292)
        self.assertTrue(all(x['T0']!=x['T1'] and x['review'].startswith('pass') for x in r))
        for i,g in pairs:
            self.assertEqual(set(i),{'request_id','text','image'})
            self.assertEqual(set(runner.messages(i)[0]),{'role','content'})

    def test_semantic_edge_cases_frozen(self):
        rs={(r['group_id'],r['condition']):r['T1'] for r in read_jsonl(HERE/'audit/B_rewrites.jsonl')}
        self.assertIn('closer to the giraffe than the building is',rs['B-573506','subset'])
        self.assertIn('railing that is farther',rs['B-1385','subset'])
        self.assertIn('rightmost sheep',rs['B-272427','subset'])
        self.assertIn('top-down view, along the vertical axis',rs['B-83203','subset'])
        self.assertIn('food preparation area',rs['B-216394','total'])

    def test_integer_parser(self):
        for text,n in [('0',0),(' 12\n',12),('003',3)]:self.assertEqual(parse_integer(text),n)
        for text in ['-1','1.0','1 or 2','two','2 objects','2.','Answer: 2','2+1','拒答','', '２']:
            self.assertIsNone(parse_integer(text))

    def test_reject_corrupt_predictions(self):
        p,g=fixture()
        for broken in [p[:-1],p+[p[0]],[dict(p[0],request_id='extra')]+p[1:]]:
            with self.assertRaises(ValueError):score(broken,g)
        for change in [dict(status='error'),dict(truncated=0),dict(text=3)]:
            x=copy.deepcopy(p);x[0].update(change)
            with self.assertRaises(ValueError):score(x,g)
        p[0]['truncated']=True;self.assertFalse(score(p,g)[0]['correct'])

    def test_gap_and_no_gap(self):
        p,g=fixture('gap');r=report(p,g,resamples=100)
        h=r['splits']['H']['cells']['B0:T0']
        self.assertEqual((h['n'],h['b'],h['c'],h['error_pattern_groups']),(88,24,0,24))
        self.assertEqual(r['decision'],'behavior_gap_priority_not_WSP_repairability')
        self.assertEqual(r['splits']['H']['B1_changes']['T0']['subset']['repaired'],24)
        self.assertEqual(sum(x['n'] for x in r['splits']['H']['strata']['B0:T0']['stratum'].values()),88)
        p,g=fixture();self.assertEqual(report(p,g,resamples=100)['decision'],'not_priority_on_current_distribution')

    def test_same_answer_not_ignored_condition_evidence(self):
        p,g=fixture()
        r=report(p,g,resamples=100)
        self.assertEqual(sum(r['splits'][s]['cells']['B0:T0']['error_pattern_eligible'] for s in ('D','H')),104)
        self.assertEqual(r['splits']['H']['cells']['B0:T0']['error_pattern_groups'],0)

    def test_robustness_and_format_gates(self):
        p,g=fixture('gap')
        for i,x in enumerate(g):
            if x['template']=='T1':p[i]['text']=str(x['answer'])
        self.assertEqual(report(p,g,resamples=100)['decision'],'unresolved')
        for i,x in enumerate(g):
            if x['arm']=='B0' and x['condition']=='total':p[i]['text']='invalid'
        self.assertEqual(report(p,g,resamples=100)['decision'],'measurement_protocol_failed')

    def test_d_only(self):
        p,g=fixture('gap');ds=[x for x in g if x['split']=='D'];ids={x['request_id'] for x in ds}
        r=report([x for x in p if x['request_id'] in ids],ds,resamples=100)
        self.assertEqual(set(r['splits']),{'D'})
        self.assertNotIn('holm',r)

    def test_eos_length_boundary(self):
        self.assertFalse(runner.check_generation([7]*127+[2],[2,3])['truncated'])
        self.assertTrue(runner.check_generation([7]*128,[2,3])['truncated'])
        self.assertFalse(runner.check_generation([2],2)['truncated'])
        with self.assertRaises(RuntimeError):runner.check_generation([7],2)

    def test_drain_failure_preserves_raw_and_does_not_retry(self):
        requests=runner.queue('B','D')[:3];calls=[]
        def infer(r,seconds):
            calls.append(r['request_id'])
            if len(calls)==2:raise RuntimeError('synthetic backend failure')
            return dict(text='not a number',truncated=False,backend='synthetic')
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'output'
            with self.assertRaises(RuntimeError):runner.drain(requests,infer,path,lambda:30)
            records=read_jsonl(path)
            self.assertEqual(len(calls),2)
            self.assertEqual([r['status'] for r in records],['ok','error'])
            self.assertEqual(records[0]['text'],'not a number')
            with self.assertRaises(FileExistsError):runner.drain(requests,infer,path,lambda:30)

    def test_default_cli_is_offline(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'dry.json'
            subprocess.run([sys.executable,str(HERE/'runner.py'),'--task','B','--stage','D','--out',str(out)],check=True)
            r=json.loads(out.read_text());self.assertEqual(r['requests'],464)
            self.assertEqual(r['model_loads'],0)
            self.assertEqual(r['status'],'OFFLINE_ONLY')

    def test_protocol_gate_precedes_loading(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(runner,'load_backend',side_effect=AssertionError('must not load')) as load:
                with self.assertRaises(RuntimeError):runner.run_execute(runner.queue('B','H'),'B','H',Path(tmp))
                load.assert_not_called()


if __name__=='__main__':unittest.main()
