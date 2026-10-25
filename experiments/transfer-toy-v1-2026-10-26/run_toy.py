"""Fixed source/target confirmation and diagnostic shards, without semantic inspection."""
import argparse
from pathlib import Path
import time
import traceback

from run_io import read, rows, write, immutable, sha, utc
from transfer_engine import TransferEngine, source_bundle

ROOT = Path(__file__).resolve().parent


def condition_order(kind, index):
    if kind == 'source':
        values = ['S_0', 'S_channel', 'S_vector']
        return values[index % 3:] + values[:index % 3]
    randoms = [f'random{r}_{arm}' for r in range(1, 4) for arm in ['D_raw', 'S_proj', 'D_match', 'S_recipe']]
    others = ['T_0', 'true_D_raw', 'true_S_proj', 'true_D_match', 'true_S_recipe', 'T_dense', 'T_sparse']
    return randoms[index % 12:] + randoms[:index % 12] + others[index % 7:] + others[:index % 7]


def prompt(engine, item):
    return engine.tokenizer.apply_chat_template([{'role':'user', 'content':item['prompt']}],
                  tokenize=False, add_generation_prompt=True, enable_thinking=False)


def calibration_path(root, split, index):
    return Path(root) / f'shard{index % 2}' / 'calibrations' / f'{split}-{index:03d}.json'


def run(args):
    out = Path(args.output) / f'shard{args.shard_index}'
    out.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    rec = {'status':'running', 'started_utc':utc(), 'kind':args.kind, 'arguments':vars(args),
           'completed_behavior':0, 'completed_diagnostic':0, 'completed_calibrations':0,
           'expected_behavior':96 if args.kind == 'source' else 608,
           'expected_diagnostic':0 if args.kind == 'source' else 608,
           'source_sha256':{p.name:sha(p) for p in [ROOT/'run_toy.py', ROOT/'transfer_engine.py']},
           'data_sha256':{name:sha(Path(args.data)/f'{name}.jsonl') for name in ['confirm','ability_diag']}}
    write(out/'receipt.json', rec)
    try:
        engine = TransferEngine(args.model, bundle=args.conditions)
        if args.kind == 'source':
            engine.conditions.update(source_bundle(engine)['conditions'])
        else:
            assert args.source_output and args.conditions
            rec['conditions_sha256'] = sha(args.conditions)
            for shard in (0, 1):
                prior = read(Path(args.source_output)/f'shard{shard}'/'receipt.json')
                assert prior['status'] == 'completed'
                assert prior['data_sha256'] == rec['data_sha256']
        rec['engine'] = engine.metadata
        for split, items in [('behavior',rows(Path(args.data)/'confirm.jsonl')),
                             ('ability',rows(Path(args.data)/'ability_diag.jsonl'))]:
            assert len(items) == 64
            for index in range(args.shard_index, len(items), 2):
                item = items[index]
                context = prompt(engine,item) if split == 'behavior' else item['context']
                scale_start = time.monotonic()
                cal = engine.calibrate([context])[0]
                cal['item_id'] = item['id']
                cal['calibration_seconds'] = time.monotonic()-scale_start
                if args.kind == 'target':
                    source_path = calibration_path(args.source_output,split,index)
                    source = read(source_path)
                    assert source['item_id'] == item['id']
                    cal['source_residual_scales'] = source['residual_scales']
                    cal['source_calibration_context_sha256'] = source['context_sha256']
                    cal['source_calibration_file_sha256'] = sha(source_path)
                write(calibration_path(args.output,split,index),cal)
                rec['completed_calibrations'] += 1
                if args.kind == 'source' and split == 'ability':
                    continue
                for condition in condition_order(args.kind,index):
                    begin = time.monotonic()
                    rec.update(current_split=split,current_item=item['id'],current_condition=condition,
                               elapsed_seconds=begin-started)
                    write(out/'receipt.json',rec)
                    if split == 'behavior':
                        result = engine.generate([context],condition,[cal],512,[])[0]
                    else:
                        details = engine.score([context]*len(item['continuations']),item['continuations'],
                                               condition,[cal]*len(item['continuations']))
                        result = {'choice_loglikelihoods':[d['loglikelihood'] for d in details],
                                  'choice_details':details}
                    record = {'status':'completed','item':item,'condition':condition,'context':context,
                              'prompt_format':'native_chat_thinking_false' if split == 'behavior' else 'frozen_benchmark_raw',
                              'calibration':cal,'output':result,'ended_utc':utc(),
                              'elapsed_seconds':time.monotonic()-begin}
                    target = out/'records'/split/f'{index:03d}-{condition}.jsonl'
                    immutable(target,record)
                    key = 'completed_behavior' if split == 'behavior' else 'completed_diagnostic'
                    rec[key] += 1
                    rec.setdefault('condition_seconds',{}).setdefault(split,{}).setdefault(condition,[]).append(record['elapsed_seconds'])
                    rec['elapsed_seconds']=time.monotonic()-started
                    write(out/'receipt.json',rec)
                    print({'split':split,'item':item['id'],'condition':condition,'completed':rec[key],
                           'seconds':record['elapsed_seconds'],'tokens':result.get('generated_token_count')},flush=True)
        assert rec['completed_behavior']==rec['expected_behavior']
        assert rec['completed_diagnostic']==rec['expected_diagnostic']
        rec.update(status='completed', **engine.verify_unchanged())
    except Exception as exc:
        rec.update(status='failed',error=str(exc),traceback=traceback.format_exc())
        raise
    finally:
        rec.update(ended_utc=utc(),elapsed_seconds=time.monotonic()-started)
        write(out/'receipt.json',rec)


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--model',required=True);p.add_argument('--kind',choices=['source','target'],required=True)
    p.add_argument('--data',required=True);p.add_argument('--output',required=True)
    p.add_argument('--conditions');p.add_argument('--source-output')
    p.add_argument('--shard-index',type=int,choices=[0,1],required=True)
    run(p.parse_args())
