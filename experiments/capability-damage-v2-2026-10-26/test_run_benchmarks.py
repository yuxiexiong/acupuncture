"""Regression: Unicode separators inside JSON strings are not JSONL records."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from run_benchmarks import read_rows

expected = [{"context": "a\u2028b\u2029c\x85d\nnext line"}, {"context": "second question"}]
with TemporaryDirectory() as directory:
    path = Path(directory) / "items.jsonl"
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in expected))
    assert read_rows(path) == expected
print("PASS: JSONL preserves embedded Unicode separators and escaped newlines")
