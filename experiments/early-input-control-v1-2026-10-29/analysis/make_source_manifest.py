"""Confirmation patch source manifest: bind mechanism-confirmation full records for each locked patch condition.

python analysis/make_source_manifest.py SELECTION MECH_CONF_RUN OUT_JSON
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import experiment as ex  # noqa: E402


def main(selection_path, run, out):
    selection = ex.read(selection_path)
    run = Path(run).resolve()
    receipts = {w: ex.read(run / f'worker-{w}' / 'receipt.json') for w in (0, 1)}
    sources, evidence = {}, {}
    for cid in sorted({c['condition_id'] for c in selection['patch_candidates']}):
        sources[cid] = {}
        for item in selection['confirmation_item_ids']:
            relative = f'records/{item}__{cid}__full.json'
            worker = next(w for w, r in receipts.items() if relative in r['record_hashes'])
            path = run / f'worker-{worker}' / relative
            assert ex.sha(path) == receipts[worker]['record_hashes'][relative]
            rel = str(path.relative_to(ex.HERE))
            sources[cid][item] = {'path': rel, 'sha256': ex.sha(path)}
            evidence[rel] = sources[cid][item]['sha256']
    ex.write(out, {'status': 'locked', 'panel': 'confirmation', 'experiment': ex.HERE.name,
                   'freeze_sha256': ex.sha(ex.HERE / 'freeze-r03.json'), 'selection_path': selection_path,
                   'selection_sha256': ex.sha(selection_path), 'source_run': str(run.relative_to(ex.HERE)),
                   'evidence_hashes': evidence, 'sources': sources, 'created_at': ex.utc(),
                   'note': 'Candidates, sites and steps are unchanged from the pre-confirmation lock; only source records are new.'},
             immutable=True)
    print({k: len(v) for k, v in sources.items()})


if __name__ == '__main__':
    main(*sys.argv[1:4])
