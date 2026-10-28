"""Read existing experiment evidence without loading models or extracting archives."""
from collections import OrderedDict
from functools import lru_cache
import json
from pathlib import Path
import re
import tarfile
from urllib.parse import unquote, urlsplit

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
CATALOG = HERE / 'all-experiments-r01/catalog.json'


def read(path):
    return json.loads(Path(path).read_text())


def load_catalog():
    data = read(CATALOG)
    return dict(data, datasets=[{k: v for k, v in d.items() if k != 'reader'}
                                for d in data['datasets']])


def _safe(path):
    p = Path(path)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError('Only repository-relative evidence paths are allowed')
    p = (REPO / p).resolve()
    if not p.is_relative_to(REPO) or not p.is_file():
        raise ValueError('Evidence file is missing or outside the repository')
    return p


def _paths(patterns):
    return sorted({p for pattern in patterns for p in REPO.glob(pattern) if p.is_file()})


@lru_cache(maxsize=1)
def _allowed():
    data = read(CATALOG)
    names = {str(CATALOG.relative_to(REPO)), str((CATALOG.parent / 'receipt.json').relative_to(REPO))}
    for d in data['datasets']:
        names.update(v['path'] for v in d['views'])
        r = d.get('reader', {})
        names.update(str(p.relative_to(REPO)) for p in _paths(r.get('patterns', [])))
        names.update(r[k] for k in ('archive', 'items', 'scores') if r.get(k))
    for manifest in data.get('manifests', []):
        names.add(manifest)
        for field in ('sources', 'outputs'):
            names.update(x['path'] for x in read(_safe(manifest)).get(field, []) if 'path' in x)
    # Follow only explicit local links/fetches, never expose an entire directory.
    queue = list(names)
    allowed = set()
    while queue:
        name = queue.pop()
        if name in allowed or any(s in name.lower() for s in ('private', 'rating_keys', 'blind-reviewer')):
            continue
        try:
            p = _safe(name)
        except ValueError:
            continue
        allowed.add(name)
        if p.suffix not in ('.html', '.md'):
            continue
        text = p.read_text()
        refs = re.findall(r'(?:href|src)=[\"\']([^\"\']+)|fetch\([\"\']([^\"\']+)|\]\(([^)]+)\)', text)
        for match in refs:
            link = next(x for x in match if x)
            u = urlsplit(link)
            if u.scheme or u.netloc or not u.path or '${' in u.path:
                continue
            q = (REPO / u.path.lstrip('/')) if u.path.startswith('/') else p.parent / unquote(u.path)
            q = q.resolve()
            if q.is_relative_to(REPO) and q.is_file():
                queue.append(str(q.relative_to(REPO)))
    return frozenset(allowed)


def allowed_file(path):
    name = unquote(str(path)).lstrip('/')
    if name not in _allowed():
        raise ValueError('File is not in the explicit evidence allowlist')
    return _safe(name)


def _records(patterns):
    for p in _paths(patterns):
        if p.suffix == '.jsonl':
            with p.open() as f:
                for line in f:
                    if line.strip():
                        yield json.loads(line), str(p.relative_to(REPO))
        else:
            data = read(p)
            for row in data if isinstance(data, list) else [data]:
                yield row, str(p.relative_to(REPO))


def _archived(path, partial=False):
    with tarfile.open(_safe(path), mode='r|gz') as archive:
        for member in archive:
            if member.isfile() and member.name.startswith('outputs/') and (
                    member.name.endswith('.jsonl') or (partial and member.name.endswith('.partial.json'))):
                stream = archive.extractfile(member)
                if member.name.endswith('.jsonl'):
                    for line in stream:
                        if line.strip():
                            yield json.loads(line), path + '::' + member.name
                else:
                    data = json.load(stream)
                    for row in data if isinstance(data, list) else [data]:
                        yield dict(row, status='partial_user_stopped'), path + '::' + member.name


def _prompt(row):
    if isinstance(row.get('prompt'), str):
        return row['prompt']
    item = row.get('item', row.get('question', row))
    if not isinstance(item, dict):
        return str(item)
    doc = item.get('doc', {})
    prompt = item.get('prompt') or doc.get('question') or item.get('question') or item.get('context', '')
    choices = doc.get('choices', item.get('options'))
    if isinstance(choices, dict):
        choices = choices.get('text', choices)
    if isinstance(choices, list):
        prompt += '\n' + '\n'.join(f'{chr(65+i)}. {s}' for i, s in enumerate(choices))
    return prompt


def _condition(name, output, score=None):
    c = {'name': name}
    if 'answer_text' in output or 'raw_text' in output:
        c['text'] = output.get('answer_text', output.get('raw_text', ''))
    for target, source in [('scores', 'choice_loglikelihoods'), ('scores', 'scores'),
                           ('correct', 'correct'), ('margin', 'margin'), ('prediction', 'prediction'),
                           ('end_reason', 'end_reason'), ('tokens', 'generated_token_count')]:
        if source in output:
            c[target] = output[source]
    if score:
        c.update({k: score[k] for k in ('correct', 'prediction', 'metric', 'parse_failed') if k in score})
    if not any(k in c for k in ('text', 'scores', 'correct', 'margin')):
        c['note'] = '没有完整输出；不补造回答或分数'
    return c


def _row(record, source, scores=None):
    key = record.get('id', record.get('condition_id', '?'))
    archive, _, member = source.partition('::')
    item = {'id': key, 'prompt': _prompt(record), 'conditions': [], 'raw': [archive],
            'provenance': {'status': record.get('status', 'recorded'), 'benchmark': record.get('benchmark')}}
    if member:
        item['provenance']['archive_member'] = member
    outputs = record.get('outputs', record.get('conditions', {}))
    item['conditions'] = [_condition(name, o, (scores or {}).get(key, {}).get('outputs', {}).get(name))
                          for name, o in outputs.items()]
    return item


@lru_cache(maxsize=4)
def _rows(dataset):
    d = next((x for x in read(CATALOG)['datasets'] if x['id'] == dataset), None)
    if d is None:
        raise ValueError('Unknown evidence dataset')
    r = d.get('reader', {})
    kind = r.get('kind')
    if not kind:
        return []
    records = _archived(r['archive'], r.get('partial', False)) if 'archive' in r else _records(r['patterns'])
    scores = {x['id']: x for x, _ in _records([r['scores']])} if r.get('scores') else {}
    questions = {x['id']: x for x, _ in _records([r['items']])} if r.get('items') else {}
    rows, grouped = [], OrderedDict()
    for rec, source in records:
        if kind == 'initial':
            q = rec['question']
            key = f"{q['id']}:{rec['attempt']['max_new_tokens']}"
            item = grouped.setdefault(key, {'id': key, 'prompt': q['prompt'], 'conditions': [], 'raw': [],
                'provenance': {'question_id': q['id'], 'attempt': rec['attempt'], 'targets': q['targets'],
                               'note': '旧停止规则；512/1024尝试不是独立重复'}})
            item['conditions'].append(_condition(rec['arm'], rec['response']))
            item['raw'].append(source)
        elif kind == 'grouped':
            q = rec.get('item', rec.get('question'))
            key = str(rec.get('model', '')) + ':' + q['id']
            item = grouped.setdefault(key, {'id': key, 'prompt': _prompt(rec), 'conditions': [], 'raw': [],
                'provenance': {'model': rec.get('model', d['model']), 'question_id': q['id'], 'status': rec.get('status')}})
            item['conditions'].append(_condition(rec['condition'], rec['output']))
            if source not in item['raw']:
                item['raw'].append(source)
        elif kind == 'survey_partial':
            item = {'id': rec['condition_id'] + ':' + rec['question_id'], 'prompt': rec['prompt'],
                    'conditions': [_condition(rec['condition_id'], rec['output'])], 'raw': [source],
                    'provenance': {k: rec.get(k) for k in ('model_id', 'layer', 'channel', 'dose', 'status')}}
            rows.append(item)
        elif kind in ('root', 'ranking'):
            rec['item'] = questions[rec['id']]
            item = _row(rec, source)
            if kind == 'ranking':
                item['conditions'] = [{'name': x['component'] + ':' + x['positions'],
                    'scores': [x['predicted_repair']], 'score_kind': 'predicted_repair',
                    'note': '排序预测，不是实测修复'} for x in rec['ranking']]
            else:
                parent = (REPO / source).parent
                if (parent / 'candidate.json').is_file():
                    candidate = read(parent / 'candidate.json')
                    item['id'] = candidate['id'] + ':' + item['id']
                    item['provenance']['candidate'] = candidate
            rows.append(item)
        else:
            rows.append(_row(rec, source, scores))
    return list(grouped.values()) if grouped else rows


def history_rows(dataset, page=0, limit=20):
    page, limit = int(page), int(limit)
    if page < 0 or not 1 <= limit <= 100:
        raise ValueError('page must be nonnegative; limit must be 1..100')
    rows = _rows(dataset)
    return {'dataset': dataset, 'total': len(rows), 'page': page, 'limit': limit,
            'items': rows[page * limit:(page + 1) * limit]}
