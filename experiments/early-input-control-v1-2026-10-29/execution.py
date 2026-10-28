"""Evidence-gated formal runners. Import and validation never load a model."""
from collections import Counter
from pathlib import Path
import re
import time

import experiment as exp
from control_engine import exact_pair, encode_text, token_hash, text_hash, digest as control_digest

CLEAN = {'id': 'clean', 'kind': 'clean', 'dose': 0.0}
EARLY_POINTS = {(0, 4146), (2, 5063), (2, 5251)}
PATCH_ARMS = ('repair', 'reverse', 'counterfactual', 'clean_self', 'treated_self', 'neighbor')


def _path(relative):
    path = (exp.HERE / relative).resolve()
    assert path.is_relative_to(exp.REPO.resolve()), 'Evidence must stay inside the project'
    return path


def _bound(path, evidence):
    assert path in evidence, f'Unbound evidence: {path}'
    actual = _path(path)
    assert exp.sha(actual) == evidence[path], f'Evidence hash changed: {path}'
    return exp.read(actual)


def _check_evidence(evidence):
    assert isinstance(evidence, dict) and evidence, 'Empty evidence is not a passed review'
    for path, expected in evidence.items():
        assert exp.sha(_path(path)) == expected, path


def validate_formal_authorization(auth, stage):
    """Run before model loading as well as immediately before formal execution."""
    assert stage in ('development', 'confirmation', 'mechanism', 'patch')
    assert auth['status'] == 'authorized' and auth['experiment'] == exp.HERE.name
    assert auth.get('formal_execution_authorized') is True and stage in auth['allowed_stages']
    assert auth['maximum_workers'] == 2 and auth['user_instruction']
    assert auth.get('panel', 'development') in ('development', 'confirmation')
    assert stage != 'development' or auth.get('panel', 'development') == 'development'
    freeze = _path(auth['freeze_path'])
    assert exp.sha(freeze) == auth['freeze_sha256']
    exp.check(freeze)
    evidence = auth['required_evidence']
    _check_evidence(evidence)
    preflight = _bound(auth['preflight_evidence_path'], evidence)
    review = _bound(auth['data_review_path'], evidence)
    cpu = _bound(auth['cpu_evidence_path'], evidence)
    assert preflight['status'] == review['status'] == cpu['status'] == 'passed'
    assert cpu['tests_run'] > 0 and cpu['failures'] == cpu['errors'] == cpu['skipped'] == 0
    assert cpu['source_hashes']
    for name, expected in cpu['source_hashes'].items():
        assert exp.sha(exp.REPO / name) == expected, 'CPU-tested source changed'
    assert review['experiment'] == exp.HERE.name
    assert review.get('confirmation_model_outputs_read') is False
    for name in ('development', 'confirmation', 'anchors'):
        path = exp.HERE / 'data' / f'{name}.json'
        assert review['file_hashes'][str(path.relative_to(exp.REPO))] == exp.sha(path)
    assert preflight['freeze_sha256'] == auth['freeze_sha256']
    gate = _bound(auth['stage_gate_path'], evidence)
    assert gate['status'] == 'passed' and gate['stage'] == stage
    assert gate['freeze_sha256'] == auth['freeze_sha256']
    _check_evidence(gate['evidence_hashes'])
    for name in ('preflight_evidence_path', 'data_review_path', 'cpu_evidence_path'):
        assert gate['evidence_hashes'][auth[name]] == evidence[auth[name]]
    if stage == 'development':
        return None
    selection = _bound(auth['selection_path'], evidence)
    assert gate['evidence_hashes'][auth['selection_path']] == evidence[auth['selection_path']]
    assert selection['status'] == 'locked' and selection['experiment'] == exp.HERE.name
    assert selection['freeze_sha256'] == auth['freeze_sha256']
    _check_evidence(selection['evidence_hashes'])
    assert gate.get('measurement_usable') is True
    if stage == 'confirmation':
        assert gate.get('interpretation_locked') is True and gate.get('selection_locked') is True
        assert gate.get('confirmation_outputs_previously_unseen') is True
    _validate_selection(selection)
    if stage == 'confirmation' or auth.get('panel') == 'confirmation':
        assert selection['confirmation_item_ids'] == [r['id'] for r in exp.items('confirmation')]
    if stage in ('mechanism', 'patch') and auth.get('panel') == 'confirmation':
        locked = _bound(auth['confirmation_lock_path'], evidence)
        assert gate['evidence_hashes'][auth['confirmation_lock_path']] == evidence[auth['confirmation_lock_path']]
        assert locked['status'] == 'passed' and locked['stage'] == 'confirmation'
        assert locked['freeze_sha256'] == auth['freeze_sha256']
        assert locked.get('interpretation_locked') is True and locked.get('selection_locked') is True
        assert locked.get('confirmation_outputs_previously_unseen') is True  # Historical first-opening gate.
        assert locked['evidence_hashes'][auth['selection_path']] == evidence[auth['selection_path']]
        _check_evidence(locked['evidence_hashes'])
        if stage == 'patch':
            _source_manifest(auth, selection)
    return selection


def _source_manifest(auth, selection):
    evidence = auth['required_evidence']
    manifest = _bound(auth['source_manifest_path'], evidence)
    gate = _bound(auth['stage_gate_path'], evidence)
    assert gate['evidence_hashes'][auth['source_manifest_path']] == evidence[auth['source_manifest_path']]
    assert manifest['status'] == 'locked' and manifest['panel'] == 'confirmation'
    assert manifest['freeze_sha256'] == auth['freeze_sha256']
    assert manifest['selection_sha256'] == evidence[auth['selection_path']]
    _check_evidence(manifest['evidence_hashes'])
    wanted = {c['condition_id'] for c in selection['patch_candidates']}
    assert set(manifest['sources']) == wanted
    condition_rows = {r['condition']['id']: r['condition'] for r in selection['conditions']}
    items = {r['id']: r for r in exp.items('confirmation')}
    for condition_id, sources in manifest['sources'].items():
        assert set(sources) == set(selection['confirmation_item_ids'])
        for item_id, source in sources.items():
            assert manifest['evidence_hashes'][source['path']] == source['sha256']
            assert exp.sha(_path(source['path'])) == source['sha256']
            payload = _source_payload(source, items[item_id], exp.engine_condition(condition_rows[condition_id]), manifest['evidence_hashes'])
            assert payload['evaluation_panel'] == 'confirmation'
    return manifest


def _validate_selection(selection):
    rows = {r['id']: r for r in exp.items('development') + exp.items('anchors')}
    available = {c['id']: c for c in exp.conditions('development')}
    conditions = selection['conditions']
    assert 1 <= len(conditions) <= 6
    assert len({c['condition']['id'] for c in conditions}) == len(conditions)
    early = other = splits = 0
    for row in conditions:
        condition = row['condition']
        assert condition['kind'] != 'clean' and re.fullmatch(r'[A-Za-z0-9_.+\-]+', condition['id'])
        if condition['kind'] == 'native' and (condition['layer'], condition['channel']) in EARLY_POINTS:
            early += 1
            assert condition['dose'] in exp.DOSES
            assert condition['id'] == f'N_L{condition["layer"]:02d}_C{condition["channel"]}_D{condition["dose"]:+g}'
        else:
            other += 1
            assert condition == available.get(condition['id']) and condition['layer'] >= 12
        assert row['item_ids'] and len(set(row['item_ids'])) == len(row['item_ids'])
        assert set(row['item_ids']) <= rows.keys(), 'Mechanism cannot expose confirmation outputs'
        assert set(row['source_records']) == set(row['item_ids'])
        for item_id, source in row['source_records'].items():
            assert selection['evidence_hashes'][source['path']] == source['sha256']
            assert exp.sha(_path(source['path'])) == source['sha256']
            _source_payload(source, rows[item_id], exp.engine_condition(condition), selection['evidence_hashes'])
        assert type(row.get('first_step_split', False)) is bool
        splits += row.get('first_step_split', False)
        # Diagnostics remain paired; selecting only the convenient fact is forbidden.
        selected = [rows[i] for i in row['item_ids']]
        for base in {r['base_id'] for r in selected if r['panel'] == 'diagnostic'}:
            assert {r['fact_version'] for r in selected if r['base_id'] == base} == {0, 1}
    assert early <= 3 and other <= 3 and splits <= 3
    candidates = selection.get('patch_candidates', [])
    assert len(candidates) <= 4 and len({c['id'] for c in candidates}) == len(candidates)
    counts = Counter(c['symptom'] for c in candidates)
    assert len(counts) <= 2 and all(n <= 2 for n in counts.values())
    selected_by_id = {c['condition']['id']: c for c in conditions}
    for candidate in candidates:
        assert re.fullmatch(r'[A-Za-z0-9_.+\-]+', candidate['id'])
        source = selected_by_id[candidate['condition_id']]
        assert candidate['item_ids'] and set(candidate['item_ids']) <= set(source['item_ids'])
        for base in {rows[i]['base_id'] for i in candidate['item_ids'] if rows[i]['panel'] == 'diagnostic'}:
            assert {rows[i]['fact_version'] for i in candidate['item_ids'] if rows[i]['base_id'] == base} == {0, 1}
        assert set(candidate['source_records']) == set(candidate['item_ids'])
        assert type(candidate['prediction_step']) is int and 0 <= candidate['prediction_step'] < 128
        for site in (candidate, candidate['neighbor']):
            assert type(site['layer']) is int and 0 <= site['layer'] < 32
            assert site['component'] in ('attention', 'mlp')
        assert (candidate['layer'], candidate['component']) != (candidate['neighbor']['layer'], candidate['neighbor']['component'])
        for item_id, source in candidate['source_records'].items():
            assert source.get('format', 'formal_v1') == 'formal_v1', 'Patch sources must be current formal full records'
            assert selection['evidence_hashes'][source['path']] == source['sha256']
            assert exp.sha(_path(source['path'])) == source['sha256']
            _source_payload(source, rows[item_id], exp.engine_condition(selected_by_id[candidate['condition_id']]['condition']), selection['evidence_hashes'])


def _source_payload(identity, item, condition, evidence):
    """Normalize only explicit supported source schemas; never mix old Q calibration with new facts."""
    assert evidence[identity['path']] == identity['sha256']
    source = exp.read(_path(identity['path']))
    if identity.get('format', 'formal_v1') == 'formal_v1':
        record_verify(source)
        assert source['item_id'] == item['id'] and source['item'] == item
        assert source['spec']['kind'] == 'generation' and source['spec']['mode'] == 'full'
        assert source['effective_condition'] == condition
        assert not source['generation']['forced_prefix_tokens']
        return {'context': source['context'], 'reference': source['reference'], 'generation': source['generation'],
                'evaluation_panel': source['evaluation_panel']}
    assert identity['format'] == 'legacy_layer_survey_v1'
    assert item['panel'] == 'anchor' and condition['kind'] == 'native' and condition['dose'] == 1.0
    old_contract = _bound(identity['contract_path'], evidence)
    assert identity['contract_path'].endswith('layer-survey-toy-v1-2026-10-27/contract.json')
    assert old_contract['instruction'] == item['instruction']
    assert source['status'] == 'completed' and source['model_id'] == '4b'
    assert source['question_id'] == item['id'] and source['prompt'] == item['prompt']
    assert all(source['intervention'][key] == condition[key] for key in ('layer', 'channel', 'dose'))
    assert source['calibration']['context_sha256'] == text_hash(source['context'])
    assert source['context'].startswith('<|im_start|>user\n' + item['user_message'] + '<|im_end|>\n')
    output = source['output']
    assert output['max_new_tokens'] == 128 and output['token_sha256'] == token_hash(output['token_ids'])
    assert output['input_token_sha256'] == source['calibration']['input_token_sha256']
    return {'context': source['context'], 'reference': source['calibration'], 'generation': output,
            'evaluation_panel': 'historical_anchor'}


def tokenizer_check(tokenizer, rows):
    contexts = exp.contexts_for(tokenizer, rows)
    checked = []
    for row in rows:
        suffixes = [exact_pair(tokenizer, contexts[row['id']], choice)[1] for choice in row['choices']]
        if suffixes:
            assert len(suffixes) == 2 and len(suffixes[0]) == len(suffixes[1]), row['id']
        checked.append({'id': row['id'], 'prompt_tokens': len(encode_text(tokenizer, contexts[row['id']])),
                        'candidate_token_lengths': [len(s) for s in suffixes]})
    return contexts, checked


def plan(stage, gpu, selection=None, panel='development'):
    assert gpu in (0, 1)
    result = []
    if stage in ('development', 'confirmation'):
        for row in exp.assigned(exp.items(stage), gpu):
            for condition in exp.conditions(stage):
                result.append({'key': f'{row["id"]}__{condition["id"]}__full', 'kind': 'generation',
                    'item_id': row['id'], 'condition': condition, 'mode': 'full'})
    else:
        all_rows = exp.items('confirmation') if panel == 'confirmation' else exp.items('development') + exp.items('anchors')
        assigned = {r['id'] for r in exp.assigned(all_rows, gpu)}
        selected = {r['condition']['id']: r for r in selection['conditions']}
        if stage == 'mechanism':
            for chosen in selected.values():
                condition = chosen['condition']
                item_ids = selection['confirmation_item_ids'] if panel == 'confirmation' else chosen['item_ids']
                for item_id in item_ids:
                    if item_id not in assigned:
                        continue
                    modes = ['full', 'prefill', 'decode']
                    if chosen.get('first_step_split'):
                        modes += ['prompt_last', 'prompt_except_last']
                    for mode in modes:
                        result.append({'key': f'{item_id}__{condition["id"]}__{mode}', 'kind': 'generation',
                            'item_id': item_id, 'condition': condition, 'mode': mode})
                    for fork in (4, 16):
                        for branch in ('continue', 'withdraw', 'rebuild'):
                            result.append({'key': f'{item_id}__{condition["id"]}__fork{fork:03d}_{branch}',
                                'kind': 'branch', 'item_id': item_id, 'condition': condition,
                                'fork_step': fork, 'branch': branch, 'mode': 'full'})
        else:
            assert stage == 'patch' and selection['patch_candidates'], 'No locked patch candidates'
            for candidate in selection['patch_candidates']:
                item_ids = selection['confirmation_item_ids'] if panel == 'confirmation' else candidate['item_ids']
                for item_id in item_ids:
                    if item_id in assigned:
                        for arm in PATCH_ARMS:
                            result.append({'key': f'{item_id}__{candidate["id"]}__{arm}', 'kind': 'patch',
                                'item_id': item_id, 'condition': selected[candidate['condition_id']]['condition'],
                                'candidate_id': candidate['id'], 'arm': arm, 'mode': 'full'})
    assert len({r['key'] for r in result}) == len(result)
    return result


def _generation_check(result, context, condition, reference):
    assert result['status'] == 'completed'
    tokens = result['token_ids']
    assert tokens and all(type(t) is int and t >= 0 for t in tokens)
    assert len(tokens) <= 128 and len(tokens) == result['generated_token_count']
    assert 1 <= result['max_new_tokens'] <= 128
    assert result['token_sha256'] == token_hash(tokens)
    assert result['input_token_sha256'] == result['calibration']['input_token_sha256']
    assert result['calibration']['context_sha256'] == text_hash(context)
    assert result['calibration']['reference_calibration_sha256'] == control_digest(reference)
    assert result['condition'] == condition
    assert not any(t in (248044, 248046) for t in tokens[:-1])
    assert (tokens[-1] in (248044, 248046)) == (result['end_reason'] == 'eos_token')
    assert result['end_reason'] == 'eos_token' or len(tokens) == result['max_new_tokens']
    assert len(result['step_readouts']) == len(tokens)
    assert tokens == [r['actual_token_id'] for r in result['step_readouts']]


def record_verify(row):
    assert row['reference_sha256'] == control_digest(row['reference'])
    if row['status'] == 'not_applicable':
        assert row['reason'] and row['spec']['kind'] in ('branch', 'patch')
        return
    assert row['status'] == 'completed'
    _generation_check(row['generation'], row['context'], row['effective_condition'], row['reference'])
    assert row['generation']['max_new_tokens'] == 128
    assert row['generation']['mode'] == row['spec']['mode']
    candidates = row.get('candidates', [])
    expected_choices = row['item']['choices'] if row['spec']['kind'] == 'generation' else []
    assert [r['text'] for r in candidates] == expected_choices
    for choice in candidates:
        result = choice['result']
        _generation_check(result, row['context'], row['effective_condition'], row['reference'])
        assert result['continuation_token_ids'] == result['token_ids']
        assert len(result['token_logprobs']) == len(result['token_ids'])
        assert abs(sum(result['token_logprobs']) - result['loglikelihood']) < 1e-6
    if row['spec']['kind'] == 'patch':
        assert len(row['generation']['patch_audit']) == 1
        assert row['generation']['patch_audit'][0]['donor_id'] == row['donor']['id']


def _store(output, receipt, record):
    record_verify(record)
    relative = f'records/{record["spec"]["key"]}.json'
    exp.write(output / relative, record, immutable=True)
    receipt['record_hashes'][relative] = exp.sha(output / relative)
    receipt['last_record_at'] = record['created_at']
    exp.write(output / 'receipt.json', receipt)


def _base_record(stage, spec, item, context, reference):
    return {'schema': 1, 'stage': stage, 'spec': spec, 'item_id': item['id'], 'item': item,
            'context': context, 'reference_id': item['reference_id'], 'reference': reference,
            'reference_sha256': control_digest(reference), 'created_at': exp.utc()}


def _targets(tokenizer, context, item):
    return sorted({token for choice in item['choices'] for token in exact_pair(tokenizer, context, choice)[1]})


def _save_donor(engine, output, receipt, donor, name):
    vector_file, metadata_file = f'donors/{name}.pt', f'donors/{name}.json'
    path = output / vector_file
    path.parent.mkdir(exist_ok=True)
    assert not path.exists()
    engine.torch.save(donor['vector'], path)
    metadata = {k: v for k, v in donor.items() if k != 'vector'}
    metadata.update(vector_file=vector_file, vector_file_sha256=exp.sha(path))
    exp.write(output / metadata_file, metadata, immutable=True)
    for relative in (vector_file, metadata_file):
        receipt['asset_hashes'][relative] = exp.sha(output / relative)
    return metadata


def _branch_comparison(engine, output, receipt, spec, branches):
    key = f'{spec["item_id"]}__{spec["condition"]["id"]}__fork{spec["fork_step"]:03d}'
    if not branches:
        value = {'status': 'not_applicable', 'reason': 'source_ended_before_fork', 'key': key}
    else:
        assert set(branches) == {'continue', 'withdraw', 'rebuild'}
        step = spec['fork_step']
        prefixes = {result['step_readouts'][step]['prefix_token_sha256'] for _, result in branches.values()}
        assert len(prefixes) == 1, 'Cross-branch logits must share a complete input prefix'
        union = sorted({result['token_ids'][step] for _, result in branches.values()})
        value = {'status': 'completed', 'key': key, 'fork_step': step,
                 'prefix_token_sha256': prefixes.pop(), 'actual_token_union': union, 'branches': {}}
        for kind, (logits, result) in branches.items():
            logprobs = engine.torch.log_softmax(logits, dim=-1)
            value['branches'][kind] = {'actual_token_id': result['token_ids'][step],
                'scores': {str(t): {'logit': float(logits[t]), 'logprob': float(logprobs[t])} for t in union}}
    relative = f'branch-comparisons/{key}.json'
    exp.write(output / relative, value, immutable=True)
    receipt['asset_hashes'][relative] = exp.sha(output / relative)


def run_formal(engine, stage, gpu, output, receipt, auth):
    selection = validate_formal_authorization(auth, stage)
    output = Path(output)
    panel = 'confirmation' if stage == 'confirmation' else auth.get('panel', 'development')
    receipt['panel'] = panel
    specs = plan(stage, gpu, selection, panel)
    rows = exp.items(stage) if stage in ('development', 'confirmation') else exp.items('confirmation') if panel == 'confirmation' else exp.items('development') + exp.items('anchors')
    by_id = {r['id']: r for r in rows}
    contexts, token_check = tokenizer_check(engine.tokenizer, rows)
    exp.write(output / 'plan.json', specs, immutable=True)
    exp.write(output / 'tokenizer-check.json', token_check, immutable=True)
    for name in ('plan.json', 'tokenizer-check.json'):
        receipt['asset_hashes'][name] = exp.sha(output / name)
    needed = {by_id[s['item_id']]['reference_id'] for s in specs}
    references = {}
    calibration_started = time.monotonic()
    for reference_id in sorted(needed):
        reference = engine.calibrate([contexts[reference_id]])[0]
        references[reference_id] = reference
        name = f'calibrations/{reference_id}.json'
        exp.write(output / name, reference, immutable=True)
        receipt['asset_hashes'][name] = exp.sha(output / name)
    calibration_seconds = time.monotonic() - calibration_started
    completed, full, branch_states, fork_logits = [], {}, {}, {}
    selected_by_id = {r['condition']['id']: r for r in selection['conditions']} if selection else {}
    candidates = {r['id']: r for r in selection.get('patch_candidates', [])} if selection else {}
    manifest = _source_manifest(auth, selection) if stage == 'patch' and panel == 'confirmation' else None
    verified_sources = {}
    for spec in specs:
        item = by_id[spec['item_id']]
        context, reference = contexts[item['id']], references[item['reference_id']]
        condition = exp.engine_condition(spec['condition'])
        record = _base_record(stage, spec, item, context, reference)
        record['evaluation_panel'] = panel
        record['effective_condition'] = condition
        targets = _targets(engine.tokenizer, context, item)
        if spec['kind'] == 'generation':
            historical = None
            if stage == 'mechanism' and panel == 'development':
                identity = selected_by_id[condition['id']]['source_records'][item['id']]
                historical = _source_payload(identity, item, condition, selection['evidence_hashes'])
                assert historical['context'] == context and historical['reference'] == reference
                record['selection_source'] = identity
            result = engine.generate_one(context, reference, condition, mode=spec['mode'], target_token_ids=targets)
            if historical is not None and spec['mode'] == 'full':
                assert result['token_ids'] == historical['generation']['token_ids'], 'Frozen source did not replay'
            record.update(status='completed', generation=result, candidates=[{'text': choice,
                'result': engine.score_one(context, choice, reference, condition, mode=spec['mode'])}
                for choice in item['choices']])
            if spec['mode'] == 'full':
                full[(item['id'], spec['condition']['id'])] = result
        elif spec['kind'] == 'branch':
            source = full[(item['id'], spec['condition']['id'])]
            prefix = source['token_ids'][:spec['fork_step']]
            record.update(source_token_sha256=source['token_sha256'], fork_step=spec['fork_step'])
            fork_key = (item['id'], condition['id'], spec['fork_step'])
            fork_logits.setdefault(fork_key, {})
            if len(prefix) < spec['fork_step'] or any(t in engine.stop_ids for t in prefix):
                record.update(status='not_applicable', reason='source_ended_before_fork', prefix_tokens=prefix)
            else:
                result = engine.branch(context, reference, condition, prefix, kind=spec['branch'], target_token_ids=targets,
                                       retain_fork_logits=True)
                logits = result.pop('_fork_logits')
                fork_logits[fork_key][spec['branch']] = (logits, result)
                record.update(status='completed', generation=result, candidates=[])
                assert result['token_ids'][:spec['fork_step']] == prefix
                if spec['branch'] == 'continue':
                    assert result['token_ids'] == source['token_ids'], 'Continue must reproduce the full source'
                    branch_states[(item['id'], condition['id'], spec['fork_step'])] = result['cache_fingerprints'][str(spec['fork_step'])]
                elif spec['branch'] == 'withdraw':
                    assert result['cache_fingerprints'][str(spec['fork_step'])] == branch_states[(item['id'], condition['id'], spec['fork_step'])], 'Withdrawal began from a different historical state'
            if spec['branch'] == 'rebuild':
                _branch_comparison(engine, output, receipt, spec, fork_logits.pop(fork_key))
        else:
            candidate = candidates[spec['candidate_id']]
            source_identity = manifest['sources'][candidate['condition_id']][item['id']] if manifest else candidate['source_records'][item['id']]
            source_key = (item['id'], spec['condition']['id'])
            if source_key not in verified_sources:
                source = exp.read(_path(source_identity['path']))
                record_verify(source)
                assert source['item_id'] == item['id'] and source['context'] == context
                assert source['evaluation_panel'] == panel
                assert source['reference'] == reference and source['effective_condition'] == condition
                assert source['generation']['mode'] == 'full' and not source['generation']['forced_prefix_tokens']
                replay = engine.generate_one(context, reference, condition, target_token_ids=targets)
                assert replay['token_ids'] == source['generation']['token_ids'], 'Patch source no longer exactly replays'
                name = f'source-replays/{item["id"]}__{spec["condition"]["id"]}.json'
                exp.write(output / name, replay, immutable=True)
                receipt['asset_hashes'][name] = exp.sha(output / name)
                verified_sources[source_key] = source['generation']
            source = verified_sources[source_key]
            step = candidate['prediction_step']
            prefix = source['token_ids'][:step]
            record.update(source_record=source_identity, source_token_sha256=source['token_sha256'])
            if len(prefix) < step or any(t in engine.stop_ids for t in prefix):
                record.update(status='not_applicable', reason='source_ended_before_patch_position')
            elif spec['arm'] == 'counterfactual' and item['panel'] != 'diagnostic':
                record.update(status='not_applicable', reason='open_anchor_has_no_counterfactual_fact')
            else:
                donor_item = item
                if spec['arm'] == 'counterfactual':
                    donor_item = next(r for r in rows if r['base_id'] == item['base_id'] and r['fact_version'] != item['fact_version'])
                donor_context = contexts[donor_item['id']]
                record['donor_item_id'] = donor_item['id']
                record['prompt_token_lengths'] = {'donor': len(encode_text(engine.tokenizer, donor_context)),
                                                  'recipient': len(encode_text(engine.tokenizer, context))}
                if record['prompt_token_lengths']['donor'] != record['prompt_token_lengths']['recipient']:
                    record.update(status='not_applicable', reason='counterfactual_prompt_token_length_mismatch')
                else:
                    site = candidate['neighbor'] if spec['arm'] == 'neighbor' else candidate
                    donor_condition = condition if spec['arm'] in ('reverse', 'treated_self') else CLEAN
                    recipient = CLEAN if spec['arm'] in ('reverse', 'clean_self') else condition
                    donor = engine.prepare_donor(donor_context, reference, donor_condition,
                        layer=site['layer'], component=site['component'], prediction_step=step,
                        prefix_tokens=prefix, donor_id=spec['key'])
                    record['donor'] = _save_donor(engine, output, receipt, donor, spec['key'])
                    patch = {'layer': site['layer'], 'component': site['component'],
                             'prediction_step': step, 'donor': donor}
                    result = engine.branch(context, reference, recipient, prefix,
                        kind='rebuild' if recipient['kind'] == 'clean' else 'continue',
                        target_token_ids=targets, patch=patch)
                    record.update(status='completed', effective_condition=recipient, generation=result, candidates=[])
        _store(output, receipt, record)
        completed.append(record)
    receipt['formal_summary'] = {'expected_records': len(specs), 'records': len(completed),
        'completed_generations': sum(r['status'] == 'completed' for r in completed),
        'not_applicable': sum(r['status'] == 'not_applicable' for r in completed),
        'candidate_groups': sum(bool(r.get('candidates')) for r in completed),
        'candidate_continuations': sum(len(r.get('candidates', [])) for r in completed),
        'technical_continue_replays': sum(r['status'] == 'completed' and r['spec'].get('branch') == 'continue' for r in completed)}
    receipt['formal_cost'] = {'calibration_seconds': calibration_seconds, 'calibration_prompts': len(references),
        'generation_and_branch_seconds': sum(r.get('generation', {}).get('seconds', 0) for r in completed),
        'candidate_seconds': sum(c['result']['seconds'] for r in completed for c in r.get('candidates', [])),
        'donor_seconds': sum(r.get('donor', {}).get('source_seconds', 0) for r in completed),
        'source_replay_count': len(verified_sources),
        'source_replay_seconds': sum(exp.read(output / relative)['seconds'] for relative in receipt['asset_hashes'] if relative.startswith('source-replays/')),
        'branch_seconds_include_prefix_replay': True}
    exp.write(output / 'receipt.json', receipt)


def verify_formal_records(path, receipt):
    path = Path(path)
    auth = exp.read(path / 'authorization.json')
    selection = validate_formal_authorization(auth, receipt['stage'])
    execution = exp.read(path / 'execution.json')
    for key, value in execution.items():
        if key not in ('status', 'record_hashes', 'asset_hashes'):
            assert receipt[key] == value, f'Immutable execution changed: {key}'
    panel = 'confirmation' if receipt['stage'] == 'confirmation' else auth.get('panel', 'development')
    assert receipt['panel'] == panel
    specs = plan(receipt['stage'], receipt['gpu'], selection, panel)
    assert exp.read(path / 'plan.json') == specs
    expected = {f'records/{s["key"]}.json': s for s in specs}
    assert set(receipt['record_hashes']) == expected.keys(), 'Missing or extra formal records'
    assert {str(p.relative_to(path)) for p in (path / 'records').glob('*.json')} == expected.keys()
    rows = []
    item_rows = exp.items(receipt['stage']) if receipt['stage'] in ('development', 'confirmation') else exp.items('confirmation') if panel == 'confirmation' else exp.items('development') + exp.items('anchors')
    by_id = {r['id']: r for r in item_rows}
    for relative, spec in expected.items():
        assert exp.sha(path / relative) == receipt['record_hashes'][relative]
        record = exp.read(path / relative)
        assert record['spec'] == spec and record['stage'] == receipt['stage']
        assert record['item_id'] == spec['item_id']
        assert record['evaluation_panel'] == panel
        assert record['item'] == by_id[spec['item_id']]
        assert record['reference'] == exp.read(path / 'calibrations' / f'{record["reference_id"]}.json')
        effective = CLEAN if spec['kind'] == 'patch' and spec['arm'] in ('reverse', 'clean_self') else exp.engine_condition(spec['condition'])
        if record['status'] == 'completed':
            assert record['effective_condition'] == effective
        record_verify(record)
        rows.append(record)
    summary = {'expected_records': len(specs), 'records': len(rows),
        'completed_generations': sum(r['status'] == 'completed' for r in rows),
        'not_applicable': sum(r['status'] == 'not_applicable' for r in rows),
        'candidate_groups': sum(bool(r.get('candidates')) for r in rows),
        'candidate_continuations': sum(len(r.get('candidates', [])) for r in rows),
        'technical_continue_replays': sum(r['status'] == 'completed' and r['spec'].get('branch') == 'continue' for r in rows)}
    assert receipt['formal_summary'] == summary
    indexed = {r['spec']['key']: r for r in rows}
    comparisons = set()
    for row in rows:
        spec = row['spec']
        if spec['kind'] != 'branch':
            continue
        source = indexed[f'{spec["item_id"]}__{spec["condition"]["id"]}__full']['generation']
        fork = spec['fork_step']
        prefix = source['token_ids'][:fork]
        applicable = len(prefix) == fork and not any(t in (248044, 248046) for t in prefix)
        assert (row['status'] == 'completed') == applicable, 'Invalid branch applicability classification'
        assert row['source_token_sha256'] == source['token_sha256']
        if applicable:
            assert row['generation']['forced_prefix_tokens'] == prefix
            assert row['generation']['token_ids'][:fork] == prefix
            if spec['branch'] == 'continue':
                assert row['generation']['token_ids'] == source['token_ids']
            if spec['branch'] == 'withdraw':
                continued = indexed[f'{spec["item_id"]}__{spec["condition"]["id"]}__fork{fork:03d}_continue']
                assert row['generation']['cache_fingerprints'][str(fork)] == continued['generation']['cache_fingerprints'][str(fork)]
        comparison = f'branch-comparisons/{spec["item_id"]}__{spec["condition"]["id"]}__fork{fork:03d}.json'
        assert comparison in receipt['asset_hashes'] and exp.sha(path / comparison) == receipt['asset_hashes'][comparison]
        comparisons.add(comparison)
        value = exp.read(path / comparison)
        assert (value['status'] == 'completed') == applicable
        if applicable:
            actual = row['generation']['token_ids'][fork]
            assert value['branches'][spec['branch']]['actual_token_id'] == actual
            assert actual in value['actual_token_union']
            assert set(value['branches'][spec['branch']]['scores']) == {str(t) for t in value['actual_token_union']}
    assert {n for n in receipt['asset_hashes'] if n.startswith('branch-comparisons/')} == comparisons
    return {'status': 'passed', **summary}
