"""Read existing WSP-VLM JSON evidence only; no model libraries or remote writes."""
import gzip
import hashlib
import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
pattern = re.compile(rb'\bC-(\d{3,})(?=[:"\s])')
files, errors, scanned_bytes = [], [], 0
for base in ('external', 'experiments'):
    for scope in sorted((root / base).glob('wsp-vlm-*')):
        if any(s in scope.name for s in ('model-cache', 'processor-prep', 'screen-data')):
            continue
        for p in sorted(scope.rglob('*')):
            if not p.is_file() or p.is_symlink():
                continue
            parts = p.relative_to(scope).parts
            if any(s in parts for s in ('model', 'hub', '__pycache__', 'conversation')):
                continue
            if not (p.name.endswith(('.json', '.jsonl', '.json.gz', '.jsonl.gz'))):
                continue
            try:
                before = p.stat()
                digest = hashlib.sha256()
                found = set()
                carry = b''
                opener = gzip.open if p.suffix == '.gz' else open
                with opener(p, 'rb') as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                        digest.update(chunk)
                        scanned_bytes += len(chunk)
                        found.update(int(x) for x in pattern.findall(carry + chunk))
                        carry = chunk[-32:]
                after = p.stat()
                if found:
                    files.append(dict(path=str(p.relative_to(root)), group_ids=sorted(found),
                        bytes_on_disk=after.st_size, decoded_sha256=digest.hexdigest(),
                        changed_during_read=(before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns)))
            except (OSError, EOFError) as exc:
                errors.append(dict(path=str(p.relative_to(root)), error=str(exc)))
print(json.dumps(dict(root=str(root), scope='existing WSP-VLM JSON/JSONL and gzip; models/caches/conversation skipped; ID references conservatively count as exposed',
    files=files, errors=errors, scanned_decoded_bytes=scanned_bytes,
    all_group_ids=sorted({i for f in files for i in f['group_ids']}), model_calls=0), ensure_ascii=False))
