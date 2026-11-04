"""One-off, explicitly authorized budget continuation; leaves the failed run intact."""
import copy
import fcntl
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import time

BASE = Path('/workspace/acupuncture/external/wcp01')
sys.path.insert(0, str(BASE / 'code/orchestration'))
from ledger import Ledger, authorize, file_hash, write


def main():
    old = BASE / 'runs/fleet-v1-0p8b'
    new = BASE / 'runs/fleet-v2-0p8b-budget-r1'
    config_path = BASE / 'fleet-configs/coding-0p8b-budget-r1.json'
    lock = (old / 'controller.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    source = sqlite3.connect('file:' + str(old / 'state.sqlite') + '?mode=ro', uri=True)
    meta = {k: json.loads(v) for k, v in source.execute('SELECT key,value FROM meta')}
    cfg = copy.deepcopy(meta['config'])
    authorize(cfg)
    assert meta['phase'] == 'D' and not meta.get('overrun')
    jobs = source.execute('SELECT * FROM jobs ORDER BY id').fetchall()
    assert [(r[0], r[2]) for r in jobs] == [('D-original-000', 'done'), ('D-original-032', 'running')]
    failed = old / 'actions/D-original-032'
    process = json.loads((failed / 'process.json').read_text())
    assert not Path('/proc', str(process['pid'])).exists()
    assert not any((failed / n).exists() for n in ('result.json', 'generation.jsonl', 'worker-result.json'))
    assert 'TimeoutExpired' in json.loads((failed / 'failure.json').read_text())['error']
    gpu = json.loads((failed / 'gpu-usage.json').read_text())
    reserve = json.loads(jobs[1][4])
    assert gpu['stage'] == 'A' and 787 < gpu['gpu_seconds'] < 790
    assert cfg['caps']['gpu_seconds'] == 14400 and cfg['caps']['gpu_A'] == 1800
    assert not new.exists() and not config_path.exists()
    assert shutil.disk_usage(old).free > cfg['reserve_free_bytes'] + 100_000_000
    new.mkdir()
    backup = sqlite3.connect(str(new / 'parent-state.sqlite'))
    source.backup(backup)
    backup.close()
    cfg['run_root'] = str(new)
    cfg['caps'].update(gpu_seconds=18000, gpu_A=5400)
    cfg['authorization_record'] += '; User 2026-11-04: 同意增加这 1 GPU 小时，原进度续跑; authorization.json in continuation root'
    write(new / 'authorization.json', dict(user_reply='同意增加这 1 GPU 小时，原进度续跑',
          scope='0.8B coding only: diagnostic A 30 to 90 GPU minutes, total 4 to 5 GPU hours; all scientific settings unchanged', time=time.time()))
    spent = meta['spent'].copy()
    for key in ('gpu_seconds', 'gpu_A'):
        spent[key] += gpu['gpu_seconds']
    # No output was flushed: reserve upper bounds rather than pretending the failed attempt was free.
    for key in ('samples', 'output_tokens'):
        spent[key] += reserve[key]
    assert all(spent[k] <= cfg['caps'][k] for k in spent)
    (new / 'actions').mkdir()
    shutil.copytree(old / 'actions/D-original-000', new / 'actions/D-original-000')
    for path in (old / 'actions/D-original-000').rglob('*'):
        if path.is_file():
            assert file_hash(path) == file_hash(new / 'actions/D-original-000' / path.relative_to(old / 'actions/D-original-000'))
    db = Ledger(new, cfg)
    try:
        with db.db:
            db.db.execute('INSERT INTO jobs VALUES(?,?,?,?,?,?)', jobs[0])
            db.put('spent', spent)
            db.put('phase', 'D')
        assert db.db.execute('SELECT * FROM jobs').fetchall() == [jobs[0]]
        receipt = dict(parent_run=str(old), continuation_run=str(new), config=str(config_path),
                       completed_reused=['D-original-000'], incomplete_to_retry=['D-original-032'],
                       failed_gpu_seconds_charged=gpu['gpu_seconds'],
                       failed_samples_upper_bound_charged=reserve['samples'],
                       failed_output_tokens_upper_bound_charged=reserve['output_tokens'],
                       failed_cpu_seconds='not measured by old exception path; original 7200-second historical CPU allocation retained; not claimed zero',
                       spent=spent, remaining=db.remaining(), budget_caps=cfg['caps'],
                       original_evidence_unchanged=True, scientific_settings_unchanged=True,
                       source_hashes_unchanged=cfg['source_hashes'] == meta['config']['source_hashes'])
        write(new / 'continuation-receipt.json', receipt)
        write(config_path, cfg)
        authorize(cfg)
        print(json.dumps(receipt), flush=True)
    finally:
        db.close()
        source.close()
        lock.close()


if __name__ == '__main__':
    main()
