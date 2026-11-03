"""Detached server controller; editor transport may require the Mac bridge."""
import argparse
import json
from pathlib import Path
import shlex
import socket
import subprocess
import time
from ledger import authorize,digest,Ledger,write

HERE=Path(__file__).resolve().parent
ENV='/workspace/acupuncture/external/wsp/code-engineering-r2/engineering-r2/server_env.sh'


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,required=True)
    ap.add_argument('--status',action='store_true');ap.add_argument('--recover-completed');a=ap.parse_args()
    cfg=json.loads(a.config.read_text());root=Path(cfg['run_root'])
    if a.status:
        if not (root/'state.sqlite').exists():print('NOT_STARTED');return
        import sqlite3
        db=sqlite3.connect('file:'+str(root/'state.sqlite')+'?mode=ro',uri=True)
        state={k:json.loads(v) for k,v in db.execute("SELECT key,value FROM meta WHERE key IN ('phase','spent','overrun')")}
        state['pending']=[r[0] for r in db.execute("SELECT id FROM jobs WHERE status!='done'")];db.close();print(json.dumps(state));return
    authorize(cfg)  # denied launch creates no run directory or tmux session
    if a.recover_completed:
        db=Ledger(root,cfg)
        try:db.recover_completed(a.recover_completed)
        finally:db.close()
        print('RECONCILED_WITHOUT_REEXECUTION');return
    root.mkdir(parents=True,exist_ok=True)
    session='wcp-'+cfg['profile']+'-'+digest(str(root))[:10]
    command=shlex.join(['sh',ENV,str(HERE/'scheduler.py'),'--config',str(a.config.resolve())])+' >> '+shlex.quote(str(root/'daemon.log'))+' 2>&1'
    subprocess.run(['tmux','new-session','-d','-s',session,'sh','-c',command],check=True)
    dependency=cfg.get('editor_transport')=='mac_ssh'
    write(root/'launch.json',dict(session=session,host=socket.gethostname(),time=time.time(),mode=cfg['mode'],config_sha256=digest(cfg),client_dependency=dependency))
    print(json.dumps(dict(session=session,root=str(root),client_dependency=dependency)))


if __name__=='__main__':main()
