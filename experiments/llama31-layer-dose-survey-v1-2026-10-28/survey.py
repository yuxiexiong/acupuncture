"""Fresh Llama signed survey, retaining the Qwen scientific settings and raw evidence."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import struct
import time
import traceback

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
OLD = HERE.parent / 'layer-survey-toy-v1-2026-10-27'
spec = importlib.util.spec_from_file_location('llama_survey_io', HERE.parent/'transfer-toy-v1-2026-10-26/run_io.py')
io = importlib.util.module_from_spec(spec)
spec.loader.exec_module(io)
MODEL = 'llama31-8b-instruct'
DOSES = (-.0625, .0625, -.125, .125, -.25, .25, -.5, .5, -1., 1.)
COMPARISON_DOSES = tuple(sorted((*DOSES, 0.)))
STOP_IDS = (128001, 128008, 128009)


def token_hash(tokens):
    return hashlib.sha256(json.dumps(tokens, separators=(',', ':')).encode()).hexdigest()


def bf16_round(value):
    bits = struct.unpack('I', struct.pack('f', value))[0]
    return struct.unpack('f', struct.pack('I', (bits + 0x7fff + ((bits >> 16) & 1)) & 0xffff0000))[0]


def dose_id(dose):
    assert dose in DOSES
    return 'D' + str(float(dose)).replace('.', 'p')


def load_design():
    contract, questions, samples = (io.read(HERE/name) for name in ('contract.json', 'questions.json', 'samples.json'))
    assert contract['experiment'] == HERE.name
    model, = contract['models']
    assert (model['id'], model['layers'], model['hidden_size'], model['intermediate_size']) == (MODEL, 32, 4096, 14336)
    assert model['repo'] == 'meta-llama/Llama-3.1-8B-Instruct'
    assert model['revision'] == '0e9e39f249a16976918f6564b8830bc894c89659'
    assert tuple(contract['nonzero_doses']) == DOSES and tuple(contract['comparison_doses']) == COMPARISON_DOSES
    assert io.sha(HERE/'questions.json') == io.sha(OLD/'questions.json')
    old = io.read(OLD/'contract.json')
    assert contract['instruction'] == old['instruction'] and contract['channels_per_layer'] == 10
    for k, v in old['generation'].items():
        if k != 'enable_thinking':
            assert contract['generation'][k] == v
    assert contract['generation']['enable_thinking'] == 'not_applicable'
    assert contract['generation']['native_chat_template_date_string'] == '26 Oct 2026'
    assert contract['predecessor'] == 'experiments/layer-negative-dose-survey-toy-v1-2026-10-27/survey-r01'
    assert (REPO/contract['predecessor']/'controller.json').is_file(), 'Predecessor path must resolve before GPU dispatch'
    assert [q['id'] for q in questions] == [f'Q{i:02}' for i in range(1, 9)]
    assert set(samples) == {MODEL}
    expected = []
    for layer in range(32):
        channels = sorted(random.Random(f'acupuncture-layer-survey-v1:{MODEL}:{layer}').sample(range(14336), 10))
        expected += [dict(id=f'L{layer:02}-N{c:06}', layer=layer, channel=c) for c in channels]
    assert samples[MODEL] == expected
    assert contract['formal'] == dict(selected_points=320, nonzero_conditions=3200, modified_answers=25600,
        baseline_answers=8, total_answers=25608, comparison_groups=2560, columns_per_group=11, display_cells=28160)
    assert contract['preflight']['total_answers'] == 88
    return contract, questions, samples


def schedule(mode, model, questions, samples, shard, shards=2):
    assert mode in ('preflight', 'survey') and shards == 2 and shard in (0, 1)
    points = samples[shard::2]
    jobs = [('baseline', None, q, None) for q in questions] if mode == 'preflight' or shard == 0 else []
    if mode == 'survey':
        jobs += [(f'{c["id"]}-{dose_id(d)}', c, q, d) for c in points for q in questions for d in DOSES]
        assert len(jobs) == 12800 + (8 if shard == 0 else 0)
    else:
        for c, q in zip((points[0], points[len(points)//2], points[-1]), (questions[0], questions[3], questions[7])):
            jobs += [(f'zero-{c["id"]}', c, q, 0.)]
            jobs += [(f'{c["id"]}-{dose_id(d)}', c, q, d) for d in DOSES]
            jobs += [(f'restored-{c["id"]}', c, q, None)]
        assert len(jobs) == 44
    return jobs


def make_specs(mode, model_id, shard, shards=2):
    contract, questions, samples = load_design()
    assert model_id == MODEL
    return schedule(mode, contract['models'][0], questions, samples[MODEL], shard, shards)


def freeze():
    load_design()
    files = set(HERE.glob('*.py')) | {HERE/n for n in ('contract.json','questions.json','samples.json','asset_manifest.json','PROTOCOL.zh-CN.md')}
    dependencies = ['layer-survey-toy-v1-2026-10-27/survey_engine.py',
        'layer-survey-toy-v1-2026-10-27/contract.json', 'layer-survey-toy-v1-2026-10-27/questions.json',
        'cross-family-transfer-toy-v1-2026-10-26/engine.py', 'transfer-toy-v1-2026-10-26/transfer_engine.py',
        'transfer-toy-v1-2026-10-26/run_io.py', 'capability-damage-v2-2026-10-26/model_engine.py']
    files |= {HERE.parent/name for name in dependencies}
    io.immutable(HERE/'freeze.json', dict(experiment=HERE.name, created_utc=io.utc(),
        files={str(p.relative_to(REPO)):io.sha(p) for p in sorted(files)}))


def check_freeze():
    frozen = io.read(HERE/'freeze.json')
    assert frozen['experiment'] == HERE.name
    for name, digest in frozen['files'].items():
        assert io.sha(REPO/name) == digest, f'Frozen input changed: {name}'
    return io.sha(HERE/'freeze.json')


def check_authorization(path, mode, model_id, gpu, execute):
    assert execute, 'Explicit --execute required before loading a model'
    identity, auth = check_freeze(), io.read(path)
    assert auth['experiment'] == HERE.name and auth['freeze_sha256'] == identity
    assert auth['status'] == 'authorized' and auth['purpose'] == mode
    assert model_id == MODEL and auth['models'] == [MODEL] and gpu in auth['gpus'] == [0, 1]
    assert auth['user_instruction'] and auth['recorded_utc']
    assert auth['maximum_workers'] == 2 and auth['maximum_new_tokens_per_record'] == 128
    assert auth['maximum_generations'] == (88 if mode == 'preflight' else 25608)
    assert auth['maximum_generated_tokens'] == auth['maximum_generations'] * 128
    if mode == 'survey':
        assert auth['formal_launch_confirmed'] is True
        assert len(auth['preflight_runs']) == 2
        runs = [REPO/p for p in auth['preflight_runs']]
        check_pair(runs, 'preflight')
        parent = runs[0].parent
        assert all(p.parent == parent for p in runs)
        controller = io.read(parent/'controller.json')
        assert io.sha(parent/'controller.json') == auth['preflight_controller_sha256']
        assert controller['status'] == 'completed' and controller['mode'] == 'preflight'
        assert controller['worker_exit_codes'] == {p.name:0 for p in runs}
        for p in runs:
            assert (parent/f'{p.name}.exit').read_text().strip() == '0'
            assert io.sha(parent/f'{p.name}.exit') == auth['preflight_exit_sha256'][p.name]
    else:
        assert auth['formal_launch_confirmed'] is False
    return identity, auth


def check_model_assets(model):
    expected = io.read(HERE/'asset_manifest.json')[MODEL]
    assert expected['revision'] == model['revision']
    started = time.monotonic()
    for name, item in expected['files'].items():
        p = Path(model['remote_path'])/name
        assert p.stat().st_size == item['bytes'] and io.sha(p) == item['sha256'], f'Model asset changed: {name}'
    return dict(status='verified', manifest_sha256=io.sha(HERE/'asset_manifest.json'), files=len(expected['files']), seconds=time.monotonic()-started)


def kind_for(condition):
    return 'baseline' if condition == 'baseline' else 'zero' if condition.startswith('zero-') else 'restored' if condition.startswith('restored-') else 'dose'


def check_record(row, job, calibrations):
    condition, c, q, dose = job
    assert row['status'] == 'completed' and row['model_id'] == MODEL
    assert row['condition_id'] == condition and row['kind'] == kind_for(condition)
    assert row['question_id'] == q['id'] and row['prompt'] == q['prompt']
    assert row['point_id'] == (c['id'] if c else None)
    assert row['layer'] == (c['layer'] if c else None) and row['channel'] == (c['channel'] if c else None)
    assert row['dose'] == (0. if dose is None else dose)
    cal, out = row['calibration'], row['output']
    assert cal == calibrations[q['id']]
    assert cal['context_sha256'] == hashlib.sha256(row['context'].encode()).hexdigest()
    assert out['input_token_sha256'] == cal['input_token_sha256']
    tokens = out['token_ids']
    assert all(type(t) is int and 0 <= t < 128256 for t in tokens)
    assert 0 < len(tokens) <= 128 and out['generated_token_count'] == len(tokens)
    assert out['token_sha256'] == token_hash(tokens)
    assert out['batch_size'] == 1 and out['max_new_tokens'] == 128 and out['returned_padding_count'] == 0
    assert out['end_reason'] in ('eos_token', 'length_limit')
    assert (out['end_reason'] == 'eos_token') == (tokens[-1] in STOP_IDS)
    assert not any(t in STOP_IDS for t in tokens[:-1])
    assert out['end_reason'] != 'length_limit' or len(tokens) == 128
    hook = row['intervention']
    if c is not None and dose is not None:
        assert (hook['layer'], hook['channel'], hook['dose']) == (c['layer'], c['channel'], dose)
        norm, scale = hook['column_norm'], cal['residual_scales'][str(c['layer'])]
        assert math.isfinite(norm) and norm > 0 and math.isfinite(scale) and scale > 0
        assert hook['clean_residual_scale'] == scale
        assert hook['requested_offset'] == dose * scale / norm
        assert hook['bf16_offset'] == bf16_round(hook['requested_offset'])
        assert hook['calls'] == len(tokens) and hook['positions'] == cal['input_token_count'] + len(tokens) - 1
        assert hook['prefill_target_values_checked'] is True
    else:
        assert hook is None


def verify(run):
    run = Path(run)
    receipt = io.read(run/'receipt.json')
    assert receipt['status'] == 'completed' and receipt['checks_passed'] is True
    assert receipt['experiment'] == HERE.name and receipt['freeze_sha256'] == check_freeze()
    jobs = make_specs(receipt['mode'], receipt['model_id'], receipt['shard'], receipt['shards'])
    expected = {f'records/{c}__{q["id"]}.json':(c,p,q,d) for c,p,q,d in jobs}
    assert set(expected) == set(receipt['record_hashes']) == {str(p.relative_to(run)) for p in (run/'records').glob('*.json')}
    assert receipt['expected_records'] == receipt['completed_records'] == len(expected)
    assert set(receipt['expected_record_ids']) == {Path(n).stem for n in expected}
    assert len(receipt['expected_record_ids']) == len(expected)
    assert set(receipt['asset_hashes']) == {'metadata.json','calibrations.json','sampled_columns.pt'}
    for name, h in receipt['asset_hashes'].items():
        assert io.sha(run/name) == h
    meta, cals = io.read(run/'metadata.json'), io.read(run/'calibrations.json')
    model = load_design()[0]['models'][0]
    assert meta['model_id'] == MODEL and meta['revision'] == model['revision']
    assert meta['layers'] == list(range(32)) and meta['hidden_size'] == 4096 and meta['intermediate_size'] == 14336
    assert meta['dtype'] == 'bfloat16' and meta['batch_size'] == 1 and meta['attention_backend'] == 'eager'
    assert meta['chat_template_applied'] is True and meta['enable_thinking'] is None
    assert meta['chat_template_date_string'] == '26 Oct 2026'
    assert meta['effective_generation']['do_sample'] is False and meta['effective_generation']['max_new_tokens'] == 128
    assert meta['effective_generation']['use_cache'] is True and meta['fresh_cache_each_call'] is True
    assert sorted(map(int, meta['effective_stop_tokens'])) == list(STOP_IDS)
    assert receipt['integrity']['hooks_removed'] is True
    assert receipt['integrity']['target_weight_sha256_after'] == meta['target_weight_sha256_before']
    assert receipt['model_asset_verification']['status'] == 'verified'
    assert receipt['model_asset_verification']['manifest_sha256'] == io.sha(HERE/'asset_manifest.json')
    baselines = {}
    for name, job in expected.items():
        assert io.sha(run/name) == receipt['record_hashes'][name]
        row = io.read(run/name)
        check_record(row, job, cals)
        if row['kind'] == 'baseline':
            baselines[row['question_id']] = row['output']
        elif row['kind'] in ('zero','restored'):
            for field in ('token_ids','raw_text','answer_text','end_reason'):
                assert row['output'][field] == baselines[row['question_id']][field]
    if receipt['mode'] == 'survey':
        pre = REPO/receipt['preflight_reference']['run']
        assert io.sha(pre/'receipt.json') == receipt['preflight_reference']['receipt_sha256']
        assert cals == io.read(pre/'calibrations.json')
        assert meta == io.read(pre/'metadata.json')
        for qid, output in baselines.items():
            old = io.read(pre/f'records/baseline__{qid}.json')['output']
            assert all(output[k] == old[k] for k in ('token_ids','raw_text','answer_text','end_reason'))
    return receipt


def check_pair(runs, mode):
    assert len(runs) == 2
    receipts = [verify(p) for p in runs]
    assert {r['shard'] for r in receipts} == {0,1} and all(r['mode'] == mode for r in receipts)
    assert io.read(Path(runs[0])/'calibrations.json') == io.read(Path(runs[1])/'calibrations.json')
    metas = [io.read(Path(p)/'metadata.json') for p in runs]
    assert {k:v for k,v in metas[0].items() if k!='device'} == {k:v for k,v in metas[1].items() if k!='device'}
    if mode == 'preflight':
        for qid in [f'Q{i:02}' for i in range(1,9)]:
            outputs = [io.read(Path(p)/f'records/baseline__{qid}.json')['output'] for p in runs]
            assert all(outputs[0][k] == outputs[1][k] for k in ('token_ids','raw_text','answer_text','end_reason'))
    return receipts


def run(args):
    identity, auth = check_authorization(args.authorization, args.mode, args.model, args.gpu, args.execute)
    contract, questions, samples = load_design()
    model = contract['models'][0]
    jobs = make_specs(args.mode, args.model, args.shard)
    destination = Path(args.output)
    assert not destination.exists(), 'Never overwrite or resume partial evidence'
    import fcntl
    import subprocess
    lock = open(f'/tmp/acupuncture-layer-survey-gpu{args.gpu}.lock', 'w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    used = subprocess.check_output(['nvidia-smi',f'--id={args.gpu}','--query-gpu=memory.used','--format=csv,noheader,nounits'],text=True)
    assert int(used.strip()) < 256, 'GPU occupied; do not disturb its owner'
    apps = subprocess.check_output(['nvidia-smi',f'--id={args.gpu}','--query-compute-apps=pid','--format=csv,noheader,nounits'],text=True)
    assert not apps.strip(), 'GPU has an active compute process; do not disturb its owner'
    destination.mkdir(parents=True)
    started = time.monotonic()
    receipt = dict(status='running',experiment=HERE.name,mode=args.mode,model_id=MODEL,shard=args.shard,shards=2,
        freeze_sha256=identity,authorization=auth,gpu=args.gpu,started_utc=io.utc(),expected_records=len(jobs),
        expected_record_ids=[f'{c}__{q["id"]}' for c,_,q,_ in jobs],record_hashes={},asset_hashes={})
    io.write(destination/'receipt.json',receipt)
    try:
        receipt['model_asset_verification'] = check_model_assets(model)
        from engine import Engine
        engine = Engine(model['remote_path'],model,f'cuda:{args.gpu}')
        receipt['load_seconds'] = time.monotonic()-started
        io.immutable(destination/'metadata.json',engine.metadata)
        contexts = {q['id']:engine.tokenizer.apply_chat_template(
            [{'role':'user','content':contract['instruction']+'\n\n'+q['prompt']}],tokenize=False,add_generation_prompt=True) for q in questions}
        for text in contexts.values():
            tokens = engine.tokenizer.encode(text,add_special_tokens=False)
            assert tokens[0] == engine.tokenizer.bos_token_id and tokens.count(engine.tokenizer.bos_token_id) == 1
        cal_started = time.monotonic()
        calibrations = dict(zip(contexts,engine.calibrate(list(contexts.values()))))
        receipt['calibration_seconds'] = time.monotonic()-cal_started
        io.immutable(destination/'calibrations.json',calibrations)
        if args.mode == 'survey':
            pre = next(REPO/p for p in auth['preflight_runs'] if io.read(REPO/p/'receipt.json')['shard'] == args.shard)
            assert calibrations == io.read(pre/'calibrations.json') and engine.metadata == io.read(pre/'metadata.json')
            receipt['preflight_reference'] = dict(run=str(pre.relative_to(REPO)),receipt_sha256=io.sha(pre/'receipt.json'))
        directions = {c['id']:engine.modules[c['layer']].weight[:,c['channel']].detach().float().cpu() for c in samples[MODEL]}
        engine.torch.save(directions,destination/'sampled_columns.pt')
        receipt['asset_hashes'] = {name:io.sha(destination/name) for name in ('metadata.json','calibrations.json','sampled_columns.pt')}
        baseline_outputs = {}
        for job in jobs:
            condition,c,q,dose = job
            qid = q['id']
            arm = (c['layer'],c['channel'],dose) if c is not None and dose is not None else 'baseline'
            output = engine.generate([contexts[qid]],arm,[calibrations[qid]],128,[])[0]
            output['token_sha256'] = token_hash(output['token_ids'])
            row = dict(status='completed',model_id=MODEL,condition_id=condition,point_id=c['id'] if c else None,
                kind=kind_for(condition),layer=c['layer'] if c else None,channel=c['channel'] if c else None,
                dose=0. if dose is None else dose,question_id=qid,prompt=q['prompt'],context=contexts[qid],
                calibration=calibrations[qid],intervention=engine.last_hook,output=output,ended_utc=io.utc())
            name = f'records/{condition}__{qid}.json'
            io.immutable(destination/name,row)
            receipt['record_hashes'][name] = io.sha(destination/name)
            check_record(row,job,calibrations)
            if row['kind'] == 'baseline':
                baseline_outputs[qid] = output
                if args.mode == 'survey':
                    reference = io.read(pre/f'records/baseline__{qid}.json')['output']
                    assert all(output[k] == reference[k] for k in ('token_ids','raw_text','answer_text','end_reason'))
            elif row['kind'] in ('zero','restored'):
                assert all(output[k] == baseline_outputs[qid][k] for k in ('token_ids','raw_text','answer_text','end_reason'))
            assert all(not m._forward_pre_hooks for m in engine.modules.values())
            receipt['completed_records'] = len(receipt['record_hashes'])
            io.write(destination/'receipt.json',receipt)
            print(json.dumps(dict(completed=receipt['completed_records'],total=len(jobs),tokens=len(output['token_ids']),seconds=output['batch_seconds'])),flush=True)
        receipt['integrity'] = engine.verify_unchanged()
        receipt.update(status='completed',checks_passed=True,ended_utc=io.utc(),wall_seconds=time.monotonic()-started)
        io.write(destination/'receipt.json',receipt)
        verify(destination)
    except BaseException:
        receipt.update(status='failed',ended_utc=io.utc(),wall_seconds=time.monotonic()-started,error=traceback.format_exc())
        io.write(destination/'receipt.json',receipt)
        raise
    finally:
        lock.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command',required=True)
    sub.add_parser('freeze')
    check = sub.add_parser('verify'); check.add_argument('run')
    launch = sub.add_parser('run')
    launch.add_argument('--mode',choices=['preflight','survey'],required=True)
    launch.add_argument('--model',choices=[MODEL],default=MODEL)
    launch.add_argument('--gpu',type=int,choices=[0,1],required=True)
    launch.add_argument('--shard',type=int,choices=[0,1],required=True)
    launch.add_argument('--output',required=True); launch.add_argument('--authorization',required=True)
    launch.add_argument('--execute',action='store_true')
    args = parser.parse_args()
    if args.command == 'freeze': freeze()
    elif args.command == 'verify': print(json.dumps({'status':verify(args.run)['status']}))
    else: run(args)
