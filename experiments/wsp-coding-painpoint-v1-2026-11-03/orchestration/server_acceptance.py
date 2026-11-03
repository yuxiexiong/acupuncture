"""Real CPU adapter checks and optionally two bounded Astra fixture calls. No GPU."""
import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path
import os
import sys
import time
from ledger import write
import editor
import protocol as P
from backend import score_one,token_window


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--live-editor',action='store_true');a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=False);started=time.time();checks=[];usage={};threads=[]
    receipt=dict(status='running',new_gpu_seconds=0,new_model_generations=0,formal_search_started=False,checks=checks)
    write(a.out/'receipt.json',receipt)
    try:
        task=dict(test_list=['assert f(0)==1','assert f(2)==3'],test_setup_code='')
        rows=[dict(key='fixture',sample=s,seed=100+s,text='</think>```python\ndef f(x): return x'+('+1' if s==0 else '')+'\n```') for s in (0,1)]
        with ProcessPoolExecutor(max_workers=2) as pool:
            scores=list(pool.map(score_one,[(r,task,'mbpp',a.out/(str(i)+'.jsonl'),True) for i,r in enumerate(rows)]))
        assert [s['result']['correct'] for s in scores]==[True,False];checks.append('real_isolated_parallel_scorer_adapter')
        for r,s in zip(rows,scores):r.update(correct=s['result']['correct'],status=s['result']['status'],tests=s['result']['tests'],user='Return x plus one from f(x).')
        import torch
        needle=dict(layer=0,channels=list(range(8)),gain=.5)
        calibration=P.calibration(torch.ones((4,96),dtype=torch.bfloat16),torch.ones((8,96)),needle,P.random_supports(needle,96))
        assert all(abs(c['rms_ratio']-1)<.01 for c in calibration['controls']);checks.append('BF16_random_control_norm_calibration')
        from transformers import AutoTokenizer
        for model in ('text-Qwen3.5-0.8B','text-Qwen3.5-4B-r2'):
            tok=AutoTokenizer.from_pretrained('/workspace/acupuncture/external/wsp/'+model,local_files_only=True)
            raw='Reasoning carefully.\n</think>\n```python\ndef f(x): return x+1\n```'
            row=dict(key='fixture',sample=0,prompt_ids=tok('Synthetic prompt',add_special_tokens=False)['input_ids'],token_ids=tok(raw,add_special_tokens=False)['input_ids'])
            w=token_window(tok,row,'state_update');assert w is not None and w['end']-w['start']<=256 and w['ids']==row['prompt_ids']+row['token_ids']
        checks.append('both_real_tokenizers_exact_prefix_window')
        projected=editor.payload('diagnosis','D','D_LABEL',[dict(rows[0],observer_private='DO_NOT_EXPOSE')])
        assert 'observer_private' not in json.dumps(projected);checks.append('payload_allowlist')
        if a.live_editor:
            if not editor.login_status():raise RuntimeError('SERVER_CODEX_LOGIN_REQUIRED')
            for profile in ('0p8b','4b'):
                data=editor.payload('engineering','fixture','ENGINEERING',rows)
                result=editor.call(data,a.out/('astra-'+profile))
                P.diagnose(rows,result['annotations'])  # evidence validation; small fixture must stop scientifically
                threads.append(result['thread']);usage[profile]=result['usage']
                write(a.out/'editor-usage.json',usage)
            assert len(set(threads))==2;checks.append('server_astra_max_two_independent_tool_free_calls')
        receipt.update(status='passed',checks=checks,editor_usage=usage,threads=threads,seconds=time.time()-started,live_editor_tested=a.live_editor)
    except BaseException as exc:
        receipt.update(status='failed',error=type(exc).__name__+': '+str(exc),seconds=time.time()-started);raise
    finally:write(a.out/'receipt.json',receipt)
    print(json.dumps(receipt))


if __name__=='__main__':main()
