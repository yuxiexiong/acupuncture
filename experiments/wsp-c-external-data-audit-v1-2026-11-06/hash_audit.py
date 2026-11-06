"""CPU-only image identity checks; no model dependencies or network access."""
import collections
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.fft import dctn

from prepare_review import DATA, HERE, ROOT, load_rows


def fingerprint(path):
    with Image.open(path) as source:
        im = source.convert('RGB')
        low = dctn(np.asarray(im.convert('L').resize((32, 32)), dtype=float), norm='ortho')[:8, :8].ravel()
        bits = low > np.median(low[1:])
        return dict(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    pixel_sha256=hashlib.sha256(str(im.size).encode() + im.tobytes()).hexdigest(),
                    phash=f'{sum(int(b) << i for i,b in enumerate(bits)):016x}')


def map_old_pixels(cross_old, old_rows):
    ledger_path = ROOT/'experiments/wsp-c-data-capacity-audit-v1-2026-11-06/source-ledger.json'
    if ledger_path.exists():
        ledger = json.loads(ledger_path.read_text())
    else:
        import gzip
        with gzip.open(str(ledger_path)+'.gz','rt') as f:
            ledger = json.load(f)
    cache, result = {}, []
    for r in cross_old:
        image_path=r['id'].split(':',1)[1]
        im=np.asarray(Image.open(DATA/'whatif'/image_path.lstrip('./')).convert('RGB').resize((350,300)),dtype=np.float32)
        matches=[]
        for near in r['near']:
            _,row,field=near['id'].split(':');row=int(row)
            if (row,field) not in cache:
                cache[row,field]=np.asarray(Image.open(ROOT/old_rows[row][field]['local_path']).convert('RGB'),dtype=np.float32)
            matches.append((float(np.abs(im-cache[row,field]).mean()),row,field,near['distance']))
        mae,row,field,distance=min(matches)
        result.append(dict(image=image_path,old_row=row,old_group=old_rows[row]['exact_group_id'],old_field=field,
                           mae_0_to_255=mae,phash_distance=distance,exposure=ledger[row]['status']))
    (HERE/'old-pixel-mapping.json').write_text(json.dumps(result,indent=2)+'\n')


def main():
    rows = load_rows()
    records = []
    for name in sorted({r['image'] for r in rows}):
        records.append(dict(id='whatif:'+name, **fingerprint(DATA/'whatif'/name.lstrip('./'))))
    for p in sorted((DATA/'vlind').glob('*.jpg')):
        records.append(dict(id='vlind:'+p.name, **fingerprint(p)))
    old_rows = json.loads((ROOT/'experiments/wsp-vlm-screen-data-v1-2026-11-05/audit/C_rows.json').read_text())
    old = [dict(id=f"old:{r['row_id']}:{field}", **fingerprint(ROOT/r[field]['local_path']))
           for r in old_rows for field in ('original_image', 'counterfact_image')]
    old_pixels = collections.defaultdict(list)
    for r in old:
        old_pixels[r['pixel_sha256']].append(r['id'])
    cross_old = []
    old_ph = [int(r['phash'],16) for r in old]
    for r in records:
        ph = int(r['phash'],16)
        near = [dict(id=o['id'], distance=bin(ph ^ oph).count('1'))
                for o, oph in zip(old,old_ph) if bin(ph ^ oph).count('1') <= 6]
        if near or r['pixel_sha256'] in old_pixels:
            cross_old.append(dict(id=r['id'], exact=old_pixels[r['pixel_sha256']], near=near))
    near_new = []
    phs = [int(r['phash'],16) for r in records]
    for i,r in enumerate(records):
        for j in range(i):
            distance = bin(phs[i]^phs[j]).count('1')
            if distance <= 6:
                near_new.append(dict(a=records[j]['id'], b=r['id'], distance=distance,
                                     exact=r['pixel_sha256']==records[j]['pixel_sha256']))
    (HERE/'image-fingerprints.json').write_text(json.dumps(records,indent=2)+'\n')
    (HERE/'image-dedup.json').write_text(json.dumps(dict(old_images=len(old),new_images=len(records),
        old_comparisons=len(old)*len(records), threshold=6, cross_old=cross_old, near_new=near_new),indent=2)+'\n')
    map_old_pixels(cross_old, old_rows)
    print(json.dumps(dict(old_images=len(old),new_images=len(records),cross_old_images=len(cross_old),
        cross_old_non_visual_counterfact=[r for r in cross_old if '/visual_counterfact/' not in r['id']],
        near_new_pairs=len(near_new))))


if __name__ == '__main__':
    main()
