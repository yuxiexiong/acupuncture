"""Unchanged-engine validation on long text, task stops, and likelihoods."""
import argparse
import os
from pathlib import Path
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from run_io import read, write, sha, utc
from run_benchmark import frozen_panel
from transfer_engine import TransferEngine, token_hash


def run(args):
    args.output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    receipt = {'status': 'running', 'pid': os.getpid(), 'started_utc': utc(), 'cases': [],
               'probe_sha256': sha(__file__), 'freeze_sha256': sha(ROOT/'freeze.json'),
               'bundle_sha256': sha(args.bundle), 'device': os.environ.get('CUDA_VISIBLE_DEVICES'),
               'scope': 'Engineering controls only; unchanged frozen engine, batch one; 7 generation calls at most 1920 tokens.'}
    path = args.output/'receipt.json'
    write(path, receipt)
    try:
        for name, digest in read(ROOT/'freeze.json')['files'].items():
            assert sha(ROOT/name) == digest
        _, _, panel = frozen_panel()
        engine = TransferEngine(args.model, bundle=args.bundle)
        receipt['engine'] = engine.metadata
        prose = 'A public library records book titles, shelf locations, and return dates. Its catalogue helps readers locate material and staff maintain accurate records. '
        long_prompt = prose*40 + '\nExplain in detail how a library can keep this catalogue accurate.'
        rendered = engine.tokenizer.apply_chat_template([{'role':'user','content':long_prompt}], tokenize=False, add_generation_prompt=True, enable_thinking=False)
        math_prompt = 'Question: A library has 4 shelves with 12 books on each. It lends out 9 books. How many books remain?\nAnswer:'
        code_prompt = 'def add_two_numbers(a, b):\n    """Return the sum of the two numeric arguments."""\n'
        specs = [('long', rendered, 512, [], ('T_0','true_S_recipe')),
                 ('math', math_prompt, 192, panel['gsm8k'][0]['gen_kwargs']['until'], ('T_0','true_S_recipe')),
                 ('code', code_prompt, 192, panel['humaneval'][0]['gen_kwargs']['until'], ('T_0','true_S_recipe')),
                 ('vector', rendered, 128, [], ('true_D_match',))]
        for name, context, budget, stops, arms in specs:
            cal = engine.calibrate([context])[0]
            for arm in arms:
                before = time.monotonic()
                result = engine.generate([context], arm, [cal], budget, stops)[0]
                receipt['cases'].append({'id':name+'-'+arm,'condition':arm,'calibration':cal,
                    'stops':stops,'output':result,'seconds':time.monotonic()-before})
                write(path,receipt)
        context = 'Question: What is 7 plus 5?\nAnswer:'
        choices = [' 10', ' 11', ' 12', ' 13']
        cal = engine.calibrate([context])[0]
        receipt['likelihoods'] = {arm:engine.score([context]*4,choices,arm,[cal]*4) for arm in ('T_0','true_S_recipe')}
        receipt.update(engine.verify_unchanged())
        receipt['generated_tokens'] = sum(x['output']['generated_token_count'] for x in receipt['cases'])
        assert len(receipt['cases']) == 7 and receipt['generated_tokens'] <= 1920
        for name, digest in read(ROOT/'freeze.json')['files'].items():
            assert sha(ROOT/name) == digest
        receipt.update(status='completed',peak_cuda_memory_allocated_bytes=engine.torch.cuda.max_memory_allocated())
    except Exception as exc:
        receipt.update(status='failed',error=str(exc),traceback=traceback.format_exc())
        raise
    finally:
        receipt.update(ended_utc=utc(),wall_seconds=time.monotonic()-started)
        write(path,receipt)


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    for name in ('model','bundle','output'):p.add_argument('--'+name,type=Path,required=True)
    run(p.parse_args())
