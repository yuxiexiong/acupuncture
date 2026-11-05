"""Lossless hard-link dedup of the explicitly named, completed v8 C archive.

No candidate, proposal, manifest or pathname is removed. Validate every declared
NPY hash before replacing anything. A durable journal makes partial completion
inspectable; rerunning requires a new receipt directory. No cache deletion.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import time


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024**2), b''):
            h.update(chunk)
    return h.hexdigest()


def write(path, value):
    tmp = path.with_suffix('.pending')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
    tmp.replace(path)


def active_references(root):
    hits = []
    for p in Path('/proc').glob('[0-9]*'):
        if int(p.name) == os.getpid():
            continue
        try:
            targets = [p/'cwd', *list((p/'fd').iterdir())]
            for target in targets:
                try:
                    if Path(os.readlink(target)).is_relative_to(root):
                        hits.append(str(target))
                except (OSError, ValueError):
                    pass
            if str(root) in (p/'maps').read_text():
                hits.append(str(p/'maps'))
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            pass
    return hits


def run(root, receipt, apply=False):
    root = root.resolve()
    expected = Path('/workspace/acupuncture/external/wsp-vlm-open-repair-v8-2026-11-05/C')
    if root != expected:
        raise ValueError('Only the completed v8 C archive is authorized')
    state = json.loads((root/'state.json').read_text())
    if not state.get('research_done') or not state.get('frozen'):
        raise ValueError('Run is not frozen and finished')
    lock = (root/'observer.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    hits = active_references(root)
    if hits:
        raise RuntimeError('Archive in active use: '+repr(hits))
    receipt.mkdir(parents=True, exist_ok=False)
    before = shutil.disk_usage(root).free
    rows, manifests = [], {}
    for p in sorted([*root.glob('candidates/*/manifest.json'), *root.glob('actions/*/proposal/manifest.json')]):
        manifests[str(p.relative_to(root))] = sha(p)
        m = json.loads(p.read_text())
        tensors = m['tensors'] if 'tensors' in m else m
        for e in tensors.values():
            q = p.parent/e['file']
            if q.is_symlink() or not q.resolve().is_relative_to(root) or q.suffix != '.npy':
                raise ValueError('Unexpected tensor path')
            st = q.stat()
            actual = sha(q)
            if actual != e['sha256']:
                raise ValueError('Manifest hash mismatch: '+str(q))
            rows.append(dict(path=str(q.relative_to(root)), sha256=actual, size=st.st_size,
                             inode=st.st_ino, device=st.st_dev, blocks=st.st_blocks,
                             mtime_ns=st.st_mtime_ns))
            write(receipt/'progress.json', dict(stage='hashing', verified=len(rows), time_unix=time.time()))
    all_files = {str(p.relative_to(root)) for p in root.glob('candidates/*/*.npy')} | {
        str(p.relative_to(root)) for p in root.glob('actions/*/proposal/*.npy')}
    if {r['path'] for r in rows} != all_files or len(rows) != len(all_files):
        raise ValueError('Missing, duplicate or unmanifested tensor files')
    write(receipt/'before.json', dict(root=str(root), rows=rows, manifest_sha256=manifests, free_bytes=before))
    if active_references(root):
        raise RuntimeError('Archive became active during verification')
    groups, replaced = {}, 0
    with (receipt/'replacements.jsonl').open('x') as journal:
        for r in rows:
            p = root/r['path']
            st = p.stat()
            if (st.st_ino, st.st_size, st.st_mtime_ns) != (r['inode'], r['size'], r['mtime_ns']):
                raise ValueError('File changed after verification')
            key = (r['device'], r['size'], r['sha256'])
            canonical = groups.setdefault(key, p)
            if apply and p.stat().st_ino != canonical.stat().st_ino:
                temp = p.with_name('.dedup-'+p.name)
                os.link(canonical, temp)  # same filesystem; no copied tensor bytes
                os.replace(temp, p)      # atomic path replacement; no gap in readers
                replaced += 1
                journal.write(json.dumps(dict(path=r['path'], canonical=str(canonical.relative_to(root)), sha256=r['sha256']))+'\n')
                journal.flush()
                os.fsync(journal.fileno())
    # Read every unique post-operation inode, then verify every path and manifest.
    verified, unique_before, unique_after = {}, {}, {}
    for r in rows:
        p = root/r['path']; st = p.stat(); key = (st.st_dev, st.st_ino)
        if key not in verified:
            verified[key] = sha(p)
        if verified[key] != r['sha256'] or st.st_size != r['size']:
            raise ValueError('Post-operation byte identity failure')
        unique_before[(r['device'], r['inode'])] = r['blocks']*512
        unique_after[key] = st.st_blocks*512
    for rel, h in manifests.items():
        if sha(root/rel) != h:
            raise ValueError('Manifest changed')
    result = dict(status='verified', applied=apply, root=str(root), files=len(rows),
                  manifests=len(manifests), replaced=replaced, unique_inodes_before=len(unique_before),
                  unique_inodes_after=len(unique_after), reclaimed_allocated_bytes=sum(unique_before.values())-sum(unique_after.values()),
                  free_before_bytes=before, free_after_bytes=shutil.disk_usage(root).free,
                  preserved_all_paths_and_hashes=True, time_unix=time.time())
    write(receipt/'receipt.json', result)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--root', type=Path, required=True)
    p.add_argument('--receipt', type=Path, required=True); p.add_argument('--apply', action='store_true')
    a = p.parse_args(); run(a.root, a.receipt, a.apply)
