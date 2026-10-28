#!/usr/bin/env python3
"""Check the running cache-only viewers without running model inference."""
import hashlib
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
SURVEY = ROOT.parents[1] / 'experiments/neuron-explorer-analysis-v1-2026-10-26/survey-evidence.json'


def request(base, path, body=None):
    req = Request(base + path, data=json.dumps(body).encode() if body is not None else None,
                  headers={'Content-Type': 'application/json'} if body is not None else {})
    try:
        with urlopen(req, timeout=30) as response:
            return response.status, response.read()
    except HTTPError as error:
        return error.code, error.read()


def main():
    results = []
    for model in json.loads((ROOT / 'models.json').read_text()):
        base = f'http://127.0.0.1:{model["port"]}'
        code, raw = request(base, '/api/index')
        assert code == 200
        index = json.loads(raw)
        assert index['profile'] == model['id'] and index['live_model'] is False and index['read_only'] is True
        assert index['arch']['n_layers'] == model['layers'] and index['arch']['inter'] == model['inter']
        code, raw = request(base, '/api/survey')
        assert code == 200 and hashlib.sha256(raw).digest() == hashlib.sha256(SURVEY.read_bytes()).digest()
        survey = next(m for m in json.loads(raw)['models'] if m['id'] == model['id'])
        assert len(survey['points']) == model['layers'] * 10
        point = survey['points'][0]
        record = point['doses']['1']['Q04']
        code, raw = request(base, '/evidence/' + record['source'])
        assert code == 200
        original = json.loads(raw)['output']
        assert original['answer_text'] == record['text'] and original['raw_text'] == record['raw_text']
        assert request(base, '/evidence/README.md')[0] == 404
        assert request(base, '/evidence/../README.md')[0] == 404
        # Empty requests cannot initiate a valid experiment even if the guard regresses.
        for path in ('/api/name', '/api/steer', '/api/claude'):
            assert request(base, path, {})[0] == 503
        for path in ('/api/layout?kind=writes', '/api/lens?layer=6&n=100', '/api/connections?layer=6&n=100&k=5'):
            assert request(base, path)[0] == 200
        results.append({'model': model['id'], 'points': len(survey['points']), 'cache_only': True,
                        'source_pairing': 'passed', 'cache_endpoints': 'passed', 'post_blocked': True})
    print(json.dumps({'status': 'passed', 'new_model_inference': False, 'models': results}, indent=2))


if __name__ == '__main__':
    main()
