"""CPU regression tests for interface boundaries and fail-closed scheduler."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import controller as C
import forward_service as F
from test_forward_service import PROF,PRACTICE


class Tokenizer:
    def __call__(self,s,**kw): return {'input_ids':list(range(int(s)))}


class Tests(unittest.TestCase):
    def test_action_parser(self):
        self.assertEqual(C.parse_action('```python\nx=1\n```'),{'kind':'python','code':'x=1\n'})
        self.assertEqual(C.parse_action('Reason.\n```forward\n{"type":"generate"}\n```',True)['kind'],'forward')
        for text in ['```bash\nrm -rf /\n```','```python\nx=1\n```\n```python\nx=2\n```','Prefix\n```python\nx=1\n```','```python\nx=1']:
            with self.assertRaises(ValueError): C.parse_action(text)
    def test_launch_gate(self):
        for cfg in [{'mode':'search','authorized':False},{'mode':'search','authorized':True},{'mode':'engineering','turn_limit':7}]:
            with self.assertRaises(ValueError): C.authorize(cfg)
        C.authorize({'mode':'engineering','turn_limit':4})
    def test_invalid_types(self):
        base={'type':'generate','model':'original','problems':['a']}
        for kwargs in [{'n':True},{'n':1.5},{'max_tokens':False},{'problems':[[]]},{'problems':['a','a']}]:
            with self.assertRaises(F.RequestError): F.validate(dict(base,**kwargs),PROF,PRACTICE)
    def test_return_bytes(self):
        req=F.validate({'type':'teacher_forced','model':'original','texts':['10','5'],
                        'return':{'hidden_states':[0,24],'mlp_act':[0],'topk':3,'token_logprobs':True}},PROF,PRACTICE)
        _,ids,size=F.tf_token_lists(Tokenizer(),req,PROF)
        expected=2*10*(2*(2*1024+3584)+4+8*3+8)-2*4+128*7
        self.assertEqual(size,expected)
        req['texts']=['32768']*100
        with self.assertRaises(F.RequestError): F.tf_token_lists(Tokenizer(),req,PROF)
    def test_public_schema(self):
        record={'correct':False,'n_tokens':16,'cut':True,'source':'math','pred':None}
        result={'type':'generate','model':'original','seconds':1,'arms':{'original':dict(F.summarize([record]),file='/work/gen_1.jsonl')}}
        r=F.public_result(result)
        self.assertEqual(r['accuracy_by_source'],{'math':0.0})
        self.assertEqual(r['failures'],{'wrong_answer':0,'no_answer_finished':0,'cut_at_max_tokens':1})
        self.assertEqual(r['generations'],1)
        self.assertNotIn('arms',r)
    def test_pair_coverage(self):
        with self.assertRaises(RuntimeError):
            F.paired([{'key':'a','sample':0,'correct':True}],[])
    def test_broker_idempotency_and_pending(self):
        from broker import Broker
        with tempfile.TemporaryDirectory() as temp, patch('forward_service.profile',return_value={'model':Path('/fake')}), \
             patch('transformers.AutoTokenizer.from_pretrained') as tok:
            tok.return_value.apply_chat_template.return_value='<u>WSP_PROBLEM_PLACEHOLDER_49871</u>'
            b=Broker({'run_root':temp,'profile':'0p8b','forward_limit':1})
            action={'id':'test','kind':'status'}
            r=b.dispatch(action); self.assertEqual(b.dispatch(action),r)
            with self.assertRaises(ValueError): b.dispatch(dict(action,kind='python'))
            (Path(temp)/'actions/pending').mkdir()
            with self.assertRaises(RuntimeError): b.dispatch({'id':'new','kind':'status'})
            b.lock.close()
    def test_notes_symlink_rejected(self):
        from broker import Broker
        with tempfile.TemporaryDirectory() as temp:
            b=Broker.__new__(Broker); b.work=Path(temp); b.state={}
            (b.work/'edited').mkdir(); (b.work/'notes.md').symlink_to('/etc/passwd')
            with self.assertRaises(OSError): b.context()


if __name__=='__main__': unittest.main()
