"""Reuse v4 download/hash verification for exactly the two authorized checkpoints."""
import argparse
import hashlib
import json
import os
import shutil
import struct
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def run(size):
    # The server's Xet data channel stalls; verified HTTP range transfer works.
    os.environ['HF_HUB_DISABLE_XET'] = '1'
    from huggingface_hub import snapshot_download
    info = json.loads((HERE / f'upstream-{size}.json').read_text())
    model = f'Qwen/Qwen3-VL-{size}-Instruct'
    assert info['id'] == model
    out = ROOT / 'external' / HERE.name / size
    out.mkdir(parents=True, exist_ok=True)
    if (out / 'download.json').exists():
        raise RuntimeError('Already completed; do not replace the frozen manifest')
    files = [f for f in info['siblings'] if '/' not in f['rfilename'] and
             Path(f['rfilename']).suffix in ('.json', '.jinja', '.safetensors', '.txt', '.model')]
    needed = sum(f['size'] for f in files)
    assert shutil.disk_usage(out).free > needed + 25 * 1024**3
    print(json.dumps(dict(stage='download', model=model, revision=info['sha'], bytes=needed)), flush=True)
    start = time.time()
    folder = Path(snapshot_download(model, revision=info['sha'],
        cache_dir=str(ROOT/'external/wsp-vlm-model-cache/hub'),
        allow_patterns=[f['rfilename'] for f in files], max_workers=2))
    view = out / 'model'
    view.mkdir(exist_ok=True)
    hashes = {}
    for f in files:
        src = (folder/f['rfilename']).resolve(strict=True)
        assert src.stat().st_size == f['size']
        sha = hashlib.sha256()
        git = hashlib.sha1(f"blob {f['size']}\0".encode())
        with src.open('rb') as stream:
            for block in iter(lambda: stream.read(8*1024**2), b''):
                sha.update(block); git.update(block)
        expected = f.get('lfs', {}).get('sha256')
        assert sha.hexdigest() == expected if expected else git.hexdigest() == f['blobId']
        dest = view/f['rfilename']
        if not dest.exists():
            os.link(src, dest)
        assert not dest.is_symlink() and os.path.samefile(src, dest)
        hashes[f['rfilename']] = sha.hexdigest()
        print(json.dumps(dict(stage='verified', name=f['rfilename'], bytes=f['size'])), flush=True)
    derived = None
    if not (view/'model.safetensors.index.json').exists():
        # Index-only adaptation: no tensor bytes, names, shapes or values change.
        with (view/'model.safetensors').open('rb') as stream:
            length = struct.unpack('<Q', stream.read(8))[0]
            header = json.loads(stream.read(length))
        index = dict(metadata={}, weight_map={n:'model.safetensors' for n in header if n != '__metadata__'})
        (view/'model.safetensors.index.json').write_text(json.dumps(index, sort_keys=True)+'\n')
        hashes['model.safetensors.index.json'] = hashlib.sha256((view/'model.safetensors.index.json').read_bytes()).hexdigest()
        derived = 'Index derived from the unchanged single safetensors header'
    receipt = dict(model=model, revision=info['sha'], model_root=str(view), files=hashes,
        total_bytes=needed, elapsed_seconds=time.time()-start, derived_index=derived,
        source_endpoint=os.environ.get('HF_ENDPOINT', 'https://huggingface.co'),
        verified_against='official upstream metadata: LFS SHA256 / Git blob SHA1', model_loads=0)
    (out/'download.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(dict(stage='complete', model=model, elapsed_seconds=receipt['elapsed_seconds'])), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--size', choices=['2B', '8B'], required=True)
    run(p.parse_args().size)
