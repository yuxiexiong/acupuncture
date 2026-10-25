"""Deterministically materialize the prewritten toy inputs; never inspect new model outputs."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import re
import unicodedata

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
OLD = ROOT.parent / 'qwen35-neuron-steering-2026-10-25' / 'raw-corpus-cpu-bf16-r01'
PANEL = ROOT.parent / 'capability-screen-v3-2026-10-26'
SEED = 20261026
GROUPS = {
    'STEM': 'abstract_algebra anatomy astronomy college_biology college_chemistry college_computer_science college_mathematics college_physics computer_security conceptual_physics electrical_engineering elementary_mathematics high_school_biology high_school_chemistry high_school_computer_science high_school_mathematics high_school_physics high_school_statistics machine_learning'.split(),
    'humanities': 'formal_logic high_school_european_history high_school_us_history high_school_world_history international_law jurisprudence logical_fallacies moral_disputes moral_scenarios philosophy prehistory professional_law world_religions'.split(),
    'social_sciences': 'econometrics high_school_geography high_school_government_and_politics high_school_macroeconomics high_school_microeconomics high_school_psychology human_sexuality professional_psychology public_relations security_studies sociology us_foreign_policy'.split(),
    'other': 'business_ethics clinical_knowledge college_medicine global_facts human_aging management marketing medical_genetics miscellaneous nutrition professional_accounting professional_medicine virology'.split(),
}
EXPECTED_PANEL_SHA = '1ab21b595e3a5ef96d34bd3e487b81158bb4c2b961da4d863847daa4870afcbc'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def write_rows(name, values):
    path = DATA / name
    content = ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in values)
    if path.exists():
        assert path.read_text() == content, f'Preserve existing data; changed regeneration: {name}'
    else:
        path.write_text(content)


def map_data():
    values = []
    for line in (DATA / 'map_sources.tsv').read_text().splitlines():
        group, zp, ep, zq, za, eq, ea = line.split('|')
        split = 'train' if int(group[1:]) <= 64 else 'val'
        for lang, kind, content in [('zh', 'prose', zp), ('en', 'prose', ep),
                                    ('zh', 'dialogue', (zq, za)), ('en', 'dialogue', (eq, ea))]:
            row = {'id': f'{group}-{lang}-{kind}', 'group_id': group, 'split': split,
                   'kind': kind, 'language': lang}
            row.update({'text': content} if kind == 'prose' else {'messages': [
                {'role': 'user', 'content': content[0]}, {'role': 'assistant', 'content': content[1]}]})
            values.append(row)
    for split in ('train', 'val'):
        write_rows(f'map_{split}.jsonl', [row for row in values if row['split'] == split])


def contrast_data():
    values = []
    for line in (DATA / 'contrast_sources.tsv').read_text().splitlines():
        scene, language, prompt, nn, nh, hn, hh = line.split('|')
        for stance, style, continuation in [('neutral', 'neutral', nn), ('neutral', 'hostile', nh),
                                            ('harmful', 'neutral', hn), ('harmful', 'hostile', hh)]:
            values.append({'id': f'{scene}-{stance}-{style}', 'scenario_id': scene,
                           'language': language, 'prompt': prompt, 'stance': stance,
                           'style': style, 'continuation': continuation})
    write_rows('contrast.jsonl', values)


def confirm_data():
    values = []
    for line in (DATA / 'confirm_sources.tsv').read_text().splitlines():
        identifier, category, language, prompt = line.split('|')
        values.append({'id': identifier, 'category': category, 'language': language, 'prompt': prompt})
    write_rows('confirm.jsonl', values)


def dev_data():
    values = []
    for filename in ('original.raw.jsonl', 'modified.raw.jsonl'):
        path = OLD / filename
        digest = sha(path)
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if row['attempt']['max_new_tokens'] != 512:
                continue
            question, answer = row['question'], row['response']['token_ids']
            stop = next((i + 1 for i, token in enumerate(answer) if token in (248044, 248046)), len(answer))
            family = row['arm']
            values.append({'id': f'{question["id"]}-{family}', 'question_id': question['id'],
                'family': family, 'prompt': question['prompt'],
                'prompt_rendered': question['input']['rendered_chat'],
                'prompt_token_ids': question['input']['tensors']['input_ids'][0],
                'answer_token_ids': answer[:stop], 'source_attempt_budget': 512,
                'source_answer_token_count': len(answer), 'answer_trimmed_at_first_eos': stop < len(answer),
                'answer_includes_eos': bool(answer[:stop] and answer[stop - 1] in (248044, 248046)),
                'source_file': str(path.relative_to(ROOT.parent.parent)), 'source_file_sha256': digest,
                'source_row_sha256': hashlib.sha256(line.encode()).hexdigest(),
                'source_question_record_sha256': row['source_question_record_sha256']})
    values.sort(key=lambda row: (row['question_id'], row['family']))
    assert len(values) == len({row['id'] for row in values}) == 48
    assert {row['question_id'] for row in values} == {f'Q{i:02}' for i in range(1, 25)}
    write_rows('dev.jsonl', values)


def ability_data():
    assert sha(PANEL / 'panel_manifest.json') == EXPECTED_PANEL_SHA
    panel = json.loads((PANEL / 'panel_manifest.json').read_text())
    source = {}
    for task in ('mmlu', 'arc_challenge'):
        path = PANEL / panel['files'][task]['file']
        assert sha(path) == panel['files'][task]['sha256']
        source[task] = rows(path)
    subject_group = {subject: group for group, subjects in GROUPS.items() for subject in subjects}
    assert len(subject_group) == sum(map(len, GROUPS.values())) == 57
    assert set(subject_group) == {row['subject'] for row in source['mmlu']}
    rng = random.Random(SEED)
    selected = []
    for group in GROUPS:
        pool = sorted((row for row in source['mmlu'] if subject_group[row['subject']] == group), key=lambda r: r['id'])
        for row in rng.sample(pool, 8):
            selected.append({**row, 'diagnostic_group': group})
    for row in rng.sample(sorted(source['arc_challenge'], key=lambda r: r['id']), 32):
        selected.append({**row, 'diagnostic_group': 'arc_challenge'})
    write_rows('ability_diag.jsonl', selected)
    return {'seed': SEED, 'algorithm': 'Python random.Random(seed); sorted IDs; groups in declared order then ARC; sample without replacement',
            'subject_groups': GROUPS, 'panel_manifest_sha256': EXPECTED_PANEL_SHA,
            'source_files': {task: panel['files'][task] for task in source},
            'selected_ids': [row['id'] for row in selected],
            'payload_verification': 'Removing diagnostic_group yields the exact frozen v3 item object; no outputs read'}


def normalized(text):
    return ''.join(c for c in unicodedata.normalize('NFKC', text).lower() if c.isalnum())


def shingles(text, language):
    parts = re.findall(r'\w+', text.lower()) if language == 'en' else list(normalized(text))
    width = 3 if language == 'en' else 5
    return {tuple(parts[i:i + width]) for i in range(max(0, len(parts) - width + 1))}


def audit():
    train, val, contrast, confirm, dev, ability = [rows(DATA / name) for name in (
        'map_train.jsonl', 'map_val.jsonl', 'contrast.jsonl', 'confirm.jsonl', 'dev.jsonl', 'ability_diag.jsonl')]
    assert [len(x) for x in (train, val, contrast, confirm, dev, ability)] == [256, 64, 128, 64, 48, 64]
    assert not ({r['group_id'] for r in train} & {r['group_id'] for r in val})
    for collection, expected in ((train, 64), (val, 16)):
        assert Counter((r['kind'], r['language']) for r in collection) == {
            ('prose', 'zh'): expected, ('prose', 'en'): expected,
            ('dialogue', 'zh'): expected, ('dialogue', 'en'): expected}
    assert len({r['category'] for r in confirm}) == 8
    assert set(Counter((r['category'], r['language']) for r in confirm).values()) == {4}
    assert Counter(r['diagnostic_group'] for r in ability) == {
        'STEM': 8, 'humanities': 8, 'social_sciences': 8, 'other': 8, 'arc_challenge': 32}
    assert len({r['scenario_id'] for r in contrast}) == 32
    for scene in {r['scenario_id'] for r in contrast}:
        group = [r for r in contrast if r['scenario_id'] == scene]
        assert {(r['stance'], r['style']) for r in group} == {
            ('neutral', 'neutral'), ('neutral', 'hostile'), ('harmful', 'neutral'), ('harmful', 'hostile')}
        assert len({r['prompt'] for r in group}) == 1
    comparisons = []
    for row in train + val:
        text = row.get('text') or ' '.join(m['content'] for m in row['messages'])
        comparisons.append((row['id'], row['language'], text))
    comparisons += [(r['id'], r['language'], r['prompt']) for r in contrast if r['stance'] == r['style'] == 'neutral']
    comparisons += [(r['id'], 'zh', r['prompt']) for r in dev if r['family'] == 'baseline']
    comparisons += [(r['id'], r['language'], r['prompt']) for r in confirm]
    nearest = []
    for row in confirm:
        a = shingles(row['prompt'], row['language'])
        candidates = []
        for identifier, language, text in comparisons:
            if identifier == row['id'] or language != row['language']:
                continue
            assert normalized(text) != normalized(row['prompt']), f'Duplicate confirm scene text: {identifier}'
            b = shingles(text, language)
            score = len(a & b) / len(a | b) if a | b else 0
            candidates.append((score, identifier))
        score, identifier = max(candidates)
        nearest.append({'id': row['id'], 'nearest_id': identifier, 'shingle_jaccard': score})
    return {'counts': {'map_train': 256, 'map_val': 64, 'contrast': 128, 'confirm': 64, 'dev': 48, 'ability_diag': 64},
            'exact_duplicate_confirm_vs_other_inputs': 0, 'map_group_overlap_train_val': 0,
            'scenario_review': 'Pre-inference authored review: confirmation scenarios use distinct tasks or constraints; broad topics can overlap. No translations treated as independent confirmation scenarios. Exact/shingle checks do not prove semantic independence.',
            'old24_excluded_scenarios': 'No empty-afternoon advice, unfamiliar-city touring, book-club setup, new-colleague onboarding, small-team project report, or plant-growth/window-plant questions in confirmation.',
            'nearest_text_overlap_for_all_confirmation_items': nearest,
            'contrast_length_note': 'Prewritten continuations are approximately length matched within scenario, not token-identical; actual token lengths are recorded at collection.',
            'provenance': 'Assistant-authored fixed ordinary texts before experimental inference; not extracted or selected from target-model outputs. Old development trajectories are explicitly historical.'}


def main():
    map_data()
    contrast_data()
    confirm_data()
    dev_data()
    selection = ability_data()
    checks = audit()
    manifest = {'status': 'inputs_frozen_before_formal_confirmation', 'seed': SEED,
                'data_authored_date': '2026-10-26', 'checks': checks, 'ability_selection': selection,
                'files': {path.name: {'sha256': sha(path), 'bytes': path.stat().st_size}
                          for path in sorted(DATA.iterdir()) if path.suffix in ('.jsonl', '.tsv')},
                'source_old_corpus': {name: sha(OLD / name) for name in ('original.raw.jsonl', 'modified.raw.jsonl')},
                'prepare_data_sha256': sha(__file__)}
    (ROOT / 'data_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': manifest['status'], 'counts': checks['counts'],
                      'max_confirmation_shingle_overlap': max(x['shingle_jaccard'] for x in checks['nearest_text_overlap_for_all_confirmation_items']),
                      'manifest_sha256': sha(ROOT / 'data_manifest.json')}))


if __name__ == '__main__':
    main()
