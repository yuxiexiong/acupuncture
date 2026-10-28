"""Background continuation of the same official files, preserving existing prefixes."""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import time

from huggingface_hub import constants, get_token
import download_official_r01 as io


def main():
    started = time.monotonic()
    io.OUT = io.ROOT / "download-r02"
    io.OUT.mkdir(exist_ok=True)
    assert constants.HF_HOME == "/workspace/hf_ruizhixu"
    token = get_token()
    assert token
    response = io.curl("https://huggingface.co/api/whoami-v2", token=token,
                       extra=["--max-time", "60"])
    assert response.returncode == 0, "Official account verification failed"
    identity = json.loads(response.stdout)
    assert identity["name"].casefold() == "ruizhixu"
    manifest_path = io.ROOT / "official-source-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["repo"] == io.REPO and manifest["revision"] == io.REVISION
    weights = [item for item in manifest["files"] if item["rfilename"].endswith(".safetensors")]
    small = [item for item in manifest["files"] if item not in weights]
    receipts = []
    for item in small:
        checked = io.verify(io.TARGET / item["rfilename"], item)
        assert checked, f"Previously verified small file changed: {item['rfilename']}"
        receipts.append(checked)
    base = {"repo": io.REPO, "revision": io.REVISION, "target": str(io.TARGET),
            "username": identity["name"], "started_at_utc": io.now(), "pid": os.getpid(),
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "helper_sha256": hashlib.sha256(Path(io.__file__).read_bytes()).hexdigest(),
            "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            "previous_run": "download-r01", "route": "official_cdn_direct",
            "credential_home": constants.HF_HOME, "metadata_transport": "ssh_socks_127.0.0.1:18765",
            "model_loaded": False, "gpu_inference_run": False, "weight_worker_count": 4}
    io.save("start-receipt.json", base)

    def worker(item):
        final = io.TARGET / item["rfilename"]
        checked = io.verify(final, item)
        if checked:
            return checked
        assert not final.exists(), f"Existing unverified final file: {final}"
        partial = final.with_name(final.name + ".part")
        for attempt in range(1, 4):
            if partial.exists() and partial.stat().st_size == item["size"]:
                checked = io.verify(partial, item)
                if checked:
                    partial.replace(final)
                    return {**checked, "path": str(final)}
                partial.replace(partial.with_name(partial.name + f".r02-hash-failed-{attempt}"))
            url = io.resolve(item, token)
            before = time.monotonic()
            initial = partial.stat().st_size if partial.exists() else 0
            response = io.curl(url, proxy=False, extra=["--location", "--continue-at", "-",
                               "--max-time", "7200", "--speed-limit", "16384", "--speed-time", "90",
                               "--output", str(partial)])
            io.save(item["rfilename"] + f".attempt-{attempt}.json", {"curl_exit": response.returncode,
                    "initial_prefix_bytes": initial, "final_bytes": partial.stat().st_size if partial.exists() else 0,
                    "elapsed_seconds": time.monotonic() - before, "completed_at_utc": io.now()})
            if response.returncode == 0:
                checked = io.verify(partial, item)
                if checked:
                    partial.replace(final)
                    return {**checked, "path": str(final), "attempt": attempt}
                partial.replace(partial.with_name(partial.name + f".r02-hash-failed-{attempt}"))
        raise RuntimeError(f"Official download or full hash validation failed: {item['rfilename']}")

    def sizes():
        values = {}
        for item in weights:
            final = io.TARGET / item["rfilename"]
            part = final.with_name(final.name + ".part")
            selected = final if final.exists() else part
            values[item["rfilename"]] = selected.stat().st_size if selected.exists() else 0
        return values

    previous = sizes()
    previous_time = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        pending = {pool.submit(worker, item) for item in weights}
        while pending:
            done, pending = concurrent.futures.wait(pending, timeout=30, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                checked = future.result()
                receipts.append(checked)
                io.save(checked["file"] + ".verified.json", checked)
            stamp = time.monotonic()
            current = sizes()
            rows = []
            for item in weights:
                name = item["rfilename"]
                rate = (current[name] - previous[name]) / max(stamp - previous_time, 0.001)
                remaining = item["size"] - current[name]
                rows.append({"file": name, "bytes": current[name], "total_bytes": item["size"],
                             "recent_bytes_per_second": rate,
                             "eta_transfer_seconds": 0 if remaining == 0 else remaining / rate if rate > 0 else None})
            estimates = [row["eta_transfer_seconds"] for row in rows]
            progress = {"status": "downloading_or_verifying", "at_utc": io.now(), "pid": os.getpid(),
                        "bytes": sum(current.values()), "total_bytes": sum(item["size"] for item in weights),
                        "workers": rows, "hash_verified_weight_shards": len(receipts) - len(small),
                        "eta_transfer_seconds_slowest_shard": max(estimates) if all(x is not None for x in estimates) else None,
                        "eta_excludes": "Full-file hash verification and final CPU readiness checks"}
            io.save("progress.json", progress)
            print(json.dumps(progress), flush=True)
            previous, previous_time = current, stamp
    index = json.loads((io.TARGET / "model.safetensors.index.json").read_text())
    assert set(index["weight_map"].values()) == {item["rfilename"] for item in weights}
    io.save("receipt.json", {**base, "status": "all_files_verified", "files": receipts,
            "completed_at_utc": io.now(), "elapsed_seconds": time.monotonic() - started,
            "index_shard_coverage": "passed", "tokenizer_and_config_cpu_readiness": "pending"})
    print(json.dumps({"status": "all_files_verified", "target": str(io.TARGET)}), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        io.OUT.mkdir(exist_ok=True)
        io.save("failure-receipt.json", {"status": "failed", "error_type": type(error).__name__,
                 "message": str(error), "at_utc": io.now(), "partials_preserved": True,
                 "model_loaded": False, "gpu_inference_run": False})
        raise
