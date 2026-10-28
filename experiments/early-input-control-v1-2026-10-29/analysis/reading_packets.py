"""Blind reading packets for free-form answers; the key stays separate until labels are locked.

build:  python analysis/reading_packets.py build RUN_DIR OUT_DIR --seed N
lock:   python analysis/reading_packets.py lock OUT_DIR
join:   python analysis/reading_packets.py join OUT_DIR   (only after lock)
Readers receive packets/*.json only; key.json maps anonymous ids to record keys.
"""
import argparse
import hashlib
import json
import random
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

LABELS = {'fact': ('follows_fact', 'other_fact', 'other_wrong', 'not_delivered', 'unclear'),
          'contradiction': (True, False), 'repetition': (True, False)}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def records(run):
    for receipt in sorted(Path(run).glob('worker-*/receipt.json')):
        worker = receipt.parent
        for relative, digest in json.loads(receipt.read_text())['record_hashes'].items():
            assert sha(worker / relative) == digest, relative
            yield worker / relative, json.loads((worker / relative).read_text())


def mechanics(tokens, end_reason):
    """Mechanical, text-free descriptors kept apart from semantic labels."""
    repeat = 0
    for n in (4, 8):
        grams = [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]
        repeat = max(repeat, max((grams.count(g) for g in set(grams)), default=0))
    return {'tokens': len(tokens), 'end_reason': end_reason, 'hit_128': end_reason == 'length_limit',
            'max_ngram_repeat': repeat}


def build(run, out, seed):
    out = Path(out)
    assert not out.exists()
    by_item, items = defaultdict(list), {}
    for path, row in records(run):
        if row['status'] != 'completed' or 'generation' not in row:
            continue
        g = row['generation']
        items[row['item_id']] = row['item']
        by_item[row['item_id']].append({'record': str(path), 'key': row['spec']['key'],
            'condition': row['effective_condition'], 'mode': row['spec'].get('mode'),
            'branch': row['spec'].get('branch'), 'arm': row['spec'].get('arm'),
            'text': g['answer_text'], 'mech': mechanics(g['token_ids'], g['end_reason'])})
    rng = random.Random(seed)
    key, packets = {}, defaultdict(list)
    for item_id in sorted(by_item):
        item, rows = items[item_id], by_item[item_id]
        unique = sorted({r['text'] for r in rows})
        rng.shuffle(unique)
        anon = {}
        for text in unique:
            a = 'A' + hashlib.sha256(f'{seed}|{item_id}|{text}'.encode()).hexdigest()[:10]
            anon[text] = a
            key[a] = {'item_id': item_id, 'text_sha256': hashlib.sha256(text.encode()).hexdigest(),
                      'records': [{'key': r['key'], 'record': r['record'], 'condition': r['condition'],
                                   'mode': r['mode'], 'branch': r['branch'], 'arm': r['arm'], 'mech': r['mech']}
                                  for r in rows if r['text'] == text]}
        packets[item['base_id']].append({'item_id': item_id, 'prompt': item['prompt'],
            'expected_answer': item['choices'][item['target_index']] if item.get('choices') else None,
            'other_fact_answer': item['choices'][1 - item['target_index']] if item.get('choices') else None,
            'truth_explanation': item.get('truth_explanation'),
            'responses': [{'id': anon[t], 'text': t} for t in unique]})
    for base, value in packets.items():
        write(out / 'packets' / f'{base}.json', {'base_id': base, 'instructions': INSTRUCTIONS, 'items': value})
    write(out / 'key.json', key)
    write(out / 'build.json', {'run': str(run), 'seed': seed, 'built_at': datetime.now(timezone.utc).isoformat(),
        'records': sum(len(v) for v in by_item.values()), 'unique_texts': len(key),
        'packet_hashes': {p.name: sha(p) for p in sorted((out / 'packets').glob('*.json'))},
        'key_sha256': sha(out / 'key.json')})


INSTRUCTIONS = ("逐条阅读每个回答，只依据题面判断，不猜测它来自何种条件。每条输出一行 JSON："
    '{"id":..., "fact": follows_fact|other_fact|other_wrong|not_delivered|unclear, '
    '"contradiction": bool, "repetition": bool, "note": "≤30字具体描述（风格、附带错误、乱码等）"}。'
    "follows_fact=给出与题面事实一致的核心答案（附语有错也算，但在 note 写明附带错误）；"
    "other_fact=给出另一事实版本的答案；other_wrong=给出其他错误答案；"
    "not_delivered=没有给出可判定的答案（空、乱码、跑题、只复述题目）；unclear=无法判断。"
    "contradiction=回答内部前后矛盾；repetition=明显重复循环。")


def lock(out):
    out = Path(out)
    labels = sorted((out / 'labels').glob('*.jsonl'))
    build_info = json.loads((out / 'build.json').read_text())
    seen = {}
    for path in labels:
        for line in path.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                assert row['fact'] in LABELS['fact'] and type(row['contradiction']) is bool and type(row['repetition']) is bool
                assert row['id'] not in seen, row['id']
                seen[row['id']] = row
    expected = {r['id'] for p in (out / 'packets').glob('*.json') for i in json.loads(p.read_text())['items'] for r in i['responses']}
    assert set(seen) == expected, (len(expected - set(seen)), len(set(seen) - expected))
    write(out / 'lock.json', {'locked_at': datetime.now(timezone.utc).isoformat(), 'labels': len(seen),
        'label_hashes': {p.name: sha(p) for p in labels}, 'build_sha256': sha(out / 'build.json'),
        'key_sha256_at_lock': build_info['key_sha256'], 'key_opened_before_lock': False})


def join(out):
    out = Path(out)
    lock_info = json.loads((out / 'lock.json').read_text())
    for name, digest in lock_info['label_hashes'].items():
        assert sha(out / 'labels' / name) == digest, 'labels changed after lock'
    labels = {}
    for path in sorted((out / 'labels').glob('*.jsonl')):
        for line in path.read_text().splitlines():
            if line.strip():
                row = json.loads(line); labels[row['id']] = row
    key = json.loads((out / 'key.json').read_text())
    rows = [{**rec, 'item_id': v['item_id'], 'anon_id': a, 'label': labels[a]} for a, v in key.items() for rec in v['records']]
    write(out / 'joined.json', {'joined_at': datetime.now(timezone.utc).isoformat(), 'lock_sha256': sha(out / 'lock.json'), 'rows': rows})


if __name__ == '__main__':
    p = argparse.ArgumentParser(); s = p.add_subparsers(dest='cmd', required=True)
    b = s.add_parser('build'); b.add_argument('run'); b.add_argument('out'); b.add_argument('--seed', type=int, required=True)
    for n in ('lock', 'join'):
        s.add_parser(n).add_argument('out')
    a = p.parse_args()
    build(a.run, a.out, a.seed) if a.cmd == 'build' else lock(a.out) if a.cmd == 'lock' else join(a.out)
