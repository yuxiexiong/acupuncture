"""Download the two authorized model assets and verify their official HF hashes."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import subprocess
import shutil
import time

ROOT = Path(__file__).resolve().parent
SOURCES = json.loads((ROOT / "sources.json").read_text())


def download_ranges(url, destination, size):
    """Use bounded HTTP ranges because this endpoint limits each connection."""
    prefix = destination.stat().st_size if destination.exists() else 0
    width = (size - prefix + 15) // 16
    ranges = [(start, min(start + width, size) - 1)
              for start in range(prefix, size, width)] if width else []

    def fetch(bounds):
        start, end = bounds
        chunk = destination.with_name(destination.name + f".range-{start}-{end}")
        result = subprocess.run(["curl", "-fLsS", "--retry", "3", "--retry-delay", "3",
                                 "--connect-timeout", "15", "--max-time", "1200",
                                 "--range", f"{start}-{end}", "--output", str(chunk), url])
        if result.returncode or chunk.stat().st_size != end - start + 1:
            raise RuntimeError(f"Range download failed: {chunk}")
        return chunk

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        chunks = list(pool.map(fetch, ranges))
    with destination.open("ab") as output:
        for chunk in chunks:
            with chunk.open("rb") as source:
                shutil.copyfileobj(source, output, 8 * 1024 * 1024)
            chunk.unlink()


def verify(path, entry):
    if not path.is_file() or path.stat().st_size != entry["size"]:
        return None
    sha256 = hashlib.sha256()
    git_sha1 = hashlib.sha1(f"blob {entry['size']}\0".encode())
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            sha256.update(chunk)
            git_sha1.update(chunk)
    expected = entry.get("lfs", {}).get("oid", entry["oid"])
    actual = sha256.hexdigest() if "lfs" in entry else git_sha1.hexdigest()
    if actual != expected:
        return None
    return {"path": str(path), "bytes": entry["size"], "sha256": sha256.hexdigest(),
            "expected_hash": expected, "verification": "passed"}


def download(model):
    target = Path(model["target"])
    target.mkdir(parents=True, exist_ok=True)
    receipts = []
    name = model["repo"].split("/")[-1]
    with (ROOT / f"{name}-attempts.jsonl").open("a", buffering=1) as log:
        for entry in model["files"]:
            dest = target / entry["path"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            checked = verify(dest, entry)
            if checked:
                receipts.append({**checked, "transfer": "reused_verified_file"})
                continue
            if dest.exists():
                raise RuntimeError(f"Existing unverified destination: {dest}")
            urls = [f"https://hf-mirror.com/{model['repo']}/resolve/{model['revision']}/{entry['path']}",
                    f"https://modelscope.cn/models/{model['repo']}/resolve/master/{entry['path']}"]
            if entry["path"].endswith(".safetensors"):
                urls.reverse()
            for attempt, url in enumerate(urls, 1):
                partial = dest.with_name(dest.name + f".part-{attempt}")
                started = time.time()
                log.write(json.dumps({"event": "start", "file": entry["path"], "url": url,
                                      "time_unix": started}) + "\n")
                if entry["path"].endswith(".safetensors"):
                    download_ranges(url, partial, entry["size"])
                    result = subprocess.CompletedProcess([], 0)
                else:
                    result = subprocess.run(["curl", "-fLsS", "--retry", "3", "--retry-delay", "3",
                                         "--connect-timeout", "15", "--speed-limit", "1024",
                                         "--speed-time", "120", "--max-time", "3600",
                                         "--output", str(partial), url])
                checked = verify(partial, entry) if result.returncode == 0 else None
                log.write(json.dumps({"event": "end", "file": entry["path"], "url": url,
                                      "elapsed_seconds": round(time.time() - started, 2),
                                      "curl_exit_code": result.returncode,
                                      "verification": "passed" if checked else "failed"}) + "\n")
                if checked:
                    partial.rename(dest)
                    checked.update(path=str(dest), download_url=url)
                    receipts.append(checked)
                    print(f"VERIFIED {name}/{entry['path']}", flush=True)
                    break
            else:
                raise RuntimeError(f"Download or verification failed: {dest}")
    index = json.loads((target / "model.safetensors.index.json").read_text())
    assert all((target / shard).is_file() for shard in set(index["weight_map"].values()))
    receipt = {"repo": model["repo"], "revision": model["revision"], "target": str(target),
               "status": "all_files_verified", "files": receipts, "model_loaded": False,
               "inference_or_experiments_run": False, "completed_at_unix": time.time()}
    (ROOT / f"{name}-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(download, SOURCES["models"]))
    (ROOT / "download-complete.json").write_text(json.dumps({"status": "complete", "models": [
        {key: item[key] for key in ("repo", "revision", "target", "status")} for item in results
    ]}, indent=2) + "\n")
