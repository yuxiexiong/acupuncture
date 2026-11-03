"""Real controller code with synthetic tools; zero model, GPU or research-data calls."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch
import fleet


def math_child(profile,out):
    spec=importlib.util.spec_from_file_location('math_controller',fleet.MATH/'controller.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    class Remote:
        def __init__(self,*args):self.count=0
        def call(self,action):
            if action['kind']=='forward':self.count+=1
            return dict(id=action['id'],failed=False,editor_output='SYNTHETIC',state=dict(forward_success=self.count,python_attempts=0))
        def close(self):pass
    turns=[]
    def turn(prompt,path,cwd,thread):
        path.mkdir();(path/'prompt.txt').write_text(prompt)
        turns.append(prompt)
        if len(turns)==51:return 'SYNTHETIC FINAL','fixture'
        prefix='Synthetic explanation.\n' if len(turns)>=29 else ''
        return prefix+'```forward\n{"type":"teacher_forced","model":"original","texts":["SYNTHETIC"]}\n```','fixture'
    initial=out/'initial.txt';initial.write_text('SYNTHETIC ONLY')
    cfg=dict(mode='search',profile=profile,authorized=True,authorization_record='FIXTURE ONLY: mocked tools',acceptance_receipt_sha256='fixture',local_run_root=str(out/'math'),initial_prompt=str(initial),turn_limit=60)
    path=out/'fixture.json';fleet.write(path,cfg)
    with patch.object(mod,'Remote',Remote),patch.object(mod,'editor_turn',turn),patch.object(sys,'argv',['controller','--config',str(path)]):mod.main()
    result=json.loads((out/'math/receipt.json').read_text());assert result['forward_success']==50 and len(turns)==51
    result.update(formal_search_started=False,scope='synthetic_tools_actual_math_controller',new_gpu_seconds=0)
    if profile=='4b':result.update(status='stopped',reason='synthetic_negative_outcome_for_queue')
    fleet.write(out/'receipt.json',result)


def child(name,out):
    out.mkdir(parents=True,exist_ok=True)
    if name.startswith('math-'):math_child(name.split('-')[1],out);return
    if name=='coding-0p8b':raise RuntimeError('INJECTED_ENGINEERING_FAILURE_NO_REPLAY')
    sys.path.insert(0,str(fleet.CODING))
    spec=importlib.util.spec_from_file_location('coding_fixture',fleet.CODING/'acceptance.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    import scheduler
    cfg=mod.config(out/'coding');cfg['profile']='4b';result=scheduler.run(cfg,mod.FixtureBackend(cfg))
    result.update(scope='synthetic_backend_actual_coding_scheduler',formal_search_started=False,new_gpu_seconds=0)
    fleet.write(out/'receipt.json',result)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--child');a=ap.parse_args()
    if a.child:child(a.child,a.out);return
    a.out.mkdir(parents=True,exist_ok=False);checks=[]
    cfg=dict(mode='fixture',authorized=False,root=str(a.out/'queue'),jobs=[dict(id=name) for name in fleet.ORDER])
    result=fleet.run(cfg,fixture=True)
    assert [j['id'] for j in result['jobs']]==fleet.ORDER
    assert [j['status'] for j in result['jobs']]==['completed','negative_or_no_target','skipped_engineering','completed']
    assert all(b['started']>=a['ended'] for a,b in zip(result['jobs'],result['jobs'][1:]));checks.append('ordered_complete_negative_failure_then_next')
    logs={p:str(p.stat().st_mtime_ns) for p in Path(cfg['root']).glob('*/process.log')}
    assert fleet.run(cfg,fixture=True)==result and logs=={p:str(p.stat().st_mtime_ns) for p in logs};checks.append('resume_does_not_repeat_finished_or_failed_jobs')
    bad=dict(cfg,mode='research',authorized=False,root=str(a.out/'denied'))
    try:fleet.run(bad)
    except ValueError as e:assert 'FORMAL_SEARCH_DISABLED' in str(e)
    else:raise AssertionError('formal gate absent')
    assert not Path(bad['root']).exists();checks.append('formal_denied_before_work')
    replies=[subprocess.CompletedProcess([],255,'','disconnect'),subprocess.CompletedProcess([],0,'OK','')]
    with patch.object(fleet.subprocess,'run',side_effect=replies) as mocked,patch.object(fleet.time,'sleep'):
        assert fleet.ssh('read',readonly=True)=='OK' and mocked.call_count==2
    with patch.object(fleet.subprocess,'run',return_value=replies[0]) as mocked:
        try:fleet.ssh('mutate')
        except RuntimeError:pass
        else:raise AssertionError('unknown action replayed')
        assert mocked.call_count==1
    checks.append('read_reconnect_only_no_uncertain_action_replay')
    p=a.out/'remote-fixture.json';fleet.write(p,dict(run_root='/synthetic-only'))
    terminal=dict(status='completed');statuses=[dict(active=True,receipt=terminal),dict(active=False,receipt=terminal)]
    with patch.object(fleet,'upload'),patch.object(fleet,'ssh'),patch.object(fleet,'coding_status',side_effect=statuses),patch.object(fleet.time,'sleep') as sleeping:
        fleet.coding_child(p,a.out/'remote-fixture-receipt.json');assert sleeping.call_count==1
    checks.append('wait_for_remote_exit_before_advancing')
    interrupted=dict(cfg,root=str(a.out/'interrupted'))
    r=Path(interrupted['root']);r.mkdir();fleet.write(r/'config.json',interrupted)
    fleet.write(r/'state.json',dict(status='running',jobs=[dict(id='math-0p8b',status='running',started=0)],formal_search_started=False))
    resumed=fleet.run(interrupted,fixture=True)
    assert resumed['jobs'][0]['status']=='skipped_engineering' and resumed['jobs'][-1]['status']=='completed'
    checks.append('interrupted_unknown_action_skipped_then_queue_continues')
    fleet.write(a.out/'receipt.json',dict(status='passed',checks=checks,scope='synthetic_continuous_queue_actual_math_and_coding_controllers',formal_search_started=False,new_gpu_seconds=0,new_model_generations=0))
    print((a.out/'receipt.json').read_text())


if __name__=='__main__':main()
