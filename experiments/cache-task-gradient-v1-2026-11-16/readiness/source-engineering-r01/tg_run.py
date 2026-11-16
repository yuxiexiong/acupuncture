"""TGA-01: reuse NGU assets/lifecycle; measure native task gradients once per background."""
import argparse
import copy
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
NGU=HERE.parent/'cache-numerator-gate-use-v1-2026-11-16'
NGU_OLD=NGU/'runs/formal-20261116-r01'
DESIGN=NGU/'analysis/asymmetry-r01'
sys.path.insert(0,str(NGU))
import ngu_run as N
W,K,R=N.W,N.K,N.R
CAP={'engineering':900,'formal':5400}
TOTAL_CAP=7200
STORAGE=2*2**30


def panel(stage):
    items,tables=R.panel(stage)
    tables={r:[d for d in ds if d['type'] in ('AL','BD')] for r,ds in tables.items()}
    expected=20 if stage=='engineering' else 168
    assert sum(map(len,tables.values()))==expected
    if stage=='engineering':
        saved=W.read(DESIGN/'measurement-engineering-panel.json')
        assert {(r,d['id']) for r,ds in tables.items() for d in ds}=={(x['receiver'],x['donor']) for x in saved['pairs']}
    return items,tables


def limits(stage):
    items,tables=panel(stage);r,p=len(items),sum(map(len,tables.values()))
    return dict(receivers=r,pairs=p,formations=2*r,prefix_prefills=r,
                formation_token_forwards=56*r,t1=2*p,native_t2=2*p,frozen_t2=2*p,
                backwards=2*p,model_forwards=57*r+6*p)


def freeze(output):
    assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
    source=NGU/'readiness/freeze-server-r03.json'
    fr=W.read(source);W.check_files(fr)
    for p,h in fr['external_sources'].items():assert W.sha(p)==h
    rc=W.read(NGU_OLD/'receipt.json');assert rc['status']=='completed'
    nr=W.read(N.RCS_OLD/'receipt.json');assert nr['status']=='completed'
    _,tables=panel('formal'); assets={}
    for r,ds in tables.items():
        for d in ds:
            rel=f'records/{r}/{d["id"]}.json'
            for root,receipt in ((NGU_OLD,rc),(N.RCS_OLD,nr)):
                p=root/rel;assert W.sha(p)==receipt['files'][rel]
                fr['files'][str(p.relative_to(ROOT))]=W.sha(p)
            for b in ('C','H'):
                for root,receipt,suffix in ((NGU_OLD,rc,b+'X'),(N.RCS_OLD,nr,b+'11')):
                    p=root/f'tensors/{r}/{d["id"]}-{suffix}-t2.pt'
                    h=receipt['files'][str(p.relative_to(root))];assert W.sha(p)==h
                    assets[str(p.relative_to(ROOT))]=h
            pkg=f'packages/{r}/{d["id"]}-H.pt'
            assert W.sha(N.OLD/pkg)==fr['packages'][pkg]
    fr['files'].update(assets)
    for p in list(HERE.glob('*.py'))+[HERE/'IMPLEMENTATION.zh-CN.md',DESIGN/'MINIMAL_MEASUREMENT.zh-CN.md',DESIGN/'measurement-engineering-panel.json',source,NGU_OLD/'receipt.json',NGU_OLD/'analysis.json',N.RCS_OLD/'receipt.json']:
        fr['files'][str(p.relative_to(ROOT))]=W.sha(p)
    fr.update(experiment=HERE.name, parent_freeze_sha256=W.sha(source), task_assets=assets,
              task_asset_bytes=sum((ROOT/p).stat().st_size for p in assets),
              limits={s:limits(s) for s in CAP},model_forwards=0)
    W.write(output,fr,immutable=True)
    print(json.dumps({'status':'passed','assets':len(assets),'limits':fr['limits']}))


def authorize(path,stage,output=None):
    # Reuse the audited authorization/budget/attempt accounting in this process only.
    N.HERE,N.CAP,N.TOTAL_CAP,N.STORAGE=HERE,CAP,TOTAL_CAP,STORAGE
    a,fr,prior=N.authorize(path,stage,output)
    assert not any(p.name.startswith('formal-') for p in (HERE/'runs').glob('*') if p.is_dir()), 'one formal attempt only'
    assert fr['experiment']==HERE.name and fr['limits']=={s:limits(s) for s in CAP}
    return a,fr,prior


class Meter(R.RunMeter):
    def __enter__(self):
        super().__enter__();forward=self.V.L.forward
        cap=limits(self.receipt['stage'])['model_forwards']
        def bounded(*args,**kwargs):
            assert self.receipt['attempted_model_forward_calls']<cap
            return forward(*args,**kwargs)
        self.V.L.forward=bounded
        return self


def project_seconds(maxima,V):
    led=V.LVKR.ledger();n=limits('formal')
    units=dict(load=1,setup=1,formation_overhead=n['receivers'],receiver_finalize=n['receivers'],
               prefix_token=sum(v['plan']['b']+1 for v in led.values()),
               formation_token=sum(2*(v['plan']['e']-v['plan']['p']+1) for v in led.values()),
               pair_total=n['pairs'],integrity=1,finalize=1)
    assert set(units)<=set(maxima)
    return 1.25*sum(units[k]*maxima[k] for k in units)


def execute(engine,V,stage,output,rc,meter,fr):
    import torch
    from rcs_hooks import CapturingWriteHook
    from tg_hooks import TaskControls,task_forward
    from tg_analysis import projection
    t=time.monotonic(); items,tables=panel(stage);refs,_=W.references();led=V.LVKR.ledger()
    contexts=V.exp.contexts_for(engine.tokenizer,[led[r]['item'] for r in items])
    types=V.L.layer_types(engine.model)
    assert tuple(V.B.g_layers(types,V.SPLIT))==K.G
    assert tuple(engine.stop_ids)==tuple(V.STOP)==(248044,248046)
    V.KRDR.QHOOK_ORIG[0]=V.gdn_module().torch_recurrent_gated_delta_rule
    V.F.hook_baseline(engine.model)
    engine.model.requires_grad_(False)
    modules={l:V.L.model_layers(engine.model)[l].linear_attn.norm for l in K.G}
    assert all(not p.requires_grad for p in engine.model.parameters())
    meter.add('setup',time.monotonic()-t)
    counts=rc['counts'];records=[]
    def save(rel,body,tensor=False):
        p=output/rel;p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists()
        if tensor:torch.save(body,p)
        else:W.write(p,body,immutable=True)
        rc['files'][rel]=W.sha(p);rc['bytes']+=p.stat().st_size
        assert N.tree_bytes(HERE/'runs')<=STORAGE
        W.write(output/'receipt.json',rc)
    def backward_started():
        assert rc['backward_calls']<limits(stage)['backwards']
        rc['backward_calls']+=1
    for r,item in items.items():
        with meter.overhead('formation_overhead'):
            meter.phase='formation'
            cal,_=V.QCR.nq_calibration(item['scenario']+'-ABC-A')
            clean,ts,info=V.form_new(engine,led[r],contexts,cal,{K.MAIN:V.conditions()[K.MAIN]},counts)
            tok=led[r]['tokens']
            assert info['code_tokens']=={info['item']['target']:tok['target_second'],**dict(zip(info['item']['distractors'],tok['distractor_second']))}
            assert all(info['hashes'][k]==refs[r]['formation_hashes'][k] for k in info['hashes'])
            hybrid=V.SP.compose(ts[K.MAIN],V.TG['OO'],{'oc':clean})
            V.SP.check_arm(hybrid,ts[K.MAIN],V.TG['OO'],{'oc':clean},types,r)
            backgrounds={'C':clean,'H':hybrid};del ts
            bg_hash={b:V.comp_sha(c,types,V.ALLK,0) for b,c in backgrounds.items()}
        for donor in tables[r]:
            start=time.monotonic();d=donor['id'];rel=f'packages/{r}/{d}-H.pt'
            assert W.sha(N.OLD/rel)==fr['packages'][rel]
            package=torch.load(N.OLD/rel,map_location='cpu',weights_only=True)
            old=W.read(NGU_OLD/f'records/{r}/{d}.json')
            record=dict(receiver=r,donor=d,scenario=item['scenario'],source_record=str((NGU_OLD/f'records/{r}/{d}.json').relative_to(ROOT)))
            gradients={};physical={};hook=None;wh=None
            try:
                for b,cache in backgrounds.items():
                    wh=CapturingWriteHook(V,engine.model,package=package['delta'])
                    meter.phase='pair_t1'
                    c1,z1=V.fwd(engine,copy.deepcopy(cache),info['last'],info['n']-1,counts,'t1',wh)
                    snap=W.snapshot(V,c1,z1,types);record[b+'_t1_snapshot']=snap
                    W.identical(snap,old['meta']['t1'][b]['snapshot'])
                    for l in K.G:
                        for k in ('J_sha256','native_state_sha256','state_sha256'):
                            assert wh.records[l][k]==old['meta']['t1'][b]['layers'][str(l)][k]
                    rc['arm_counts']['t1']+=1
                    tr=old[b+'11'];tx=old[b+'X'];prefix=tr['t2']['prefix_ids']
                    assert prefix==tx['t2']['prefix_ids']==[int(z1.argmax())]
                    assert tr['t2']['mapping_valid'] and tx['t2']['mapping_valid']
                    tokens=tr['t2']['candidate_token_ids'];assert tokens==tx['t2']['candidate_token_ids']
                    assert tokens==[info['code_tokens'][code] for code in item['listed_codes']]
                    y=item['listed_codes'].index(item['target']);dr=donor['row'];assert y!=dr
                    record[b+'_score_contract']=dict(prefix=prefix,position=info['n'],candidate_tokens=tokens,target_row=y,donor_row=dr)
                    c1_sha=V.comp_sha(c1,types,V.ALLK,0)
                    npath=N.RCS_OLD/f'tensors/{r}/{d}-{b}11-t2.pt'
                    xpath=NGU_OLD/f'tensors/{r}/{d}-{b}X-t2.pt'
                    for p in (npath,xpath):assert W.sha(p)==fr['task_assets'][str(p.relative_to(ROOT))]
                    native=torch.load(npath,map_location='cpu',weights_only=True)
                    changed=torch.load(xpath,map_location='cpu',weights_only=True)
                    physical[b]={l:changed[l]['patch'].double()-changed[l]['native'].double() for l in K.G}
                    outputs={}
                    for cell,ref in [('native',tr),('frozen',tx)]:
                        expected={l:(native[l]['native_norm'] if cell=='native' else changed[l]['native']) for l in K.G}
                        hook=TaskControls(modules,expected,None if cell=='native' else physical[b])
                        meter.phase=cell+'_t2'
                        out,z,g=task_forward(V,engine.model,copy.deepcopy(c1),prefix[0],info['n'],hook,tokens[y],tokens[dr],backward_started)
                        if g is not None:gradients[b]=g
                        actual={'full_logits_sha256':V.F.th(z),'candidate_logits':[float(z[i]) for i in tokens],
                                'stop_logits':{str(i):float(z[i]) for i in V.STOP},'flow':hook.flow}
                        # Save actual values before any endpoint bridge can fail.
                        save(f'raw/{r}/{d}-{b}-{cell}.json',actual)
                        assert actual['full_logits_sha256']==ref['answer']['N']['t2_sha'],('full logits bridge',b,cell)
                        assert actual['candidate_logits']==ref['t2']['candidate_logits']
                        assert actual['stop_logits']==ref['t2']['stop_logits']
                        for l in K.G:
                            expected_patch=native[l]['native_norm'] if cell=='native' else changed[l]['patch']
                            assert torch.equal(hook.tensors[l]['patch'],expected_patch),('patch bridge',b,cell,l)
                        assert V.comp_sha(c1,types,V.ALLK,0)==c1_sha,'cross-arm cache mutation'
                        outputs[cell]=actual;rc['arm_counts'][cell+'_t2']+=1
                        if cell=='native':gradients[b]=g
                        del out,z,hook
                        hook=None
                    ln=outputs['native']['candidate_logits'];lx=outputs['frozen']['candidate_logits']
                    observed=(lx[dr]-lx[y])-(ln[dr]-ln[y])
                    record[b]=dict(observed=observed if b=='C' else -observed, endpoints=outputs, t1_snapshot=snap)
                    save(f'gradients/{r}/{d}-{b}.pt',gradients[b],tensor=True)
                    del native,changed,c1,z1,wh
                    wh=None
                record['projection']=projection(gradients,physical)
                save(f'records/{r}/{d}.json',record);records.append(record)
            except BaseException:
                save(f'failures/{r}/{d}.pt',{'hook_tensors':getattr(hook,'tensors',{}),
                     'hook_flow':getattr(hook,'flow',{}),'logits':getattr(hook,'logits',None),
                     'score':getattr(hook,'score',None),'current_gradients':getattr(hook,'gradients',None),'t1_records':getattr(wh,'records',{}),'t1_states':getattr(wh,'states',{}),
                     'record':record,'gradients':gradients},tensor=True)
                raise
            meter.add('pair_total',time.monotonic()-start)
            print('pair',len(records),'/',limits(stage)['pairs'],r,d,'seconds',round(time.monotonic()-start,2),flush=True)
            del package,gradients,physical,record
        t=time.monotonic()
        assert all(V.comp_sha(c,types,V.ALLK,0)==bg_hash[b] for b,c in backgrounds.items())
        meter.add('receiver_finalize',time.monotonic()-t)
        del backgrounds,clean,hybrid,cache
    lim=limits(stage)
    assert all(rc['arm_counts'][k]==lim[k] for k in rc['arm_counts'])
    assert rc['backward_calls']==lim['backwards']
    assert all(counts[k]==lim[k] for k in ('formations','prefix_prefills','t1'))
    assert counts['formation_token_forwards']==sum(2*(led[r]['plan']['e']-led[r]['plan']['p']+1) for r in items)
    assert counts['trajectories']==counts['n_steps']==0
    assert all(p.grad is None for p in engine.model.parameters())
    return records


def worker(args):
    a,fr,prior=authorize(args.authorization,args.stage,args.output)
    assert os.environ.get('TG_SUPERVISOR_PID')==str(os.getppid())
    V=W.runtime()
    import torch
    sys.path.insert(0,str(V.T1.SOURCE))
    from control_engine import ControlEngine
    output=Path(args.output).resolve();output.mkdir(parents=True,exist_ok=False)
    start=time.monotonic()
    rc=dict(status='running',stage=args.stage,pid=os.getpid(),gpu=args.gpu,
        counts={k:0 for k in V.COUNT_KEYS},arm_counts={k:0 for k in ('t1','native_t2','frozen_t2')},
        backward_calls=0,attempted_model_forward_calls=0,files={},bytes=0,prior_bytes=prior,
        freeze_sha256=a['freeze_sha256'],authorization_sha256=W.sha(args.authorization),natural_answers=0)
    W.write(output/'authorization.json',a,immutable=True);W.write(output/'receipt.json',rc)
    try:
        source=W.read(V.T1.SOURCE/'contract.json')['source']
        engine=ControlEngine(source['model_path'],V.exp.model_spec(),f'cuda:{args.gpu}')
        V.exp.metadata_check(engine);W.check_model_assets(V.exp.model_assets(),fr['model_assets'])
        W.write(output/'metadata.json',engine.metadata,immutable=True)
        meter=Meter(V,args.gpu,rc);meter.add('load',time.monotonic()-start)
        with meter:records=execute(engine,V,args.stage,output,rc,meter,fr)
        t=time.monotonic();rc['integrity']=engine.verify_unchanged()
        assert rc['integrity']['hooks_removed']
        assert rc['integrity']['target_weight_sha256_after']==engine.metadata['target_weight_sha256_before']
        W.check_files(fr);meter.add('integrity',time.monotonic()-t)
        t=time.monotonic()
        assert all(W.sha(output/p)==h for p,h in rc['files'].items())
        # Engineering endpoints/gradients are inspected numerically; scientific calibration
        # is released only after the unchanged formal panel has completed.
        if args.stage=='formal':
            from tg_analysis import analyse
            W.write(output/'analysis.json',analyse(records),immutable=True)
            rc['files']['analysis.json']=W.sha(output/'analysis.json')
        meter.add('finalize',time.monotonic()-t)
        rc.update(status='completed',timing_maxima=meter.maxima,peak_memory_bytes=torch.cuda.max_memory_allocated(args.gpu))
    except BaseException:
        rc.update(status='failed',error=traceback.format_exc());raise
    finally:
        rc['wall_seconds']=time.monotonic()-start;W.write(output/'receipt.json',rc)
    if args.stage=='engineering':
        seconds=project_seconds(rc['timing_maxima'],V)
        measured=N.tree_bytes(output)
        estimated=math.ceil(1.25*measured*168/20)
        gate=seconds<=CAP['formal'] and N.tree_bytes(HERE/'runs')+estimated<=STORAGE
        W.write(output/'verification.json',dict(status='passed',budget_gate='passed' if gate else 'blocked',
            freeze_sha256=a['freeze_sha256'],formal_seconds_estimate=seconds,formal_bytes_estimate=estimated,
            receipt_path=str((output/'receipt.json').relative_to(HERE)),receipt_sha256=W.sha(output/'receipt.json')),immutable=True)


def launch(args):
    import fcntl
    authorize(args.authorization,args.stage,args.output)
    with open('/tmp/acupuncture-task-gradient-01.lock','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        authorize(args.authorization,args.stage,args.output)
        query=['nvidia-smi',f'--id={args.gpu}']
        assert not subprocess.check_output(query+['--query-compute-apps=pid','--format=csv,noheader,nounits'],text=True).strip(),'GPU occupied'
        free=int(subprocess.check_output(query+['--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True).strip());assert free>=24576
        output=Path(args.output).resolve();assert not output.exists();output.parent.mkdir(parents=True,exist_ok=True)
        assert shutil.disk_usage(output.parent).free>=STORAGE
        command=[sys.executable,str(Path(__file__).resolve()),'_worker','--stage',args.stage,'--gpu',str(args.gpu),'--authorization',str(Path(args.authorization).resolve()),'--output',str(output)]
        start=time.monotonic()
        with output.with_suffix('.log').open('x') as log:
            p=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'TG_SUPERVISOR_PID':str(os.getpid())})
            try:
                while p.poll() is None:
                    if time.monotonic()-start>CAP[args.stage] or N.tree_bytes(HERE/'runs')>STORAGE:
                        raise RuntimeError('hard time/storage limit reached')
                    time.sleep(5)
            finally:
                if p.poll() is None:
                    p.terminate()
                    try:p.wait(timeout=10)
                    except subprocess.TimeoutExpired:p.kill();p.wait()
                output.mkdir(exist_ok=True)
                elapsed=time.monotonic()-start
                W.write(output/'exit.json',dict(returncode=p.returncode,supervisor_wall_seconds=elapsed,command=command),immutable=True)
                if p.returncode!=0:
                    path=output/'receipt.json';failed=W.read(path) if path.exists() else {'stage':args.stage,'files':{}}
                    failed.update(status='failed',wall_seconds=max(failed.get('wall_seconds',0.),elapsed),supervisor_returncode=p.returncode)
                    W.write(path,failed)
        assert p.returncode==0,('worker failed; evidence retained',p.returncode)


def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    f=sub.add_parser('freeze');f.add_argument('--output',required=True)
    for name in ('run','_worker'):
        x=sub.add_parser(name);x.add_argument('--stage',choices=CAP,required=True);x.add_argument('--gpu',type=int,required=True);x.add_argument('--authorization',required=True);x.add_argument('--output',required=True)
    a=p.parse_args()
    if a.command=='freeze':freeze(a.output)
    elif a.command=='run':launch(a)
    else:worker(a)


if __name__=='__main__':main()
