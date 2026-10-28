#!/usr/bin/env python3
"""Freeze a small public FineWeb-Edu subset; not the author's shuffled sample."""
import concurrent.futures
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
RAW.mkdir(exist_ok=True)
MANIFEST = ROOT / "manifest.json"
if MANIFEST.exists():
    raise SystemExit("Preserve the existing manifest; this acquisition has already run.")

def now():
    return datetime.now(timezone.utc).isoformat()

def digest(data):
    return hashlib.sha256(data).hexdigest()

manifest = {
    "started_at": now(), "dataset": "HuggingFaceFW/fineweb-edu",
    "config": "sample-10BT", "split": "train", "row_range_inclusive": [0, 1099],
    "method": "Official datasets-server rows API; first 1100 rows, 100 rows per request.",
    "sampling_limit": "New fixed subset, not the original author's streaming shuffle(seed=0) sample.",
    "revision_limit": "The rows API responses do not establish a repository revision; content is pinned by saved response and JSONL SHA-256.",
    "repository_tip_observed_separately": "87f09149ef4734204d70ed1d046ddc9ca3f2b8f9",
    "status": "started", "pages": [],
}

def fetch(offset):
    url = "https://datasets-server.huggingface.co/rows?dataset=HuggingFaceFW%2Ffineweb-edu&config=sample-10BT&split=train&offset=" + str(offset) + "&length=100"
    record = {"offset": offset, "url": url, "requested_at": now()}
    try:
        with urlopen(url, timeout=45) as response:
            data = response.read()
            record["http_status"] = response.status
        target = RAW / ("rows-%04d.json" % offset)
        target.write_bytes(data)
        record.update(file=str(target.relative_to(ROOT)), bytes=len(data), sha256=digest(data))
        parsed = json.loads(data)
        rows = parsed["rows"]
        assert [r["row_idx"] for r in rows] == list(range(offset, offset + 100)), "Incomplete or unexpected row indices"
        assert not any(r.get("truncated_cells") for r in rows), "Truncated source cells"
        assert all(isinstance(r["row"].get("text"), str) and r["row"]["text"] for r in rows), "Missing text"
        record.update(row_count=len(rows), truncated_cells=0, status="passed")
    except Exception as error:
        record.update(status="failed", error=repr(error))
    record["finished_at"] = now()
    return record

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    for record in pool.map(fetch, range(0, 1100, 100)):
        manifest["pages"].append(record)
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

if all(p["status"] == "passed" for p in manifest["pages"]):
    rows = [row for page in manifest["pages"] for row in json.loads((ROOT / page["file"]).read_bytes())["rows"]]
    data = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows).encode()
    target = RAW / "fineweb-edu-sample-10BT-first-1100.jsonl"
    target.write_bytes(data)
    manifest.update(status="complete", output={"file": str(target.relative_to(ROOT)), "rows": len(rows), "bytes": len(data), "sha256": digest(data)})
else:
    manifest["status"] = "failed"
manifest["finished_at"] = now()
MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"status": manifest["status"], "output": manifest.get("output")}, ensure_ascii=False))
raise SystemExit(0 if manifest["status"] == "complete" else 1)
