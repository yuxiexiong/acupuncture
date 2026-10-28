#!/usr/bin/env python3
"""CPU-only acceptance of all archived answers; HTTP acceptance is separate."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
import resource
import time

from serve_trajectories import Evidence, EXPECTED, EXPECTED_RESULTS, check_result_match, result_identity


def must_fail(call, error=KeyError):
    try:
        call()
    except error:
        return
    raise AssertionError('Expected rejection')


def main():
    start = time.monotonic()
    ev = Evidence()
    init_seconds = time.monotonic() - start
    assert len(ev.result_sources) == 18272 and len(ev.sources) == 7632
    assert sum(len(r['references']) for r in ev.result_sources.values()) == 19264
    assert Counter(r['model'] for r in ev.result_sources.values() if r['has_trace']) == EXPECTED
    for model, total in EXPECTED_RESULTS.items():
        index = ev.result_index(model)
        rows = index['records']
        assert len(rows) == total and index['formal_unique_records'] == 18272
        assert index['trace_counts'] == EXPECTED and len(ev.index(model)['records']) == EXPECTED[model]
        assert Counter(r['layer'] for r in rows)[None] == 8
        assert sum(r['has_trace'] for r in rows) == EXPECTED[model]
        assert all(r['model'] == model for r in rows)
        for row in rows:
            key = row['trace_id']
            source = ev.result_source(model, key)
            if row['has_trace']:
                check_result_match(ev.sources[key]['record'], source['record'])
            else:
                stable = 'answer-' + hashlib.sha256(json.dumps(result_identity(source['record']), separators=(',', ':')).encode()).hexdigest()
                assert key == stable
        traced = next(r for r in rows if r['layer'] == 0 and r['dose'] == 1)
        detail = ev.result_detail(model, traced['trace_id'])
        assert detail['trace'] is not None and detail['trace_status'] == 'collected'
        assert detail['trace']['generated_token_ids'] == detail['intervened']['token_ids']
        untraced = next((r for r in rows if not r['has_trace']), None)
        if untraced:
            detail = ev.result_detail(model, untraced['trace_id'])
            assert detail['trace'] is None and detail['sources']['trace'] is None
            assert detail['has_trace'] is False and detail['trace_status'] == 'not_collected'
            assert detail['baseline']['source'].startswith('/api/results/source?')
            assert detail['intervened']['token_ids'] == ev.result_original(model, untraced['trace_id'], 'intervened')['output']['token_ids']
            base = ev.result_original(model, untraced['trace_id'], 'baseline')
            assert base['layer'] is None and base['question_id'] == detail['question_id']
            must_fail(lambda: ev.source(model, untraced['trace_id']))
        wrong_model = '2b' if model != '2b' else '4b'
        must_fail(lambda: ev.result_detail(wrong_model, traced['trace_id']))
        must_fail(lambda: ev.result_original(model, traced['trace_id'], '../../README.md'))
        must_fail(lambda: ev.result_detail(model, '../../README.md'))
    record = next(iter(ev.result_sources.values()))['record']
    for field in ('prompt', 'context', 'calibration', 'output'):
        changed = deepcopy(record)
        changed[field] = 'different'
        must_fail(lambda: check_result_match(record, changed), ValueError)
    print(json.dumps({'status': 'passed', 'formal_unique_results': 18272, 'formal_traces': 7632,
                      'source_references': 19264, 'source_reuse_counted_once': True,
                      'model_isolation': True, 'conflict_rejected': True, 'new_inference': False,
                      'initialization_seconds': round(init_seconds, 3),
                      'max_rss_native_units': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}, indent=2))


if __name__ == '__main__':
    main()
