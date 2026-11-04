"""Build C inputs/gold separately and validate assets, without loading any model."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
B1 = ("Follow the scope of the question. For size in the image, use visible size even if unusual. "
      "For typical real-world size, use general knowledge even if the image differs. "
      "Return only the object's name.")
TEMPLATES = {
    "usual": ["In the real world, which is typically larger, {x} or {y}?",
              "Which normally has a greater real-world size, {x} or {y}?"],
    "visual": ["Which object appears larger in this image, {x} or {y}?",
               "Looking only at the pictured sizes, which is bigger, {x} or {y}?"],
}
CONDITIONS = [
    ("no_image_usual", None, "usual"),
    ("original_usual", "original_image", "usual"),
    ("counterfact_usual", "counterfact_image", "usual"),
    ("original_visual", "original_image", "visual"),
    ("counterfact_visual", "counterfact_image", "visual"),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(name):
    return json.loads((HERE / "audit" / name).read_text())


def selected_groups():
    rows = load("C_rows.json")
    pool = load("C_review_pool.json")
    reviews = load("C_visual_review.json")
    assert len({r['row_id'] for r in reviews}) == len(reviews)
    passed = sorted((r for r in reviews if r['status'] == 'pass_ai_visual'), key=lambda r: r['rank'])
    assert len(passed) >= 160, "Insufficient visually audited groups"
    selected, used_pairs, used_pixels = [], set(), set()
    for i, review in enumerate(passed[:160]):
        assert review['group'] == pool[review['rank']]
        r = rows[review['row_id']]
        assert r['row_id'] == min(review['group'])
        pair = tuple(r['unordered_pair'])
        assert pair not in used_pairs
        used_pairs.add(pair)
        for field in ('original_image', 'counterfact_image'):
            key = r[field]['pixel_sha256']
            assert key not in used_pixels
            used_pixels.add(key)
        group_id = f"C-{r['exact_group_id']:03d}"
        selected.append(dict(**r, group_id=group_id, source_rows=review['group'],
                             review_rank=review['rank'], split='D' if i < 64 else 'H',
                             primary_order=int(sha(f'20261105:{group_id}'.encode())[:8], 16) % 2))
    return selected


def requests(groups):
    for g in groups:
        names = [g['correct_answer'], g['incorrect_answer']]
        for condition, field, scope in CONDITIONS:
            answer = names[1] if condition == 'counterfact_visual' else names[0]
            for t in range(2):
                for order in range(2):
                    x, y = names if order == 0 else names[::-1]
                    question = TEMPLATES[scope][t].format(x=x, y=y) + " Return only the object's name."
                    for arm in ('B0', 'B1'):
                        rid = f"{g['group_id']}:{condition}:T{t}:O{order}:{arm}"
                        # Gold, condition names and usual/visual labels are evaluator metadata,
                        # never additional text sent to the model.
                        inp = dict(request_id=rid, text=(B1 + '\n' if arm == 'B1' else '') + question,
                                   image=g[field]['local_path'] if field else None)
                        gold = dict(request_id=rid, group_id=g['group_id'], split=g['split'],
                                    condition=condition, template=f'T{t}', order=order, arm=arm,
                                    answer=answer, names=names,
                                    primary=(arm == 'B0' and t == 0 and order == g['primary_order']))
                        yield inp, gold


def normalize(text):
    return ' '.join(text.strip().strip('.').strip().casefold().split())


def parse_answer(text, names):
    """Only a complete canonical name matches; no substring or hindsight aliases."""
    matched = [n for n in names if normalize(text) == normalize(n)]
    return matched[0] if len(matched) == 1 else None


def validate_predictions(predictions, gold):
    expected = {g['request_id']: g for g in gold}
    assert len(expected) == len(gold)
    seen, scored = set(), []
    for p in predictions:
        rid = p['request_id']
        if rid not in expected or rid in seen:
            raise ValueError('Unknown or duplicate request_id: ' + rid)
        seen.add(rid)
        g = expected[rid]
        parsed = parse_answer(p['text'], g['names'])
        scored.append(dict(request_id=rid, parsed=parsed, format_valid=parsed is not None,
                           correct=parsed == g['answer'] and not p.get('truncated', False)))
    if seen != set(expected):
        raise ValueError(f'Missing {len(set(expected)-seen)} predictions')
    return scored


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--repo-root', type=Path, default=HERE.parents[1])
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    groups = selected_groups()
    for g in groups:
        for field in ('original_image', 'counterfact_image'):
            r = g[field]
            with Image.open(args.repo_root / r['local_path']) as im:
                im = im.convert('RGB')
                assert sha(str(im.size).encode() + im.tobytes()) == r['pixel_sha256']
    args.out.mkdir(parents=True, exist_ok=True)
    pairs = list(requests(groups))
    assert len(pairs) == 6400 and len({x['request_id'] for x, _ in pairs}) == 6400
    hashes = {}
    for name, records in [('selected_groups.jsonl', groups), ('inputs.jsonl', [x for x, _ in pairs]),
                          ('gold.jsonl', [g for _, g in pairs])]:
        data = ''.join(json.dumps(x, ensure_ascii=False, sort_keys=True) + '\n' for x in records).encode()
        (args.out / name).write_bytes(data)
        hashes[name] = dict(sha256=sha(data), bytes=len(data), records=len(records))
    shared = {n for g in groups if g['split']=='D' for n in g['unordered_pair']} & {
        n for g in groups if g['split']=='H' for n in g['unordered_pair']}
    receipt = dict(status='CPU data preparation only; no inference',
                   selected_groups=len(groups), split_counts=dict(Counter(g['split'] for g in groups)),
                   request_counts=dict(Counter(g['split'] for _,g in pairs)), files=hashes,
                   shared_object_names_D_H=sorted(shared),
                   H_groups_with_shared_name=sum(g['split']=='H' and bool(set(g['unordered_pair']) & shared) for g in groups),
                   model_loads=0, model_calls=0)
    (args.out / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
