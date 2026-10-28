"""CPU-only checks of actual scheduling, signed records, and authorization boundaries."""
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
        self.assertEqual(list(map(len,jobs)),[1152,1152])
        seen = set(); groups = defaultdict(set)
        for shard, work in enumerate(jobs):
            for condition,p,question,dose in work:
                key = (condition,question['id']); self.assertNotIn(key,seen); seen.add(key)
                if p:
                    groups[(p['id'],dose)].add(question['id'])
                    self.assertEqual(p['layer']%2,shard)
        self.assertEqual(len(seen),2304); self.assertEqual(len(groups),288)
        self.assertTrue(all(len(v)==8 for v in groups.values()))
        for layer in range(32):
            for shard in (0,1):
                self.assertEqual(len({p['id'] for _,p,_,_ in jobs[shard] if p and p['layer']==layer}),1 if layer%2==shard else 0)

    def test_preflight_full_signed_anchors(self):
        for shard in (0,1):
            jobs = survey.make_specs('preflight',survey.MODEL,shard)
            self.assertEqual(len(jobs),44)
            self.assertEqual(Counter(survey.kind_for(x[0]) for x in jobs),dict(baseline=8,zero=3,restored=3,dose=30))
            self.assertEqual({p['layer'] for _,p,_,_ in jobs if p},{shard,16+shard,30+shard})
            for p in {p['id'] for _,p,_,_ in jobs if p}:
                self.assertEqual({d for _,a,_,d in jobs if a and a['id']==p and d not in (None,0)},set(survey.DOSES))

    def make_row(self):
        job = survey.make_specs('survey',survey.MODEL,0)[0]
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

    def test_dose_names_and_symmetry(self):
        self.assertEqual(len({survey.dose_id(d) for d in survey.DOSES}),10)
        with self.assertRaises(AssertionError):survey.dose_id(.75)
        for d in survey.DOSES:
            self.assertIn(-d,survey.DOSES)
            self.assertEqual(survey.bf16_round(d*2/3),-survey.bf16_round(-d*2/3))

    def test_permission_gate_before_model_loading(self):
        with self.assertRaises(AssertionError):survey.check_authorization('/not/a/file','survey',survey.MODEL,0,False)
        auth=dict(experiment=survey.HERE.name,freeze_sha256='f',status='authorized',purpose='preflight',models=[survey.MODEL],gpus=[0,1],user_instruction='authorized',recorded_utc='time',maximum_workers=2,maximum_new_tokens_per_record=128,maximum_generations=88,maximum_generated_tokens=11264,formal_launch_confirmed=False)
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'auth.json';survey.io.write(p,auth)
            with patch.object(survey,'check_freeze',return_value='f'),patch.object(survey,'source_evidence'):
                survey.check_authorization(p,'preflight',survey.MODEL,0,True)
                with self.assertRaises(AssertionError):survey.check_authorization(p,'survey',survey.MODEL,0,True)

    def test_formal_requires_completed_preflight_controller_and_zero_exits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);parent=root/'preflight';names=[f'{survey.MODEL}-shard-{i}' for i in (0,1)]
            state=dict(status='completed',mode='preflight',worker_exit_codes={k:0 for k in names})
            survey.io.write(parent/'controller.json',state)
            for key in names:(parent/f'{key}.exit').write_text('0\n')
            auth=dict(experiment=survey.HERE.name,freeze_sha256='f',status='authorized',purpose='survey',models=[survey.MODEL],gpus=[0,1],user_instruction='authorized',recorded_utc='time',maximum_workers=2,maximum_new_tokens_per_record=128,maximum_generations=2304,maximum_generated_tokens=2304*128,formal_launch_confirmed=True,preflight_runs=[f'preflight/{k}' for k in names],preflight_controller_sha256=survey.io.sha(parent/'controller.json'),preflight_exit_sha256={k:survey.io.sha(parent/f'{k}.exit') for k in names})
            p=root/'auth.json';survey.io.write(p,auth)
            with patch.object(survey,'REPO',root),patch.object(survey,'check_freeze',return_value='f'),patch.object(survey,'check_pair'),patch.object(survey,'source_evidence'):
                survey.check_authorization(p,'survey',survey.MODEL,0,True)
                (parent/f'{names[1]}.exit').write_text('1\n')
                with self.assertRaises(AssertionError):survey.check_authorization(p,'survey',survey.MODEL,0,True)

    def test_source_gate_and_replay(self):
        with patch.object(survey,'source_evidence',side_effect=AssertionError('source not complete')):
            with self.assertRaisesRegex(AssertionError,'source not complete'):
                launch_survey.check_predecessor({})
        row,job,cals = self.make_row()
        row['dose'] = 1.; row['output'].update(raw_text='raw',answer_text='answer')
        source = {(row['point_id'],row['question_id']):(None,None,copy.deepcopy(row))}
        survey.check_source_replay(row,source)
        row['output']['token_ids'] = [8,128009]
        with self.assertRaises(AssertionError):survey.check_source_replay(row,source)

    def test_selected_channel_is_seeded_and_not_outcome_based(self):
        import random
        samples = survey.load_design()[2][survey.MODEL]
        candidates = survey.io.read(survey.SOURCE/'samples.json')[survey.MODEL]
        self.assertEqual(len(samples),32)
        for layer, point in enumerate(samples):
            ten = sorted([p for p in candidates if p['layer']==layer],key=lambda p:p['channel'])
            self.assertEqual(point,random.Random(f'acupuncture-layer-dose-v1:{survey.MODEL}:{layer}').choice(ten))
        self.assertNotIn(1.,survey.NEW_DOSES)
        self.assertEqual(set(survey.NEW_DOSES)|{1.},set(survey.DOSES))

    def test_every_dose_retains_source_context_and_column_norm(self):
        row,job,cals = self.make_row()
        source = {(row['point_id'],row['question_id']):(None,None,copy.deepcopy(row))}
        survey.check_source_replay(row,source)
        for field in ('column_norm','clean_residual_scale'):
            bad = copy.deepcopy(row);bad['intervention'][field] += 1
            with self.assertRaises(AssertionError):survey.check_source_replay(bad,source)
        bad=copy.deepcopy(row);bad['output']['input_token_sha256']='another input'
        with self.assertRaises(AssertionError):survey.check_source_replay(bad,source)

    def test_source_requires_completed_controller_and_exact_identity(self):
        import types
        stub = types.SimpleNamespace()
        loader = types.SimpleNamespace(exec_module=lambda module:None)
        spec = types.SimpleNamespace(loader=loader)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);run=root/'survey-r01'
            state=dict(status='running',mode='survey')
            survey.io.write(run/'controller.json',state)
            with patch.object(survey,'SOURCE',root),patch.object(survey.importlib.util,'spec_from_file_location',return_value=spec),patch.object(survey.importlib.util,'module_from_spec',return_value=stub):
                with self.assertRaises(AssertionError):survey.source_evidence({})
                state['status']='completed';survey.io.write(run/'controller.json',state)
                with self.assertRaises(AssertionError):survey.source_evidence({'source_controller_sha256':'wrong'})


if __name__ == '__main__':unittest.main()
