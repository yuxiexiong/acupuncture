"""Frozen-source internal traces; prepare on CPU, then bounded preflight and collection."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from functools import lru_cache
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import time
import traceback

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
MODELS = ('4b', '2b', '9b')
EXPECTED = {'2b': 616, '4b': 616, '9b': 920}


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def utc():
    return datetime.now(timezone.utc).isoformat()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def identity(row):
    layer = row.get('layer')
    dose = float(row.get('dose', (row.get('intervention') or {}).get('dose', 0))) if layer is not None else 0.0
    return row['model_id'], layer, row.get('channel'), dose, row['question_id']


def trace_id(row):
    model, layer, channel, dose, question = identity(row)
    point = 'baseline' if layer is None else f'L{layer:02}-N{channel:06}-D{dose:+g}'
    return f'{model}-{point}__{question}'


def build_source_inventory(source_paths=None):
    contract = read(ROOT / 'contract.json')
    sources = source_paths or [REPO / item['path'] for item in contract['sources']]
    assert len(sources) == 3
    rows, duplicate_count = {}, 0
    for path, source in zip(sources, contract['sources']):
        assert sha(path) == source['sha256'], f'Source changed: {path}'
        with Path(path).open() as f:
            for line, text in enumerate(f, 1):
                row = json.loads(text)
                key = identity(row)
                reference = {'jsonl': source['path'], 'line': line, 'sha256': source['sha256']}
                if key in rows:
                    old = rows[key]['record']
                    assert old['output']['token_ids'] == row['output']['token_ids'], f'Conflicting source: {key}'
                    assert old['context'] == row['context'] and old['calibration'] == row['calibration']
                    rows[key]['references'].append(reference)
                    duplicate_count += 1
                else:
                    rows[key] = {'record': row, 'references': [reference]}
    assert len(rows) == 13400 and duplicate_count == 4272
    included = {m['id']: m['included_layers'] for m in contract['models']}
    selected = []
    for key, item in rows.items():
        model, layer, channel, dose, qid = key
        if layer is not None and layer not in included[model]:
            continue
        row = item['record']
        historical_shard = int(row.get('export_source', {}).get('worker_shard', str(row.get('source_run', '')).rsplit('-', 1)[-1] or 0))
        selected.append({**item, 'trace_id': trace_id(row), 'model': model, 'historical_shard': historical_shard})
    selected.sort(key=lambda item: item['trace_id'])
    for model in MODELS:
        model_rows = [item for item in selected if item['model'] == model]
        assert len(model_rows) == EXPECTED[model]
        conditions = sorted({identity(item['record'])[1:4] for item in model_rows if item['record']['layer'] is not None})
        assert len(conditions) == len(included[model]) * 19
        for item in model_rows:
            key = identity(item['record'])
            item['shard'] = 0 if key[1] is None else conditions.index(key[1:4]) % 2
        for layer in included[model]:
            records = [item['record'] for item in model_rows if item['record']['layer'] == layer]
            assert len(records) == 152
            assert len({r['channel'] for r in records}) == 10
            assert sum(identity(r)[3] == 1 for r in records) == 80
        for condition in [None] + conditions:
            group = [item['record'] for item in model_rows if (identity(item['record'])[1:4] if item['record']['layer'] is not None else None) == condition]
            assert sorted(r['question_id'] for r in group) == [f'Q{i:02}' for i in range(1, 9)]
    return selected


def split_records(records, model, shard):
    assert model in MODELS and shard in (0, 1)
    return sorted((item for item in records if item['model'] == model and item['shard'] == shard), key=lambda item: (item['record']['layer'] is not None, item['trace_id']))


def select_preflight(records, model, shard):
    baseline = next(item for item in records if item['model'] == model and item['record']['layer'] is None and item['record']['question_id'] == 'Q01')
    pool = [item for item in split_records(records, model, shard) if item['record']['layer'] is not None]
    used, selected = set(), [{'name': 'baseline', 'record': baseline, 'arm_override': 'baseline'}]
    criteria = [
        ('short_eos', lambda item: True, lambda item: (len(item['record']['output']['token_ids']), item['trace_id'])),
        ('long_positive', lambda item: identity(item['record'])[3] > 0, lambda item: (-len(item['record']['output']['token_ids']), item['trace_id'])),
        ('negative', lambda item: identity(item['record'])[3] < 0, lambda item: item['trace_id']),
        ('low_positive', lambda item: 0 < identity(item['record'])[3] < 1, lambda item: item['trace_id']),
    ]
    for name, predicate, key in criteria:
        candidates = sorted((item for item in pool if predicate(item) and item['trace_id'] not in used), key=key)
        assert candidates, f'No preflight coverage: {model}/{shard}/{name}'
        item = candidates[0]
        used.add(item['trace_id'])
        selected.append({'name': name, 'record': item, 'arm_override': None})
    point = min(pool, key=lambda item: item['trace_id'])['record']
    selected += [{'name': 'zero', 'record': baseline, 'arm_override': [point['layer'], point['channel'], 0.0]},
                 {'name': 'restored', 'record': baseline, 'arm_override': 'baseline'}]
    return selected


def source_provenance(item):
    row = item['record']
    if row.get('export_source', {}).get('origin') == 'new':
        path = REPO / row['export_source']['record']
    else:
        run = 'experiments/' + row['source_run'].split('/experiments/', 1)[1]
        path = REPO / run / row['source_record']
    run = path.parent.parent
    receipt, raw = read(run / 'receipt.json'), read(path)
    relative = str(path.relative_to(run))
    assert receipt['status'] == 'completed' and receipt['checks_passed'] is True
    assert receipt['record_hashes'][relative] == sha(path)
    assert receipt['integrity']['hooks_removed'] is True
    for key in ('model_id', 'layer', 'channel', 'question_id', 'context', 'calibration', 'output'):
        assert raw[key] == row[key], f'Source export disagrees with raw: {path} {key}'
    metadata = read(run / 'metadata.json')
    assert receipt['asset_hashes']['metadata.json'] == sha(run / 'metadata.json')
    assert metadata['target_weight_sha256_before'] == receipt['integrity']['target_weight_sha256_after']
    return {'record': str(path.relative_to(REPO)), 'record_sha256': sha(path),
            'run': str(run.relative_to(REPO)), 'receipt_sha256': sha(run / 'receipt.json'),
            'metadata_sha256': sha(run / 'metadata.json')}, metadata


def prepare():
    assert not (ROOT / 'freeze.json').exists(), 'Frozen preparation already exists; do not overwrite'
    rows = build_source_inventory()
    metadata = {}
    for item in rows:
        provenance, source_metadata = source_provenance(item)
        item['provenance'] = provenance
        metadata[provenance['run']] = source_metadata
    (ROOT / 'sources.jsonl').write_text(''.join(json.dumps(item, ensure_ascii=False, allow_nan=False) + '\n' for item in rows))
    write(ROOT / 'source-metadata.json', metadata)
    write(ROOT / 'source-manifest.json', {
        'sources': read(ROOT / 'contract.json')['sources'],
        'total_records': len(rows), 'counts': dict(Counter(item['model'] for item in rows)),
        'shards': {f'{m}-{s}': len(split_records(rows, m, s)) for m in MODELS for s in (0, 1)},
        'preflight': {f'{m}-{s}': [{'name': c['name'], 'trace_id': c['record']['trace_id'], 'arm_override': c['arm_override']} for c in select_preflight(rows, m, s)] for m in MODELS for s in (0, 1)},
        'source_raw_and_receipts_verified': True, 'created_utc': utc()})
    dependencies = [
        'layer-negative-dose-survey-toy-v1-2026-10-27/dose_engine.py',
        'layer-negative-dose-survey-toy-v1-2026-10-27/dose_survey.py',
        'layer-negative-dose-survey-toy-v1-2026-10-27/asset_manifest.json',
        'layer-dose-survey-toy-v1-2026-10-27/dose_engine.py',
        'layer-survey-toy-v1-2026-10-27/survey_engine.py',
        'transfer-toy-v1-2026-10-26/transfer_engine.py',
        'transfer-toy-v1-2026-10-26/run_io.py',
        'capability-damage-v2-2026-10-26/model_engine.py']
    paths = list(ROOT.glob('*.py')) + [ROOT / name for name in ('contract.json', 'CONTRACT.zh-CN.md', 'sources.jsonl', 'source-metadata.json', 'source-manifest.json')]
    paths += [ROOT.parent / name for name in dependencies]
    write(ROOT / 'freeze.json', {'experiment': ROOT.name, 'created_utc': utc(), 'files': {str(p.relative_to(REPO)): sha(p) for p in sorted(paths)}})
    return read(ROOT / 'source-manifest.json')


def validate_freeze():
    frozen = read(ROOT / 'freeze.json')
    assert frozen['experiment'] == ROOT.name
    for name, digest in frozen['files'].items():
        assert sha(REPO / name) == digest, f'Frozen file changed: {name}'
    return sha(ROOT / 'freeze.json')


def validate_authorization(path):
    auth = read(path)
    assert auth['status'] == 'authorized' and auth['purpose'] == 'early_layer_trace_queue'
    assert auth['experiment'] == ROOT.name and auth['user_instruction']
    assert auth['freeze_sha256'] == validate_freeze()
    assert auth['models'] == list(MODELS)
    assert auth['maximum_records'] == {'preflight': 42, 'survey': 2152}
    assert auth['maximum_generations'] == {'preflight': 114, 'survey': 4304}
    cpu = auth['cpu_test_receipt']
    assert sha(ROOT / cpu['path']) == cpu['sha256']
    result = read(ROOT / cpu['path'])
    assert result['status'] == 'passed' and result['failures'] == 0 and result['errors'] == 0 and result['skipped'] == 0
    assert result['freeze_sha256'] == auth['freeze_sha256']
    assert auth['queue_sha256'] == sha(ROOT / 'queue_run.py')
    return auth


@lru_cache(maxsize=1)
def load_sources():
    with (ROOT / 'sources.jsonl').open() as f:
        return [json.loads(line) for line in f]


def cases_for(mode, model, shard):
    rows = load_sources()
    if mode == 'preflight':
        return select_preflight(rows, model, shard)
    assert mode == 'survey'
    return [{'name': item['trace_id'], 'record': item, 'arm_override': None} for item in split_records(rows, model, shard)]


def check_trace(trace, item, arm):
    row = item['record']
    ids = trace['generated_token_ids']
    assert ids == row['output']['token_ids']
    assert trace['source_token_ids_match'] is True
    assert trace['input_token_sha256'] == row['calibration']['input_token_sha256']
    count = row['calibration']['input_token_count'] + len(ids) - 1
    assert trace['observed_position_count'] == count
    assert trace['observed_input_token_ids'] == trace['input_token_ids'] + ids[:-1]
    assert len(trace['forward_steps']) == len(ids) == len(trace['logits']['steps'])
    assert trace['clean_shadow']['fresh_cache'] is True
    assert trace['clean_shadow']['token_ids'] == ids
    assert trace['clean_shadow']['prefixes_verified'] == len(ids)
    spec = next(m for m in read(ROOT / 'contract.json')['models'] if m['id'] == item['model'])
    expected_sites = {(layer, component) for layer in range(spec['layers']) for component in ('attention', 'mlp', 'residual')}
    assert {(s['layer'], s['component']) for s in trace['sites']} == expected_sites
    assert len(trace['sites']) == len(expected_sites)
    zero = arm == 'baseline' or arm[2] == 0
    for site in trace['sites']:
        for field in ('clean_norm', 'steer_norm', 'delta_norm', 'relative_delta', 'cosine'):
            values = site[field]
            assert len(values) == count
            assert all(v is None or math.isfinite(v) for v in values)
        for i, norm in enumerate(site['clean_norm']):
            assert norm is not None and norm >= 0 and site['steer_norm'][i] is not None and site['delta_norm'][i] is not None
            assert (site['relative_delta'][i] is None) == (norm == 0)
            assert (site['cosine'][i] is None) == (norm * site['steer_norm'][i] == 0)
        if zero:
            assert all(value == 0 for value in site['delta_norm']), 'Zero/control branch changed components'
        elif site['layer'] < arm[0] or (site['layer'] == arm[0] and site['component'] == 'attention'):
            assert all(value == 0 for value in site['delta_norm'][:trace['prompt_token_count']]), 'Prompt changed before injection site'
    for step in trace['logits']['steps']:
        assert step['generated_token_id'] == ids[step['step']]
        if zero:
            assert all(c['clean_logit'] == c['steer_logit'] for c in step['candidates'])
        assert all(math.isfinite(c[k]) for c in step['candidates'] for k in ('clean_logit', 'steer_logit', 'clean_logprob', 'steer_logprob'))
    return True


def read_trace(path):
    with gzip.open(path, 'rt') as f:
        return json.load(f)


def verify_worker(output, mode, model, shard):
    output = Path(output)
    receipt = read(output / 'receipt.json')
    assert receipt['status'] == 'completed' and receipt['checks_passed'] is True
    assert (receipt['mode'], receipt['model_id'], receipt['shard']) == (mode, model, shard)
    assert receipt['freeze_sha256'] == sha(ROOT / 'freeze.json')
    cases = cases_for(mode, model, shard)
    assert receipt['completed_records'] == receipt['expected_records'] == len(cases)
    assert receipt['integrity']['hooks_removed'] is True
    metadata = read(output / 'metadata.json')
    assert metadata['target_weight_sha256_before'] == receipt['integrity']['target_weight_sha256_after']
    for name, digest in receipt['asset_hashes'].items():
        assert sha(output / name) == digest
    expected_files = set()
    for index, case in enumerate(cases):
        name = f'records/{index:04}-{case["name"]}.json'
        trace_name = f'traces/{index:04}-{case["name"]}.json.gz'
        expected_files.update((name, trace_name))
        record = read(output / name)
        assert record['trace_id'] == case['record']['trace_id']
        assert record['status'] == 'completed' and record['checks_passed'] is True
        assert record['source'] == case['record']['provenance']
        assert record['source_token_ids_match'] is True and record['hooks_removed'] is True
        assert record['output']['token_ids'] == case['record']['record']['output']['token_ids']
        if mode == 'preflight':
            assert record['preflight_checks_passed'] is True
        trace = read_trace(output / trace_name)
        check_trace(trace, case['record'], record['arm'])
    assert set(receipt['record_hashes']) == expected_files
    for name, digest in receipt['record_hashes'].items():
        assert sha(output / name) == digest, f'Result changed: {name}'
    return receipt


def require_preflight_acceptance(output, auth):
    root = Path(output).parent.parent
    accepted = read(root / 'preflight-accepted.json')
    assert accepted['status'] == 'passed' and accepted['freeze_sha256'] == auth['freeze_sha256']
    assert set(accepted['workers']) == {f'{m}-shard-{s}' for m in MODELS for s in (0, 1)}
    for model in MODELS:
        for shard in (0, 1):
            key = f'{model}-shard-{shard}'
            run = root / 'preflight' / key
            assert accepted['workers'][key]['status'] == 'completed' and accepted['workers'][key]['exit_code'] == 0
            assert sha(run / 'receipt.json') == accepted['workers'][key]['receipt_sha256']
            verify_worker(run, 'preflight', model, shard)


def worker(args):
    assert args.execute and args.mode in ('preflight', 'survey')
    auth = validate_authorization(args.authorization)
    assert args.gpu == args.shard
    assert Path(args.output).resolve() == Path(auth['remote_output']) / args.mode / f'{args.model}-shard-{args.shard}'
    if args.mode == 'survey':
        require_preflight_acceptance(args.output, auth)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    cases = cases_for(args.mode, args.model, args.shard)
    receipt = {'status': 'running', 'mode': args.mode, 'model_id': args.model, 'shard': args.shard,
               'freeze_sha256': auth['freeze_sha256'], 'authorization_sha256': sha(args.authorization),
               'started_utc': utc(), 'completed_records': 0, 'expected_records': len(cases),
               'checks_passed': False, 'record_hashes': {}, 'asset_hashes': {}}
    write(output / 'receipt.json', receipt)
    started = time.monotonic()
    try:
        from trace_engine import TraceEngine
        old = load_module('trace_source_checks', ROOT.parent / 'layer-negative-dose-survey-toy-v1-2026-10-27/dose_survey.py')
        spec = next(m for m in read(ROOT / 'contract.json')['models'] if m['id'] == args.model)
        receipt['asset_verification'] = old.check_model_assets(spec)
        engine = TraceEngine(spec['remote_path'], spec, f'cuda:{args.gpu}')
        sources = [item for item in load_sources() if item['model'] == args.model]
        source_metadata = read(ROOT / 'source-metadata.json')
        for run in {item['provenance']['run'] for item in sources}:
            old.compatible_metadata(engine.metadata, source_metadata[run])
        baselines = sorted((item['record'] for item in sources if item['record']['layer'] is None), key=lambda row: row['question_id'])
        calibrations = engine.calibrate([row['context'] for row in baselines])
        assert calibrations == [row['calibration'] for row in baselines], 'Original prompt calibration changed'
        write(output / 'metadata.json', engine.metadata)
        write(output / 'calibrations.json', {row['question_id']: cal for row, cal in zip(baselines, calibrations)})
        receipt['asset_hashes'] = {name: sha(output / name) for name in ('metadata.json', 'calibrations.json')}
        baseline_hashes = None
        for index, case in enumerate(cases):
            item, override = case['record'], case['arm_override']
            row = item['record']
            plain = engine.collect(row, observe=False, arm_override=override) if args.mode == 'preflight' and index < 5 else None
            trace_name = f'traces/{index:04}-{case["name"]}.json.gz'
            result = engine.collect(row, output / trace_name, arm_override=override)
            result.update(status='completed', trace_id=item['trace_id'], source=item['provenance'],
                          question_id=row['question_id'], prompt=row['prompt'], context=row['context'],
                          condition_id=row['condition_id'], case_name=case['name'])
            result['output']['token_sha256'] = old.token_hash(result['output']['token_ids'])
            name = f'records/{index:04}-{case["name"]}.json'
            write(output / name, result)  # Preserve a failing replay as evidence before asserting.
            assert result['source_token_ids_match'] is True and result['hooks_removed'] is True
            old.check_output(result['output'])
            trace = read_trace(output / trace_name)
            check_trace(trace, item, result['arm'])
            if result['arm'] != 'baseline' and result['arm'][2] != 0:
                for field in ('layer', 'channel', 'dose', 'column_norm', 'clean_residual_scale', 'requested_offset', 'bf16_offset'):
                    assert result['intervention'][field] == row['intervention'][field], f'Injection identity changed: {field}'
            if args.mode == 'preflight':
                if plain is not None:
                    assert plain['source_token_ids_match'] and plain['hooks_removed']
                    assert plain['output']['token_ids'] == result['output']['token_ids']
                    assert plain['raw_logit_sha256_per_step'] == result['raw_logit_sha256_per_step'], 'Component observer changed logits'
                    result['without_component_observers'] = plain
                if index == 0:
                    baseline_hashes = result['raw_logit_sha256_per_step']
                if case['name'] in ('zero', 'restored'):
                    assert result['raw_logit_sha256_per_step'] == baseline_hashes, 'Zero/removal changed baseline logits'
                result['preflight_checks_passed'] = True
            result['checks_passed'] = True
            write(output / name, result)
            receipt['record_hashes'].update({name: sha(output / name), trace_name: sha(output / trace_name)})
            receipt['completed_records'] += 1
            receipt['elapsed_seconds'] = time.monotonic() - started
            receipt['updated_utc'] = utc()
            write(output / 'receipt.json', receipt)
            print(json.dumps({'case': case['name'], 'completed': receipt['completed_records'], 'expected': len(cases), 'seconds': result['total_seconds']}), flush=True)
        receipt['integrity'] = engine.verify_unchanged()
        receipt.update(status='completed', checks_passed=True, ended_utc=utc(), elapsed_seconds=time.monotonic() - started)
        write(output / 'receipt.json', receipt)
        verify_worker(output, args.mode, args.model, args.shard)
    except BaseException as error:
        receipt.update(status='failed', checks_passed=False, error=repr(error), traceback=traceback.format_exc(), ended_utc=utc(), elapsed_seconds=time.monotonic() - started)
        write(output / 'receipt.json', receipt)
        raise


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('prepare')
    task = sub.add_parser('worker')
    task.add_argument('--mode', choices=('preflight', 'survey'), required=True)
    task.add_argument('--model', choices=MODELS, required=True)
    task.add_argument('--shard', type=int, choices=(0, 1), required=True)
    task.add_argument('--gpu', type=int, choices=(0, 1), required=True)
    task.add_argument('--output', type=Path, required=True)
    task.add_argument('--authorization', type=Path, required=True)
    task.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if args.command == 'prepare':
        print(json.dumps(prepare(), ensure_ascii=False, indent=2))
    else:
        worker(args)


if __name__ == '__main__':
    main()
