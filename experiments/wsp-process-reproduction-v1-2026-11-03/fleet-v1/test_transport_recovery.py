"""Saved-result recovery is read-only and cannot replay a forward."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

source=Path(__file__).resolve().parent.parent/'engineering-r2/controller.py'
spec=importlib.util.spec_from_file_location('controller',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def main():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);checks=[]
    cfg=dict(mode='search',authorized=True,authorization_record='SYNTHETIC',acceptance_receipt_sha256='fixture',ssh_host='fixture',server_code='/fixture',server_config='/fixture/config',local_run_root=str(out/'run'),initial_prompt=str(out/'prompt.txt'),turn_limit=3)
    result=dict(id='turn-002',failed=False,state=dict(forward_success=50,python_attempts=1),editor_output='SYNTHETIC SAVED RESULT')
    action=dict(id='turn-002',kind='forward',request={})
    remote=m.Remote(cfg,out)
    responses=[dict(busy=True,result=None),dict(busy=False,result=result)]
    with patch.object(m.subprocess,'run',side_effect=[subprocess.CompletedProcess([],0,json.dumps(x),'') for x in responses]) as run,patch.object(m.time,'sleep'),patch.object(m.subprocess,'Popen') as spawn:
        assert remote.reconcile(action)['state']['forward_success']==50
        assert run.call_count==2 and spawn.call_count==0
    with patch.object(m.subprocess,'run',return_value=subprocess.CompletedProcess([],0,json.dumps(dict(busy=False,result=None)),'')):
        try:remote.reconcile(action)
        except RuntimeError as e:assert 'INCOMPLETE_ACTION' in str(e)
        else:raise AssertionError('missing result was replayed')
    remote.close();checks.append('wait_for_saved_result_without_dispatch_or_missing_result_replay')
    root=Path(cfg['local_run_root']);d=root/'turn-002';d.mkdir(parents=True)
    (root/'config.json').write_text(json.dumps(cfg));Path(cfg['initial_prompt']).write_text('SYNTHETIC')
    (d/'reply.txt').write_text('```forward\n{}\n```');(d/'receipt.json').write_text(json.dumps(dict(thread='original-thread')))
    resume=dict(cfg,resume_completed_turn=2);p=out/'resume.json';p.write_text(json.dumps(resume));calls=[]
    class FakeRemote:
        def __init__(self,*args):pass
        def reconcile(self,a):assert a['id']=='turn-002';calls.append('reconcile');return result
        def call(self,a):assert a['kind']=='finalize';calls.append('finalize');return dict(failed=False)
        def close(self):pass
    def editor(prompt,target,cwd,thread):
        assert thread=='original-thread' and 'SYNTHETIC SAVED RESULT' in prompt and 'variables are lost' in prompt
        calls.append('editor');return 'FINAL','original-thread'
    with patch.object(m,'Remote',FakeRemote),patch.object(m,'editor_turn',editor),patch.object(sys,'argv',['controller','--config',str(p)]):m.main()
    assert calls==['reconcile','editor','finalize'];assert json.loads((root/'receipt.json').read_text())['forward_success']==50
    checks.append('resume_original_thread_counter_and_saved_result_without_forward')
    (out/'receipt.json').write_text(json.dumps(dict(status='passed',checks=checks,new_gpu_seconds=0,scope='synthetic_transport_only'),indent=2));print((out/'receipt.json').read_text())


if __name__=='__main__':main()
