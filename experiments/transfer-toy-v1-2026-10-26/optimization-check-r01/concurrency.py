"""Two independent batch-one probes on one GPU; never edit the formal queue."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from run_io import read, write, utc, sha


def run(args):
    args.output.mkdir(parents=True, exist_ok=False)
    path = args.output / 'receipt.json'
    reference = read(args.baseline)
    assert reference['status'] == 'completed' and reference['all_exact_matches']
    started = time.monotonic()
    receipt = {'status': 'running', 'started_utc': utc(), 'pid': os.getpid(),
               'script_sha256': sha(__file__), 'probe_sha256': sha(ROOT/'probe.py'),
               'baseline_sha256': sha(args.baseline), 'workers': [],
               'load_context': 'Two 9B probes share GPU0 with the existing 4B source worker.',
               'scope': 'Bounded engineering check, not formal experiment evidence; actual forward batch remains one.'}
    processes = []
    write(path, receipt)
    try:
        for index in range(2):
            output = args.output/f'worker{index}'
            command = [sys.executable, str(ROOT/'probe.py'), '--model', str(args.model),
                       '--bundle', str(args.bundle), '--output', str(output)]
            with (args.output/f'worker{index}.log').open('x') as stream:
                child = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT)
            processes.append(child)
            receipt['workers'].append({'pid': child.pid, 'command': command, 'output': str(output)})
            write(path, receipt)
        for child in processes:
            assert child.wait(timeout=600) == 0, 'Probe failed; preserve child receipt and log'
        receipt['wall_seconds'] = time.monotonic() - started
        tokens = 0
        for index in range(2):
            result = read(args.output/f'worker{index}/receipt.json')
            assert result['status'] == 'completed' and result['all_exact_matches']
            assert len(result['cases']) == len(reference['cases'])
            for left, right in zip(reference['cases'], result['cases']):
                assert (left['id'], left['condition']) == (right['id'], right['condition'])
                for variant in ('original', 'omit_empty_stop'):
                    for field in ('token_ids', 'end_reason', 'input_token_sha256', 'raw_text_sha256', 'answer_text_sha256'):
                        assert left['outputs'][variant][field] == right['outputs'][variant][field], (index, left['id'], variant, field)
            tokens += sum(row['generated_tokens'] for row in result['totals'].values())
        reference_tokens = sum(row['generated_tokens'] for row in reference['totals'].values())
        receipt.update(status='completed', all_cross_process_outputs_exact=True,
                       generated_tokens=tokens, aggregate_tokens_per_wall_second=tokens/receipt['wall_seconds'],
                       one_probe_tokens_per_wall_second=reference_tokens/reference['wall_seconds'],
                       observed_end_to_end_throughput_ratio=(tokens/receipt['wall_seconds'])/(reference_tokens/reference['wall_seconds']),
                       limits='Short synthetic contexts; includes model loading. Single and concurrent probes were run sequentially with a continuing 4B background worker. This is not a guaranteed full-run speedup.')
    except Exception as error:
        receipt.update(status='failed', error=str(error))
        for child in processes:
            if child.poll() is None:
                child.terminate()
        raise
    finally:
        receipt['ended_utc'] = utc()
        write(path, receipt)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('model', 'bundle', 'baseline', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    run(parser.parse_args())
