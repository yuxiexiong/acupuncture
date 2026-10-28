#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python_bin="${EXPLORER_PYTHON:-$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3}"
if [[ ! -x "$python_bin" ]]; then python_bin=python3; fi
mkdir -p runtime
if curl --silent --fail --max-time 2 http://127.0.0.1:8794/api/index > runtime/local-viewer-index.json; then
    "$python_bin" -c 'import json; assert json.load(open("runtime/local-viewer-index.json")).get("trace_view"), "Port 8794 belongs to another service; left unchanged."'
else
    nohup "$python_bin" serve_trajectories.py > runtime/local-trajectories.log 2>&1 < /dev/null &
    echo "$!" > runtime/local-trajectories.pid
fi
for attempt in {1..30}; do
    if curl --silent --fail --max-time 1 http://127.0.0.1:8794/api/index > /dev/null; then
        open 'http://127.0.0.1:8794/?model=4b'
        exit 0
    fi
    sleep 1
done
echo '本地轨迹服务未就绪，请查看 runtime/local-trajectories.log。'
exit 1
