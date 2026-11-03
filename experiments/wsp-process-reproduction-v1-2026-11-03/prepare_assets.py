"""Download pinned WSP inputs and record hashes; never loads a model."""
import argparse
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path


def digest(path, kind):
    h = hashlib.sha1() if kind == "git_blob_sha1" else hashlib.sha256()
    if kind == "git_blob_sha1":
        h.update(f"blob {path.stat().st_size}\0".encode())
    with path.open("rb") as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--model-manifest", type=Path, default=Path(__file__).with_name("model_manifest.json"))
    p.add_argument("--four-b", type=Path, required=True)
    args = p.parse_args()
    args.root.mkdir(parents=True, exist_ok=True)
    receipt = {"started_unix": time.time(), "assets": [], "failures": []}
    receipt_path = args.root / "asset_receipt.json"

    def flush():
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")

    def obtain(path, size, kind, expected, urls):
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.stat().st_size == size and digest(path, kind) == expected:
            url = "existing_verified"
        else:
            partial = path.with_name(path.name + ".wsp-partial")
            for url in urls:
                try:
                    subprocess.run(["curl", "--fail", "--location", "--silent", "--show-error",
                                    "--connect-timeout", "20", "--max-time", "900",
                                    "--speed-time", "60", "--speed-limit", "1024",
                                    "--output", str(partial), url], check=True, timeout=930)
                    if partial.stat().st_size != size or digest(partial, kind) != expected:
                        raise ValueError("size or pinned hash mismatch")
                    partial.replace(path)
                    break
                except Exception as e:
                    receipt["failures"].append({"url": url, "error": str(e), "time": time.time()})
                    flush()
            else:
                raise RuntimeError(f"No validated download for {path.name}")
        entry = {"path": str(path), "size": size, kind: expected,
                 "sha256": digest(path, "sha256"), "source": url}
        receipt["assets"].append(entry)
        flush()
        print(json.dumps({"verified": str(path), "size": size}), flush=True)

    upstream = json.loads(args.manifest.read_text())
    receipt["upstream_revision"] = upstream["revision"]
    for item in upstream["files"]:
        url = f'https://raw.githubusercontent.com/{upstream["repository"]}/{upstream["revision"]}/{item["path"]}'
        obtain(args.root / "observer-upstream" / item["path"], item["size"],
               "git_blob_sha1", item["git_blob_sha1"],
               [url, f'https://cdn.jsdelivr.net/gh/{upstream["repository"]}@{upstream["revision"]}/{item["path"]}'])

    metadata = json.loads(args.model_manifest.read_text())
    revision = metadata["revision"]
    receipt["zero_eight_b_revision"] = revision
    for item in metadata["files"]:
        name = item["path"]
        kind, expected = item["hash_kind"], item["hash"]
        destination = args.root / "raw-Qwen3.5-0.8B" / name
        reusable = args.four_b / name
        if not destination.exists() and reusable.exists() and reusable.stat().st_size == item["size"] and digest(reusable, kind) == expected:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(reusable, destination)
        urls = [f"https://hf-mirror.com/Qwen/Qwen3.5-0.8B/resolve/{revision}/{name}",
                f"https://modelscope.cn/models/Qwen/Qwen3.5-0.8B/resolve/master/{name}"]
        if name.endswith(".safetensors"):
            urls.reverse()
        obtain(destination, item["size"], kind, expected, urls)

    for name, size, sha in [
        ("model.safetensors-00001-of-00002.safetensors", 5329398688,
         "26a93f066e1916adb13453dae5a0c707c0fbc71299ed98779571a907b8e74c61"),
        ("model.safetensors-00002-of-00002.safetensors", 3990429408,
         "cb544bd9bfae93dc59b0f22b292f5933573854a7f9b97835c67060d7d910e188")]:
        obtain(args.four_b / name, size, "sha256", sha, [])
    receipt["completed_unix"] = time.time()
    receipt["status"] = "all_listed_assets_verified"
    flush()


if __name__ == "__main__":
    main()
