"""Tokenizer-only CPU acceptance; never loads model weights."""
import os
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'cache-donor-write-readout-v1-2026-11-07'))
import dwr_run as R
import materials as M

def main():
    assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
    sys.path.insert(0,str(R.T1.SOURCE))
    from control_engine import encode_text
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(R.exp.read(R.T1.SOURCE/'contract.json')['source']['model_path'])
    data=M.load(); old=R.LVKR.ledger(); families={}
    for v in old.values():
        f=families.setdefault(v['plan']['base_id'],dict(n=0,L=0,q=set()))
        f['n']=max(f['n'],v['plan']['n']);f['L']=max(f['L'],v['plan']['L']);f['q'].add(v['tokens']['q_shared'])
    contexts=R.exp.contexts_for(tok,list(data['items'].values()))
    ledger={}; suffixes={}; failures=[]
    for iid,it in data['items'].items():
        seg=R.PK.label_tokens(tok,contexts[iid],it['boundary_text'],encode_text)
        b,n=seg['b'],seg['n'];q,t,d=R.QSTR.shared_tokens(tok,it);f=families[it['family']]
        errors=[]
        if seg['straddling_tokens']:errors.append('boundary straddling')
        if not 0<b+1<=n-2<n-1:errors.append('B1 window')
        if n>2*f['n'] or n-b-2>2*f['L']:errors.append('length >2x old family')
        if {q}!=f['q']:errors.append('first code token changed')
        if [len(tok.encode(c,add_special_tokens=False)) for c in it['listed_codes']] != [3,3,3]:errors.append('code lengths')
        suffix=tuple(seg['ids'][-5:-1]); suffixes.setdefault(it['scenario'],set()).add(suffix)
        ledger[iid]=dict(item=it,plan=dict(base_id=it['family'],scene_id=it['scenario'],b=b,n=n,p=b+1,e=n-2,L=n-b-2,
                         prompt_token_sha256=R.exp.digest(seg['ids'])),tokens=dict(q_shared=q,target_second=t,distractor_second=d,last_four_cached=list(suffix)),failures=errors)
        if errors:failures.append([iid,errors])
    failures += [[s,'last four cached tokens differ'] for s,x in suffixes.items() if len(x)!=1]
    out=dict(status='failed' if failures else 'passed',materials_sha256=M.sha(HERE/'data/materials-r01.json'),
             model_revision='851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a',model_calls=0,failures=failures,items=ledger,
             n_range=[min(x['plan']['n'] for x in ledger.values()),max(x['plan']['n'] for x in ledger.values())],
             L_range=[min(x['plan']['L'] for x in ledger.values()),max(x['plan']['L'] for x in ledger.values())])
    M.write(HERE/'data/token-ledger-r01.json',out)
    print({k:v for k,v in out.items() if k!='items'})
    assert not failures
if __name__=='__main__':main()
