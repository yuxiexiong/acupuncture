#!/usr/bin/env python3
"""Acceptance of real archived data, model isolation, and the read-only HTTP boundary."""
from collections import Counter
import json
import threading
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from serve_trajectories import Evidence, EXPECTED, Handler, MODELS, ROOT, ThreadingHTTPServer, read


def main():
    evidence = Evidence()
    checked = []
    for model, total in EXPECTED.items():
        rows = evidence.index(model)['records']
        assert len(rows) == total
        counts = Counter(r['layer'] for r in rows)
        assert counts.pop(None) == 8
        assert set(counts) == set(range(32 if model == '4b' else 6))
        assert set(counts.values()) == {152}
        assert {r['dose'] for r in rows} == {-1, -.5, -.25, -.125, -.0625, 0, .0625, .125, .25, .5, 1}
        for row in rows:
            source = evidence.source(model, row['trace_id'])['record']
            base = evidence.original(model, row['trace_id'], 'baseline')
            assert base['layer'] is None and base['channel'] is None
            assert base['question_id'] == source['question_id'] and base['prompt'] == source['prompt']
            assert base['calibration']['input_token_sha256'] == source['calibration']['input_token_sha256']
        chosen = [next(r for r in rows if r['layer'] is None),
                  next(r for r in rows if r['layer'] == max(counts) and r['dose'] == -1),
                  next(r for r in rows if r['layer'] == 0 and r['dose'] == 1)]
        for row in chosen:
            detail = evidence.detail(model, row['trace_id'])
            trace = detail['trace']
            assert trace['model_id'] == model
            assert trace['generated_token_ids'] == detail['intervened']['token_ids']
            assert trace['observed_input_token_ids'] == trace['input_token_ids'] + trace['generated_token_ids'][:-1]
            assert len(trace['sites']) == MODELS[model]['layers'] * 3
            assert trace['clean_shadow']['forced_history'] and trace['clean_shadow']['fresh_cache']
            if row['layer'] is None:
                assert detail['baseline']['answer_text'] == detail['intervened']['answer_text']
                assert all(v == 0 for s in trace['sites'] for v in s['delta_norm'])
        checked.append({'model': model, 'records': total, 'injection_layers': len(counts), 'detail_checks': len(chosen)})
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.evidence = evidence
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_port}'
    def request(path, data=None, headers=None):
        req = Request(base + path, data=data, headers=headers or {})
        try:
            with urlopen(req, timeout=30) as response:
                return response.status, response.read()
        except HTTPError as error:
            return error.code, error.read()
    try:
        for model in EXPECTED:
            code, raw = request('/api/index?' + urlencode({'model': model}))
            index = json.loads(raw)
            assert code == 200 and index['profile'] == model and index['trace_view']
            assert index['live_model'] is False and index['read_only'] is True
            code, raw = request('/api/traces/index?' + urlencode({'model': model}))
            assert code == 200 and len(json.loads(raw)['records']) == EXPECTED[model]
            key = next(r['trace_id'] for r in evidence.records[model] if r['layer'] == 0 and r['dose'] < 0)
            qs = urlencode({'model': model, 'id': key})
            code, raw = request('/api/traces/detail?' + qs)
            assert code == 200
            detail = json.loads(raw)
            code, raw = request(detail['baseline']['source'])
            assert code == 200 and json.loads(raw)['output']['answer_text'] == detail['baseline']['answer_text']
            code, raw = request(detail['intervened']['source'])
            assert code == 200 and json.loads(raw)['output']['token_ids'] == detail['intervened']['token_ids']
            code, raw = request(detail['sources']['record'])
            assert code == 200 and json.loads(raw)['trace_id'] == key
            code, raw = request(detail['sources']['trace'])
            assert code == 200 and raw[:2] == b'\x1f\x8b'
            wrong = '2b' if model != '2b' else '4b'
            assert request('/api/traces/detail?' + urlencode({'model': wrong, 'id': key}))[0] == 404
        for path in ['/api/index?model=bogus', '/api/unit?model=2b&layer=24&n=0',
                     '/api/unit?model=2b&layer=0&n=6144']:
            assert request(path)[0] == 400
        for path in ['/../../README.md', '/%2e%2e/README.md', '/evidence/README.md',
                     '/evidence/../README.md', '/api/traces/raw?model=4b&id=../../README.md']:
            assert request(path)[0] == 404
        assert request('/api/index', headers={'Origin': 'https://example.com'})[0] == 403
        assert request('/api/index', headers={'Host': 'attacker.example'})[0] == 403
        for path in ['/api/steer', '/api/agent/chat', '/api/name']:
            assert request(path, data=b'{}', headers={'Content-Type': 'application/json'})[0] == 503
        assert request('/')[0] == 200
        # Qwen original static caches remain available; Llama explicitly has no computed layout.
        for model in ('2b', '4b', '9b'):
            code, raw = request('/api/layout?' + urlencode({'model': model, 'kind': 'writes'}))
            assert code == 200 and json.loads(raw)['shape'] == [MODELS[model]['layers'], MODELS[model]['inter']]
            for api in ('lens', 'connections', 'hover'):
                code, raw = request('/api/' + api + '?' + urlencode({'model': model, 'layer': 10, 'n': 100}))
                assert code == 200 and json.loads(raw)
                if api == 'lens':
                    saved = ROOT / (f'live-{model}-r01.json' if model != '9b' else 'evidence-final-r01/live-9b-r01.json')
                    original = next(c for c in read(saved)['checks'] if c['name'] == 'lens')
                    assert json.loads(raw) == json.loads(original['raw_response'])
            code, raw = request('/api/search?' + urlencode({'model': model, 'q': 'sky', 'limit': 5}))
            assert code == 200 and json.loads(raw)['ready']
            code, raw = request('/api/web?' + urlencode({'model': model, 'layer': 10, 'n': 100, 'first': 2, 'k': 1, 'hops': 2}))
            assert code == 200 and len(raw) > 0 and len(raw) % 12 == 0
        code, raw = request('/api/layout?model=llama31-8b-instruct&kind=writes')
        assert code == 200 and json.loads(raw)['available'] is False
    finally:
        server.shutdown()
        server.server_close()
    report = {'status': 'passed', 'new_inference': False, 'formal_records': sum(EXPECTED.values()),
              'models': checked, 'all_source_baseline_pairs_checked': True,
              'model_isolation': True, 'path_boundary': True, 'post_blocked': True,
              'local_archive_gate': str(evidence.verification['status'])}
    output = ROOT / 'trace-view-r01/backend-acceptance.json'
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
