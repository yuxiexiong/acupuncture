"""Local Astra editor + remote broker. Formal search is disabled without explicit authorization."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
import time

HERE=Path(__file__).resolve().parent
CLI='/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex'
EXPLAIN='EXPLAIN EVERY STEP. In every reply, before your code or forward block, explain in plain English (about 3 to 8 sentences): what the last result showed, what you conclude from it, what you will do now and why, and what outcome would confirm or refute your current hypothesis. In your final answer, also summarize the path that led to your edits. These explanations are read by the experimenters.'
ENGINEERING='''This is an engineering integration test, NOT a weight search. Use no native tools. Reply with one python or forward fenced block for the remote executor. Do not inspect weights, practice data or modify weights. Step 1: Python set probe_value=41 and write /work/notes.md containing ENGINEERING_ONLY. Step 2 after the result: Python assert probe_value+1==42; assert tok.encode("2 + 2").ids and tok.encode("2 + 2").offsets; print PERSISTENCE_OK. Step 3: forward JSON {"type":"teacher_forced","model":"original","texts":["2 + 2 = 4"],"return":{"token_logprobs":true,"hidden_states":[0]}}. After success reply exactly ENGINEERING_COMPLETE without code. If an operation fails, report the failure without attempting research.'''


def parse_action(text, explanations=False):
    blocks=list(re.finditer(r'^```(python|forward)\s*\n(.*?)^```\s*$',text,re.M|re.S))
    if not blocks:
        if '```' in text: raise ValueError('Malformed or unsupported fenced block')
        return None
    if len(blocks)!=1 or text.count('```')!=2:
        raise ValueError('Exactly one action block is required')
    b=blocks[0]
    if explanations and not text[:b.start()].strip():
        raise ValueError('Missing explanation before action block')
    if text[b.end():].strip() or (not explanations and text[:b.start()].strip()):
        raise ValueError('Unexpected text outside action block')
    if b[1]=='python': return {'kind':'python','code':b[2]}
    value=json.loads(b[2])
    if not isinstance(value,dict): raise ValueError('Forward JSON must be an object')
    return {'kind':'forward','request':value}


def editor_turn(prompt, out, cwd, thread=None):
    out.mkdir()
    (out/'prompt.txt').write_text(prompt)
    instructions=cwd/'instructions.txt'
    instructions.write_text("Answer the user's request.\n")
    cmd=[CLI,'exec','--ignore-user-config','--ignore-rules','--strict-config','--skip-git-repo-check',
         '--json','-s','read-only','-C',str(cwd),'-m','gpt-6-astra','-c','model_reasoning_effort="max"',
         '-c','model_context_window=872000','-c','model_auto_compact_token_limit=1000000',
         '-c','project_doc_max_bytes=0','-c','web_search="disabled"','-c',f'model_instructions_file={json.dumps(str(instructions))}']
    for feature in ['shell_tool','code_mode','code_mode_host','apps','plugins','hooks','memories','multi_agent',
                    'browser_use','computer_use','image_generation','view_image','skill_search','goals','artifact']:
        cmd += ['--disable',feature]
    for feature in ['skip_host_skill_discovery','omit_skill_descriptions']: cmd += ['--enable',feature]
    if thread: cmd += ['resume',thread,'-']
    else: cmd += ['-']
    (out/'command.json').write_text(json.dumps(cmd,indent=2))
    started=time.time()
    with open(out/'events.jsonl','w') as stdout, open(out/'stderr.txt','w') as stderr:
        p=subprocess.run(cmd,input=prompt,text=True,stdout=stdout,stderr=stderr,timeout=1800)
    events=[json.loads(x) for x in (out/'events.jsonl').read_text().splitlines()]
    replies=[]; usage=None; found=None
    for e in events:
        if e['type']=='thread.started': found=e['thread_id']
        if e['type']=='turn.completed': usage=e.get('usage')
        item=e.get('item',{})
        if item.get('type') not in (None,'agent_message','reasoning','error'):
            raise RuntimeError('Unexpected native tool event; stop editor')
        if e['type']=='item.completed' and item.get('type')=='agent_message': replies.append(item['text'])
    if p.returncode or usage is None or not replies or (thread and found != thread):
        raise RuntimeError('Editor turn failed or wrong session resumed; inspect raw receipt')
    reply=replies[-1]
    (out/'reply.txt').write_text(reply)
    (out/'receipt.json').write_text(json.dumps({'thread':found,'usage':usage,'seconds':time.time()-started,'native_tool_events':0},indent=2))
    return reply,found


class Remote:
    def __init__(self,cfg,out):
        self.cfg=cfg;self.out=out;self.proc=None
        self.ssh=['ssh','-o','ConnectTimeout=20','-o','ServerAliveInterval=15',
                  '-o','ControlMaster=auto','-o','ControlPath=/tmp/acupuncture-wsp-fleet-%C',
                  '-o','ControlPersist=600',cfg['ssh_host']]
        self.cmd=self.ssh+[
             shlex.join(['sh',cfg['server_code']+'/server_env.sh',cfg['server_code']+'/broker.py','--config',cfg['server_config']])]
        self.log=open(out/'ssh.stderr.txt','a')
    def reconcile(self,action):
        """Read an already durable response; never dispatch an uncertain action again."""
        code='''import json,hashlib,fcntl,sys
from pathlib import Path
cfg=json.loads(Path(sys.argv[1]).read_text());r=Path(cfg['run_root']);a=json.loads(sys.argv[2]);p=r/'actions'/a['id'];busy=False
if (r/'broker.lock').exists():
 with (r/'broker.lock').open('a') as f:
  try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:busy=True
if (p/'response.json').exists():
 assert (p/'request.sha256').read_text()==hashlib.sha256(json.dumps(a,sort_keys=True).encode()).hexdigest(),'ACTION_IDENTITY_MISMATCH'
 print(json.dumps(dict(busy=busy,result=json.loads((p/'response.json').read_text()))))
else:print(json.dumps(dict(busy=busy,result=None)))'''
        deadline=time.monotonic()+7200
        while time.monotonic()<deadline:
            p=subprocess.run(self.ssh+[shlex.join(['python3','-c',code,self.cfg['server_config'],json.dumps(action)])],capture_output=True,text=True,timeout=40)
            if p.returncode==255:time.sleep(5);continue
            if p.returncode:raise RuntimeError('RECONCILIATION_FAILED: '+p.stderr[-2000:])
            value=json.loads(p.stdout)
            if value['busy']:time.sleep(5);continue
            if value['result'] is None:raise RuntimeError('INCOMPLETE_ACTION: no saved result; do not replay')
            result=value['result']
            if result.get('id')!=action['id']:raise RuntimeError('Saved response identity mismatch')
            result['transport_reconnected']=True
            (self.out/('reconciled-'+action['id']+'.json')).write_text(json.dumps(result,indent=2))
            return result
        raise RuntimeError('TRANSPORT_RECOVERY_EXPIRED: uncertain action preserved')
    def call(self,action):
        if self.proc is None:
            self.proc=subprocess.Popen(self.cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.log,text=True,bufsize=1)
        try:
            self.proc.stdin.write(json.dumps(action)+'\n'); self.proc.stdin.flush()
            line=self.proc.stdout.readline()
        except (BrokenPipeError,OSError):line=''
        if not line:
            self.disconnect()
            return self.reconcile(action)
        result=json.loads(line)
        if result.get('id')!=action['id']: raise RuntimeError('Broker response identity mismatch')
        return result
    def disconnect(self):
        if self.proc is None:return
        try:self.proc.stdin.close()
        except (BrokenPipeError,OSError):pass
        try: self.proc.wait(timeout=30)
        except subprocess.TimeoutExpired: self.proc.terminate(); self.proc.wait(timeout=10)
        self.proc=None
    def close(self):
        self.disconnect()
        self.log.close()


def authorize(cfg):
    if cfg['mode']=='engineering':
        if cfg['turn_limit']>6: raise ValueError('engineering editor probe is limited to six turns')
        return
    if cfg['mode']!='search' or not cfg.get('authorized',False):
        raise ValueError('FORMAL_SEARCH_DISABLED: explicit user authorization required')
    if not cfg.get('authorization_record') or not cfg.get('acceptance_receipt_sha256'):
        raise ValueError('formal launch requires recorded approval and accepted engineering receipt')


def accepted_editor_retry(out, turn, directory):
    """Use one already accepted, identical retry; this function never calls the editor."""
    original=out/f'turn-{turn:03d}';retry=Path(directory)
    if (out/f'turn-{turn+1:03d}').exists() or any((original/name).exists() for name in ('reply.txt','tool_result.json','receipt.json')):
        raise ValueError('EDITOR_RETRY_ALREADY_CONSUMED')
    events=[json.loads(line) for line in (original/'events.jsonl').read_text().splitlines()]
    if not any(e['type']=='turn.failed' for e in events):raise ValueError('NO_FAILED_EDITOR_TURN')
    if (original/'prompt.txt').read_bytes()!=(retry/'prompt.txt').read_bytes():raise ValueError('RETRY_PROMPT_CHANGED')
    receipt=json.loads((retry/'receipt.json').read_text())
    if receipt['thread']!=json.loads((out/f'turn-{turn-1:03d}'/'receipt.json').read_text())['thread']:
        raise ValueError('RETRY_THREAD_CHANGED')
    if receipt['native_tool_events']!=0:raise ValueError('RETRY_USED_NATIVE_TOOLS')
    reply=(retry/'reply.txt').read_text()
    if parse_action(reply,explanations=turn>=29) is None:raise ValueError('RETRY_HAS_NO_ACTION')
    return reply,dict(receipt,accepted_retry_directory=str(retry))


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config',required=True); ap.add_argument('--check',action='store_true')
    args=ap.parse_args(); cfg=json.loads(Path(args.config).read_text()); authorize(cfg)
    if args.check: print('CONFIG_GATE_OK'); return
    out=Path(cfg['local_run_root']);resume=cfg.get('resume_completed_turn',0);editor_resume=cfg.get('resume_editor_turn',0)
    if resume and editor_resume:raise ValueError('AMBIGUOUS_RESUME')
    if resume or editor_resume:
        original=json.loads((out/'config.json').read_text())
        if original!={k:v for k,v in cfg.items() if k not in ('resume_completed_turn','resume_editor_turn','accepted_editor_retry')}:raise ValueError('RESUME_CONFIG_CHANGED')
        if resume and any(out.glob(f'turn-{resume+1:03d}')):raise ValueError('NEXT_TURN_ALREADY_EXISTS')
        if editor_resume:cached_reply,cached_receipt=accepted_editor_retry(out,editor_resume,cfg['accepted_editor_retry'])
    else:
        out.mkdir(parents=True,exist_ok=False)
        (out/'config.json').write_text(json.dumps(cfg,indent=2))
    cwd=Path(tempfile.mkdtemp(prefix='wsp-clean-editor-'))
    remote=Remote(cfg,out); thread=None; previous=''; successes=0; nudges=0; explanation_retries=0
    initial=ENGINEERING if cfg['mode']=='engineering' else Path(cfg['initial_prompt']).read_text()
    try:
        if editor_resume:
            thread=cached_receipt['thread']
            response=json.loads((out/f'turn-{editor_resume-1:03d}'/'tool_result.json').read_text())
            successes=response['state']['forward_success']
        if resume:
            d=out/f'turn-{resume:03d}'
            if (d/'tool_result.json').exists():raise ValueError('RESUME_RESULT_ALREADY_DELIVERED')
            action=parse_action((d/'reply.txt').read_text(),explanations=resume>=29);action['id']=d.name
            response=remote.reconcile(action)
            (d/'tool_result.json').write_text(json.dumps(response,indent=2))
            thread=json.loads((d/'receipt.json').read_text())['thread'];successes=response['state']['forward_success']
            previous='Recovered a saved action response, without rerunning the action. Python kernel variables are lost; /work files persist.\n'+response['editor_output']
            previous+=f'\nSuccessful forward passes: {successes}; Python calls: {response["state"]["python_attempts"]}.'
        for turn in range(editor_resume or resume+1,cfg['turn_limit']+1):
            prompt=initial if turn==1 else previous
            if cfg['mode']=='search':
                if turn==29: prompt+='\n[note from the experimenters: a new instruction for the rest of the session]\n'+EXPLAIN
                if turn in (46,51):
                    file='001_pass_size.txt' if turn==46 else '002_tool_facts.txt'
                    notice=(HERE/'notices'/file).read_text()
                    if cfg.get('profile')=='4b' and turn==51:
                        notice=notice.replace('3, 7, 11, 15, 19, 23','3, 7, 11, 15, 19, 23, 27, 31')
                    prompt+='\n'+notice
                if turn>1 and (turn-1)%40==0:
                    context=remote.call({'id':f'context-{turn}','kind':'status'})
                    thread=None
                    prompt=initial+'\n'+EXPLAIN+'\nSESSION HANDOFF (your own notes and files):\n'+context['editor_output']+'\nLast tool result:\n'+previous
            if turn==editor_resume:
                reply=cached_reply
                (out/f'turn-{turn:03d}'/'reply.txt').write_text(reply)
                (out/f'turn-{turn:03d}'/'receipt.json').write_text(json.dumps(cached_receipt,indent=2))
            else:reply,thread=editor_turn(prompt,out/f'turn-{turn:03d}',cwd,thread)
            try: action=parse_action(reply,explanations=(cfg['mode']=='search' and turn>=29))
            except (ValueError,json.JSONDecodeError) as e:
                if str(e)=='Missing explanation before action block':
                    explanation_retries+=1
                    if explanation_retries>2:raise RuntimeError('missing explanation after two reminders')
                    previous=EXPLAIN+'\nYour action block was not executed. Please include an explanation before resubmitting it.'
                    continue
                previous='Invalid response: '+str(e); nudges+=1
                if nudges>10: raise RuntimeError('too many invalid replies')
                continue
            explanation_retries=0
            if action is None:
                if cfg['mode']=='engineering':
                    if successes!=1 or reply.strip()!='ENGINEERING_COMPLETE': raise RuntimeError('engineering probe ended prematurely')
                    break
                if successes>=50:
                    final=remote.call({'id':'final-submission','kind':'finalize'})
                    (out/'final-submission.json').write_text(json.dumps(final,indent=2))
                    if final['failed']: raise RuntimeError('final edit validation failed')
                    break
                previous='The session continues until all 50 successful forward passes are used. Reply with one action block.'
                nudges+=1
                if nudges>10: raise RuntimeError('too many early final replies')
                continue
            action['id']=f'turn-{turn:03d}'
            response=remote.call(action)
            (out/f'turn-{turn:03d}'/'tool_result.json').write_text(json.dumps(response,indent=2))
            successes=response['state']['forward_success']
            previous=response['editor_output']
            if response.get('transport_reconnected'):previous='Transport recovered without rerunning the action. Python kernel variables are lost; /work files persist.\n'+previous
            if response.get('kernel_restarted'): previous='Python kernel (re)started: variables from a previous kernel are lost; /work files persist.\n'+previous
            previous+=f'\nSuccessful forward passes: {successes}; Python calls: {response["state"]["python_attempts"]}.'
            if any(x in previous for x in ('GPU_BUSY','STORAGE_LOW','INCOMPLETE_ACTION','budget exhausted','safety limit')): raise RuntimeError(previous)
        else: raise RuntimeError('turn limit reached; stopped without completing the session')
        (out/'receipt.json').write_text(json.dumps({'status':'passed' if cfg['mode']=='engineering' else 'completed',
            'mode':cfg['mode'],'turns':turn,'forward_success':successes,'last_thread':thread,'formal_search_started':cfg['mode']=='search'},indent=2))
    finally: remote.close()


if __name__=='__main__': main()
