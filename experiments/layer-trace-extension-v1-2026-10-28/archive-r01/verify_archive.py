"""Verify downloaded traces on CPU using the unchanged experiment validators."""
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time

REPO = Path(__file__).resolve().parents[3]
EXPERIMENTS = (
    ('early-layer-mechanism-v1-2026-10-28', 2152),
    ('layer-trace-extension-v1-2026-10-28', 4560),
    ('llama31-early-layer-trace-v1-2026-10-28', 920),
)


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(root, filename):
    spec = importlib.util.spec_from_file_location('archive_' + root.name, root / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_worker(job):
    experiment, relative = job
    root = REPO / 'experiments' / experiment
    output = root / 'archive-r01' / 'execution-r01' / relative
    receipt = read(output / 'receipt.json')
    mode, model, shard = (receipt[k] for k in ('mode', 'model_id', 'shard'))
    if experiment.startswith('layer-trace-extension'):
        runner = load(root, 'supplement.py').adapted_runner(relative.split('/')[0])
    elif experiment.startswith('llama31-'):
        runner = load(root, 'trace_run.py').adapted_runner()
    else:
        runner = load(root, 'trace_run.py')
    # This only reads JSON/gzip and checks stored hashes/numbers; no model engine is imported.
    runner.verify_worker(output, mode, model, shard)
    actual = {str(path.relative_to(output)) for folder in ('records', 'traces')
              for path in (output / folder).iterdir() if path.is_file()}
    assert actual == set(receipt['record_hashes']), 'Unexpected or missing record/trace files'
    assert receipt['authorization_sha256'] == sha(root / 'readiness/queue-authorization-r01.json')
    assert output.with_suffix('.exit').read_text().strip() == '0'
    cases = runner.cases_for(mode, model, shard)
    files = {str(Path(relative) / name): digest for name, digest in
             (receipt['asset_hashes'] | receipt['record_hashes']).items()}
    files[str(Path(relative) / 'receipt.json')] = sha(output / 'receipt.json')
    files[str(Path(relative).with_suffix('.exit'))] = sha(output.with_suffix('.exit'))
    return {'experiment': experiment, 'worker': relative, 'mode': mode, 'model': model,
            'shard': shard, 'records': receipt['completed_records'],
            'status': 'verified', 'checks': 'frozen verify_worker: SHA-256, source token/provenance, '
            'all layer/component/position coverage, finite/undefined numeric semantics, same-prefix '
            'control, zero/control branch, pre-injection prompt, hook cleanup, stored weight hashes',
            'receipt_sha256': files[str(Path(relative) / 'receipt.json')],
            'ids': [case['record']['trace_id'] for case in cases], 'files': files}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--experiment', choices=[name for name, _ in EXPERIMENTS])
    args = parser.parse_args()
    selected = [(name, count) for name, count in EXPERIMENTS if not args.experiment or name == args.experiment]
    started = time.monotonic()
    jobs, states, source_ids = [], {}, {}
    for experiment, expected in selected:
        root = REPO / 'experiments' / experiment
        run = root / 'archive-r01/execution-r01'
        runner = load(root, 'supplement.py' if experiment.startswith('layer-trace-extension') else 'trace_run.py')
        runner.validate_authorization(root / 'readiness/queue-authorization-r01.json')
        state = read(run / 'queue-state.json')
        assert state['status'] == 'completed'
        assert state['expected_records'] == state['completed_records'] == expected
        assert state['freeze_sha256'] == sha(root / 'freeze.json')
        assert state['authorization_sha256'] == sha(root / 'readiness/queue-authorization-r01.json')
        states[experiment] = state
        rows = [json.loads(line) for line in (root / 'sources.jsonl').read_text().splitlines()]
        source_ids[experiment] = [row['trace_id'] for row in rows if 'stage' not in row or row['stage']]
        assert len(source_ids[experiment]) == len(set(source_ids[experiment])) == expected
        for receipt in sorted(run.rglob('receipt.json')):
            jobs.append((experiment, str(receipt.parent.relative_to(run))))
    assert len(jobs) == sum(6 if name.startswith('layer-trace-extension') else 4 if name.startswith('llama31-') else 12
                            for name, _ in selected)
    results = []
    with ProcessPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(verify_worker, job): job for job in jobs}
        for future in as_completed(futures):
            item = future.result()
            results.append(item)
            print(json.dumps({k: item[k] for k in ('experiment', 'worker', 'records', 'status')}), flush=True)
    all_ids, counts = [], Counter()
    for experiment, expected in selected:
        root = REPO / 'experiments' / experiment
        run = root / 'archive-r01/execution-r01'
        workers = sorted((item for item in results if item['experiment'] == experiment), key=lambda item: item['worker'])
        ids = [trace_id for item in workers if item['mode'] == 'survey' for trace_id in item['ids']]
        assert len(ids) == len(set(ids)) == expected and set(ids) == set(source_ids[experiment])
        all_ids.extend(ids)
        for item in workers:
            state = states[experiment]['stages']
            parts = item['worker'].split('/')
            entry = state[parts[0]][parts[-1]]
            assert entry['status'] == 'completed' and entry['exit_code'] == 0
            assert entry['receipt_sha256'] == item['receipt_sha256']
            if item['mode'] == 'survey':
                counts[item['model']] += item['records']
        file_hashes = {}
        for item in workers:
            file_hashes.update(item.pop('files'))
        # Include every other downloaded file, without rehashing the verified large traces.
        for path in run.rglob('*'):
            if path.is_file() and str(path.relative_to(run)) not in file_hashes:
                file_hashes[str(path.relative_to(run))] = sha(path)
        manifest = {'status': 'verified', 'verified_utc': datetime.now(timezone.utc).isoformat(),
                    'remote_source': 'gqa-h20:/workspace/acupuncture/experiments/' + experiment + '/execution-r01',
                    'local_root': str(run.relative_to(REPO)), 'formal_records': expected,
                    'preflight_records': sum(w['records'] for w in workers if w['mode'] == 'preflight'),
                    'new_inference': False, 'source_ids_exact_match': True,
                    'freeze_sha256': sha(root / 'freeze.json'),
                    'authorization_sha256': sha(root / 'readiness/queue-authorization-r01.json'),
                    'sources_sha256': sha(root / 'sources.jsonl'),
                    'formal_trace_ids': sorted(ids),
                    'workers': [{k: v for k, v in w.items() if k != 'ids'} for w in workers],
                    'downloaded_files': len(file_hashes), 'downloaded_bytes': sum(p.stat().st_size for p in run.rglob('*') if p.is_file()),
                    'files_sha256': dict(sorted(file_hashes.items()))}
        (root / 'archive-r01/verification.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    manifests = [REPO / 'experiments' / name / 'archive-r01/verification.json' for name, _ in EXPERIMENTS]
    if not all(path.exists() for path in manifests):
        print(json.dumps({'status': 'batch_verified', 'experiments': [name for name, _ in selected],
                          'seconds': time.monotonic() - started}), flush=True)
        return
    all_ids, counts = [], Counter()
    for (name, expected), path in zip(EXPERIMENTS, manifests):
        manifest = read(path)
        root = path.parent.parent
        assert manifest['status'] == 'verified' and manifest['formal_records'] == expected
        assert manifest['sources_sha256'] == sha(root / 'sources.jsonl')
        assert manifest['freeze_sha256'] == sha(root / 'freeze.json')
        all_ids.extend(manifest['formal_trace_ids'])
        for worker in manifest['workers']:
            if worker['mode'] == 'survey':
                counts[worker['model']] += worker['records']
    assert len(all_ids) == len(set(all_ids)) == 7632
    assert counts == {'2b': 920, '4b': 4872, '9b': 920, 'llama31-8b-instruct': 920}
    summary = {'status': 'verified', 'verified_utc': datetime.now(timezone.utc).isoformat(),
               'formal_records': 7632, 'formal_unique_records': 7632, 'preflight_records': 56, 'models': dict(counts),
               'missing': 0, 'extra': 0, 'duplicates': 0, 'new_inference': False,
               'final_invocation_seconds': time.monotonic() - started,
               'manifests': [f'experiments/{name}/archive-r01/verification.json' for name, _ in EXPERIMENTS]}
    Path(__file__).with_name('combined-verification.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
