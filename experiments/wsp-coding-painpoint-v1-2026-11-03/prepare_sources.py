"""Fetch pinned public inputs only; no model calls or program execution."""
import gzip
import hashlib
import json
from pathlib import Path
import tarfile
import urllib.request

ROOT = Path('/workspace/acupuncture/external/wcp01')
SOURCES = {
    'mbpp.jsonl': 'https://raw.githubusercontent.com/google-research/google-research/f46ca8374b4cddef97ca4208ad986049d74d296a/mbpp/mbpp.jsonl',
    'HumanEvalPlus.jsonl.gz': 'https://github.com/evalplus/humanevalplus_release/releases/download/v0.1.10/HumanEvalPlus.jsonl.gz',
    'gsm8k-test.jsonl': 'https://raw.githubusercontent.com/openai/grade-school-math/3101c7d5072418e28b9008a6636bde82a006892c/grade_school_math/data/test.jsonl',
    'evalplus.tar.gz': 'https://codeload.github.com/evalplus/evalplus/tar.gz/26d6d00bb1fd0fa37f39c99d5290da67891d1c5e',
}


def main():
    raw = ROOT / 'sources'
    raw.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, url in SOURCES.items():
        p = raw / name
        if not p.exists():
            with urllib.request.urlopen(url, timeout=60) as response:
                data = response.read(50_000_001)
            if len(data) > 50_000_000:
                raise ValueError('unexpected source size')
            p.write_bytes(data)
        rows.append(dict(name=name, url=url, bytes=p.stat().st_size,
                         sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    vendor = ROOT / 'vendor'
    vendor.mkdir(exist_ok=True)
    with tarfile.open(raw / 'evalplus.tar.gz') as arc:
        for member in arc.getmembers():
            parts = Path(member.name).parts[1:]
            if not parts or parts[0] not in ('evalplus', 'LICENSE', 'requirements.txt'):
                continue
            if member.isfile() and '..' not in parts:
                dest = vendor.joinpath(*parts)
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(arc.extractfile(member).read())
    content = gzip.decompress((raw / 'HumanEvalPlus.jsonl.gz').read_bytes())
    (raw / 'HumanEvalPlus.jsonl').write_bytes(content)
    rows.append(dict(name='HumanEvalPlus.jsonl', bytes=len(content), sha256=hashlib.sha256(content).hexdigest()))
    counts = {name: len((raw / name).read_text().splitlines())
              for name in ('mbpp.jsonl', 'HumanEvalPlus.jsonl', 'gsm8k-test.jsonl')}
    assert counts == {'mbpp.jsonl': 974, 'HumanEvalPlus.jsonl': 164, 'gsm8k-test.jsonl': 1319}, counts
    receipt = dict(sources=rows, counts=counts, model_calls=0)
    (ROOT / 'sources-manifest.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
