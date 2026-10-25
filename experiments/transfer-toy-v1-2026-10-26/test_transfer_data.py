"""CPU checks for provenance, exact benchmark payloads, and fixed historical trajectories."""
import hashlib
import json
from pathlib import Path

from prepare_data import DATA, OLD, PANEL, ROOT, audit, main, rows, sha


def test_data():
    before = {p: sha(p) for p in DATA.glob('*.jsonl')}
    main()
    assert {p: sha(p) for p in DATA.glob('*.jsonl')} == before
    audit()
    originals = {r['id']: r for task in ('mmlu', 'arc_challenge')
                 for r in rows(PANEL / 'items' / f'{task}.jsonl')}
    for row in rows(DATA / 'ability_diag.jsonl'):
        original = dict(row)
        original.pop('diagnostic_group')
        assert original == originals[row['id']]
    historical = {}
    for name in ('original.raw.jsonl', 'modified.raw.jsonl'):
        for line in (OLD / name).read_text().splitlines():
            row = json.loads(line)
            if row['attempt']['max_new_tokens'] == 512:
                historical[(row['question']['id'], row['arm'])] = (row, line)
    for row in rows(DATA / 'dev.jsonl'):
        source, line = historical[(row['question_id'], row['family'])]
        assert row['source_row_sha256'] == hashlib.sha256(line.encode()).hexdigest()
        assert row['prompt_token_ids'] == source['question']['input']['tensors']['input_ids'][0]
        tokens = source['response']['token_ids']
        stop = next((i + 1 for i, token in enumerate(tokens) if token in (248044, 248046)), len(tokens))
        assert row['answer_token_ids'] == tokens[:stop]
        assert row['source_attempt_budget'] == 512 and int(row['question_id'][1:]) <= 24
    manifest = json.loads((ROOT / 'data_manifest.json').read_text())
    for name, spec in manifest['files'].items():
        assert sha(DATA / name) == spec['sha256']
    print('PASS: deterministic data regeneration, category balance, no exact overlaps, v3 payload identity, all 48 token-exact historical trajectories')


if __name__ == '__main__':
    test_data()
