"""Read existing WSP evidence, returning only aggregate counts and public C IDs."""
import gzip
import json
from pathlib import Path
import re
import sys

root = Path(sys.argv[1])
names = re.compile(rb'whatifvis|vlind|rome_size|vlms_are_biased|weight_z_image_turbo|/vilp/', re.I)
ids = re.compile(rb'\bC-(\d{3,})(?=[:"\s])')
found, hits, errors, changed, count, size = set(), {}, 0, 0, 0, 0
for base in ('external', 'experiments'):
    for scope in sorted((root / base).glob('wsp-vlm-*')):
        if any(s in scope.name for s in ('model-cache', 'processor-prep', 'screen-data')):
            continue
        for p in scope.rglob('*'):
            if not p.is_file() or p.is_symlink() or any(s in p.relative_to(scope).parts for s in ('model', 'hub', '__pycache__', 'conversation')):
                continue
            if not p.name.endswith(('.json', '.jsonl', '.json.gz', '.jsonl.gz', '.py')):
                continue
            try:
                before = p.stat()
                opener = gzip.open if p.suffix == '.gz' else open
                with opener(p, 'rb') as stream:
                    carry = b''
                    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                        size += len(chunk)
                        found.update(int(x) for x in ids.findall(carry + chunk))
                        for match in names.findall(carry + chunk):
                            key = match.decode().lower()
                            hits[key] = hits.get(key, 0) + 1
                        carry = chunk[-128:]
                after = p.stat()
                changed += (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns)
                count += 1
            except (OSError, EOFError):
                errors += 1
print(json.dumps(dict(files=count, decoded_bytes=size, c_ids=sorted(found), dataset_name_hits=hits,
                     errors=errors, changed_files=changed, model_calls=0)))
