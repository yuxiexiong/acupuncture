"""Offline closeout verification; joins archived parts in listed order, no model calls."""
import gzip
import hashlib
import io
import json
import tarfile
from pathlib import Path

P = Path(__file__).resolve().parent
remote = json.loads((P/'remote.json').read_text())
local = json.loads((P/'local.json').read_text())['C']
run = remote['runs']['v9C']
state = json.loads((P/'state.json').read_text())
frozen = json.loads((P/'frozen-candidate.json').read_text())
report = json.loads((P/'mechanism-report.json').read_text())
manifest = {r['path']:r for r in json.loads((P/'C-remote-file-manifest.json').read_text())}
assert state == run['state']
assert state['repair_rounds_completed'] == 30
assert len(state['completed_repair_candidates']) == 30
assert state['best'] == state['frozen'] == frozen['manifest']['id'] == report['report']['candidate']
assert state['research_done']
assert run['process_cmdline'] is None and local['process'] == '' and local['status']['stage'] == 'finished'
assert len(run['evaluations']) == 31 and all(r['hash_ok'] and r['full_development'] for r in run['evaluations'])
science = json.loads(gzip.decompress((P.parents[1]/'wsp-gemma-v8-v9-final-comparison-2026-11-06/C-science-complete.json.gz').read_bytes()))
assert science['evaluation_sha256'] == {v['path']:v['sha256'] for v in state['evaluations'].values()}
for row in state['evaluations'].values():
    assert manifest['search/'+row['path']]['sha256'] == row['sha256']
for tensor in frozen['manifest']['tensors'].values():
    row = manifest['search/candidates/'+state['best']+'/'+tensor['file']]
    assert row['sha256'] == tensor['sha256'] and not row['included']
archives = json.loads((P/'archive-sha256.json').read_text())
counts = {}
for name, a in archives.items():
    chunks=[]
    for part in a['parts_in_order']:
        data=(P/part['file']).read_bytes()
        assert len(data)==part['bytes'] and hashlib.sha256(data).hexdigest()==part['sha256']
        chunks.append(data)
    data=b''.join(chunks)
    assert len(data)==a['bytes'] and hashlib.sha256(data).hexdigest()==a['sha256']
    observed={}
    with tarfile.open(fileobj=io.BytesIO(data),mode='r|gz') as tf:
        for member in tf:
            if member.isfile():observed[member.name]=hashlib.sha256(tf.extractfile(member).read()).hexdigest()
    if 'remote-evidence' in name:
        expected={n:r['sha256'] for n,r in manifest.items() if r['included']}
        observed.pop('archive-file-manifest.json')
        assert observed==expected
    counts[name]=len(observed)
verification=dict(complete_nonzero_rounds=30,complete_evaluations_including_w0=31,
    science_and_final_cache_hashes_match=True,frozen_patch_file_hash_matches=True,
    report_and_freeze_match_selected_candidate=True,remote_and_local_processes_exited=True,
    archive_members_verified=counts,independent_confirmation=False,
    excluded_binary_files_retained_remote=sum(not r['included'] for r in manifest.values()))
(P/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
print(json.dumps(verification,indent=2))
