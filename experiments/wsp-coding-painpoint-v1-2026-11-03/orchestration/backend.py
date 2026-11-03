"""Observer-only real adapters. Imported models live in bounded GPU subprocesses."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from ledger import write,file_hash
import protocol as P


def lines(path):return [json.loads(x) for x in Path(path).read_text().splitlines()]


def score_one(args):
    from score_batch import score_rows
    row,task,kind,journal,thinking=args
    return score_rows([row],{row['key']:task},kind,journal,thinking)[0]


def selected_pairs(req):
    indexed={(r['key'],r['sample']):r for r in req['rows']}
    labels={(a['key'],a['sample']):a for a in req['diagnosis']['annotations']}
    pairs=[]
    for key in req['diagnosis']['pairs']:
        success=next(r for (k,s),r in indexed.items() if k==key and r['correct'])
        failure=next(r for (k,s),r in indexed.items() if k==key and not r['correct'] and req['diagnosis']['target'] in labels[(k,s)]['labels'])
        pairs.append((success,failure))
    return pairs


class Backend:
    def __init__(self,cfg):
        self.cfg=cfg;self.data=Path(cfg['data_root'])
        manifest=json.loads((self.data/'manifest.json').read_text())
        if file_hash(self.data/'manifest.json')!=cfg['data_manifest_sha256']:raise ValueError('DATA_FREEZE_CHANGED')
        for p,meta in manifest['files'].items():
            if file_hash(self.data/p)!=meta['sha256']:raise ValueError('DATA_FILE_CHANGED: '+p)
        self.panels={p:lines(self.data/('editor-D' if p in ('D','S') else 'observer-private')/(p+'.jsonl')) for p in ('D','S','V','T','M')}
        self.tasks={p:{str(t['task_id']):t for t in lines(self.data/'observer-private'/(p+'-scoring.jsonl'))} for p in self.panels}

    def locate_tokens(self,req):
        return sum(len(r['prompt_ids'])+len(r['token_ids']) for pair in selected_pairs(req) for r in pair)

    def perform(self,req,out):
        before=resource.getrusage(resource.RUSAGE_CHILDREN);own=time.process_time()
        if req['op']=='labels':
            import editor
            result=editor.call(req['payload'],out/'editor');result['_usage']=result.pop('usage')
        else:result=self.gpu(req,out)
        after=resource.getrusage(resource.RUSAGE_CHILDREN)
        result['_usage']['cpu_seconds']=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime+time.process_time()-own
        return result

    def gpu(self,req,out):
        # Only idle cards and the same advisory lock used by the accepted WSP service.
        lock=None
        peak=(1504832352 if self.cfg['profile']=='0p8b' else 8411565480)+2200000000
        current=sum(p.stat().st_size for p in Path(self.cfg['run_root']).rglob('*') if p.is_file())
        if shutil.disk_usage(out).free<self.cfg['reserve_free_bytes']+peak or current+peak>self.cfg['new_data_bytes_cap']:
            raise RuntimeError('STORAGE_LOW_BEFORE_MODEL_LOAD')
        while lock is None:
            status=subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True)
            for row in status.splitlines():
                gpu,mem,util=map(int,row.split(','))
                if mem>=128 or util:continue
                candidate=open(f'/workspace/acupuncture/external/wsp/engineering-gpu-{gpu}.lock','a')
                try:fcntl.flock(candidate,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:candidate.close();continue
                lock=candidate;break
            if lock is None:
                write(out/'waiting-for-gpu.json',dict(waiting=True,time=time.time(),gpu_seconds_charged=0))
                time.sleep(10)
        started=time.monotonic();proc=None
        try:
            request=dict(req,profile=self.cfg['profile'])
            if req['op']=='generate':request['tasks']=[t for t in self.panels[req['panel']] if str(t['task_id']) in req['keys']]
            write(out/'worker-request.json',request)
            with (out/'worker.log').open('w') as log:
                proc=subprocess.Popen([sys.executable,__file__,'--worker',str(out/'worker-request.json'),'--out',str(out)],
                    stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES=str(gpu)))
                write(out/'process.json',dict(pid=proc.pid,gpu=gpu,started_unix=time.time()))
                proc.wait(timeout=req['deadline_seconds'])
            if proc.returncode:raise RuntimeError('GPU_WORKER_FAILED: inspect preserved worker.log')
            result=json.loads((out/'worker-result.json').read_text())
        finally:
            if proc is not None and proc.poll() is None:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
            elapsed=time.monotonic()-started;write(out/'gpu-usage.json',dict(gpu_seconds=elapsed,stage=req['stage']))
            lock.close()
        usage=dict(gpu_seconds=elapsed,**{'gpu_'+req['stage']:elapsed},samples=0,output_tokens=0,tf_tokens=result.pop('tf_tokens',0))
        if req['op']=='generate':
            rows=lines(out/'generation.jsonl');items={it['key']:it for it in json.loads((out/'items.json').read_text())}
            if len(rows)!=len(req['keys'])*req['n']:raise ValueError('MISSING_GENERATIONS')
            if req['panel']=='M':
                import model_interface as MI
                scorer=MI.FS.load_mathqa();scored=[]
                for r in rows:
                    pred,_=scorer['extract'](r['text']);answer=self.tasks['M'][r['key']]['answer'].rsplit('####',1)[-1].strip()
                    scored.append(dict(key=r['key'],sample=r['sample'],result=dict(correct=bool(scorer['is_correct'](pred,answer)),status='math_scored',tests=[])))
            else:
                score_dir=out/'scores';score_dir.mkdir()
                jobs=[(r,self.tasks[req['panel']][r['key']],'humaneval' if req['panel']=='T' else 'mbpp',score_dir/(str(i)+'.jsonl'),req['thinking']) for i,r in enumerate(rows)]
                with ProcessPoolExecutor(max_workers=4) as pool:scored=list(pool.map(score_one,jobs))
            for r,s in zip(rows,scored):
                if type(s['result'].get('correct')) is not bool:raise RuntimeError('SCORER_INFRASTRUCTURE_FAILURE')
                r.update(correct=s['result']['correct'],status=s['result']['status'],tests=s['result'].get('tests',[]),
                         score=s['result'],prompt_ids=items[r['key']]['prompt_ids'],user=next(t['user'] for t in self.panels[req['panel']] if str(t['task_id'])==r['key']),
                         unfinished=s['result']['status']=='unfinished_thinking' or r['finish_reason']=='length')
            usage.update(samples=len(rows),output_tokens=sum(len(r['token_ids']) for r in rows));result=dict(rows=rows)
        result['_usage']=usage
        return result


def token_window(tok,row,target):
    ids=row['token_ids'];text=tok.decode(ids,skip_special_tokens=True)
    encoded=tok(text,add_special_tokens=False,return_offsets_mapping=True)
    nonspecial=[i for i in ids if i not in tok.all_special_ids]
    if encoded['input_ids']!=nonspecial:raise ValueError('TOKEN_WINDOW_ALIGNMENT_UNVERIFIED')
    positions=[i for i,t in enumerate(ids) if t not in tok.all_special_ids]
    if target=='reasoning_loop':
        boundary=text.find('</think>');boundary=len(text) if boundary<0 else boundary
        eligible=[positions[i] for i,(a,b) in enumerate(encoded['offset_mapping']) if b<=boundary]
        selected=eligible[-128:]
    else:
        from scoring import extract
        code,error=extract(text,True)
        if error or not code:return None
        start=text.find(code,text.rfind('</think>')+8)
        if start<0:raise ValueError('CODE_WINDOW_MISSING')
        selected=[positions[i] for i,(a,b) in enumerate(encoded['offset_mapping']) if b>start and a<start+len(code)][:256]
    if not selected:return None
    offset=len(row['prompt_ids']);return dict(ids=row['prompt_ids']+ids,start=offset+selected[0],end=offset+selected[-1]+1,key=row['key'],sample=row['sample'])


def worker(req,out):
    import torch
    import numpy as np
    import model_interface as MI
    from transformers import AutoTokenizer
    prof=MI.FS.profile(req['profile']);tok=AutoTokenizer.from_pretrained(prof['model'],local_files_only=True)
    if req['op']=='generate':
        gain=req['gain'];checkpoint=prof['model']
        if gain:
            checkpoint,_=MI.compile_gain(prof,gain['layer'],gain['channels'],gain['gain'],out/'compiled')
        if req['panel']=='M':
            items=[dict(key=str(t['task_id']),prompt_ids=tok(MI.FS.render_prompt(tok,t['user']+'\n'+MI.FS.INSTRUCTION),add_special_tokens=False)['input_ids'],seed=MI.FS.item_seed('wcp01:'+str(t['task_id'])),n=req['n'],max_tokens=32768) for t in req['tasks']]
        else:items=MI.coding_items(tok,req['tasks'],req['thinking'],n=req['n'])
        write(out/'items.json',items)
        a=argparse.Namespace(ckpt=str(checkpoint),items=str(out/'items.json'),out=str(out/'generation.jsonl'),
                            max_len=max(len(t['prompt_ids'])+t['max_tokens']+16 for t in items),max_seqs=32,mem=.75,eager=True)
        if req['panel']!='M':MI.FS.SAMPLING=MI.SAMPLING
        MI.FS.vllm_worker(a)
        # Preserve every edit/snapshot/build record, remove only reconstructable full model copies.
        cache=out/'compiled/checkpoint-cache'
        if cache.exists():shutil.rmtree(cache)
        return dict(tf_tokens=0)
    reader=MI.FS.Reader(prof['model'],'cuda:0');torch.set_num_threads(4)
    if req['op']=='locate':
        stats=dict(mean=[],rms=[]);replays=[];keys=[];tokens=0
        for pair in selected_pairs(req):
            windows=[token_window(tok,r,req['diagnosis']['target']) for r in pair]
            if any(w is None for w in windows):continue
            pair_mean=[];pair_rms=[]
            for w in windows:
                s=MI.activation_summary(reader,w['ids'],w['start'],w['end']);tokens+=len(w['ids'])
                pair_mean.append(np.stack([s[i]['mean'].numpy() for i in range(prof['n_layers'])]))
                pair_rms.append(np.stack([s[i]['rms'].numpy() for i in range(prof['n_layers'])]))
                replays.append(w)
            stats['mean'].append(pair_mean);stats['rms'].append(pair_rms);keys.append(pair[0]['key'])
        if len(keys)<8:return dict(supports=[],pairs=keys,calibration_tf_tokens=0,tf_tokens=tokens)
        np.savez(out/'paired-stats.npz',**{k:np.asarray(v) for k,v in stats.items()});write(out/'replays.json',replays)
        return dict(supports=P.rank_supports(stats),pairs=keys,replays=str(out/'replays.json'),replays_sha256=file_hash(out/'replays.json'),calibration_tf_tokens=tokens,tf_tokens=tokens)
    loc=req['location']
    if file_hash(loc['replays'])!=loc['replays_sha256']:raise ValueError('REPLAY_CHANGED')
    replays=json.loads(Path(loc['replays']).read_text());xs=[];needle=req['needle'];module=reader.layers[needle['layer']].mlp.down_proj
    for w in replays:
        handle=module.register_forward_pre_hook(lambda mod,args,w=w:xs.append(args[0][0,w['start']:w['end']].detach().cpu()))
        try:reader.run([w['ids']])
        finally:handle.remove()
    controls=P.random_supports(needle,prof['inter'])
    try:
        result=P.calibration(module.weight.detach().cpu(),torch.cat(xs),needle,controls);result['valid']=True
    except ValueError as exc:result=dict(valid=False,reason=str(exc),supports=controls)
    result['tf_tokens']=sum(len(w['ids']) for w in replays)
    return result


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--worker',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    write(a.out/'worker-result.json',worker(json.loads(a.worker.read_text()),a.out))
