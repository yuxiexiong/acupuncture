"""Check the delivered offline report against its archived sources, without inference."""
import base64
import collections
import gzip
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REPORT = ROOT / 'docs/Acupuncture_实验结果_导师展示_2026-10-28.html'
page = REPORT.read_text()
old = (HERE / 'original-report-20261028.html').read_text()
audit = json.loads((HERE / 'build-audit.json').read_text())
sha = lambda b: hashlib.sha256(b).hexdigest()
assert sha(page.encode()) == audit['output_sha256']
assert sha(old.encode()) == audit['base_html_sha256']
for path, digest in audit['sources'].items():
    assert sha(Path(path).read_bytes()) == digest, path

class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links, self.resources = [], [], []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.append(a['id'])
        if tag == 'a' and a.get('href', '').startswith('#'):
            self.links.append(a['href'][1:])
        if tag in ['script', 'img', 'iframe', 'link']:
            self.resources.extend(a[k] for k in ['src', 'href'] if k in a)

tags, prior = Tags(), Tags()
tags.feed(page)
prior.feed(old)
oldcounts = collections.Counter(prior.ids)
for ident, count in collections.Counter(tags.ids).items():
    assert count <= max(1, oldcounts[ident]), ('new duplicate id', ident)
assert set(tags.links) <= set(tags.ids)
assert not [r for r in tags.resources if r.startswith(('http:', 'https:', '//'))]
for pattern in [r'<svg\b.*?</svg>', r'<script\b.*?</script>']:
    for chunk in re.findall(pattern, old, re.S):
        assert chunk in page, 'old chart or script changed'
# Original textual sections are retained as ordered slices around the insertion anchors.
anchors = ['</style>', '<header>', '<section id="trace">', '<section id="direction">', '<section id="evidence">', '</body>']
parts = re.split('|'.join(map(re.escape, anchors)), old)
cursor = 0
for part in parts:
    if not part:
        continue
    pos = page.find(part, cursor)
    assert pos >= 0, 'an original content block was modified or removed'
    cursor = pos + len(part)

def script(ident):
    return re.search(r'<script id="' + ident + r'"[^>]*>(.*?)</script>', page, re.S).group(1)

data = json.loads(script('extended-data'))
raw = json.loads(gzip.decompress(base64.b64decode(script('answers-gzip'))))
assert {k: len(v) for k, v in raw.items()} == audit['data_counts'] == data['coverage']
assert len(audit['new_figures']) == 8
assert sum(len(v) for v in raw.values()) == 33882
assert all('localization' not in json.dumps(v, ensure_ascii=False) for v in raw.values())
assert all('localization' not in json.dumps(v, ensure_ascii=False) for v in data['results'].values())
locsources = [p for p in audit['sources'] if 'early-state-localization' in p]
assert len(locsources) == 1 and locsources[0].endswith('/CONTRACT.zh-CN.md')
assert not any('localization' in p.name for p in HERE.iterdir())

joint = raw['双针联合测量·全部31条件']
assert set(collections.Counter(r['condition_id'] for r in joint).values()) == {120}
assert len({(r['item_id'], r['condition_id']) for r in joint}) == 3720
for stage, count in [('开发', 193), ('新题确认', 145)]:
    rows = raw['早层深度比较·' + stage]
    counts = collections.Counter(r['condition_id'] for r in rows)
    assert len(counts) == count and set(counts.values()) == {24}
assert sum(r['status'] != 'completed' for k, rows in raw.items() if k.startswith(('早层', '时段', '局部')) for r in rows) == 676
withdraw = data['results']['撤针与重建·全部条件']
assert next(r['counts'] for r in withdraw if r['panel'] == '确认' and r['condition'] == 'N_L02_C5063_D+1' and r['step'] == 4) == [2, 18, 0, 0]
result = {
    'status': 'passed', 'html_sha256': sha(page.encode()),
    'original_content_blocks_preserved': len(parts),
    'original_svgs_preserved': len(re.findall(r'<svg\b', old)),
    'new_figures': 8, 'raw_archive_records': 33882,
    'raw_datasets': data['coverage'], 'source_files_checked': len(audit['sources']),
    'ongoing_experiment': 'contract and design only; no results or raw data',
    'checks': ['source hashes', 'original content and scripts', 'links and new IDs',
               'offline assets', 'gzip coverage', 'condition denominators',
               'NA retention', 'withdrawal counts', 'ongoing-result exclusion']
}
(HERE / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
print(json.dumps(result, ensure_ascii=False, indent=2))
