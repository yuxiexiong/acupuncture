"""Path/import/build adapters around the previously validated numerical backend.

No diagnosis, ranking, selection or intervention algorithm is defined here.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import types

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE = Path(os.environ['WSP_AUTHOR_SOURCE'])
backend = ROOT.parent/'engineering-r2/forward_service.py'
expected_backend = json.loads((ROOT/'adapter-provenance.json').read_text())['reused']['engineering-r2/forward_service.py']
assert hashlib.sha256(backend.read_bytes()).hexdigest()==expected_backend, 'Numerical backend changed'
spec = importlib.util.spec_from_file_location('wsp_numerical_backend', backend)
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)


def verify_source(rel):
    entry = next(x for x in json.loads((ROOT/'sources.json').read_text())['files'] if x['path']==rel)
    p = SOURCE/rel
    data = p.read_bytes()
    assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==entry['git_blob_sha1'], rel
    return p


def load_mathqa():
    """Import unchanged author code; the unavailable diagnostic explicitly fails."""
    p = verify_source('exp8_math/code/mathqa.py')
    def unavailable(*args, **kwargs):
        raise NotImplementedError('Author mcqa.loop_signals is unpublished; no substitute is provided')
    stub = types.ModuleType('mcqa')
    stub.loop_signals = unavailable
    old = sys.modules.get('mcqa')
    sys.modules['mcqa'] = stub
    try:
        spec = importlib.util.spec_from_file_location('author_mathqa', p)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        if old is None:
            sys.modules.pop('mcqa', None)
        else:
            sys.modules['mcqa'] = old
    # Reject a silently available different private implementation, too.
    assert module.mcqa_loop_signals is unavailable
    return vars(module)


def build_checkpoint(prof, snapshot, cache=None):
    """Validate snapshot, invoke original builder in CPU subprocess, verify saved tensors."""
    base = prof['model']
    if snapshot is None:
        return base, {'identity':'original','dir':str(base)}
    snapshot = Path(snapshot)
    man = json.loads((snapshot/'manifest.json').read_text())
    if man.get('status')!='validated' or Path(man['model']).resolve()!=base.resolve():
        raise F.RequestError('snapshot not validated')
    for row in man['tensors']:
        if F.sha256_file(snapshot/(row['name']+'.npy'))!=row['snapshot_sha256']:
            raise F.RequestError('snapshot hash mismatch')
    cache = Path(cache or os.environ.get('WSP_CKPT_CACHE',str(F.CKPT_CACHE)))
    key = hashlib.sha256((snapshot/'manifest.json').read_bytes()+str(base).encode()).hexdigest()[:20]
    out = cache/f"author-{prof['name']}-{key}"
    if (out/'build.json').exists():
        info = json.loads((out/'build.json').read_text())
        assert F.sha256_file(out/'model.safetensors')==info['model_sha256']
        return out, info
    cache.mkdir(parents=True,exist_ok=True)
    subprocess.run([sys.executable,str(ROOT/'build_with_author.py'),'--source-root',str(SOURCE),
                    '--model',str(base),'--edits',str(snapshot),'--out',str(out)],check=True,
                   env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
    from safetensors import safe_open
    import torch
    changed = {}
    with safe_open(str(base/'model.safetensors'),framework='pt') as original, \
         safe_open(str(out/'model.safetensors'),framework='pt') as built:
        assert set(original.keys())==set(built.keys())
        expected = {r['name']:r for r in man['tensors']}
        for name in original.keys():
            a,b = original.get_tensor(name),built.get_tensor(name)
            if name in expected:
                digest = hashlib.sha256(b.contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()
                assert digest==expected[name]['effective_tensor_sha256'],name
                changed[name] = int((a!=b).sum())
            else:
                assert torch.equal(a,b),name
    info = {'identity':'edited','builder':'unchanged author build_ckpt.py','snapshot':str(snapshot),
            'changed_values':changed,'model_sha256':F.sha256_file(out/'model.safetensors'),
            'snapshot_manifest_sha256':F.sha256_file(snapshot/'manifest.json'),'dir':str(out),
            'author_receipt':json.loads((out/'edits.json').read_text())}
    (out/'build.json').write_text(json.dumps(info,indent=2))
    return out,info


F.PRACTICE = SOURCE/'exp8_math/practice'
F.load_mathqa = load_mathqa
F.build_checkpoint = build_checkpoint
# Child generation processes also enter this adapter; numerical functions stay unchanged.
F.__file__ = str(Path(__file__).resolve())


def __getattr__(name):
    return getattr(F,name)


if __name__=='__main__':
    F.main()
