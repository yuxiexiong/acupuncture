"""Complete raw exports and capability scores; behavior labels remain blank for blind review."""
import argparse
from collections import Counter
import hashlib
import html
import json
from pathlib import Path
import random
import shutil
import time
import traceback

from run_io import read, rows, sha, utc, write

ROOT = Path(__file__).resolve().parent
SOURCE_CONDITIONS = ['S_0', 'S_channel', 'S_vector']
TARGET_CONDITIONS = ['T_0'] + [f'{pair}_{arm}' for pair in ['true', 'random1', 'random2', 'random3']
    for arm in ['D_raw', 'S_proj', 'D_match', 'S_recipe']] + ['T_dense', 'T_sparse']
LABELS = ['harmful_stance', 'hostile_wording', 'task_completed', 'coherent', 'repetition', 'unrateable']


def digest_text(text):
    return hashlib.sha256(text.encode()).hexdigest()


def dump_rows(path, content):
    with Path(path).open('x') as stream:
        for row in content:
            stream.write(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n')


def validate_generation(output):
    tokens = output['token_ids']
    assert all(isinstance(token, int) for token in tokens)
    assert len(tokens) == output['generated_token_count'] <= output['max_new_tokens'] == 512
    assert output['end_reason'] in ('eos_token', 'length_limit')
    assert isinstance(output['raw_text'], str) and isinstance(output['answer_text'], str)
    if output['end_reason'] == 'eos_token':
        assert tokens and tokens[-1] in (248044, 248046)
    else:
        assert len(tokens) == 512
    return {'generated_token_sha256': digest_text(json.dumps(tokens, separators=(',', ':'))),
            'raw_text_sha256': digest_text(output['raw_text'])}


def verified_toy(directory, kind, data, inputs):
    directory = Path(directory)
    conditions = SOURCE_CONDITIONS if kind == 'source' else TARGET_CONDITIONS
    frozen = {'behavior': rows(data / 'confirm.jsonl'), 'ability': rows(data / 'ability_diag.jsonl')}
    assert all(len(items) == 64 and len({item['id'] for item in items}) == 64 for items in frozen.values())
    records = {'behavior': [], 'ability': []}
    identity_receipts = []
    expected_behavior = 96 if kind == 'source' else 608
    expected_ability = 0 if kind == 'source' else 608
    for shard in (0, 1):
        shard_root = directory / f'shard{shard}'
        receipt_path = shard_root / 'receipt.json'
        receipt = read(receipt_path)
        inputs[str(receipt_path)] = sha(receipt_path)
        assert receipt['status'] == 'completed' and receipt['kind'] == kind
        assert receipt['completed_behavior'] == receipt['expected_behavior'] == expected_behavior
        assert receipt['completed_diagnostic'] == receipt['expected_diagnostic'] == expected_ability
        assert receipt['completed_calibrations'] == 64
        assert receipt['hooks_removed'] and receipt['target_weight_sha256_after'] == receipt['engine']['target_weight_sha256_before']
        assert receipt['data_sha256'] == {name: sha(data / f'{name}.jsonl') for name in ('confirm', 'ability_diag')}
        identity_receipts.append(receipt)
        for split, items in frozen.items():
            expected_conditions = [] if kind == 'source' and split == 'ability' else conditions
            files = sorted((shard_root / 'records' / split).glob('*.jsonl'))
            assert len(files) == 32 * len(expected_conditions), f'Unexpected record count: {shard_root}/{split}'
            observed = set()
            for index in range(shard, 64, 2):
                calibration_path = shard_root / 'calibrations' / f'{split}-{index:03d}.json'
                calibration = read(calibration_path)
                inputs[str(calibration_path)] = sha(calibration_path)
                assert calibration['item_id'] == items[index]['id']
                for condition in expected_conditions:
                    path = shard_root / 'records' / split / f'{index:03d}-{condition}.jsonl'
                    content = rows(path)
                    assert len(content) == 1
                    row = content[0]
                    assert row['status'] == 'completed' and row['item'] == items[index] and row['condition'] == condition
                    assert row['calibration'] == calibration
                    assert digest_text(row['context']) == calibration['context_sha256']
                    key = (row['item']['id'], condition)
                    assert key not in observed
                    observed.add(key)
                    entry = {'model_role': kind, **row, 'source_file': str(path), 'source_file_sha256': sha(path)}
                    inputs[str(path)] = entry['source_file_sha256']
                    if split == 'behavior':
                        entry['export_integrity'] = validate_generation(row['output'])
                    else:
                        assert len(row['output']['choice_loglikelihoods']) == len(row['item']['continuations'])
                    records[split].append(entry)
    for field in ('data_sha256', 'source_sha256'):
        assert identity_receipts[0][field] == identity_receipts[1][field]
    assert identity_receipts[0]['engine']['target_weight_sha256_before'] == identity_receipts[1]['engine']['target_weight_sha256_before']
    if kind == 'target':
        assert identity_receipts[0]['conditions_sha256'] == identity_receipts[1]['conditions_sha256']
    for split in records:
        order = {item['id']: i for i, item in enumerate(frozen[split])}
        records[split].sort(key=lambda row: (order[row['item']['id']], conditions.index(row['condition'])))
    return records


def blind_pack(records, reviewer, target, seed):
    order = list(range(len(records)))
    rng = random.Random(seed)
    rng.shuffle(order)
    opaque = list(range(len(records)))
    rng.shuffle(opaque)
    packet, keys = [], []
    for position, record_index in enumerate(order):
        record = records[record_index]
        identity = f'{reviewer}-{opaque[position] + 1:05d}'
        packet.append({'anonymous_id': identity, 'question': record['item']['prompt'],
                       'answer': record['output']['raw_text'],
                       'labels': {label: None for label in LABELS}, 'evidence': None, 'uncertain_reason': None})
        keys.append({'reviewer': reviewer, 'anonymous_id': identity, 'target_run': target,
                     'model_role': record['model_role'], 'item_id': record['item']['id'],
                     'condition': record['condition'], 'source_file': record['source_file'],
                     'source_file_sha256': record['source_file_sha256']})
    return packet, keys


def paired_html(source, target, questions):
    lookup = {(row['model_role'], row['item']['id'], row['condition']): row for row in source + target}
    pieces = ['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>Acupuncture 完整并排原文</title><style>body{font:16px/1.6 system-ui;margin:24px;background:#f4f5f7;color:#17202a}h2{padding:12px;background:#fff;position:sticky;top:0;border-bottom:2px solid #999}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:14px}.card{background:white;padding:16px;border:1px solid #cbd1d8;border-radius:6px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.6 system-ui}small{color:#555}section{margin:32px 0}</style>',
        '<h1>64 题：源模型 3 条件与目标模型 19 条件完整原文</h1><p>全部回答按固定题序展示。没有内容筛选、自动行为评分或差异高亮；达到 token 上限的原文也完整保留。行为双盲标签待填写。</p>']
    for item in questions:
        pieces.append(f'<section><h2>{html.escape(item["id"])} · {html.escape(item["prompt"])}</h2><div class="grid">')
        for role, conditions in [('source', SOURCE_CONDITIONS), ('target', TARGET_CONDITIONS)]:
            for condition in conditions:
                row = lookup[role, item['id'], condition]
                output = row['output']
                pieces.append(f'<article class="card"><strong>{role} · {html.escape(condition)}</strong><br><small>{output["generated_token_count"]} tokens · {html.escape(output["end_reason"])}</small><pre>{html.escape(output["raw_text"])}</pre></article>')
        pieces.append('</div></section>')
    return ''.join(pieces) + '</html>'


def diagnostic_scores(records, project):
    from run_benchmark import load_v3
    official_module = load_v3('score_results')
    scorer = official_module.OfficialScorer(project / '.runtime/lm-evaluation-harness', project / '.cache/hf/datasets')
    scored = []
    for row in records:
        parsed = scorer.score(row['item'], {'status': 'completed', **row['output']})
        scored.append({'id': row['item']['id'], 'benchmark': row['item']['benchmark'],
            'condition': row['condition'], 'diagnostic_group': row['item']['diagnostic_group'],
            'cluster_id': row['item']['context_sha256'], 'result': {**parsed, 'end_reason': 'loglikelihood'}})
    lookup = {(row['condition'], row['id']): row for row in scored}
    summary = {}
    for condition in TARGET_CONDITIONS:
        summary[condition] = {}
        for task in ('mmlu', 'arc_challenge'):
            subset = [row for row in scored if row['condition'] == condition and row['benchmark'] == task]
            assert len(subset) == 32
            paired = []
            for row in subset:
                pair = {'id': row['id'], 'cluster_id': row['cluster_id'], 'outputs': {
                    'baseline': lookup['T_0', row['id']]['result'], 'evo': row['result']}}
                if task == 'mmlu':
                    pair['subject'] = row['diagnostic_group']
                paired.append(pair)
            population = None
            if task == 'mmlu':
                groups = Counter(row['diagnostic_group'] for row in subset)
                assert len(groups) == 4 and set(groups.values()) == {8}
                population = {group: 1 for group in groups}
            summary[condition][task] = {'metric': official_module.METRICS[task],
                **official_module.summarize(paired, population)}
    return scored, {'status': 'completed', 'scope': '64-item diagnostic only; separate from the official 1400-item panel',
        'mmlu_weighting': 'Four predefined broad groups, eight questions per group, equal group weights',
        'conditions': summary}


def verify_benchmark(directory, inputs):
    from finish_benchmark import verified_records
    from run_benchmark import frozen_panel
    _, _, items = frozen_panel()
    records, paths, _ = verified_records(directory, items)
    assert len(records) == 1400
    finish = directory / 'finish-r01'
    receipt = read(finish / 'receipt.json')
    assert receipt['status'] == 'completed' and receipt['inference_pairs'] == 1400 and receipt['condition_units'] == 2800
    inputs[str(finish / 'receipt.json')] = sha(finish / 'receipt.json')
    for name, digest in receipt['artifacts_sha256'].items():
        assert sha(finish / name) == digest
        inputs[str(finish / name)] = digest
    for path in paths:
        inputs[str(path)] = sha(path)
    summary = read(finish / 'summary.json')
    assert summary['status'] == 'completed' and summary['technical_failures'] == 0
    assert {task: row['n'] for task, row in summary['benchmarks'].items()} == {
        'mmlu': 1000, 'arc_challenge': 200, 'gsm8k': 100, 'humaneval': 100}
    return summary


def run(args):
    started = time.monotonic()
    destination = args.run / args.target / 'export-r01'
    destination.mkdir(parents=True, exist_ok=False)
    receipt_path = destination / 'receipt.json'
    receipt = {'status': 'running', 'started_utc': utc(), 'target': args.target,
               'source_sha256': {name: sha(ROOT / name) for name in ('export_results.py', 'RATING_MANUAL.zh-CN.md')},
               'behavior_ratings': 'not_started', 'behavior_semantic_analysis_performed': False}
    write(receipt_path, receipt)
    inputs = {}
    try:
        for name in ('confirm', 'ability_diag'):
            inputs[str(args.data / (name + '.jsonl'))] = sha(args.data / (name + '.jsonl'))
        source = verified_toy(args.run / 'source', 'source', args.data, inputs)
        target = verified_toy(args.run / args.target / 'toy', 'target', args.data, inputs)
        assert len(source['behavior']) == 192 and not source['ability']
        assert len(target['behavior']) == len(target['ability']) == 1216
        benchmark = verify_benchmark(args.run / args.target / 'benchmark', inputs)
        toy_identity = read(args.run / args.target / 'toy/shard0/receipt.json')
        benchmark_identity = read(args.run / args.target / 'benchmark/shard-0/receipt.json')
        assert toy_identity['conditions_sha256'] == benchmark['conditions_sha256'] == benchmark_identity['conditions_sha256']
        assert toy_identity['engine']['target_weight_sha256_before'] == benchmark_identity['engine']['target_weight_sha256_before']
        for split, name in [('behavior', 'confirm'), ('ability', 'ability_diag')]:
            frozen_items = rows(args.data / f'{name}.jsonl')
            calibration_by_id = {}
            for index, item in enumerate(frozen_items):
                path = args.run / 'source' / f'shard{index % 2}' / 'calibrations' / f'{split}-{index:03d}.json'
                calibration_by_id[item['id']] = (read(path), inputs[str(path)])
            for row in target[split]:
                original, digest = calibration_by_id[row['item']['id']]
                assert row['calibration']['source_calibration_file_sha256'] == digest
                assert row['calibration']['source_residual_scales'] == original['residual_scales']
        dump_rows(destination / 'source.raw.jsonl', source['behavior'])
        dump_rows(destination / 'original.raw.jsonl', [row for row in target['behavior'] if row['condition'] == 'T_0'])
        dump_rows(destination / 'modified.raw.jsonl', [row for row in target['behavior'] if row['condition'] != 'T_0'])
        dump_rows(destination / 'diagnostic.raw.jsonl', target['ability'])
        behavior = source['behavior'] + target['behavior']
        (destination / 'paired_raw.html').write_text(paired_html(source['behavior'], target['behavior'], rows(args.data / 'confirm.jsonl')))
        private = []
        for reviewer, seed in (('A', 20261026), ('B', 20261027)):
            packet, keys = blind_pack(behavior, reviewer, args.target, seed)
            directory = destination / f'blind_{reviewer}'
            directory.mkdir()
            dump_rows(directory / 'ratings.blank.jsonl', packet)
            shutil.copyfile(ROOT / 'RATING_MANUAL.zh-CN.md', directory / 'RATING_MANUAL.zh-CN.md')
            private.extend(keys)
        dump_rows(destination / 'rating_keys.private.jsonl', private)
        scored, diagnostic = diagnostic_scores(target['ability'], args.project)
        dump_rows(destination / 'diagnostic.scores.jsonl', scored)
        write(destination / 'diagnostic.summary.json', diagnostic)
        write(destination / 'benchmark.summary.json', benchmark)
        for path, digest in inputs.items():
            assert sha(path) == digest, f'Input changed during export: {path}'
        receipt.update(status='machine_completed_blind_review_pending', counts={
            'questions': 64, 'source_behavior_records': 192, 'target_behavior_records': 1216,
            'target_original_records': 64, 'target_modified_records': 1152,
            'target_diagnostic_records': 1216, 'benchmark_pairs': 1400,
            'blind_records_per_reviewer': 1408, 'independent_reviewers': 2},
            input_sha256=inputs, behavior_ratings='blank_independent_forms_exported',
            claims='Machine inference, integrity, raw export, diagnostic scoring and official capability benchmark complete; behavioral transfer remains unjudged.')
    except Exception as error:
        receipt.update(status='failed', error=str(error), traceback=traceback.format_exc())
        raise
    finally:
        receipt.update(ended_utc=utc(), elapsed_seconds=time.monotonic() - started,
            artifacts_sha256={str(p.relative_to(destination)): sha(p) for p in sorted(destination.rglob('*'))
                              if p.is_file() and p != receipt_path})
        write(receipt_path, receipt)
        print(json.dumps({'status': receipt['status'], 'target': args.target, 'receipt': str(receipt_path)}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--target', choices=['target9b', 'target2b'], required=True)
    parser.add_argument('--data', type=Path, default=ROOT / 'data')
    parser.add_argument('--project', type=Path, default=ROOT.parents[1])
    run(parser.parse_args())
