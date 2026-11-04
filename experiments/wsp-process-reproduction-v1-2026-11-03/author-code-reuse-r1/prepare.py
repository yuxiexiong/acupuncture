"""Fetch pinned public sources and extract original actions. Never execute them."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent


def blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def prepare(root):
    manifest = json.loads((HERE / "sources.json").read_text())
    verified = []
    for entry in manifest["files"]:
        path = root / "upstream" / entry["path"]
        if path.exists():
            data = path.read_bytes()
        else:
            url = ("https://raw.githubusercontent.com/" + manifest["repository"] + "/"
                   + manifest["revision"] + "/" + entry["path"])
            with urlopen(url, timeout=60) as response:
                data = response.read()
        assert blob_sha(data) == entry["git_blob_sha1"], entry["path"]
        assert len(data) == entry["size"], entry["path"]
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        verified.append({"path": entry["path"], "sha256": hashlib.sha256(data).hexdigest()})

    log = root / "upstream/exp8_math/runs/p50c/tool_calls.jsonl"
    actions = []
    for line, raw in enumerate(log.read_text().split("\n"), 1):
        if not raw.strip():
            continue
        row = json.loads(raw)
        kind = row["kind"]
        item = {"line": line, "kind": kind}
        if kind == "python":
            # Exact logged code, no added prelude, rewritten constants or author output.
            body = row["code"].encode()
            suffix = ".py"
            try:
                ast.parse(row["code"])
                item["syntax"] = "valid"
            except SyntaxError as exc:
                item["syntax"] = str(exc)  # Preserve original failures too.
        elif kind == "forward":
            # JSON formatting changes; the request object must be exactly equal.
            body = (json.dumps(row["request"], ensure_ascii=False, indent=2) + "\n").encode()
            assert json.loads(body) == row["request"]
            suffix = ".json"
            item["author_attempt"] = row.get("k")
        else:
            item["status"] = "non-executable log entry retained in source"
            actions.append(item)
            continue
        path = root / "actions" / (f"{line:03d}-{kind}" + suffix)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            assert path.read_bytes() == body, path
        else:
            path.write_bytes(body)
        item.update(path=str(path.relative_to(root)), sha256=hashlib.sha256(body).hexdigest())
        actions.append(item)

    receipt = {"status": "SOURCE_IDENTITY_VERIFIED_NOT_RUNTIME_ACCEPTED", "execution_enabled": False,
               "source_revision": manifest["revision"], "files": verified, "actions": actions,
               "final_patch_downloaded": False,
               "blockers": ["Exp8 persistent kernel/prelude not published",
                            "Exp8 generation/teacher-forced server not published",
                            "Published evaluator imports unavailable modules"]}
    (root / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    # CPU acceptance fixtures: unchanged function definitions, never author output.
    fixtures = []
    for line, names in ((13, ("clear_edits", "mlp_direction_edit")), (98, ("set_subset_edit",))):
        code = (root / "actions" / f"{line:03d}-python.py").read_text()
        for node in ast.parse(code).body:
            if isinstance(node, ast.FunctionDef) and node.name in names:
                source = ast.get_source_segment(code, node)
                fixtures.append({"action": line, "name": node.name, "source": source,
                                 "sha256": hashlib.sha256(source.encode()).hexdigest()})
    (root / "function-fixture.json").write_text(json.dumps(fixtures, indent=2) + "\n")
    requests = [{"source_pass": r["k"], "request": r["request"], "author_lengths": r["result"].get("lengths")}
                for r in (json.loads(s) for s in log.read_text().splitlines())
                if r["kind"] == "forward" and r["result"].get("ok")]
    (root / "interface-requests.json").write_text(json.dumps(requests, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.out.resolve())
    print(json.dumps({"status": result["status"], "files": len(result["files"]),
                      "actions": len(result["actions"]), "execution_enabled": False}))
