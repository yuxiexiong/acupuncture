"""Persistent NumPy research workspace, adapted from the old math CPU kernel.

Arbitrary Python is NOT sandboxed by exec(). Production use requires SandboxKernel
below (OS isolation). In-process use is only for trusted synthetic unit fixtures.
"""
import ast
import contextlib
import io
import json
import os
from pathlib import Path
import resource
import selectors
import signal
import subprocess
import sys
import time
import traceback

import numpy as np
from common import HERE, digest, file_hash, inside, write_json, require_live
from weights import TensorSource, Candidates, quantize


class BoundedOutput(io.StringIO):
    """Explicit failure on excessive tool output, not silent evidence truncation."""
    def write(self, text):
        if self.tell() + len(text) > 1_000_000:
            raise ValueError('Python output exceeds 1,000,000 characters; save an array/file and inspect a subset')
        return super().write(text)


class PythonNamespace:
    def __init__(self, source, candidates, work, state_file, evidence_root, artifacts):
        self.source, self.candidates = source, candidates
        self.work, self.state_file = Path(work), Path(state_file)
        self.work.mkdir(exist_ok=True)
        (self.work / 'staged').mkdir(exist_ok=True)
        self.namespace = dict(np=np, NAMES=sorted(source.catalog()), catalog=source.catalog,
                              load_original=source.load, load=self.load, save_edit=self.save_edit,
                              drop_edit=self.drop_edit, edited=lambda: sorted(self.staged()),
                              EVIDENCE=str(evidence_root), ARTIFACTS=str(artifacts))

    def staged(self):
        path = self.work / 'stage.json'
        return json.loads(path.read_text()) if path.exists() else {}

    def load(self, name):
        name = self.source.canonical(name)
        stage = self.staged()
        if name in stage:
            return np.load(inside(self.work, stage[name]), allow_pickle=False).copy()
        state = json.loads(self.state_file.read_text())
        return self.candidates.load(state['current'], name)

    def save_edit(self, name, value):
        name = self.source.canonical(name)
        x = quantize(value, self.source.effective_dtype)
        if list(x.shape) != self.source.entries[name]['shape']:
            raise ValueError('Wrong parameter shape')
        rel = 'staged/' + digest(name.encode()) + '.npy'
        temp = self.work / (rel + '.pending')
        with temp.open('wb') as f:
            np.save(f, x, allow_pickle=False)
        temp.replace(self.work / rel)
        stage = self.staged()
        stage[name] = rel
        write_json(self.work / 'stage.json', stage)
        return dict(name=name, staged=True, observer_validation_pending=True)

    def drop_edit(self, name):
        stage = self.staged()
        stage.pop(self.source.canonical(name), None)
        write_json(self.work / 'stage.json', stage)

    def execute(self, code):
        output = BoundedOutput()
        failed = False
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            try:
                tree = ast.parse(code)
                if tree.body and isinstance(tree.body[-1], ast.Expr):
                    expression = tree.body.pop()
                    exec(compile(tree, '<researcher>', 'exec'), self.namespace)
                    result = eval(compile(ast.Expression(expression.value), '<researcher>', 'eval'), self.namespace)
                    if result is not None:
                        print(repr(result))
                else:
                    exec(compile(tree, '<researcher>', 'exec'), self.namespace)
            except Exception:
                failed = True
                error = traceback.format_exc()
                # Bypass the cap for the small explicit error record itself.
                io.StringIO.write(output, '\n'+error[-4096:])
        # Full UTF-8 output is retained; the observer attaches a bounded preview.
        return dict(failed=failed, output=output.getvalue())


def stop(proc):
    if proc is not None and proc.poll() is None:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()


class SandboxKernel:
    """No unsandboxed production fallback; system isolation must pass live acceptance."""
    def __init__(self, config, work, state, candidates, evidence, artifacts):
        require_live(config)
        if sys.platform != 'linux':
            raise RuntimeError('Live Python tools require Linux bubblewrap; no fallback')
        self.config, self.work, self.proc = config, Path(work), None
        c = config['sandbox']
        args = [c['bwrap'], '--unshare-all', '--die-with-parent', '--new-session', '--cap-drop', 'ALL']
        # Explicit runtime-only roots, not /, home, repository, observer or credential roots.
        for p in ('/usr', '/bin', '/lib', '/lib64', '/etc/ld.so.cache', c['prefix'], c['environment']):
            if Path(p).exists():
                if any(Path(q).resolve().is_relative_to(Path(p).resolve()) for q in (HERE, work, evidence, candidates, config['model_root'])):
                    raise ValueError('Runtime mount would expose research/observer directories')
                args += ['--ro-bind', p, p]
        for src, dest in ((HERE, '/code'), (config['model_root'], '/model'), (state, '/state'),
                          (candidates, '/candidates'), (evidence, '/evidence'), (artifacts, '/artifacts')):
            args += ['--ro-bind', str(src), dest]
        args += ['--bind', str(work), '/work', '--proc', '/proc', '--dev', '/dev', '--tmpfs', '/tmp',
                 '--chdir', '/work', '--setenv', 'PATH', '/usr/bin:/bin', '--setenv', 'PYTHONNOUSERSITE', '1',
                 '--setenv', 'OPENBLAS_NUM_THREADS', '1', c['python'], '-u', '/code/kernel.py']
        self.command = args

    def call(self, code, seconds):
        restarted = self.proc is None or self.proc.poll() is not None
        if restarted:
            self.stderr = (self.work / 'kernel.stderr.log').open('a')
            self.proc = subprocess.Popen(self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                         stderr=self.stderr, text=True, bufsize=1, start_new_session=True, env={})
        self.proc.stdin.write(json.dumps(dict(code=code), ensure_ascii=False) + '\n')
        self.proc.stdin.flush()
        try:
            with selectors.DefaultSelector() as sel:
                sel.register(self.proc.stdout, selectors.EVENT_READ)
                if not sel.select(seconds):
                    raise TimeoutError('CPU tool deadline exceeded')
                response = self.proc.stdout.readline()
            if not response:
                raise RuntimeError('CPU worker exited')
            value = json.loads(response)
            value['kernel_restarted'] = restarted
            return value
        except Exception:
            self.close()
            raise

    def close(self):
        stop(self.proc)
        self.proc = None
        if getattr(self, 'stderr', None):
            self.stderr.close()


def collect_staged(work, source):
    """Observer revalidates even proposals written without save_edit()."""
    work = Path(work)
    manifest = inside(work, 'stage.json')
    edits = json.loads(manifest.read_text()) if manifest.exists() else {}
    result = {}
    for name, rel in edits.items():
        canonical = source.canonical(name)
        path = inside(work, rel)
        if path.stat().st_size > np.prod(source.entries[canonical]['shape']) * 8 + 4096:
            raise ValueError('Oversized proposal file')
        with path.open('rb') as f:
            version = np.lib.format.read_magic(f)
            if version == (1, 0): shape, _, dtype = np.lib.format.read_array_header_1_0(f)
            elif version == (2, 0): shape, _, dtype = np.lib.format.read_array_header_2_0(f)
            else: raise ValueError('Unsupported proposal NPY version')
            if list(shape) != source.entries[canonical]['shape'] or dtype.kind != 'f':
                raise ValueError('Invalid proposal array header')
        result[name] = np.load(path, allow_pickle=False)
    return result


if __name__ == '__main__':
    if str(HERE) != '/code' or not Path('/state/public.json').exists():
        raise SystemExit('Kernel must be launched by the isolated observer service')
    import importlib.util
    if any(importlib.util.find_spec(name) is not None for name in ('torch', 'transformers', 'jax', 'tensorflow')):
        raise SystemExit('CPU research environment must be NumPy-only; model frameworks belong in the observer backend')
    resource.setrlimit(resource.RLIMIT_AS, (64 * 1024**3, 64 * 1024**3))
    cfg = json.loads(Path('/state/kernel.json').read_text())
    source = TensorSource('/model', cfg['aliases'])
    candidates = Candidates(source, '/candidates', cfg['temporary_scalars'], cfg['final_scalars'])
    kernel = PythonNamespace(source, candidates, '/work', '/state/public.json', '/evidence', '/artifacts')
    for line in sys.stdin:
        print(json.dumps(kernel.execute(json.loads(line)['code']), ensure_ascii=False), flush=True)
