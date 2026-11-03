"""Read-only live evidence audit; never imports torch or loads model weights."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import experiment as e


def command(argv):
    p = subprocess.run(argv, capture_output=True, text=True)
    return {'exit_code': p.returncode, 'stdout': p.stdout.strip(), 'stderr': p.stderr.strip()}


def collect():
    identity = e.check()
    now = datetime.now(timezone.utc)
    result = {'at': now.isoformat(), 'freeze': identity, 'runs': {}, 'errors': []}
    items = {r['id']: r for r in e.inputs()}
    for run_name in ('preflight-r01', 'survey-r01', 'weak-r01'):
        root = HERE / 'runs' / run_name
        if not root.exists():
            result['runs'][run_name] = {'status': 'not_started'}
            continue
        run = {}
        for name in ('execution.json', 'controller.json'):
            if (root / name).exists():
                run[name] = e.read(root / name)
                assert run[name]['freeze_sha256'] == identity['freeze_sha256']
        run['workers'] = []
        for gpu in (0, 1):
            worker = root / f'worker-{gpu}'
            if not (worker / 'receipt.json').exists():
                run['workers'].append({'gpu': gpu, 'status': 'not_started'})
                continue
            receipt = e.read(worker / 'receipt.json')
            summary = {k: v for k, v in receipt.items() if k not in ('record_hashes', 'asset_hashes')}
            assert receipt['freeze_sha256'] == identity['freeze_sha256']
            for name, sha in receipt['asset_hashes'].items():
                assert e.sha(worker / name) == sha
            summary['process'] = command(['ps', '-p', str(receipt['pid']), '-o', 'pid=,etimes=,stat=,args='])
            counts, bases, duration, tokens, generation_seconds, families = Counter(), Counter(), 0.0, 0, 0.0, defaultdict(lambda: {'records': 0, 'tokens': 0, 'seconds': 0.0})
            if receipt['record_hashes']:
                token_info = e.read(worker / 'tokens.json')['rows']
                references = e.read(worker / 'calibrations.json')
                specs = {c['id']: c for c in e.conditions(receipt['stage'])}
                for name, expected in receipt['record_hashes'].items():
                    assert e.sha(worker / name) == expected
                    row = e.read(worker / name)
                    item = items[row['item_id']]
                    e.check_record(row, item, specs[row['condition']['id']], token_info[item['id']], references[item['base_id']])
                    counts[item['panel']] += 1
                    bases[item['base_id']] += 1
                    duration += row['wall_seconds']
                    tokens += row['output']['generated_token_count']
                    generation_seconds += row['output']['batch_seconds']
                    family = families[item['family']]
                    family['records'] += 1
                    family['tokens'] += row['output']['generated_token_count']
                    family['seconds'] += row['wall_seconds']
            n_conditions = len(e.conditions(receipt['stage']))
            base_sizes = Counter(r['base_id'] for r in e.assigned(list(items.values()), gpu))
            summary['audit'] = {'verified_records': sum(counts.values()), 'by_panel': dict(counts),
                'completed_base_groups': sum(count == base_sizes[base] * n_conditions for base, count in bases.items()),
                'total_base_groups': len(base_sizes), 'generated_tokens': tokens,
                'sum_record_seconds': duration, 'sum_generation_seconds': generation_seconds,
                'by_family': dict(families), 'file_and_token_hashes': 'passed',
                'coverage_hash': e.digest(receipt['record_hashes'])}
            run['workers'].append(summary)
        for name in ('preflight-worker-0-exit.json', 'preflight-worker-1-exit.json', 'formal-worker-0-exit.json', 'formal-worker-1-exit.json'):
            if (root / name).exists():
                run[name] = e.read(root / name)
        if 'execution.json' in run:
            run['controller_process'] = command(['ps', '-p', str(run['execution.json']['pid']), '-o', 'pid=,etimes=,stat=,args='])
        result['runs'][run_name] = run
    result['gpu'] = command(['nvidia-smi', '--query-gpu=index,name,memory.used,memory.total,utilization.gpu', '--format=csv,noheader'])
    result['gpu_processes'] = command(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv,noheader'])
    result['disks'] = command(['df', '-Pk', str(e.REPO), '/data/models', '/tmp'])
    result['sizes_kib'] = {'experiment': command(['du', '-sk', str(HERE)]),
                           'outputs': command(['du', '-sk', str(HERE / 'runs')])}
    path = HERE / 'monitoring' / (now.strftime('%Y%m%dT%H%M%S%fZ') + '.json')
    e.write(path, result, immutable=True)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    collect()
