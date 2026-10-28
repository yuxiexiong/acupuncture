#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"
url=http://127.0.0.1:8800/experiments/neuron-explorer-analysis-v1-2026-10-26/graph.html
if curl --max-time 2 -fsS "$url" >/dev/null 2>&1; then
    open "$url"
    exit 0
fi
exec python3 serve.py --open
