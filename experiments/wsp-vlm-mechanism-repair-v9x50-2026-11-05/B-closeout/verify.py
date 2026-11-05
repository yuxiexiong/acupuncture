"""Verify the complete stopped B50 archive and re-score saved answers; no model calls."""
import gzip
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
EXPERIMENTS = HERE.parents[1]
sys.path.insert(0, str(EXPERIMENTS / 'wsp-vlm-mechanism-repair-v9-2026-11-05'))
from evidence import scorers, summarize, repair_score, compare


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main(root):
    source = json.loads((HERE / 'remote-files.json').read_text())
    assert not source['symlinks']
    files = {str(p.relative_to(root)): p for p in root.rglob('*') if p.is_file()}
    assert set(files) == set(source['files']), 'Missing or extra archive files'
    for name, path in files.items():
        ref = source['files'][name]
        assert path.stat().st_size == ref['bytes'] and sha(path) == ref['sha256'], name
    read = lambda p: json.loads(p.read_text())
    state = read(root / 'state.json')
    assert state['research_done'] and state['repair_rounds_completed'] == 50
    rounds = [read(p) for p in sorted(root.glob('artifacts/repair-round-*.json'))]
    assert len(rounds) == 50 and len({r['signature'] for r in rounds}) == 50
    assert {r['round'] for r in rounds} == set(range(1, 51))
    evaluations = []
    scorer = scorers()['B']
    for ref in state['evaluations'].values():
        path = root / ref['path']
        assert sha(path) == ref['sha256']
        e = read(path)
        assert e['full_development'] and len(e['predictions']) == 464
        rows = scorer.score(e['predictions'], e['scored'])
        assert rows == e['scored']
        assert summarize(rows) == {k: v for k, v in e['summary'].items() if k != 'repair_score'}
        assert abs(repair_score(rows) - e['summary']['repair_score']) < 1e-12
        evaluations.append(e)
    ev = {e['candidate']: e for e in evaluations}
    assert len(ev) == len(evaluations) == 51
    baseline = next(e for k, e in ev.items() if k.startswith('w0-'))
    assert all(e['ids'] == baseline['ids'] and e['protocol'] == baseline['protocol'] for e in ev.values())
    best = ev[state['best']]
    freeze = read(root / 'frozen-candidate.json')
    report = read(root / 'mechanism-report.json')
    assert state['frozen'] == state['best'] == freeze['manifest']['id'] == report['report']['candidate']
    manifests = [read(p) for p in sorted(root.glob('candidates/*/manifest.json'))]
    by_id = {m['id']: m for m in manifests}
    assert all(by_id[r['candidate']]['changed_scalars'] > 0 for r in rounds)
    selected = baseline['candidate']
    contract = freeze['contract']
    eligible = 0
    for r in sorted(rounds, key=lambda r: r['round']):
        c = r['candidate']
        s = ev[c]['summary']
        protected = max(s['format_errors'], s['truncated']) / 464 <= contract['max_format_rate']
        for key, cell in baseline['summary']['cells'].items():
            if key.rsplit(':', 1)[-1] in contract['protection_conditions']:
                after = s['cells'][key]
                protected &= cell['n'] == after['n'] and (cell['correct']-after['correct'])/cell['n'] <= contract['max_protection_drop']
        if protected:
            eligible += 1
            rank = lambda candidate: (ev[candidate]['summary']['repair_score'],
                                      0 if candidate == baseline['candidate'] else -by_id[candidate]['changed_scalars'])
            if rank(c) >= rank(selected):
                selected = c
    assert selected == state['best'], 'Frozen selection does not match the recorded rule'
    for path in sorted(root.glob('actions/*/request.json')):
        assert (path.parent / 'response.json').exists(), str(path)
    for path in root.glob('inbox/*.json'):
        assert (root / 'actions' / path.stem / 'response.json').exists()
    changes = compare(baseline['scored'], best['scored'])
    result = dict(model_calls=0, files_verified=len(files), bytes_verified=sum(p.stat().st_size for p in files.values()),
                  rounds=50, unique_nonzero_candidates=50, complete_evaluations=51,
                  scored_answers_verified=51*464, frozen=state['frozen'], eligible_candidates=eligible,
                  selected_round=next(r['round'] for r in rounds if r['candidate'] == selected),
                  baseline=baseline['summary'], best=best['summary'], repaired=changes['repaired'],
                  worsened=changes['worsened'], independent_confirmation=False,
                  fresh_model_reload_performed=False, scientific_review='not_independent')
    evidence = dict(state=state, rounds=rounds, evaluations=evaluations, manifests=manifests,
                    freeze=freeze, mechanism_report=report, source_manifest='remote-files.json')
    with gzip.open(HERE / 'evaluations-and-candidates.json.gz', 'wt', encoding='utf-8') as f:
        json.dump(evidence, f, ensure_ascii=False)
    (HERE / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('baseline', 'best', 'repaired', 'worsened')}, ensure_ascii=False))


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
