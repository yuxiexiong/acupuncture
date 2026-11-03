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
    instructions.write_text('Follow the supplied experiment task. Do not use native tools. All actions must be emitted as the specified fenced text for an external executor.\n')
    cmd=[CLI,'exec','--ignore-user-config','--ignore-rules','--strict-config','--skip-git-repo-check',
         '--json','-s','read-only','-C',str(cwd),'-m','gpt-6-astra','-c','model_reasoning_effort="max"',
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
        cmd=['ssh','-o','ConnectTimeout=20','-o','ServerAliveInterval=15',cfg['ssh_host'],
             shlex.join(['sh',cfg['server_code']+'/server_env.sh',cfg['server_code']+'/broker.py','--config',cfg['server_config']])]
        self.log=open(out/'ssh.stderr.txt','a')
        self.proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.log,text=True,bufsize=1)
    def call(self,action):
        self.proc.stdin.write(json.dumps(action)+'\n'); self.proc.stdin.flush()
        line=self.proc.stdout.readline()
        if not line: raise RuntimeError('SSH broker disconnected; do not retry pending action automatically')
        result=json.loads(line)
        if result.get('id')!=action['id']: raise RuntimeError('Broker response identity mismatch')
        return result
    def close(self):
        self.proc.stdin.close()
        try: self.proc.wait(timeout=30)
        except subprocess.TimeoutExpired: self.proc.terminate(); self.proc.wait(timeout=10)
        self.log.close()


def authorize(cfg):
    if cfg['mode']=='engineering':
        if cfg['turn_limit']>6: raise ValueError('engineering editor probe is limited to six turns')
        return
    if cfg['mode']!='search' or not cfg.get('authorized',False):
        raise ValueError('FORMAL_SEARCH_DISABLED: explicit user authorization required')
    if not cfg.get('authorization_record') or not cfg.get('acceptance_receipt_sha256'):
        raise ValueError('formal launch requires recorded approval and accepted engineering receipt')


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config',required=True); ap.add_argument('--check',action='store_true')
    args=ap.parse_args(); cfg=json.loads(Path(args.config).read_text()); authorize(cfg)
    if args.check: print('CONFIG_GATE_OK'); return
    out=Path(cfg['local_run_root']); out.mkdir(parents=True,exist_ok=False)
    (out/'config.json').write_text(json.dumps(cfg,indent=2))
    cwd=Path(tempfile.mkdtemp(prefix='wsp-clean-editor-'))
    remote=Remote(cfg,out); thread=None; previous=''; successes=0; nudges=0
    initial=ENGINEERING if cfg['mode']=='engineering' else Path(cfg['initial_prompt']).read_text()
    try:
        for turn in range(1,cfg['turn_limit']+1):
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
            reply,thread=editor_turn(prompt,out/f'turn-{turn:03d}',cwd,thread)
            try: action=parse_action(reply,explanations=(cfg['mode']=='search' and turn>=29))
            except (ValueError,json.JSONDecodeError) as e:
                previous='Invalid response: '+str(e); nudges+=1
                if nudges>10: raise RuntimeError('too many invalid replies')
                continue
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
            if response.get('kernel_restarted'): previous='Python kernel (re)started: variables from a previous kernel are lost; /work files persist.\n'+previous
            previous+=f'\nSuccessful forward passes: {successes}; Python calls: {response["state"]["python_attempts"]}.'
            if any(x in previous for x in ('GPU_BUSY','STORAGE_LOW','INCOMPLETE_ACTION','budget exhausted','safety limit')): raise RuntimeError(previous)
        else: raise RuntimeError('turn limit reached; stopped without completing the session')
        (out/'receipt.json').write_text(json.dumps({'status':'passed' if cfg['mode']=='engineering' else 'completed',
            'mode':cfg['mode'],'turns':turn,'forward_success':successes,'last_thread':thread,'formal_search_started':cfg['mode']=='search'},indent=2))
    finally: remote.close()


if __name__=='__main__': main()
