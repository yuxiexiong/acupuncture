"""Extract local, archived researcher evidence; no network or model calls."""
import gzip
import hashlib
import io
import json
import re
import tarfile
from pathlib import Path

P = Path(__file__).resolve().parent
ROOT = P.parents[1]

def sha(b):
    return hashlib.sha256(b).hexdigest()

def main():
    collect_protocols()
    pack = {'provenance': {}, 'runs': {}}
    for version in ('v8', 'v9'):
        controller = ROOT / f'external/wsp-vlm-gemma3-{version}-2026-11-05-r02/C/controller'
        if version == 'v8':
            paths = [controller.parent / 'delivery/C-researcher-trace.tar.gz']
            expected = '693fc97efda59cce0ec426e751bb1eb80a0020cc5447f810b559f38124102165'
        else:
            delivery = ROOT / 'experiments/wsp-vlm-gemma3-v9-shared-admission-2026-11-06/final-C-delivery'
            paths = sorted(delivery.glob('C-researcher-trace.tar.gz.part*'))
            expected = 'ec6ea641dc574b7f6535e0a39f5f05a595c446cc4adbd60d4b48d3eb5369f758'
        raw = b''.join(p.read_bytes() for p in paths)
        assert sha(raw) == expected
        with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as archive:
            selected = {m.name.removeprefix('controller/'): archive.extractfile(m).read() for m in archive
                        if m.isfile() and (m.name.endswith('/reply.txt') or m.name.endswith('/tool_result.json'))}
        records = []
        for path in sorted(controller.glob('turn-*-request.json')):
            request = json.loads(path.read_text())
            turn = request['id']
            reply_path = f'conversation/{turn}/reply.txt'
            reply = selected[reply_path]
            assert reply == (controller / reply_path).read_bytes()
            fences = re.findall(r'```(forward|python)\s*\n(.*?)```', reply.decode(), re.S)
            if request['kind'] == 'forward':
                assert any(lang == 'forward' and json.loads(code) == request['request'] for lang, code in fences), turn
            else:
                assert any(lang == 'python' and code.strip() == request['code'].strip() for lang, code in fences), turn
            response_path = f'conversation/{turn}/tool_result.json'
            response = json.loads(selected[response_path])
            local_response = json.loads((controller / f'{turn}-response.json').read_text())
            assert response == local_response, turn
            # Keep all researcher prose/code, exact actions, and full Python/commit feedback.
            # Other model output arrays already belong to the original archived evidence.
            op = request.get('request', {}).get('op')
            kept = response if request['kind'] == 'python' or op == 'commit' else {
                'id': response['id'], 'failed': response.get('failed'), 'elapsed_seconds': response.get('elapsed_seconds')}
            records.append({'turn': turn, 'request': request, 'reply': reply.decode(), 'response': kept,
                            'reply_sha256': sha(reply), 'response_archive_sha256': sha(selected[response_path])})
        pack['runs'][version] = records
        pack['provenance'][version] = {'archive_paths': [str(p.relative_to(ROOT)) for p in paths],
                                       'archive_sha256': expected, 'verified_request_reply_response_triples': len(records)}
    data = (json.dumps(pack, ensure_ascii=False, sort_keys=True) + '\n').encode()
    (P / 'trace-extract.json.gz').write_bytes(gzip.compress(data, mtime=0))
    print(json.dumps(pack['provenance'], indent=2))

def collect_protocols():
    protocols = {}
    for version in ('v8', 'v9'):
        base = ROOT / f'experiments/wsp-vlm-gemma3-{version}-2026-11-05-r02'
        manifest = json.loads((base / 'source-manifest.json').read_text())
        for name in ('RESEARCHER.md', 'evidence.py'):
            raw = (base / name).read_bytes()
            assert sha(raw) == manifest['files'][name]
            protocols[f'{version}/{name}'] = {'source': str((base / name).relative_to(ROOT)),
                'sha256': sha(raw), 'source_manifest_sha256': sha((base / 'source-manifest.json').read_bytes()),
                'content': raw.decode()}
    (P / 'protocol-sources.json').write_text(json.dumps(protocols, ensure_ascii=False, indent=2) + '\n')

if __name__ == '__main__':
    main()
