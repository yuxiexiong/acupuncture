"""Verify saved records for the broadening review; no model imports."""
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
L0, L12 = 'N_L00_C4146_D-1', 'N_L12_C3621_D-1'
SOURCES = {
    'NCC': 'native-carrier-comparison', 'NSR': 'native-s-reverse',
    'NQK': 'native-qk-history', 'NPC': 'native-pair-combination',
    'LVK': 'local-v-k',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit():
    records, source_files = {}, {}
    for key, name in SOURCES.items():
        folder = ROOT / 'experiments' / f'cache-{name}-v1-2026-11-03'
        selected = {}
        for receipt_path in sorted((folder / 'runs/formal-r01').glob('worker-*/receipt.json')):
            receipt = json.loads(receipt_path.read_text())
            assert receipt['status'] == 'completed', receipt_path
            source_files[str(receipt_path.relative_to(ROOT))] = sha(receipt_path)
            for rel, expected in sorted(receipt['record_hashes'].items()):
                path = receipt_path.parent / rel
                d = json.loads(path.read_text())
                if key == 'LVK' and d['panel'] != 'new':
                    continue
                actual = sha(path)
                assert actual == expected, path
                assert d['text'] not in selected, (key, d['text'])
                source_files[str(path.relative_to(ROOT))] = actual
                selected[d['text']] = (d, str(path.relative_to(ROOT)))
        assert len(selected) == 48, (key, len(selected))
        records[key] = selected
    ids = sorted(records['NCC'])
    assert all(set(r) == set(ids) for r in records.values())

    ledger_path = ROOT / 'experiments/cache-local-v-k-v1-2026-11-03/data/heldout-tokens-r01.json'
    ledger = json.loads(ledger_path.read_text())['items']
    source_files[str(ledger_path.relative_to(ROOT))] = sha(ledger_path)
    rows, summaries, bridges, paired = [], {}, Counter(), []
    for uid in ids:
        ds = {key: records[key][uid][0] for key in SOURCES}
        ncc, nsr, nqk, npc, lvk = (ds[k] for k in SOURCES)
        for key in ('NSR', 'NQK', 'NPC'):
            assert ds[key]['formation_hashes'] == ncc['formation_hashes']
            for arm in ('C', L0, L12):
                a = ds[key]['results'][arm]
                b = ncc['results'][arm]
                if arm != 'C':
                    a, b = a['T'], b['T']
                assert a['N']['ids'] == b['N']['ids']
                assert all(a[f] == b[f] for f in ('B', 'z_f', 'best_stop', 'best_nonstop_comp'))
        assert npc['ncc_record_sha256'] == source_files[records['NCC'][uid][1]]
        assert npc['nsr_record_sha256'] == source_files[records['NSR'][uid][1]]
        assert npc['nqk_record_sha256'] == source_files[records['NQK'][uid][1]]
        it = ncc['item']
        assert lvk['competitor'] == (it['first_listed'] if it['target'] != it['first_listed'] else it['listed_codes'][1])
        assert all(ds[k]['item'] == it for k in SOURCES)
        assert lvk['formation_hashes']['C_b'] == ncc['formation_hashes']['C_b']
        assert lvk['formation_hashes'][f'T_b|{L0}'] == ncc['formation_hashes'][f'T_b|{L0}']
        tokens = ledger[uid]['tokens']
        assert tokens['q_shared'] == ncc['f']
        assert len(set([tokens['target_second']] + tokens['distractor_second'])) == 3

        for key in ('NCC', 'NSR', 'NQK', 'NPC'):
            result = ds[key]['results']
            for needle in (L0, L12):
                for arm, r in result[needle].items():
                    if arm == '_nsr_CJ_sha':
                        continue  # NQK provenance metadata, not an experimental cell.
                    name = f'{key}|{needle}|{arm}'
                    s = summaries.setdefault(name, Counter())
                    s.update(n=1, correct=r['Y'], first_stop=r['first_stop'], first_is_f=r['first_is_f'])
                    s['category:' + r['cat']] += 1

        cells = {
            'C': ('NCC', ncc['results']['C']),
            'T': ('NCC', ncc['results'][L0]['T']),
            'TV': ('NCC', ncc['results'][L0]['TV']),
            'TS': ('NCC', ncc['results'][L0]['TS']),
            'CS': ('NSR', nsr['results'][L0]['CS']),
            'CK': ('NSR', nsr['results'][L0]['CK']),
            'CSK': ('NPC', npc['results'][L0]['CSK']),
            'CVK': ('NPC', npc['results'][L0]['CVK']),
            'CVSK': ('NQK', nqk['results'][L0]['CVSK']),
        }
        old = {
            'C': lvk['directions']['C_clean'],
            'T': lvk['directions'][L0]['arms']['L00'],
            'TV': lvk['directions'][L0]['arms']['V'],
        }
        for arm, (key, r) in cells.items():
            stop_margin = r['best_stop'] - max(r['z_f'], r['best_nonstop_comp'])
            assert (stop_margin > 0 and r['first_stop']) or (stop_margin < 0 and not r['first_stop']) or stop_margin == 0
            row = {'input': uid, 'scenario': ncc['scenario'], 'arm': arm,
                   'source': records[key][uid][1], 'target': it['target'], 'first_listed': it['first_listed'],
                   'B': r['B'], 'stop_margin': stop_margin, 'first_is_f': r['first_is_f'],
                   'first_stop': r['first_stop'], 'Y': r['Y'], 'category': r['cat'],
                   'conditional_M_first': None, 'conditional_M_all': None, 'conditional_source': None}
            if arm in old:
                prior = old[arm]
                assert prior['N']['ids'] == r['N']['ids'] and prior['x'] == r['winner']
                if r['first_is_f']:
                    assert r['N']['t2_sha'] == prior['C']['t2_sha']
                    bridges['natural_common_prefix_t2_hash_matches'] += 1
                row.update(conditional_M_first=prior['C']['M'] if it['target'] != it['first_listed'] else None,
                           conditional_M_all=prior['C']['M_all'], conditional_source=records['LVK'][uid][1])
                bridges['reusable_conditional_rows'] += 1
            else:
                bridges['missing_conditional_rows'] += 1
            rows.append(row)
        a, b = cells['CSK'][1], cells['CVSK'][1]
        paired.append({'input': uid, 'CSK_Y': a['Y'], 'CVSK_Y': b['Y'],
                       'CSK_etype': a['etype'], 'CVSK_etype': b['etype'],
                       'CSK_first_stop': a['first_stop'], 'CVSK_first_stop': b['first_stop']})

    assert len(rows) == 432 and bridges['reusable_conditional_rows'] == 144
    assert bridges['missing_conditional_rows'] == 288
    wrong = [r for r in paired if not r['CSK_Y']]
    assert len(wrong) == 16 and all(not r['CVSK_Y'] for r in wrong)
    assert all(r['CSK_etype'] != r['CVSK_etype'] for r in wrong)
    return {'status': 'passed', 'scope': 'CPU verification and saved-readout inventory; no model execution',
            'source_files_sha256': source_files, 'records_verified': 240, 'unique_inputs': 48,
            'target_not_first': sum(records['NCC'][i][0]['item']['target'] != records['NCC'][i][0]['item']['first_listed'] for i in ids),
            'bridges': dict(bridges), 'historical_summaries': summaries,
            'primary_pair': paired, 'selected_L0_readouts': rows,
            'remote_tensor_contents_rechecked': False,
            'cache_rebuild_upper_bound': {'formations': 96, 'prefix_prefills': 48,
                                          'formation_token_forwards': 2 * sum(ledger[i]['plan']['L'] for i in ids)}}


if __name__ == '__main__':
    output = audit()
    (HERE / 'existing-readouts-audit.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: output[k] for k in ('status', 'records_verified', 'unique_inputs', 'target_not_first', 'bridges', 'cache_rebuild_upper_bound')}, ensure_ascii=False))
