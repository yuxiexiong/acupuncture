"""One request per disposable low-privilege bubblewrap sandbox; no model mounts."""
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import tempfile
import time
import uuid

ROOT = Path('/workspace/acupuncture/external/wcp01')
BWRAP = Path('/workspace/acupuncture/external/wsp/tools/bubblewrap-local/usr/bin/bwrap')
ENV = Path('/workspace/acupuncture/.venv-wsp')
PREFIX = Path('/workspace/miniconda/envs/gqa')
HERE = Path(__file__).resolve().parent


def limits(groups):
    for group in groups:
        (group/'tasks').write_text(str(os.getpid()))
    for kind, value in ((resource.RLIMIT_AS, 4*1024**3), (resource.RLIMIT_CPU, 60),
                        (resource.RLIMIT_NPROC, 32), (resource.RLIMIT_NOFILE, 64),
                        (resource.RLIMIT_FSIZE, 8*1024**2), (resource.RLIMIT_CORE, 0)):
        resource.setrlimit(kind, (value, value))


def command():
    args = [str(BWRAP), '--unshare-all', '--die-with-parent', '--new-session',
            '--uid', '65534', '--gid', '65534', '--cap-drop', 'ALL']
    for p in ('/usr','/bin','/lib','/lib64','/etc/ld.so.cache',str(ENV),str(PREFIX)):
        args += ['--ro-bind',p,p]
    args += ['--ro-bind',str(ROOT/'vendor'),'/vendor', '--ro-bind',str(HERE/'scoring.py'),'/scoring.py',
             '--proc','/proc','--dev','/dev','--tmpfs','/tmp','--chdir','/tmp',
             str(ENV/'bin/python'),'-B','/scoring.py']
    return args


def score(request, timeout=60):
    if not 0 < timeout <= 60:
        raise ValueError('execution timeout must be <=60s')
    start = time.monotonic()
    # No caller credentials, server environment or GPU visibility enters the sandbox.
    env = {'PATH':'/usr/bin:/bin', 'HOME':'/tmp', 'PYTHONPATH':'/vendor', 'PYTHONNOUSERSITE':'1',
           'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
    groups = []
    memory_failures = 0
    tag = 'wcp01-'+uuid.uuid4().hex
    try:
        for controller, settings in (
            ('memory', {'memory.limit_in_bytes':str(4*1024**3)}),
            ('pids', {'pids.max':'16'}),
            ('cpu', {'cpu.cfs_period_us':'100000','cpu.cfs_quota_us':'100000'})):
            group = Path('/sys/fs/cgroup')/controller/tag
            group.mkdir(); groups.append(group)
            for name, value in settings.items():
                (group/name).write_text(value)
        with tempfile.TemporaryFile(mode='w+') as out, tempfile.TemporaryFile(mode='w+') as err:
            p = subprocess.Popen(command(), stdin=subprocess.PIPE, stdout=out, stderr=err,
                                 text=True, env=env, start_new_session=True, preexec_fn=lambda: limits(groups))
            timed_out = False
            try:
                p.communicate(json.dumps(request), timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(p.pid, signal.SIGKILL)
                p.communicate()
            out.seek(0); err.seek(0)
            stdout, stderr = out.read(8*1024**2), err.read(8*1024**2)
    finally:
        memory_group = next((g for g in groups if g.parent.name=='memory'),None)
        if memory_group is not None:
            memory_failures = int((memory_group/'memory.failcnt').read_text())
        for group in reversed(groups):
            for pid in (group/'tasks').read_text().split():
                try: os.kill(int(pid), signal.SIGKILL)
                except ProcessLookupError: pass
            for _ in range(100):
                try: group.rmdir(); break
                except OSError: time.sleep(0.05)
            else: raise RuntimeError('sandbox cgroup did not empty: '+str(group))
    elapsed = time.monotonic()-start
    if timed_out:
        return dict(status='timeout', correct=False, wall_seconds=elapsed, returncode=p.returncode)
    if p.returncode and memory_failures:
        return dict(status='memory_limit', correct=False, wall_seconds=elapsed, returncode=p.returncode)
    if p.returncode == -signal.SIGXCPU:
        return dict(status='timeout', correct=False, wall_seconds=elapsed, returncode=p.returncode)
    if p.returncode:
        # Reference/probe/bootstrap failures cannot silently count as a model mistake.
        return dict(status='execution_error', correct=None, wall_seconds=elapsed,
                    returncode=p.returncode, stderr=stderr[-4000:])
    try:
        result = json.loads(stdout)
    except (ValueError, TypeError):
        return dict(status='execution_error', correct=None, wall_seconds=elapsed,
                    stderr=stderr[-4000:], stdout=stdout[-4000:])
    result['wall_seconds'] = elapsed
    return result
