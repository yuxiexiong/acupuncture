#!/usr/bin/env python3
"""Local read-only archived traces in the original Neuron Explorer; never imports a model runtime."""
import argparse
import base64
from collections import Counter
from functools import lru_cache
import gzip
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
from urllib.parse import parse_qs, urlencode, unquote, urlsplit

import numpy as np

from all_experiments import allowed_file, history_rows, load_catalog

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
STATIC = ROOT / 'upstream/explorer/static'
EXPERIMENTS = ['early-layer-mechanism-v1-2026-10-28',
               'layer-trace-extension-v1-2026-10-28', 'llama31-early-layer-trace-v1-2026-10-28']
VERIFICATION = REPO / 'experiments' / EXPERIMENTS[1] / 'archive-r01/combined-verification.json'
SURVEY = REPO / 'experiments/neuron-explorer-analysis-v1-2026-10-26/survey-evidence.json'
EXPECTED = {'2b': 920, '4b': 4872, '9b': 920, 'llama31-8b-instruct': 920}
EXPECTED_RESULTS = {'2b': 3656, '4b': 4872, '9b': 4872, 'llama31-8b-instruct': 4872}
RESULT_EXPORTS = {
    'layer-survey-toy-v1-2026-10-27': '3a926932b0c3f1ec856cd2ceba460f445354984d53337062d5db864773f311b6',
    'layer-negative-dose-survey-toy-v1-2026-10-27': '3fe11f40b8dd87b84db75dd7ceef5f4e9b28804110a36abe8e6ba514773c623b',
    'llama31-layer-survey-v1-2026-10-28': '8cf02306046e3f00fb5fa40ccfe67af0520d2bc33e4f5091d662e07b74fb2782',
    'llama31-single-point-dose-survey-v1-2026-10-28': '22a249e9a918e858a71123b84a0324d7d9c5d508f0f9e2fd6d6b881e47279028'}


def read(path):
    return json.loads(Path(path).read_text())


def result_identity(record):
    dose = record['intervention']['dose'] if record.get('intervention') else 0
    return (record['model_id'], record['layer'], record['channel'], float(dose), record['question_id'])


def check_result_match(expected, actual):
    if result_identity(expected) != result_identity(actual) or any(
            expected[field] != actual[field] for field in ('prompt', 'context', 'calibration', 'output')):
        raise ValueError('Conflicting archived result identity: ' + str(result_identity(actual)))


def models():
    out = read(ROOT / 'models.json')
    for m in out:
        p = ROOT / (f'live-{m["id"]}-r01.json' if m['id'] != '9b' else 'evidence-final-r01/live-9b-r01.json')
        check = next(c for c in read(p)['checks'] if c['name'] == 'index')
        m['arch'] = json.loads(check['raw_response'])['arch']
    out.append({'id': 'llama31-8b-instruct', 'label': 'Llama-3.1-8B-Instruct',
                'repo': 'meta-llama/Llama-3.1-8B-Instruct', 'revision': '0e9e39f249a16976918f6564b8830bc894c89659', 'layers': 32, 'hidden': 4096, 'inter': 14336,
                'arch': {'n_layers': 32, 'hidden': 4096, 'inter': 14336, 'attn_heads': 32, 'kv_heads': 8,
                         'layer_types': ['full_attention'] * 32, 'linear_k_heads': 0, 'linear_v_heads': 0}})
    return {m['id']: dict(m, port=8794, url='/?model=' + m['id']) for m in out}


MODELS = models()


class Evidence:
    def __init__(self):
        verification = read(VERIFICATION)
        if verification['status'] != 'verified' or verification['formal_unique_records'] != 7632:
            raise ValueError('Local archive verification has not passed')
        self.verification = verification
        self.sources, self.files, self.baselines = {}, {}, {}
        for experiment in EXPERIMENTS:
            root = REPO / 'experiments' / experiment
            for line in (root / 'sources.jsonl').open():
                row = json.loads(line)
                if experiment == EXPERIMENTS[1] and not row.get('stage'):
                    continue  # The 16 calibration references are not new formal records.
                key = row['trace_id']
                if key in self.sources:
                    raise ValueError('Duplicate source: ' + key)
                self.sources[key] = row
                if row['record']['layer'] is None:
                    self.baselines[row['model'], row['record']['question_id']] = row
            run = root / 'archive-r01/execution-r01'
            patterns = ['survey/*/records/*.json'] if experiment != EXPERIMENTS[1] else ['*/survey/*/records/*.json']
            for pattern in patterns:
                for p in run.glob(pattern):
                    key = p.stem.split('-', 1)[1]
                    if key in self.files:
                        raise ValueError('Duplicate archived trace: ' + key)
                    trace = p.parent.parent / 'traces' / (p.stem + '.json.gz')
                    if not trace.is_file():
                        raise ValueError('Missing compressed trace: ' + key)
                    self.files[key] = (p, trace)
        if set(self.files) != set(self.sources):
            raise ValueError('Archive/source coverage mismatch')
        if dict(Counter(r['model'] for r in self.sources.values())) != EXPECTED:
            raise ValueError('Wrong formal model counts')
        self.records = {m: [] for m in MODELS}
        self.questions = {}
        for key, row in self.sources.items():
            r = row['record']
            self.questions[r['question_id']] = {'id': r['question_id'], 'prompt': r['prompt']}
            self.records[row['model']].append({
                'trace_id': key, 'model': row['model'], 'layer': r['layer'], 'channel': r['channel'],
                'dose': r.get('intervention', {}).get('dose', 0) if r.get('intervention') else 0,
                'question_id': r['question_id'], 'tokens': len(r['output']['token_ids']),
                'stop_reason': r['output']['end_reason']})
        for rows in self.records.values():
            rows.sort(key=lambda r: (-1 if r['layer'] is None else r['layer'],
                                    -1 if r['channel'] is None else r['channel'], r['dose'], r['question_id']))
        self.old_allowed = set(read(SURVEY.with_name('survey-manifest.json'))['record_paths']) if SURVEY.exists() else set()
        self.load_results()

    def load_results(self):
        trace_ids = {result_identity(s['record']): key for key, s in self.sources.items()}
        if len(trace_ids) != len(self.sources):
            raise ValueError('Duplicate trace result identity')
        merged = {}
        for experiment, expected_hash in RESULT_EXPORTS.items():
            path = REPO / 'experiments' / experiment / 'delivery-r01/all.records.jsonl'
            data = path.read_bytes()
            if hashlib.sha256(data).hexdigest() != expected_hash:
                raise ValueError('Archived answer export hash mismatch: ' + experiment)
            for line_number, line in enumerate(data.splitlines(), 1):
                record = json.loads(line)
                identity = result_identity(record)
                reference = {'jsonl': str(path.relative_to(REPO)), 'line': line_number, 'sha256': expected_hash}
                if identity in merged:
                    check_result_match(merged[identity]['record'], record)
                    merged[identity]['references'].append(reference)
                    continue  # Reused output is one source, never an additional experiment.
                key = trace_ids.get(identity)
                if key is not None:
                    check_result_match(self.sources[key]['record'], record)
                    record = self.sources[key]['record']
                else:
                    key = 'answer-' + hashlib.sha256(json.dumps(identity, separators=(',', ':')).encode()).hexdigest()
                merged[identity] = {'trace_id': key, 'model': record['model_id'], 'record': record,
                                    'has_trace': identity in trace_ids, 'references': [reference]}
        if not set(trace_ids).issubset(merged):
            raise ValueError('Trace source absent from full answer archive')
        self.result_sources = {s['trace_id']: s for s in merged.values()}
        if len(self.result_sources) != len(merged) or dict(Counter(s['model'] for s in merged.values())) != EXPECTED_RESULTS:
            raise ValueError('Wrong full answer coverage')
        self.result_records = {m: [] for m in MODELS}
        for row in merged.values():
            r = row['record']
            baseline = self.baselines[row['model'], r['question_id']]['record']
            if any(r[field] != baseline[field] for field in ('prompt', 'context', 'calibration')):
                raise ValueError('Result/baseline input mismatch: ' + row['trace_id'])
            self.result_records[row['model']].append({
                'trace_id': row['trace_id'], 'model': row['model'], 'layer': r['layer'], 'channel': r['channel'],
                'dose': result_identity(r)[3], 'question_id': r['question_id'],
                'tokens': len(r['output']['token_ids']), 'stop_reason': r['output']['end_reason'],
                'has_trace': row['has_trace']})
        for rows in self.result_records.values():
            rows.sort(key=lambda r: (-1 if r['layer'] is None else r['layer'],
                                    -1 if r['channel'] is None else r['channel'], r['dose'], r['question_id']))

    def result_index(self, model):
        return {'model': MODELS[model], 'models': list(MODELS.values()), 'records': self.result_records[model],
                'questions': list(self.questions.values()), 'counts': EXPECTED_RESULTS, 'trace_counts': EXPECTED,
                'formal_unique_records': sum(EXPECTED_RESULTS.values()), 'formal_trace_records': sum(EXPECTED.values()),
                'full_results': True, 'verified': True, 'new_inference': False,
                'scope': 'Archived single-channel outputs; reused sources counted once. Only has_trace records have internal measurements.'}

    def result_source(self, model, key):
        row = self.result_sources.get(key)
        if row is None or row['model'] != model:
            raise KeyError('No result in selected model')
        return row

    def result_original(self, model, key, arm):
        row = self.result_source(model, key)
        if arm == 'baseline':
            return self.baselines[model, row['record']['question_id']]['record']
        if arm == 'intervened':
            return row['record']
        raise KeyError('Unknown result arm')

    def result_detail(self, model, key):
        row = self.result_source(model, key)
        if row['has_trace']:
            return {**self.detail(model, key), 'has_trace': True, 'trace_status': 'collected'}
        r = row['record']
        qs = urlencode({'model': model, 'id': key})
        def answer(arm):
            output = self.result_original(model, key, arm)['output']
            return {**output, 'stop_reason': output['end_reason'], 'source': '/api/results/source?' + qs + '&arm=' + arm}
        return {'trace_id': key, 'model': model, 'layer': r['layer'], 'channel': r['channel'],
                'dose': result_identity(r)[3], 'question_id': r['question_id'], 'prompt': r['prompt'],
                'baseline': answer('baseline'), 'intervened': answer('intervened'), 'trace': None,
                'sources': {'record': '/api/results/source?' + qs + '&arm=intervened', 'trace': None},
                'provenance': {'references': row['references']}, 'checks_passed': True,
                'has_trace': False, 'trace_status': 'not_collected'}

    def source(self, model, key):
        row = self.sources.get(key)
        if row is None or row['model'] != model:
            raise KeyError('No trace in selected model')
        return row

    def index(self, model):
        return {'model': MODELS[model], 'models': list(MODELS.values()), 'records': self.records[model],
                'questions': list(self.questions.values()), 'counts': EXPECTED,
                'formal_unique_records': 7632, 'verified': True, 'new_inference': False}

    def original(self, model, key, arm):
        row = self.source(model, key)
        if arm == 'baseline':
            row = self.baselines[model, row['record']['question_id']]
        return row['record']

    @lru_cache(maxsize=12)
    def detail(self, model, key):
        row = self.source(model, key)
        r = row['record']
        record_path, trace_path = self.files[key]
        archived = read(record_path)
        with gzip.open(trace_path, 'rt') as f:
            trace = json.load(f)
        if not (archived['checks_passed'] and archived['source_token_ids_match']
                and archived['output']['token_ids'] == trace['generated_token_ids'] == r['output']['token_ids']):
            raise ValueError('Record/source token mismatch')
        qs = urlencode({'model': model, 'id': key})
        def answer(arm):
            src = self.original(model, key, arm)
            output = src['output']
            return {**output, 'stop_reason': output['end_reason'],
                    'source': '/api/traces/source?' + qs + '&arm=' + arm}
        return {'trace_id': key, 'model': model, 'layer': r['layer'], 'channel': r['channel'],
                'dose': r['intervention']['dose'] if r.get('intervention') else 0,
                'question_id': r['question_id'], 'prompt': r['prompt'],
                'baseline': answer('baseline'), 'intervened': answer('intervened'), 'trace': trace,
                'sources': {'record': '/api/traces/record?' + qs, 'trace': '/api/traces/raw?' + qs},
                'provenance': row['provenance'], 'checks_passed': True}


# The following cache readers keep the upstream layout, lens and direct-connection formulas.
# No cache miss is allowed to fall back to model loading.
@lru_cache(maxsize=20)
def cache(model, name):
    path = ROOT / 'data' / model / 'cache' / (name + '.npz')
    if not path.is_file():
        return None
    identity = read(path.with_name('model.json'))
    if any(identity.get(k) != MODELS[model][k] for k in ('repo', 'revision', 'layers', 'inter')):
        raise ValueError('Static cache belongs to a different model')
    with np.load(path) as z:
        data = {k: z[k] for k in z.files}
    shape = (MODELS[model]['layers'], MODELS[model]['inter'])
    fields, tail = {'layout_writes': (('cell',), ()), 'layout_reads': (('cell',), ()),
                    'lens_index': (('up', 'down'), (12,)), 'steer_index': (('up', 'down'), (12,)),
                    'connections': (('down_z', 'up_z'), (24,)), 'act_scale': (('pos', 'neg'), ())}[name]
    if any(data[k].shape != shape + tail for k in fields):
        raise ValueError('Static cache dimensions do not match selected model')
    return data


@lru_cache(maxsize=4)
def vocab(model):
    path = ROOT / 'data' / model / 'cache/vocab.json'
    return read(path) if path.is_file() else []


def lens(model, layer, n, k=12):
    idx = cache(model, 'lens_index')
    if idx is None:
        return {'available': False, 'up': [], 'down': [], 'reason': 'No archived static lens for this model'}
    v = vocab(model)
    out = {side: [v[t] for t in idx[side][layer, n, :k]] for side in ('up', 'down')}
    st = cache(model, 'steer_index')
    if st is not None:
        out.update({f'steer_{side}': [v[t] for t in st[side][layer, n, :k]] for side in ('up', 'down')})
        out.update(kl_up=round(float(st['up_kl'][layer, n]), 3), kl_down=round(float(st['down_kl'][layer, n]), 3))
    return out


def connections(model, layer, n, k=24, lens_k=5):
    ci = cache(model, 'connections')
    out = {'down': [], 'up': [], 'available': ci is not None}
    if ci is None:
        return out
    for side in ('down', 'up'):
        for i in range(min(k, int(ci['k']))):
            z = float(ci[side + '_z'][layer, n, i])
            if z <= -1e4:
                continue
            l, channel = int(ci[side + '_layer'][layer, n, i]), int(ci[side + '_n'][layer, n, i])
            row = {'layer': l, 'n': channel, 'z': round(z, 2), 'sign': int(ci[side + '_sign'][layer, n, i]),
                   'name': '', 'words': []}
            if lens_k:
                words = lens(model, l, channel, lens_k)
                row.update(lens=words.get('steer_up', words['up']), lens_neg=words.get('steer_down', words['down']),
                           logit=words['up'], logit_neg=words['down'])
            out[side].append(row)
    return out


def search(model, query, limit=300):
    idx, st, v = cache(model, 'lens_index'), cache(model, 'steer_index'), vocab(model)
    if idx is None or len(query.strip()) < 2:
        return {'ready': idx is not None, 'results': []}
    match = np.array([i for i, t in enumerate(v) if query.strip().lower() in t.lower()], dtype=np.int32)
    out = []
    for source, data in [('lens', idx), ('steer', st)]:
        if data is None:
            continue
        for sign, side in [('+', 'up'), ('-', 'down')]:
            arr = data[side]
            hit = np.isin(arr, match)
            count = hit.sum(-1)
            best = np.where(hit, np.arange(arr.shape[-1]), 99).min(-1)
            out.extend((int(best[l, n]), -int(count[l, n]), int(l), int(n), sign, source)
                       for l, n in zip(*np.nonzero(count)))
    seen, result = set(), []
    for rank, _, layer, n, sign, source in sorted(out):
        key = layer, n, sign
        if key in seen:
            continue
        seen.add(key)
        if len(result) < limit:
            arr = (idx if source == 'lens' else st)['up' if sign == '+' else 'down']
            result.append({'layer': layer, 'n': n, 'sign': sign, 'rank': rank, 'src': source, 'name': '',
                           'swept': False, 'lens': [v[t] for t in arr[layer, n, :6]]})
    return {'ready': True, 'results': result, 'tokens': len(match), 'total': len(seen)}


def cone(model, layer, n, first=5, k=2, hops=0):
    ci = cache(model, 'connections')
    if ci is None:
        return []
    out = []
    for side, direction in [('down', 1), ('up', -1)]:
        front, seen, hop, start = [(layer, n)], {(layer, n)}, 1, len(out)
        while front and len(out) - start < 10000 and (not hops or hop <= hops):
            nxt = []
            for a, b in front:
                for i in range(min(first if hop == 1 else k, int(ci['k']))):
                    z = float(ci[side + '_z'][a, b, i])
                    if z < -1e4 or (hop > 1 and z < 15):
                        break
                    t = int(ci[side + '_layer'][a, b, i]), int(ci[side + '_n'][a, b, i])
                    src, dst = ((a, b), t) if side == 'down' else (t, (a, b))
                    out.append((*src, *dst, z * int(ci[side + '_sign'][a, b, i]), hop * direction))
                    if t not in seen:
                        seen.add(t)
                        nxt.append(t)
            front, hop = nxt, hop + 1
        del out[start + 10000:]
    return out


class Handler(BaseHTTPRequestHandler):
    def send(self, data, status=200, content_type='application/json', headers=None):
        if not isinstance(data, bytes):
            data = json.dumps(data, ensure_ascii=False, allow_nan=False).encode()
        if content_type.startswith('application/json') and len(data) > 2000 and 'gzip' in self.headers.get('Accept-Encoding', ''):
            data = gzip.compress(data, compresslevel=1)
            headers = dict(headers or {}, **{'Content-Encoding': 'gzip'})
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        self.send({'error': 'read-only archived evidence; model inference is disabled'}, 503)

    def do_GET(self):
        port = self.server.server_port
        hosts = {f'127.0.0.1:{port}', f'localhost:{port}'}
        origin = self.headers.get('Origin')
        if (self.headers.get('Host') not in hosts or (origin and urlsplit(origin).netloc not in hosts)
                or self.headers.get('Sec-Fetch-Site') == 'cross-site'):
            return self.send({'error': 'forbidden'}, 403)
        try:
            self.get()
        except (ValueError, TypeError) as error:
            self.send({'error': str(error)}, 400)
        except (KeyError, FileNotFoundError) as error:
            self.send({'error': str(error)}, 404)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def get(self):
        url = urlsplit(self.path)
        path, params = unquote(url.path), parse_qs(url.query)
        p = lambda name, default='': params.get(name, [default])[0]
        model = p('model', '4b')
        if model not in MODELS:
            raise ValueError('Unknown model')
        m = MODELS[model]
        ev = self.server.evidence
        if path == '/api/experiments':
            return self.send(load_catalog())
        if path == '/api/experiments/rows':
            return self.send(history_rows(p('dataset'), page=int(p('page', '0')), limit=int(p('limit', '12'))))
        if path.startswith(('/experiments/', '/docs/')):
            target = allowed_file(path.lstrip('/'))
            return self.send(target.read_bytes(), content_type=mimetypes.guess_type(target.name)[0] or 'application/octet-stream')
        layer, n = int(p('layer', '0')), int(p('n', '0'))
        if not (0 <= layer < m['layers'] and 0 <= n < m['inter']):
            raise ValueError('Coordinate outside selected model')
        if path == '/api/index':
            return self.send({'model': m['repo'], 'arch': m['arch'], 'layers': {}, 'status': 'archived traces · read only',
                              'profile': model, 'models': list(MODELS.values()), 'live_model': False,
                              'read_only': True, 'trace_view': True, 'full_results': True, 'new_inference': False})
        if path == '/api/results/index':
            return self.send(ev.result_index(model))
        if path.startswith('/api/results/'):
            key = p('id')
            ev.result_source(model, key)
            if path == '/api/results/detail':
                return self.send(ev.result_detail(model, key))
            if path == '/api/results/source':
                return self.send(ev.result_original(model, key, p('arm')))
            raise KeyError('Unknown result endpoint')
        if path == '/api/traces/index':
            return self.send(ev.index(model))
        if path.startswith('/api/traces/'):
            key = p('id')
            ev.source(model, key)
            if path == '/api/traces/detail':
                return self.send(ev.detail(model, key))
            if path == '/api/traces/source' and p('arm') in ('baseline', 'intervened'):
                return self.send(ev.original(model, key, p('arm')))
            if path == '/api/traces/record':
                return self.send(ev.files[key][0].read_bytes())
            if path == '/api/traces/raw':
                return self.send(ev.files[key][1].read_bytes(), content_type='application/gzip',
                                 headers={'Content-Disposition': 'attachment; filename="' + ev.files[key][1].name + '"'})
            raise KeyError('Unknown trace endpoint')
        if path == '/api/layout':
            kind = p('kind', 'writes')
            if kind not in ('writes', 'reads'):
                raise ValueError('Unknown layout kind')
            data = cache(model, 'layout_' + kind)
            return self.send({'available': False} if data is None else
                             {'available': True, 'shape': list(data['cell'].shape),
                              'cell': base64.b64encode(data['cell'].astype('<i2').tobytes()).decode()})
        if path == '/api/lens':
            return self.send(lens(model, layer, n))
        if path == '/api/connections':
            return self.send(connections(model, layer, n, min(24, max(0, int(p('k', '24'))))))
        if path == '/api/hover':
            words = lens(model, layer, n, 8)
            return self.send({'lens': words['up'], 'lens_neg': words['down'], 'steer': words.get('steer_up'),
                              'steer_neg': words.get('steer_down'), 'con': connections(model, layer, n, 16, 0)})
        if path == '/api/search':
            return self.send(search(model, p('q'), min(400, max(0, int(p('limit', '300'))))))
        if path in ('/api/web', '/api/web/summary'):
            links = cone(model, layer, n, min(24, max(1, int(p('first', '5')))),
                         min(24, max(1, int(p('k', '2')))), max(0, int(p('hops', '0'))))
            if path == '/api/web':
                rows = np.array([(*r[:4], round(r[4] * 10), r[5]) for r in links], dtype='<i2').reshape(-1, 6)
                return self.send(rows.tobytes(), content_type='application/octet-stream', headers={'X-Web-Total': str(len(rows))})
            return self.send({'src': 'static archived links; pooled summary not exported', 'links': len(links),
                              'available': False,
                              'down': {'neurons': len({(r[2], r[3]) for r in links if r[5] > 0}), 'toward': [], 'away': []},
                              'up': {'neurons': len({(r[0], r[1]) for r in links if r[5] < 0}), 'fed_by': [], 'held_by': []}})
        if path == '/api/unit':
            return self.send({'layer': layer, 'n': n, 'kind': p('kind', 'neuron'), 'name': ''})
        if path == '/api/units':
            return self.send([])
        if path == '/api/embeddings':
            return self.send({})
        if path == '/api/status':
            return self.send({'status': 'archived traces · read only', 'live_model': False})
        if path == '/api/survey':
            return self.send(SURVEY.read_bytes())
        if path.startswith('/evidence/'):
            name = path[len('/evidence/'):]
            target = (REPO / name).resolve()
            if name not in ev.old_allowed or not target.is_relative_to(REPO):
                raise KeyError('Evidence not in manifest')
            return self.send(target.read_bytes())
        if path.startswith('/api/'):
            raise KeyError('API is not available in the local archived viewer')
        target = (STATIC / ('index.html' if path == '/' else path.lstrip('/'))).resolve()
        if not target.is_relative_to(STATIC) or not target.is_file():
            raise KeyError('Static file not found')
        return self.send(target.read_bytes(), content_type=mimetypes.guess_type(target.name)[0] or 'application/octet-stream')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8794)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    server.evidence = Evidence()
    print(f'http://127.0.0.1:{args.port}/?model=4b — 18272 verified archived outputs, 7632 internal traces; no model runtime', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
