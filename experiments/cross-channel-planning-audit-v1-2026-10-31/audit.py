"""Read existing L0/4B JSON records only; no model or third-party imports."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sources = [
    'layer-survey-toy-v1-2026-10-27',
    'layer-dose-survey-toy-v1-2026-10-27',
    'layer-negative-dose-survey-toy-v1-2026-10-27',
]
manifest = {}


def read(p):
    raw = p.read_bytes()
    manifest[str(p.relative_to(ROOT))] = hashlib.sha256(raw).hexdigest()
    return json.loads(raw)


samples = read(ROOT / 'experiments' / sources[0] / 'samples.json')
channels = sorted(x['channel'] for x in samples['4b'] if x['layer'] == 0)
selection = read(ROOT / 'experiments' / sources[1] / 'selection.json')
assert [x['channel'] for x in selection['selected_channels']
        if x['model_id'] == '4b' and x['layer'] == 0] == [4146]
baseline = {}
records = []
receipts = []
for source in sources:
    base = ROOT / 'experiments' / source
    for name in ['contract.json', 'freeze.json']:
        read(base / name)
    for worker in sorted((base / 'survey-r01').glob('4b-shard-*')):
        if not worker.is_dir():
            continue
        receipt = read(worker / 'receipt.json')
        assert receipt['status'] == 'completed' and receipt['checks_passed']
        receipts.append({'path': str((worker / 'receipt.json').relative_to(ROOT)),
                         'completed_records': receipt['completed_records']})
        paths = sorted((worker / 'records').glob('L00-*.json'))
        if source == sources[0]:
            paths += sorted((worker / 'records').glob('baseline__*.json'))
        for p in paths:
            r = read(p)
            assert manifest[str(p.relative_to(ROOT))] == receipt['record_hashes'][str(p.relative_to(worker))]
            assert r['status'] == 'completed' and r['model_id'] == '4b'
            if p.name.startswith('baseline__'):
                baseline[r['question_id']] = r
            else:
                assert r['layer'] == 0 and r['channel'] in channels
                records.append((p, r))

assert len(baseline) == 8
groups = defaultdict(list)
for p, r in records:
    dose = r.get('dose', r['intervention']['dose'])
    groups[(r['channel'], dose)].append((p, r))
assert len(records) == 152  # 80 ten-channel +1, 32 new positive, 40 negative
assert len(groups) == 19
rows = []
raw_rows = []
for (channel, dose), items in sorted(groups.items()):
    assert len(items) == 8 and {r['question_id'] for _, r in items} == set(baseline)
    vals = []
    for p, r in sorted(items, key=lambda pr: pr[1]['question_id']):
        o = r['output']
        b = baseline[r['question_id']]
        assert r['calibration']['input_token_sha256'] == b['calibration']['input_token_sha256']
        ids = o['token_ids']
        assert len(ids) == o['generated_token_count'] <= 128
        v = {'question': r['question_id'], 'first_eos': bool(ids and ids[0] in [248044, 248046]),
             'empty': not o['answer_text'].strip(), 'cap128': len(ids) == 128,
             'same_tokens_as_clean': ids == b['output']['token_ids'], 'tokens': len(ids)}
        vals.append(v)
        raw_rows.append({'channel': channel, 'dose': dose, **v, 'path': str(p.relative_to(ROOT)),
                         'answer_text': o['answer_text'], 'token_ids': ids,
                         'clean_answer_text': b['output']['answer_text']})
    rows.append({'channel': channel, 'dose': dose, 'n': 8,
                 **{k: sum(v[k] for v in vals) for k in ['first_eos', 'empty', 'cap128', 'same_tokens_as_clean']},
                 'tokens_min_max': [min(v['tokens'] for v in vals), max(v['tokens'] for v in vals)]})
result = {'scope': 'L0 Qwen3.5-4B, historical Q01-Q08, whole-prompt-and-generation injection',
          'channels': channels, 'verified_modified_records': len(records), 'verified_baselines': 8,
          'coverage': rows, 'receipts': receipts, 'source_sha256': manifest, 'records': raw_rows,
          'limitations': ['Mechanical output counts, not semantic correctness or mechanism evidence.',
                         'Only N4146 has the full signed dose sweep in these three sources.',
                         'No new model execution; token digest not independently rederived; record bytes checked against receipts.']}
(OUT / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'verified_modified_records': len(records), 'baselines': len(baseline), 'coverage': rows}, ensure_ascii=False, indent=2))
