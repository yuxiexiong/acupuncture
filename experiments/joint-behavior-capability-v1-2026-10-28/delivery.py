"""Export verified evidence for anonymous reading; never assign semantic labels."""
import argparse
from collections import Counter, defaultdict
import hashlib
import html
import json
from pathlib import Path
import random

SEED = 20261028


def digest_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_text(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def anonymize(sources, items, seed=SEED):
    """Stable shuffle and opaque sequential IDs; the key stays out of blind files."""
    ordered = sorted(sources, key=lambda x: (x['record']['item_id'], x['record']['condition']['id']))
    random.Random(seed).shuffle(ordered)
    blind, key = [], []
    identities = set()
    for index, source in enumerate(ordered):
        row = source['record']
        identity = (row['item_id'], row['condition']['id'])
        if identity in identities:
            raise ValueError('Duplicate item/condition evidence')
        identities.add(identity)
        anonymous_id = hashlib.sha256(f'joint-blind-v1:{seed}:{index:06d}'.encode()).hexdigest()[:20]
        answer = row['output']
        blind.append({'id': anonymous_id, 'prompt': items[row['item_id']]['prompt'],
                      'answer_text': answer['answer_text'], 'raw_text': answer['raw_text']})
        key.append({'id': anonymous_id, 'item_id': row['item_id'], 'condition': row['condition'],
                    'source_path': source['source_path'], 'source_sha256': source['source_sha256']})
    return blind, key


def render(blind):
    parts = ['<!doctype html><html lang="zh-CN"><meta charset="utf-8">',
             '<title>联合测量：匿名原文阅读</title>',
             '<style>body{max-width:1100px;margin:32px auto;padding:0 20px;font:16px/1.6 system-ui}'
             'article{border-top:1px solid #ccc;padding:20px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;'
             'background:#f6f6f6;padding:14px;font:inherit}small{color:#666}</style>',
             '<h1>联合测量：匿名原文阅读</h1><p>先记录原文观察，再揭盲。空答和异常文本均保留；本页没有自动语义判定。</p>']
    for row in blind:
        parts.append('<article><small>匿名编号：' + html.escape(row['id']) + '</small>')
        for title, field in [('题目', 'prompt'), ('正文（未裁剪）', 'answer_text'), ('原始文本（含特殊标记）', 'raw_text')]:
            # A span prevents HTML's special removal of a pre element's first newline.
            parts.append('<h2>' + title + '</h2><pre><span>' + html.escape(row[field]) + '</span></pre>')
            if row[field] == '':
                parts.append('<small>上方字段为空字符串。</small>')
        parts.append('</article>')
    parts.append('</html>')
    return '\n'.join(parts)


def reading_template(blind):
    return [{'id': row['id'], 'status': 'unread', 'content': None, 'delivery': None,
             'style': None, 'evidence': None, 'uncertainty': None, 'reader': None}
            for row in blind]


def quantitative(sources, items):
    """Only mechanical stopping/length and frozen candidate probability readouts."""
    records, groups = [], defaultdict(list)
    for source in sources:
        row = source['record']
        item = items[row['item_id']]
        output = row['output']
        entry = {'item_id': item['id'], 'base_id': item['base_id'], 'panel': item['panel'],
                 'family': item['family'], 'demand': item['demand'], 'fact_version': item['fact_version'],
                 'condition': row['condition']['id'], 'generated_token_count': output['generated_token_count'],
                 'end_reason': output['end_reason'], 'candidate_readout': None}
        if item['choices']:
            values = [x['loglikelihood'] for x in row['choice_details']]
            if len(values) != 2:
                raise ValueError('Expected two frozen candidate scores')
            target = item['target_index']
            prediction = max(range(2), key=values.__getitem__)
            entry['candidate_readout'] = {'choices': item['choices'], 'sum_loglikelihood': values,
                'target_index': target, 'prediction_index': prediction, 'tied': values[0] == values[1],
                'correct': prediction == target, 'target_margin': values[target] - values[1-target]}
        records.append(entry)
        groups[(item['panel'], item['family'], item['demand'], entry['condition'])].append(entry)
    summaries = []
    for (panel, family, demand, condition), rows in sorted(groups.items(), key=lambda x: repr(x[0])):
        scored = [r['candidate_readout'] for r in rows if r['candidate_readout'] is not None]
        summaries.append({'panel': panel, 'family': family, 'demand': demand, 'condition': condition,
            'records': len(rows), 'end_reasons': dict(Counter(r['end_reason'] for r in rows)),
            'generated_tokens': sum(r['generated_token_count'] for r in rows),
            'candidate_readout_count': len(scored),
            'candidate_correct_count': sum(r['correct'] for r in scored),
            'candidate_margin_mean': sum(r['target_margin'] for r in scored) / len(scored) if scored else None})
    return {'interpretation': 'Mechanical outputs and candidate-phrasing likelihood diagnostics only; not a final capability or semantic judgment.',
            'semantic_assessment_complete': False, 'groups': summaries, 'records': records}


def export(run, stage, output, stage1_run=None):
    import experiment
    if stage not in ('stage1', 'stage2'):
        raise ValueError('Unknown stage')
    if (stage == 'stage2') != (stage1_run is not None):
        raise ValueError('Stage2 requires the verified stage1 source; stage1 accepts no extra source')
    runs = [(Path(run).resolve(), stage)]
    if stage == 'stage2':
        runs.insert(0, (Path(stage1_run).resolve(), 'stage1'))
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError('Delivery must use a new directory')
    items = {r['id']: r for r in experiment.inputs()}
    sources, verification, freezes = [], [], set()
    for root, phase in runs:
        verification.append({'run': str(root), **experiment.verify_stage(root, phase)})
        stage_count = 0
        for worker in (0, 1):
            worker_root = root / f'worker-{worker}'
            receipt = experiment.read(worker_root / 'receipt.json')
            freezes.add(receipt['freeze_sha256'])
            for path in sorted((worker_root / 'records').glob('*.json')):
                relative = str(path.relative_to(worker_root))
                source_sha = digest_file(path)
                if receipt['record_hashes'].get(relative) != source_sha:
                    raise ValueError('Record changed after verification')
                sources.append({'record': experiment.read(path), 'source_path': str(path), 'source_sha256': source_sha})
                stage_count += 1
        if stage_count != {'stage1':1560, 'stage2':2160}[phase]:
            raise ValueError('Incomplete stage source count')
    if len(freezes) != 1:
        raise ValueError('Stages do not share one frozen implementation')
    condition_ids = {c['id'] for c in experiment.conditions('stage1')}
    if stage == 'stage2':
        condition_ids.update(c['id'] for c in experiment.conditions('stage2'))
    expected = {(item_id, condition_id) for item_id in items for condition_id in condition_ids}
    actual = {(r['record']['item_id'], r['record']['condition']['id']) for r in sources}
    if actual != expected or len(sources) != len(actual):
        raise ValueError('Missing, duplicate or extra item/condition sources')
    blind, key = anonymize(sources, items)
    metrics = quantitative(sources, items)
    output.mkdir(parents=True, exist_ok=False)
    def save_json(name, value):
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    def save_jsonl(name, rows):
        (output / name).write_text(''.join(json_text(r)+'\n' for r in rows))
    save_jsonl('blind.jsonl', blind)
    (output / 'blind.html').write_text(render(blind))
    save_json('private-key.json', {'warning': 'Keep separate until reading observations are locked.', 'mapping': key})
    save_jsonl('reading-template.jsonl', reading_template(blind))
    save_json('quantitative.json', metrics)
    manifest = {'stage': stage, 'whole_stage_complete': True, 'full_experiment_complete': stage == 'stage2',
                'reading_complete': False, 'freeze_sha256': next(iter(freezes)), 'shuffle_seed': SEED,
                'generation_records': len(sources), 'condition_count': len(condition_ids),
                'candidate_readouts': sum(bool(items[r['record']['item_id']]['choices']) for r in sources),
                'source_verification': verification,
                'files': {p.name:digest_file(p) for p in sorted(output.iterdir()) if p.is_file()}}
    save_json('manifest.json', manifest)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--stage', choices=('stage1','stage2'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--stage1-run', type=Path)
    print(json.dumps(export(**vars(parser.parse_args())), ensure_ascii=False, indent=2))
