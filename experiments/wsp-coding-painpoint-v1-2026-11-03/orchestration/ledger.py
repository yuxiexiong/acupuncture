"""One locked controller, durable intent before work, atomic result/state/accounting."""
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import time


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,allow_nan=False).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    path=Path(path);p=path.with_suffix(path.suffix+'.pending')
    with p.open('w') as f:
        json.dump(value,f,indent=2,allow_nan=False);f.write('\n');f.flush();__import__('os').fsync(f.fileno())
    p.replace(path)


class Ledger:
    def __init__(self,root,config):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
        self.lock=(self.root/'controller.lock').open('a');fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        self.db=sqlite3.connect(self.root/'state.sqlite');self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT); CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,hash TEXT,status TEXT,request TEXT,reserve TEXT,result TEXT);')
        prior=self.get('config')
        if prior is not None and prior!=config:raise ValueError('FROZEN_CONFIG_CHANGED')
        if prior is None:
            self.put('config',config);self.put('phase','D');self.put('spent',config.get('spent',{}));self.db.commit()
        self.cfg=config

    def get(self,key):
        r=self.db.execute('SELECT value FROM meta WHERE key=?',(key,)).fetchone()
        return json.loads(r[0]) if r else None

    def put(self,key,value):
        self.db.execute('INSERT OR REPLACE INTO meta VALUES(?,?)',(key,json.dumps(value,allow_nan=False)))

    def close(self):
        self.db.close();self.lock.close()

    def run(self,ident,phase,next_phase,request,reserve,perform):
        identity=digest(dict(phase=phase,next_phase=next_phase,request=request,reserve=reserve))
        old=self.db.execute('SELECT hash,status,result FROM jobs WHERE id=?',(ident,)).fetchone()
        if old:
            if old[0]!=identity:raise ValueError('ACTION_ID_CONTENT_CHANGED')
            if old[1]!='done':raise RuntimeError('INCOMPLETE_ACTION: reconcile recorded work; automatic replay forbidden')
            return json.loads(old[2])
        if self.db.execute("SELECT id FROM jobs WHERE status!='done'").fetchone():raise RuntimeError('INCOMPLETE_ACTION')
        if self.get('phase')!=phase:raise ValueError('STAGE_ORDER_DENIED')
        spent=self.get('spent')
        for k,n in reserve.items():
            if n<0 or spent.get(k,0)+n>self.cfg['caps'][k]:raise RuntimeError('BUDGET_EXHAUSTED: '+k)
        if shutil.disk_usage(self.root).free<self.cfg['reserve_free_bytes']:raise RuntimeError('STORAGE_LOW')
        size=sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file())
        if size>self.cfg['new_data_bytes_cap']:raise RuntimeError('DISK_WORK_CAP')
        self.db.execute('INSERT INTO jobs VALUES(?,?,?,?,?,NULL)',(ident,identity,'running',json.dumps(request),json.dumps(reserve)))
        self.db.commit()  # crash before/after external work is visible, never silently free
        out=self.root/'actions'/ident;out.mkdir(parents=True,exist_ok=False);write(out/'request.json',request)
        write(out/'action-contract.json',dict(phase=phase,next_phase=next_phase,request=request,reserve=reserve))
        started=time.time()
        try:
            result=perform(request,out)
            actual=result.pop('_usage',{})
            if any(k not in reserve or v<0 for k,v in actual.items()):raise ValueError('INVALID_RESOURCE_RECEIPT')
            write(out/'result.json',dict(result=result,usage=actual,seconds=time.time()-started))
            if self.cfg['mode']=='fixture' and __import__('os').environ.get('WCP_TEST_CRASH_AFTER_RESULT')==ident:
                __import__('os')._exit(71)
            # If the provider exceeded a soft per-turn allowance, record the real bill and stop.
            exceeded=any(actual.get(k,0)>v for k,v in reserve.items())
            for k,v in actual.items():spent[k]=spent.get(k,0)+v
            with self.db:
                self.db.execute("UPDATE jobs SET status='done',result=? WHERE id=?",(json.dumps(result,allow_nan=False),ident))
                self.put('spent',spent);self.put('phase',next_phase)
                if exceeded:self.put('overrun',dict(job=ident,actual=actual,reserved=reserve))
            if exceeded:raise RuntimeError('RESOURCE_OVERRUN_RECORDED')
            return result
        except BaseException as exc:
            write(out/'failure.json',dict(error=type(exc).__name__+': '+str(exc),elapsed=time.time()-started,reserved=reserve))
            raise

    def recover_completed(self,ident):
        """Explicit reconciliation only: accept a fully checked result written before commit."""
        row=self.db.execute('SELECT hash,status FROM jobs WHERE id=?',(ident,)).fetchone()
        if row is None or row[1]!='running':raise ValueError('NO_PENDING_ACTION')
        out=self.root/'actions'/ident;contract=json.loads((out/'action-contract.json').read_text())
        if digest(contract)!=row[0] or self.get('phase')!=contract['phase']:raise ValueError('RECOVERY_IDENTITY_MISMATCH')
        process=out/'process.json'
        if process.exists() and Path('/proc',str(json.loads(process.read_text())['pid'])).exists():raise RuntimeError('WORKER_MAY_BE_ALIVE')
        result=json.loads((out/'result.json').read_text())  # absence deliberately blocks unconfirmed work
        spent=self.get('spent')
        for k,v in result['usage'].items():
            if k not in contract['reserve'] or v<0 or v>contract['reserve'][k]:raise ValueError('RECOVERY_RESOURCE_MISMATCH')
            spent[k]=spent.get(k,0)+v
        with self.db:
            self.db.execute("UPDATE jobs SET status='done',result=? WHERE id=?",(json.dumps(result['result']),ident))
            self.put('spent',spent);self.put('phase',contract['next_phase'])
        write(out/'recovery.json',dict(reconciled=True,time=time.time(),reexecuted=False))

    def remaining(self):
        spent=self.get('spent').copy()
        for row in self.db.execute("SELECT reserve FROM jobs WHERE status!='done'"):
            for k,v in json.loads(row[0]).items():spent[k]=spent.get(k,0)+v
        return {k:v-spent.get(k,0) for k,v in self.cfg['caps'].items()}


def authorize(cfg):
    if cfg['mode']=='fixture':
        if cfg.get('backend')!='fixture' or cfg.get('data_root') is not None:raise ValueError('FIXTURE_CANNOT_READ_RESEARCH_DATA')
        return
    if cfg['mode']!='research' or not cfg.get('authorized') or not cfg.get('authorization_record'):
        raise ValueError('FORMAL_SEARCH_DISABLED')
    if cfg.get('backend')!='real' or cfg.get('profile') not in ('0p8b','4b'):raise ValueError('RESEARCH_BACKEND_IDENTITY')
    if not cfg.get('acceptance_sha256') or not cfg.get('source_hashes'):raise ValueError('ACCEPTANCE_OR_SOURCE_FREEZE_MISSING')
    for path,sha in cfg['source_hashes'].items():
        if file_hash(path)!=sha:raise ValueError('SOURCE_HASH_CHANGED: '+path)
    if file_hash(cfg['acceptance_path'])!=cfg['acceptance_sha256']:raise ValueError('ACCEPTANCE_CHANGED')
    acceptance=json.loads(Path(cfg['acceptance_path']).read_text())
    if acceptance.get('status')!='passed':raise ValueError('ACCEPTANCE_NOT_PASSED')
