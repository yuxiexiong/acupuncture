"""Blind packets for localization records in the early-input-control reading format (lock/join reuse its tool).

python analysis/build_reading.py RUN_DIR [RUN_DIR ...] OUT_DIR SEED
"""
import hashlib
import importlib.util
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location('rp', HERE.parent / 'early-input-control-v1-2026-10-29/analysis/reading_packets.py')
rp = importlib.util.module_from_spec(_s)
_s.loader.exec_module(rp)


def main(*args):
    *runs, out, seed = args
    seed, out = int(seed), Path(out)
    assert not out.exists()
    by_item, items = defaultdict(list), {}
    for run in runs:
        for receipt in sorted(Path(run).glob('worker-*/receipt.json')):
            for rel, digest in json.loads(receipt.read_text())['record_hashes'].items():
                path = receipt.parent / rel
                assert rp.sha(path) == digest, rel
                r = json.loads(path.read_text())
                g = r['generation']
                items[r['item']['id']] = r['item']
                by_item[r['item']['id']].append({'record': str(path.resolve()), 'key': r['spec']['key'], 'condition': r['condition'],
                    'mode': None, 'branch': None, 'arm': r['spec']['arm'], 'text': g['answer_text'],
                    'mech': rp.mechanics(g['token_ids'], g['end_reason'])})
    rng = random.Random(seed)
    key, packets = {}, defaultdict(list)
    for item_id in sorted(by_item):
        item, rows = items[item_id], by_item[item_id]
        unique = sorted({r['text'] for r in rows})
        rng.shuffle(unique)
        anon = {t: 'A' + hashlib.sha256(f'{seed}|{item_id}|{t}'.encode()).hexdigest()[:10] for t in unique}
        for t in unique:
            key[anon[t]] = {'item_id': item_id, 'text_sha256': hashlib.sha256(t.encode()).hexdigest(),
                            'records': [{k: r[k] for k in ('key', 'record', 'condition', 'mode', 'branch', 'arm', 'mech')} for r in rows if r['text'] == t]}
        packets[item['base_id']].append({'item_id': item_id, 'prompt': item['prompt'],
            'expected_answer': item['choices'][item['target_index']], 'other_fact_answer': item['choices'][1 - item['target_index']],
            'truth_explanation': item.get('truth_explanation'), 'responses': [{'id': anon[t], 'text': t} for t in unique]})
    for base, value in packets.items():
        rp.write(out / 'packets' / f'{base}.json', {'base_id': base, 'instructions': rp.INSTRUCTIONS, 'items': value})
    rp.write(out / 'key.json', key)
    rp.write(out / 'build.json', {'runs': [str(r) for r in runs], 'seed': seed, 'records': sum(len(v) for v in by_item.values()),
        'unique_texts': len(key), 'packet_hashes': {p.name: rp.sha(p) for p in sorted((out / 'packets').glob('*.json'))}, 'key_sha256': rp.sha(out / 'key.json')})
    print(sum(len(v) for v in by_item.values()), len(key))


if __name__ == '__main__':
    main(*sys.argv[1:])
