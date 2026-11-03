"""Frozen joint measurement; importing this module never loads model weights."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import time
import traceback

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ASSETS = REPO / 'experiments/layer-dose-survey-toy-v1-2026-10-27/asset_manifest.json'
SOURCE_QUESTIONS = REPO / 'experiments/qwen35-neuron-steering-2026-10-25/raw-corpus-cpu-bf16-r01/questions.json'
RANDOM_SOURCE = REPO / 'experiments/root-cause-toy-v1-2026-10-26/runs/root-r01/decompose-r01/conditions.json'


def utc():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for part in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(part)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    allow_nan=False).encode()).hexdigest()


def write(path, value, immutable=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    if immutable:
        with path.open('x') as stream:
            stream.write(data)
    else:
        temporary = path.with_suffix(path.suffix + '.tmp')
        temporary.write_text(data)
        temporary.replace(path)


def inputs():
    import task_data
    items, fixtures = task_data.build()
    assert read(HERE / 'data/items.json') == items
    assert read(HERE / 'data/assessment-fixtures.json') == fixtures
    assert len(items) == 120 and len({r['id'] for r in items}) == 120
    return items


def conditions(stage):
    assert stage in ('stage1', 'stage2')
    pairs = read(RANDOM_SOURCE)['random_pairs']
    recipes = [('AB', {'13': 7956, '14': 8949})] + [
        (f'R{i:02d}', pair) for i, pair in enumerate(pairs, 1)]
    doses = [0.5, 1.0] if stage == 'stage1' else [0.0625, 0.125, 0.25]
    result = [{'id': 'clean', 'recipe': 'clean', 'dose': 0.0, 'channels': {}}] if stage == 'stage1' else []
    return result + [{'id': f'{name}_d{dose:g}', 'recipe': name, 'dose': dose,
                      'channels': pair} for dose in doses for name, pair in recipes]


def assigned(items, gpu):
    assert gpu in (0, 1)
    bases = list(dict.fromkeys(r['base_id'] for r in items))
    return [r for r in items if bases.index(r['base_id']) % 2 == gpu]


def frozen_paths():
    local = sorted(HERE.glob('*.py')) + [HERE / n for n in (
        'CONTRACT.zh-CN.md', 'contract.json', 'data/items.json', 'data/assessment-fixtures.json')]
    return local + [ASSETS, SOURCE_QUESTIONS, RANDOM_SOURCE,
        REPO / 'experiments/transfer-toy-v1-2026-10-26/transfer_engine.py',
        REPO / 'experiments/capability-damage-v2-2026-10-26/model_engine.py']


def freeze():
    inputs()
    value = {'created_at': utc(), 'experiment': HERE.name,
             'files': {str(p.relative_to(REPO)): sha(p) for p in frozen_paths()}}
    write(HERE / 'freeze.json', value, immutable=True)
    return value


def check():
    value = read(HERE / 'freeze.json')
    assert value['experiment'] == HERE.name
    assert value['files'] == {str(p.relative_to(REPO)): sha(p) for p in frozen_paths()}
    items = inputs()
    for gpu in (0, 1):
        rows = assigned(items, gpu)
        assert len(rows) == 60 and sum(bool(r['choices']) for r in rows) == 48
    return {'status': 'passed', 'freeze_sha256': sha(HERE / 'freeze.json'), 'items': len(items)}


def contexts_for(tokenizer, items):
    return {r['id']: tokenizer.apply_chat_template([{'role': 'user', 'content': r['prompt']}],
        tokenize=False, add_generation_prompt=True, enable_thinking=False) for r in items}


def tokenizer_check(tokenizer, items):
    from joint_engine import encode_text, encode_pair, token_hash
    contexts = contexts_for(tokenizer, items)
    rows = {}
    for item in items:
        context = contexts[item['id']]
        prefix = encode_text(tokenizer, context)
        tails = []
        for choice in item['choices']:
            left, right = encode_pair(tokenizer, context, choice)
            whole = encode_text(tokenizer, context + choice)
            assert left == prefix and whole == left + right, 'Candidate changed prompt token boundary'
            tails.append(right)
        if tails:
            assert len(tails) == 2 and tails[0] != tails[1]
            assert len(tails[0]) == len(tails[1]), f"Unequal candidate tokens: {item['id']}"
        assert len(prefix) + 128 <= 32768
        rows[item['id']] = {'input_token_ids': prefix, 'input_token_sha256': token_hash(prefix),
                             'candidate_token_ids': tails}
    return {'status': 'passed', 'rows': rows}


def authorize(path, stage, mode, execute):
    if not execute or not path:
        raise ValueError('Explicit user authorization and --execute required before model loading')
    value = read(path)
    assert value['experiment'] == HERE.name and value['status'] == 'authorized'
    assert value['freeze_sha256'] == sha(HERE / 'freeze.json')
    assert stage in value['stages'] and mode in ('preflight', 'formal')
    assert value['maximum_model_workers'] == 2 and value['user_instruction']
    if stage == 'stage2':
        gate = read(HERE / 'readiness/stage2-gate.json')
        assert gate['status'] == 'passed' and gate['measurement_usable'] is True
        assert gate['freeze_sha256'] == value['freeze_sha256']
        assert gate['basis'] == 'measurement_validity_not_AB_effect'
        assert gate['review_evidence'] and gate['reviewer']
        assert gate['evidence_hashes'], 'A review gate must bind actual evidence'
        for name, expected in gate['evidence_hashes'].items():
            assert sha(HERE / name) == expected
        fixture_review = read(HERE / gate['fixture_review_path'])
        clean_review = read(HERE / gate['clean_review_path'])
        assert gate['fixture_review_path'] in gate['evidence_hashes'] and gate['clean_review_path'] in gate['evidence_hashes']
        assert fixture_review['status'] == clean_review['status'] == 'passed'
        assert len(fixture_review['rows']) == 36 and {r['id'] for r in fixture_review['rows']} == {
            r['id'] for r in read(HERE / 'data/assessment-fixtures.json')}
        assert all(r['expected_matched'] is True for r in fixture_review['rows'])
        assert len(clean_review['rows']) == 96 and {r['id'] for r in clean_review['rows']} == {
            r['id'] for r in inputs() if r['panel'] == 'diagnostic'}
        assert clean_review['measurement_usable'] is True
        assert all(r['status'] == 'reviewed' and r['evidence'] for r in clean_review['rows'])
        verify_stage(HERE / gate['stage1_run'], 'stage1')
    return value


def model_assets():
    source = read(HERE / 'contract.json')['source']
    expected = read(ASSETS)['4b']
    assert source['revision'] == expected['revision']
    started = time.monotonic()
    for name, identity in expected['files'].items():
        path = Path(source['model_path']) / name
        assert path.stat().st_size == identity['bytes'] and sha(path) == identity['sha256'], name
    return {'status': 'passed', 'files': len(expected['files']), 'manifest_sha256': sha(ASSETS),
            'seconds': time.monotonic() - started}


def metadata_check(engine):
    source = read(HERE / 'contract.json')['source']
    assert engine.weight_hashes == source['target_weight_sha256']
    assert engine.metadata['dtype'] == 'bfloat16' and engine.metadata['attention_backend'] == 'eager'
    assert engine.metadata['batch_size'] == 1
    assert len(engine.layers) == 32
    for package in ('torch', 'transformers'):
        assert engine.metadata['versions'][package] == source[package + '_version']


def collect_one(engine, item, context, reference, condition, token_info):
    from joint_engine import bind_calibration, validate_audit, token_hash
    started = time.monotonic()
    calibration = bind_calibration(context, reference, engine.tokenizer)
    output = engine.generate([context], condition['id'], [calibration], 128, [])[0]
    output['token_sha256'] = token_hash(output['token_ids'])
    generation_audit = deepcopy(engine.last_audit)
    validate_audit(generation_audit, condition, calibration, len(token_info['input_token_ids']),
                   generated_count=len(output['token_ids']))
    choices = []
    for continuation in item['choices']:
        detail = engine.score([context], [continuation], condition['id'], [calibration])[0]
        detail['audit'] = deepcopy(engine.last_audit)
        length = len(token_info['input_token_ids']) + len(detail['continuation_token_ids']) - 1
        validate_audit(detail['audit'], condition, calibration, len(token_info['input_token_ids']), input_length=length)
        choices.append(detail)
    return {'status': 'completed', 'item_id': item['id'], 'item_sha256': digest(item),
            'condition': condition, 'context': context, 'reference_calibration': reference,
            'calibration': calibration, 'output': output, 'generation_audit': generation_audit,
            'choice_details': choices, 'finished_at': utc(), 'wall_seconds': time.monotonic() - started}


def check_record(row, item, condition, token_info, reference):
    from joint_engine import token_hash, validate_audit, text_hash
    assert row['status'] == 'completed' and row['item_id'] == item['id']
    assert row['item_sha256'] == digest(item) and row['condition'] == condition
    assert row['reference_calibration'] == reference
    calibration = row['calibration']
    assert calibration['residual_scales'] == reference['residual_scales']
    assert calibration['reference_calibration_sha256'] == digest(reference)
    assert calibration['reference_context_sha256'] == reference['context_sha256']
    assert calibration['reference_input_token_sha256'] == reference['input_token_sha256']
    assert calibration['input_token_sha256'] == token_info['input_token_sha256']
    assert calibration['input_token_count'] == len(token_info['input_token_ids'])
    assert calibration['context_sha256'] == text_hash(row['context'])
    output = row['output']
    tokens = output['token_ids']
    assert len(tokens) == output['generated_token_count'] and 1 <= len(tokens) <= 128
    assert output['token_sha256'] == token_hash(tokens)
    assert output['input_token_sha256'] == token_info['input_token_sha256']
    assert output['max_new_tokens'] == 128 and output['returned_padding_count'] == 0
    if output['end_reason'] == 'eos_token':
        assert tokens[-1] in (248044, 248046) and not any(t in (248044, 248046) for t in tokens[:-1])
    else:
        assert output['end_reason'] == 'length_limit' and len(tokens) == 128
        assert not any(t in (248044, 248046) for t in tokens)
    prompt_length = len(token_info['input_token_ids'])
    validate_audit(row['generation_audit'], condition, calibration, prompt_length, generated_count=len(tokens))
    assert len(row['choice_details']) == len(item['choices'])
    for detail, tail in zip(row['choice_details'], token_info['candidate_token_ids']):
        assert detail['continuation_token_ids'] == tail
        assert detail['context_token_count'] == prompt_length
        assert detail['input_token_sha256'] == token_hash(token_info['input_token_ids'] + tail[:-1])
        assert len(detail['token_logprobs']) == len(tail) and all(math.isfinite(x) for x in detail['token_logprobs'])
        assert math.isclose(sum(detail['token_logprobs']), detail['loglikelihood'], abs_tol=1e-4)
        validate_audit(detail['audit'], condition, calibration, prompt_length,
                       input_length=prompt_length + len(tail) - 1)


def preflight(engine, items, contexts, references, tokens, output):
    from joint_engine import TransferEngine, encode_pair
    from types import MethodType
    specimens = [next(r for r in items if r['family'] == family) for family in ('reading', 'arithmetic', 'relation', 'open')]
    all_conditions = conditions('stage1') + conditions('stage2')
    engine.configure(all_conditions)
    zero = {'id': 'zero', 'recipe': 'AB', 'dose': 0.0, 'channels': {'13': 7956, '14': 8949}}
    clean, ab = all_conditions[0], next(c for c in all_conditions if c['id'] == 'AB_d1')
    evidence, durations = [], []
    def collect(item, condition):
        ref = references[item['base_id']]
        row = collect_one(engine, item, contexts[item['id']], ref, condition, tokens[item['id']])
        check_record(row, item, condition, tokens[item['id']], ref)
        evidence.append(row)
        durations.append(row['wall_seconds'])
        return row
    for item in specimens:
        before = collect(item, clean)
        zero_row = collect(item, zero)
        collect(item, next(c for c in all_conditions if c['id'] == 'AB_d0.5'))
        collect(item, ab)
        restored = collect(item, clean)
        for row in (zero_row, restored):
            assert before['output']['token_ids'] == row['output']['token_ids']
            assert [r['token_logprobs'] for r in before['choice_details']] == [r['token_logprobs'] for r in row['choice_details']]
    first = specimens[0]
    for condition in all_conditions:
        if condition['recipe'].startswith('R') and condition['dose'] in (0.5, 1.0):
            collect(first, condition)
        elif condition['recipe'] == 'AB' and condition['dose'] in (0.0625, 0.125, 0.25):
            collect(first, condition)
    # Independent frozen implementation comparison: same calibration/conditions,
    # with its original hook instead of the added audit wrapper.
    new = collect(first, ab)
    saved = engine._intervention
    try:
        engine._intervention = MethodType(TransferEngine._intervention, engine)
        reference_output = engine.generate([new['context']], ab['id'], [new['calibration']], 128, [])[0]
        reference_scores = [TransferEngine.score(engine, [new['context']], [s], ab['id'], [new['calibration']])[0] for s in first['choices']]
    finally:
        engine._intervention = saved
    assert new['output']['token_ids'] == reference_output['token_ids']
    legacy_score_difference = 0.0
    for current, legacy in zip(new['choice_details'], reference_scores):
        count = len(current['continuation_token_ids'])
        assert current['input_token_sha256'] == legacy['input_token_sha256']
        assert current['continuation_token_ids'] == legacy['continuation_token_ids'][-count:]
        difference = max(abs(a - b) for a, b in zip(current['token_logprobs'], legacy['token_logprobs'][-count:]))
        legacy_score_difference = max(legacy_score_difference, difference)
        assert difference <= 0.02
    # Verify likelihood suffix indexing with a full-logit forward.
    left, right = encode_pair(engine.tokenizer, new['context'], first['choices'][0])
    tensor_inputs = engine._inputs([left + right[:-1]])
    torch = engine.torch
    with torch.inference_mode(), engine._intervention(ab['id'], [new['calibration']], tensor_inputs['attention_mask']):
        logits = engine.model(**tensor_inputs, use_cache=False).logits[0, -len(right):]
        ll = torch.log_softmax(logits, -1, dtype=torch.float32)
        full = ll.gather(-1, torch.tensor(right, device=engine.device)[:, None]).flatten().tolist()
    assert max(abs(a - b) for a, b in zip(full, new['choice_details'][0]['token_logprobs'])) <= 0.02
    result = {'status': 'passed', 'records': evidence, 'reference_output': reference_output,
              'reference_scores': reference_scores, 'full_forward_token_logprobs': full,
              'zero_and_restored_exact': True, 'legacy_generation_exact': True,
              'legacy_score_max_abs_difference_nats': legacy_score_difference,
              'seconds': sum(durations), 'generated_records': len(evidence) + 1,
              'formal_records': 0}
    write(output / 'preflight.json', result, immutable=True)
    return result


def run(stage, mode, gpu, output, authorization, execute=False):
    launch = authorize(authorization, stage, mode, execute)
    check()
    output = Path(output).resolve()
    assert output.is_relative_to((HERE / 'runs').resolve())
    expected_root = launch['preflight_run'] if mode == 'preflight' else launch['formal_runs'][stage]
    assert output == (HERE / expected_root / f'worker-{gpu}').resolve()
    if mode == 'formal':
        preflight_root = HERE / launch['preflight_run']
        for shard in (0, 1):
            verify_worker(preflight_root / f'worker-{shard}', 'preflight', 'stage1')
    import fcntl
    lock = open(f'/tmp/acupuncture-layer-survey-gpu{gpu}.lock', 'w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    used = subprocess.check_output(['nvidia-smi', f'--id={gpu}', '--query-gpu=memory.used', '--format=csv,noheader,nounits'], text=True)
    assert int(used.strip()) < 256, 'GPU occupied; keep existing jobs untouched'
    output.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    receipt = {'status': 'running', 'stage': stage, 'mode': mode, 'gpu': gpu,
        'pid': os.getpid(), 'freeze_sha256': sha(HERE / 'freeze.json'), 'started_at': utc(),
        'authorization_sha256': sha(authorization), 'record_hashes': {}, 'asset_hashes': {}}
    write(output / 'authorization.json', launch, immutable=True)
    write(output / 'receipt.json', receipt)
    engine = None
    try:
        from joint_engine import JointEngine
        source = read(HERE / 'contract.json')['source']
        receipt['model_assets'] = model_assets()
        engine = JointEngine(source['model_path'], device=f'cuda:{gpu}', threads=4)
        metadata_check(engine)
        receipt['load_seconds'] = time.monotonic() - start
        all_items = inputs()
        token_result = tokenizer_check(engine.tokenizer, all_items)
        contexts = contexts_for(engine.tokenizer, all_items)
        items = assigned(all_items, gpu) if mode == 'formal' else all_items
        reference_items = {r['base_id']: next(x for x in all_items if x['id'] == r['reference_id']) for r in items}
        references = {base: engine.calibrate([contexts[row['id']]])[0] for base, row in reference_items.items()}
        if stage == 'stage2':
            assert mode == 'formal', 'Stage2 reuses the all-dose stage1 preflight'
            gate = read(HERE / 'readiness/stage2-gate.json')
            previous = read(HERE / gate['stage1_run'] / f'worker-{gpu}/calibrations.json')
            for base in references:
                assert references[base] == previous[base], 'Stage calibration drift'
        engine.configure(conditions(stage))
        for name, value in [('metadata.json', engine.metadata), ('tokens.json', token_result),
                            ('contexts.json', contexts), ('calibrations.json', references)]:
            write(output / name, value, immutable=True)
            receipt['asset_hashes'][name] = sha(output / name)
        if mode == 'preflight':
            result = preflight(engine, all_items, contexts, references, token_result['rows'], output)
            receipt['asset_hashes']['preflight.json'] = sha(output / 'preflight.json')
            receipt['preflight_summary'] = {k: v for k, v in result.items() if k not in ('records', 'reference_output', 'reference_scores', 'full_forward_token_logprobs')}
        else:
            receipt['expected_records'] = len(items) * len(conditions(stage))
            for item in items:
                for condition in conditions(stage):
                    row = collect_one(engine, item, contexts[item['id']], references[item['base_id']], condition, token_result['rows'][item['id']])
                    name = f"records/{item['id']}__{condition['id']}.json"
                    write(output / name, row, immutable=True)
                    receipt['record_hashes'][name] = sha(output / name)
                    check_record(row, item, condition, token_result['rows'][item['id']], references[item['base_id']])
                    receipt.update(completed_records=len(receipt['record_hashes']), latest_record_at=row['finished_at'])
                    write(output / 'receipt.json', receipt)
                    print(json.dumps({'completed': receipt['completed_records'], 'expected': receipt['expected_records'],
                        'item': item['id'], 'condition': condition['id'], 'seconds': row['wall_seconds']}, ensure_ascii=False), flush=True)
        receipt['integrity'] = engine.verify_unchanged()
        receipt['status'] = 'completed'
    except BaseException:
        receipt.update(status='failed', error=traceback.format_exc())
        if engine is not None:
            try:
                receipt['integrity_after_failure'] = engine.verify_unchanged()
            except BaseException:
                receipt['integrity_error'] = traceback.format_exc()
        raise
    finally:
        receipt.update(finished_at=utc(), wall_seconds=time.monotonic() - start)
        write(output / 'receipt.json', receipt)
    return verify_worker(output, mode, stage)


def verify_worker(output, mode, stage):
    check()
    output = Path(output)
    receipt = read(output / 'receipt.json')
    assert receipt['status'] == 'completed' and receipt['mode'] == mode and receipt['stage'] == stage
    assert receipt['freeze_sha256'] == sha(HERE / 'freeze.json')
    assert receipt['authorization_sha256'] == sha(output / 'authorization.json')
    auth = read(output / 'authorization.json')
    assert auth['status'] == 'authorized' and auth['experiment'] == HERE.name
    assert auth['freeze_sha256'] == receipt['freeze_sha256'] and stage in auth['stages']
    expected_assets = {'metadata.json', 'tokens.json', 'contexts.json', 'calibrations.json'}
    if mode == 'preflight':
        expected_assets.add('preflight.json')
    assert set(receipt['asset_hashes']) == expected_assets
    assert receipt['integrity']['hooks_removed'] is True
    assert receipt['integrity']['target_weight_sha256_after'] == read(HERE / 'contract.json')['source']['target_weight_sha256']
    for name, expected in receipt['asset_hashes'].items():
        assert sha(output / name) == expected, name
    if mode == 'preflight':
        result = read(output / 'preflight.json')
        assert result['status'] == 'passed' and result['zero_and_restored_exact'] and result['legacy_generation_exact']
        assert result['legacy_score_max_abs_difference_nats'] <= 0.02
        assert result['generated_records'] == 35 and len(result['records']) == 34
        return {'status': 'passed', 'mode': mode, 'gpu': receipt['gpu'], 'generated_records': result['generated_records']}
    items = assigned(inputs(), receipt['gpu'])
    rows = {r['id']: r for r in items}
    expected_names = {f"records/{r['id']}__{c['id']}.json" for r in items for c in conditions(stage)}
    assert set(receipt['record_hashes']) == expected_names
    assert {str(p.relative_to(output)) for p in (output / 'records').glob('*.json')} == expected_names
    tokens = read(output / 'tokens.json')['rows']
    contexts = read(output / 'contexts.json')
    references = read(output / 'calibrations.json')
    choices = {c['id']: c for c in conditions(stage)}
    for name, expected in receipt['record_hashes'].items():
        assert sha(output / name) == expected
        row = read(output / name)
        item = rows[row['item_id']]
        assert row['context'] == contexts[item['id']]
        check_record(row, item, choices[row['condition']['id']], tokens[item['id']], references[item['base_id']])
    return {'status': 'passed', 'stage': stage, 'gpu': receipt['gpu'], 'records': len(expected_names)}


def verify_stage(output, stage):
    output = Path(output)
    results = [verify_worker(Path(output) / f'worker-{i}', 'formal', stage) for i in (0, 1)]
    assert {r['gpu'] for r in results} == {0, 1}
    assert sum(r['records'] for r in results) == {'stage1': 1560, 'stage2': 2160}[stage]
    for gpu in (0, 1):
        exit_record = read(output / f'formal-worker-{gpu}-exit.json')
        assert exit_record['gpu'] == gpu and exit_record['exit_code'] == 0
    return {'status': 'passed', 'stage': stage, 'records': sum(r['records'] for r in results), 'workers': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('freeze', 'check', 'run', 'verify-worker', 'verify-stage', 'tokenizer-check'))
    parser.add_argument('--stage', choices=('stage1', 'stage2'), default='stage1')
    parser.add_argument('--mode', choices=('preflight', 'formal'), default='preflight')
    parser.add_argument('--gpu', type=int, choices=(0, 1), default=0)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--authorization', type=Path)
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if args.command == 'freeze':
        result = freeze()
    elif args.command == 'check':
        result = check()
    elif args.command == 'tokenizer-check':
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(read(HERE / 'contract.json')['source']['model_path'], local_files_only=True)
        result = tokenizer_check(tok, inputs())
    elif args.command == 'run':
        result = run(args.stage, args.mode, args.gpu, args.output, args.authorization, args.execute)
    elif args.command == 'verify-worker':
        result = verify_worker(args.output, args.mode, args.stage)
    else:
        result = verify_stage(args.output, args.stage)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
