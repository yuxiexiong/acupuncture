"""Create a symlink-free, hash-verified runtime view of an existing HF snapshot.

Byte copies/hard links only; no model, processor or tensor deserialization. Needed
because the isolated kernel must not mount an entire Hugging Face cache or repo.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
from common import REVISION, file_hash, write_json


def materialize(snapshot, download_manifest, destination):
    metadata = json.loads(Path(download_manifest).read_text())
    if metadata['model'] != 'Qwen/Qwen3-VL-4B-Instruct' or metadata['revision'] != REVISION:
        raise ValueError('Wrong fixed model revision')
    root, out = Path(snapshot), Path(destination)
    out.mkdir(parents=True, exist_ok=False)
    hashes = {}
    for row in metadata['files']:
        name = row['name']
        if Path(name).name != name:
            raise ValueError('Only fixed flat snapshot files are supported')
        # Resolve HF blob symlinks only under an observer-owned, hash-pinned receipt.
        source = (root/name).resolve(strict=True)
        if source.stat().st_size != row['bytes'] or file_hash(source) != row['sha256']:
            raise ValueError('Downloaded asset no longer matches receipt: '+name)
        try:
            os.link(source, out/name)
        except OSError:
            shutil.copyfile(source, out/name)
        if (out/name).is_symlink() or file_hash(out/name) != row['sha256']:
            raise ValueError('Materialized asset identity mismatch')
        hashes[name] = row['sha256']
    write_json(out/'view-receipt.json', dict(revision=REVISION, files=hashes,
        download_manifest_sha256=file_hash(download_manifest), model_loads=0, weight_deserializations=0))
    return hashes


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('snapshot', 'download-manifest', 'out'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(materialize(a.snapshot, a.download_manifest, a.out), indent=2))
