"""D-only image/evidence export and frozen B/C scoring reuse. No model imports."""
import argparse
import json
import shutil
from pathlib import Path
from common import HERE, EXPERIMENTS, digest, packed, file_hash, inside, write_json, legacy


def scorers():
    # These are import-safe; dependencies are checked as well as their entry points.
    reuse = json.loads((HERE / 'reuse.json').read_text())
    for name, expected in reuse['scoring_dependencies'].items():
        if file_hash(EXPERIMENTS / name) != expected:
            raise ValueError('Frozen scoring dependency changed: ' + name)
    b = legacy('wsp-vlm-screen-ready-v3-2026-11-05/statistics_b.py', 'repair_b_scoring')
    c = legacy('wsp-vlm-screen-prep-v2-2026-11-05/statistics_c.py', 'repair_c_scoring')
    return {'B': b, 'C': c}


def export_development(task, destination, preview_manifest, preview_root, predictions=None):
    """Copies only D sources. Seen-H development needs a separately reviewed new exporter."""
    prep = legacy('wsp-vlm-screen-ready-v3-2026-11-05/prepare_inputs.py', 'repair_inputs')
    pairs = [(i, g) for i, g in prep.all_pairs(task) if g['split'] == 'D']
    previews = {r['source']: r for r in json.loads(Path(preview_manifest).read_text())['images']}
    out = Path(destination)
    out.mkdir(parents=True, exist_ok=False)
    (out / 'images').mkdir()
    records, files = [], {}

    def copy(path, expected=None):
        path = Path(path)
        h = file_hash(path)
        if expected and h != expected:
            raise ValueError('Image/preview hash mismatch')
        rel = 'images/' + h + path.suffix.lower()
        if rel not in files:
            shutil.copyfile(path, out / rel)
            files[rel] = h
        return rel

    for inp, gold in pairs:
        r = dict(inp)
        preview = None
        if r['image'] is not None:
            original = r['image']
            p = previews[original]
            r['image'] = copy(prep.ROOT / original, p['source_png_sha256'])
            preview = copy(inside(Path(preview_root), p['preview']), p['preview_sha256'])
        records.append(dict(input=r, gold=gold, preview=preview))
    previous = [] if predictions is None else [json.loads(x) for x in Path(predictions).read_text().splitlines()]
    if predictions is not None:
        scorers()[task].score(previous, [g for _, g in pairs])
    package = dict(task=task, role='development', split='D', records=records, files=files,
                   previous_predictions=previous, previous_role='diagnostic_only_not_cached_baseline',
                   sources=dict(preview_manifest_sha256=file_hash(preview_manifest),
                                predictions_sha256=file_hash(predictions) if predictions else None))
    write_json(out / 'bundle.json', package)
    return dict(bundle_sha256=file_hash(out / 'bundle.json'), groups=len({g['group_id'] for _, g in pairs}),
                requests=len(pairs), model_loads=0, model_calls=0)


class Evidence:
    def __init__(self, root, expected_hash, role='development', split='D'):
        self.root = Path(root).resolve()
        if file_hash(self.root / 'bundle.json') != expected_hash:
            raise ValueError('Evidence bundle identity mismatch')
        self.package = json.loads((self.root / 'bundle.json').read_text())
        p = self.package
        if p['role'] != role or p['split'] != split:
            raise PermissionError('Evidence role/split mismatch')
        self.task, self.identity = p['task'], expected_hash
        self.records = {r['input']['request_id']: r for r in p['records']}
        if not self.records or len(self.records) != len(p['records']):
            raise ValueError('Empty or duplicate development requests')
        for rid, r in self.records.items():
            if set(r['input']) != {'request_id', 'text', 'image'} or r['gold']['request_id'] != rid or r['gold']['split'] != split:
                raise ValueError('Input/gold identity or split mismatch')
            for rel in (r['input']['image'], r['preview']):
                if rel and (rel not in p['files'] or file_hash(inside(self.root, rel)) != p['files'][rel]):
                    raise ValueError('Missing or modified development image')

    def select(self, ids=None):
        ids = list(self.records) if ids is None else ids
        if not ids or len(ids) != len(set(ids)) or any(i not in self.records for i in ids):
            raise PermissionError('Unknown, duplicate, empty or sealed request IDs')
        return [self.records[i] for i in ids]

    def view(self, ids=None):
        rows = self.select(ids)
        previous = {r['request_id']: r for r in self.package['previous_predictions']}
        return [dict(r, previous_prediction=previous.get(r['input']['request_id'])) for r in rows]

    def image(self, request_id, kind):
        r = self.select([request_id])[0]
        rel = r['preview'] if kind == 'preview' else r['input']['image'] if kind == 'input' else None
        if rel is None:
            raise ValueError('No image of requested kind')
        path = inside(self.root, rel)
        if file_hash(path) != self.package['files'][rel]:
            raise ValueError('Image changed after bundle validation')
        return path

    def score(self, predictions, ids):
        return scorers()[self.task].score(predictions, [r['gold'] for r in self.select(ids)])


def summarize(rows):
    """Descriptive candidate feedback; never repurposes screen significance tests."""
    cells, groups = {}, {}
    for r in rows:
        key = ':'.join(str(r.get(k, '-')) for k in ('arm', 'template', 'order', 'condition'))
        cells.setdefault(key, []).append(r)
        if r['primary']:
            groups.setdefault(r['group_id'], []).append(r)
    return dict(n=len(rows), accuracy=sum(r['correct'] for r in rows) / len(rows),
                format_errors=sum(not r['format_valid'] for r in rows),
                truncated=sum(r['truncated'] for r in rows),
                primary_joint=sum(all(r['correct'] for r in rs) for rs in groups.values()) / len(groups) if groups else None,
                primary_groups=len(groups),
                cells={k: dict(n=len(rs), correct=sum(r['correct'] for r in rs)) for k, rs in cells.items()})


def repair_score(rows):
    """Equal source groups, then equal wording/order panels; ordinary prompts only.

    Partial diagnostic sets have no selection score. C's target is the conflicting
    image usual/visual pair; all five conditions remain per-panel protections.
    """
    conditions = {r['condition'] for r in rows}
    target = {'total', 'subset'} if 'subset' in conditions else {'counterfact_usual', 'counterfact_visual'}
    panels = {}
    for r in rows:
        if r['arm'] == 'B0' and r['condition'] in target:
            key = (r['group_id'], r['template'], r.get('order', '-'))
            panel = panels.setdefault(key, {})
            if r['condition'] in panel:
                raise ValueError('Duplicate joint condition')
            panel[r['condition']] = r['correct']
    if not panels or any(set(p) != target for p in panels.values()):
        return None
    groups = {}
    for (group, template, order), p in panels.items():
        groups.setdefault(group, []).append(all(p.values()))
    return sum(sum(v)/len(v) for v in groups.values())/len(groups)


def compare(before, after):
    a, b = ({r['request_id']: r for r in rows} for rows in (before, after))
    if set(a) != set(b):
        raise ValueError('Cannot compare different request sets')
    return dict(repaired=[i for i in a if not a[i]['correct'] and b[i]['correct']],
                worsened=[i for i in a if a[i]['correct'] and not b[i]['correct']],
                before=summarize(before), after=summarize(after))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--task', choices=['B', 'C'], required=True)
    for k in ('out', 'preview-manifest', 'preview-root'):
        ap.add_argument('--' + k, type=Path, required=True)
    ap.add_argument('--predictions', type=Path)
    a = ap.parse_args()
    print(json.dumps(export_development(a.task, a.out, a.preview_manifest, a.preview_root, a.predictions)))
