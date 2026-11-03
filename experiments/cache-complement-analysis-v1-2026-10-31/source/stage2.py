"""All-layer cache-type difference (G) and stage-II cache-depth comparison (II-A, II-B).

Implements CONTRACT.zh-CN.md draft-r02. Imports never load a model. Every model-touching entry point
requires a frozen authorization file; nothing here authorizes a run.

Stage order (contract §1): audit -> g_preflight -> g_development, g_history -> (G lock) -> a_preflight -> a_scan
-> (A lock) -> b_preflight -> b_validate.

python stage2.py freeze PATH
python stage2.py run --stage STAGE --worker W --authorization AUTH --output DIR   (GPU = W % 2)
python stage2.py verify WORKER_DIR
python stage2.py launch --stage STAGE --authorization AUTH --output RUN_DIR
"""
import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
STAGE1 = HERE.parent / 'early-state-localization-v1-2026-10-29'
_spec = importlib.util.spec_from_file_location('stage1_localize', STAGE1 / 'localize.py')
L = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(L)
exp, SOURCE = L.exp, L.SOURCE

STAGE1_COMMIT = '34e5d4a4533d3cbbe3a0994b7d80d060bb336a9f'
POINTS_SOURCE = REPO / 'experiments/layer-dose-survey-toy-v1-2026-10-27/selection.json'
VALIDATION_DATA = HERE / 'data/validation-r01.json'
COMPONENTS = L.COMPONENTS  # ('kv', 'recurrent', 'conv'); code letters K, R, V in this order
CONTENT_FIELDS = ('keys', 'values', 'recurrent_states', 'conv_states')
# §4: the eight C/T combinations, code order KV, recurrent R, conv V.
G_CODES = ('TTT', 'CCC', 'CTT', 'TCT', 'TTC', 'TCC', 'CTC', 'CCT')
# §7: the seven non-empty subsets of the three classes.
SUBSETS = ('kv', 'recurrent', 'conv', 'kv+recurrent', 'kv+conv', 'recurrent+conv', 'kv+recurrent+conv')
JOINT = 'kv+recurrent+conv'
# §7 table: group g = linear layers 4g..4g+2 (recurrent and conv) and full-attention layer 4g+3 (KV).
CONTRACT_GROUPS = tuple({'linear': (4 * g, 4 * g + 1, 4 * g + 2), 'full': (4 * g + 3,)} for g in range(8))
WINDOWS = {'early': (0, 1, 2, 3), 'mid': (12, 13, 14, 15), 'late': (24, 25, 26, 27)}
BACKGROUND = {'clean': 'T', 'pollute': 'C'}
STAGES = ('audit', 'g_preflight', 'g_development', 'g_history', 'a_preflight', 'a_scan', 'b_preflight', 'b_validate')
PREFLIGHT_STAGES = ('g_preflight', 'a_preflight', 'b_preflight')
G_PREFLIGHT_CONDITIONS = ('N_L00_C4146_D+1', 'N_L13_C248_D-1', 'N_L31_C8750_D+1')  # early, mid, structural boundary
PREFLIGHT_GROUPS = (0, 7)
PREFLIGHT_LIMITS = {'generations': 128, 'candidate_reads': 256}  # per preflight stage, both workers together
FORMAL_LIMITS = {'audit': 24, 'g_development': 10776, 'g_history': 10776, 'a_scan': 8064, 'b_validate': 3048}
MIN_FREE_MIB = L.MIN_FREE_MIB  # per worker, at start
# 2026-10-30 speed trial: batch-1 workers sharing a card are bitwise identical to a lone worker; 4 per card
# gave 1.80 generations/s per card against 0.53 for one (6 per card: 1.85). Batched decoding and fused
# linear-attention kernels changed logits and were rejected (IMPLEMENTATION.zh-CN.md).
MAX_WORKERS_PER_GPU = 6


# ---------------------------------------------------------------- conditions (§2)

def points():
    rows = [r for r in exp.read(POINTS_SOURCE)['selected_channels'] if r['model_id'] == '4b']
    rows.sort(key=lambda r: r['layer'])
    assert [r['layer'] for r in rows] == list(range(32)), 'need exactly one fixed point per layer L0-L31'
    return [{'layer': r['layer'], 'channel': r['channel'], 'source_condition_id': r['condition_id']} for r in rows]


def condition_id(layer, channel, dose):
    return f'N_L{layer:02d}_C{channel}_D{dose:+g}'


def g_conditions():
    out = []
    for p in points():
        for dose in (-1.0, 1.0):
            out.append({'id': condition_id(p['layer'], p['channel'], dose), 'kind': 'native',
                        'layer': p['layer'], 'channel': p['channel'], 'dose': dose})
    assert len(out) == 64 and len({c['id'] for c in out}) == 64
    return out


def engine_condition(cid):
    if cid == 'clean':
        return {'id': 'clean', 'kind': 'clean', 'dose': 0.0}
    return dict(next(c for c in g_conditions() if c['id'] == cid))


# ---------------------------------------------------------------- groups, swaps, provenance (no model needed)

def derive_groups(types):
    """Each full-attention layer closes a group together with the linear layers since the previous one."""
    groups, linear = [], []
    for i, kind in enumerate(types):
        if kind == 'linear_attention':
            linear.append(i)
        else:
            assert kind == 'full_attention', kind
            groups.append({'linear': tuple(linear), 'full': (i,)})
            linear = []
    assert not linear, 'trailing linear layers without a closing full-attention layer'
    return tuple(groups)


def check_contract_groups(types):
    """§7: a model whose layout differs from the table stops; groups are never re-derived silently."""
    groups = derive_groups(types)
    assert groups == CONTRACT_GROUPS, 'model layer layout does not match the contract group table'
    return groups


def components_of(subset):
    comps = tuple(subset.split('+'))
    assert comps and set(comps) <= set(COMPONENTS) and len(set(comps)) == len(comps), subset
    return comps


def code_cleaned(code):
    """Classes taken from C in a G code (letters ordered KV, R, V)."""
    assert len(code) == 3 and set(code) <= {'T', 'C'}, code
    return tuple(comp for comp, letter in zip(COMPONENTS, code) if letter == 'C')


def swaps_for(groups, group, comps):
    """(layer, component) pairs swapped by an operation; group None means every layer of those classes."""
    chosen = groups if group is None else (groups[group],)
    out = set()
    for g in chosen:
        for comp in comps:
            for layer in (g['full'] if comp == 'kv' else g['linear']):
                out.add((layer, comp))
    return frozenset(out)


def compose_swaps(cache_t, cache_c, types, background, swaps):
    """Deep copy of the background cache with the listed (layer, component) tensors cloned from the other source."""
    assert background in ('T', 'C')
    base, other = (cache_t, cache_c) if background == 'T' else (cache_c, cache_t)
    new = copy.deepcopy(base)
    for i, comp, field in L.component_tensors(new, types):
        if (i, comp) in swaps:
            source = L._get(other.layers[i], field)
            assert source is not None, (i, field)
            L._set(new.layers[i], field, source.clone())
    return new


def check_sources(rows, background, swaps):
    """Every tensor must equal its designed source; rows where T equals C are kept and counted, never dropped."""
    other = 'C' if background == 'T' else 'T'
    t_equals_c = 0
    for r in rows:
        want = other if (r['layer'], r['component']) in swaps else background
        assert r['equals_' + want], r
        t_equals_c += r['equals_T'] and r['equals_C']
    return {'rows': len(rows), 't_equals_c_rows': t_equals_c}


def cache_manifest(cache, types):
    return {f'{i}:{field}': L.tensor_hash(L._get(cache.layers[i], field)) for i, _, field in L.component_tensors(cache, types)}


def other_state(cache):
    """§10: every cache field except the three content classes (flags, lengths, positions, any other tensor).
    Same payload as control_engine.state_fingerprint with the content fields dropped, but content tensors are
    never hashed (they are audited separately), which keeps the per-record cost to the small management fields."""
    from control_engine import tensor_hash
    import math
    seen = {}

    def visit(item, path):
        if item is None or isinstance(item, (str, bool, int)):
            return item
        if isinstance(item, float):
            return item if math.isfinite(item) else str(item)
        if hasattr(item, 'detach') and hasattr(item, 'shape'):
            return {'dtype': str(item.dtype), 'shape': list(item.shape), 'sha256': tensor_hash(item)}
        if id(item) in seen:
            return {'alias': seen[id(item)]}
        seen[id(item)] = path
        if isinstance(item, dict):
            return {str(k): visit(v, f'{path}.{k}') for k, v in sorted(item.items(), key=lambda p: str(p[0]))
                    if str(k) not in CONTENT_FIELDS}
        if isinstance(item, (tuple, list)):
            return [visit(v, f'{path}.{i}') for i, v in enumerate(item)]
        if hasattr(item, '__dict__'):
            return {'class': type(item).__qualname__, 'fields': visit(vars(item), path + '.fields')}
        return {'class': type(item).__qualname__}

    state = visit(cache, 'cache')
    return {'sha256': exp.digest(state), 'state': state}


def audit_against(cache, manifest_t, manifest_c, types):
    """Rows identical to stage-1 L.audit, but T and C hashes come from manifests computed once per condition."""
    rows = []
    for i, comp, field in L.component_tensors(cache, types):
        h = L.tensor_hash(L._get(cache.layers[i], field))
        key = f'{i}:{field}'
        rows.append({'layer': i, 'component': comp, 'field': field, 'sha256': h,
                     'equals_T': h == manifest_t[key], 'equals_C': h == manifest_c[key]})
    return rows


def structure(cache_t, cache_c, types, layer):
    """§5: per tensor T/C equality and difference norm. The MLP write at `layer` follows that layer's attention,
    so every cache of layers <= `layer` must have T == C; only later layers can carry a structural write."""
    rows = []
    for i, comp, field in L.component_tensors(cache_t, types):
        t, c = L._get(cache_t.layers[i], field), L._get(cache_c.layers[i], field)
        equal = L.tensor_hash(t) == L.tensor_hash(c)
        rows.append({'layer': i, 'component': comp, 'field': field, 'equal': equal,
                     'diff_norm': float((t.float() - c.float()).norm()), 'c_norm': float(c.float().norm()),
                     'downstream': i > layer})
    upstream_differs = [r for r in rows if not r['downstream'] and not r['equal']]
    assert not upstream_differs, f'cache at or before the injection layer differs (check hook timing): {upstream_differs[:2]}'
    return {'injection_layer': layer, 'rows': rows,
            'downstream_layers': {comp: sorted({r['layer'] for r in rows if r['component'] == comp and r['downstream']}) for comp in COMPONENTS},
            'differing_layers': {comp: sorted({r['layer'] for r in rows if r['component'] == comp and not r['equal']}) for comp in COMPONENTS}}


# ---------------------------------------------------------------- plan

def make_spec(item_id, condition_id, background, group, subset, direction, code, roles):
    spec = {'item_id': item_id, 'condition_id': condition_id, 'background': background, 'group': group,
            'subset': subset, 'direction': direction, 'code': code, 'roles': sorted(roles)}
    spec['arm'] = f'all:{code}' if group is None else f'grp{group}:{subset}:{direction}'
    spec['key'] = f'{item_id}__{condition_id}__{spec["arm"].replace(":", "-")}'
    return spec


def identity(spec):
    """De-duplication identity: same input, condition, background and swapped classes/groups (§8)."""
    comps = tuple(sorted(components_of(spec['subset']))) if spec['subset'] else spec['code']
    return (spec['item_id'], spec['condition_id'], spec['background'], spec['group'], comps)


def global_specs(item_id, conditions):
    """CCC shared per input (condition 'clean'); the other seven codes per condition, background T."""
    out = [make_spec(item_id, 'clean', 'C', None, None, None, 'CCC', ['global'])]
    for c in conditions:
        for code in G_CODES:
            if code != 'CCC':
                out.append(make_spec(item_id, c, 'T', None, None, None, code, ['global']))
    return out


def local_specs(item_id, condition_id, groups, directions, roles):
    return [make_spec(item_id, condition_id, BACKGROUND[d], g, s, d, None, roles)
            for g in groups for s in SUBSETS for d in directions]


def dedupe(specs):
    seen, out = {}, []
    for s in specs:
        k = identity(s)
        if k in seen:
            seen[k]['roles'] = sorted(set(seen[k]['roles']) | set(s['roles']))
            continue
        seen[k] = s
        out.append(s)
    assert len({s['key'] for s in out}) == len(out)
    return out


def check_g_selection(selection):
    """selection: {role: condition_id}, role = '<window>:<stop|fact>', at most six roles (§6)."""
    ids = {c['id']: c for c in g_conditions()}
    assert selection and set(selection) <= {f'{w}:{r}' for w in WINDOWS for r in ('stop', 'fact')}, selection
    for role, cid in selection.items():
        assert ids[cid]['layer'] in WINDOWS[role.split(':')[0]], (role, cid)
    return selection


def check_candidates(candidates):
    """candidates: {role: {'condition_id', 'group'}} with roles from the G selection (§7)."""
    assert candidates and len(candidates) <= 6
    for role, c in candidates.items():
        assert c['group'] in range(8) and c['condition_id'] in {x['id'] for x in g_conditions()}, (role, c)
    return candidates


def roles_by_condition(selection):
    out = {}
    for role, cid in selection.items():
        out.setdefault(cid, []).append(role)
    return out


def plan_items(stage, item_ids, selection=None, candidates=None):
    specs = []
    for item_id in item_ids:
        if stage == 'audit':
            specs.append(make_spec(item_id, 'clean', 'C', None, None, None, 'CCC', ['audit']))
        elif stage == 'g_preflight':
            specs += global_specs(item_id, G_PREFLIGHT_CONDITIONS)
        elif stage in ('g_development', 'g_history'):
            specs += global_specs(item_id, [c['id'] for c in g_conditions()])
        elif stage in ('a_preflight', 'a_scan'):
            by_cond = roles_by_condition(check_g_selection(selection))
            conds = sorted(by_cond)[:1] if stage == 'a_preflight' else sorted(by_cond)
            if stage == 'a_preflight':  # reuse replay of the G references (§11) plus a bounded local slice
                specs += [s for s in global_specs(item_id, conds) if s['code'] in ('TTT', 'CCC')]
            for cid in conds:
                groups = PREFLIGHT_GROUPS if stage == 'a_preflight' else range(8)
                specs += local_specs(item_id, cid, groups, ('clean',), by_cond[cid])
        else:
            assert stage in ('b_preflight', 'b_validate'), stage
            cands = check_candidates(candidates)
            roles = sorted(cands)[:1] if stage == 'b_preflight' else sorted(cands)
            specs += global_specs(item_id, sorted({cands[r]['condition_id'] for r in roles}))
            for role in roles:
                specs += local_specs(item_id, cands[role]['condition_id'], (cands[role]['group'],), ('clean', 'pollute'), [role])
    return dedupe(specs)


def panel_of(stage):
    if stage in ('audit', 'b_preflight', 'b_validate'):
        return 'validation'
    return 'confirmation' if stage == 'g_history' else 'development'


def items_for(stage):
    panel = panel_of(stage)
    return exp.read(VALIDATION_DATA) if panel == 'validation' else exp.items(panel)


def stage_items(stage):
    """Items a stage covers, in fixed order; a preflight takes the first item of each of the two base halves."""
    rows = items_for(stage)
    return [exp.assigned(rows, g)[0] for g in (0, 1)] if stage in PREFLIGHT_STAGES else rows


def unit_of(stage, spec):
    """Scheduling unit: a whole item in preflights (its gates need every condition of the item), else item x condition."""
    return spec['item_id'] if stage in PREFLIGHT_STAGES else (spec['item_id'], spec['condition_id'])


def plan(stage, worker, n_workers=2, selection=None, candidates=None):
    """Worker share of the stage plan: units dealt round-robin, so the union over workers is the full plan."""
    assert 0 <= worker < n_workers
    specs = plan_items(stage, [r['id'] for r in stage_items(stage)], selection, candidates)
    units = list(dict.fromkeys(unit_of(stage, s) for s in specs))
    mine = {u for k, u in enumerate(units) if k % n_workers == worker}
    return [s for s in specs if unit_of(stage, s) in mine]


# ---------------------------------------------------------------- freeze and authorization

def frozen_paths():
    """Top-level *.py, the contract, the II-B data and every dependency; analysis/, readiness/, runs/ stay writable."""
    own = sorted(HERE.glob('*.py')) + [HERE / 'CONTRACT.zh-CN.md', VALIDATION_DATA, POINTS_SOURCE]
    return own + [p for p in L.frozen_paths() if p not in own]


def freeze(path):
    value = {'experiment': HERE.name, 'created_at': exp.utc(), 'stage1_commit': STAGE1_COMMIT,
             'conditions_sha256': exp.digest(g_conditions()),
             'files': {str(p.relative_to(REPO)): exp.sha(p) for p in frozen_paths()}}
    exp.write(path, value, immutable=True)
    return {'path': str(path), 'sha256': exp.sha(path), 'files': len(value['files'])}


def check_freeze(path):
    value = exp.read(path)
    actual = {str(p.relative_to(REPO)): exp.sha(p) for p in frozen_paths()}
    assert value['files'] == actual, 'Frozen source changed'
    return exp.sha(path)


def _evidence(auth, key, **expect):
    value = exp.read(HERE / auth[key])
    assert auth[key] in auth['required_evidence'], key
    for k, v in expect.items():
        assert value[k] == v, (key, k)
    return value


def authorize(path, stage):
    auth = exp.read(path)
    assert auth['status'] == 'authorized' and auth['experiment'] == HERE.name and auth['user_instruction']
    assert stage in auth['allowed_stages']
    assert auth['maximum_workers'] % 2 == 0 and 2 <= auth['maximum_workers'] <= 2 * MAX_WORKERS_PER_GPU
    assert exp.sha(HERE / auth['freeze_path']) == auth['freeze_sha256']
    check_freeze(HERE / auth['freeze_path'])
    for rel, digest in auth['required_evidence'].items():
        assert exp.sha(HERE / rel) == digest, rel
    if stage != 'audit':
        # §3: the new panel and its clean audit are locked before any G intervention output is opened.
        lock = _evidence(auth, 'items_lock_path', status='locked', clean_audit='passed')
        assert lock['validation_data_sha256'] == exp.sha(VALIDATION_DATA)
    preflight = {'g_development': 'g', 'g_history': 'g', 'a_scan': 'a', 'b_validate': 'b'}.get(stage)
    if preflight:
        _evidence(auth, f'{preflight}_preflight_verification_path', status='passed', freeze_sha256=auth['freeze_sha256'])
    if stage in ('a_preflight', 'a_scan', 'b_preflight', 'b_validate'):
        g_lock = _evidence(auth, 'g_lock_path', status='locked', stage_two_outputs_previously_unseen=True)
        assert auth['selection'] == check_g_selection(g_lock['selection'])
        g_dev = _evidence(auth, 'g_development_verification_path', status='passed', freeze_sha256=auth['freeze_sha256'])
        assert g_lock['g_development_verification_sha256'] == exp.sha(HERE / auth['g_development_verification_path'])
        assert g_dev['generations'] == FORMAL_LIMITS['g_development']
    if stage in ('b_preflight', 'b_validate'):
        a_lock = _evidence(auth, 'a_lock_path', status='locked', validation_outputs_previously_unseen=True)
        assert auth['candidates'] == check_candidates(a_lock['candidates'])
    return auth


# ---------------------------------------------------------------- execution (model only)

def generation_summary(token_ids, readouts, end_reason, stop_ids):
    eos = [i for i, t in enumerate(token_ids) if t in stop_ids]
    return {'first_step_eos': token_ids[0] in stop_ids, 'first_eos_position': eos[0] if eos else None,
            'generated_tokens': len(token_ids), 'truncated': end_reason == 'length_limit',
            'stop_advantage_steps': [r['stop_advantage'] for r in readouts]}


def swaps_of_spec(groups, spec):
    if spec['group'] is None:
        cleaned = code_cleaned(spec['code'])
        return frozenset() if spec['background'] == 'C' else swaps_for(groups, None, cleaned)
    return swaps_for(groups, spec['group'], components_of(spec['subset']))


def execute(engine, stage, output, receipt, specs, auth):
    from control_engine import exact_pair, encode_text
    rows = items_for(stage)
    by_id = {r['id']: r for r in rows}
    mine = [by_id[i] for i in dict.fromkeys(s['item_id'] for s in specs)]
    contexts = exp.contexts_for(engine.tokenizer, rows)
    types = L.layer_types(engine.model)
    groups = check_contract_groups(types)
    references = {}
    for rid in sorted({by_id[s['item_id']]['reference_id'] for s in specs}):
        references[rid] = engine.calibrate([contexts[rid]])[0]
        exp.write(output / f'calibrations/{rid}.json', references[rid], immutable=True)
    counts = {'records': 0, 'generations': 0, 'candidate_reads': 0}
    checks = []
    for item in mine:
        context, reference = contexts[item['id']], references[item['reference_id']]
        prompt = encode_text(engine.tokenizer, context)
        prefix, last = prompt[:-1], prompt[-1]
        cands = [exact_pair(engine.tokenizer, context, choice)[1] for choice in item['choices']]
        cache_c, decay_c = L._clean_cache(engine, prefix)
        other_c = other_state(cache_c)
        item_specs = [s for s in specs if s['item_id'] == item['id']]
        built, manifests = {}, {'clean': cache_manifest(cache_c, types)}
        for cid in sorted({s['condition_id'] for s in item_specs} - {'clean'}):
            condition = engine_condition(cid)
            built[cid] = L._build_T(engine, condition, reference, prefix)
            manifests[cid] = cache_manifest(built[cid][0], types)
            # §10: management fields must match between T and C; no persistent state outside the three classes may differ.
            other_t = other_state(built[cid][0])
            assert other_t['sha256'] == other_c['sha256'], f'state outside KV/recurrent/conv differs for {cid}; revise contract'
            exp.write(output / f'caches/{item["id"]}__{cid}.json', {'T': manifests[cid], 'C': manifests['clean'],
                      'structure': structure(built[cid][0], cache_c, types, condition['layer']),
                      'other_state_sha256': other_t['sha256'], 'write_audit': built[cid][1],
                      'gate_decay': {'T': built[cid][2], 'C': decay_c}}, immutable=True)
        for spec in item_specs:
            cid = spec['condition_id']
            cache_t = cache_c if cid == 'clean' else built[cid][0]
            swaps = swaps_of_spec(groups, spec)
            cache = compose_swaps(cache_t, cache_c, types, spec['background'], swaps)
            audit_rows = audit_against(cache, manifests['clean' if cid == 'clean' else cid], manifests['clean'], types)
            source_check = check_sources(audit_rows, spec['background'], swaps)
            assert other_state(cache)['sha256'] == other_c['sha256'], 'composed cache management state differs'
            gen = L.decode(engine.model, cache, last, len(prompt), engine.stop_ids, hash_all=stage in PREFLIGHT_STAGES)
            scores = [L.score(engine.model, cache, last, len(prompt), c) for c in cands]
            del cache
            counts['generations'] += 1
            counts['candidate_reads'] += len(scores)
            answer = engine.tokenizer.decode(gen['token_ids'], skip_special_tokens=True)
            record = {'schema': 2, 'experiment': HERE.name, 'stage': stage, 'spec': spec, 'item': item, 'context': context,
                      'reference_sha256': exp.digest(reference), 'prompt_token_sha256': exp.digest(prompt),
                      'condition': engine_condition(cid), 'swaps': sorted([list(s) for s in swaps]),
                      'component_audit': audit_rows, 'source_check': source_check,
                      'cache_manifest': None if cid == 'clean' else f'caches/{item["id"]}__{cid}.json',
                      'prompt_token_count': len(prompt),
                      'generation': {**gen, **generation_summary(gen['token_ids'], gen['readouts'], gen['end_reason'], engine.stop_ids),
                                     'answer_text': answer, 'delivered_nonempty': bool(answer.strip()),
                                     'raw_text': engine.tokenizer.decode(gen['token_ids'], skip_special_tokens=False)},
                      'candidates': [{'text': t, **s} for t, s in zip(item['choices'], scores)],
                      'freeze_sha256': receipt['freeze_sha256'], 'created_at': exp.utc()}
            L._store(output, receipt, f'records/{spec["key"]}.json', record)
            counts['records'] += 1
        # §4: generation and scoring use independent deep copies and never write back into T or C.
        assert cache_manifest(cache_c, types) == manifests['clean'], 'clean cache mutated'
        for cid, (cache_t, _, _) in built.items():
            assert cache_manifest(cache_t, types) == manifests[cid], f'treated cache mutated: {cid}'
        if stage in PREFLIGHT_STAGES:
            checks.append(preflight_gates(engine, stage, item, context, reference, prompt, cache_c, built, types, groups, output, auth))
            exp.write(output / f'preflight/{item["id"]}.json', checks[-1], immutable=True)
        del built
    if stage in PREFLIGHT_STAGES:
        assert counts['generations'] <= PREFLIGHT_LIMITS['generations'] // 2
        assert counts['candidate_reads'] <= PREFLIGHT_LIMITS['candidate_reads'] // 2
        exp.write(output / 'preflight.json', L.summarize_preflight(checks, len(mine)), immutable=True)
    return counts


def swap_gates(model, cache_t, cache_c, types, groups, last, n_prompt, stop):
    """Stage-II engineering gates on one (T, C) pair; any assertion failure stops the worker."""
    before = {'T': cache_manifest(cache_t, types), 'C': cache_manifest(cache_c, types)}
    out = {'global_replay': {}, 'provenance': {}, 'readability': {}}
    # Global class swaps over all groups replay the stage-1 class-wise compose byte for byte and on first-step logits.
    for code in G_CODES:
        cleaned = code_cleaned(code)
        mine = compose_swaps(cache_t, cache_c, types, 'T', swaps_for(groups, None, cleaned))
        ref = L.compose(cache_t, cache_c, types, cleaned)
        assert [r['sha256'] for r in L.audit(mine, cache_t, cache_c, types)] == \
               [r['sha256'] for r in L.audit(ref, cache_t, cache_c, types)], code
        a = L.decode(model, mine, last, n_prompt, stop, max_new_tokens=1, attentions=False)
        b = L.decode(model, ref, last, n_prompt, stop, max_new_tokens=1, attentions=False)
        assert a['readouts'][0]['logits_sha256'] == b['readouts'][0]['logits_sha256'], code
        out['global_replay'][code] = 'passed'
    # Every group x subset x direction has the designed provenance; subsets swap only their named classes.
    for g in range(len(groups)):
        for s in SUBSETS:
            for d, bg in BACKGROUND.items():
                swaps = swaps_for(groups, g, components_of(s))
                rows = L.audit(compose_swaps(cache_t, cache_c, types, bg, swaps), cache_t, cache_c, types)
                out['provenance'][f'grp{g}:{s}:{d}'] = check_sources(rows, bg, swaps)
    # Readability: each class is actually read (same-norm random replacement changes logits).
    base = L.decode(model, cache_t, last, n_prompt, stop, max_new_tokens=1, attentions=False)['readouts'][0]['logits_sha256']
    for comp in COMPONENTS:
        rnd = L.decode(model, L.randomize(cache_t, types, comp, 7), last, n_prompt, stop, max_new_tokens=1, attentions=False)
        out['readability'][comp] = rnd['readouts'][0]['logits_sha256'] != base
    assert all(out['readability'].values()), out['readability']
    assert {'T': cache_manifest(cache_t, types), 'C': cache_manifest(cache_c, types)} == before, 'source mutated'
    return out


def reuse_replay(output, item, auth):
    """§11: II-A reuses G development TTT/CCC records; the regenerated preflight records must match them exactly."""
    g_run = HERE / auth['g_development_run']
    out = {}
    for rec_path in sorted((output / 'records').glob(f'{item["id"]}__*__all-*.json')):
        mine = exp.read(rec_path)
        matches = list(g_run.glob(f'worker-*/records/{rec_path.name}'))
        assert len(matches) == 1, rec_path.name
        old = exp.read(matches[0])
        for k in ('reference_sha256', 'prompt_token_sha256', 'swaps'):
            assert mine[k] == old[k], (rec_path.name, k)
        assert mine['generation']['token_ids'] == old['generation']['token_ids'], rec_path.name
        assert mine['generation']['readouts'][0]['logits_sha256'] == old['generation']['readouts'][0]['logits_sha256']
        assert [c['loglikelihood'] for c in mine['candidates']] == [c['loglikelihood'] for c in old['candidates']]
        out[rec_path.name] = 'identical'
    assert out, 'no reuse records to replay'
    return out


def preflight_gates(engine, stage, item, context, reference, prompt, cache_c, built, types, groups, output, auth):
    """§11 engineering gates. g_preflight also reruns the stage-1 gates (same path, readability, incremental
    path, masked hook, inert attention readout) on its N_L00_C4146_D+1 cache, and the L31 structural boundary."""
    if stage == 'g_preflight':
        out = L.preflight_gates(engine, item, context, reference, prompt, cache_c, built, types)
        boundary = exp.read(output / f'caches/{item["id"]}__N_L31_C8750_D+1.json')['structure']
        assert not any(boundary['differing_layers'].values()), 'L31 caches differ from clean; check hook timing'
        out['gates']['L31_boundary'] = 'T == C for every cache tensor'
    else:
        out = {'item_id': item['id'], 'gates': {}}
    out['gates']['group_mapping'] = [{k: list(v) for k, v in g.items()} for g in groups]
    for cid, (cache_t, _, _) in sorted(built.items()):
        if exp.read(output / f'caches/{item["id"]}__{cid}.json')['structure']['differing_layers'] == {c: [] for c in COMPONENTS}:
            out['gates'][f'swaps:{cid}'] = 'skipped: T == C everywhere (structural boundary)'
            continue
        out['gates'][f'swaps:{cid}'] = swap_gates(engine.model, cache_t, cache_c, types, groups, prompt[-1], len(prompt), engine.stop_ids)
    if stage == 'a_preflight':
        out['gates']['reuse_replay'] = reuse_replay(output, item, auth)
    out['status'] = 'passed'
    return out


def run(stage, worker, output, authorization):
    auth = authorize(authorization, stage)
    n_workers, gpu = auth['maximum_workers'], worker % 2
    assert 0 <= worker < n_workers
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root'] / f'worker-{worker}').resolve()
    import fcntl
    lock = open(f'/tmp/acupuncture-stage2-worker{worker}.lock', 'w')  # one process per worker slot; cards are shared
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    free_mib = int(subprocess.check_output(['nvidia-smi', f'--id={gpu}', '--query-gpu=memory.free', '--format=csv,noheader,nounits'], text=True).strip())
    neighbours = subprocess.check_output(['nvidia-smi', f'--id={gpu}', '--query-compute-apps=pid,used_memory', '--format=csv,noheader,nounits'], text=True).strip()
    # §11: insufficient resources stop submission; other tasks are never pre-empted.
    assert free_mib >= MIN_FREE_MIB, f'Only {free_mib} MiB free on GPU {gpu}'
    output.mkdir(parents=True, exist_ok=False)
    receipt = {'status': 'running', 'stage': stage, 'worker': worker, 'n_workers': n_workers, 'gpu': gpu, 'pid': os.getpid(), 'started_at': exp.utc(),
               'freeze_path': auth['freeze_path'], 'freeze_sha256': auth['freeze_sha256'],
               'authorization_sha256': exp.sha(authorization), 'record_hashes': {},
               'gpu_free_mib_at_start': free_mib, 'coresident_processes_at_start': neighbours.splitlines()}
    exp.write(output / 'execution.json', dict(receipt), immutable=True)
    exp.write(output / 'authorization.json', auth, immutable=True)
    exp.write(output / 'receipt.json', receipt)
    started = time.monotonic()
    sys.path.insert(0, str(SOURCE))
    from control_engine import ControlEngine
    try:
        source = exp.read(SOURCE / 'contract.json')['source']
        receipt['asset_identity'] = exp.model_assets()
        engine = ControlEngine(source['model_path'], exp.model_spec(), f'cuda:{gpu}')
        exp.metadata_check(engine)
        exp.write(output / 'metadata.json', engine.metadata, immutable=True)
        receipt['load_seconds'] = time.monotonic() - started
        specs = plan(stage, worker, n_workers, auth.get('selection'), auth.get('candidates'))
        exp.write(output / 'plan.json', specs, immutable=True)
        receipt['plan_sha256'] = exp.sha(output / 'plan.json')
        receipt['summary'] = execute(engine, stage, output, receipt, specs, auth)
        receipt['integrity'] = engine.verify_unchanged()
        receipt['status'] = 'completed'
    except BaseException:
        receipt.update(status='failed', error=traceback.format_exc())
        raise
    finally:
        receipt.update(finished_at=exp.utc(), wall_seconds=time.monotonic() - started)
        exp.write(output / 'receipt.json', receipt)
    return receipt


def verify_worker(path):
    path = Path(path)
    r = exp.read(path / 'receipt.json')
    assert r['status'] == 'completed'
    assert r['freeze_sha256'] == exp.sha(HERE / r['freeze_path'])
    check_freeze(HERE / r['freeze_path'])
    assert r['authorization_sha256'] == exp.sha(path / 'authorization.json')
    auth = exp.read(path / 'authorization.json')
    execution = exp.read(path / 'execution.json')
    for key in ('stage', 'worker', 'n_workers', 'gpu', 'pid', 'started_at', 'freeze_sha256', 'authorization_sha256'):
        assert execution[key] == r[key], key
    specs = exp.read(path / 'plan.json')
    assert r['n_workers'] == auth['maximum_workers'] and r['gpu'] == r['worker'] % 2
    assert specs == plan(r['stage'], r['worker'], r['n_workers'], auth.get('selection'), auth.get('candidates'))
    expected = {f'records/{s["key"]}.json' for s in specs}
    assert set(r['record_hashes']) == expected
    assert {str(p.relative_to(path)) for p in (path / 'records').glob('*.json')} == expected
    for rel, digest in r['record_hashes'].items():
        assert exp.sha(path / rel) == digest, rel
        rec = exp.read(path / rel)
        g = rec['generation']
        assert 1 <= len(g['token_ids']) <= 128 and len(g['readouts']) == len(g['token_ids'])
        assert (g['end_reason'] == 'eos_token') == (g['token_ids'][-1] in (248044, 248046))
        assert not any(t in (248044, 248046) for t in g['token_ids'][:-1])
        check_sources(rec['component_audit'], rec['spec']['background'], {tuple(s) for s in rec['swaps']})
        assert [c['text'] for c in rec['candidates']] == rec['item']['choices']
        assert rec['freeze_sha256'] == r['freeze_sha256']
        if rec['cache_manifest']:
            assert (path / rec['cache_manifest']).exists(), rec['cache_manifest']
    assert r['integrity']['hooks_removed'] is True
    assert r['integrity']['target_weight_sha256_after'] == exp.read(path / 'metadata.json')['target_weight_sha256_before']
    assert exp.read(path / 'exit.json')['returncode'] == 0
    if r['stage'] in PREFLIGHT_STAGES:
        assert exp.read(path / 'preflight.json')['status'] == 'passed'
    return {'status': 'passed', 'stage': r['stage'], 'records': len(r['record_hashes']), 'freeze_sha256': r['freeze_sha256'],
            'generations': r['summary']['generations'], 'candidate_reads': r['summary']['candidate_reads'],
            'wall_seconds': r['wall_seconds']}


def launch(stage, authorization, output):
    auth = authorize(authorization, stage)
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root']).resolve()
    output.mkdir(parents=True, exist_ok=False)
    controller = {'status': 'running', 'pid': os.getpid(), 'stage': stage, 'started_at': exp.utc(),
                  'authorization_sha256': exp.sha(authorization), 'freeze_sha256': auth['freeze_sha256'], 'workers': {}}
    exp.write(output / 'execution.json', dict(controller), immutable=True)
    procs, logs, started = {}, [], time.monotonic()
    try:
        for gpu in range(auth['maximum_workers']):  # worker index; its card is index % 2
            log = (output / f'worker-{gpu}.log').open('x')
            logs.append(log)
            cmd = [sys.executable, '-u', str(HERE / 'stage2.py'), 'run', '--stage', stage, '--worker', str(gpu),
                   '--authorization', str(Path(authorization).resolve()), '--output', str(output / f'worker-{gpu}')]
            procs[gpu] = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
            controller['workers'][str(gpu)] = {'pid': procs[gpu].pid, 'command': cmd}
        exp.write(output / 'controller.json', controller)
        pending, failure = dict(procs), False
        while pending:
            for gpu, p in list(pending.items()):
                code = p.poll()
                if code is None:
                    continue
                (output / f'worker-{gpu}').mkdir(exist_ok=True)
                exp.write(output / f'worker-{gpu}/exit.json', {'returncode': code, 'finished_at': exp.utc()}, immutable=True)
                controller['workers'][str(gpu)]['returncode'] = code
                failure |= code != 0
                del pending[gpu]
            exp.write(output / 'controller.json', controller)
            if failure:
                for p in pending.values():
                    p.terminate()
            if pending:
                time.sleep(2)
        assert not failure, 'A worker failed; partial evidence preserved'
        results = [verify_worker(output / f'worker-{g}') for g in range(auth['maximum_workers'])]
        total = sum(w['generations'] for w in results)
        reads = sum(w['candidate_reads'] for w in results)
        if stage in PREFLIGHT_STAGES:
            assert total <= PREFLIGHT_LIMITS['generations'] and reads <= PREFLIGHT_LIMITS['candidate_reads']
        else:
            assert total <= FORMAL_LIMITS[stage], (stage, total)
        exp.write(output / 'verification.json', {'status': 'passed', 'freeze_sha256': auth['freeze_sha256'],
                  'workers': results, 'generations': total, 'candidate_reads': reads, 'verified_at': exp.utc()}, immutable=True)
        controller['status'] = 'completed'
    except BaseException as error:
        controller.update(status='failed', error=repr(error))
        for gpu, p in procs.items():
            if p.poll() is None:
                p.terminate()
                code = p.wait()
                w = output / f'worker-{gpu}'
                w.mkdir(exist_ok=True)
                if not (w / 'exit.json').exists():
                    exp.write(w / 'exit.json', {'returncode': code, 'finished_at': exp.utc()}, immutable=True)
        raise
    finally:
        for log in logs:
            log.close()
        controller.update(finished_at=exp.utc(), wall_seconds=time.monotonic() - started)
        exp.write(output / 'controller.json', controller)
    return controller


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('freeze').add_argument('path')
    sub.add_parser('verify').add_argument('path')
    for name in ('run', 'launch'):
        q = sub.add_parser(name)
        q.add_argument('--stage', required=True, choices=STAGES)
        q.add_argument('--authorization', required=True)
        q.add_argument('--output', required=True)
        if name == 'run':
            q.add_argument('--worker', required=True, type=int, choices=range(2 * MAX_WORKERS_PER_GPU))
    a = p.parse_args()
    if a.cmd == 'freeze':
        value = freeze(a.path)
    elif a.cmd == 'verify':
        value = verify_worker(a.path)
    elif a.cmd == 'run':
        sys.path.insert(0, str(SOURCE))
        value = run(a.stage, a.worker, a.output, a.authorization)
        value = {k: v for k, v in value.items() if k != 'record_hashes'}
    else:
        value = launch(a.stage, a.authorization, a.output)
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    main()
