"""One locked two-GPU queue: source prerequisites, 9B, then 2B; fail closed."""
import argparse
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
from run_io import read, write, sha, utc

ROOT = Path(__file__).resolve().parent
MODELS = {'source4b':'/data/models/Qwen3.5-4B-851bf6e',
          'target9b':'/workspace/models/Qwen3.5-9B-c2022362',
          'target2b':'/workspace/models/Qwen3.5-2B-15852e8c'}


def command(script, **kwargs):
    parts = [sys.executable, str(ROOT/script)]
    for key,value in kwargs.items():
        parts.extend(['--'+key.replace('_','-'),str(value)])
    return parts


def complete(path):
    if not Path(path).exists():
        return False
    return read(path).get('status') in ('completed','machine_completed_blind_review_pending')


def run(args):
    run = Path(args.run).resolve()
    run.mkdir(parents=True,exist_ok=True)
    lock = (run/'queue.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    freeze = read(ROOT/'freeze.json')
    for name,digest in freeze['files'].items():
        assert sha(ROOT/name)==digest, f'Frozen input/code changed: {name}'
    path = run/'queue_receipt.json'
    previous = read(path) if path.exists() else None
    assert not previous or args.resume, 'Existing queue requires explicit --resume'
    receipt = {'status':'running','started_utc':utc(),'pid':os.getpid(),'run':str(run),
               'freeze_sha256':sha(ROOT/'freeze.json'),'sequence':['target9b','target2b'],'stages':[],
               'root_cause_experiment':'paused','behavior_ratings':'pending_independent_blind_review'}
    if previous:
        immutable = run/('queue-history-'+str(time.time_ns())+'.json')
        write(immutable,previous)
        receipt['previous_receipt']=immutable.name
    write(path,receipt)

    def wait_existing(name, expected):
        entry={'name':name,'status':'waiting_for_existing_process','started_utc':utc(),'receipts':[str(x) for x in expected]}
        receipt['stages'].append(entry);receipt['current_stage']=name;write(path,receipt)
        while not all(complete(p) for p in expected):
            for p in expected:
                if Path(p).exists():
                    state=read(p)
                    assert state.get('status')!='failed', f'{p}: {state.get("error")}'
            time.sleep(5)
        entry.update(status='completed_existing',ended_utc=utc());write(path,receipt)

    def group(name, jobs):
        entry={'name':name,'status':'running','started_utc':utc(),'jobs':[]}
        receipt['stages'].append(entry);receipt['current_stage']=name;write(path,receipt)
        processes=[]
        for gpu,cmd,expected in jobs:
            job={'gpu':gpu,'command':cmd,'receipt':str(expected)}
            entry['jobs'].append(job)
            if complete(expected):
                job.update(status='reused_completed');continue
            assert not Path(expected).exists(), f'Preserve failed/partial attempt before retry: {expected}'
            logpath=run/(name+'-'+str(len(entry['jobs']))+'-'+str(time.time_ns())+'.log')
            stream=logpath.open('x')
            env=dict(os.environ,TOKENIZERS_PARALLELISM='false')
            if gpu is not None:env['CUDA_VISIBLE_DEVICES']=str(gpu)
            child=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
            stream.close()
            job.update(status='running',pid=child.pid,log=str(logpath),started_utc=utc())
            processes.append((child,job));write(path,receipt)
        while any(child.poll() is None for child,_ in processes):
            for child,job in processes:
                if child.poll() is not None and job['status']=='running':
                    job.update(status='completed' if child.returncode==0 else 'failed',exit_code=child.returncode,ended_utc=utc())
            write(path,receipt);time.sleep(5)
        for child,job in processes:
            job.update(status='completed' if child.returncode==0 else 'failed',exit_code=child.returncode,ended_utc=utc())
        write(path,receipt)
        assert all(job.get('exit_code',0)==0 and complete(job['receipt']) for job in entry['jobs']), f'Stage failed: {name}'
        entry.update(status='completed',ended_utc=utc());write(path,receipt)

    try:
        wait_existing('initial-clean-collections',[run/'collection-source4b/receipt.json',run/'collection-target9b/receipt.json'])
        wait_existing('source-bridge-and-9b-mapping',[run/'bridge/receipt.json',run/'target9b/mapping/receipt.json'])
        group('source-and-9b-decode-check',[(gpu,command('run_decode_check.py',model=MODELS[name],
            output=run/('decode-'+name)),run/('decode-'+name)/'receipt.json') for gpu,name in [(0,'source4b'),(1,'target9b')]])
        group('source-confirmation',[(gpu,command('run_toy.py',kind='source',model=MODELS['source4b'],data=ROOT/'data',
            output=run/'source',shard_index=gpu),run/f'source/shard{gpu}/receipt.json') for gpu in (0,1)])
        for target in ('target9b','target2b'):
            base=run/target
            if target=='target2b':
                group('2b-preflight',[(0,command('run_preflight.py',model=MODELS[target],output=run/'preflight-target2b'),run/'preflight-target2b/receipt.json')])
                group('2b-decode-check',[(0,command('run_decode_check.py',model=MODELS[target],output=run/'decode-target2b'),run/'decode-target2b/receipt.json')])
                group('2b-clean-collection',[(0,command('collect_activations.py',model=MODELS[target],data=ROOT/'data',
                    output=run/'collection-target2b',role='target'),run/'collection-target2b/receipt.json')])
                group('2b-mapping',[(0,command('fit_mapping.py',source=run/'collection-source4b',target=run/'collection-target2b',
                    output=base/'mapping',device='cuda:0'),base/'mapping/receipt.json')])
            bundle=base/'mapping/bundle.pt'
            group(target+'-confirmation',[(gpu,command('run_toy.py',kind='target',model=MODELS[target],data=ROOT/'data',
                output=base/'toy',conditions=bundle,source_output=run/'source',shard_index=gpu),base/f'toy/shard{gpu}/receipt.json') for gpu in (0,1)])
            group(target+'-benchmark',[(gpu,command('run_benchmark.py',model=MODELS[target],conditions=bundle,
                output=base/'benchmark',shard_index=gpu),base/f'benchmark/shard-{gpu}/receipt.json') for gpu in (0,1)])
            group(target+'-benchmark-finish',[(None,command('finish_benchmark.py',output=base/'benchmark',project=ROOT.parents[1]),
                base/'benchmark/finish-r01/receipt.json')])
            group(target+'-export',[(None,command('export_results.py',run=run,target=target,data=ROOT/'data',project=ROOT.parents[1]),
                base/'export-r01/receipt.json')])
        receipt.update(status='machine_completed_blind_review_pending',ended_utc=utc())
    except Exception as exc:
        receipt.update(status='failed',ended_utc=utc(),error=str(exc),traceback=traceback.format_exc())
        raise
    finally:
        write(path,receipt)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--resume',action='store_true')
    run(p.parse_args())
