"""Observer-owned JSONL broker. Run via SSH; never mount this code in the editor kernel."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import selectors
import shutil
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from sandbox_probe import command
import forward_service as FS


def write_json(path, obj):
    temp = path.with_suffix('.pending')
    temp.write_text(json.dumps(obj, indent=2) + '\n')
    temp.replace(path)


def read_line(proc, timeout):
    with selectors.DefaultSelector() as sel:
        sel.register(proc.stdout, selectors.EVENT_READ)
        if not sel.select(timeout):
            raise TimeoutError('external process deadline exceeded')
        line = proc.stdout.readline()
    if not line:
        raise RuntimeError('child terminated without a response')
    return json.loads(line)


def stop(proc):
    if proc is not None and proc.poll() is None:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()


class Broker:
    def __init__(self, config):
        if config['forward_limit']>3 and not config.get('authorized',False):
            raise ValueError('FORMAL_SEARCH_DISABLED at broker gate')
        if config['forward_limit']>3 and not config.get('authorization_record'):
            raise ValueError('formal broker requires recorded user authorization')
        self.cfg = config
        self.root = Path(config['run_root'])
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = open(self.root / 'broker.lock', 'a')
        fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if shutil.disk_usage(self.root).free < config.get('minimum_free_bytes',0):
            raise RuntimeError('STORAGE_LOW: provision the reviewed disk budget before launch')
        self.work = self.root / 'work'
        self.work.mkdir(exist_ok=True)
        (self.work / 'edited').mkdir(exist_ok=True)
        self.kernel = None
        self.kernel_log = None
        self.state_path = self.root / 'state.json'
        self.state = json.loads(self.state_path.read_text()) if self.state_path.exists() else {
            'python_attempts':0, 'forward_attempts':0, 'forward_success':0, 'gpu_seconds':0.0, 'kernel_restarts':0}
        frozen = self.root / 'config.json'
        if frozen.exists() and json.loads(frozen.read_text()) != config:
            raise ValueError('run config differs from frozen config; use a new run directory')
        write_json(frozen, config)
        self.prof = FS.profile(config['profile'])
        from transformers import AutoTokenizer
        tokenizer=AutoTokenizer.from_pretrained(self.prof['model'],local_files_only=True)
        marker='WSP_PROBLEM_PLACEHOLDER_49871'
        rendered=FS.render_prompt(tokenizer,marker+'\n'+FS.INSTRUCTION)
        prefix,suffix=rendered.split(marker)
        (self.work / 'eval_prompt_format.txt').write_text(
            "The evaluation prompt, exactly as the model sees it (thinking on), for a problem P:\n"
            "PREFIX + P + SUFFIX, with\nPREFIX = "+repr(prefix)+"\nSUFFIX = "+repr(suffix)+
            "\nThe model's answer follows SUFFIX directly. To score a text with a teacher-forced pass, "
            "send PREFIX + P + SUFFIX + answer as one raw text in texts. Chats re-renders assistant turns.\n")

    def save(self):
        write_json(self.state_path, self.state)

    def start_kernel(self):
        ext = FS.EXT
        env = Path('/workspace/acupuncture/.venv-wsp')
        prefix = Path('/workspace/miniconda')
        args = command(ext/'tools/bubblewrap-local/usr/bin/bwrap', env/'bin/python', prefix,
                       env, self.prof['model'], FS.PRACTICE, self.work, HERE/'sandbox_kernel.py')
        self.kernel_log = open(self.root/'kernel.stderr.log', 'a')
        self.kernel = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=self.kernel_log, text=True, bufsize=1, env={'PATH':'/usr/bin:/bin'}, start_new_session=True)
        ready = read_line(self.kernel, 120)
        if not ready.get('ready'):
            raise RuntimeError('kernel did not become ready')
        self.state['kernel_restarts'] += 1
        self.save()

    def cpu(self, request):
        if self.state['python_attempts'] >= self.cfg['python_limit']:
            raise ValueError('Python budget exhausted')
        restarted = self.kernel is None or self.kernel.poll() is not None
        if restarted:
            self.start_kernel()
        self.state['python_attempts'] += 1
        self.save()
        try:
            self.kernel.stdin.write(json.dumps(request) + '\n'); self.kernel.stdin.flush()
            result = read_line(self.kernel, min(900, self.cfg.get('python_timeout',900))+5)
            if result.get('id') != request['id']:
                raise RuntimeError('kernel response ID mismatch')
        except Exception:
            stop(self.kernel); self.kernel = None
            raise
        result['kernel_restarted'] = restarted
        return result

    def forward(self, request, attempt):
        if self.state['forward_success'] >= self.cfg['forward_limit']:
            raise ValueError('forward budget exhausted')
        if self.state['forward_attempts'] >= self.cfg['forward_attempt_limit']:
            raise ValueError('forward attempt safety limit reached; stop for review')
        req = FS.validate(request['request'], self.prof, FS.practice_index())
        count = 2 if req['model']=='both' else 1
        remain = self.cfg['gpu_seconds_limit'] - self.state['gpu_seconds']
        if remain < count * 30:
            raise ValueError('GPU wall budget exhausted')
        locks=[]
        try:
            # Advisory locks coordinate WSP; live memory/process checks protect unrelated jobs.
            deadline=time.monotonic()+self.cfg.get('gpu_wait_seconds',60)
            while True:
                rows = subprocess.check_output(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu',
                                               '--format=csv,noheader,nounits'],text=True)
                idle=[int(a) for a,b,c in (line.split(',') for line in rows.splitlines()) if int(b)<128 and int(c)==0]
                gpus=[]
                for g in idle:
                    handle=open(FS.EXT/f'engineering-gpu-{g}.lock','a')
                    try: fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
                    except BlockingIOError: handle.close(); continue
                    locks.append(handle); gpus.append(g)
                    if len(gpus)==count: break
                if len(gpus)==count: break
                for handle in locks: handle.close()
                locks=[]
                if time.monotonic()>=deadline:
                    raise RuntimeError('GPU_BUSY: pause and wait for existing jobs; none interrupted')
                time.sleep(2)
            self.state['forward_attempts'] += 1
            self.save()
            # Preserve original file IDs even when historical failed attempts are not executed.
            # Actual attempts/successes remain separately counted above/below.
            k=request.get('source_pass',self.state['forward_attempts'])
            if type(k) is not int or k < 1:
                raise ValueError('invalid source pass')
            write_json(attempt/'request.json',req)
            # Always validate edits, even files written directly rather than via save_edit.
            from snapshot_edits import snapshot
            snap=attempt/'snapshot'
            manifest=snapshot(self.prof['model'],self.work/'edited',snap)
            cmd=[sys.executable,str(HERE/'forward_service.py'),'serve','--profile',self.cfg['profile'],
                 '--request',str(attempt/'request.json'),'--k',str(k),'--work',str(self.work),
                 '--archive',str(attempt),'--gpus',*[str(g) for g in gpus]]
            if manifest['tensors']: cmd += ['--snapshot',str(snap)]
            started=time.monotonic()
            proc=None
            try:
                with open(attempt/'service.log','w') as log:
                    proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
                                          env=dict(os.environ,WSP_CKPT_CACHE=str(self.root/'checkpoint-cache')))
                    write_json(attempt/'process.json',{'pid':proc.pid,'gpu_slots':gpus,'started_unix':time.time()})
                    proc.wait(timeout=min(self.cfg['forward_timeout'],remain/count))
                if proc.returncode:
                    raise RuntimeError('forward service failed; observer receipt retained')
            finally:
                stop(proc)
                self.state['gpu_seconds'] += count*(time.monotonic()-started)
                self.save()
            result=json.loads((attempt/f'pass_{k}.public.json').read_text())
            # Derived full checkpoints can be reconstructed from preserved validated snapshots.
            # Only this run's private cache is removed; raw edits and evidence are retained.
            shutil.rmtree(self.root/'checkpoint-cache',ignore_errors=True)
            self.state['forward_success'] += 1
            self.save()
            return {'failed':False,'editor_output':json.dumps(result),'pass_attempt':k,
                    'snapshot_sha256':FS.sha256_file(snap/'manifest.json')}
        finally:
            for handle in locks: handle.close()

    def dispatch(self, request):
        ident=request.get('id','')
        if not ident or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in ident):
            raise ValueError('invalid action ID')
        digest=hashlib.sha256(json.dumps(request,sort_keys=True).encode()).hexdigest()
        attempt=self.root/'actions'/ident
        if attempt.exists():
            if (attempt/'request.sha256').read_text()!=digest:
                raise ValueError('action ID reused with different content')
            if (attempt/'response.json').exists():
                return json.loads((attempt/'response.json').read_text())
            raise RuntimeError('INCOMPLETE_ACTION: do not replay automatically; reconcile observer receipt')
        if any(not (p/'response.json').exists() for p in (self.root/'actions').glob('*') if p.is_dir()):
            raise RuntimeError('INCOMPLETE_ACTION: reconcile previous pending action before continuing')
        attempt.mkdir(parents=True)
        (attempt/'request.sha256').write_text(digest)
        write_json(attempt/'input.json',request)
        try:
            if shutil.disk_usage(self.root).free < self.cfg.get('reserve_free_bytes',20*10**9):
                raise RuntimeError('STORAGE_LOW: pause before filling the shared volume')
            if request['kind']=='python': result=self.cpu(request)
            elif request['kind']=='forward': result=self.forward(request,attempt)
            elif request['kind']=='status': result={'failed':False,'editor_output':self.context()}
            elif request['kind']=='finalize':
                from snapshot_edits import snapshot
                manifest=snapshot(self.prof['model'],self.work/'edited',attempt/'final-snapshot')
                result={'failed':False,'editor_output':'Final edits validated and archived.',
                        'final_manifest_sha256':FS.sha256_file(attempt/'final-snapshot/manifest.json'),
                        'tensors':manifest['tensors']}
            else: raise ValueError('unknown action kind')
        except Exception as e:
            result={'failed':True,'editor_output':f'{type(e).__name__}: {e}'}
        result.update(id=ident,state=dict(self.state))
        write_json(attempt/'response.json',result)
        # Never expose observer paths, checkpoints or full uncapped Python output to editor.
        return result

    def context(self):
        notes=self.work/'notes.md'
        text=''
        try:
            fd=os.open(notes,os.O_RDONLY|os.O_NOFOLLOW)
            with os.fdopen(fd,'rb') as f:
                f.seek(max(0,os.fstat(f.fileno()).st_size-32000))
                text=f.read().decode('utf-8',errors='replace')[-8000:]
        except FileNotFoundError: pass
        return json.dumps({'budget':self.state,'edited':[p.name[:-4] for p in (self.work/'edited').glob('*.npy')],
                           'files':sorted(p.name for p in self.work.iterdir()),'notes':text})


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config',required=True)
    a=ap.parse_args(); cfg=json.loads(Path(a.config).read_text())
    broker=Broker(cfg)
    try:
        for line in sys.stdin:
            try: result=broker.dispatch(json.loads(line))
            except Exception as e: result={'failed':True,'editor_output':str(e),'fatal':True}
            print(json.dumps(result),flush=True)
    finally:
        stop(broker.kernel)


if __name__=='__main__': main()
