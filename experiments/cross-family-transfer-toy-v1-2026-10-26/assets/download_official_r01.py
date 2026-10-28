"""Download the pinned official checkpoint; no model loading or GPU operations."""
import concurrent.futures
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import time
from urllib.parse import urlsplit

from huggingface_hub import constants, get_token

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "download-r01"
TARGET = Path("/workspace/models/Llama-3.1-8B-Instruct-0e9e39f2")
REPO = "meta-llama/Llama-3.1-8B-Instruct"
REVISION = "0e9e39f249a16976918f6564b8830bc894c89659"
PROXY = "127.0.0.1:18765"


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save(name, data):
    path = OUT / name
    partial = path.with_suffix(path.suffix + ".tmp")
    partial.write_text(json.dumps(data, indent=2) + "\n")
    partial.replace(path)


def curl(url, *, token=None, proxy=True, extra=()):
    # Credentials and CDN signed URLs are passed through stdin, never argv/logs.
    config = 'url = "' + url.replace('"', '\\"') + '"\n'
    if token:
        config += 'header = "Authorization: Bearer ' + token + '"\n'
    command = ["curl", "--config", "-", "--silent", "--show-error", "--fail",
               "--connect-timeout", "10"]
    if proxy:
        command += ["--socks5-hostname", PROXY]
    return subprocess.run(command + list(extra), input=config, text=True, capture_output=True)


def verify(path, item):
    if not path.is_file() or path.stat().st_size != item["size"]:
        return None
    sha = hashlib.sha256()
    blob = hashlib.sha1(f"blob {item['size']}\0".encode())
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            sha.update(chunk)
            if not item.get("lfs"):
                blob.update(chunk)
    expected = item["lfs"]["sha256"] if item.get("lfs") else item["blobId"]
    observed = sha.hexdigest() if item.get("lfs") else blob.hexdigest()
    if observed != expected:
        return None
    return {"file": item["rfilename"], "path": str(path), "bytes": item["size"],
            "sha256": sha.hexdigest(), "official_expected_hash": expected,
            "official_hash_type": "sha256" if item.get("lfs") else "git_blob_sha1",
            "verification": "passed"}


def resolve(item, token):
    url = f"https://huggingface.co/{REPO}/resolve/{REVISION}/{item['rfilename']}"
    response = curl(url, token=token, extra=["--head", "--max-time", "60"])
    if response.returncode:
        raise RuntimeError(f"Official HEAD failed for {item['rfilename']}: curl={response.returncode}")
    headers = {}
    for line in response.stdout.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.lower()] = value.strip()
    assert headers.get("x-repo-commit") == REVISION
    assert headers.get("x-linked-etag", "").strip('"') == item["lfs"]["sha256"]
    assert int(headers["x-linked-size"]) == item["size"]
    location = headers["location"]
    assert urlsplit(location).scheme == "https"
    return location


def main():
    started = time.monotonic()
    OUT.mkdir(exist_ok=True)
    TARGET.mkdir(parents=True, exist_ok=True)
    assert constants.HF_HOME == "/workspace/hf_ruizhixu"
    token = get_token()
    assert token
    response = curl("https://huggingface.co/api/whoami-v2", token=token,
                    extra=["--max-time", "60"])
    assert response.returncode == 0, "Official account verification failed"
    identity = json.loads(response.stdout)
    assert identity["name"].casefold() == "ruizhixu", "Wrong account"
    source = json.loads((ROOT / "official-source-manifest.json").read_text())
    assert source["repo"] == REPO and source["revision"] == REVISION
    files = source["files"]
    small = [item for item in files if not item["rfilename"].endswith(".safetensors")]
    weights = [item for item in files if item["rfilename"].endswith(".safetensors")]
    base_receipt = {"repo": REPO, "revision": REVISION, "target": str(TARGET),
                    "username": identity["name"], "started_at_utc": now(),
                    "model_loaded": False, "gpu_inference_run": False,
                    "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    "manifest_sha256": hashlib.sha256((ROOT / "official-source-manifest.json").read_bytes()).hexdigest()}
    save("start-receipt.json", base_receipt)

    def small_file(item):
        path = TARGET / item["rfilename"]
        checked = verify(path, item)
        if checked:
            return checked
        assert not path.exists(), f"Existing unverified file: {path}"
        partial = path.with_name(path.name + ".part")
        url = f"https://huggingface.co/{REPO}/resolve/{REVISION}/{item['rfilename']}"
        response = curl(url, token=token, extra=["--location", "--retry", "2", "--max-time", "180", "--output", str(partial)])
        assert response.returncode == 0, f"Small file download failed: {item['rfilename']}, curl={response.returncode}"
        checked = verify(partial, item)
        assert checked, f"Small file hash failed: {item['rfilename']}"
        partial.replace(path)
        return {**checked, "path": str(path)}

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        receipts = list(pool.map(small_file, small))
    save("small-files-receipt.json", {**base_receipt, "status": "small_files_verified", "files": receipts, "completed_at_utc": now()})
    print(json.dumps({"event": "small_files_verified", "count": len(receipts), "target": str(TARGET)}), flush=True)

    signed_url = resolve(weights[0], token)
    probe_bytes = 16 * 1024 * 1024

    def probe(proxy):
        path = OUT / ("route-socks-probe.bin" if proxy else "route-direct-probe.bin")
        before = time.monotonic()
        response = curl(signed_url, proxy=proxy, extra=["--location", "--range", f"0-{probe_bytes-1}",
                        "--max-time", "30", "--max-filesize", str(probe_bytes), "--output", str(path)])
        elapsed = time.monotonic() - before
        size = path.stat().st_size if path.exists() else 0
        return {"route": "ssh_socks" if proxy else "official_cdn_direct", "curl_exit": response.returncode,
                "bytes": size, "elapsed_seconds": elapsed, "bytes_per_second": size / elapsed,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if size == probe_bytes else None,
                "passed": response.returncode == 0 and size == probe_bytes}

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        probes = list(pool.map(probe, [False, True]))
    passing = [probe for probe in probes if probe["passed"]]
    assert passing, "Neither official CDN transport passed the bounded range probe"
    if len(passing) == 2:
        assert passing[0]["sha256"] == passing[1]["sha256"], "Transport probe bytes differ"
    route = max(passing, key=lambda probe: probe["bytes_per_second"])["route"]
    save("transport-receipt.json", {"probes": probes, "selected_route": route,
         "official_cdn_host": urlsplit(signed_url).hostname, "selection": "fastest successful 16 MiB route; shared live network, not isolated benchmark"})
    print(json.dumps({"event": "transport_selected", "route": route, "probes": probes}), flush=True)

    def weight_file(item):
        path = TARGET / item["rfilename"]
        checked = verify(path, item)
        if checked:
            return checked
        assert not path.exists(), f"Existing unverified file: {path}"
        partial = path.with_name(path.name + ".part")
        for attempt in range(1, 4):
            location = resolve(item, token)
            before = time.monotonic()
            response = curl(location, proxy=route == "ssh_socks", extra=["--location", "--continue-at", "-",
                            "--max-time", "7200", "--speed-limit", "16384", "--speed-time", "90", "--output", str(partial)])
            save(item["rfilename"] + f".attempt-{attempt}.json", {"curl_exit": response.returncode,
                 "elapsed_seconds": time.monotonic() - before, "bytes": partial.stat().st_size if partial.exists() else 0,
                 "route": route, "completed_at_utc": now()})
            if response.returncode:
                continue
            checked = verify(partial, item)
            if checked:
                partial.replace(path)
                return {**checked, "path": str(path), "attempt": attempt}
            partial.replace(partial.with_name(partial.name + f".hash-failed-{attempt}"))
        raise RuntimeError(f"Weight download or hash verification failed: {item['rfilename']}")

    total = sum(item["size"] for item in weights)
    transfer_started = time.monotonic()
    previous_bytes = 0
    previous_time = transfer_started
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        pending = {pool.submit(weight_file, item) for item in weights}
        while pending:
            done, pending = concurrent.futures.wait(pending, timeout=30, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                receipt = future.result()
                receipts.append(receipt)
                save(receipt["file"] + ".verified.json", receipt)
            stamp = time.monotonic()
            downloaded = 0
            for item in weights:
                final = TARGET / item["rfilename"]
                part = final.with_name(final.name + ".part")
                chosen = final if final.exists() else part
                downloaded += min(chosen.stat().st_size, item["size"]) if chosen.exists() else 0
            speed = (downloaded - previous_bytes) / max(stamp - previous_time, 0.001)
            progress = {"event": "weight_progress", "at_utc": now(), "bytes": downloaded, "total_bytes": total,
                        "percent": downloaded / total * 100, "recent_bytes_per_second": speed,
                        "eta_transfer_seconds": (total - downloaded) / speed if speed > 0 else None,
                        "hash_verified_weight_shards": len(receipts) - len(small), "total_weight_shards": len(weights),
                        "elapsed_transfer_seconds": stamp - transfer_started, "route": route}
            save("progress.json", progress)
            print(json.dumps(progress), flush=True)
            previous_bytes, previous_time = downloaded, stamp
    index = json.loads((TARGET / "model.safetensors.index.json").read_text())
    assert set(index["weight_map"].values()) == {item["rfilename"] for item in weights}
    save("receipt.json", {**base_receipt, "status": "all_files_verified", "files": receipts,
         "route": route, "completed_at_utc": now(), "elapsed_seconds": time.monotonic() - started,
         "weight_bytes": total, "index_shard_coverage": "passed", "tokenizer_and_config_cpu_readiness": "pending"})
    print(json.dumps({"event": "all_files_verified", "target": str(TARGET), "weight_bytes": total}), flush=True)


if __name__ == "__main__":
    main()
