"""CPU-only checks of actual scheduling, +1 records, and authorization boundaries."""
import copy
from collections import Counter, defaultdict
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import survey
import launch_survey


class SurveyTests(unittest.TestCase):
    def test_full_design_and_exact_coverage(self):
        c,q,s = survey.load_design()
        jobs = [survey.make_specs('survey',survey.MODEL,i) for i in (0,1)]
        self.assertEqual(list(map(len,jobs)),[1288,1280])
        seen = set(); groups = defaultdict(set)
        for shard, work in enumerate(jobs):
            for condition,p,question,dose in work:
                key = (condition,question['id']); self.assertNotIn(key,seen); seen.add(key)
                if p:
                    groups[(p['id'],dose)].add(question['id'])
                    self.assertEqual(s[survey.MODEL].index(p)%2,shard)
        self.assertEqual(len(seen),2568); self.assertEqual(len(groups),320)
        self.assertTrue(all(len(v)==8 for v in groups.values()))
        for layer in range(32):
            for shard in (0,1):
                self.assertEqual(len({p['id'] for _,p,_,_ in jobs[shard] if p and p['layer']==layer}),5)

    def test_preflight_plus_one_anchors(self):
        for shard in (0,1):
            jobs = survey.make_specs('preflight',survey.MODEL,shard)
            self.assertEqual(len(jobs),17)
            self.assertEqual(Counter(survey.kind_for(x[0]) for x in jobs),dict(baseline=8,zero=3,restored=3,dose=3))
            self.assertEqual({p['layer'] for _,p,_,_ in jobs if p},{0,16,31})
            for p in {p['id'] for _,p,_,_ in jobs if p}:
                self.assertEqual({d for _,a,_,d in jobs if a and a['id']==p and d not in (None,0)},set(survey.DOSES))

    def make_row(self):
        job = survey.make_specs('survey',survey.MODEL,0)[8]
        condition,p,q,dose = job
        cal = dict(context_sha256=hashlib.sha256(b'context').hexdigest(),input_token_sha256='input',input_token_count=5,residual_scales={str(p['layer']):2.})
        tokens = [7,128009]
        out = dict(token_ids=tokens,token_sha256=survey.token_hash(tokens),generated_token_count=2,
            batch_size=1,max_new_tokens=128,returned_padding_count=0,input_token_sha256='input',end_reason='eos_token')
        requested = dose*2/3
        hook = dict(layer=p['layer'],channel=p['channel'],dose=dose,column_norm=3.,clean_residual_scale=2.,
            requested_offset=requested,bf16_offset=survey.bf16_round(requested),calls=2,positions=6,prefill_target_values_checked=True)
        row = dict(status='completed',model_id=survey.MODEL,condition_id=condition,kind='dose',point_id=p['id'],layer=p['layer'],channel=p['channel'],dose=dose,
            question_id=q['id'],prompt=q['prompt'],context='context',calibration=cal,output=out,intervention=hook)
        return row,job,{q['id']:cal}

    def test_record_rejects_sign_eos_padding_and_bad_count(self):
        row,job,cals = self.make_row(); survey.check_record(row,job,cals)
        for key,value in [('dose',.75),('point_id','wrong')]:
            bad=copy.deepcopy(row);bad[key]=value
            with self.assertRaises(AssertionError):survey.check_record(bad,job,cals)
        for key,value in [('token_sha256','bad'),('returned_padding_count',1),('generated_token_count',3),('end_reason','length_limit')]:
            bad=copy.deepcopy(row);bad['output'][key]=value
            with self.assertRaises(AssertionError):survey.check_record(bad,job,cals)
        bad=copy.deepcopy(row);bad['intervention']['requested_offset']*=-1
        with self.assertRaises(AssertionError):survey.check_record(bad,job,cals)
        bad=copy.deepcopy(row);bad['output']['token_ids']=[248046];bad['output']['token_sha256']=survey.token_hash([248046]);bad['output']['generated_token_count']=1
        with self.assertRaises(AssertionError):survey.check_record(bad,job,cals)

    def test_only_plus_one_is_a_scientific_condition(self):
        self.assertEqual(survey.DOSES,(1.,))
        self.assertEqual(survey.COMPARISON_DOSES,(0.,1.))
        self.assertEqual(survey.dose_id(1.),'D1p0')
        for dose in (-1.,-.5,-.0625,0.,.0625,.5,.75):
            with self.assertRaises(AssertionError):survey.dose_id(dose)

    def test_permission_gate_before_model_loading(self):
        with self.assertRaises(AssertionError):survey.check_authorization('/not/a/file','survey',survey.MODEL,0,False)
        auth=dict(experiment=survey.HERE.name,freeze_sha256='f',status='authorized',purpose='preflight',models=[survey.MODEL],gpus=[0,1],user_instruction='authorized',recorded_utc='time',maximum_workers=2,maximum_new_tokens_per_record=128,maximum_generations=34,maximum_generated_tokens=4352,formal_launch_confirmed=False)
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'auth.json';survey.io.write(p,auth)
            with patch.object(survey,'check_freeze',return_value='f'):
                survey.check_authorization(p,'preflight',survey.MODEL,0,True)
                with self.assertRaises(AssertionError):survey.check_authorization(p,'survey',survey.MODEL,0,True)

    def test_formal_requires_completed_preflight_controller_and_zero_exits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);parent=root/'preflight';names=[f'{survey.MODEL}-shard-{i}' for i in (0,1)]
            state=dict(status='completed',mode='preflight',worker_exit_codes={k:0 for k in names})
            survey.io.write(parent/'controller.json',state)
            for key in names:(parent/f'{key}.exit').write_text('0\n')
            auth=dict(experiment=survey.HERE.name,freeze_sha256='f',status='authorized',purpose='survey',models=[survey.MODEL],gpus=[0,1],user_instruction='authorized',recorded_utc='time',maximum_workers=2,maximum_new_tokens_per_record=128,maximum_generations=2568,maximum_generated_tokens=2568*128,formal_launch_confirmed=True,preflight_runs=[f'preflight/{k}' for k in names],preflight_controller_sha256=survey.io.sha(parent/'controller.json'),preflight_exit_sha256={k:survey.io.sha(parent/f'{k}.exit') for k in names})
            p=root/'auth.json';survey.io.write(p,auth)
            with patch.object(survey,'REPO',root),patch.object(survey,'check_freeze',return_value='f'),patch.object(survey,'check_pair'):
                survey.check_authorization(p,'survey',survey.MODEL,0,True)
                (parent/f'{names[1]}.exit').write_text('1\n')
                with self.assertRaises(AssertionError):survey.check_authorization(p,'survey',survey.MODEL,0,True)

    def test_predecessor_must_be_user_stopped_with_processes_exited(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/'previous.json'
            state=dict(status='user_stopped',processes_exited=True)
            survey.io.write(path,state)
            auth=dict(predecessor_stop_sha256=survey.io.sha(path))
            with patch.object(survey,'REPO',root),patch.object(survey,'load_design',return_value=({'predecessor':'previous.json'},None,None)):
                launch_survey.check_predecessor(auth)
                for changed in (dict(status='running',processes_exited=True),dict(status='user_stopped',processes_exited=False)):
                    survey.io.write(path,changed)
                    auth['predecessor_stop_sha256']=survey.io.sha(path)
                    with self.assertRaises(AssertionError):launch_survey.check_predecessor(auth)


if __name__ == '__main__':unittest.main()
