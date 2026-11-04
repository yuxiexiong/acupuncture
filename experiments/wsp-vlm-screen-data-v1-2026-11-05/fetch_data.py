"""Download only B/C data at pinned revisions. No model dependencies."""
import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

SOURCES = {
    "B": ("wei2912/SPHERE-VLM", "25f0922a5290505fee8252e2dbb7771ff2d8afe9", [
        "README.md", "prepare_parquet.py",
        "single_skill/counting_only-paired-position_and_counting.parquet",
        "single_skill/counting_only-paired-distance_and_counting.parquet",
        "combine_2_skill/position_and_counting.parquet",
        "combine_2_skill/distance_and_counting.parquet"]),
    "C": ("mgolov/Visual-Counterfact", "f8cd0b2335356b0f01a164df0cac7403f56a6c83", [
        "README.md", "data/size-00000-of-00001.parquet"]),
}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("root", type=Path)
    p.add_argument("--endpoint", default="https://huggingface.co")
    args = p.parse_args()
    manifest = []
    for candidate, (repo, revision, files) in SOURCES.items():
        with urllib.request.urlopen(f"{args.endpoint}/api/datasets/{repo}/revision/{revision}", timeout=60) as response:
            info = json.load(response)
        assert info["sha"] == revision
        folder = args.root / candidate
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "revision.json").write_text(json.dumps(info, indent=2))
        for name in files:
            dest = folder / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            url = f"{args.endpoint}/datasets/{repo}/resolve/{revision}/{name}"
            temporary = dest.with_suffix(dest.suffix + ".partial")
            with urllib.request.urlopen(url, timeout=60) as response, temporary.open("wb") as out:
                while chunk := response.read(1024 * 1024):
                    out.write(chunk)
            temporary.replace(dest)
            item = dict(candidate=candidate, repo=repo, revision=revision, path=name,
                        download_url=url, bytes=dest.stat().st_size,
                        sha256=hashlib.sha256(dest.read_bytes()).hexdigest())
            manifest.append(item)
            (args.root / "download_manifest.json").write_text(json.dumps(manifest, indent=2))
            print(json.dumps(item), flush=True)

if __name__ == "__main__":
    main()
