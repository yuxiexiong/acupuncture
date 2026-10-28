#!/usr/bin/env python3
"""Serve the analysis page and only its explicitly referenced evidence locally."""
import argparse
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
import webbrowser

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
PAGE = '/' + ROOT.relative_to(REPO).as_posix() + '/graph.html'


def allowed_paths():
    names = ('graph.html', 'index.html', 'evidence.json', 'evidence-manifest.json',
             'trace-format.json', 'survey-evidence.json', 'survey-manifest.json')
    paths = {ROOT / name for name in names}
    manifest = json.loads((ROOT / 'evidence-manifest.json').read_text())
    sources = [entry['path'] for entry in manifest['sources']]
    survey_manifest = ROOT / 'survey-manifest.json'
    if survey_manifest.is_file():
        survey = json.loads(survey_manifest.read_text())
        sources.extend(survey['record_paths'])
    for source in sources:
        candidate = (REPO / source).resolve()
        if not candidate.is_relative_to(REPO):
            raise ValueError('Evidence path is outside the repository')
        paths.add(candidate)
    return paths


class Handler(SimpleHTTPRequestHandler):
    def send_head(self):
        route = unquote(urlsplit(self.path).path)
        if route == '/':
            self.send_response(302)
            self.send_header('Location', PAGE)
            self.end_headers()
            return None
        candidate = (REPO / route.lstrip('/')).resolve()
        if candidate not in self.server.allowed_files or not candidate.is_file():
            self.send_error(404, 'Not a published evidence file')
            return None
        return super().send_head()

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        super().end_headers()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8800)
    parser.add_argument('--open', action='store_true', help='Open the page in the default browser')
    args = parser.parse_args()
    with ThreadingHTTPServer(('127.0.0.1', args.port), partial(Handler, directory=str(REPO))) as server:
        server.allowed_files = allowed_paths()
        url = f'http://127.0.0.1:{args.port}{PAGE}'
        print(url, flush=True)
        if args.open:
            webbrowser.open(url)
        server.serve_forever()


if __name__ == '__main__':
    main()
