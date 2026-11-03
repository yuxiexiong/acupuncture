"""Full-size synthetic scheduling fixtures; never import a model or read benchmark data."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from ledger import Ledger,authorize,write
import protocol as P
import editor


def config(root,scenario='positive'):
    return dict(mode='fixture',backend='fixture',profile='0p8b',data_root=None,authorized=False,
                run_root=str(root),scenario=scenario,reserve_free_bytes=0,new_data_bytes_cap=1000000000,spent={},
                caps=dict(gpu_seconds=14400,gpu_A=1800,gpu_B=5400,gpu_C=7200,samples=3008,output_tokens=52957184,
                          tf_tokens=2000000,editor_turns=100,editor_input_tokens=1500000,editor_output_tokens=150000,cpu_seconds=216000))


class FixtureBackend:
    def __init__(self,cfg):
        assert cfg['mode']=='fixture' and cfg['data_root'] is None
        self.cfg=cfg;self.calls=0
        self.panels={p:[dict(task_id=str(i),user='SYNTHETIC f(x)=x+1') for i in range(n)] for p,n in [('D',128),('S',32),('V',64),('T',164),('M',64)]}
    def locate_tokens(self,req):return 64
    def perform(self,req,out):
        self.calls+=1
        if self.cfg.get('delay'):time.sleep(self.cfg['delay'])
        if req['op']=='labels':
            a=[dict(key=r['key'],sample=r['sample'],labels=['state_update'],evidence='return x',reason='Synthetic return omits increment; failing assertion is known.') for r in req['payload']['records'] if not r['correct']]
            return dict(annotations=a,rules=req['payload'].get('frozen_rule') or {c:'Synthetic '+c+' rule' for c in P.CATEGORIES},_usage=dict(editor_turns=1,editor_input_tokens=1,editor_output_tokens=1,cpu_seconds=0))
        if req['op']=='locate':
            return dict(supports=[dict(layer=i,channels=list(range(n))) for i in (0,1) for n in (8,32)],pairs=req['diagnosis']['pairs'],calibration_tf_tokens=64,_usage=dict(tf_tokens=64,gpu_seconds=0,gpu_A=0,cpu_seconds=0))
        if req['op']=='calibrate':
            controls=P.random_supports(req['needle'],96)
            return dict(valid=True,controls=[dict(c,gain=.5,rms_ratio=1) for c in controls],_usage=dict(tf_tokens=64,gpu_seconds=0,gpu_B=0,cpu_seconds=0))
        rows=[]
        for key in req['keys']:
            for s in range(req['n']):
                correct=s==0 if req['n']==2 else int(key)%2==0
                if req['panel']=='D' and self.cfg['scenario']=='no_pairs':correct=False
                if req['panel']=='S' and req['gain']['layer']==1 and req['gain']['gain']==.5:correct=int(key)%4!=3
                if req['panel'] in ('V','T') and req['arm']=='needle' and self.cfg['scenario']!='negative_V':correct=s==0 or int(key)%2==0
                rows.append(dict(key=key,sample=s,correct=correct,text='</think>```python\ndef f(x): return x'+('+1' if correct else '')+'\n```',status='pass' if correct else 'test_failure',tests=['assert f(1)==2'],user='SYNTHETIC f(x)=x+1',unfinished=False))
        return dict(rows=rows,_usage=dict(samples=len(rows),output_tokens=len(rows)*8,gpu_seconds=0,**{'gpu_'+req['stage']:0},tf_tokens=0,cpu_seconds=0))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    import scheduler
    checks=[]
    def record(name):checks.append(name)
    c=config(a.out/'positive');b=FixtureBackend(c);r=scheduler.run(c,b);assert r['status']=='completed' and r['primary']['delta']>0
    original_calls=b.calls;r2=scheduler.run(c,b);assert r==r2 and b.calls==original_calls;record('full_D_S_V_T_M_and_idempotent_resume')
    for case in ('no_pairs','negative_V'):
        c=config(a.out/case,case);r=scheduler.run(c,FixtureBackend(c));assert r['status']=='stopped';record(case+'_stops_before_T')
    for role,panel,phase in [('diagnosis','V','D_LABEL'),('diagnosis','T','D_LABEL'),('diagnosis','M','D_LABEL'),('validation','D','V_LABEL'),('diagnosis','D','V_LABEL')]:
        try:editor.payload(role,panel,phase,[])
        except ValueError:pass
        else:raise AssertionError('access accepted')
    record('role_and_stage_denial')
    try:authorize(dict(mode='research',authorized=False))
    except ValueError as e:assert 'FORMAL_SEARCH_DISABLED' in str(e)
    else:raise AssertionError('research started')
    record('formal_gate_precedes_work')
    c=config(a.out/'budget');c['caps']['samples']=10
    try:scheduler.run(c,FixtureBackend(c))
    except RuntimeError as e:assert 'BUDGET_EXHAUSTED' in str(e)
    else:raise AssertionError('budget not enforced')
    record('budget_exhaustion')
    c=config(a.out/'uncertain');db=Ledger(c['run_root'],c)
    try:
        try:db.run('pending','D','D',{},dict(samples=1),lambda q,o:(_ for _ in ()).throw(RuntimeError('injected crash')))
        except RuntimeError:pass
        assert db.remaining()['samples']==3007
    finally:db.close()
    db=Ledger(c['run_root'],c)
    try:
        try:db.run('pending','D','D',{},dict(samples=1),lambda q,o:{})
        except RuntimeError as e:assert 'INCOMPLETE_ACTION' in str(e)
        else:raise AssertionError('unsafe replay')
    finally:db.close()
    record('uncertain_action_no_replay_and_reserved_budget')
    crash=config(a.out/'commit-crash');crash_file=a.out/'commit-crash-config.json';write(crash_file,crash)
    import os
    crashed=subprocess.run([sys.executable,str(Path(__file__).with_name('scheduler.py')),'--config',str(crash_file)],
                           env=dict(os.environ,WCP_TEST_CRASH_AFTER_RESULT='D-original-000'),capture_output=True,text=True)
    assert crashed.returncode==71
    db=Ledger(crash['run_root'],crash)
    try:db.recover_completed('D-original-000')
    finally:db.close()
    resumed=FixtureBackend(crash);result=scheduler.run(crash,resumed)
    assert result['status']=='completed' and resumed.calls==original_calls-1
    record('completed_result_reconciliation_without_rerun')
    c=config(a.out/'positive');db=Ledger(c['run_root'],c)
    try:
        try:db.run('attempt-to-reopen-V','V','V',{}, {},lambda q,o:{})
        except ValueError as e:assert 'STAGE_ORDER_DENIED' in str(e)
        else:raise AssertionError('V reopened')
        try:db.run('freeze-before-V','CALIBRATED','V',dict(changed=True),{},lambda q,o:{})
        except ValueError as e:assert 'ACTION_ID_CONTENT_CHANGED' in str(e)
        else:raise AssertionError('needle changed')
    finally:db.close()
    record('one_time_V_and_frozen_candidate')
    import numpy as np
    stats=dict(mean=np.zeros((8,2,2,64)),rms=np.ones((8,2,2,64)));stats['mean'][:,0,1,:8]=2
    supports=P.rank_supports(stats);assert supports[0]==dict(layer=1,channels=list(range(8)));record('support_ranking')
    assert P.evidence_valid('<EMPTY_RESPONSE>','');record('empty_response_is_labelable')
    result=dict(status='passed',scope='synthetic_control_flow_not_model_or_capability_evidence',checks=checks,full_positive_external_jobs=original_calls,new_gpu_seconds=0,new_model_generations=0,formal_search_started=False)
    write(a.out/'receipt.json',result);print(json.dumps(result))


if __name__=='__main__':main()
