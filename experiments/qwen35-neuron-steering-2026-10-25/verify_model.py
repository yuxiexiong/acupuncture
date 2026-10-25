"""Verify all runtime files against the pinned official Hugging Face tree."""
import hashlib
import json
from pathlib import Path
import sys
import time

REVISION = "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"
root, tree = Path(sys.argv[1]), Path(sys.argv[2])
started = time.monotonic()
records = []
for item in json.loads(tree.read_text()):
    if item["path"] in (".gitattributes", "README.md"):
        continue
    path = root / item["path"]
    sha256 = hashlib.sha256()
    git_blob = hashlib.sha1(f'blob {item["size"]}\0'.encode())
    count = 0
    with path.open("rb") as file:
        while chunk := file.read(8 * 1024 * 1024):
            sha256.update(chunk)
            git_blob.update(chunk)
            count += len(chunk)
    actual = sha256.hexdigest() if "lfs" in item else git_blob.hexdigest()
    expected = item.get("lfs", item)["oid"]
    if count != item["size"] or actual != expected:
        raise ValueError(f'File differs from pinned official version: {item["path"]}')
    records.append({"file": item["path"], "bytes": count, "sha256": sha256.hexdigest(),
                    "expected_hf_hash": expected, "verified": True})
    print(json.dumps(records[-1]), flush=True)
receipt = {"base_repo": "Qwen/Qwen3.5-4B", "revision": REVISION,
           "official_tree_url": f"https://huggingface.co/api/models/Qwen/Qwen3.5-4B/tree/{REVISION}?recursive=true&expand=false",
           "status": "all_files_verified", "files": records,
           "transport": "Official HF small files; Qwen ModelScope weight shards via aria2, verified against HF hashes",
           "elapsed_seconds": time.monotonic() - started}
(root / "download_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
