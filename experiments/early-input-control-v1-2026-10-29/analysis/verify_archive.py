"""Verify a run archive (.tar.zst) locally against the worker receipts it contains, without extracting.

python analysis/verify_archive.py ARCHIVE.tar.zst OUT_JSON
"""
import hashlib
import json
import subprocess
import sys
import tarfile
from datetime import datetime, timezone


def main(archive, out):
    proc = subprocess.Popen(['zstd', '-dc', archive], stdout=subprocess.PIPE)
    hashes, receipts, sizes = {}, {}, 0
    with tarfile.open(fileobj=proc.stdout, mode='r|') as tar:
        for member in tar:
            if not member.isfile():
                continue
            data = tar.extractfile(member).read()
            sizes += len(data)
            hashes[member.name] = hashlib.sha256(data).hexdigest()
            if member.name.endswith('/receipt.json') and '/worker-' in member.name:
                receipts[member.name] = json.loads(data)
    assert proc.wait() == 0
    checked, missing, mismatched = 0, [], []
    for name, receipt in receipts.items():
        root = name.rsplit('/', 1)[0]
        assert receipt['status'] == 'completed', name
        for relative, digest in {**receipt['record_hashes'], **receipt['asset_hashes']}.items():
            got = hashes.get(f'{root}/{relative}')
            checked += 1
            if got is None:
                missing.append(f'{root}/{relative}')
            elif got != digest:
                mismatched.append(f'{root}/{relative}')
    archive_sha = hashlib.sha256(open(archive, 'rb').read()).hexdigest()
    value = {'status': 'passed' if checked and not missing and not mismatched else 'failed', 'archive': archive,
             'archive_sha256': archive_sha, 'files_in_archive': len(hashes), 'uncompressed_bytes': sizes,
             'receipt_listed_files_checked': checked, 'missing': missing, 'mismatched': mismatched,
             'workers': sorted(receipts), 'verified_at': datetime.now(timezone.utc).isoformat()}
    with open(out, 'x') as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in value.items() if k not in ('missing', 'mismatched')}, indent=1), len(missing), len(mismatched))


if __name__ == '__main__':
    main(*sys.argv[1:3])
