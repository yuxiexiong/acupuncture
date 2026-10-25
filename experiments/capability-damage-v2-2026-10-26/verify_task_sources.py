"""Verify downloaded HF bytes against canonical pinned repository metadata."""
import argparse
import json
from pathlib import Path

from prepare_tasks import save_once, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hub-cache", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--expected", type=Path, default=Path(__file__).with_name("source_expected_files.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    expected = json.loads(args.expected.read_text())
    verified = []
    for repo, source in expected.items():
        revision = source["revision"]
        assert revision == manifest["dataset_revisions"][repo]
        snapshot = args.hub_cache / ("datasets--" + repo.replace("/", "--")) / "snapshots" / revision
        files = {row["path"]: row for row in source["files"]}
        configs = {config["dataset_name"] for config in manifest["task_configs"].values()
                   if config["dataset_path"] == repo}
        for config in configs:
            wanted = [name for name in files if name.startswith(config + "/") and name.endswith(".parquet")]
            assert wanted, (repo, config)
            for name in wanted:
                path = snapshot / name
                assert path.is_file(), f"Missing pinned source file: {path}"
                expected_hash = files[name]["lfs"]["sha256"]
                actual_hash = sha(path)
                assert actual_hash == expected_hash, f"Source hash mismatch: {path}"
                assert path.stat().st_size == files[name]["size"]
                verified.append({"repository": repo, "revision": revision, "path": name,
                                 "bytes": path.stat().st_size, "sha256": actual_hash})
        readme = snapshot / "README.md"
        assert sha(readme) == source["readme_sha256"]
        verified.append({"repository": repo, "revision": revision, "path": "README.md",
                         "bytes": readme.stat().st_size, "sha256": sha(readme)})
    receipt = {"status": "all_pinned_dataset_source_bytes_verified_against_official_huggingface_metadata",
               "manifest_sha256": sha(args.manifest), "expected_metadata_sha256": sha(args.expected),
               "verifier_sha256": sha(__file__), "files": sorted(verified, key=lambda x: (x["repository"], x["path"]))}
    save_once(args.output, json.dumps(receipt, indent=2, sort_keys=True).encode() + b"\n")
    print(json.dumps({"verified_files": len(verified), "output": str(args.output)}))


if __name__ == "__main__":
    main()
