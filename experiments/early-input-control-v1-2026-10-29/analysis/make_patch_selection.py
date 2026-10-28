"""Selection r02 = locked r01 conditions + patch candidates (rules r02) + confirmation item list.

python analysis/make_patch_selection.py SELECTION_R01 DEV_JOINED MECH_EXPORT_ZST OUT_JSON
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import experiment as ex  # noqa: E402

ABNORMAL = {'other_fact', 'other_wrong', 'not_delivered'}


def main(selection_path, joined_path, mech_export, out):
    r01 = ex.read(selection_path)
    joined = {(r['item_id'], r['condition']['id']): r for r in ex.read(joined_path)['rows']}
    mech = [json.loads(l) for l in subprocess.run(['zstd', '-dc', mech_export], capture_output=True, check=True).stdout.decode().splitlines()]
    items = {r['id']: r for r in ex.items('development')}

    def first_eos(cid, mode):
        return sum(1 for r in mech if r['condition']['id'] == cid and r['spec']['kind'] == 'generation' and r['spec']['mode'] == mode
                   and r['status'] == 'completed' and len(r['token_ids']) == 1 and r['end_reason'] == 'eos_token')

    early = ['N_L00_C4146_D+1', 'N_L02_C5251_D-1']
    score = {c: first_eos(c, 'full') + first_eos(c, 'prefill') for c in early}
    s1 = max(early, key=lambda c: (score[c], c == 'N_L00_C4146_D+1'))
    rows = {c['condition']['id']: c for c in r01['conditions']}

    def paired(ids):
        bases = {items[i]['base_id'] for i in ids}
        return sorted(i for i, r in items.items() if r['base_id'] in bases)

    def sources(cid, ids):
        value = {}
        for i in ids:
            rec = Path(joined[(i, cid)]['record']).resolve()
            value[i] = {'path': str(rec.relative_to(ex.HERE)), 'sha256': ex.sha(rec)}
        return value

    s1_items = paired([i for i in rows[s1]['item_ids'] if joined[(i, s1)]['mech']['tokens'] == 1 and joined[(i, s1)]['mech']['end_reason'] == 'eos_token'])
    s1_layer = rows[s1]['condition']['layer']
    s2 = 'N_L13_C248_D+1'
    usable = {i for i in items if joined[(i, 'clean')]['label']['fact'] == 'follows_fact'}
    ab = [i for i in rows[s2]['item_ids'] if i in usable and (joined[(i, s2)]['label']['fact'] in ABNORMAL or joined[(i, s2)]['label']['contradiction'])]
    s2_items = paired(ab)
    assert len({items[i]['base_id'] for i in s2_items}) >= 2
    candidates = []
    for symptom, cid, ids, layer, full_attention in (('first_step_stop', s1, s1_items, s1_layer, 3), ('content_error', s2, s2_items, 13, 15)):
        assert set(ids) <= set(rows[cid]['item_ids'])
        src = sources(cid, ids)
        for tag, site, neighbor in (('a', {'layer': layer, 'component': 'mlp'}, {'layer': layer + 1, 'component': 'mlp'}),
                                    ('b', {'layer': full_attention, 'component': 'attention'}, {'layer': full_attention + 1, 'component': 'attention'})):
            candidates.append({'id': f'{symptom}_{tag}_L{site["layer"]:02d}_{site["component"]}', 'symptom': symptom, 'condition_id': cid,
                               'item_ids': ids, 'source_records': src, 'prediction_step': 0, **site, 'neighbor': neighbor})
    evidence = dict(r01['evidence_hashes'])
    for c in candidates:
        for s in c['source_records'].values():
            evidence[s['path']] = s['sha256']
    value = {**r01, 'evidence_hashes': evidence, 'patch_candidates': candidates,
             'confirmation_item_ids': [r['id'] for r in ex.items('confirmation')],
             'supersedes': {'path': selection_path, 'sha256': ex.sha(selection_path)},
             'patch_rule_document': 'readiness/patch-candidate-rules-r02.zh-CN.md',
             'patch_rule_document_sha256': ex.sha(ex.HERE / 'readiness/patch-candidate-rules-r02.zh-CN.md'),
             'patch_rule_inputs': {'first_step_eos_full_plus_prefill': score, 's1_condition': s1,
                                   's2_abnormal_dev_items': ab, 'mechanism_export_sha256': ex.sha(mech_export)},
             'confirmation_outputs_previously_unseen': True, 'locked_at': ex.utc()}
    from execution import _validate_selection
    _validate_selection(value)
    ex.write(out, value, immutable=True)
    print(score, s1, len(s1_items), len(s2_items), [c['id'] for c in candidates])


if __name__ == '__main__':
    main(*sys.argv[1:5])
