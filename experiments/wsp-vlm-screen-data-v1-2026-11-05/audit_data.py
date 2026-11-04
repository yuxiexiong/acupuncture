"""CPU-only pairing, exact grouping and review sheets; never imports a model."""
import argparse
import hashlib
import io
import json
import textwrap
from collections import defaultdict
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
from PIL import Image, ImageDraw, ImageFont
from scipy.fft import dctn


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source(row):
    m = row["metadata"]
    return f"{m['source_dataset']}:{int(m['source_img_id'])}"


def load_image(value):
    return Image.open(io.BytesIO(value["bytes"])).convert("RGB")


def image_record(value, path):
    image = load_image(value)
    image.save(path)
    gray = np.asarray(image.convert("L").resize((32, 32)), dtype=float)
    low = dctn(gray, norm="ortho")[:8, :8].flatten()
    bits = low > np.median(low[1:])
    phash = sum(int(b) << i for i, b in enumerate(bits))
    return dict(bytes_sha256=digest(value["bytes"]),
                pixel_sha256=digest(str(image.size).encode() + image.tobytes()),
                size=list(image.size), phash=f"{phash:016x}")


def sheet(items, output, columns=2):
    # Fixed-size contact sheets are review aids; originals remain available for zoom.
    font = ImageFont.load_default(size=14)
    w, h = 760, 560
    canvas = Image.new("RGB", (columns*w, ((len(items)+columns-1)//columns)*h), "white")
    draw = ImageDraw.Draw(canvas)
    for i, (paths, label) in enumerate(items):
        x, y = (i % columns)*w, (i//columns)*h
        for j, path in enumerate(paths):
            im = Image.open(path).convert("RGB")
            im.thumbnail((w//len(paths)-8, 340))
            canvas.paste(im, (x+j*w//len(paths), y))
        lines = []
        for line in label.splitlines():
            lines.extend(textwrap.wrap(line, 86) or [""])
        draw.multiline_text((x+5, y+345), "\n".join(lines), font=font, fill="black", spacing=2)
    canvas.save(output)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("root", type=Path)
    p.add_argument("out", type=Path)
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    images = args.root / "review_images"
    images.mkdir(exist_ok=True)
    sheets = args.root / "review_sheets"
    sheets.mkdir(exist_ok=True)
    for f in json.loads((args.root / "download_manifest.json").read_text()):
        assert digest((args.root / f['candidate'] / f['path']).read_bytes()) == f['sha256']
    b = defaultdict(dict)
    counts = {}
    for stratum in ("position", "distance"):
        name = stratum + "_and_counting"
        total = pq.read_table(args.root / "B/single_skill" / f"counting_only-paired-{name}.parquet").to_pylist()
        restricted = pq.read_table(args.root / "B/combine_2_skill" / f"{name}.parquet").to_pylist()
        lookup = {source(r): r for r in total}
        assert len(lookup) == len(total)
        counts[stratum] = dict(total_rows=len(total), restricted_rows=len(restricted), sources=len(lookup))
        for r in restricted:
            key = source(r)
            t = lookup[key]
            assert int(r["question_id"]) == int(t["question_id"])
            assert t["image"]["bytes"] == r["image"]["bytes"]
            assert isinstance(t['answer'], int) and isinstance(r['answer'], int)
            if stratum not in b[key]:
                b[key][stratum] = dict(total_question=t['question'], total_answer=t['answer'],
                                       total_id=t['question_id'], restricted=[])
            b[key][stratum]['restricted'].append({k: v for k, v in r.items() if k != 'image'})
            if "image" not in b[key]:
                path = images / ("B_" + key.split(':')[-1] + ".png")
                b[key]["image"] = image_record(r['image'], path)
                b[key]['image']['local_path'] = str(path)
    records_b = [dict(source_id=k, **v) for k, v in sorted(b.items(), key=lambda x: int(x[0].split(':')[-1]))]
    (args.out / "B_source_groups.json").write_text(json.dumps(records_b, indent=2))
    b_items = []
    for r in records_b:
        label = [r['source_id']]
        for s in ('position', 'distance'):
            if s not in r: continue
            v = r[s]
            label.append(f"{s} ALL={v['total_answer']}: {v['total_question']}")
            for question in v['restricted']:
                label.append(f"{question['question_id']} [{question['answer']}] {question['question']}")
        b_items.append(([r['image']['local_path']], '\n'.join(label)))
    for i in range(0, len(b_items), 4):
        sheet(b_items[i:i+4], sheets / f"B_{i//4:02d}.png")
    c = pq.read_table(args.root / "C/data/size-00000-of-00001.parquet").to_pylist()
    records_c = []
    parent = list(range(len(c)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def union(i,j):
        parent[find(max(i,j))] = find(min(i,j))
    seen_pairs, seen_pixels = {}, {}
    phashes = []
    for i, r in enumerate(c):
        pair = tuple(sorted([r['correct_answer'].strip().lower(), r['incorrect_answer'].strip().lower()]))
        assert len(set(pair)) == 2
        if pair in seen_pairs: union(i, seen_pairs[pair])
        seen_pairs[pair] = i
        rec = dict(row_id=i, object=r['object'], correct_answer=r['correct_answer'],
                   incorrect_answer=r['incorrect_answer'], unordered_pair=pair)
        for field in ('original_image', 'counterfact_image'):
            path = images / f"C_{i:03d}_{field}.png"
            rec[field] = image_record(r[field], path)
            rec[field]['local_path'] = str(path)
            key = rec[field]['pixel_sha256']
            if key in seen_pixels: union(i, seen_pixels[key])
            seen_pixels[key] = i
            phashes.append((i, field, int(rec[field]['phash'],16)))
        records_c.append(rec)
    groups = defaultdict(list)
    for i in range(len(c)): groups[find(i)].append(i)
    ordered = sorted(groups.values(), key=lambda g: digest(f"20261105:C:{min(g)}".encode()))
    for rec in records_c: rec['exact_group_id'] = find(rec['row_id'])
    near = []
    for k, (i, field, ph) in enumerate(phashes):
        for j, field2, ph2 in phashes[:k]:
            if find(i) == find(j): continue
            distance = bin(ph ^ ph2).count('1')
            if distance <= 4:
                near.append(dict(row_a=j, field_a=field2, row_b=i, field_b=field, phash_distance=distance))
    (args.out / "C_rows.json").write_text(json.dumps(records_c, indent=2))
    (args.out / "C_group_order.json").write_text(json.dumps(ordered, indent=2))
    (args.out / "C_near_candidates.json").write_text(json.dumps(near, indent=2))
    quarantine = {r[k] for r in near for k in ('row_a', 'row_b')}
    pool = [g for g in ordered if not quarantine.intersection(g)]
    (args.out / "C_review_pool.json").write_text(json.dumps(pool, indent=2))
    b_near = []
    for i, r in enumerate(records_b):
        for s in records_b[:i]:
            distance = bin(int(r['image']['phash'], 16) ^ int(s['image']['phash'], 16)).count('1')
            if distance <= 4:
                b_near.append(dict(source_a=s['source_id'], source_b=r['source_id'], phash_distance=distance))
    (args.out / "B_near_candidates.json").write_text(json.dumps(b_near, indent=2))
    c_items = []
    for rank, group in enumerate(ordered[:220]):
        r = records_c[min(group)]
        label = f"rank={rank} row={r['row_id']} group={group}\nLEFT original / RIGHT counterfact\nUPSTREAM usual larger: {r['correct_answer']}\nUPSTREAM other: {r['incorrect_answer']}"
        c_items.append(([r[f]['local_path'] for f in ('original_image','counterfact_image')], label))
    for i in range(0, len(c_items), 6):
        sheet(c_items[i:i+6], sheets / f"C_{i//6:02d}.png")
    summary = dict(B=counts, B_source_union=len(b), B_source_intersection=sum('position' in r and 'distance' in r for r in b.values()),
                   B_exact_pixel_groups=len({r['image']['pixel_sha256'] for r in b.values()}),
                   C_rows=len(c), C_unordered_pairs=len(seen_pairs), C_exact_union_groups=len(groups),
                   C_near_candidate_image_pairs=len(near), model_loads=0, model_calls=0)
    (args.out / 'structural_counts.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    main()
