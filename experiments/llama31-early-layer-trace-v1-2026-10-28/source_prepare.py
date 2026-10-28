"""Select and verify existing Llama A/B answers for six-layer internal tracing."""
from collections import Counter
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
MODEL = 'llama31-8b-instruct'
REVISION = '0e9e39f249a16976918f6564b8830bc894c89659'
SOURCE_EXPERIMENTS = ('llama31-layer-survey-v1-2026-10-28',
                      'llama31-single-point-dose-survey-v1-2026-10-28')
SOURCE_PATHS = [f'experiments/{name}/delivery-r01/all.records.jsonl' for name in SOURCE_EXPERIMENTS]
DOSES = {-1.0, -0.5, -0.25, -0.125, -0.0625, 0.0625, 0.125, 0.25, 0.5, 1.0}
spec = importlib.util.spec_from_file_location('llama_trace_source_helpers', ROOT.parent / 'early-layer-mechanism-v1-2026-10-28/trace_run.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
base.MODELS = (MODEL,)
read, write, sha, utc = base.read, base.write, base.sha, base.utc
identity, trace_id = base.identity, base.trace_id
split_records, select_preflight = base.split_records, base.select_preflight


def build_source_inventory(source_paths=None, contract=None):
    contract = contract or read(ROOT / 'contract.json')
    assert [s['path'] for s in contract['sources']] == SOURCE_PATHS, 'Only completed separate Llama A/B sources are allowed'
    model = contract['models'][0]
    assert len(contract['models']) == 1 and model['id'] == MODEL and model['revision'] == REVISION
    assert (model['layers'], model['hidden_size'], model['intermediate_size']) == (32, 4096, 14336)
    assert model['included_layers'] == list(range(6))
    paths = source_paths or [REPO / p for p in SOURCE_PATHS]
    assert len(paths) == 2
    inventory, duplicates = {}, 0
    for path, source in zip(paths, contract['sources']):
        assert sha(path) == source['sha256'], f'Source changed: {path}'
        for line, text in enumerate(Path(path).read_text().splitlines(), 1):
            row = json.loads(text)
            assert row['model_id'] == MODEL and row['status'] == 'completed'
            key = identity(row)
            reference = {'jsonl': source['path'], 'line': line, 'sha256': source['sha256']}
            if key in inventory:
                previous = inventory[key]['record']
                assert all(previous[field] == row[field] for field in ('context', 'calibration', 'prompt', 'intervention', 'output')), f'Conflicting source: {key}'
                inventory[key]['references'].append(reference)
                duplicates += 1
            else:
                inventory[key] = {'record': row, 'references': [reference]}
    assert len(inventory) == 4872 and duplicates == 264, 'Source coverage changed'
    selected = []
    for item in inventory.values():
        row = item['record']
        if row['layer'] is not None and row['layer'] not in range(6):
            continue
        origin = row['export_source']
        assert origin['origin'] == 'new', 'Canonical records must come from their producing run'
        selected.append({**item, 'trace_id': trace_id(row), 'model': MODEL,
                         'historical_shard': origin['worker_shard']})
    selected.sort(key=lambda item: item['trace_id'])
    conditions = sorted({identity(i['record'])[1:4] for i in selected if i['record']['layer'] is not None})
    assert len(selected) == 920 and len(conditions) == 114
    for item in selected:
        key = identity(item['record'])
        item['shard'] = 0 if key[1] is None else conditions.index(key[1:4]) % 2
    for layer in range(6):
        rows = [i['record'] for i in selected if i['record']['layer'] == layer]
        assert len(rows) == 152 and len({r['channel'] for r in rows}) == 10
        assert sum(r['dose'] == 1 for r in rows) == 80
        signed = {r['channel'] for r in rows if r['dose'] != 1}
        assert len(signed) == 1
        assert {r['dose'] for r in rows if r['channel'] in signed} == DOSES
    for condition in [None] + conditions:
        rows = [i['record'] for i in selected if (identity(i['record'])[1:4] if i['record']['layer'] is not None else None) == condition]
        assert sorted(r['question_id'] for r in rows) == [f'Q{i:02}' for i in range(1, 9)]
    assert [len(split_records(selected, MODEL, s)) for s in (0, 1)] == [464, 456]
    return selected


def source_provenance(item):
    row = item['record']
    path = REPO / row['export_source']['record']
    assert any(path.is_relative_to(REPO / 'experiments' / e / 'survey-r01') for e in SOURCE_EXPERIMENTS), 'Stopped/other source run forbidden'
    provenance, metadata = base.source_provenance(item)
    run = REPO / provenance['run']
    receipt, raw = read(run / 'receipt.json'), read(path)
    assert identity(raw) == identity(row) and raw['intervention'] == row['intervention']
    assert row['export_source']['record_sha256'] == provenance['record_sha256']
    assert row['export_source']['receipt_sha256'] == provenance['receipt_sha256']
    assert metadata['model_id'] == MODEL and metadata['revision'] == REVISION
    assert metadata['hidden_size'] == 4096 and metadata['intermediate_size'] == 14336
    assert metadata['layers'] == list(range(32))
    assert receipt['mode'] == 'survey' and receipt['model_id'] == MODEL
    assert receipt['shard'] == item['historical_shard']
    assert (run.parent / f'{run.name}.exit').read_text().strip() == '0'
    source_root = run.parent.parent
    assert receipt['freeze_sha256'] == sha(source_root / 'freeze.json')
    provenance.update(source_freeze_sha256=receipt['freeze_sha256'],
                      exit_sha256=sha(run.parent / f'{run.name}.exit'))
    return provenance, metadata


def prepare_sources():
    assert not (ROOT / 'freeze.json').exists(), 'Frozen preparation cannot be overwritten'
    for name in ('sources.jsonl', 'source-metadata.json', 'source-manifest.json'):
        assert not (ROOT / name).exists(), f'Do not overwrite preparation evidence: {name}'
    rows, metadata = build_source_inventory(), {}
    for item in rows:
        provenance, source_metadata = source_provenance(item)
        item['provenance'] = provenance
        metadata[provenance['run']] = source_metadata
    manifest = {
        'sources': read(ROOT / 'contract.json')['sources'],
        'input_unique_records': 4872, 'duplicate_references': 264,
        'total_records': len(rows), 'counts': dict(Counter(i['model'] for i in rows)),
        'shards': {f'{MODEL}-{s}': len(split_records(rows, MODEL, s)) for s in (0, 1)},
        'source_output_tokens': {str(s): sum(len(i['record']['output']['token_ids']) for i in split_records(rows, MODEL, s)) for s in (0, 1)},
        'source_generation_seconds': {str(s): sum(i['record']['output']['batch_seconds'] for i in split_records(rows, MODEL, s)) for s in (0, 1)},
        'preflight': {f'{MODEL}-{s}': [{'name': c['name'], 'trace_id': c['record']['trace_id'], 'arm_override': c['arm_override']} for c in select_preflight(rows, MODEL, s)] for s in (0, 1)},
        'source_raw_and_receipts_verified': True, 'created_utc': utc(),
    }
    (ROOT / 'sources.jsonl').write_text(''.join(json.dumps(i, ensure_ascii=False, allow_nan=False) + '\n' for i in rows))
    write(ROOT / 'source-metadata.json', metadata)
    write(ROOT / 'source-manifest.json', manifest)
    return manifest


if __name__ == '__main__':
    print(json.dumps(prepare_sources(), ensure_ascii=False, indent=2))
