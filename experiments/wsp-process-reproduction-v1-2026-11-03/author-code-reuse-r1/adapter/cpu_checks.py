"""CPU protocol checks. No author analysis or generation is executed."""
import importlib.metadata
import json
import math
from pathlib import Path
import sys
import forward_service as F

root=Path(sys.argv[1]); root.mkdir(parents=True,exist_ok=True)
Q=F.load_mathqa()
cases=[(r'\boxed{\frac{1}{2}}','0.5',True),(r'\boxed{2}','3',False),('no boxed answer','2',False),
       (r'\boxed{1} then \boxed{2}','2',True),('<think>\\boxed{2}</think>\\boxed{3}','3',True)]
scores=[]
for text,gold,expected in cases:
    pred,_=Q['extract'](text)
    actual=bool(Q['is_correct'](pred,gold))
    assert actual==expected,(text,pred,actual)
    scores.append({'text':text,'pred':pred,'gold':gold,'correct':actual})
try:
    Q['mcqa_loop_signals']('x')
    raise AssertionError('Missing diagnostic must fail')
except NotImplementedError:
    pass
orig=[]; edit=[]
for key,aa,bb in [('a',[False,False],[True,True]),('b',[True,False],[False,False])]:
    for i,(a,b) in enumerate(zip(aa,bb)):
        orig.append(dict(key=key,sample=i,correct=a,text='o'))
        edit.append(dict(key=key,sample=i,correct=b,text='e'))
pair=F.paired(orig,edit)
assert pair['items']==2 and pair['answers']==4 and pair['accuracy_difference']==.25 and pair['standard_error']==.75
from transformers import AutoTokenizer
from tokenizers import Tokenizer
tok=AutoTokenizer.from_pretrained(F.profile('0p8b')['model'],local_files_only=True)
backend=Tokenizer.from_file(str(F.profile('0p8b')['model']/'tokenizer.json'))
lengths={}
for file,expected in [('006-forward.json',[130,129,137,142,113,152,104,141]),('009-forward.json',[124,123,131,136,107,146,98,135])]:
    q=json.loads((root/file).read_text())
    req=F.validate(q,F.profile('0p8b'),F.practice_index())
    strings,ids,_=F.tf_token_lists(tok,req,F.profile('0p8b'))
    assert list(map(len,ids))==expected
    assert all(backend.encode(s,add_special_tokens=False).ids==v for s,v in zip(strings,ids))
    lengths[file]=expected
versions={n:importlib.metadata.version(n) for n in ['torch','transformers','vllm','math-verify','latex2sympy2_extended','antlr4-python3-runtime','tokenizers']}
assert versions['math-verify']=='0.9.0'
for f in ['gsm8k_train.jsonl','math_train.jsonl','aime.jsonl']:
    F.verify_source('exp8_math/practice/'+f)
receipt={'status':'passed','scores':scores,'missing_diagnostic':'raises NotImplementedError','paired_fixture':pair,
         'author_lengths':lengths,'backend_token_ids_equal':True,'versions':versions,'gpu_seconds':0,'formal_started':False}
(root/'cpu-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
