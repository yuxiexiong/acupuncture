"""Temporary loopback-only Astra bridge. Mac and its SSH tunnel must remain online."""
import argparse
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import uuid
import editor


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    os.environ.pop('WCP_EDITOR_URL',None)
    os.environ['CODEX_HOME']=str(Path.home()/'.codex')
    editor.CLI=Path('/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex')
    editor.ENGINE=Path(__file__).resolve().parents[2]/'wsp-process-reproduction-v1-2026-11-03/engineering-r2'
    class Handler(BaseHTTPRequestHandler):
        def send(self,value):
            data=json.dumps(value).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        def do_GET(self):self.send(dict(login_ok=editor.login_status()))
        def do_POST(self):
            out=a.out/str(uuid.uuid4());value={}
            try:
                size=int(self.headers['Content-Length'])
                if not 0<size<=16000000:raise ValueError('PAYLOAD_SIZE')
                data=json.loads(self.rfile.read(size));value['result']=editor.call(data,out)
            except Exception as exc:value['error']=type(exc).__name__+': '+str(exc)
            value['artifacts']={p.name:p.read_text() for p in out.glob('*') if p.is_file() and p.name in ('prompt.txt','command.json','events.jsonl','stderr.txt','reply.txt','receipt.json')}
            self.send(value)
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',18765),Handler)
    tunnel=subprocess.Popen(['ssh','-N','-o','ExitOnForwardFailure=yes','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3','-R','127.0.0.1:18765:127.0.0.1:18765','gqa-h20'])
    try:server.serve_forever()
    finally:tunnel.terminate();tunnel.wait(timeout=10);server.server_close()


if __name__=='__main__':main()
