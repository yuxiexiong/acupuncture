"""CPU-only provenance grouping and deterministic review sheets."""
import collections
import json
from pathlib import Path
import re
import textwrap
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'external/wsp-c-external-data-audit-v1-2026-11-06'
HERE = Path(__file__).resolve().parent

def group(r):
    source, name = r['image'].split('/')[-2:]
    if source == 'vlind' or (source == 'generated' and not name.startswith('weight')):
        return 'vlind-context:' + name.split('_')[0]
    if source == 'vilp':
        return 'vilp:' + name.split('_')[1]
    if source == 'rome_size':
        return 'rome:' + name.rsplit('_', 1)[0]
    if source == 'visual_counterfact':
        return 'old-corpus:' + name.rsplit('.', 1)[0]
    if source == 'vlms_are_biased':
        # Conservative: one entity/brand family, not one edited image.
        stem = name.rsplit('.', 1)[0]
        stem = re.sub(r'_[0-9_]+$', '', stem)
        return 'count-family:' + stem.split('-')[0]
    if source in ('weight_z_image_turbo', 'generated'):
        return 'weight-pair:' + '|'.join(sorted((r['context_answer'].lower(), r['prior_answer'].lower())))
    raise ValueError(source)

def load_rows():
    return [dict(json.loads(s), split=f.stem, row=i) for f in sorted(DATA.glob('*.jsonl'))
            for i, s in enumerate(f.read_text().splitlines())]

def main():
    rows = load_rows()
    native = {r['context_id']:r for r in json.loads((DATA / 'vlind-data.json').read_text())}
    groups = collections.defaultdict(list)
    for r in rows:
        r['source_group'] = group(r)
        groups[group(r)].append(r)
    chosen = []
    for key, variants in sorted(groups.items()):
        if key.startswith(('old-corpus:', 'rome:')):
            continue
        def priority(r):
            direct = not r['split'].startswith('size')
            is_native_best = False
            if '/vlind/' in r['image']:
                cid = int(r['image'].split('/')[-1].split('_')[0])
                is_native_best = r['image'].rsplit('_',1)[1].split('.')[0] == native[cid]['best_img_id']
            return (direct, not is_native_best, '/generated/' in r['image'], r['split'], r['row'])
        r = dict(min(variants, key=priority), variants=len(variants))
        chosen.append(r)
    (HERE / 'whatif-representatives.json').write_text(json.dumps(chosen, indent=2))
    font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 16)
    for start in range(0,len(chosen),16):
        sheet = Image.new('RGB', (1440,1640), 'white')
        draw = ImageDraw.Draw(sheet)
        for j,r in enumerate(chosen[start:start+16]):
            x,y = j%4*360,j//4*410
            im=Image.open(DATA/'whatif'/r['image'].lstrip('./')).convert('RGB')
            im.thumbnail((350,280)); sheet.paste(im,(x,y))
            label=f"[{start+j}] {r['source_group']}\n{r['question']}\nVIS={r['context_answer']} | PRI={r['prior_answer']}"
            draw.text((x+2,y+282),'\n'.join(s for para in label.split('\n') for s in textwrap.wrap(para,40)),font=font,fill='black')
        sheet.save(DATA/'sheets'/f'whatif-{start//16:02}.jpg')
    print('rows',len(rows),'groups',len(groups),'representatives',len(chosen))
    print(collections.Counter(r['source_group'].split(':')[0] for r in chosen))

if __name__ == '__main__':
    main()
