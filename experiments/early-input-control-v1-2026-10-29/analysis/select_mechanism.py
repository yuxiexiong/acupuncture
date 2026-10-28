"""Apply readiness/reading-and-selection-rules-r01 §2-§4 to locked, joined development labels.

python analysis/select_mechanism.py JOINED DEV_RUN OUT_JSON SUMMARY_JSON
Run on the server from the experiment directory; writes through experiment.write.
"""
import glob
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import experiment as ex  # noqa: E402

ABNORMAL = {'other_fact', 'other_wrong', 'not_delivered'}
EARLY = [(0, 4146), (2, 5251)]
LEGACY = (2, 5063)


def main(joined_path, dev_run, out, summary_out):
    joined = ex.read(joined_path)['rows']
    items = {r['id']: r for r in ex.items('development')}
    conds = {c['id']: c for c in ex.conditions('development')}
    label = {}
    for row in joined:
        cid = row['condition']['id']
        assert row['key'] == f'{row["item_id"]}__{cid}__full'
        label[(row['item_id'], cid)] = row
    assert len(label) == 4632, len(label)
    usable = {i: label[(i, 'clean')]['label']['fact'] == 'follows_fact' for i in items}
    bases = defaultdict(list)
    for i, r in items.items():
        bases[r['base_id']].append(i)
    base_usable = {b: all(usable[i] for i in ids) for b, ids in bases.items()}
    families = defaultdict(list)
    for b, ids in bases.items():
        families[items[ids[0]]['family']].append(b)
    family_usable = {f: sum(base_usable[b] for b in bs) >= 3 for f, bs in families.items()}

    def abnormal(item_id, cid):
        lab = label[(item_id, cid)]['label']
        return usable[item_id] and (lab['fact'] in ABNORMAL or lab['contradiction'])

    def abnormal_bases(cid):
        return sorted(b for b, ids in bases.items() if any(abnormal(i, cid) for i in ids))

    def rank(cid):
        c = conds[cid]
        return (len(abnormal_bases(cid)), abs(c['dose']), c['dose'] > 0, -c['layer'], -c.get('channel', 10**6))

    def item_ids(cid):
        ab = abnormal_bases(cid)
        chosen = ab if len(ab) >= 2 else sorted(bases)
        return [i for b in chosen for i in sorted(bases[b])], len(ab) >= 2

    def first_eos(cid, ids):
        return sum(label[(i, cid)]['mech']['tokens'] == 1 and label[(i, cid)]['mech']['end_reason'] == 'eos_token' for i in ids)

    picks = []
    for layer, channel in EARLY:
        cands = [c for c in conds.values() if c['kind'] == 'native' and (c['layer'], c['channel']) == (layer, channel)]
        best = max(cands, key=lambda c: rank(c['id']))
        picks.append(('early', best, *item_ids(best['id'])))
    others = []
    for name, layers in (('middle', range(12, 16)), ('late', range(24, 28))):
        cands = [c for c in conds.values() if c['kind'] == 'native' and c['layer'] in layers]
        best = max(cands, key=lambda c: rank(c['id']))
        if not abnormal_bases(best['id']):
            best = next(c for c in cands if c['dose'] == 1.0)
        others.append((name, best, *item_ids(best['id'])))
    taken = {p[1]['id'] for p in others}
    rest = [c for c in conds.values() if c['kind'] != 'clean' and c['layer'] >= 12 and c['id'] not in taken]
    third = max(rest, key=lambda c: rank(c['id']))
    if abnormal_bases(third['id']):
        others.append(('third_reference', third, *item_ids(third['id'])))

    evidence, conditions, rows_out = {}, [], []
    for role, cond, ids, symptomatic in picks + others:
        sources = {}
        for i in ids:
            rec = Path(label[(i, cond['id'])]['record']).resolve()
            relative = str(rec.relative_to(ex.HERE))
            sources[i] = {'path': relative, 'sha256': ex.sha(rec)}
            evidence[relative] = sources[i]['sha256']
        conditions.append({'role': role, 'condition': cond, 'item_ids': ids, 'source_records': sources,
                           'symptomatic': symptomatic, 'abnormal_bases': abnormal_bases(cond['id']),
                           'first_step_eos_items': first_eos(cond['id'], ids)})
    # Legacy +1 anchor point; only supported old-format adapter.
    contract_path = '../layer-survey-toy-v1-2026-10-27/contract.json'
    evidence[contract_path] = ex.sha(ex.HERE / contract_path)
    anchors = ex.items('anchors')
    legacy_sources = {}
    for a in anchors:
        found = glob.glob(str(ex.HERE.parent / f'layer-survey-toy-v1-2026-10-27/survey-r01/4b-shard-*/records/L{LEGACY[0]:02d}-N{LEGACY[1]:06d}__{a["id"]}.json'))
        assert len(found) == 1, (a['id'], found)
        rel = str(Path('..') / Path(found[0]).resolve().relative_to(ex.HERE.parent.resolve()))
        legacy_sources[a['id']] = {'format': 'legacy_layer_survey_v1', 'path': rel, 'sha256': ex.sha(found[0]), 'contract_path': contract_path}
        evidence[rel] = legacy_sources[a['id']]['sha256']
    legacy_cond = {'id': f'N_L{LEGACY[0]:02d}_C{LEGACY[1]}_D+1', 'kind': 'native', 'layer': LEGACY[0], 'channel': LEGACY[1], 'dose': 1.0}
    conditions.insert(2, {'role': 'early_legacy_anchor', 'condition': legacy_cond, 'item_ids': [a['id'] for a in anchors],
                          'source_records': legacy_sources, 'symptomatic': None, 'abnormal_bases': None,
                          'first_step_eos_items': sum(ex.read(ex.HERE / s['path'])['output']['token_ids'][:1] in ([248044], [248046]) for s in legacy_sources.values())})
    split = sorted([c for c in conditions if c['first_step_eos_items']], key=lambda c: -c['first_step_eos_items'])[:3]
    for c in conditions:
        c['first_step_split'] = c in split
    assert len(conditions) <= 6
    value = {'status': 'locked', 'experiment': ex.HERE.name, 'freeze_sha256': ex.sha(ex.HERE / 'freeze-r03.json'),
             'rule_document': 'readiness/reading-and-selection-rules-r01.zh-CN.md',
             'rule_document_sha256': ex.sha(ex.HERE / 'readiness/reading-and-selection-rules-r01.zh-CN.md'),
             'labels_joined_path': str(Path(joined_path).resolve().relative_to(ex.HERE)), 'labels_joined_sha256': ex.sha(joined_path),
             'evidence_hashes': evidence,
             'conditions': [{k: c[k] for k in ('condition', 'item_ids', 'source_records', 'first_step_split')} for c in conditions],
             'condition_rationale': [{k: c[k] for k in ('role', 'symptomatic', 'abnormal_bases', 'first_step_eos_items')} | {'id': c['condition']['id']} for c in conditions],
             'patch_candidates': [], 'locked_at': ex.utc()}
    summary = {'usable_items': usable, 'base_usable': base_usable, 'family_usable': family_usable,
               'abnormal_bases_by_condition': {cid: abnormal_bases(cid) for cid in conds if cid != 'clean'}}
    from execution import _validate_selection
    _validate_selection(value)
    ex.write(out, value, immutable=True)
    ex.write(summary_out, summary, immutable=True)
    print(json.dumps(value['condition_rationale'], ensure_ascii=False, indent=1), family_usable)


if __name__ == '__main__':
    main(*sys.argv[1:5])
