"""Inspect the authorized official asset endpoint; never load a model or print a token."""
import argparse
import datetime
import importlib.metadata
import json
from pathlib import Path
import subprocess

from huggingface_hub import get_token

REPO = "meta-llama/Llama-3.1-8B-Instruct"
REVISION = "0e9e39f249a16976918f6564b8830bc894c89659"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--socks5", help="Optional temporary SSH transport, e.g. 127.0.0.1:18765")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    token = get_token()
    config = f'header = "Authorization: Bearer {token}"\n' if token else ""
    command = ["curl", "--config", "-", "--silent", "--show-error",
               "--connect-timeout", "10", "--max-time", "40"]
    if args.socks5:
        command += ["--socks5-hostname", args.socks5]

    def request(url, head=False):
        return subprocess.run(command + (["--head"] if head else ["--fail"]) + [url],
                              input=config, text=True, capture_output=True)

    info_result = request(f"https://huggingface.co/api/models/{REPO}/revision/{REVISION}?blobs=true")
    receipt = {"checked_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "repo": REPO, "revision": REVISION, "token_present": bool(token),
               "endpoint": "https://huggingface.co", "transport": "temporary_ssh_socks" if args.socks5 else "direct",
               "model_loaded": False, "gpu_inference_run": False,
               "metadata_curl_exit": info_result.returncode}
    if info_result.returncode:
        receipt["status"] = "network_or_metadata_access_failed"
    else:
        info = json.loads(info_result.stdout)
        assert info["id"] == REPO and info["sha"] == REVISION
        files = [{k: item[k] for k in ("rfilename", "size", "blobId", "lfs") if k in item}
                 for item in info["siblings"] if "/" not in item["rfilename"]]
        manifest = {"repo": REPO, "revision": REVISION, "endpoint": "https://huggingface.co",
                    "gated": info.get("gated"), "files": files, "downloaded": False}
        (args.output / "official-source-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        filename = next(item["rfilename"] for item in files if item["rfilename"].endswith(".safetensors"))
        access = request(f"https://huggingface.co/{REPO}/resolve/{REVISION}/{filename}", head=True)
        receipt.update(weight_access_file=filename, weight_access_curl_exit=access.returncode)
        receipt["http_status_lines"] = [line for line in access.stdout.splitlines() if line.startswith("HTTP/")]
        headers = {}
        for line in access.stdout.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                if key.lower() in {"x-error-code", "x-linked-etag", "x-linked-size", "x-repo-commit"}:
                    headers[key.lower()] = value.strip()
        receipt["access_headers"] = headers
        receipt["status"] = "blocked_official_gated_access" if headers.get("x-error-code") == "GatedRepo" else "access_checked_only"
    receipt["packages"] = {name: importlib.metadata.version(name) for name in
                           ("torch", "transformers", "safetensors", "huggingface_hub")}
    path = args.output / "official-access-receipt.json"
    path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "receipt": str(path), "revision": REVISION}))


if __name__ == "__main__":
    main()
