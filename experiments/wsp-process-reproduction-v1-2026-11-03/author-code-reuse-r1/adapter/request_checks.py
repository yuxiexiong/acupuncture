"""Validate frozen author requests without executing any forward."""
import hashlib
import json
from pathlib import Path
import sys
from transformers import AutoTokenizer
from tokenizers import Tokenizer
import forward_service as F

root=Path(sys.argv[1]); source=root/'interface-requests.json'
items=json.loads(source.read_text())
prof=F.profile('0p8b'); practice=F.practice_index()
tok=AutoTokenizer.from_pretrained(prof['model'],local_files_only=True)
backend=Tokenizer.from_file(str(prof['model']/'tokenizer.json'))
rows=[]
for item in items:
    req=F.validate(item['request'],prof,practice)
    row={'source_pass':item['source_pass'],'type':req['type'],'status':'passed'}
    if req['type']=='teacher_forced':
        strings,ids,est=F.tf_token_lists(tok,req,prof)
        assert list(map(len,ids))==item['author_lengths'],item['source_pass']
        assert all(backend.encode(s,add_special_tokens=False).ids==v for s,v in zip(strings,ids))
        row.update(lengths=item['author_lengths'],estimated_bytes=est)
    else:
        texts=[practice[p]['problem']+'\n'+F.INSTRUCTION for p in req['problems']]+req['prompts']
        for s in texts:
            rendered=F.render_prompt(tok,s)
            assert tok(rendered,add_special_tokens=False).input_ids==backend.encode(rendered,add_special_tokens=False).ids
        row.update(items=len(texts),n=req['n'],max_tokens=req['max_tokens'])
    rows.append(row)
receipt={'status':'passed','request_file_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'rows':rows,
         'successful_requests':len(rows),'gpu_seconds':0,'formal_started':False,
         'limitation':'Author complete input_ids were not published; exact IDs checked between our server and sandbox; all published TF lengths match'}
(root/'request-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'status':'passed','requests':len(rows),'tf':sum(r['type']=='teacher_forced' for r in rows)}))
