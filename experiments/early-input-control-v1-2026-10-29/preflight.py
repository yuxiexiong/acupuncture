"""Bounded mechanical controls and measured timings; never launches formal work."""
from copy import deepcopy
import time

import experiment as ex


def tokenizer_check(engine, rows, contexts):
    from control_engine import exact_pair, encode_text, token_hash
    result = {}
    for row in rows:
        context = contexts[row['id']]
        prompt = encode_text(engine.tokenizer, context)
        candidates = []
        for choice in row.get('choices', []):
            prefix, tail = exact_pair(engine.tokenizer, context, choice)
            assert prefix == prompt
            candidates.append(tail)
        if candidates:
            assert len(candidates) == 2 and candidates[0] != candidates[1]
            assert len(candidates[0]) == len(candidates[1]), f'Unequal candidate lengths: {row["id"]}'
        result[row['id']] = {'input_token_ids': prompt, 'input_token_sha256': token_hash(prompt),
            'candidate_token_ids': candidates}
    return result


def verify_output(row, reference, condition, context, mode='full'):
    from control_engine import text_hash, token_hash, digest, selection_mask
    if row['status'] == 'not_applicable':
        return
    assert row['status'] == 'completed' and row['condition'] == condition and row['mode'] == mode
    tokens = row['token_ids']
    assert 1 <= len(tokens) <= 128 and len(tokens) == row['generated_token_count']
    assert row['token_sha256'] == token_hash(tokens)
    assert row['calibration']['context_sha256'] == text_hash(context)
    assert row['calibration']['reference_calibration_sha256'] == digest(reference)
    assert row['calibration']['residual_scales'] == reference['residual_scales']
    assert len(row['step_readouts']) == len(tokens)
    assert all(r['actual_token_id'] == t for r, t in zip(row['step_readouts'], tokens))
    assert not any(t in (248044, 248046) for t in tokens[:-1])
    if row['end_reason'] == 'eos_token':
        assert tokens[-1] in (248044, 248046)
    else:
        assert len(tokens) == row['max_new_tokens']
    audits = row['write_audit']
    assert len(audits) == (0 if condition['kind'] == 'clean' else len(tokens))
    for i, audit in enumerate(audits):
        active = row['branch_kind'] != 'rebuild' and not (
            row['branch_kind'] == 'withdraw' and i >= row['fork_step'])
        expected = selection_mask(mode, i, audit['width'], row['context_token_count'], active)
        assert audit['prediction_step'] == i and audit['mask'] == expected
        assert audit['positions'] == sum(expected) and audit['target_values_match']
        assert audit['masked_positions_unchanged'] and audit['layer'] == condition['layer']
        if condition['kind'] == 'native':
            assert audit['channel'] == condition['channel'] and audit['non_target_values_unchanged']
    return True


def run_preflight(engine, gpu, output, receipt):
    from control_engine import exact_pair, digest, token_hash
    all_rows = ex.items('development') + ex.items('anchors') + ex.items('confirmation')
    by_id = {r['id']: r for r in all_rows}
    contexts = ex.contexts_for(engine.tokenizer, all_rows)
    tokens = tokenizer_check(engine, all_rows, contexts)
    references = {}
    counters = {'generations_or_branches': 0, 'candidate_continuations': 0, 'donor_replays': 0,
                'calibration_prompts': 0, 'legacy_generations': 0, 'full_forward_checks': 0}
    limits = ex.read(ex.HERE / 'contract.json')['preflight_limits_per_worker']
    checks, benchmark_ids, donor_seconds = [], [], []
    save_seconds, calibration_seconds, pending_logits = {}, {}, {}

    def budget(key):
        counters[key] += 1
        assert counters[key] <= limits[key], f'Preflight budget exceeded: {key}'

    def ref(item):
        assert item not in {r['id'] for r in ex.items('confirmation')}, 'No confirmation model outputs in preflight'
        base = by_id[item]['base_id']
        if base not in references:
            budget('calibration_prompts')
            reference_id = by_id[item]['reference_id']
            started = time.monotonic()
            references[base] = engine.calibrate([contexts[reference_id]])[0]
            calibration_seconds[base] = time.monotonic() - started
        return references[base]

    def save(name, value):
        started = time.monotonic()
        filename = f'records/{name}.json'
        ex.write(output / filename, value, immutable=True)
        receipt['record_hashes'][filename] = ex.sha(output / filename)
        receipt.update(completed_records=len(receipt['record_hashes']), latest_record_at=ex.utc(), counters=counters.copy())
        ex.write(output / 'receipt.json', receipt)
        save_seconds[name] = time.monotonic() - started
        print(f'preflight gpu={gpu} record={name} streams={counters["generations_or_branches"]}', flush=True)
        return value

    def take(name, item, condition, mode='full', branch=None, patch=None, score=True):
        budget('generations_or_branches')
        condition = ex.engine_condition(condition)
        reference, context = ref(item), contexts[item]
        target_ids = sorted({t for candidate in tokens[item]['candidate_token_ids'] for t in candidate})
        started = time.monotonic()
        if branch is None:
            generated = engine.generate_one(context, reference, condition, mode=mode,
                target_token_ids=target_ids, patch=patch)
        else:
            generated = engine.branch(context, reference, condition, branch['prefix'], kind=branch['kind'],
                mode=mode, target_token_ids=target_ids, patch=patch, retain_fork_logits=True)
            if '_fork_logits' in generated:
                pending_logits[name] = generated.pop('_fork_logits')
        verify_output(generated, reference, condition, context, mode)
        choices = []
        if score and branch is None and patch is None:
            for choice in by_id[item].get('choices', []):
                budget('candidate_continuations')
                detail = engine.score_one(context, choice, reference, condition, mode=mode)
                verify_output(detail, reference, condition, context, mode)
                choices.append(detail)
        row = {'status': generated['status'], 'item': by_id[item], 'context': context,
            'reference_calibration': reference, 'condition': condition, 'mode': mode,
            'output': generated, 'choices': choices, 'wall_seconds': time.monotonic()-started,
            'finished_at': ex.utc(), 'purpose': 'technical_preflight_not_formal_science'}
        return save(name, row)

    def legacy(name, item, condition):
        budget('generations_or_branches'); counters['legacy_generations'] += 1
        row = engine.legacy_generate(contexts[item], ref(item), condition)
        return save(name, {'item_id': item, 'condition': condition, 'legacy_output': row})['legacy_output']

    def same(a, b, label):
        assert a['token_ids'] == b['token_ids'], label
        scope = 'token_ids'
        if 'step_readouts' in a and 'step_readouts' in b:
            assert [r['logits_sha256'] for r in a['step_readouts']] == [
                r['logits_sha256'] for r in b['step_readouts']], label + '_logits'
            scope = 'token_ids_and_captured_logits'
        checks.append({'check': label, 'status': 'passed', 'tokens': len(a['token_ids']), 'scope': scope})

    clean = {'id': 'clean', 'kind': 'clean', 'dose': 0.0}
    n0 = {'id': 'anchor_L0_C4146_D+1', 'kind': 'native', 'layer': 0, 'channel': 4146, 'dose': 1.}
    n2 = {'id': 'anchor_L2_C5251_D+1', 'kind': 'native', 'layer': 2, 'channel': 5251, 'dose': 1.}
    loop = {'id': 'anchor_L2_C5063_D+1', 'kind': 'native', 'layer': 2, 'channel': 5063, 'dose': 1.}
    base = take('clean-q04', 'Q04', clean, score=False)['output']
    same(base, legacy('legacy-clean-q04', 'Q04', clean), 'new_vs_legacy_clean_tokens')
    zero = dict(n0, id='zero-native', dose=0.)
    same(base, take('zero-native', 'Q04', zero, score=False)['output'], 'zero_native_exact')
    vector_zero = {'id': 'zero-vector', 'kind': 'direction', 'layer': 0, 'direction_id': 'V0', 'dose': 0.}
    same(base, take('zero-vector', 'Q04', vector_zero, score=False)['output'], 'zero_direction_exact')
    full = {}
    for label, item, condition in [('eos', 'Q04', n0), ('loop', 'Q05', n2),
                                   ('negative', 'Q05', dict(n2, id='negative', dose=-1.))]:
        row = take('native-' + label, item, condition, score=False)['output']
        same(row, legacy('legacy-' + label, item, condition), 'new_vs_legacy_' + label)
        full[label] = row
    same(base, take('restored-clean', 'Q04', clean, score=False)['output'], 'restored_clean_exact')
    loop_full = take('timing-full', 'Q04', loop, score=False)['output']
    for mode in ('prefill', 'decode', 'prompt_last', 'prompt_except_last'):
        take('timing-' + mode, 'Q04', loop, mode=mode, score=False)
    for k in (4, 16):
        source = full['loop']
        if len(source['token_ids']) <= k or any(t in engine.stop_ids for t in source['token_ids'][:k]):
            save(f'fork-{k}-unreachable', {'status': 'not_applicable', 'source': 'native-loop', 'fork_step': k})
            continue
        branches = {}
        for kind in ('continue', 'withdraw', 'rebuild'):
            branches[kind] = take(f'fork-{k}-{kind}', 'Q05', n2, score=False,
                branch={'prefix': source['token_ids'][:k], 'kind': kind})['output']
        same(source, branches['continue'], f'forced_continue_k{k}_exact')
        assert branches['continue']['cache_fingerprints'][str(k)] == branches['withdraw']['cache_fingerprints'][str(k)]
        assert branches['continue']['step_readouts'][:k] == branches['withdraw']['step_readouts'][:k]
        assert all(a['positions'] == 0 for a in branches['withdraw']['write_audit'][k:])
        assert all(a['positions'] == 0 for a in branches['rebuild']['write_audit'])
        checks.append({'check': f'fork_{k}_same_state_then_withdraw', 'status': 'passed',
            'cache_before_fork_sha256': branches['continue']['cache_fingerprints'][str(k)]['sha256'],
            'clean_rebuilt_sha256': branches['rebuild']['cache_fingerprints'][str(k)]['sha256']})
        union = sorted({r['token_ids'][k] for r in branches.values()})
        cross = {'fork_step': k, 'token_ids': union, 'rows': {}}
        for kind in branches:
            logits = pending_logits.pop(f'fork-{k}-{kind}')
            log_probs = engine.torch.log_softmax(logits.float(), -1)
            cross['rows'][kind] = {str(t): {'logit': float(logits[t]), 'logprob': float(log_probs[t])} for t in union}
        save(f'fork-{k}-cross-readout', cross)
    if len(base['token_ids']) > 4:
        prefix = base['token_ids'][:4]
        for kind in ('continue', 'withdraw', 'rebuild'):
            zero_branch = take('zero-fork-' + kind, 'Q04', zero, score=False,
                branch={'prefix': prefix, 'kind': kind})['output']
            same(base, zero_branch, 'zero_branch_' + kind)
    assert engine.branch(contexts['Q04'], ref('Q04'), n0, [engine.stop_ids[0]])['status'] == 'not_applicable'
    checks.append({'check': 'no_branch_past_eos', 'status': 'passed'})

    # Donors use the same fact-pair calibration. No confirmation model output is generated.
    item, other = f'RD{gpu+1:02d}-f0-required', f'RD{gpu+1:02d}-f1-required'
    selected = ex.read(ex.HERE / 'selection.json')['selected'][0]['channels'][0]
    treatment = {'id': 'patch-native', 'kind': 'native', 'layer': 0, 'channel': selected, 'dose': 1.}
    clean_patch_source = take('patch-clean-source', item, clean, score=False)['output']
    bad_patch_source = take('patch-bad-source', item, treatment, score=False)['output']
    donors = {}
    for name, source_item, arm, component in [('clean', item, clean, 'attention'),
        ('bad', item, treatment, 'attention'), ('other_fact', other, clean, 'attention'),
        ('neighbor', item, clean, 'mlp')]:
        budget('donor_replays')
        donor = engine.prepare_donor(contexts[source_item], ref(item), arm, layer=1, component=component,
                                     prediction_step=0, donor_id=name)
        path = output / 'donors' / f'{name}.pt'
        path.parent.mkdir(exist_ok=True)
        assert not path.exists()
        engine.torch.save(donor, path)
        receipt['asset_hashes'][str(path.relative_to(output))] = ex.sha(path)
        donor_seconds.append(donor['source_seconds'])
        donors[name] = donor
    for name, arm, donor_name, component in [('repair', treatment, 'clean', 'attention'),
        ('reverse', clean, 'bad', 'attention'), ('other_fact', treatment, 'other_fact', 'attention'),
        ('self_clean', clean, 'clean', 'attention'), ('self_bad', treatment, 'bad', 'attention'),
        ('neighbor', treatment, 'neighbor', 'mlp')]:
        result = take('patch-' + name, item, arm, score=False, patch={'layer': 1, 'component': component,
            'prediction_step': 0, 'donor': donors[donor_name]})['output']
        assert len(result['patch_audit']) == 1 and result['patch_audit'][0]['other_positions_unchanged']
        if name.startswith('self_'):
            same(clean_patch_source if name == 'self_clean' else bad_patch_source, result, name + '_exact')
            assert result['patch_audit'][0]['delta_norm'] == 0
    checks.append({'check': 'six_patch_arms_donor_identity_and_actual_write', 'status': 'passed'})

    # Exact independent incremental reference; one-shot BF16 is a separate numerical diagnostic.
    context, reference = contexts[item], ref(item)
    for arm in (clean, treatment):
        for index, choice in enumerate(by_id[item]['choices']):
            budget('candidate_continuations')
            score = engine.score_one(context, choice, reference, arm, verify_logits=True)
            budget('candidate_continuations')
            manual = engine.manual_score_one(context, choice, reference, arm)
            assert manual['continuation_token_ids'] == score['continuation_token_ids']
            assert manual['logits_sha256'] == [r['logits_sha256'] for r in score['step_readouts']]
            assert manual['token_logprobs'] == score['token_logprobs']
            prefix, suffix = exact_pair(engine.tokenizer, context, choice)
            inputs = engine._inputs([prefix + suffix[:-1]])
            state = {'step': -1, 'write_audit': [], 'patch_audit': [], 'cache_fingerprints': {}}
            torch = engine.torch
            with torch.inference_mode(), engine._control_hooks(arm, reference, 'full', len(prefix+suffix[:-1]),
                    state, 0, 'continue', set(), None, None):
                logits = engine.model(**inputs, use_cache=False, logits_to_keep=len(suffix)).logits[0, -len(suffix):]
            lp = torch.log_softmax(logits, -1, dtype=torch.float32)
            expected = lp.gather(-1, torch.tensor(suffix, device=engine.device)[:, None]).flatten().tolist()
            difference = max(abs(a-b) for a, b in zip(expected, score['token_logprobs']))
            counters['full_forward_checks'] += 1
            assert counters['full_forward_checks'] <= 4
            assert counters['candidate_continuations'] + counters['full_forward_checks'] <= limits['candidate_continuations']
            save(f'candidate-check-{arm["id"]}-{index}', {'status': 'passed', 'max_difference_nats': difference,
                'full_token_logprobs': expected, 'incremental': score, 'independent_incremental': manual,
                'acceptance_basis': 'independent matching incremental path: exact full logits and token logprobs',
                'one_shot_comparison': 'diagnostic only: different sequence shapes/cache path; not used to relax exact incremental acceptance'})
            checks.append({'check': 'candidate_suffix_independent_incremental_exact', 'condition': arm['id'],
                           'candidate': index, 'status': 'passed', 'max_difference_nats': difference})

    for i, case in enumerate(ex.read(ex.HERE / 'readiness/preflight-cases-r01.json')['workers'][str(gpu)]['benchmarks']):
        name = f'benchmark-{i:03d}'
        take(name, case['item_id'], case['condition'])
        benchmark_ids.append(f'records/{name}.json')
    for name, value in [('tokens.json', tokens), ('calibrations.json', references), ('contexts.json', contexts)]:
        ex.write(output / name, value, immutable=True)
        receipt['asset_hashes'][name] = ex.sha(output / name)
    result = {'status': 'passed', 'checks': checks, 'counters': counters, 'benchmark_records': benchmark_ids,
        'donor_replay_seconds': donor_seconds, 'confirmation_model_outputs': 0,
        'save_seconds_by_record': save_seconds, 'calibration_seconds_by_base': calibration_seconds,
        'semantic_success_required': False, 'limits': limits}
    assert counters['candidate_continuations'] + counters['full_forward_checks'] <= limits['candidate_continuations']
    # A missing scientific branch is valid data, but cannot certify an unexercised implementation.
    for k in (4, 16):
        assert any(r['check'] == f'fork_{k}_same_state_then_withdraw' for r in checks), \
            f'No reachable real fork at {k}; preflight incomplete, retain evidence and revise technical fixtures separately'
    ex.write(output / 'preflight.json', result, immutable=True)
    receipt['asset_hashes']['preflight.json'] = ex.sha(output / 'preflight.json')
    return result
