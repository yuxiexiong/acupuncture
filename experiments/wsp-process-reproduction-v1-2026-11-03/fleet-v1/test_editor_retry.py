"""Accepted retry preserves the failed evidence and dispatches only the new action."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

source=Path(__file__).resolve().parent.parent/'engineering-r2/controller.py'
spec=importlib.util.spec_from_file_location('controller',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


with tempfile.TemporaryDirectory() as directory:
    root=Path(directory);out=root/'experiment';out.mkdir();retry=root/'retry';retry.mkdir()
    previous=out/'turn-005';previous.mkdir();failed=out/'turn-006';failed.mkdir()
    prompt='SYNTHETIC UNCHANGED REQUEST'
    for d in [failed,retry]:(d/'prompt.txt').write_text(prompt)
    (failed/'events.jsonl').write_text('{"type":"turn.failed"}\n')
    receipt=dict(thread='original-thread',native_tool_events=0)
    for d in [previous,retry]:(d/'receipt.json').write_text(json.dumps(receipt))
    (previous/'tool_result.json').write_text(json.dumps(dict(state=dict(forward_success=1))))
    (retry/'reply.txt').write_text('```forward\n{"type":"teacher_forced"}\n```')
    cfg=dict(mode='search',authorized=True,authorization_record='SYNTHETIC',acceptance_receipt_sha256='fixture',
             local_run_root=str(out),initial_prompt=str(root/'initial'),turn_limit=7)
    (out/'config.json').write_text(json.dumps(cfg));(root/'initial').write_text('SYNTHETIC')
    config=root/'config.json';config.write_text(json.dumps(dict(cfg,resume_editor_turn=6,accepted_editor_retry=str(retry))))
    (retry/'prompt.txt').write_text('CHANGED')
    try:m.accepted_editor_retry(out,6,retry)
    except ValueError as e:assert str(e)=='RETRY_PROMPT_CHANGED'
    else:raise AssertionError('changed retry accepted')
    (retry/'prompt.txt').write_text(prompt);calls=[]
    class Remote:
        def __init__(self,*args):pass
        def call(self,action):
            calls.append(action['id'])
            return dict(failed=False,state=dict(forward_success=50,python_attempts=4),editor_output='NEW RESULT')
        def close(self):pass
    def editor(prompt,target,cwd,thread):
        assert target.name=='turn-007' and thread=='original-thread' and 'NEW RESULT' in prompt
        return 'FINAL',thread
    with patch.object(m,'Remote',Remote),patch.object(m,'editor_turn',editor),patch.object(sys,'argv',['controller','--config',str(config)]):m.main()
    assert calls==['turn-006','final-submission']
    assert (failed/'events.jsonl').read_text()=='{"type":"turn.failed"}\n'
    try:m.accepted_editor_retry(out,6,retry)
    except ValueError as e:assert str(e)=='EDITOR_RETRY_ALREADY_CONSUMED'
    else:raise AssertionError('consumed retry accepted')
import resume_after_fleet as queued
with tempfile.TemporaryDirectory() as directory:
    root=Path(directory);wait=root/'fleet-state.json';wait.write_text('{"status":"running"}')
    fleet_config=root/'fleet-config.json';fleet_config.write_text('{"jobs":[]}')
    experiment=root/'experiment';experiment.mkdir();(experiment/'receipt.json').write_text('{"status":"completed"}')
    controller=root/'controller.json';controller.write_text(json.dumps(dict(local_run_root=str(experiment))))
    cfg=root/'recovery.json';cfg.write_text(json.dumps(dict(wait_state=str(wait),fleet_config=str(fleet_config),controller_config=str(controller),controller_sha256=queued.fleet.sha(queued.fleet.MATH/'controller.py'))))
    events=[]
    def sleep(seconds):events.append('wait');wait.write_text('{"status":"finished_with_skips"}')
    def idle(jobs):events.append('idle')
    class Child:
        pid=123
        def __init__(self,*args,**kwargs):events.append('launch')
        def wait(self):return 0
    with patch.object(queued.time,'sleep',sleep),patch.object(queued.fleet,'check_previous_idle',idle),patch.object(queued.subprocess,'Popen',Child):
        assert queued.run(cfg,root/'recovery')['status']=='completed'
    assert events==['wait','idle','launch']
    with patch.object(queued.fleet,'check_previous_idle',side_effect=RuntimeError('busy')),patch.object(queued.subprocess,'Popen') as launch:
        assert queued.run(cfg,root/'blocked')['status']=='blocked_engineering'
        launch.assert_not_called()
print(json.dumps(dict(status='passed',checks=['changed_prompt_rejected','new_action_only','original_thread_and_failure_preserved','consumed_retry_rejected','wait_then_check_idle_before_launch','busy_blocks_launch'],new_gpu_seconds=0)))
