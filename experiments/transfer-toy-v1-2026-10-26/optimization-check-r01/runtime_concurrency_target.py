"""Independent unchanged-engine batch-one controls on one GPU; never edit the formal queue."""
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
    assert reference['status'] == 'completed' and reference['hooks_removed']
    started = time.monotonic()
    receipt = {'status': 'running', 'started_utc': utc(), 'pid': os.getpid(),
               'script_sha256': sha(__file__), 'probe_sha256': sha(ROOT/'runtime_worker.py'),
               'baseline_sha256': sha(args.baseline), 'worker_count': args.workers, 'workers': [],
               'load_context': 'Independent target model workers share one GPU; formal generation starts only after this check.',
               'scope': 'Bounded engineering check, not formal experiment evidence; actual forward batch remains one.'}
    processes = []
    write(path, receipt)
    try:
        for index in range(args.workers):
            output = args.output/f'worker{index}'
            command = [sys.executable, str(ROOT/'runtime_worker.py'), '--model', str(args.model),
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
        for index in range(args.workers):
            result = read(args.output/f'worker{index}/receipt.json')
            assert result['status'] == 'completed' and result['hooks_removed']
            assert len(result['cases']) == len(reference['cases'])
            for left, right in zip(reference['cases'], result['cases']):
                assert (left['id'], left['condition']) == (right['id'], right['condition'])
                assert left['calibration'] == right['calibration']
                assert left['stops'] == right['stops']
                for field in ('token_ids', 'end_reason', 'input_token_sha256', 'raw_text', 'answer_text'):
                    assert left['output'][field] == right['output'][field], (index, left['id'], field)
            assert result['likelihoods'] == reference['likelihoods']
            tokens += result['generated_tokens']
        reference_tokens = reference['generated_tokens']
        receipt.update(status='completed', all_cross_process_outputs_exact=True,
                       generated_tokens=tokens, aggregate_tokens_per_wall_second=tokens/receipt['wall_seconds'],
                       one_probe_tokens_per_wall_second=reference_tokens/reference['wall_seconds'],
                       observed_end_to_end_throughput_ratio=(tokens/receipt['wall_seconds'])/(reference_tokens/reference['wall_seconds']),
                       limits='Fixed synthetic long-context, task-stop and likelihood controls; includes model loading. Single and concurrent target-model probes run sequentially before formal target generation. This is not a guaranteed full-run speedup.')
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
    parser.add_argument('--workers',type=int,choices=(2,3),required=True)
    for name in ('model', 'bundle', 'baseline', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    run(parser.parse_args())
