"""Sharded tensor reading and observer-owned immutable sparse candidates; NumPy only.

Safetensors bytes are read only by explicit load(). No checkpoint is read on import.
BF16 edits are counted after round-to-nearest-even, relative to W0, not the parent.
"""
import json
import math
import shutil
import struct
import tempfile
from pathlib import Path

import numpy as np
from common import digest, packed, file_hash, inside, write_json

DTYPES = {'F32': '<f4', 'F16': '<f2', 'BF16': '<u2'}


def quantize(value, dtype):
    x = np.asarray(value, dtype=np.float32)
    if not np.isfinite(x).all():
        raise ValueError('Nonfinite parameter')
    if dtype == 'BF16':
        bits = x.copy().view(np.uint32)
        bits = ((bits + np.uint32(0x7fff) + ((bits >> 16) & 1)) >> 16) << 16
        x = bits.view(np.float32)
    elif dtype == 'F16':
        with np.errstate(over='ignore'):
            x = x.astype(np.float16).astype(np.float32)
    elif dtype != 'F32':
        raise ValueError('Noneditable dtype: ' + dtype)
    if not np.isfinite(x).all():
        raise ValueError('Edit overflows effective dtype')
    return x.copy()


class TensorSource:
    def __init__(self, root, aliases=None, effective_dtype='BF16'):
        self.root = Path(root)
        self.effective_dtype = effective_dtype
        index = json.loads((self.root / 'model.safetensors.index.json').read_text())
        self.entries = {}
        self.file_hashes = {}
        for shard in sorted(set(index['weight_map'].values())):
            path = inside(self.root, shard)
            self.file_hashes[shard] = file_hash(path)
            with path.open('rb') as f:
                length = struct.unpack('<Q', f.read(8))[0]
                if length > 64 * 1024**2:
                    raise ValueError('Oversized safetensors header')
                header = json.loads(f.read(length))
            for name, info in header.items():
                if name == '__metadata__':
                    continue
                if index['weight_map'].get(name) != shard or name in self.entries:
                    raise ValueError('Index/header mismatch')
                a, b = info['data_offsets']
                if a < 0 or b < a or 8 + length + b > path.stat().st_size:
                    raise ValueError('Invalid tensor offsets')
                self.entries[name] = dict(info, shard=shard, offset=8 + length + a)
        if set(self.entries) != set(index['weight_map']):
            raise ValueError('Missing indexed tensors')
        self.aliases = dict(aliases or {})
        for alias, canonical in self.aliases.items():
            if canonical not in self.entries or alias == canonical or canonical in self.aliases:
                raise ValueError('Invalid tied parameter map')
            if alias in self.entries and not np.array_equal(self.load(alias, canonicalize=False), self.load(canonical)):
                raise ValueError('Tied storage values differ')
        self.identity = digest(packed(dict(files=self.file_hashes, aliases=self.aliases, effective_dtype=effective_dtype)))

    def canonical(self, name):
        name = self.aliases.get(name, name)
        if name not in self.entries:
            raise KeyError(name)
        return name

    def catalog(self):
        return {n: dict(shape=e['shape'], dtype=e['dtype'], effective_dtype=self.effective_dtype, editable=e['dtype'] in DTYPES,
                        canonical=self.aliases.get(n, n)) for n, e in self.entries.items()} | {
            a: dict(shape=self.entries[n]['shape'], dtype=self.entries[n]['dtype'],
                    editable=self.entries[n]['dtype'] in DTYPES, canonical=n) for a, n in self.aliases.items()}

    def load(self, name, canonicalize=True):
        name = self.canonical(name) if canonicalize else name
        e = self.entries[name]
        if e['dtype'] not in DTYPES:
            raise ValueError('Only floating parameter reads supported')
        size = math.prod(e['shape']) * np.dtype(DTYPES[e['dtype']]).itemsize
        if e['data_offsets'][1] - e['data_offsets'][0] != size:
            raise ValueError('Tensor byte count mismatch')
        with inside(self.root, e['shard']).open('rb') as f:
            f.seek(e['offset'])
            raw = f.read(size)
        if len(raw) != size:
            raise ValueError('Truncated tensor')
        x = np.frombuffer(raw, dtype=DTYPES[e['dtype']])
        if e['dtype'] == 'BF16':
            x = (x.astype(np.uint32) << 16).view(np.float32)
        return quantize(x.astype(np.float32).reshape(e['shape']), self.effective_dtype)


class Candidates:
    def __init__(self, source, root, temporary_scalars, final_scalars):
        self.source, self.root = source, Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.temporary_scalars, self.final_scalars = temporary_scalars, final_scalars
        if not 0 < final_scalars <= temporary_scalars:
            raise ValueError('Invalid sparse support budgets')
        self.base_id = 'w0-' + source.identity

    def manifest(self, candidate):
        if candidate == self.base_id:
            return dict(id=candidate, base=self.base_id, parent=None, tensors={}, changed_scalars=0, l2=0.)
        path = inside(self.root, candidate)
        m = json.loads((path / 'manifest.json').read_text())
        if m['base'] != self.base_id or m['id'] != candidate:
            raise ValueError('Candidate base identity mismatch')
        content = {k:v for k,v in m.items() if k != 'id'}
        if 'c-' + digest(packed(content)) != candidate:
            raise ValueError('Candidate manifest changed')
        for e in m['tensors'].values():
            if file_hash(inside(path, e['file'])) != e['sha256']:
                raise ValueError('Candidate tensor changed')
        return m

    def load(self, candidate, name):
        name = self.source.canonical(name)
        m = self.manifest(candidate)
        if name not in m['tensors']:
            return self.source.load(name)
        return np.load(inside(self.root / candidate, m['tensors'][name]['file']), allow_pickle=False).copy()

    def commit(self, parent, edits, rationale):
        if not isinstance(rationale, str) or not rationale.strip():
            raise ValueError('A hypothesis/expectation is required')
        pm = self.manifest(parent)
        normalized = {}
        for name, value in edits.items():
            canonical = self.source.canonical(name)
            e = self.source.entries[canonical]
            x = quantize(value, self.source.effective_dtype)
            if list(x.shape) != e['shape']:
                raise ValueError('Parameter shape changed')
            if canonical in normalized and not np.array_equal(normalized[canonical], x):
                raise ValueError('Conflicting edits to tied parameter')
            normalized[canonical] = x
        folder = Path(tempfile.mkdtemp(prefix='.pending-', dir=self.root))
        tensors, total, norm2 = {}, 0, 0.
        try:
            for name in sorted(set(pm['tensors']) | set(normalized)):
                original = self.source.load(name)
                x = normalized[name] if name in normalized else self.load(parent, name)
                count = int(np.count_nonzero(x != original))
                total += count
                if total > self.temporary_scalars:
                    raise ValueError('Temporary scalar budget exceeded relative to W0')
                if not count:
                    continue
                norm2 += float(np.square(x.astype(np.float64) - original).sum())
                filename = digest(name.encode()) + '.npy'
                np.save(folder / filename, x, allow_pickle=False)
                tensors[name] = dict(file=filename, sha256=file_hash(folder / filename), changed=count,
                                     shape=list(x.shape), dtype=self.source.effective_dtype)
            m = dict(base=self.base_id, parent=parent, tensors=tensors, changed_scalars=total,
                     l2=math.sqrt(norm2), rationale=rationale)
            candidate = 'c-' + digest(packed(m))
            m['id'] = candidate
            write_json(folder / 'manifest.json', m)
            destination = self.root / candidate
            if destination.exists():
                self.manifest(candidate)
            else:
                folder.rename(destination)
            return m
        finally:
            if folder.exists():
                shutil.rmtree(folder)

    def freeze(self, candidate):
        m = self.manifest(candidate)
        if m['changed_scalars'] > self.final_scalars:
            raise ValueError('Final scalar budget exceeded')
        return m
