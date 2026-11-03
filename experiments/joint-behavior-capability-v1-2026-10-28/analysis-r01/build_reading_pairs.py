"""Join locked observations by source SHA; never classify response semantics."""
from collections import defaultdict
from pathlib import Path
import json
import sys

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import experiment as e


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def cell(value):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return text.replace('|', '\\|').replace('\n', '<br>')


def main():
    identity = e.check()
    observations = {}
    source_names = ['freeze.json', 'data/items.json', 'delivery-stage1-r01/private-key.json',
                    'delivery-stage1-r01/manifest.json', 'delivery-full-r01/private-key.json',
                    'delivery-full-r01/manifest.json', 'delivery-full-r01/quantitative.json',
                    'readiness/full-local-verification-r01.json',
                    'reading-r01/locked-source-coverage-final-stage1-r01.json',
                    'reading-r01/locked-source-coverage-stage2-final-r01.json',
                    'reading-r01/adjudication-selected-r01.json',
                    'reading-r01/adjudication-stage2-selected-r01.json']
    input_hashes = {name: e.sha(HERE / name) for name in source_names}
    for stage, namespace, expected_packets in [('stage1', 'delivery-stage1-r01', 15),
                                                ('stage2', 'delivery-full-r01', 18)]:
        key = {r['id']: r for r in e.read(HERE / namespace / 'private-key.json')['mapping']}
        locks = sorted((HERE / f'reading-r01/{stage}-reviews').glob('packet-*-lock.json'))
        assert len(locks) == expected_packets
        for lock_path in locks:
            lock = e.read(lock_path)
            name = lock_path.name.replace('-lock.json', '.jsonl')
            review_path = lock_path.with_name(name)
            assert lock['status'] == 'locked' and e.sha(review_path) == lock['output_sha256']
            packet_path = HERE / f'reading-r01/{stage}-packets' / name
            assert e.sha(packet_path) == lock['input_sha256']
            reviews, packet = lines(review_path), lines(packet_path)
            assert len(reviews) == len(packet)
            assert {r['id'] for r in reviews} == {r['id'] for r in packet}
            for path in [lock_path, review_path, packet_path]:
                input_hashes[str(path.relative_to(HERE))] = e.sha(path)
            for review in reviews:
                assert review['delivery_namespace'] == namespace
                source = key[review['id']]
                digest = source['source_sha256']
                assert digest not in observations
                observations[digest] = {'review': review, 'review_path': str(review_path.relative_to(HERE))}
    assert len(observations) == 3720
    items = {r['id']: r for r in e.inputs()}
    conditions = ['clean'] + [f'{recipe}_d{dose}' for recipe in ['AB', 'R01', 'R02', 'R03', 'R04', 'R05']
                              for dose in ['0.0625', '0.125', '0.25', '0.5', '1']]
    keys = e.read(HERE / 'delivery-full-r01/private-key.json')['mapping']
    metrics = {(r['item_id'], r['condition']): r for r in e.read(HERE / 'delivery-full-r01/quantitative.json')['records']}
    records, groups, pairs = [], defaultdict(list), set()
    for key in keys:
        suffix = key['source_path'].split('/' + HERE.name + '/', 1)[1]
        path = HERE / suffix
        assert e.sha(path) == key['source_sha256']
        raw, item = e.read(path), items[key['item_id']]
        pair = (item['id'], key['condition']['id'])
        assert pair not in pairs
        pairs.add(pair)
        row = {'item': item, 'condition': key['condition'], 'source_path': suffix,
               'source_sha256': key['source_sha256'], 'output': raw['output'],
               'candidate_readout': metrics[pair]['candidate_readout'],
               **observations[key['source_sha256']]}
        records.append(row)
        groups[item['base_id']].append(row)
    assert pairs == {(item, condition) for item in items for condition in conditions}
    output = HERE / 'analysis-r01'
    e.write(output / 'paired-reading-records-r01.json', {'at': e.utc(), 'records': records,
            'note': 'Verbatim locked observations joined by source SHA, not new semantic classification.'}, immutable=True)
    notes = output / 'paired-units-r01'
    notes.mkdir(exist_ok=False)
    for base, rows in sorted(groups.items()):
        rows.sort(key=lambda r: (conditions.index(r['condition']['id']), r['item']['id']))
        text = [f'# {base}：已锁定原文判读的配对索引', '',
                '下表原样保留模型辅助匿名阅读的判读，不是互斥评分或新的语义分类。'
                '固定候选读数只代表规定措辞偏好。请结合原文和追加争议复核解释损伤，'
                '不要把粗俗、未交付、明确错误和正确核心后的错误解释混为一类。', '',
                '| 条件 | 输入 | 内容观察 | 任务交付 | 表达风格 | 不确定性 | 原文来源 |',
                '|---|---|---|---|---|---|---|']
        for row in rows:
            r = row['review']
            values = [row['condition']['id'], row['item']['id'], r['content'], r['delivery'], r['style'], r['uncertainty']]
            text.append('| ' + ' | '.join(cell(v) for v in values) +
                        f" | [原文](../../{row['source_path']}) |")
        (notes / f'{base}.md').write_text('\n'.join(text) + '\n')
    e.write(output / 'paired-reading-manifest-r01.json', {'status': 'joined_locked_observations',
            'at': e.utc(), 'records': len(records), 'diagnostic_bases': 24, 'open_questions': 24,
            'conditions': 31, 'new_semantic_judgments': 0, 'input_hashes': input_hashes,
            'freeze_identity': identity,
            'script_sha256': e.sha(Path(__file__)), 'files': {str(p.relative_to(output)): e.sha(p)
                for p in [output / 'paired-reading-records-r01.json', *sorted(notes.glob('*.md'))]}}, immutable=True)
    print(json.dumps({'status': 'joined', 'records': len(records), 'units': len(groups)}))


if __name__ == '__main__':
    main()
