"""CPU-only path adapter: call the unchanged author's checkpoint builder.

No checkpoint is built on import. No edited tensor or final patch is supplied here.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys


def build(source_root, model, edits, out):
    source_root, model, edits, out = map(lambda p: Path(p).resolve(), (source_root, model, edits, out))
    assert not out.exists(), "Use a new output directory; preserve historical checkpoints."
    assert model.is_dir() and edits.is_dir()
    manifest = json.loads((Path(__file__).parent / "sources.json").read_text())
    for name in ("profiles.py", "build_ckpt.py"):
        rel = "exp8_math/code/" + name
        entry = next(x for x in manifest["files"] if x["path"] == rel)
        data = (source_root / rel).read_bytes()
        assert hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest() == entry["git_blob_sha1"]
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ["MATHEDIT_PROFILE"] = "qwen35think"
    code = source_root / "exp8_math/code"
    sys.path.insert(0, str(code))
    import profiles
    assert Path(profiles.__file__).resolve() == code / "profiles.py"
    # Only bind the redacted deployment path; retain all scientific profile fields.
    profiles.PROFILES["qwen35think"]["model"] = str(model)
    spec = importlib.util.spec_from_file_location("author_build_ckpt", code / "build_ckpt.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.build(str(edits), str(out))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source-root", "model", "edits", "out"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    build(args.source_root, args.model, args.edits, args.out)
