"""Download public, author-selected representative images; no model imports."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'external/wsp-c-external-data-audit-v1-2026-11-06'
REV = '0aa47d9387f4c9a554d56067dd51900315954c81'
BASE = 'https://huggingface.co/datasets/klee972/VLind-Bench'

def main():
    info = json.load(urllib.request.urlopen(BASE.replace('/datasets/', '/api/datasets/') + '/revision/' + REV))
    (OUT / 'vlind-info.json').write_text(json.dumps(info))
    paths = [r['rfilename'] for r in info['siblings']]
    rows = json.loads((OUT / 'vlind-data.json').read_text())
    jobs = []
    for r in rows:
        if max(r['aggregated_human_label_good_images'].values()) < 2:
            continue
        for kind in ('counterfactual', 'factual'):
            prefix = f"VLind-Bench Dataset/images/{kind}/{r['concept']}/{r['context_id']}_"
            name = r['best_img_id'] if kind == 'counterfactual' else '0'
            matches = [p for p in paths if p.startswith(prefix) and p.endswith('/' + name + '.jpg')]
            assert len(matches) == 1, (prefix, matches)
            jobs.append((r['context_id'], kind, matches[0]))

    def get(job):
        i, kind, remote = job
        local = OUT / 'vlind' / f'{i}_{kind}.jpg'
        local.parent.mkdir(exist_ok=True)
        url = BASE + '/resolve/' + REV + '/' + urllib.parse.quote(remote)
        if not local.exists():
            local.write_bytes(urllib.request.urlopen(url, timeout=60).read())
        return dict(context_id=i, kind=kind, path=remote, local=str(local.relative_to(ROOT)),
                    bytes=local.stat().st_size, sha256=hashlib.sha256(local.read_bytes()).hexdigest())
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        receipts = []
        for r in pool.map(get, jobs):
            receipts.append(r)
            if len(receipts) % 50 == 0:
                print('downloaded', len(receipts), '/', len(jobs), flush=True)
    (OUT / 'vlind-downloads.json').write_text(json.dumps(receipts, indent=2))
    print('DONE', len(receipts), flush=True)

if __name__ == '__main__':
    main()
