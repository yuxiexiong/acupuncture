"""CPU-only checks for the task adapter trust boundary."""
import os
from pathlib import Path

local=Path(__file__).resolve().parent.parent/'wsp-process-reproduction-v1-2026-11-03/engineering-r2'
if local.exists(): os.environ['WCP_WSP_ENGINE']=str(local)
import model_interface as M
from scoring import extract


def main():
    prof=dict(n_layers=24,inter=3584)
    M.validate_gain(prof,0,list(range(8)),.5)
    bad=[(24,list(range(8)),.5),(0,[1]*8,.5),(0,list(range(7)),.5),
         (0,list(range(8)),float('nan')),(0,list(range(8)),1.5),(0,list(range(7))+[3584],.5)]
    for args in bad:
        try: M.validate_gain(prof,*args)
        except ValueError: pass
        else: raise AssertionError(args)
    assert extract('unclosed reasoning',True)[1]=='unfinished_thinking'
    assert extract('reason</think>```python\ndef f(): pass\n```')[0]=='def f(): pass'
    assert M.SAMPLING['presence_penalty']==0
    print('9 CPU interface assertions passed')


if __name__=='__main__': main()
