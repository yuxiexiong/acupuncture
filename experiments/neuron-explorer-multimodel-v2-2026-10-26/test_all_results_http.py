"""Exercise the running local archive service; no model runtime or writes to raw evidence."""
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
BASE = 'http://127.0.0.1:8794'


def get(path, data=None, headers=None):
    try:
        with urlopen(Request(BASE + path, data=data, headers=headers or {}), timeout=60) as response:
            return response.status, response.read()
    except HTTPError as error:
        return error.code, error.read()


def read(path):
    code, raw = get(path)
    assert code == 200, (path, code, raw[:300])
    return json.loads(raw)


def main():
    index = read('/api/index')
    assert index['full_results'] and index['read_only'] and not index['new_inference']
    models = []
    for model, count, traces in [('2b', 3656, 920), ('4b', 4872, 4872), ('9b', 4872, 920), ('llama31-8b-instruct', 4872, 920)]:
        rows = read('/api/results/index?' + urlencode({'model': model}))['records']
        assert len(rows) == count and sum(r['has_trace'] for r in rows) == traces
        traced = next(r for r in rows if r['layer'] == 0 and r['dose'] == 1)
        untraced = next((r for r in reversed(rows) if not r['has_trace'] and r['dose'] == -1), None)
        for row in [traced] + ([untraced] if untraced else []):
            detail = read('/api/results/detail?' + urlencode({'model': model, 'id': row['trace_id']}))
            assert detail['has_trace'] == row['has_trace']
            assert (detail['trace'] is not None) == row['has_trace']
            for arm in ('baseline', 'intervened'):
                original = read(detail[arm]['source'])
                assert original['output']['token_ids'] == detail[arm]['token_ids']
            wrong = '2b' if model != '2b' else '4b'
            assert get('/api/results/detail?' + urlencode({'model': wrong, 'id': row['trace_id']}))[0] == 404
        models.append({'model': model, 'answers': count, 'traces': traces, 'untraced_checked': untraced is not None})
    catalog = read('/api/experiments')
    datasets = []
    for dataset in catalog['datasets']:
        page = read('/api/experiments/rows?' + urlencode({'dataset': dataset['id'], 'limit': 1}))
        if 'expected_rows' in dataset:
            assert page['total'] == dataset['expected_rows'], dataset['id']
        for view in dataset['views']:
            path = view['path']
            if path.endswith('.html'):
                assert get('/' + quote(path))[0] == 200, path
        datasets.append({'id': dataset['id'], 'rows': page['total']})
    for path in ['/api/experiments/rows?dataset=unknown', '/api/experiments/rows?dataset=initial24&page=-1',
                 '/experiments/../AGENTS.md', '/docs/../../AGENTS.md']:
        assert get(path)[0] == 400, path
    for path in ['/', '/library.html', '/library.js', '/trace.js']:
        assert get(path)[0] == 200, path
    assert get('/api/index', headers={'Origin': 'https://example.com'})[0] == 403
    assert get('/api/steer', data=b'{}')[0] == 503
    report = {'status': 'passed', 'checked_at': datetime.now(timezone.utc).isoformat(),
              'models': models, 'datasets': datasets, 'catalog_entries': len(datasets),
              'new_inference': False, 'model_isolation': True, 'missing_trace_is_null': True,
              'history_html_served': True, 'write_endpoints_blocked': True}
    (ROOT / 'all-experiments-r01/http-acceptance.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
