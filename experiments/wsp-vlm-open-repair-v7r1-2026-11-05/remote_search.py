"""Old math local-researcher/SSH-observer transport, with v7 actions and no replay.

Uncertain transport stops. Reconciliation is read-only and must be explicit; no
automatic new model calls or workspace restart after a disconnect.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from common import HERE, file_hash, write_json, packed
from controller import CodexResearcher, run_session
from evidence import Evidence


class RemoteService:
    def __init__(self, config, task, root):
        self.contract=config['contract'];self.root=root;self.started=time.time()
        self.evidence=Evidence(HERE.parents[1]/'external/wsp-vlm-open-repair-v7-2026-11-05'/f'{task}_D',config['evidence_sha256'])
        self.state={};self.stop_sent=False
        command=['ssh','-o','ConnectTimeout=20','-o','ServerAliveInterval=15','gqa-h20',
            'cd /workspace/acupuncture && CUDA_VISIBLE_DEVICES=0 timeout 7200 .venv-bench/bin/python -u '
            f'experiments/wsp-vlm-open-repair-v7-2026-11-05/live.py --serve --config experiments/wsp-vlm-open-repair-v7-2026-11-05/config-{task}.json']
        write_json(root/'server_command.json',command)
        self.log=(root/'ssh.stderr.log').open('w')
        self.proc=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.log,text=True,bufsize=1)
        self.dispatch(dict(id='observer-initial',kind='forward',request=dict(op='status')))

    def remaining(self):return self.contract['wall_seconds']-(time.time()-self.started)

    def dispatch(self,action):
        write_json(self.root/(action['id']+'-request.json'),action)
        self.proc.stdin.write(packed(action).decode()+'\n');self.proc.stdin.flush()
        line=self.proc.stdout.readline()
        if not line:raise RuntimeError('INCOMPLETE_TRANSPORT: inspect durable server response; never replay blindly')
        result=json.loads(line)
        if result['id']!=action['id']:raise RuntimeError('Response identity mismatch')
        write_json(self.root/(action['id']+'-response.json'),result)
        self.state=result['budget']
        return result

    def save(self):
        if self.state.get('research_done') and not self.stop_sent:
            self.stop_sent=True
            self.dispatch(dict(id='observer-final',kind='forward',request=dict(op='stop',reason='Researcher ended without another action')))

    def close(self):
        try:self.proc.stdin.close()
        except (BrokenPipeError,OSError):pass
        try:self.proc.wait(timeout=30)
        except subprocess.TimeoutExpired:self.proc.terminate();self.proc.wait(timeout=10)
        self.log.close()


def worker(task,config):
    root=HERE/('search-'+task);root.mkdir(exist_ok=False)
    cfg=json.loads(config.read_text())
    cfg['researcher_cli']='/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex'
    cfg['researcher_cli_sha256']=file_hash(cfg['researcher_cli'])
    write_json(root/'local_config.json',cfg)
    service=RemoteService(cfg,task,root)
    try:
        researcher=CodexResearcher(cfg,root/'researcher-empty')
        instructions=(HERE/'RESEARCHER.md').read_text()+'\nCurrent branch: '+task+'\nFrozen contract: '+json.dumps(cfg['contract'])
        result=run_session(service,researcher,root/'conversation',instructions)
        write_json(root/'receipt.json',result)
    finally:service.close()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--task',choices=['B','C'],required=True);p.add_argument('--config',type=Path,required=True);p.add_argument('--worker',action='store_true');a=p.parse_args()
    if a.worker:worker(a.task,a.config)
    else:
        proc=subprocess.Popen([sys.executable,__file__,'--task',a.task,'--config',str(a.config),'--worker'],start_new_session=True)
        started=time.time()
        try:
            proc.wait(timeout=7200)
        finally:
            if proc.poll() is None:
                os.killpg(proc.pid,signal.SIGKILL);proc.wait()
            write_json(HERE/('search-'+a.task+'-supervisor.json'),dict(exit_code=proc.returncode,elapsed_seconds=time.time()-started,budget_seconds=7200))
        raise SystemExit(proc.returncode)
