"""CPU recheck of archived WSB answers/receipts; large tensors stay on the server."""
import argparse
import json
import os

os.environ['CUDA_VISIBLE_DEVICES'] = ''
import wsb_core as K
import wsb_run as R


def audit(run, stage):
    root = K.HERE/'runs'/run
    rc, ex = R.read(root/'receipt.json'), R.read(root/'exit.json')
    assert rc['status'] == 'completed' and ex['returncode'] == 0
    R.check_counts(rc, stage, complete=True)
    assert ex['supervisor_wall_seconds'] <= K.CAP[stage]
    authorization = K.HERE/f'readiness/authorization-{run}.json'
    assert R.sha(authorization) == rc['authorization_sha256']
    assert R.read(root/'authorization.json') == R.read(authorization)
    metadata = R.read(root/'metadata.json')
    assert rc['integrity']['hooks_removed']
    assert rc['integrity']['target_weight_sha256_after'] == metadata['target_weight_sha256_before']
    checked, tensor_manifests = 0, 0
    for rel, h in rc['files'].items():
        if rel.endswith('.pt'):
            tensor_manifests += 1  # Actual bytes/hash verified separately on server, not claimed here.
        else:
            assert R.sha(root/rel) == h, rel
            checked += 1
    items, tables = K.panel(stage)
    refs, _ = R.references()
    import spf_analysis as A
    data = R.read(root/'answers.json')
    rebuilt = {r: {c: {} for c in K.CELLS} for r in items}
    pairs = diagonals = answers = 0
    signed_zero = 0
    max_native_oracle = 0.
    for r in items:
        item = refs[r]['item']
        assert item['listed_codes'] == items[r]['listed_codes'] and item['target'] == items[r]['target']
        bases = R.read(root/f'records/{r}/bases.json')
        for bg in ('C', 'H'):
            old = refs[r]['once']['C0'] if bg == 'C' else refs[r]['directions'][K.MAIN]['OO']
            R.bridge(bases['bases'][bg]['answer'], old)
            signed_zero += bases['bases'][bg]['zero_signed_zero_tensors']
        for donor in tables[r]:
            d = donor['id']
            record = R.read(root/f'records/{r}/{d}.json')
            pairs += 1
            R.bridge(record['R_H']['answer'], refs[r]['directions'][K.MAIN]['DO|'+d])
            for source in ('C', 'H'):
                a, b = record['R_'+source], record[source+source]
                assert a['answer'] == b['answer']
                signed_zero += R.identical(a['snapshot'], b['snapshot'])
                diagonals += 1
                for bg in ('C', 'H'):
                    assert record[bg+source]['package_sha256'] == rc['files'][a['package']]
                assert all(record['C'+source]['layers'][str(l)]['delta_sha256'] ==
                           record['H'+source]['layers'][str(l)]['delta_sha256'] for l in K.G)
            for cell in ('R_C', 'R_H')+K.CELLS:
                a = record[cell]['answer']
                assert A.row_out(a['N'], item) == a['row']
                answers += 1
            for c in K.CELLS:
                rebuilt[r][c][d] = record[c]['answer']['row']
                assert set(map(int, record[c]['layers'])) == set(K.G)
                max_native_oracle = max(max_native_oracle, *(v['native_oracle'] for v in record[c]['layers'].values()))
    assert rebuilt == data['rows']
    assert pairs == K.limits(stage)['pairs'] and tensor_manifests == 2*pairs
    for c, rows in data['delivery'].items():
        assert len(rows) == pairs
        assert len({(v['receiver'], v['donor']) for v in rows}) == pairs
        for v in rows:
            assert v['row'] == rebuilt[v['receiver']][c][v['donor']]
    assert max_native_oracle <= 1e-5
    result = dict(status='passed', run=run, small_file_hashes=checked,
                  tensor_hash_manifest_entries=tensor_manifests, tensors_verified_here=False,
                  pairs=pairs, diagonal_checks=diagonals, parsed_answers=answers,
                  signed_zero_tensor_differences=signed_zero, max_native_oracle=max_native_oracle,
                  gpu_process_seconds=ex['supervisor_wall_seconds'])
    if stage == 'formal':
        recomputed = K.analyse(rebuilt, items, tables)
        saved = R.read(root/'analysis.json')
        assert all(saved[k] == v for k, v in recomputed.items())
        # Independently express the frozen receiver-balanced score, without calling d_transfer.
        direct = {}
        for c in K.CELLS:
            values = []
            for r, ds in tables.items():
                al = [d for d in ds if d['type'] == 'AL']
                terms = []
                for d in al:
                    controls = [x for x in ds if x['id'] != d['id'] and x['row'] != d['row'] and x['key'] != d['row']]
                    terms.append(float(rebuilt[r][c][d['id']] == d['row']) -
                                 sum(rebuilt[r][c][x['id']] == d['row'] for x in controls)/len(controls))
                values.append(sum(terms)/len(terms))
            direct[c] = sum(values)/len(values)
            assert abs(direct[c]-saved['cells'][c]['mean']) < 1e-12
        result.update(statistics_recomputed=True, direct_cell_means=direct)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True)
    args = p.parse_args()
    reports = [audit('preflight-20261111-r02', 'preflight'), audit('formal-20261111-r01', 'formal')]
    failed = R.read(K.HERE/'runs/preflight-20261111-r01/exit.json')
    assert failed['returncode'] == 1
    seconds = failed['supervisor_wall_seconds']+sum(r['gpu_process_seconds'] for r in reports)
    assert seconds <= K.TOTAL_CAP
    result = dict(status='passed', kind='author-side CPU recheck, not independent peer review',
                  runs=reports, total_gpu_process_seconds=seconds, total_gpu_process_hours=seconds/3600,
                  model_forwards=0, failed_attempt_included=True)
    R.write(args.output, result, immutable=True)
    print(json.dumps(result, ensure_ascii=False))
